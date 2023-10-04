from flask import Flask, jsonify
from flask_caching import Cache
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options


BASE_URL = 'https://www.tapology.com'
MAJOR_ORGS = ['UFC', 'PFL', 'BELLATOR', 'ONE', 'RIZIN']
MAX_MAJOR_ORGS = 10

app = Flask(__name__)

# setup cache config
app.config['CACHE_TYPE'] = 'simple'
cache = Cache(app)

# utility function


def get_browser():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=options)


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


@cache.memoize(timeout=86400)
def scrape():
    browser = get_browser()
    browser.get(f"{BASE_URL}/fightcenter?group=major&schedule=upcoming")
    soup = BeautifulSoup(browser.page_source, 'lxml')

    events = [extract_event_details(el) for el in soup.select('.promotion')]
    events = filter_major_orgs(events)

    for event in events:
        browser.get(event['link'])
        soup = BeautifulSoup(browser.page_source, 'lxml')
        event["fights"] = [extract_fight_details(
            el) for el in soup.select('li.fightCard:not(.picks)')]

    browser.quit()

    return [event for event in events if len(event["fights"]) > 4]


@app.route('/get_fight_data', methods=['GET'])
def get_fight_data():
    data = scrape()
    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=True)
