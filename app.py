import streamlit as st
import httpx
from bs4 import BeautifulSoup
import re
import time

st.set_page_config(page_title="Twitter Status Checker", page_icon="🐦", layout="centered")

st.title("🐦 فحص حالة حساب تويتر")
st.markdown("""
<div style='background-color:#e6f2ff;padding:15px;border-radius:10px'>
تحقق هل حساب تويتر (X) نشط أو موقوف أو غير موجود
</div>
""", unsafe_allow_html=True)

def clean_username(username):
    username = username.strip()
    username = re.sub(r"(https?://)?(www\.)?(x|twitter)\.com/", "", username)
    username = re.sub(r"^@", "", username)
    username = username.split("?")[0]
    return username

def build_twitter_url(username):
    return f"https://twitter.com/{username}"

def check_twitter_status(username):
    if not username:
        return "❓ غير معروف", None

    url = build_twitter_url(username)
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        with httpx.Client(timeout=20, follow_redirects=True) as client:
            response = client.get(url, headers=headers)

            if response.status_code == 404:
                return "❓ غير موجود", url

            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text(separator=' ', strip=True).lower()

            # تحقق من وجود الحساب موقوف
            if "account suspended" in text or "this account doesn’t exist" in text:
                return "🚫 موقوف", url

            # تحقق من وجود الحساب نشط
            if "followers" in text or "following" in text or "posts" in text:
                return "✅ نشط", url

            # fallback
            return "❓ غير معروف", url

    except Exception as e:
        return "❓ غير معروف", url

# إدخال المستخدم
col1, col2 = st.columns([3, 1])
with col1:
    user_input = st.text_input("اسم المستخدم أو رابط الحساب:")
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    check_btn = st.button("🔍 فحص", type="primary")

if check_btn and user_input.strip():
    username = clean_username(user_input)
    if not username:
        st.warning("⚠️ يرجى إدخال اسم مستخدم صحيح.")
    else:
        st.info(f"جارٍ فحص الحساب: {username}")
        progress_bar = st.progress(0)
        for i in range(100):
            time.sleep(0.005)
            progress_bar.progress(i + 1)
        status, profile_url = check_twitter_status(username)
        progress_bar.empty()

        st.subheader("🔎 النتيجة:")
        if status == "✅ نشط":
            st.success(f"الحساب {status}")
        elif status == "🚫 موقوف":
            st.error(f"الحساب {status}")
        elif status == "❓ غير موجود":
            st.warning(f"الحساب {status}")
        else:
            st.info(f"الحالة: {status}")

        st.markdown(f"[🔗 زيارة الحساب على تويتر]({profile_url})")

elif check_btn:
    st.warning("⚠️ يرجى كتابة اسم المستخدم أولًا.")

st.markdown("---")
st.caption("تم التطوير باستخدام Streamlit | OpenAI")
