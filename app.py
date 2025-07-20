import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
import time

st.set_page_config(page_title="فحص حسابات Reddit", page_icon="🔍")
st.title("🔎 أداة فحص حالة حسابات Reddit")
st.markdown("تحقق هل الحساب نشط أم موقوف على Reddit عبر محاكاة حقيقية للموقع.")

user_input = st.text_area("✏️ أدخل روابط حسابات Reddit (رابط في كل سطر):")

# إعداد المتصفح مرة واحدة
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1280x720")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--log-level=3")
    return webdriver.Chrome(options=chrome_options)

# فحص رابط واحد باستخدام متصفح واحد
def check_reddit_status(driver, url):
    try:
        driver.set_page_load_timeout(15)
        driver.get(url)
        time.sleep(2)
        html = driver.page_source.lower()

        if "this account has been suspended" in html:
            return "🚫 موقوف"
        elif "sorry, nobody on reddit goes by that name" in html:
            return "❌ غير موجود"
        else:
            return "✅ نشط"
    except (TimeoutException, WebDriverException) as e:
        return f"⚠️ خطأ أثناء الفحص"

# عند الضغط
if st.button("تحقق الآن"):
    if user_input.strip():
        links = [line.strip() for line in user_input.strip().splitlines() if line.strip()]
        st.subheader("📊 النتائج:")

        with st.spinner("جاري الفحص..."):
            driver = get_driver()
            results = {}
            for i, url in enumerate(links, 1):
                if not url.startswith("https://www.reddit.com/user/"):
                    results[url] = "❌ رابط غير صالح"
                    continue
                status = check_reddit_status(driver, url)
                results[url] = status
            driver.quit()

        # عرض النتائج
        for url, status in results.items():
            st.write(f"🔗 [{url}]({url}) → {status}")
    else:
        st.warning("يرجى إدخال روابط أولًا.")
