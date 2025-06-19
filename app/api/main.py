from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.db.models import Page, Category, Link
from dotenv import load_dotenv
import os
import json
from fastapi.responses import HTMLResponse

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

app = FastAPI()

# Load cache
try:
    with open("outdated_cache.json") as f:
        outdated_cache = json.load(f)
except FileNotFoundError:
    outdated_cache = {}


@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <html>
        <head><title>Wikipedia Assistant API</title></head>
        <body>
            <h1>Wikipedia Assistant API is running</h1>
            <p>Available endpoints:</p>
            <ul>
                <li><strong>POST</strong> /query – Run a SQL SELECT query</li>
                <li><strong>GET</strong> /outdated_page/{category_name}</li>
                <li><strong>GET</strong> /cached_outdated_page/{category_name}</li>
            </ul>
            <p>Visit <a href="/docs">/docs</a> for the Swagger UI.</p>
        </body>
    </html>
    """


@app.post("/query")
def run_query(sql: str):
    if not sql.strip().lower().startswith("select"):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed.")
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = [dict(row._mapping) for row in result]
            return {"results": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/outdated_page/{category_name}")
def get_outdated_page(category_name: str):
    session = SessionLocal()
    try:
        pages = session.query(Page).join(Category).filter(Category.category_name == category_name).all()
        if not pages:
            raise HTTPException(status_code=404, detail="Category not found")

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

        return {"page_id": outdated.id, "title": outdated.title} if outdated else {"message": "No outdated page found"}
    finally:
        session.close()

@app.get("/cached_outdated_page/{category_name}")
def get_cached(category_name: str):
    return outdated_cache.get(category_name, {"message": "Not cached or unknown category."})
