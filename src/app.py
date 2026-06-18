import json
import os
from pathlib import Path

import redis


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

# app.py is stored inside src/, so move up one folder to reach data/
DATA_FOLDER = Path(__file__).resolve().parent.parent / "data"

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True,
)


# ---------------------------------------------------------
# General helper functions
# ---------------------------------------------------------

def test_redis_connection():
    """Test the Redis connection before opening the application menu."""
    try:
        redis_client.ping()
        print("\nConnected to Redis successfully.")
        return True
    except redis.exceptions.ConnectionError:
        print("\nCould not connect to Redis.")
        print("Make sure the Redis server is running, then try again.")
        return False


def read_json_lines(file_path, limit=None):
    """
    Read a JSON Lines file one record at a time.

    This allows the application to process large files without loading
    the complete file into memory.
    """
    count = 0

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                line = line.strip()

                if not line:
                    continue

                try:
                    yield json.loads(line)
                    count += 1
                except json.JSONDecodeError:
                    print(
                        f"Skipped invalid JSON on line {line_number} "
                        f"in {file_path.name}."
                    )

                if limit is not None and count >= limit:
                    break
    except OSError as error:
        print(f"\nCould not open {file_path}: {error}")


def get_import_limit():
    """Ask the user how many records should be imported."""
    while True:
        value = input(
            "Enter the maximum number of records to import "
            "(press Enter to import all records): "
        ).strip()

        if value == "":
            return None

        try:
            limit = int(value)

            if limit <= 0:
                print("The limit must be greater than zero.")
                continue

            return limit
        except ValueError:
            print("Enter a whole number or press Enter.")


def pause():
    """Pause before returning to a menu."""
    input("\nPress Enter to return to the menu...")


def clean_text(value):
    """Convert values to strings that Redis can safely store."""
    if value is None:
        return ""

    if isinstance(value, (dict, list)):
        return json.dumps(value)

    return str(value)


def confirm_file_exists(file_path):
    """Check that a required dataset file exists."""
    if not file_path.exists():
        print(f"\nFile not found: {file_path}")
        print(
            "Make sure the repository was cloned correctly and "
            "run 'git lfs pull' if needed."
        )
        return False

    return True


# ---------------------------------------------------------
# Commit CRUD operations
# ---------------------------------------------------------

def commit_key(commit_id):
    """Create the Redis key for a commit."""
    return f"commit:{commit_id}"


def save_commit(record):
    """Save one commit as a Redis hash and update lookup indexes."""
    commit_id = clean_text(record.get("commit")).strip()

    if not commit_id:
        return False

    author = record.get("author") or {}
    committer = record.get("committer") or {}
    repo_names = record.get("repo_name") or []

    if isinstance(repo_names, str):
        repo_names = [repo_names]

    repo_name = repo_names[0] if repo_names else ""

    mapping = {
        "commit": commit_id,
        "author_name": clean_text(author.get("name")),
        "author_email": clean_text(author.get("email")),
        "committer_name": clean_text(committer.get("name")),
        "committer_email": clean_text(committer.get("email")),
        "repo_name": clean_text(repo_name),
        "subject": clean_text(record.get("subject")),
        "message": clean_text(record.get("message")),
        "tree": clean_text(record.get("tree")),
        "parent": clean_text(record.get("parent")),
    }

    key = commit_key(commit_id)

    # Remove the old index entries when an existing record is updated.
    if redis_client.exists(key):
        old_repo = redis_client.hget(key, "repo_name")
        old_author = redis_client.hget(key, "author_name")

        if old_repo:
            redis_client.srem(f"repo:{old_repo}:commits", commit_id)

        if old_author:
            redis_client.srem(f"author:{old_author}:commits", commit_id)

    redis_client.hset(key, mapping=mapping)
    redis_client.sadd("commits:all", commit_id)

    if mapping["repo_name"]:
        redis_client.sadd(
            f"repo:{mapping['repo_name']}:commits",
            commit_id,
        )

    if mapping["author_name"]:
        redis_client.sadd(
            f"author:{mapping['author_name']}:commits",
            commit_id,
        )

    return True


