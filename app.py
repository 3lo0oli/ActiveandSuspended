import streamlit as st
import httpx
import re
from urllib.parse import urlparse

# إعدادات الصفحة
st.set_page_config(
    page_title="أداة التحقق من الحسابات",
    page_icon="🔍",
    layout="centered"
)

# CSS مخصص
st.markdown("""
<style>
    .header {
        text-align: center;
        color: #2b5876;
        margin-bottom: 30px;
    }
    .platform-tabs {
        display: flex;
        margin-bottom: 20px;
        border-bottom: 1px solid #ddd;
    }
    .platform-tab {
        padding: 10px 20px;
        cursor: pointer;
        border-bottom: 3px solid transparent;
    }
    .platform-tab.active {
        border-bottom: 3px solid #FF4500;
        font-weight: bold;
    }
    .result-box {
        padding: 20px;
        border-radius: 8px;
        margin: 20px 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .active { border-left: 5px solid #4CAF50; background-color: #e8f5e9; }
    .suspended { border-left: 5px solid #f44336; background-color: #ffebee; }
    .not-found { border-left: 5px solid #FF9800; background-color: #fff3e0; }
    .deleted { border-left: 5px solid #607d8b; background-color: #eceff1; }
    .unknown { border-left: 5px solid #9e9e9e; background-color: #f5f5f5; }
</style>
""", unsafe_allow_html=True)

# عنوان التطبيق
st.markdown("<h1 class='header'>🔍 أداة التحقق من حالة الحسابات</h1>", unsafe_allow_html=True)

# تبويب المنصات
platform = st.radio(
    "اختر المنصة:",
    ["Reddit", "Facebook", "Twitter"],
    horizontal=True,
    label_visibility="collapsed"
)

# دالة لاستخراج اسم المستخدم من الرابط
def extract_username(url, platform):
    try:
        if not url:
            return None
            
        if platform == "Reddit":
            if "reddit.com" not in url:
                return url.strip("/").replace("u/", "").replace("@", "")
            return url.split("/user/")[-1].split("/")[0] if "/user/" in url else url.split("/u/")[-1].split("/")[0]
        
        elif platform == "Facebook":
            if "facebook.com" not in url:
                return url.strip("/")
            return url.split("facebook.com/")[-1].split("/")[0].split("?")[0]
        
        elif platform == "Twitter":
            if "twitter.com" not in url:
                return url.strip("/").replace("@", "")
            return url.split("twitter.com/")[-1].split("/")[0].split("?")[0]
    
    except:
        return url.strip("/").replace("@", "")

# دالة التحقق من حالة حساب Reddit
def check_reddit(username):
    url = f"https://www.reddit.com/user/{username}/"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = httpx.get(url, headers=headers, timeout=10)
        html = response.text.lower()

        if response.status_code == 404 or "page not found" in html:
            return "❌ الحساب غير موجود", "not-found", url

        if "suspended" in html or "content unavailable" in html:
            return "🔴 الحساب موقوف", "suspended", url

        if response.status_code == 200 and username.lower() in html:
            return "🟢 الحساب نشط", "active", url

        return "⚠️ لم يتم التأكد من الحالة", "unknown", url

    except Exception as e:
        return f"⚠️ خطأ في الاتصال: {str(e)}", "unknown", url

# دالة التحقق من حالة حساب Facebook
def check_facebook(username):
    url = f"https://www.facebook.com/{username}/"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    try:
        response = httpx.get(url, headers=headers, timeout=10)
        html = response.text.lower()

        if response.status_code == 404 or "page not found" in html:
            return "❌ الحساب غير موجود", "not-found", url

        if "content isn't available" in html or "this page isn't available" in html:
            return "🔴 الحساب محظور أو غير متاح", "suspended", url

        if response.status_code == 200 and (f"facebook.com/{username}" in html or f"fb.com/{username}" in html):
            return "🟢 الحساب نشط", "active", url

        return "⚠️ لم يتم التأكد من الحالة", "unknown", url

    except Exception as e:
        return f"⚠️ خطأ في الاتصال: {str(e)}", "unknown", url

# دالة التحقق من حالة حساب Twitter
def check_twitter(username):
    url = f"https://twitter.com/{username}/"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    try:
        response = httpx.get(url, headers=headers, timeout=10)
        html = response.text.lower()

        if response.status_code == 404 or "page doesn't exist" in html:
            return "❌ الحساب غير موجود", "not-found", url

        if "account suspended" in html or "هذا الحساب معلق" in html:
            return "🔴 الحساب موقوف", "suspended", url

        if response.status_code == 200 and f"twitter.com/{username}" in html:
            return "🟢 الحساب نشط", "active", url

        return "⚠️ لم يتم التأكد من الحالة", "unknown", url

    except Exception as e:
        return f"⚠️ خطأ في الاتصال: {str(e)}", "unknown", url

# واجهة المستخدم
input_col, button_col = st.columns([4, 1])
with input_col:
    user_input = st.text_input(
        f"أدخل رابط الحساب أو اسم المستخدم على {platform}:",
        placeholder=f"مثال: username أو https://{'reddit.com' if platform == 'Reddit' else 'facebook.com' if platform == 'Facebook' else 'twitter.com'}/username"
    )

with button_col:
    st.write("")
    st.write("")
    check_button = st.button("تحقق")

# معالجة النتيجة
if check_button:
    if user_input:
        username = extract_username(user_input, platform)
        
        if username:
            with st.spinner("جاري التحقق..."):
                if platform == "Reddit":
                    status, status_class, profile_url = check_reddit(username)
                elif platform == "Facebook":
                    status, status_class, profile_url = check_facebook(username)
                else:
                    status, status_class, profile_url = check_twitter(username)
                
                # عرض النتيجة
                st.markdown(
                    f"""
                    <div class="result-box {status_class}">
                        <h3>{status}</h3>
                        <p><strong>اسم المستخدم:</strong> {username}</p>
                        <p><a href="{profile_url}" target="_blank">رابط الحساب</a></p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.warning("⚠️ لم يتم التعرف على اسم المستخدم. يرجى التأكد من الرابط المدخل")
    else:
        st.warning("⚠️ يرجى إدخال رابط الحساب أو اسم المستخدم أولاً")

# تذييل الصفحة
st.markdown("---")
st.markdown("""
<p style="text-align: center; color: #666; font-size: 0.9rem;">
    أداة التحقق من حالة الحسابات | تم التطوير باستخدام Python و Streamlit
</p>
""", unsafe_allow_html=True)
