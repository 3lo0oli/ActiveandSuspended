import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

# إعداد صفحة ستريملت
st.set_page_config(page_title="تحقق من حالة الحساب", page_icon="🔍", layout="centered")

st.markdown("""
    <h1 style='text-align: center;'>🔍 تحقق من حالة الحساب</h1>
""", unsafe_allow_html=True)

# إدخال الرابط
account_url = st.text_input("🔗 أدخل رابط الحساب:")

# اختيار المنصة
platform = st.selectbox("🌐 اختر المنصة (أو اترك التحديد):", ["reddit", "twitter", "instagram", "tiktok", "facebook", "youtube"])

# زر التحقق
if st.button("تحقق"):
    if not account_url:
        st.warning("⚠️ الرجاء إدخال رابط الحساب.")
    else:
        try:
            # إعداد Selenium على Streamlit Cloud
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

            driver.get(account_url)
            time.sleep(3)  # الانتظار لتحميل الصفحة

            page_source = driver.page_source.lower()

            suspended_keywords = [
                "account has been suspended",
                "page not found",
                "user not found",
                "sorry, this page isn't available",
                "couldn't find this account",
                "this account doesn’t exist",
                "this account was suspended",
                "content not available",
                "unavailable"
            ]

            is_suspended = any(keyword in page_source for keyword in suspended_keywords)

            driver.quit()

            if is_suspended:
                st.error("🔴 الحساب موقوف (Suspended)")
            else:
                st.success("🟢 الحساب نشط (Active)")

        except Exception as e:
            st.warning(f"⚠️ لم يتم التأكد من الحالة بدقة.\n\n{e}")