def import_commits():
    """Import commit records from the Git repository dataset."""
    file_path = DATA_FOLDER / "Commits.json"

    if not confirm_file_exists(file_path):
        return

    limit = get_import_limit()
    imported = 0

    for record in read_json_lines(file_path, limit):
        if save_commit(record):
            imported += 1

    print(f"\nImported {imported} commit records into Redis.")


def create_commit():
    """Create a new commit record through user input."""
    print("\nCREATE COMMIT")

    commit_id = input("Commit ID: ").strip()

    if not commit_id:
        print("Commit ID is required.")
        return

    if redis_client.exists(commit_key(commit_id)):
        print("A commit with that ID already exists.")
        return

    record = {
        "commit": commit_id,
        "author": {
            "name": input("Author name: ").strip(),
            "email": input("Author email: ").strip(),
        },
        "committer": {
            "name": input("Committer name: ").strip(),
            "email": input("Committer email: ").strip(),
        },
        "repo_name": [input("Repository name: ").strip()],
        "subject": input("Subject: ").strip(),
        "message": input("Message: ").strip(),
        "tree": input("Tree ID: ").strip(),
        "parent": [input("Parent commit ID: ").strip()],
    }

    save_commit(record)
    print("Commit created successfully.")


def display_commit_data(data):
    """Display one commit record."""
    if not data:
        print("Commit not found.")
        return

    print("\nCOMMIT DETAILS")
    print(f"Commit ID:       {data.get('commit', '')}")
    print(f"Repository:      {data.get('repo_name', '')}")
    print(f"Author:          {data.get('author_name', '')}")
    print(f"Author email:    {data.get('author_email', '')}")
    print(f"Committer:       {data.get('committer_name', '')}")
    print(f"Committer email: {data.get('committer_email', '')}")
    print(f"Subject:         {data.get('subject', '')}")
    print(f"Message:         {data.get('message', '')}")
    print(f"Tree:            {data.get('tree', '')}")
    print(f"Parent:          {data.get('parent', '')}")


def read_commit():
    """Read a commit by its ID."""
    print("\nREAD COMMIT")
    commit_id = input("Enter the commit ID: ").strip()
    data = redis_client.hgetall(commit_key(commit_id))
    display_commit_data(data)


def update_commit():
    """Update an existing commit record."""
    print("\nUPDATE COMMIT")
    commit_id = input("Enter the commit ID: ").strip()
    key = commit_key(commit_id)

    if not redis_client.exists(key):
        print("Commit not found.")
        return

    current = redis_client.hgetall(key)

    print("Press Enter to keep the current value.")

    new_repo = input(
        f"Repository [{current.get('repo_name', '')}]: "
    ).strip()
    new_author = input(
        f"Author name [{current.get('author_name', '')}]: "
    ).strip()
    new_author_email = input(
        f"Author email [{current.get('author_email', '')}]: "
    ).strip()
    new_committer = input(
        f"Committer name [{current.get('committer_name', '')}]: "
    ).strip()
    new_committer_email = input(
        f"Committer email [{current.get('committer_email', '')}]: "
    ).strip()
    new_subject = input(
        f"Subject [{current.get('subject', '')}]: "
    ).strip()
    new_message = input(
        f"Message [{current.get('message', '')}]: "
    ).strip()

    try:
        parent_value = json.loads(current.get("parent", "[]") or "[]")
    except json.JSONDecodeError:
        parent_value = [current.get("parent", "")]

    record = {
        "commit": commit_id,
        "repo_name": [new_repo or current.get("repo_name", "")],
        "author": {
            "name": new_author or current.get("author_name", ""),
            "email": new_author_email or current.get("author_email", ""),
        },
        "committer": {
            "name": new_committer or current.get("committer_name", ""),
            "email": (
                new_committer_email
                or current.get("committer_email", "")
            ),
        },
        "subject": new_subject or current.get("subject", ""),
        "message": new_message or current.get("message", ""),
        "tree": current.get("tree", ""),
        "parent": parent_value,
    }

    save_commit(record)
    print("Commit updated successfully.")


