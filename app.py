import streamlit as st
import requests

st.set_page_config(page_title="Active / Suspended Checker", layout="centered")

st.title("🔍 تحقق من حالة الحساب")

platform_phrases = {
    "twitter": [
        "account suspended", "profile doesn’t exist", "profile doesn\\u2019t exist"
    ],
    "reddit": [
        "this account has been suspended", "nobody on reddit", "page not found"
    ],
    "facebook": [
        "this content isn't available", "page isn't available", "content not found"
    ],
    "instagram": [
        "sorry, this page isn't available", "user not found"
    ],
    "youtube": [
        "this account has been terminated", "channel does not exist"
    ],
    "tiktok": [
        "couldn't find", "page not available", "account was banned", "could not be found"
    ]
}

with st.form("check_form"):
    url = st.text_input("🔗 أدخل رابط الحساب:", placeholder="https://...")
    platform = st.selectbox("🌐 اختر المنصة:", list(platform_phrases.keys()))
    submitted = st.form_submit_button("تحقق")

    if submitted:
        try:
            clean_url = url.split("?")[0]
            response = requests.get(clean_url, timeout=10, headers={
                "User-Agent": "Mozilla/5.0"
            })
            content = response.text.lower()

            suspended_phrases = platform_phrases.get(platform, [])
            is_suspended = any(p.lower() in content for p in suspended_phrases)

            if is_suspended:
                st.error("🔴 الحساب موقوف (Suspended)")
            else:
                st.success("🟢 الحساب نشط (Active)")

        except Exception as e:
            st.warning(f"⚠️ حدث خطأ أثناء محاولة الوصول إلى الرابط: {e}")
