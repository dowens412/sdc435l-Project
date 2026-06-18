# sdc435l-Project
Python database application using GitHub Archive data
# SDC435L GitHub Archive Redis Analyzer

## Project Overview

This project is a Python command-line application that uses Redis as a NoSQL database to store and analyze JSON data from the GitHub Archive dataset.

The application supports Create, Read, Update, and Delete operations for commit records. It also includes multiple analysis features that demonstrate how Redis can be used to organize, search, and summarize large datasets.

## Features

### CRUD Operations

The application allows the user to:

- Create a new commit record
- Read a commit by commit ID
- Update an existing commit
- Delete a commit
- Search commits by repository name

### Data Import

The application can import JSON Lines data from the following files:

- `Commits.json`
- `Languages.json`
- `Licenses.json`
- `Sample_Repos.json`
- `Files.json`

The user can choose a record limit during each import. This makes it possible to test the application with a small number of records before importing larger amounts of data.

### Analysis Features

The application includes the following analysis features:

1. Programming-language analysis
   - Displays the most common programming languages by total bytes
   - Shows how many repositories use each language

2. License analysis
   - Displays the most common repository licenses
   - Shows the number of repositories using each license

3. Most-watched repository analysis
   - Ranks repositories by watch count

4. File-extension analysis
   - Displays the most common file extensions in the imported file data

5. Repository commit analysis
   - Searches for and displays commits associated with a repository

### Additional Tools

- Redis database summary
- Import limits for large files
- Project-data clearing option
- Redis connection testing
- Git LFS support for large JSON files

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
│   └── app.py
├── SDC435L_Week1_Progress_Report.docx
├── .gitattributes
├── .gitignore
└── README.md
```

## Requirements

The following software is required:

- Python 3
- Redis
- Git
- Git LFS
- Python `redis` package

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/dowens412/sdc435l-Project.git
cd sdc435l-Project
```

### 2. Download the Git LFS files

```bash
git lfs install
git lfs pull
```

### 3. Install Redis on macOS

```bash
brew install redis
```

Start Redis:

```bash
brew services start redis
```

Test the Redis connection:

```bash
redis-cli ping
```

A successful connection should return:

```text
PONG
```

### 4. Install the Python Redis package

```bash
python3 -m pip install redis
```

## Running the Application

From the main project folder, run:

```bash
python3 src/app.py
```

The application will test the Redis connection and display the main menu.

## Main Menu

```text
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
```

## Importing Data

Select option `1` from the main menu.

The application will display:

```text
1. Import Commits.json
2. Import Languages.json
3. Import Licenses.json
4. Import Sample_Repos.json
5. Import Files.json
6. Return to main menu
```

The application asks for a maximum number of records to import.

For testing, enter a small number such as:

```text
5
```

Press Enter without typing a number to import the complete file.

## Testing CRUD Operations

### Create

Choose option `2` and enter the requested commit information.

### Read

Choose option `3` and enter the commit ID.

### Update

Choose option `4`, enter the commit ID, and enter new values. Press Enter to keep an existing value.

### Delete

Choose option `5`, enter the commit ID, and confirm the deletion.

## Testing the Analysis Features

Choose option `7` from the main menu.

The application includes:

```text
1. Programming-language analysis
2. License analysis
3. Most-watched repositories
4. File-extension analysis
5. Repository commit analysis
6. Return to main menu
```

The related JSON data must be imported before running an analysis.

## Redis Data Model

Commit records are stored as Redis hashes using keys such as:

```text
commit:<commit_id>
```

Repository and author indexes are stored as Redis sets:

```text
commits:all
repo:<repository_name>:commits
author:<author_name>:commits
```

Analysis results are stored using Redis hashes and sorted sets.

## Dataset Format

The GitHub Archive files use JSON Lines format. Each line contains one complete JSON object.

The program reads one line at a time so that large files do not need to be loaded into memory all at once.

## Notes

- The JSON files are stored in the GitHub repository using Git LFS because some files are larger than GitHub's standard file-size limit.
- Redis must be running before the application starts.
- The imported Redis data is stored locally and is not included in the zipped project folder.
- Another user can rebuild the Redis data by cloning the repository, downloading the Git LFS files, starting Redis, and importing the JSON records through the application.

## Author

David Owens
Joel Elizee

## Course

SDC435L
