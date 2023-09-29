import requests
from bs4 import BeautifulSoup

URL = "https://www.tapology.com/fightcenter/events/101866-ufc-fight-night"
page = requests.get(URL)

soup = BeautifulSoup(page.content, "html.parser")
results = soup.find_all("div", class_="fightCardBoutNumber")
if __name__ == '__main__':
    for result in results:
        print(result)
