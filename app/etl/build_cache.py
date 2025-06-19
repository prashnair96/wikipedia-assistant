import json
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, scoped_session
from app.db.models import Page, Category
from dotenv import load_dotenv
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionFactory = sessionmaker(bind=engine)
Session = scoped_session(SessionFactory)  # thread-safe sessions

def compute_outdated_page(category_name):
    session = Session()
    try:
        pages = session.query(Page).join(Category).filter(Category.category_name == category_name).all()
        outdated = None
        max_diff = None

        for page in pages:
            linked_ids = [link.target_page_id for link in page.out_links]
            if not linked_ids:
                continue
            most_recent = session.query(Page.last_modified_date).filter(Page.id.in_(linked_ids)).order_by(Page.last_modified_date.desc()).first()
            if not most_recent:
                continue
            diff = (most_recent[0] - page.last_modified_date).total_seconds()
            if max_diff is None or diff > max_diff:
                max_diff = diff
                outdated = page

        return category_name, {"page_id": outdated.id, "title": outdated.title} if outdated else None
    finally:
        session.close()

def main():
    session = Session()
    print("Fetching top categories...")
    top_categories_query = (
        session.query(Category.category_name, func.count().label("page_count"))
        .group_by(Category.category_name)
        .order_by(func.count().desc())
        .limit(10)
    )
    top_categories = [row.category_name for row in top_categories_query.all()]
    session.close()

    cache = {}

    print("Computing outdated pages in parallel...")
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_cat = {executor.submit(compute_outdated_page, cat): cat for cat in top_categories}
        for future in as_completed(future_to_cat):
            cat = future_to_cat[future]
            try:
                category, result = future.result()
                if result:
                    cache[category] = result
                    print(f"{category}: {result['title']}")
                else:
                    print(f"{category}: No outdated page found")
            except Exception as e:
                print(f"Error computing {cat}: {e}")

    with open("outdated_cache.json", "w") as f:
        json.dump(cache, f, indent=2)

    print("Cache built and saved.")

if __name__ == "__main__":
    main()
