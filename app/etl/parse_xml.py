import bz2
import xml.etree.ElementTree as ET
from datetime import datetime
import mwparserfromhell
import pickle
from concurrent.futures import ThreadPoolExecutor, as_completed

def extract_links(text):
    """Extract internal wiki links from wikitext using mwparserfromhell."""
    wikicode = mwparserfromhell.parse(text)
    links = []
    for node in wikicode.filter_wikilinks():
        target = str(node.title).strip()
        if ':' not in target and target:
            links.append(target)
    return links

def process_page(page_tuple):
    """Process a single page and extract metadata + links."""
    title, page_id, timestamp_str, text, title_to_id = page_tuple
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        link_titles = extract_links(text)
        link_ids = [title_to_id[lt] for lt in link_titles if lt in title_to_id]

        return {
            "page_id": page_id,
            "title": title,
            "last_modified": timestamp,
            "link_ids": link_ids
        }
    except Exception:
        return None

def parse_with_elementtree(xml_path, title_to_id):
    """Stream and parse XML to extract valid article pages."""
    ns = {'mw': 'http://www.mediawiki.org/xml/export-0.11/'}
    pages = []
    count = 0

    with bz2.open(xml_path, 'rb') as f:
        context = ET.iterparse(f, events=('end',))
        for event, elem in context:
            if elem.tag == '{http://www.mediawiki.org/xml/export-0.11/}page':
                title_elem = elem.find('mw:title', ns)
                ns_elem = elem.find('mw:ns', ns)
                revision_elem = elem.find('mw:revision', ns)
                text_elem = revision_elem.find('mw:text', ns) if revision_elem is not None else None
                timestamp_elem = revision_elem.find('mw:timestamp', ns) if revision_elem is not None else None

                if (title_elem is not None and
                    ns_elem is not None and
                    ns_elem.text == '0' and
                    timestamp_elem is not None and
                    text_elem is not None):

                    title = title_elem.text
                    if title in title_to_id:
                        page_id = title_to_id[title]
                        text = text_elem.text or ""
                        timestamp = timestamp_elem.text
                        pages.append((title, page_id, timestamp, text, title_to_id))

                count += 1
                if count % 1000 == 0:
                    print(f"Collected {count} pages...")

                elem.clear()

    return pages

def main():
    print("Loading title_to_id.pkl...")
    with open("title_to_id.pkl", "rb") as f:
        title_to_id = pickle.load(f)

    xml_path = "data/simplewiki-latest-pages-articles.xml.bz2"
    print(f"Parsing XML file: {xml_path}")
    raw_pages = parse_with_elementtree(xml_path, title_to_id)

    print(f"{len(raw_pages)} pages collected. Starting parallel link extraction...")

    pages_data = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_page, page) for page in raw_pages]
        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            if result:
                pages_data.append(result)
            if i % 1000 == 0:
                print(f"Processed {i} pages...")

    print(f"Writing {len(pages_data)} processed pages to pages_data.pkl...")
    with open("pages_data.pkl", "wb") as f_out:
        pickle.dump(pages_data, f_out)

    print("XML parsing and link extraction completed successfully.")

if __name__ == "__main__":
    main()
