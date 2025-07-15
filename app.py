import streamlit as st
import requests

st.set_page_config(page_title="Active / Suspended Checker", layout="centered")

st.title("🔍 تحقق من حالة الحساب")

with st.form("check_form"):
    url = st.text_input("🔗 أدخل رابط الحساب:", placeholder="https://twitter.com/xyz")
    platform = st.selectbox("🌐 اختر المنصة:", ["twitter", "reddit"])
    submitted = st.form_submit_button("تحقق")

    if submitted:
        try:
            response = requests.get(url, timeout=10)
            content = response.text.lower()
            if platform == "twitter":
                if "account suspended" in content:
                    st.error("🔴 الحساب موقوف (Suspended)")
                else:
                    st.success("🟢 الحساب نشط (Active)")
            elif platform == "reddit":
                if "nobody on reddit goes by that name" in content:
                    st.error("🔴 الحساب موقوف (Suspended)")
                else:
                    st.success("🟢 الحساب نشط (Active)")
        except:
            st.warning("⚠️ حدث خطأ أثناء محاولة الوصول إلى الرابط.")