def delete_commit():
    """Delete a commit and remove its index references."""
    print("\nDELETE COMMIT")
    commit_id = input("Enter the commit ID: ").strip()
    key = commit_key(commit_id)

    if not redis_client.exists(key):
        print("Commit not found.")
        return

    data = redis_client.hgetall(key)
    repo_name = data.get("repo_name", "")
    author_name = data.get("author_name", "")

    confirm = input(
        f"Delete commit {commit_id}? Enter Y to confirm: "
    ).strip().lower()

    if confirm != "y":
        print("Delete cancelled.")
        return

    redis_client.delete(key)
    redis_client.srem("commits:all", commit_id)

    if repo_name:
        redis_client.srem(f"repo:{repo_name}:commits", commit_id)

    if author_name:
        redis_client.srem(f"author:{author_name}:commits", commit_id)

    print("Commit deleted successfully.")


def search_commits_by_repository():
    """Search imported commits by full repository name."""
    print("\nSEARCH COMMITS BY REPOSITORY")

    repo_name = input(
        "Enter the full repository name, such as owner/project: "
    ).strip()

    commit_ids = sorted(
        redis_client.smembers(f"repo:{repo_name}:commits")
    )

    if not commit_ids:
        print("No commits were found for that repository.")
        return

    print(f"\nFound {len(commit_ids)} commit(s) for {repo_name}:")

    for commit_id in commit_ids:
        data = redis_client.hgetall(commit_key(commit_id))

        print(
            f"- {commit_id[:12]} | "
            f"{data.get('author_name', 'Unknown')} | "
            f"{data.get('subject', '')}"
        )


# ---------------------------------------------------------
# Analysis feature 1: programming languages
# ---------------------------------------------------------

def import_languages():
    """Import language information from Languages.json."""
    file_path = DATA_FOLDER / "Languages.json"

    if not confirm_file_exists(file_path):
        return

    limit = get_import_limit()
    imported = 0

    for record in read_json_lines(file_path, limit):
        repo_name = clean_text(record.get("repo_name")).strip()
        languages = record.get("language") or []

        if not repo_name:
            continue

        # Remove old totals when re-importing a repository.
        old_languages = redis_client.hgetall(
            f"repo:{repo_name}:languages"
        )

        for old_name, old_bytes in old_languages.items():
            redis_client.zincrby(
                "analysis:language_bytes",
                -int(old_bytes),
                old_name,
            )
            redis_client.zincrby(
                "analysis:language_repo_count",
                -1,
                old_name,
            )

        redis_client.delete(f"repo:{repo_name}:languages")

        for item in languages:
            language_name = clean_text(item.get("name")).strip()

            try:
                byte_count = int(item.get("bytes", 0))
            except (TypeError, ValueError):
                byte_count = 0

            if language_name:
                redis_client.hset(
                    f"repo:{repo_name}:languages",
                    language_name,
                    byte_count,
                )
                redis_client.zincrby(
                    "analysis:language_bytes",
                    byte_count,
                    language_name,
                )
                redis_client.zincrby(
                    "analysis:language_repo_count",
                    1,
                    language_name,
                )

        redis_client.sadd("languages:repos", repo_name)
        imported += 1

    print(f"\nImported language data for {imported} repositories.")


def show_language_analysis():
    """Display the top languages by total bytes."""
    print("\nPROGRAMMING LANGUAGE ANALYSIS")

    results = redis_client.zrevrange(
        "analysis:language_bytes",
        0,
        9,
        withscores=True,
    )

    if not results:
        print("No language data found. Import Languages.json first.")
        return

    print("\nTop languages by total bytes:")

    for position, (language, total_bytes) in enumerate(results, start=1):
        repo_count = redis_client.zscore(
            "analysis:language_repo_count",
            language,
        ) or 0

        print(
            f"{position}. {language}: "
            f"{int(total_bytes):,} bytes across "
            f"{int(repo_count):,} repositories"
        )


# ---------------------------------------------------------
# Analysis feature 2: licenses
# ---------------------------------------------------------

