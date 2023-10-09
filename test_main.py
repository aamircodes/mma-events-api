import pytest
import os
from main import app, connect_to_db, scrape
from unittest.mock import patch, MagicMock

SECRET_KEY = os.getenv('SECRET_KEY')


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_get_fight_data(client):
    with patch('main.connect_to_db') as mock_connect:
        mock_collection = MagicMock()
        mock_collection.find.return_value = [{"title": "Test Fight"}]
        mock_connect.return_value = {"major_org_events": mock_collection}

        response = client.get('/')
        assert response.status_code == 200
        assert b"Test Fight" in response.data


def test_run_scrape(client):
    mock_json = {
        "data": SECRET_KEY
    }

    with patch('main.scrape') as mock_scrape:
        mock_scrape.return_value = True

        response = client.post('/scrape', json=mock_json)
        assert response.status_code == 200
        assert b"success" in response.data


def test_db_connection():
    with patch('main.MongoClient') as mock_client:
        instance = mock_client.return_value
        instance.__getitem__.return_value = "mock_db"

        assert connect_to_db() == "mock_db"


def test_scrape_function():
    with patch('main.get_browser') as mock_browser, patch('main.store_data') as mock_store:
        mock_browser_instance = MagicMock()
        mock_browser_instance.page_source = "<html></html>"
        mock_browser.return_value = mock_browser_instance
        mock_store.return_value = True

        assert scrape() == True
