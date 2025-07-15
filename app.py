import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

def check_reddit_account_status(url):
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        time.sleep(3)

        source = driver.page_source.lower()
        driver.quit()

        if "this account has been suspended" in source:
            return "🚫 الحساب موقوف (Suspended)", "red"
        elif "sorry, nobody on reddit goes by that name" in source:
            return "❓ الحساب غير موجود (Not Found)", "orange"
        else:
            return "✅ الحساب نشط (Active)", "green"

    except Exception as e:
        return f"⚠️ حدث خطأ: {str(e)}", "gray"


st.set_page_config(page_title="تحقق من حالة الحساب", page_icon="🔍", layout="centered")
st.markdown("<h1 style='text-align: center;'>🔍 تحقق من حالة الحساب</h1>", unsafe_allow_html=True)

url = st.text_input("📎 أدخل رابط الحساب:", placeholder="https://www.reddit.com/user/username")

platform = st.selectbox("🌐 اختر المنصة:", ["reddit"], index=0)

if st.button("تحقق"):
    if url:
        with st.spinner("جاري التحقق من الحالة..."):
            if platform == "reddit":
                status, color = check_reddit_account_status(url)
                st.success(f"🟢 {status}") if color == "green" else st.error(f"🔴 {status}") if color == "red" else st.warning(status)
    else:
        st.warning("⚠️ يرجى إدخال رابط الحساب أولًا.")
