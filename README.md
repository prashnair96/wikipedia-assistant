# Introduction & Overview

This project implements a Wikipedia Assistant based on the Simple English Wikipedia dataset. It involves building a comprehensive database containing metadata about Wikipedia pages—including page titles, categories, last modification dates—and the intricate web of links between these pages. The core objective is to identify “outdated” pages within categories by comparing modification dates between pages and the pages they reference.

To ensure the database remains current, a monthly automated pipeline downloads and preprocesses the latest Wikipedia dumps. This pipeline is scheduled using cron, chosen for its straightforward setup and dependable execution in the deployment environment. Although containerization tools like Docker were considered, the application currently runs directly on the host system to maintain simplicity and reduce operational overhead.

The system exposes a RESTful API with two key endpoints: one allows execution of arbitrary SQL queries on the database, and the other returns the most outdated page within a given category. For performance, the outdated-page queries are precomputed monthly for the top 10 categories by page count.

The entire application is deployed on a free cloud provider to facilitate ease of access and scalability. All code, preprocessing scripts, and documentation—including design decisions and simplifications—are openly shared to promote transparency and reproducibility.

# Key Features

- Comprehensive Wikipedia Database: Stores page titles, categories, last modification dates, and detailed inter-page link data including link order on the referring page.
- Outdated Page Detection: Identifies pages as outdated if any referenced page has a more recent modification date, calculating the maximum lag.
- RESTful API with Two Endpoints:
    - Execute arbitrary SQL queries on the database.
    - Retrieve the most outdated page in a specified category (precomputed for the top 10 categories).
- Monthly Automated Pipeline:
    - Downloads and preprocesses updated Wikipedia dumps.
    - Calculates outdated pages for top categories.
    - Scheduled using cron for reliability and simplicity.
-   Direct Host Deployment: Runs natively without containerization to reduce complexity and overhead.
-   Cloud Deployment: Hosted on a free cloud platform ensuring availability and scalability.
-   Open Source & Documentation: Complete codebase, preprocessing scripts, and documentation provided, including explanations for design choices and simplifications.

# Links

