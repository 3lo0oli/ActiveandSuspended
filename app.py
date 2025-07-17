import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException
import time

# تهيئة Streamlit
st.set_page_config(page_title="أداة فحص الحسابات", page_icon="🔍")
st.title("🔎 أداة التحقق من حالة الحسابات")
st.markdown("تحقق من حالة الحسابات: Reddit, Twitter, Instagram, TikTok, Facebook, Telegram, YouTube")

urls = st.text_area("✏️ أدخل الروابط (رابط في كل سطر):")

# دالة فحص الروابط
def check_account_status(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1280x720")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--log-level=3")

    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(15)
        driver.get(url)
        time.sleep(3)

        page = driver.page_source.lower()
        driver.quit()

        if "reddit.com" in url:
            if "this account has been suspended" in page:
                return "🚫 موقوف (Reddit)"
            elif "sorry, nobody on reddit goes by that name" in page:
                return "❌ غير موجود (Reddit)"
            else:
                return "✅ نشط (Reddit)"

        elif "twitter.com" in url:
            if "account suspended" in page:
                return "🚫 موقوف (Twitter)"
            elif "doesn’t exist" in page or "page doesn’t exist" in page:
                return "❌ غير موجود (Twitter)"
            else:
                return "✅ نشط (Twitter)"

        elif "instagram.com" in url:
            if "sorry, this page isn't available" in page:
                return "❌ غير موجود (Instagram)"
            elif "private" in page:
                return "⚠️ خاص (Instagram)"
            else:
                return "✅ نشط (Instagram)"

        elif "facebook.com" in url:
            if "content isn't available" in page or "page isn't available" in page:
                return "❌ غير موجود أو محذوف (Facebook)"
            else:
                return "✅ نشط (Facebook)"

        elif "tiktok.com" in url:
            if "couldn't find this account" in page:
                return "❌ غير موجود (TikTok)"
            elif "account is private" in page:
                return "⚠️ خاص (TikTok)"
            else:
                return "✅ نشط (TikTok)"

        elif "t.me" in url or "telegram.me" in url:
            if "this channel can't be displayed" in page or "not found" in page:
                return "❌ غير موجود (Telegram)"
            else:
                return "✅ نشط (Telegram)"

        elif "youtube.com" in url:
            if "has been terminated" in page or "channel does not exist" in page:
                return "❌ غير موجود أو محذوف (YouTube)"
            else:
                return "✅ نشط (YouTube)"

        else:
            return "✅ نشط (منصة غير معرفة)"

    except (WebDriverException, TimeoutException) as e:
        return f"❌ خطأ في الوصول للرابط: {e}"

# عند الضغط
if st.button("تحقق الآن"):
    if urls.strip():
        st.subheader("🔍 النتائج:")
        for line in urls.strip().splitlines():
            url = line.strip()
            if url:
                result = check_account_status(url)
                st.write(f"🔗 [{url}]({url}) → {result}")
    else:
        st.warning("يرجى إدخال روابط أولًا.")
