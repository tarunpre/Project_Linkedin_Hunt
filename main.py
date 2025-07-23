#!/usr/bin/env python3
import os
import time
from urllib.parse import quote_plus
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

def linkedin_login():
    # load creds
    load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
    username = os.getenv('LINKEDIN_USERNAME')
    password = os.getenv('LINKEDIN_PASSWORD')
    if not username or not password:
        raise ValueError("Set LINKEDIN_USERNAME and LINKEDIN_PASSWORD in .env")

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.get("https://www.linkedin.com/login")
    wait = WebDriverWait(driver, 15)
    wait.until(EC.presence_of_element_located((By.ID, "username")))

    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    # verify
    try:
        wait.until(EC.url_contains("/feed/"))
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "img.global-nav__me-photo")))
        print("✅ Logged in successfully.")
    except:
        print("❌ Login may have failed. Check the browser.")
    return driver

def linkedin_people_search(driver, query):
    q = quote_plus(query)
    driver.get(f"https://www.linkedin.com/search/results/people/?keywords={q}")
    print(f"⏳ Searching people for '{query}'…")
    while "/search/results/people/" not in driver.current_url:
        time.sleep(1)
    print(f"🔍 On People results for '{query}'.")

def linkedin_prepare_connect(driver, note_text):
    wait = WebDriverWait(driver, 20)

    # 1) Scroll a bit so buttons render
    driver.execute_script("window.scrollBy(0, 500);")
    time.sleep(1)

    # 2) Locate all “Connect” buttons via their label span
    connect_buttons = wait.until(EC.presence_of_all_elements_located((
        By.XPATH, "//span[text()='Connect']/ancestor::button"
    )))
    if not connect_buttons:
        print("ℹ️ No Connect buttons found.")
        return

    # 3) Pick the first one
    btn = connect_buttons[0]

    # 4) Scroll into center of view
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
        btn
    )
    time.sleep(0.5)

    # 5) Click it via JS to avoid interception
    driver.execute_script("arguments[0].click();", btn)

    # 6) Wait for the modal dialog
    wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']")))

    # 7) Click “Add a note” via JS too
    add_note = wait.until(EC.element_to_be_clickable((
        By.XPATH, "//button[contains(normalize-space(), 'Add a note')]"
    )))
    driver.execute_script("arguments[0].click();", add_note)

    # 8) Fill in your note
    textarea = wait.until(EC.presence_of_element_located((
        By.XPATH, "//textarea[@name='message']"
    )))
    textarea.clear()
    textarea.send_keys(note_text)

    print("✅ Note added. Please review and click Send manually.")

if __name__ == "__main__":
    driver = linkedin_login()
    linkedin_people_search(driver, "technical recruiter")

    my_note = (
        "Hi there! I came across your profile and would love to connect "
        "and learn more about your work in the industry."
    )
    linkedin_prepare_connect(driver, my_note)

    print("🛑 Waiting until you close Chrome…")
    while True:
        try:
            _ = driver.current_url
        except WebDriverException:
            print("👋 Browser closed; exiting.")
            break
        time.sleep(1)
