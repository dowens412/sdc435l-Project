# SDC435L GitHub Archive Database Analyzer

## Project Overview

This project is a Python command-line application that uses JSON data from the GitHub Archive dataset.

The application currently includes two database versions:

- Week 1: Redis
- Week 2: MongoDB

Both applications allow the user to import JSON data, perform Create, Read, Update, and Delete operations on commit records, search for repository information, and run analysis features on the dataset.

## Group Members

- David Owens
- Joel Elizee

## Project Structure

```text
sdc435l-Project/
├── data/
│   ├── Commits.json
│   ├── Contents.json
│   ├── Files.json
│   ├── Languages.json
│   ├── Licenses.json
│   ├── Sample_Commits.json
│   ├── Sample_Contents.json
│   ├── Sample_Files.json
│   └── Sample_Repos.json
├── src/
│   ├── redis_app.py
│   └── mongo_app.py
├── SDC435L_Week1_Progress_Report.docx
├── .gitattributes
├── .gitignore
└── README.md
```

## Dataset Format

The dataset uses JSON Lines format. Each line contains one complete JSON object.

The applications read the files one line at a time so that large files do not need to be loaded into memory all at once.

The user can also enter a record limit during an import. This makes it possible to test the program with a smaller amount of data.

## Requirements

The following software is required:

- Python 3
- Git
- Git LFS
- Redis
- MongoDB
- Python `redis` package
- Python `pymongo` package

## Clone the Repository

```bash
git clone https://github.com/dowens412/sdc435l-Project.git
cd sdc435l-Project
```

Because the dataset files use Git LFS, run:

```bash
git lfs install
git lfs pull
```

## Install Python Dependencies

```bash
python3 -m pip install redis pymongo
```

# Week 1: Redis Application

## Redis Overview

The Redis application stores commit information in Redis hashes. Sets and sorted sets are used for repository indexes and analysis results.

## Redis Features

### CRUD Operations

The Redis application allows the user to:

- Create a commit record
- Read a commit by commit ID
- Update an existing commit
- Delete a commit
- Search commits by repository name

### Redis Analysis Features

1. Programming-language analysis
2. License analysis
3. Most-watched repository analysis
4. File-extension analysis
5. Repository commit analysis

### Additional Redis Tools

- Database summary
- Import limits
- Redis connection testing
- Project-data clearing option

## Install and Start Redis on macOS

```bash
brew install redis
brew services start redis
```

Test the connection:

```bash
redis-cli ping
```

A successful connection returns:

```text
PONG
```

## Run the Redis Application

```bash
python3 src/redis_app.py
```

## Redis Data Model

Commit records are stored as Redis hashes:

```text
commit:<commit_id>
```

Repository and author indexes are stored as Redis sets:

```text
commits:all
repo:<repository_name>:commits
author:<author_name>:commits
```

Analysis rankings are stored using Redis sorted sets.

# Week 2: MongoDB Application

## MongoDB Overview

The MongoDB application stores the GitHub Archive records as documents inside separate collections.

The MongoDB database is named:

```text
GitHubArchiveDB
```

The application uses these collections:

```text
commits
languages
licenses
repositories
files
```

## MongoDB CRUD Operations

The MongoDB application allows the user to:

- Create a commit document
- Read a commit by commit ID
- Update an existing commit document
- Delete a commit document
- Search commits by repository name

## MongoDB Analysis Features

The three main Week 2 analysis features are:

1. Longest and shortest repository names
2. Repository watch-count distribution
3. Most common words in commit messages

The application also includes:

- Most-watched repository rankings
- Repository commit searching
- MongoDB database summary

## Install MongoDB on macOS

Add and trust the MongoDB Homebrew tap:

```bash
brew tap mongodb/brew
brew trust mongodb/brew
```

Install MongoDB:

```bash
brew install mongodb-community@8.2
```

Start MongoDB:

```bash
brew services start mongodb-community@8.2
```

Verify the MongoDB version:

```bash
mongod --version
```

Test the Python connection:

```bash
python3 -c "from pymongo import MongoClient; print(MongoClient('mongodb://localhost:27017/').admin.command('ping'))"
```

A successful connection returns:

```text
{'ok': 1.0}
```

## Run the MongoDB Application

```bash
python3 src/mongo_app.py
```

## MongoDB Main Menu

```text
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
```

## Importing Data into MongoDB

Choose option `1` from the main menu.

The import menu includes:

```text
1. Import Commits.json
2. Import Languages.json
3. Import Licenses.json
4. Import Sample_Repos.json
5. Import Files.json
6. Return to main menu
```

For testing, enter a small number such as:

```text
5
```

Press Enter without entering a number to import the complete file.

## Testing MongoDB CRUD Operations

### Create

Choose option `2` and enter the requested commit information.

### Read

Choose option `3` and enter the commit ID.

### Update

Choose option `4`, enter the commit ID, and enter new values.

Press Enter to keep any existing value.

### Delete

Choose option `5`, enter the commit ID, and confirm the deletion.

## Testing MongoDB Analysis Features

Choose option `7` from the main menu.

```text
1. Longest and shortest repository names
2. Repository watch-count distribution
3. Most common words in commit messages
4. Most-watched repositories
5. Repository commit search
6. Return to main menu
```

The related JSON files must be imported before running each analysis.

## Notes

- Redis and MongoDB must be running before their applications are started.
- The JSON dataset files are stored in GitHub using Git LFS.
- Redis and MongoDB data are stored locally and are not included in the Git repository.
- The data can be rebuilt by cloning the repository, downloading the Git LFS files, and importing the JSON files through the applications.
- The import limit is useful when testing large dataset files.

## Course

SDC435L
