import pickle
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base, Page, Category, Link
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def load_data(pages_data, page_to_categories):
    print("Loading data into DB...")

    valid_page_ids = {page["page_id"] for page in pages_data}
    skipped_links = 0

    session = Session()

    try:
        # Phase 1: Insert or update pages and categories
        for page in pages_data:
            page_obj = Page(
                id=page["page_id"],
                title=page["title"],
                last_modified_date=page["last_modified"]
            )
            session.merge(page_obj)

            for cat in page_to_categories.get(page["page_id"], []):
                session.merge(Category(page_id=page["page_id"], category_name=cat))

        session.commit()  # Commit pages and categories first

        # Phase 2: Insert links
        for page in pages_data:
            for idx, target_id in enumerate(page["link_ids"]):
                if target_id not in valid_page_ids:
                    skipped_links += 1
                    continue

                session.merge(Link(
                    source_page_id=page["page_id"],
                    target_page_id=target_id,
                    link_index=idx
                ))

        session.commit()  # Commit links after pages exist

        print("Data loaded successfully.")
        print(f"Skipped {skipped_links} links due to missing target pages.")

    except Exception as e:
        session.rollback()
        print(f"Error occurred: {e}")
        raise

    finally:
        session.close()

if __name__ == "__main__":
    print("Loading pickle files...")
    with open("title_to_id.pkl", "rb") as f:
        title_to_id = pickle.load(f)

    with open("page_categories.pkl", "rb") as f:
        page_to_categories = pickle.load(f)

    with open("pages_data.pkl", "rb") as f:
        pages_data = pickle.load(f)

    load_data(pages_data, page_to_categories)
