from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def check_reddit_status_selenium(url):
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(service=Service(), options=options)

        driver.get(url)
        time.sleep(3)  # ثواني بسيطة للتحميل

        page_source = driver.page_source.lower()

        if "this account has been suspended" in page_source:
            status = "suspended"
        elif "sorry, nobody on reddit goes by that name" in page_source:
            status = "not found"
        else:
            status = "active"

        driver.quit()
        return status

    except Exception as e:
        return f"error: {str(e)}"
