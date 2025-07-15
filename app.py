import streamlit as st
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

st.set_page_config(page_title="تحقق من حالة الحساب", page_icon="🔍", layout="centered")

st.markdown(
    """
    <h1 style='text-align: center;'>🔍 تحقق من حالة الحساب</h1>
    """,
    unsafe_allow_html=True,
)

account_url = st.text_input("🔗 أدخل رابط الحساب:", placeholder="https://www.reddit.com/user/...")
platform = st.selectbox("🌐 اختر المنصة (أو اترك التحديد):", options=["reddit"])

if st.button("تحقق"):
    if not account_url.strip():
        st.warning("يرجى إدخال رابط الحساب.")
    else:
        try:
            with st.spinner("جارٍ التحقق..."):
                # إعداد المتصفح بدون واجهة (headless)
                chrome_options = Options()
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')

                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)

                driver.get(account_url)
                time.sleep(3)

                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                driver.quit()

                # التحقق من حالة الحساب على Reddit
                if platform == "reddit":
                    if "This account has been suspended" in soup.text:
                        st.error("🔴 الحساب موقوف (Suspended)")
                    elif "Sorry, nobody on Reddit goes by that name." in soup.text:
                        st.error("⚠️ الحساب غير موجود")
                    elif "u/" in soup.text:
                        st.success("🟢 الحساب نشط (Active)")
                    else:
                        st.warning("⚠️ لم يتم التأكد من الحالة بدقة.")

        except Exception as e:
            st.warning(f"حدث خطأ أثناء التحقق: {e}")
