import json
import os
import re
from collections import Counter
from pathlib import Path

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, PyMongoError


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

DATA_FOLDER = Path(__file__).resolve().parent.parent / "data"

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DATABASE_NAME = "GitHubArchiveDB"

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
database = client[DATABASE_NAME]

commits_collection = database["commits"]
languages_collection = database["languages"]
licenses_collection = database["licenses"]
repositories_collection = database["repositories"]
files_collection = database["files"]


# ---------------------------------------------------------
# General helper functions
# ---------------------------------------------------------

def test_mongodb_connection():
    """Test the MongoDB connection before opening the menu."""
    try:
        client.admin.command("ping")
        print("\nConnected to MongoDB successfully.")
        print(f"Database: {DATABASE_NAME}")
        return True
    except ConnectionFailure:
        print("\nCould not connect to MongoDB.")
        print("Make sure MongoDB is running, then try again.")
        return False


def read_json_lines(file_path, limit=None):
    """Read a JSON Lines file one record at a time."""
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
    """Ask how many records should be imported."""
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


def confirm_file_exists(file_path):
    """Confirm that a dataset file exists before importing it."""
    if not file_path.exists():
        print(f"\nFile not found: {file_path}")
        print(
            "Make sure the Git repository was cloned correctly and "
            "run 'git lfs pull' if needed."
        )
        return False

    return True


def pause():
    """Pause before returning to a menu."""
    input("\nPress Enter to return to the menu...")


def normalize_repo_name(value):
    """Convert repository-name values into one string."""
    if isinstance(value, list):
        return value[0] if value else ""

    return value or ""


def create_indexes():
    """Create MongoDB indexes used by the application."""
    commits_collection.create_index(
        [("commit", ASCENDING)],
        unique=True,
        sparse=True,
    )
    commits_collection.create_index([("repo_name", ASCENDING)])
    commits_collection.create_index([("author.name", ASCENDING)])

    languages_collection.create_index(
        [("repo_name", ASCENDING)],
        unique=True,
        sparse=True,
    )
    licenses_collection.create_index(
        [("repo_name", ASCENDING)],
        unique=True,
        sparse=True,
    )
    repositories_collection.create_index(
        [("repo_name", ASCENDING)],
        unique=True,
        sparse=True,
    )
    files_collection.create_index(
        [("id", ASCENDING)],
        unique=True,
        sparse=True,
    )


# ---------------------------------------------------------
# Import functions
# ---------------------------------------------------------

def import_commits():
    """Import commit documents from Commits.json."""
    file_path = DATA_FOLDER / "Commits.json"

    if not confirm_file_exists(file_path):
        return

    limit = get_import_limit()
    inserted = 0
    updated = 0

    for record in read_json_lines(file_path, limit):
        commit_id = record.get("commit")

        if not commit_id:
            continue

        record["repo_name"] = normalize_repo_name(record.get("repo_name"))

        result = commits_collection.update_one(
            {"commit": commit_id},
            {"$set": record},
            upsert=True,
        )

        if result.upserted_id is not None:
            inserted += 1
        elif result.modified_count > 0:
            updated += 1

    print(
        f"\nCommit import complete. "
        f"Inserted: {inserted}, Updated: {updated}."
    )


def import_languages():
    """Import repository language documents from Languages.json."""
    file_path = DATA_FOLDER / "Languages.json"

    if not confirm_file_exists(file_path):
        return

    limit = get_import_limit()
    inserted = 0
    updated = 0

    for record in read_json_lines(file_path, limit):
        repo_name = record.get("repo_name")

        if not repo_name:
            continue

        result = languages_collection.update_one(
            {"repo_name": repo_name},
            {"$set": record},
            upsert=True,
        )

        if result.upserted_id is not None:
            inserted += 1
        elif result.modified_count > 0:
            updated += 1

    print(
        f"\nLanguage import complete. "
        f"Inserted: {inserted}, Updated: {updated}."
    )


def import_licenses():
    """Import repository license documents from Licenses.json."""
    file_path = DATA_FOLDER / "Licenses.json"

    if not confirm_file_exists(file_path):
        return

    limit = get_import_limit()
    inserted = 0
    updated = 0

    for record in read_json_lines(file_path, limit):
        repo_name = record.get("repo_name")

        if not repo_name:
            continue

        result = licenses_collection.update_one(
            {"repo_name": repo_name},
            {"$set": record},
            upsert=True,
        )

        if result.upserted_id is not None:
            inserted += 1
        elif result.modified_count > 0:
            updated += 1

    print(
        f"\nLicense import complete. "
        f"Inserted: {inserted}, Updated: {updated}."
    )


