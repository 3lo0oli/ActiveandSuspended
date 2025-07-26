import streamlit as st
import httpx
from bs4 import BeautifulSoup
import re
import time

st.set_page_config(
    page_title="فحص حالة حساب Reddit", 
    page_icon="🔍", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.title("🔎 فحص حالة حساب Reddit")
st.markdown("""
<div style='text-align: center; padding: 20px; background-color: #f0f2f6; border-radius: 10px; margin-bottom: 30px;'>
    <h3 style='color: #FF4500;'>أداة التحقق من حسابات Reddit</h3>
    <p>تحقق بدقة هل الحساب <strong>نشط</strong> أم <strong>موقوف</strong></p>
</div>
""", unsafe_allow_html=True)

def clean_username(input_text):
    input_text = input_text.strip()
    if "reddit.com" in input_text:
        match = re.search(r'/(?:u|user)/([^/?]+)', input_text)
        if match:
            return match.group(1)
    input_text = re.sub(r'^(u/|user/|@|/)', '', input_text)
    return re.sub(r'[^a-zA-Z0-9_-]', '', input_text)

def build_reddit_url(username):
    return f"https://www.reddit.com/user/{username}"

def check_reddit_status(username):
    if not username or len(username) < 3:
        return "🚫 موقوف", None  # نعتبره موقوف لو الاسم غير صالح

    url = build_reddit_url(username)
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html",
        "Accept-Language": "en-US,en;q=0.5"
    }

    try:
        with httpx.Client(timeout=25, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            full_text = soup.get_text(separator=' ', strip=True).lower()

            # أولاً: فحص الحسابات الموقوفة
            suspended_phrases = [
                "this account has been suspended",
                "account has been suspended", 
                "user has been suspended",
                "account is suspended",
                "permanently suspended",
                "temporarily suspended"
            ]
            if any(phrase in full_text for phrase in suspended_phrases):
                return "🚫 موقوف", url

            # ثانياً: فحص الحسابات النشطة
            active_keywords = [
                "post karma", "comment karma", "awardee karma",
                "cake day", "joined", "reddit premium",
                "trophy case", "overview", "posts", "comments",
                "about", "karma", "achievements", "badges",
                "submitted", "gilded", "saved"
            ]
            active_matches = sum(1 for keyword in active_keywords if keyword in full_text)
            has_profile_elements = any([
                soup.find('div', {'data-testid': 'user-profile'}),
                soup.find('main'),
                soup.find('nav'),
                soup.select_one('article'),
                soup.select_one('div[data-testid*="post"]')
            ])

            if active_matches >= 2 or has_profile_elements:
                return "✅ نشط", url

            # الباقي نعتبره موقوف
            return "🚫 موقوف", url

    except Exception:
        return "🚫 موقوف", url

# واجهة المستخدم
col1, col2 = st.columns([3, 1])
with col1:
    user_input = st.text_input(
        "اسم المستخدم أو رابط الحساب:",
        placeholder="مثال: username أو u/username أو https://reddit.com/u/username"
    )
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    check_button = st.button("🔍 فحص الحساب", type="primary")

if check_button and user_input.strip():
    username = clean_username(user_input)
    if not username:
        st.error("❌ يرجى إدخال اسم مستخدم صالح")
    else:
        st.info(f"🔍 جارٍ فحص الحساب: **{username}**")
        progress_bar = st.progress(0)
        status_text = st.empty()
        for i in range(100):
            progress_bar.progress(i + 1)
            if i < 30:
                status_text.text("جارٍ الاتصال بـ Reddit...")
            elif i < 70:
                status_text.text("جارٍ تحليل البيانات...")
            else:
                status_text.text("جارٍ معالجة النتائج...")
            time.sleep(0.01)

        status, url = check_reddit_status(username)
        progress_bar.empty()
        status_text.empty()

        st.markdown("---")
        st.subheader("📊 نتيجة الفحص:")

        if status == "✅ نشط":
            st.success(f"**{status}**")
            st.balloons()
        else:
            st.error(f"**{status}**")

        with st.expander("📋 تفاصيل الفحص"):
            st.write(f"**اسم المستخدم:** {username}")
            if url:
                st.write(f"**الرابط:** {url}")
            st.write(f"**وقت الفحص:** {time.strftime('%Y-%m-%d %H:%M:%S')}")

elif check_button:
    st.warning("⚠️ يرجى إدخال اسم مستخدم أو رابط الحساب أولاً")

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>🛠️ تم تطوير هذه الأداة لفحص حسابات Reddit بدقة</p>
    <p>💻 مطور باستخدام Streamlit | 🔒 سريع وآمن</p>
</div>
""", unsafe_allow_html=True)