def import_licenses():
    """Import repository licenses from Licenses.json."""
    file_path = DATA_FOLDER / "Licenses.json"

    if not confirm_file_exists(file_path):
        return

    limit = get_import_limit()
    imported = 0

    for record in read_json_lines(file_path, limit):
        repo_name = clean_text(record.get("repo_name")).strip()
        license_name = clean_text(record.get("license")).strip()

        if not repo_name or not license_name:
            continue

        old_license = redis_client.hget("licenses:by_repo", repo_name)

        if old_license and old_license != license_name:
            redis_client.zincrby(
                "analysis:license_count",
                -1,
                old_license,
            )

        if old_license != license_name:
            redis_client.hset(
                "licenses:by_repo",
                repo_name,
                license_name,
            )
            redis_client.zincrby(
                "analysis:license_count",
                1,
                license_name,
            )

        imported += 1

    print(f"\nImported {imported} license records.")


def show_license_analysis():
    """Display the most common licenses."""
    print("\nLICENSE ANALYSIS")

    results = redis_client.zrevrange(
        "analysis:license_count",
        0,
        9,
        withscores=True,
    )

    if not results:
        print("No license data found. Import Licenses.json first.")
        return

    print("\nMost common licenses:")

    for position, (license_name, count) in enumerate(results, start=1):
        print(f"{position}. {license_name}: {int(count)} repositories")


# ---------------------------------------------------------
# Analysis feature 3: most-watched repositories
# ---------------------------------------------------------

def import_watched_repositories():
    """Import watch counts from Sample_Repos.json."""
    file_path = DATA_FOLDER / "Sample_Repos.json"

    if not confirm_file_exists(file_path):
        return

    limit = get_import_limit()
    imported = 0

    for record in read_json_lines(file_path, limit):
        repo_name = clean_text(record.get("repo_name")).strip()

        try:
            watch_count = int(record.get("watch_count", 0))
        except (TypeError, ValueError):
            watch_count = 0

        if not repo_name:
            continue

        redis_client.zadd(
            "analysis:watch_counts",
            {repo_name: watch_count},
        )
        imported += 1

    print(f"\nImported {imported} repository watch-count records.")


def show_watched_repositories():
    """Display the most-watched repositories."""
    print("\nMOST-WATCHED REPOSITORIES")

    results = redis_client.zrevrange(
        "analysis:watch_counts",
        0,
        9,
        withscores=True,
    )

    if not results:
        print(
            "No repository watch data found. "
            "Import Sample_Repos.json first."
        )
        return

    for position, (repo_name, watch_count) in enumerate(results, start=1):
        print(f"{position}. {repo_name}: {int(watch_count):,} watchers")


# ---------------------------------------------------------
# Analysis feature 4: file extensions
# ---------------------------------------------------------

def import_files():
    """Import file records from Files.json."""
    file_path = DATA_FOLDER / "Files.json"

    if not confirm_file_exists(file_path):
        return

    limit = get_import_limit()
    imported = 0

    for record in read_json_lines(file_path, limit):
        file_id = clean_text(record.get("id")).strip()

        if not file_id:
            continue

        mapping = {
            "repo_name": clean_text(record.get("repo_name")),
            "ref": clean_text(record.get("ref")),
            "path": clean_text(record.get("path")),
            "mode": clean_text(record.get("mode")),
            "id": file_id,
            "symlink_target": clean_text(record.get("symlink_target")),
        }

        key = f"file:{file_id}"

        # Remove the previous extension count if this file already exists.
        if redis_client.exists(key):
            old_path = redis_client.hget(key, "path") or ""
            old_extension = (
                Path(old_path).suffix.lower() or "[no extension]"
            )
            redis_client.zincrby(
                "analysis:file_extensions",
                -1,
                old_extension,
            )

        redis_client.hset(key, mapping=mapping)
        redis_client.sadd("files:all", file_id)

        extension = Path(mapping["path"]).suffix.lower() or "[no extension]"

        redis_client.zincrby(
            "analysis:file_extensions",
            1,
            extension,
        )

        imported += 1

    print(f"\nImported {imported} file records.")


def show_file_extension_analysis():
    """Display the most common file extensions."""
    print("\nFILE EXTENSION ANALYSIS")

    results = redis_client.zrevrange(
        "analysis:file_extensions",
        0,
        9,
        withscores=True,
    )

    if not results:
        print("No file data found. Import Files.json first.")
        return

    for position, (extension, count) in enumerate(results, start=1):
        print(f"{position}. {extension}: {int(count)} files")


# ---------------------------------------------------------
# Database tools
# ---------------------------------------------------------

