import streamlit as st
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="تحقق من حالة الحساب", page_icon="🔍", layout="centered")

st.markdown("<h1 style='text-align: center;'>🔍 تحقق من حالة الحساب</h1>", unsafe_allow_html=True)

url = st.text_input("🔗 أدخل رابط الحساب:", placeholder="https://www.reddit.com/user/xyz")
platform = st.selectbox("🌐 اختر المنصة:", ["reddit", "twitter", "instagram", "youtube", "tiktok", "facebook"])
check_btn = st.button("تحقق")

def check_account_status(url, platform):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(url, headers=headers, timeout=10)
        content = response.text.lower()
        soup = BeautifulSoup(content, "html.parser")

        # Reddit
        if platform == "reddit":
            if "this account has been suspended" in content:
                return "suspended"
            elif "sorry, nobody on reddit goes by that name." in content:
                return "not found"
            elif "u/" in content:
                return "active"

        # Twitter
        elif platform == "twitter":
            if "account suspended" in content or "suspended" in soup.title.text.lower():
                return "suspended"
            elif "this account doesn’t exist" in content:
                return "not found"
            else:
                return "active"

        # Instagram
        elif platform == "instagram":
            if "sorry, this page isn't available." in content or "not found" in content:
                return "suspended"
            else:
                return "active"

        # YouTube
        elif platform == "youtube":
            if "this channel does not exist" in content or "unavailable" in content:
                return "suspended"
            else:
                return "active"

        # TikTok
        elif platform == "tiktok":
            if "couldn't find this account" in content or "this account was banned" in content:
                return "suspended"
            else:
                return "active"

        # Facebook
        elif platform == "facebook":
            if "this content isn't available" in content:
                return "suspended"
            else:
                return "active"

        return "unknown"

    except:
        return "error"

if check_btn:
    if not url:
        st.warning("يرجى إدخال رابط الحساب.")
    else:
        status = check_account_status(url, platform)

        if status == "active":
            st.success("🟢 الحساب نشط (Active)")
        elif status == "suspended":
            st.error("🔴 الحساب موقوف (Suspended)")
        elif status == "not found":
            st.warning("⚠️ الحساب غير موجود")
        elif status == "unknown":
            st.warning("⚠️ لم يتم التحقق من الحالة")
        else:
            st.error("❌ حدث خطأ أثناء التحقق")
