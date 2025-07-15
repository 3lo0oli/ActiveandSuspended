import streamlit as st
import requests

st.set_page_config(page_title="Checker", layout="centered")
st.title("🔍 تحقق من حالة الحساب")

with st.form("check_form"):
    url = st.text_input("🔗 أدخل رابط الحساب:", placeholder="https://reddit.com/user/...")
    platform = st.selectbox("🌐 اختر المنصة:", ["reddit", "twitter"])
    submitted = st.form_submit_button("تحقق")

    if submitted:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0"
            }
            response = requests.get(url, headers=headers, timeout=10)
            content = response.text.lower()

            status = "unknown"
            if platform == "reddit":
                if "this account has been suspended" in content or "nobody on reddit goes by that name" in content:
                    status = "suspended"
                elif "/user/" in url and "posts" in content:
                    status = "active"
            elif platform == "twitter":
                if "account suspended" in content:
                    status = "suspended"
                elif "profile-banner" in content or "tweets" in content:
                    status = "active"

            if status == "active":
                st.success("🟢 الحساب نشط (Active)")
            elif status == "suspended":
                st.error("🔴 الحساب موقوف (Suspended)")
            else:
                st.warning("⚠️ لم يتم التأكد من الحالة بدقة")

        except Exception as e:
            st.warning(f"⚠️ حدث خطأ: {str(e)}")
