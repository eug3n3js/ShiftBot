# import time
# import json
# import os
# import logging
# from dotenv import load_dotenv
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.chrome.service import Service as ChromeService
# from selenium.webdriver.chrome.options import Options
# from bs4 import BeautifulSoup
# import requests
#
# # --- config ---
# load_dotenv()
# LOGIN = os.getenv("LOGIN")
# PASSWORD = os.getenv("PASSWORD")
# TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
# CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "300"))
# HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
# TARGET_URL = "https://shameless.sinch.cz/react/position"
# KNOWN_FILE = "known_shifts.json"
# LOGFILE = "watcher.log"
#
# # --- logging ---
# logging.basicConfig(filename=LOGFILE, level=logging.INFO,
#                     format="%(asctime)s %(levelname)s: %(message)s")
# console = logging.StreamHandler()
# console.setLevel(logging.INFO)
# logging.getLogger('').addHandler(console)
#
#
# def send_telegram(text):
#     url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
#     payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
#     try:
#         r = requests.post(url, json=payload, timeout=10)
#         r.raise_for_status()
#         logging.info("Telegram sent.")
#     except Exception as e:
#         logging.exception("Failed to send telegram: %s", e)
#
#
# def load_known():
#     if os.path.exists(KNOWN_FILE):
#         with open(KNOWN_FILE, "r", encoding="utf-8") as f:
#             return set(json.load(f))
#     return set()
#
#
# def save_known(s):
#     with open(KNOWN_FILE, "w", encoding="utf-8") as f:
#         json.dump(list(s), f, ensure_ascii=False, indent=2)
#
#
# def start_browser():
#     chrome_options = Options()
#     if HEADLESS:
#         chrome_options.add_argument("--headless=new")
#         chrome_options.add_argument("--window-size=1920,1080")
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
#     service = ChromeService(ChromeDriverManager().install())
#     driver = webdriver.Chrome(service=service, options=chrome_options)
#     return driver
#
#
# def login_and_get_table_html(driver):
#     driver.get(TARGET_URL)
#     time.sleep(2)  # wait for page to load
#
#     # --- ВНИМАНИЕ: селекторы логина могут отличаться ---
#     # Попробуем найти поля автоматически: ищем input[type="text"]/input[type="email"] и input[type="password"]
#     try:
#         driver.find_element(By.ID, 'UserEmail').clear()
#         driver.find_element(By.ID, 'UserPassword').clear()
#         driver.find_element(By.ID, 'UserEmail').send_keys(LOGIN)
#         driver.find_element(By.ID, 'UserPassword').send_keys(PASSWORD)
#         driver.find_element(By.CLASS_NAME, 'theme-main-button.big-btn.full-btn').click()
#     except Exception as e:
#         logging.exception("Error during login attempt: %s", e)
#
#     time.sleep(4)
#
#     html = driver.page_source
#     return html
#
#
# def parse_table_rows(driver, page):
#     driver.get(TARGET_URL + f"?page={page}")
#     time.sleep(4)
#     html = driver.page_source
#     soup = BeautifulSoup(html, "html.parser")
#     rows = soup.select("tbody tr")
#     parsed = []
#     for i, r in enumerate(rows):
#         classes = r.get("class", None)
#         if classes and "MuiTableRow-root" in classes and "MuiTableRow-hover" in classes:
#             text = [td.get_text(strip=True) for td in r.find_all(["td","th"])]
#             if text:
#                 try:
#                     link = rows[i + 1].find("a").get("href")
#                     if r.select("svg.jss42.jss44"):
#                         print(f"liq {link}")
#                     else:
#                         print(f"default {link}")
#                 except:
#                     print(rows[i + 1], i)
#                     raise
#                 text.append(link)
#                 print(text)
#                 parsed.append("".join(text))
#     return parsed, html
#
#
# def main_loop():
#     known = load_known()
#     driver = start_browser()
#     logging.info("Browser started.")
#     try:
#         while True:
#             try:
#                 html = login_and_get_table_html(driver)
#                 rows = []
#                 prev = None
#                 for i in range(1, 10):
#                     p_rows, html = parse_table_rows(driver, i)
#                     if set(p_rows) == prev:
#                         break
#                     prev = set(p_rows)
#                     if len(p_rows) > 0:
#                         for r in p_rows:
#                             rows.append(r)
#                     else:
#                         break
#                 print(len(rows))
#                 logging.info("Found %d rows.", len(rows))
#                 new = []
#                 for r in rows:
#                     if r not in known:
#                         new.append(r)
#                         known.add(r)
#                 if new:
#                     for n in new:
#                         msg = f"Новая смена обнаружена:\n{n}\nСсылка: {TARGET_URL}"
#                         send_telegram(msg)
#                         logging.info("New shift: %s", n)
#                     save_known(known)
#                 else:
#                     logging.info("Новых смен не найдено.")
#             except Exception as e:
#                 logging.exception("Ошибка при проверке: %s", e)
#             logging.info("Sleeping %s seconds...", CHECK_INTERVAL)
#             time.sleep(CHECK_INTERVAL)
#     finally:
#         driver.quit()
#         logging.info("Driver closed.")
import asyncio

from src.main.utils.start_utils import run_bot

if __name__ == "__main__":
    print("runn")
    asyncio.run(run_bot())