def show_database_summary():
    """Display counts for the current Redis project data."""
    print("\nDATABASE SUMMARY")
    print(f"Stored commits: {redis_client.scard('commits:all'):,}")
    print(
        "Repositories with language data: "
        f"{redis_client.scard('languages:repos'):,}"
    )
    print(
        "Stored license records: "
        f"{redis_client.hlen('licenses:by_repo'):,}"
    )
    print(f"Stored file records: {redis_client.scard('files:all'):,}")
    print(
        "Watched repository records: "
        f"{redis_client.zcard('analysis:watch_counts'):,}"
    )


def clear_project_data():
    """
    Delete keys created by this application without deleting unrelated
    data from the Redis database.
    """
    confirm = input(
        "\nEnter DELETE to remove all project data from Redis: "
    ).strip()

    if confirm != "DELETE":
        print("Clear operation cancelled.")
        return

    patterns = [
        "commit:*",
        "repo:*:commits",
        "author:*:commits",
        "repo:*:languages",
        "file:*",
        "commits:all",
        "languages:repos",
        "licenses:by_repo",
        "files:all",
        "analysis:*",
    ]

    keys_to_delete = set()

    for pattern in patterns:
        for key in redis_client.scan_iter(match=pattern):
            keys_to_delete.add(key)

    if keys_to_delete:
        redis_client.delete(*keys_to_delete)

    print(f"Deleted {len(keys_to_delete)} Redis keys.")


# ---------------------------------------------------------
# Menus
# ---------------------------------------------------------

def import_menu():
    """Display the dataset import menu."""
    while True:
        print(
            """
IMPORT DATA
1. Import Commits.json
2. Import Languages.json
3. Import Licenses.json
4. Import Sample_Repos.json
5. Import Files.json
6. Return to main menu
"""
        )

        choice = input("Select an option: ").strip()

        if choice == "1":
            import_commits()
            pause()
        elif choice == "2":
            import_languages()
            pause()
        elif choice == "3":
            import_licenses()
            pause()
        elif choice == "4":
            import_watched_repositories()
            pause()
        elif choice == "5":
            import_files()
            pause()
        elif choice == "6":
            return
        else:
            print("Invalid option.")


def analysis_menu():
    """Display the analysis menu."""
    while True:
        print(
            """
ANALYSIS FEATURES
1. Programming-language analysis
2. License analysis
3. Most-watched repositories
4. File-extension analysis
5. Repository commit analysis
6. Return to main menu
"""
        )

        choice = input("Select an option: ").strip()

        if choice == "1":
            show_language_analysis()
            pause()
        elif choice == "2":
            show_license_analysis()
            pause()
        elif choice == "3":
            show_watched_repositories()
            pause()
        elif choice == "4":
            show_file_extension_analysis()
            pause()
        elif choice == "5":
            search_commits_by_repository()
            pause()
        elif choice == "6":
            return
        else:
            print("Invalid option.")


def main_menu():
    """Display the main application menu."""
    while True:
        print(
            """
==================================================
       GITHUB ARCHIVE REDIS ANALYZER
==================================================
1. Import JSON data
2. Create a commit
3. Read a commit
4. Update a commit
5. Delete a commit
6. Search commits by repository
7. View analysis features
8. View database summary
9. Clear project data
10. Exit
"""
        )

        choice = input("Select an option: ").strip()

        if choice == "1":
            import_menu()
        elif choice == "2":
            create_commit()
            pause()
        elif choice == "3":
            read_commit()
            pause()
        elif choice == "4":
            update_commit()
            pause()
        elif choice == "5":
            delete_commit()
            pause()
        elif choice == "6":
            search_commits_by_repository()
            pause()
        elif choice == "7":
            analysis_menu()
        elif choice == "8":
            show_database_summary()
            pause()
        elif choice == "9":
            clear_project_data()
            pause()
        elif choice == "10":
            print("Application closed.")
            break
        else:
            print("Invalid option. Enter a number from 1 through 10.")


def main():
    """Start the program."""
    print("Starting GitHub Archive Redis Analyzer...")
    print(f"Dataset folder: {DATA_FOLDER}")

    if not test_redis_connection():
        return

    main_menu()


if __name__ == "__main__":
    main()
