# Exam Paper similarity analyzer
The project is written in Python and requires Python 2.7 to be installed. It uses a PostgreSQL background so PostgreSQL 9.4.2 or higher must be installed.

### Dependencies
This project has the following dependencies:

    pip install flask pyparsing sqlalchemy pycurl slate sklearn nltk pandas numpy scipy

For the scraper:

    pip install beautifulsoup

### Configuration
Rename `src/config.py.sample` to `src/config.py` and update the variables inside accordingly. `PAPER_DIR` is a directory to download the exam papers to.

### Database
Connect to PostgreSQL and create the database `exam_papers`

    CREATE DATABASE exam_papers;

And import the database dump in `data/dumps/exam_papers.sql` using the `psql` tool:

    psql -d exam_papers -U username -f data/dumps/exam_papers.sql

#### Troubleshooting
* `pycurl` requires `curl` to be installed.
* `nltk` requires running `nltk.download()` to download it's files. We only use the `english.pickle` but it's not that smart. It may take a while.

### Installing