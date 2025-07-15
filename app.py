import streamlit as st
import requests

st.set_page_config(page_title="Active / Suspended Checker", layout="centered")

st.title("🔍 تحقق من حالة الحساب")

with st.form("check_form"):
    url = st.text_input("🔗 أدخل رابط الحساب:", placeholder="https://...")
    platform = st.selectbox("🌐 اختر المنصة:", [
        "twitter", "reddit", "facebook", "instagram", "youtube", "tiktok"
    ])
    submitted = st.form_submit_button("تحقق")

    if submitted:
        try:
            clean_url = url.split("?")[0]
            response = requests.get(clean_url, timeout=10)
            content = response.text.lower()

            if platform == "twitter":
                is_suspended = "account suspended" in content
            elif platform == "reddit":
                is_suspended = "this account has been suspended" in content
            elif platform == "facebook":
                is_suspended = "this content isn't available" in content or "page isn't available" in content
            elif platform == "instagram":
                is_suspended = "sorry, this page isn't available" in content
            elif platform == "youtube":
                is_suspended = "this account has been terminated" in content or "channel does not exist" in content
            elif platform == "tiktok":
                is_suspended = "couldn't find this account" in content or "page not available" in content
            else:
                is_suspended = True

            if is_suspended:
                st.error("🔴 الحساب موقوف (Suspended)")
            else:
                st.success("🟢 الحساب نشط (Active)")

        except Exception as e:
            st.warning(f"⚠️ حدث خطأ أثناء محاولة الوصول إلى الرابط: {e}")
