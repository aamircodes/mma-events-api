from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=options)

def initialize_browser():
    driver.get('https://www.tapology.com/fightcenter/events/101866-ufc-fight-night')
    print("starting_Driver")

    # Corrected method to find elements
    fight_card_bouts = driver.find_elements(By.CSS_SELECTOR, ".fightCardFighterName.left")
    fight_card_bouts_two = driver.find_elements(By.CSS_SELECTOR, ".fightCardFighterName.right")


    for bout in fight_card_bouts:
        try:
            # Using the method to find the nested anchor element and get its text
            fight_name_left = bout.find_element(By.CSS_SELECTOR, "a").text
            print(fight_name_left)
        except Exception as e:
            print(f'error: {e}')  # Log the error and continue
    for bout in fight_card_bouts_two:
        try:
            # Using the method to find the nested anchor element and get its text
            fight_name_right = bout.find_element(By.CSS_SELECTOR, "a").text
            print(fight_name_right)
        except Exception as e:
            print(f'error: {e}')  # Log the error and continue
    driver.quit()

initialize_browser()