def import_repositories():
    """Import repository watch-count documents from Sample_Repos.json."""
    file_path = DATA_FOLDER / "Sample_Repos.json"

    if not confirm_file_exists(file_path):
        return

    limit = get_import_limit()
    inserted = 0
    updated = 0

    for record in read_json_lines(file_path, limit):
        repo_name = record.get("repo_name")

        if not repo_name:
            continue

        try:
            record["watch_count"] = int(record.get("watch_count", 0))
        except (TypeError, ValueError):
            record["watch_count"] = 0

        result = repositories_collection.update_one(
            {"repo_name": repo_name},
            {"$set": record},
            upsert=True,
        )

        if result.upserted_id is not None:
            inserted += 1
        elif result.modified_count > 0:
            updated += 1

    print(
        f"\nRepository import complete. "
        f"Inserted: {inserted}, Updated: {updated}."
    )


def import_files():
    """Import file documents from Files.json."""
    file_path = DATA_FOLDER / "Files.json"

    if not confirm_file_exists(file_path):
        return

    limit = get_import_limit()
    inserted = 0
    updated = 0

    for record in read_json_lines(file_path, limit):
        file_id = record.get("id")

        if not file_id:
            continue

        result = files_collection.update_one(
            {"id": file_id},
            {"$set": record},
            upsert=True,
        )

        if result.upserted_id is not None:
            inserted += 1
        elif result.modified_count > 0:
            updated += 1

    print(
        f"\nFile import complete. "
        f"Inserted: {inserted}, Updated: {updated}."
    )


# ---------------------------------------------------------
# CRUD operations for commit documents
# ---------------------------------------------------------

def create_commit():
    """Create a new commit document."""
    print("\nCREATE COMMIT")

    commit_id = input("Commit ID: ").strip()

    if not commit_id:
        print("Commit ID is required.")
        return

    if commits_collection.find_one({"commit": commit_id}):
        print("A commit with that ID already exists.")
        return

    document = {
        "commit": commit_id,
        "author": {
            "name": input("Author name: ").strip(),
            "email": input("Author email: ").strip(),
        },
        "committer": {
            "name": input("Committer name: ").strip(),
            "email": input("Committer email: ").strip(),
        },
        "repo_name": input("Repository name: ").strip(),
        "subject": input("Subject: ").strip(),
        "message": input("Message: ").strip(),
        "tree": input("Tree ID: ").strip(),
        "parent": [input("Parent commit ID: ").strip()],
    }

    try:
        commits_collection.insert_one(document)
        print("Commit created successfully.")
    except PyMongoError as error:
        print(f"Could not create the commit: {error}")


def display_commit(document):
    """Display one commit document."""
    if not document:
        print("Commit not found.")
        return

    author = document.get("author") or {}
    committer = document.get("committer") or {}

    print("\nCOMMIT DETAILS")
    print(f"Commit ID:       {document.get('commit', '')}")
    print(f"Repository:      {document.get('repo_name', '')}")
    print(f"Author:          {author.get('name', '')}")
    print(f"Author email:    {author.get('email', '')}")
    print(f"Committer:       {committer.get('name', '')}")
    print(f"Committer email: {committer.get('email', '')}")
    print(f"Subject:         {document.get('subject', '')}")
    print(f"Message:         {document.get('message', '')}")
    print(f"Tree:            {document.get('tree', '')}")
    print(f"Parent:          {document.get('parent', '')}")


def read_commit():
    """Read a commit document by commit ID."""
    print("\nREAD COMMIT")
    commit_id = input("Enter the commit ID: ").strip()

    document = commits_collection.find_one(
        {"commit": commit_id},
        {"_id": 0},
    )

    display_commit(document)


def update_commit():
    """Update an existing commit document."""
    print("\nUPDATE COMMIT")
    commit_id = input("Enter the commit ID: ").strip()

    current = commits_collection.find_one({"commit": commit_id})

    if not current:
        print("Commit not found.")
        return

    print("Press Enter to keep the current value.")

    current_author = current.get("author") or {}
    current_committer = current.get("committer") or {}

    repository = input(
        f"Repository [{current.get('repo_name', '')}]: "
    ).strip()
    author_name = input(
        f"Author name [{current_author.get('name', '')}]: "
    ).strip()
    author_email = input(
        f"Author email [{current_author.get('email', '')}]: "
    ).strip()
    committer_name = input(
        f"Committer name [{current_committer.get('name', '')}]: "
    ).strip()
    committer_email = input(
        f"Committer email [{current_committer.get('email', '')}]: "
    ).strip()
    subject = input(
        f"Subject [{current.get('subject', '')}]: "
    ).strip()
    message = input(
        f"Message [{current.get('message', '')}]: "
    ).strip()

    update_data = {
        "repo_name": repository or current.get("repo_name", ""),
        "author.name": author_name or current_author.get("name", ""),
        "author.email": author_email or current_author.get("email", ""),
        "committer.name": (
            committer_name or current_committer.get("name", "")
        ),
        "committer.email": (
            committer_email or current_committer.get("email", "")
        ),
        "subject": subject or current.get("subject", ""),
        "message": message or current.get("message", ""),
    }

    result = commits_collection.update_one(
        {"commit": commit_id},
        {"$set": update_data},
    )

    if result.modified_count > 0:
        print("Commit updated successfully.")
    else:
        print("No changes were made.")


