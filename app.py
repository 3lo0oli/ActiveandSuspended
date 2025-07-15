import streamlit as st
import requests

st.set_page_config(page_title="Active / Suspended Checker", layout="centered")

st.markdown("""
    <style>
    body {
        font-family: Arial;
        background: #f9f9f9;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🔍 تحقق من حالة الحساب")

with st.form("check_form"):
    url = st.text_input("🔗 أدخل رابط الحساب:", placeholder="https://...")
    platform = st.selectbox("🌐 اختر المنصة:", ["twitter", "reddit", "facebook", "instagram", "youtube", "tiktok"])
    submitted = st.form_submit_button("تحقق")

    if submitted:
        try:
            response = requests.get(url, timeout=10)
            content = response.text.lower()

            if platform == "twitter":
                is_suspended = any(x in content for x in ["account suspended"])
            elif platform == "reddit":
                is_suspended = any(x in content for x in ["nobody on reddit goes by that name", "page not found", "this account has been suspended"])
            elif platform == "facebook":
                is_suspended = any(x in content for x in ["this content isn't available", "page isn't available"])
            elif platform == "instagram":
                is_suspended = any(x in content for x in ["sorry, this page isn't available"])
            elif platform == "youtube":
                is_suspended = any(x in content for x in ["this account has been terminated", "channel does not exist"])
            elif platform == "tiktok":
                is_suspended = any(x in content for x in ["couldn't find this account", "page not available"])
            else:
                is_suspended = True

            if is_suspended:
                st.error("🔴 الحساب موقوف (Suspended)")
            else:
                st.success("🟢 الحساب نشط (Active)")

        except Exception as e:
            st.warning(f"⚠️ حدث خطأ أثناء محاولة الوصول إلى الرابط: {e}")
