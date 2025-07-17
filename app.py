import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
import time

# إعداد Streamlit
st.set_page_config(page_title="فحص حسابات Reddit", page_icon="🔍")
st.title("🔎 أداة فحص حالة حسابات Reddit")
st.markdown("تحقق هل الحساب نشط أم موقوف على Reddit عبر محاكاة حقيقية للموقع.")

# إدخال الروابط
user_input = st.text_area("✏️ أدخل روابط حسابات Reddit (رابط في كل سطر):")

# دالة تشغيل المتصفح
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1280x720")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--log-level=3")

    return webdriver.Chrome(options=chrome_options)

# فحص رابط فردي
def check_reddit_status(url):
    try:
        driver = get_driver()
        driver.set_page_load_timeout(15)
        driver.get(url)
        time.sleep(5)
        html = driver.page_source.lower()
        driver.quit()

        if "this account has been suspended" in html:
            return "🚫 موقوف"
        elif "sorry, nobody on reddit goes by that name" in html:
            return "❌ غير موجود"
        else:
            return "✅ نشط"
    except (TimeoutException, WebDriverException) as e:
        return f"❌ خطأ: {str(e)}"

# عند الضغط
if st.button("تحقق الآن"):
    if user_input.strip():
        st.subheader("📊 النتائج:")
        links = [line.strip() for line in user_input.strip().splitlines() if line.strip()]
        for url in links:
            if not url.startswith("https://www.reddit.com/user/"):
                st.warning(f"الرابط غير صحيح: {url}")
                continue
            result = check_reddit_status(url)
            st.write(f"🔗 [{url}]({url}) → {result}")
    else:
        st.warning("يرجى إدخال روابط أولًا.")
