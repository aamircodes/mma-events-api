from flask import Flask, jsonify
from pymongo import MongoClient
from selenium import webdriver
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv('MONGODB_URI')

app = Flask(__name__)

BASE_URL = 'https://www.tapology.com'
MAJOR_ORGS = ['UFC', 'PFL', 'BELLATOR', 'ONE', 'RIZIN']
MAX_MAJOR_ORGS = 10


def connect_to_db():
    try:
        print("Attempting to connect to the database...")
        client = MongoClient(uri, tls=True, tlsAllowInvalidCertificates=True)
        print("Connected to the database successfully.")
        return client['fight_data_db']
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None


def store_data(data):
    db = connect_to_db()
    if db is not None:
        collection = db['major_org_events']
        collection.delete_many({})  # remove existing data
        collection.insert_many(data)


def get_browser():
    print("Initializing the browser...")
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=chrome_options)
    print("Browser initialized successfully.")
    return driver


def filter_major_orgs(events):
    return [event for event in events if any(org in event["title"].upper() for org in MAJOR_ORGS)][:MAX_MAJOR_ORGS]


def extract_event_details(el):
    title_element = el.select_one('span.name a')
    title = title_element.text.strip() if title_element else None

    datetime_element = el.select_one('span.datetime')
    date = datetime_element.text.strip() if datetime_element else None

    link = BASE_URL + title_element['href'] if title_element else None

    return {"title": title, "date": date, "link": link}


def extract_fight_details(el):
    def get_weight():
        weight_element = el.select_one('.weight')
        return weight_element.text if weight_element else None

    def get_fighter(side):
        name_selector = f'.fightCardFighterName.{side} a'
        link_selector = f'.fightCardFighterBout.{side} a'
        rank_selector = f'.fightCardFighterRankNum.{side}.world .number'
        record_selector = f'.fightCardRecord'

        name = el.select_one(name_selector).text
        link = BASE_URL + el.select_one(link_selector)['href']
        rank = el.select_one(rank_selector).nextSibling.strip(
        ) if el.select_one(rank_selector) else None
        record = el.select_one(record_selector).text.strip(
        ) if el.select_one(record_selector) else None

        return {"name": name, "link": link, "rank": rank, "record": record}

    main_card = 'main' in el.select_one('.billing').text.lower()
    title_match = el.select_one('.fightCardWeight span.title') is not None

    return {
        "title_match": title_match,
        "main_card": main_card,
        "weight": get_weight(),
        "fighterA": get_fighter('left'),
        "fighterB": get_fighter('right')
    }


def scrape():
    browser = get_browser()
    try:
        print("Starting the scraping process...")
        browser.get(f"{BASE_URL}/fightcenter?group=major&schedule=upcoming")
        soup = BeautifulSoup(browser.page_source, 'lxml')

        events = [extract_event_details(el)
                  for el in soup.select('.promotion')]
        events = filter_major_orgs(events)
        print(f"Found {len(events)} major events.")

        for event in events:
            print(f"Scraping details for {event['title']}...")
            browser.get(event['link'])
            soup = BeautifulSoup(browser.page_source, 'lxml')
            event["fights"] = [extract_fight_details(
                el) for el in soup.select('li.fightCard:not(.picks)')]
        data = [event for event in events if len(event["fights"]) > 4]
        store_data(data)
        print("Scraping process completed successfully.")
        return True
    except Exception as e:
        print(f"Error occurred during scraping: {e}")
        return False
    finally:
        print("Closing the browser.")
        browser.quit()


@app.route('/scrape', methods=['POST'])
def run_scrape():
    print("Received a request to scrape.")
    success = scrape()
    print(f"Scraping {'succeeded' if success else 'failed'}.")
    return jsonify({"status": "success" if success else "failure"})


@app.route('/', methods=['GET'])
def get_fight_data():
    print("Received a request for fight data.")
    db = connect_to_db()
    if db is not None:
        collection = db['major_org_events']
        data = list(collection.find({}, {'_id': 0}))
        return jsonify(data)
    else:
        return jsonify({"error": "Failed to connect to database"}), 500


if __name__ == "__main__":
    print("Starting the application...")
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