def delete_commit():
    """Delete one commit document."""
    print("\nDELETE COMMIT")
    commit_id = input("Enter the commit ID: ").strip()

    document = commits_collection.find_one({"commit": commit_id})

    if not document:
        print("Commit not found.")
        return

    confirm = input(
        f"Delete commit {commit_id}? Enter Y to confirm: "
    ).strip().lower()

    if confirm != "y":
        print("Delete cancelled.")
        return

    result = commits_collection.delete_one({"commit": commit_id})

    if result.deleted_count == 1:
        print("Commit deleted successfully.")
    else:
        print("The commit could not be deleted.")


def search_commits_by_repository():
    """Search commit documents by repository name."""
    print("\nSEARCH COMMITS BY REPOSITORY")

    repo_name = input(
        "Enter the full repository name, such as owner/project: "
    ).strip()

    documents = list(
        commits_collection.find(
            {"repo_name": repo_name},
            {
                "_id": 0,
                "commit": 1,
                "author.name": 1,
                "subject": 1,
            },
        ).limit(20)
    )

    if not documents:
        print("No commits were found for that repository.")
        return

    print(f"\nFound {len(documents)} commit(s) for {repo_name}:")

    for document in documents:
        author = document.get("author") or {}

        print(
            f"- {document.get('commit', '')[:12]} | "
            f"{author.get('name', 'Unknown')} | "
            f"{document.get('subject', '')}"
        )


# ---------------------------------------------------------
# Analysis feature 1: repository-name lengths
# ---------------------------------------------------------

