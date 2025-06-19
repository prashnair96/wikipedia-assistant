import re
import pickle
import csv
import io
from collections import defaultdict


def split_sql_row(row):
    """
    Safely split a SQL row string into fields using CSV parser logic.
    """
    reader = csv.reader(io.StringIO(row), delimiter=',', quotechar="'", escapechar='\\')
    return next(reader)


def parse_page_titles(sql_file_path):
    title_to_id = {}

    with open(sql_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.startswith('INSERT INTO'):
                continue

            values_part = re.search(r'VALUES\s*(.*);', line, re.DOTALL)
            if not values_part:
                continue

            rows = re.findall(r'\((.*?)\)', values_part.group(1))
            for row in rows:
                try:
                    fields = split_sql_row(row)
                    page_id = int(fields[0])
                    namespace = int(fields[1])
                    title = fields[2].replace("_", " ")

                    if namespace == 0:  # Main content namespace
                        title_to_id[title] = page_id

                except Exception as e:
                    print(f"Skipping row (titles) due to error: {e}")
                    continue

    return title_to_id


def parse_categories(sql_file_path):
    page_to_categories = defaultdict(list)

    with open(sql_file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if not line.startswith('INSERT INTO'):
                continue

            values_part = re.search(r'VALUES\s*(.*);', line, re.DOTALL)
            if not values_part:
                continue

            rows = re.findall(r'\((.*?)\)', values_part.group(1))
            for row in rows:
                try:
                    fields = split_sql_row(row)
                    page_id = int(fields[0])
                    category_name = fields[1].replace("_", " ")

                    page_to_categories[page_id].append(category_name)

                except Exception as e:
                    print(f"Skipping row (categories) due to error: {e}")
                    continue

    return dict(page_to_categories)


def main():
    print("Parsing title → page_id...")
    title_to_id = parse_page_titles("data/simplewiki-latest-page.sql")
    with open("title_to_id.pkl", "wb") as f:
        pickle.dump(title_to_id, f)
    print(f"Saved {len(title_to_id)} titles.")

    print("Parsing page_id → categories...")
    page_to_categories = parse_categories("data/simplewiki-latest-categorylinks.sql")
    with open("page_categories.pkl", "wb") as f:
        pickle.dump(page_to_categories, f)
    print(f"Saved {len(page_to_categories)} pages with categories.")


if __name__ == "__main__":
    main()
