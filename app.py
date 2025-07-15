import streamlit as st
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Active / Suspended Checker", layout="centered")

st.title("🔍 تحقق من حالة الحساب")

platform_phrases = {
    "twitter": ["account suspended", "profile doesn’t exist", "profile doesn\u2019t exist"],
    "reddit": ["this account has been suspended", "nobody on reddit", "page not found"],
    "facebook": ["this content isn't available", "page isn't available", "content not found"],
    "instagram": ["sorry, this page isn't available", "user not found"],
    "youtube": ["this account has been terminated", "channel does not exist"],
    "tiktok": ["couldn't find", "page not available", "account was banned", "could not be found"]
}

def detect_platform_from_url(url):
    url = url.lower()
    if "twitter.com" in url:
        return "twitter"
    elif "reddit.com" in url:
        return "reddit"
    elif "facebook.com" in url:
        return "facebook"
    elif "instagram.com" in url:
        return "instagram"
    elif "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    elif "tiktok.com" in url:
        return "tiktok"
    else:
        return None

with st.form("check_form"):
    url = st.text_input("🔗 أدخل رابط الحساب:", placeholder="https://...")
    detected_platform = detect_platform_from_url(url)
    platform = st.selectbox("🌐 اختر المنصة (أو اترك المكتشفة):", list(platform_phrases.keys()), index=list(platform_phrases.keys()).index(detected_platform) if detected_platform else 0)
    submitted = st.form_submit_button("تحقق")

    if submitted:
        try:
            clean_url = url.split("?")[0]
            response = requests.get(clean_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text().lower()

            suspended_phrases = platform_phrases.get(platform, [])
            is_suspended = any(p.lower() in text for p in suspended_phrases)

            if is_suspended:
                st.error("🔴 الحساب موقوف (Suspended)")
            else:
                st.success("🟢 الحساب نشط (Active)")

        except Exception as e:
            st.warning(f"⚠️ حدث خطأ أثناء محاولة الوصول إلى الرابط: {e}")
