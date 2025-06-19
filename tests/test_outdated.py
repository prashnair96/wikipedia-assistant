from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone
from app.etl.build_cache import compute_outdated_page, main  

# === Mock classes ===
class MockLink:
    def __init__(self, target_page_id):
        self.target_page_id = target_page_id

class MockPage:
    def __init__(self, id, title, last_modified_date, out_links):
        self.id = id
        self.title = title
        self.last_modified_date = last_modified_date
        self.out_links = out_links

# === Tests ===

@patch("app.etl.build_cache.Session")
def test_compute_outdated_page_no_pages(mock_session):
    mock_sess_instance = mock_session.return_value
    mock_sess_instance.query.return_value.join.return_value.filter.return_value.all.return_value = []
    
    category, result = compute_outdated_page("EmptyCategory")
    assert category == "EmptyCategory"
    assert result is None

@patch("app.etl.build_cache.Session")
def test_compute_outdated_page_with_outdated_page(mock_session):
    now = datetime.now(timezone.utc)
    link1 = MockLink(target_page_id=2)
    page1 = MockPage(id=1, title="Page1", last_modified_date=now - timedelta(days=2), out_links=[link1])
    
    mock_sess_instance = mock_session.return_value
    mock_sess_instance.query.return_value.join.return_value.filter.return_value.all.return_value = [page1]
    mock_sess_instance.query.return_value.filter.return_value.order_by.return_value.first.return_value = (now,)
    
    category, result = compute_outdated_page("TestCategory")
    assert category == "TestCategory"
    assert result["page_id"] == 1
    assert result["title"] == "Page1"

@patch("app.etl.build_cache.open", create=True)
@patch("app.etl.build_cache.compute_outdated_page")
@patch("app.etl.build_cache.Session")
def test_main(mock_session, mock_compute_outdated, mock_open):
    mock_sess_instance = mock_session.return_value
    category_rows = [MagicMock(category_name="Cat1"), MagicMock(category_name="Cat2")]
    mock_sess_instance.query.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = category_rows

    mock_compute_outdated.side_effect = [
        ("Cat1", {"page_id": 1, "title": "Page1"}),
        ("Cat2", None)
    ]

    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file

    main()

    assert mock_compute_outdated.call_count == 2
