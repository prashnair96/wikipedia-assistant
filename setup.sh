#!/bin/bash

set -e  # Exit immediately on error

# --- Setup Paths ---
PROJECT_DIR="/Users/prashanth/wikipedia-assistant"
cd "$PROJECT_DIR"

DUMP_DIR="data"
LOG_DIR="$PROJECT_DIR/logs"
PYTHON_BIN="/Users/prashanth/wikipedia-assistant/venv/bin/python3"

mkdir -p "$DUMP_DIR"
mkdir -p "$LOG_DIR"

# --- Step 0.5: Ensure DB schema exists ---
echo "$(date '+%Y-%m-%d %H:%M:%S') [0/7] Ensuring database schema exists..."
$PYTHON_BIN -m app.db.init_db

# --- Step 1: Clean old intermediate files ---
echo "$(date '+%Y-%m-%d %H:%M:%S') [1/7] Removing old files (if they exist)..."
files_to_remove=("outdated_cache.json" "title_to_id.pkl" "page_categories.pkl")
for file in "${files_to_remove[@]}"; do
    if [ -f "$file" ]; then
        echo "Deleting $file..."
        rm -f "$file"
    else
        echo "$file does not exist, skipping."
    fi
done

# --- Step 2: Download latest Wikipedia dumps ---
echo "$(date '+%Y-%m-%d %H:%M:%S') [2/7] Downloading latest dumps from Wikimedia..."
curl -o "$DUMP_DIR/simplewiki-latest-pages-articles.xml.bz2" https://dumps.wikimedia.org/simplewiki/latest/simplewiki-latest-pages-articles.xml.bz2
curl -o "$DUMP_DIR/simplewiki-latest-page.sql.gz" https://dumps.wikimedia.org/simplewiki/latest/simplewiki-latest-page.sql.gz
curl -o "$DUMP_DIR/simplewiki-latest-categorylinks.sql.gz" https://dumps.wikimedia.org/simplewiki/latest/simplewiki-latest-categorylinks.sql.gz

# --- Step 3: Unzip SQL files ---
echo "$(date '+%Y-%m-%d %H:%M:%S') [3/7] Checking for gzipped files to unzip..."
if ls "$DUMP_DIR"/*.gz 1> /dev/null 2>&1; then
  echo "Unzipping SQL files..."
  gunzip -f "$DUMP_DIR"/*.gz
else
  echo "No gzipped files found. Skipping unzip step."
fi

# --- Step 4: Parse SQL (pages, categories) ---
echo "$(date '+%Y-%m-%d %H:%M:%S') [4/7] Parsing SQL dumps..."
$PYTHON_BIN -m app.etl.parse_sql

# --- Step 5: Parse XML (page content + metadata) ---
echo "$(date '+%Y-%m-%d %H:%M:%S') [5/7] Parsing XML pages dump..."
$PYTHON_BIN -m app.etl.parse_xml

# --- Step 6: Load parsed data into database ---
echo "$(date '+%Y-%m-%d %H:%M:%S') [6/7] Loading data into the database..."
$PYTHON_BIN -m app.etl.load

# --- Step 7: Build precomputed outdated page cache ---
echo "$(date '+%Y-%m-%d %H:%M:%S') [7/7] Building outdated page cache..."
$PYTHON_BIN -m app.etl.build_cache

# --- Done ---
echo "$(date '+%Y-%m-%d %H:%M:%S') All steps completed successfully."