def show_repository_name_analysis():
    """Display the longest and shortest repository names."""
    print("\nREPOSITORY NAME LENGTH ANALYSIS")

    pipeline = [
        {
            "$match": {
                "repo_name": {
                    "$exists": True,
                    "$type": "string",
                    "$ne": "",
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "repo_name": 1,
                "name_length": {"$strLenCP": "$repo_name"},
            }
        },
        {"$sort": {"name_length": 1, "repo_name": 1}},
    ]

    results = list(repositories_collection.aggregate(pipeline))

    if not results:
        print(
            "No repository data found. "
            "Import Sample_Repos.json first."
        )
        return

    shortest = results[0]
    longest = results[-1]

    print(
        f"Shortest repository name: {shortest['repo_name']} "
        f"({shortest['name_length']} characters)"
    )
    print(
        f"Longest repository name: {longest['repo_name']} "
        f"({longest['name_length']} characters)"
    )


# ---------------------------------------------------------
# Analysis feature 2: watch-count distribution
# ---------------------------------------------------------

def show_watch_count_distribution():
    """Display repositories grouped into watch-count ranges."""
    print("\nWATCH-COUNT DISTRIBUTION")

    pipeline = [
        {
            "$bucket": {
                "groupBy": "$watch_count",
                "boundaries": [0, 100, 1000, 10000, 100000, 1000000],
                "default": "1,000,000+",
                "output": {
                    "repository_count": {"$sum": 1},
                    "examples": {"$push": "$repo_name"},
                },
            }
        }
    ]

    results = list(repositories_collection.aggregate(pipeline))

    if not results:
        print(
            "No repository watch data found. "
            "Import Sample_Repos.json first."
        )
        return

    labels = {
        0: "0-99",
        100: "100-999",
        1000: "1,000-9,999",
        10000: "10,000-99,999",
        100000: "100,000-999,999",
        "1,000,000+": "1,000,000+",
    }

    for result in results:
        label = labels.get(result["_id"], str(result["_id"]))
        examples = result.get("examples", [])[:3]

        print(
            f"{label} watchers: "
            f"{result.get('repository_count', 0)} repositories"
        )

        if examples:
            print(f"  Examples: {', '.join(examples)}")


# ---------------------------------------------------------
# Analysis feature 3: common commit-message words
# ---------------------------------------------------------

def show_common_commit_words():
    """Display the most common meaningful words in commit messages."""
    print("\nMOST COMMON COMMIT-MESSAGE WORDS")

    stop_words = {
        "a", "an", "and", "are", "as", "at", "be", "by", "for",
        "from", "has", "in", "is", "it", "of", "on", "or", "that",
        "the", "this", "to", "was", "were", "with",
    }

    word_counts = Counter()

    cursor = commits_collection.find(
        {"message": {"$exists": True, "$type": "string"}},
        {"_id": 0, "message": 1},
    )

    for document in cursor:
        message = document.get("message", "").lower()
        words = re.findall(r"[a-zA-Z]{3,}", message)

        for word in words:
            if word not in stop_words:
                word_counts[word] += 1

    if not word_counts:
        print("No commit messages found. Import Commits.json first.")
        return

    print("\nTop 10 words:")

    for position, (word, count) in enumerate(
        word_counts.most_common(10),
        start=1,
    ):
        print(f"{position}. {word}: {count}")


# ---------------------------------------------------------
# Additional analysis and database tools
# ---------------------------------------------------------

def show_top_watched_repositories():
    """Display the ten most-watched repositories."""
    print("\nMOST-WATCHED REPOSITORIES")

    documents = repositories_collection.find(
        {},
        {"_id": 0, "repo_name": 1, "watch_count": 1},
    ).sort("watch_count", DESCENDING).limit(10)

    found = False

    for position, document in enumerate(documents, start=1):
        found = True
        print(
            f"{position}. {document.get('repo_name', '')}: "
            f"{document.get('watch_count', 0):,} watchers"
        )

    if not found:
        print(
            "No repository watch data found. "
            "Import Sample_Repos.json first."
        )


def show_database_summary():
    """Display the number of documents in each collection."""
    print("\nDATABASE SUMMARY")
    print(
        f"Commit documents: "
        f"{commits_collection.count_documents({}):,}"
    )
    print(
        f"Language documents: "
        f"{languages_collection.count_documents({}):,}"
    )
    print(
        f"License documents: "
        f"{licenses_collection.count_documents({}):,}"
    )
    print(
        f"Repository documents: "
        f"{repositories_collection.count_documents({}):,}"
    )
    print(
        f"File documents: "
        f"{files_collection.count_documents({}):,}"
    )


def clear_project_database():
    """Delete all documents created by this application."""
    confirm = input(
        "\nEnter DELETE to remove all project documents from MongoDB: "
    ).strip()

    if confirm != "DELETE":
        print("Clear operation cancelled.")
        return

    collections = [
        commits_collection,
        languages_collection,
        licenses_collection,
        repositories_collection,
        files_collection,
    ]

    total_deleted = 0

    for collection in collections:
        result = collection.delete_many({})
        total_deleted += result.deleted_count

    print(f"Deleted {total_deleted} MongoDB documents.")


# ---------------------------------------------------------
# Menus
# ---------------------------------------------------------

def import_menu():
    """Display the MongoDB import menu."""
    while True:
        print(
            """
IMPORT DATA INTO MONGODB
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
            import_repositories()
            pause()
        elif choice == "5":
            import_files()
            pause()
        elif choice == "6":
            return
        else:
            print("Invalid option.")


def analysis_menu():
    """Display the MongoDB analysis menu."""
    while True:
        print(
            """
MONGODB ANALYSIS FEATURES
1. Longest and shortest repository names
2. Repository watch-count distribution
3. Most common words in commit messages
4. Most-watched repositories
5. Repository commit search
6. Return to main menu
"""
        )

        choice = input("Select an option: ").strip()

        if choice == "1":
            show_repository_name_analysis()
            pause()
        elif choice == "2":
            show_watch_count_distribution()
            pause()
        elif choice == "3":
            show_common_commit_words()
            pause()
        elif choice == "4":
            show_top_watched_repositories()
            pause()
        elif choice == "5":
            search_commits_by_repository()
            pause()
        elif choice == "6":
            return
        else:
            print("Invalid option.")


def main_menu():
    """Display the MongoDB application menu."""
    while True:
        print(
            """
==================================================
      GITHUB ARCHIVE MONGODB ANALYZER
==================================================
1. Import JSON data
2. Create a commit
3. Read a commit
4. Update a commit
5. Delete a commit
6. Search commits by repository
7. View analysis features
8. View database summary
9. Clear MongoDB project data
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
            clear_project_database()
            pause()
        elif choice == "10":
            print("Application closed.")
            break
        else:
            print("Invalid option. Enter a number from 1 through 10.")


def main():
    """Start the MongoDB application."""
    print("Starting GitHub Archive MongoDB Analyzer...")
    print(f"Dataset folder: {DATA_FOLDER}")

    if not test_mongodb_connection():
        return

    create_indexes()
    main_menu()


if __name__ == "__main__":
    main()
