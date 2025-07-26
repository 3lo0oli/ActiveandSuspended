import streamlit as st
import httpx
from bs4 import BeautifulSoup
import re
import time

# إعداد واجهة المستخدم
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
    <p>تحقق من حالة أي حساب Reddit (نشط / موقوف / محذوف / غير موجود)</p>
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
        return "❌ اسم المستخدم غير صالح", None

    url = build_reddit_url(username)

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html",
        "Accept-Language": "en-US,en;q=0.5"
    }

    try:
        with httpx.Client(timeout=25, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            full_text = soup.get_text(separator=' ', strip=True).lower()

            # ✅ فحص الحسابات الموقوفة أولاً
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

            # 🗑️ فحص الحسابات المحذوفة
            deleted_phrases = [
                "this user has deleted their account",
                "user deleted their account",
                "account has been deleted",
                "deleted their account"
            ]
            if any(phrase in full_text for phrase in deleted_phrases):
                return "🗑️ محذوف", url

            # ✅ فحص النشاط
            active_keywords = [
                "post karma", "comment karma", "awardee karma",
                "cake day", "joined", "reddit premium",
                "trophy case", "overview", "posts", "comments",
                "about", "karma", "achievements", "badges",
                "submitted", "gilded", "saved"
            ]
            active_matches = sum(1 for keyword in active_keywords if keyword in full_text)
            if active_matches >= 2:
                return "✅ نشط", url

            # ❓ حالة غير واضحة أو عامة
            if "reddit" in full_text and len(full_text) > 100:
                unclear_errors = [
                    "page not found", "user not found", "doesn't exist",
                    "no longer available", "been removed"
                ]
                if not any(err in full_text for err in unclear_errors):
                    return "❓ حالة غير واضحة", url

            return "❌ غير موجود", url

    except httpx.TimeoutException:
        return "⏱️ انتهت مهلة الاتصال", url
    except httpx.ConnectError:
        return "🌐 خطأ في الاتصال بالإنترنت", url
    except Exception as e:
        return f"⚠️ خطأ غير متوقع: {str(e)[:50]}...", url

# الواجهة
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

        if status.startswith("✅"):
            st.success(f"**{status}**")
            st.balloons()
            if url:
                st.markdown(f"🔗 [زيارة الحساب]({url})")
        elif status.startswith("🚫"):
            st.error(f"**{status}**")
        elif status.startswith("❌") or status.startswith("🗑️"):
            st.warning(f"**{status}**")
        else:
            st.info(f"**{status}**")

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
    <p>🛠️ تم تطوير هذه الأداة لمساعدتك في فحص حسابات Reddit بسهولة وسرعة</p>
    <p>💻 مطور بتقنية Streamlit | 🔒 آمن وسريع</p>
</div>
""", unsafe_allow_html=True)