- [GitHub Repository](https://github.com/prashnair96/wikipedia-assistant)
- [Deployed API URL](https://wikipedia-assistant.onrender.com)
- [Postman Tests](https://app.getpostman.com/join-team?invite_code=db51400d1ff78ef6ffae929c25bd44816b8b3ed9966c0badc83e54571bad7c29&target_code=fce0bbea7b93945ee4e31e35eb885a46)


Note: Downloaded data files (`simplewiki-latest-categorylinks.sql`, `simplewiki-latest-page.sql` and `simplewiki-latest-pages-articles.xml.bz2`),  were not able to be pushed to Github repo due to huge size. However the `setup.sh` wrapper script - which will covered in detail later on , always downloads the latest dumps, hence not an issue


# Wikipedia Assistant — Local Development Environment Setup

This section outlines the steps to set up a consistent, isolated local development environment for the Wikipedia Assistant project on **macOS, Windows, and Linux**. This setup ensures easy dependency management, reproducibility, and smooth deployment preparation.

---

## 1. Prerequisites: Install Essential Tools

### macOS (Apple Silicon M1/M2/M4)

1. Install Homebrew (macOS package manager):

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

2. Add Homebrew to your shell environment:

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

3. Verify Homebrew installation:

```bash
brew --version
```

4. Install Python and PostgreSQL:

```bash
brew install python postgresql
```

---

### Windows (10/11)

1. Install Chocolatey (Windows package manager). Run PowerShell as Administrator and execute:

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; `
[System.Net.ServicePointManager]::SecurityProtocol = `
[System.Net.ServicePointManager]::SecurityProtocol -bor 3072; `
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

2. Install Python and PostgreSQL:

```powershell
choco install python postgresql
```

---

### Linux (Ubuntu/Debian)

1. Update packages:

```bash
sudo apt update && sudo apt upgrade -y
```

2. Install Python and PostgreSQL:

```bash
sudo apt install -y python3 python3-venv python3-pip postgresql
```

3. Start and enable PostgreSQL services:

```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

---

## 2. Create Project Directory and Python Virtual Environment

1. Create your project folder and navigate into it:

```bash
mkdir wikipedia-assistant
cd wikipedia-assistant
```

2. Create a Python virtual environment:

```bash
python3 -m venv venv
```

3. Activate the virtual environment:

* macOS/Linux:

```bash
source venv/bin/activate
```

* Windows PowerShell:

```powershell
venv\Scripts\Activate.ps1
```

---

## 3. Install Python Dependencies and Generate `requirements.txt`

With the virtual environment activated, run:

```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary mwparserfromhell requests beautifulsoup4 lxml python-dotenv
pip freeze > requirements.txt
```

---

## 4. Initialize Git Repository and Create `.gitignore`

Initialize Git:

```bash
git init
```

Create a `.gitignore` file with the following content:

```
venv/
__pycache__/
*.py[cod]
.vscode/
.DS_Store
*.log
```

Add and commit files:

```bash
git add .
git commit -m "Initial project setup with virtual environment and dependencies"
```

---

## 5. Start PostgreSQL Server

* macOS:

```bash
brew services start postgresql
```

* Windows:
  Start PostgreSQL from Services app or run in PowerShell (adjust the path as needed):

```powershell
pg_ctl start -D "C:\Program Files\PostgreSQL\<version>\data"
```

* Linux:

```bash
sudo systemctl start postgresql
```

---

## 6. Connect to PostgreSQL and Create Database

Open the PostgreSQL shell:

```bash
psql -d postgres
```

Create your project database (replace username and database name accordingly):

```sql
CREATE DATABASE wikipedia;
```

---

## 7. Prepare Your `.env` File

Create a `.env` file in the project root with the following variables:

```env
DB_USER=your_postgres_username
DB_PASSWORD=your_postgres_password
DB_NAME=wikipedia
DB_HOST=localhost
DB_PORT=5432
DATABASE_URL=postgresql://your_postgres_username:your_postgres_password@localhost:5432/wikipedia
```

---

## 8. Usage Notes

* Always activate your virtual environment before working:

  * macOS/Linux:

  ```bash
  source venv/bin/activate
  ```

  * Windows PowerShell:

  ```powershell
  venv\Scripts\Activate.ps1
  ```

* To exit the virtual environment:

```bash
deactivate
```

* Do **not** commit the `venv` directory to Git.

* Use `requirements.txt` to install dependencies on other machines:

```bash
pip install -r requirements.txt
```

* Windows users may find running setup scripts via **PowerShell** or **Windows Subsystem for Linux (WSL)** helpful for compatibility.





# Wikipedia Assistant - DB Layer


## 1. Database tables schema definition and table creation
Relevant tables required for this assignment are created, where the tables are the following:

- `pages`: Store essential metadata for each Wikipedia page (id, title, last_modified_date). 
- `categories`: Associate pages with one or more category labels (page_id, category_name); An index on category_name for faster queries
- `links`: Store internal links between pages and their order (source_page_id, target_page_id, link_index); And adds indexes on both page IDs for performance.

Schemas are in `app/db/models.py`
Tables are then created in `app/db/init_db.py`


Note: Foreign keys are enforced where possible.


## 2. ETL Scripts to Parse and Load Data

Pre-requisites -
The following Simple English Wikipedia Dumps have been downloaded and are in the `data/` folder (has been automated in final setup.sh later on):
| File Name                                  | Purpose                            |
| ------------------------------------------ | ---------------------------------- |
| `simplewiki-latest-pages-articles.xml.bz2` | Main dump of all page content      |
| `simplewiki-latest-page.sql.gz`            | Metadata about pages (IDs, titles) |
| `simplewiki-latest-categorylinks.sql.gz`   | Links between pages and categories |


### ETL Flow:  parse_sql.py --> parse_xml.py --> load.py


### Scripts overview


`parse_sql.py`:
- Extract key metadata from SQL dumps to support later parsing and database loading steps.


**What It Parses**

1. `simplewiki-latest-page.sql`
    - Extracts:
        - page_id
        - namespace
        - title
- Keeps only pages in main namespace (namespace == 0)
- Builds: title_to_id dictionary (e.g., "Albert Einstein" → 12345)

2. `simplewiki-latest-categorylinks.sql`
- Extracts:
    - page_id
    - category_name
- Builds: page_to_categories dictionary (e.g., 12345 → ["Physicists", "Nobel laureates"])

Outputs:
- `title_to_id.pkl`: A pickle file mapping page titles → page IDs
- `page_categories.pkl`: A pickle file mapping page IDs → categories


**Simplifications made**:

1. The code was modified to include the argument errors='ignore' when opening the SQL file for reading.

Why was this done?
- The original SQL files might contain some characters or byte sequences that aren't valid UTF-8 or cause decoding errors.
- Without errors='ignore', Python will raise a UnicodeDecodeError and stop reading the file when it encounters these invalid characters.
- Adding errors='ignore' tells Python to skip over any invalid or malformed byte sequences silently instead of raising an exception.

What does this simplify?
- It makes the file reading more robust and fault-tolerant.
- The parser can continue processing the entire file without crashing due to a few bad characters.
- avoid adding extra code to handle encoding errors explicitly.


`parse_xml.py`:

- Loads a title-to-ID mapping from a title_to_id.pkl pickle file.
- Parses a compressed Wikipedia XML dump (simplewiki-latest-pages-articles.xml.bz2) using xml.etree.ElementTree.iterparse in streaming mode.
- Extracts valid article pages from the main namespace (ns=0) only.
- Extracts internal wiki links using mwparserfromhell from the wikitext of each article.
- Maps links to known page IDs using the loaded title_to_id dictionary.
- Processes each page in parallel using ThreadPoolExecutor to speed up link parsing.
- Writes the parsed result to a pages_data.pkl pickle file.

Output:
- pickle file `pages_data.pkl` containing a list of dictionaries, one per article page, with the following structure:



**Simplifications and Improvements made**:

1. Memory-efficient streaming XML parsing
    - Uses ElementTree.iterparse() with 'end' events to process large XML dumps incrementally.
    - Avoids loading the entire XML into memory, which is crucial for multi-GB dumps.
    - Calls elem.clear() after each page to free memory immediately.
2. Namespace-aware parsing
    - XML elements are parsed using a namespace dictionary (ns) for clarity and maintainability.
3. Robust element validation
    - Ensures required tags (title, namespace, revision, timestamp, text) exist before processing.
    - Filters to namespace ns=0 to exclude non-article content (like user, talk, or meta pages).
4. Fault-tolerant processing
    - Each page is wrapped in a try/except block to skip malformed or incomplete pages without crashing the entire run.
5. Parallel link extraction
    - Uses Python’s ThreadPoolExecutor for concurrent parsing of wikitext with mwparserfromhell.
    - Despite the GIL, this works efficiently since mwparserfromhell is implemented in C and releases the GIL during parsing.
6. Accurate internal link resolution
    - Uses mwparserfromhell to extract true internal links, avoiding brittle regex approaches.
    - Filters out non-content or special links (e.g., ones containing :).
    - Converts link titles to IDs using the preloaded title_to_id mapping.
7. Transparent compressed file handling
    - Uses bz2.open() directly, avoiding the need for manual decompression before parsing.

`load.py`:

The script loads structured Wikipedia page data into a database using SQLAlchemy ORM. Specifically, it:

1. Reads data from pickle files containing:
    - Page information (pages_data.pkl)
    - Page-to-category mappings (page_categories.pkl)
    - (Unused here, but loaded) title-to-ID mapping (title_to_id.pkl)
2. Connects to the database using a URL stored in environment variables (DATABASE_URL).
3. Inserts or updates pages and their categories in the database, ensuring each page and its categories are stored.
4. Inserts links between pages—representing connections from one page to another—only if the target page exists in the loaded data.
5. Handles foreign key constraints properly by committing pages and categories before inserting links to prevent database errors.
6. Reports how many links were skipped because their target pages were missing.


**Simplifications made**:

1. Two-phase commit:
    - Before: Pages, categories, and links were all merged in one loop before committing. This caused foreign key violations because links reference pages that weren't yet committed in the DB.
    - Now: Pages and categories are inserted and committed first so the DB knows about all pages. Then links are inserted and committed after. This respects foreign key constraints.
2. Session management inside function:
    - Created a local session within load_data and properly closed it in a finally block to avoid session leakage or accidental reuse.
    - This is better practice for resource cleanup.
3. Error handling:
    - Wrapped the session operations in a try-except block to rollback on exceptions and print the error message, which helps with debugging and prevents partial commits.
4. Removed global session:
    -   Instead of a global session instance, create it inside the function — makes the function more reusable and self-contained.
5. Minor readability tweaks:
    - Clear comments, consistent print statements.
    - Using the valid_page_ids set exactly as before to skip invalid links.

**Why is this simpler and better?**:

- Respects DB constraints: The two-step commit approach aligns with how SQL foreign keys enforce integrity.
- More robust: You avoid partial data commits, session leaks, and confusing errors.
- Easier debugging: Clear error handling and no hidden session states.
- Self-contained function: Makes the function reusable and easier to test or modify later.

```bash
Sample output from load.py script:
Loading pickle files...
Loading data into DB...
Data loaded successfully.
Skipped 15 links due to missing target pages.
```
Note: Normal for wiki dataset to skip few links , since not all links will point to known pages.

```sql
SELECT COUNT(*) FROM pages;
 count  
--------
 343524
(1 row)
```


# Wikipedia Assistant - API Layer

This module provides a FastAPI-based API that allows querying and analysis of Wikipedia page data loaded into a PostgreSQL database.

## Features

1. Run SQL Queries Securely
   - Execute read-only SELECT queries through an API endpoint, with protection against unsafe operations.
2. Find Outdated Pages by Category
    - Identify pages in a category whose linked pages are more recently updated — a useful proxy for stale content.
3. Cached Insights for Top Categories
    - Precompute and serve most-outdated pages for popular categories, reducing load and improving response speed.


| Route                                   | Method | Description                                         |
| --------------------------------------- | ------ | --------------------------------------------------- |
| `/query`                                | `POST` | Run a safe SQL `SELECT` query on the DB             |
| `/outdated_page/{category_name}`        | `GET`  | Compute the most outdated page in a category (live) |
| `/cached_outdated_page/{category_name}` | `GET`  | Retrieve precomputed outdated page (fast)           |


## Setup & Run

1. Install Dependencies (should have been already installed at the start, but just in the event that not yet)

```bash
pip install fastapi uvicorn[standard] python-dotenv sqlalchemy psycopg2-binary
```

2. Ensure .env has the DB URL:

```bash
DATABASE_URL=postgresql://username:password@localhost:5432/your_db
```

3. `build_cache.py` – Precomputing Most Outdated Pages

This script analyzes the database to determine, for each of the top 10 most common categories, which page is the most outdated. A page is considered outdated if the pages it links to have a more recent last_modified_date than itself.

## Key Features & Logic:
- Dynamically selects the top 10 categories from the Category table, based on the number of pages in each category.
- For each category, it identifies the page whose linked pages have the greatest positive difference in modification date — meaning the linked pages are more recently updated than the page itself, and the difference is maximal.
- Parallelizes this computation across categories using ThreadPoolExecutor from Python’s concurrent.futures, significantly reducing total runtime.
- The final results are cached into a JSON file (outdated_cache.json), which can be quickly served by the API without hitting the database again.
- Uses efficient querying with SQLAlchemy, leveraging joins and filters, and manages database sessions safely with scoped sessions.
- Designed to be part of an ETL pipeline step that is rerun whenever the Wikipedia dump is refreshed.


4. `main.py` – FastAPI Service for Wiki Data Queries

This script defines the FastAPI web service that exposes two main endpoints for interacting with the preprocessed Wikipedia data:

### `/query` (POST)
- Accepts arbitrary SQL SELECT queries.
- Validates input to ensure only safe `SELECT` statements are run.
- Returns query results as JSON.
- Useful for debugging or advanced analytical queries.

### `/outdated_page/{category_name}` (GET)
- Computes on-the-fly the most outdated page in a given category.
- A page is outdated if its linked pages have been modified more recently.
- Can be slower, since it queries and compares timestamps dynamically.

### `/cached_outdated_page/{category_name}` (GET)
- Returns precomputed outdated page info from `outdated_cache.json`.
- Much faster and more efficient, especially for frequent categories.
- Designed for top 10 categories, as computed in the ETL step (`build_cache.py`).

# Other Features:
- Uses SQLAlchemy ORM to interface with the database.
- Reads environment config (e.g., `DATABASE_URL`) from `.env`.
- Gracefully handles errors (e.g., SQL injection prevention, missing categories).

**Simplifications & Design Choices (API)**
- `build_cache.py`
    - The outdated page computations are parallelized using ThreadPoolExecutor with a fixed thread pool of 4 workers to avoid overloading the database.
    -   Only the top 10 categories (ranked by number of pages) are analyzed, ensuring relevance and manageable compute cost.
    -   Results are stored in a simple JSON cache file (outdated_cache.json) for quick retrieval by the API.
    -   Cache updates are designed to run manually or via scheduled jobs aligned with Wikimedia’s monthly dump frequency, accepting some downtime instead of implementing complex live updates.
    -   Assumes the SQLAlchemy Page model has an out_links relationship, enabling efficient traversal of page link data.

- `main.py`
    - The `/query` endpoint only allows SELECT statements to prevent any accidental or malicious database modifications, improving security.
    - Arbitrary SQL queries are executed directly with minimal validation beyond the SELECT check; this is a tradeoff between flexibility and security, assuming trusted users or further sandboxing could be added.
    - The `/outdated_page/{category_name}` endpoint dynamically computes the most outdated page in real time by querying the database, which can be resource-intensive for large categories.
    - To improve performance, `/cached_outdated_page/{category_name}` returns precomputed results from a JSON cache built by `build_cache.py`.
    - The API uses SQLAlchemy ORM for database access and connection management to simplify database interactions and ensure cleaner code.
    - Error handling is implemented to return appropriate HTTP status codes for invalid queries, missing categories, or internal errors.
    - The API server itself is started separately (e.g., with `uvicorn main:app`), not automatically within this script, to allow more flexible deployment and control.



5. Start the API server:

```bash
uvicorn app.api.main:app --reload
```

Access docs at: http://localhost:8000/docs



## Sample output from URL:

`/query`: select count(*) from pages
```json
{
  "results": [
    {
      "count": 343524
    }
  ]
}
```

`/outdated_page/{category_name}`: category name input --> France

```json
{
  "page_id": 1049466,
  "title": "Climate of France"
}
```

`/cached_outdated_page/{category_name}`: category name input --> Stubs

```json
{
  "page_id": 105819,
  "title": "The Sean Hannity Show"
}
```


# Wikipedia Assistant - Automation of jobs (`setup.sh` for calling all script, `setup_cron.sh` for cron job to execute `setup.sh` to run every month --> 4 AM on 1st of every month )

## Automation setup (wrapper script)
1. `setup.sh` created to run the entire pipeline from dump --> DB --> cache

- Script breakdown:
    1. Create database schemas and tables if not exist
    2. Remove old files `outdated_cache.json`, `title_to_id.pkl` and `page_categories.pkl` if they exist
        -   Justification: We do not want outdated or mismatched data from previous dumps, if not removed, may:
            - Skip re-parsing and reuse old .pkl files.
            - Load incorrect or partial data into the database.
            - Use outdated cache, resulting in incorrect API responses.
    3. `mkdir -p data` ensures the folder exists (no error if it already exists).
    4. `curl -o path/to/file URL` downloads latest dumps from Wikimedia to the given file path instead of the current directory.  
        - Note: This automates the downloads for DB Layer inputs
    5. Check if SQL files are already unzipped, else unzipped
        - Note: When earlier manually downloaded, found that the files were auto-unzipped
    6. Parse SQL dumps - runs `parse_sql.py`
    7. Parse XML dumps - runs `parse_xml.py`
    8. Load data to database - runs `load.py`
    9. Build outdated page cache - runs `build_cache.py`


## To run the script

1. Make the script executable

```bash
chmod +x setup.sh
```

2. Then run automation script
 
 ```bash
./setup.sh
```




## Automation setup (cron wrapper script)
`setup_cron.sh` orchestrates the full monthly ETL pipeline using fresh Simple English Wikipedia dumps. It calls the wrapper `setup.sh` script to ensure the database schema exists, cleans old files, downloads new content, parses and loads it, and precomputes the cache of outdated pages for the top 10 categories. Designed for cron automation with robust timestamped logging. It is scheduled to run at 4:00 AM on the 1st of every month, in line with the Wikimedia dump release schedule.


- Script breakdown:
1. Define paths and filenames
    - Sets environment variables with full paths for:
    - Project root
    - Log directory
    - Cron job definition file
    - Script to be run by cron (setup.sh)
    - Output log file for cron job
2. `mkdir -p "$LOG_DIR"`
    - Creates the logs/ directory if it doesn't already exist.
    - Ensures that the log file's parent directory exists when cron tries to write to it.
3. Write a cron job to the crontab file and append all output (including errors) to `logs/wiki_etl.log` (Useful for verifying job status or diagnosing failures)
    - Actual: `"0 4 1 * * $SETUP_SCRIPT >> $LOG_FILE 2>&1" > "$CRON_FILE"` , Run at 4:00 AM on the 1st of every month
    - Test (Commented out): `"10 23 * * * /$SETUP_SCRIPT > $LOG_FILE 2>&1" > "$CRON_FILE"` , Run at 11.10 pm on 19 June 2025 for testing purposes
4. Install the crontab - `crontab "$CRON_FILE"`
    - Installs the cron job defined in crontab.txt into the current user’s crontab.
    - After this, cron will know to run setup.sh at the specified schedule.
5. Show installed cron jobs
    - `crontab -l` help displays the currently installed cron jobs for verification.



## Important things to note

1. Use full python path of virtual environment (can find via `which python3`)
2. cd to project root folder at the start
3. create setup_cron.sh at project root directory:
4. Make setup_cron.sh executable, `chmod +x setup_cron.sh`
5. Create logs folder for cron job, `mkdir -p /full/path/to/your/project/logs`
6. then run it - `./setup_cron.sh` (Note: Windows users should run this script inside Git Bash or WSL to ensure compatibility.)



## Why `cron` is used

- Simplicity: Ideal for time-based, infrequent jobs (in this case: once, at the start of every month)
- Reliability: Mature tool built into UNIX-based systems
- Transparency: Easy to inspect the crontab and job logs
- No overhead: No need for heavier orchestration tools like Airflow or Prefect



# Wikipedia Assistant - Pytest

Pytest is important because it automates testing, helps catch bugs early, ensures code changes don’t break functionality, and improves overall code quality. It also serves as documentation, supports collaboration, and fits well into automated workflows.

`test_outdated.py` created under the `\tests` folder.

## What `test_outdated.py` Test

The `test_outdated.py` script verifies the correctness of the logic used to compute the most outdated Wikipedia page for a given category.

It includes unit tests for the key components of the outdated-page computation pipeline:

### 1. `compute_outdated_page()`

* **Test when no pages exist** for a given category — ensures the function safely returns `None` without errors.
* **Test when an outdated page exists** — checks that the function correctly identifies the most outdated page based on the time difference between the page and the newest linked page.

### 2. `main()`

* Mocks the top categories and simulates outdated-page computation.
* Confirms that the results are written to a cache file and that all categories are processed correctly.
* Ensures integration between DB queries, computation, and file writing.

---

## Logging

Test execution is logged to `tests/logs/test_outdated_mock.log` for debugging and submission purposes.

---

## Output from tests (from log file)
...========================= 3 passed, 1 warning in 0.12s =========================...


## Important
1. `pip install pytest` then `pip freeze > requirements.txt` to be run in sequence to install pytest and record in requirements.txt
2. `pytest.ini` file created to gelp pyteste add current directory to the sys.path
3. Create logs directory for test output: `mkdir -p tests/logs`
4. Command for running pytest and outputting to log file: `pytest /path/to/tests/test_outdated.py > /path/to/tests/logs/pytest_output.log 2>&1`


# Wikipedia Assistant - Deployment & Collaboration

## Collaboration ease
Makefile in root folder:
- Creating a Makefile is a great way to simplify repetitive tasks like setting up your environment, running your app, and executing your ETL pipeline. It works like a simple command-line interface that other developers (or you later!) can use with a single command.

- Includes commands to execute, can refer to help section on how to run essential scrips, like requirements.txt , run API and run setup.sh (etl script)
 
### Why This Works Well
- Consistency: make run-etl is simpler than remembering bash setup.sh.
- Portability: Other developers just run make run-etl — no guesswork.
- Maintainability: You can expand the Makefile later (e.g., make deploy).


## Cloud Provider Decision: Render

In deploying this application, I chose **Render** as my cloud provider for several reasons, but I also encountered tradeoffs and limitations with other platforms. 

### Deployment in Render

- **Database**: PostgreSQL (hosted on Render)
- **Environment Variables**: The application uses `DATABASE_URL` to connect to the PostgreSQL database


### Summary of the considerations:

#### Why I Chose Render:
Render provided the best combination of ease-of-use, **fully managed PostgreSQL** database, and **automatic deployment** from GitHub. Render also offered a **free tier** for both **web services** and **PostgreSQL databases**, which was a great starting point for this project.

- **Managed PostgreSQL**: Render's PostgreSQL setup is easy to configure and provides a **free database tier**, which suits my needs for a small-scale project.
- **Automatic Deployment from GitHub**: Integration with GitHub was seamless, allowing me to automatically deploy updates whenever I push changes to my GitHub repository.
- **Transparent Pricing**: Render offers clear pricing with predictable costs. When scaling the app, I will have an easy time understanding the expenses.

#### Tradeoff with Cron Jobs:
A key feature that I **sacrificed** due to **cost** is **scheduled cron jobs**. **Render’s free tier** does not support cron jobs, and implementing them requires **additional payment**. Since I did not want to incur these extra costs for a small project, cron jobs for scheduled tasks are not available in my current setup.

#### Why Not Other Cloud Providers?

1. **Heroku**:
   - Initially, I considered **Heroku**, which is well-known for ease of use and its free tier, but I was unable to access the **free PostgreSQL tier** on Heroku. They only offered limited plans or required payment for a managed database, which didn’t fit the budget for this project.

2. **Railway**:
   - **Railway** provided a great experience with easy setup, but their **free tier** was limited to deploying only **databases**, and I couldn’t use their **web hosting** services with a free plan.
   - Additionally, the **free PostgreSQL database** offered on Railway had some limitations, such as limited storage and performance, making it difficult to scale as the project grows.

3. **Fast.io**:
   - I also explored **Fast.io**, but unfortunately, their deployment process encountered issues. During the middle of the deployment, the service failed and reverted back to the **initial state**, which caused a lot of frustration.
   - The platform seems promising for simple deployments but did not work well for this project’s requirements.

#### Summary:
In conclusion, I opted for **Render** due to its **managed PostgreSQL support**, **ease of use**, and **seamless integration with GitHub**. While the absence of **cron jobs** in the free tier is a limitation, it is a tradeoff I made to keep costs low. If you’re considering a similar cloud provider for your own app, **Render** offers a good balance between simplicity and functionality for small-to-medium projects.



## Postman Testing for API endpoints after deployment


Here are the available API endpoints:

1. **GET /outdated_page/{category_name}**  
   Fetches the most outdated page for a given category.

2. **GET /cached_outdated_page/{category_name}**  
   Fetches cached data for an outdated page if available.

3. **POST /query**  
   Executes a `SELECT` SQL query on the database.

---

## Postman Tests

I have created a **Postman collection** that includes the following tests for the API:

### Test Cases:

1. **Outdated Page Request**  
   - Verifies that the `/outdated_page/{category_name}` endpoint correctly returns the most outdated page for a valid category.
   - Expected Response: `200 OK` with the page details.

2. **Cached Outdated Page Request**  
   - Verifies that the `/cached_outdated_page/{category_name}` endpoint returns cached data (or a relevant message if no cache exists).
   - Expected Response: `200 OK` with the cached data or a message indicating no cache.

3. **Querying a Valid Table**  
   - Verifies that querying a valid table (e.g., `SELECT COUNT(*) FROM pages`) returns the correct count of entries.
   - Expected Response: `200 OK` with the correct result.

4. **Querying an Invalid Table**  
   - Verifies that querying a non-existent table - page instead of pages (e.g., `SELECT COUNT(*) FROM page`) triggers a **500 Internal Server Error** due to the lack of error handling for invalid queries.
   - Expected Response: `500 Internal Server Error`.


# Wikipedia Assistant - Future Improvements

While Docker offers a powerful way to package and run the application with consistent environments across different systems, setting it up properly requires additional time and effort, especially when dealing with databases and complex pipelines.

Due to time constraints, this project currently uses a Python virtual environment and shell scripts for setup and execution. This simpler approach ensures that the application runs correctly on macOS and Linux, and can also be used on Windows with Git Bash or WSL.

Implementing Docker support is planned for future iterations to simplify deployment and improve cross-platform consistency.