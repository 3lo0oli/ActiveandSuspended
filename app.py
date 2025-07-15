import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

st.set_page_config(page_title="Checker", layout="centered")
st.title("🔍 تحقق من حالة الحساب")

with st.form("check_form"):
    url = st.text_input("🔗 أدخل رابط الحساب:")
    platform = st.selectbox("🌐 اختر المنصة:", ["reddit", "twitter"])
    submitted = st.form_submit_button("تحقق")

    if submitted:
        try:
            # إعداد Selenium بدون واجهة
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            driver = webdriver.Chrome(options=options)

            driver.get(url)
            time.sleep(5)  # انتظر تحميل الصفحة

            content = driver.page_source.lower()

            driver.quit()

            # التحقق من حالات التعليق
            if platform == "reddit":
                if "this account has been suspended" in content or "nobody on reddit goes by that name" in content:
                    st.error("🔴 الحساب موقوف (Suspended)")
                else:
                    st.success("🟢 الحساب نشط (Active)")
            elif platform == "twitter":
                if "account suspended" in content:
                    st.error("🔴 الحساب موقوف (Suspended)")
                else:
                    st.success("🟢 الحساب نشط (Active)")

        except Exception as e:
            st.warning(f"⚠️ حدث خطأ أثناء التحقق: {str(e)}")
