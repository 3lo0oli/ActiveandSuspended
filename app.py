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
    .stButton>button {
        background-color: #FF4500;
        color: white;
        font-weight: bold;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
    }
    .stButton>button:hover {
        background-color: #FF5722;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# عنوان التطبيق
st.markdown("<h1 class='header'>🔍 أداة التحقق من حالة الحسابات</h1>", unsafe_allow_html=True)

# تبويب المنصات
platform = st.selectbox(
    "اختر المنصة:",
    ["Reddit", "Facebook", "Twitter"],
    index=0
)

# دالة لاستخراج اسم المستخدم من الرابط
def extract_username(url, platform):
    try:
        if not url:
            return None
            
        # تنظيف المدخلات
        url = url.strip().strip("/").replace("https://", "").replace("http://", "")
        
        if platform == "Reddit":
            if "reddit.com" not in url:
                return url.split("/")[0].replace("u/", "").replace("@", "")
            return url.split("/user/")[-1].split("/")[0] if "/user/" in url else url.split("/u/")[-1].split("/")[0]
        
        elif platform == "Facebook":
            if "facebook.com" not in url:
                return url.split("/")[0].split("?")[0]
            return url.split("facebook.com/")[-1].split("/")[0].split("?")[0]
        
        elif platform == "Twitter":
            if "twitter.com" not in url and "x.com" not in url:
                return url.split("/")[0].replace("@", "")
            return url.split("twitter.com/")[-1].split("/")[0].split("?")[0] if "twitter.com" in url else url.split("x.com/")[-1].split("/")[0].split("?")[0]
    
    except Exception as e:
        st.error(f"حدث خطأ في استخراج اسم المستخدم: {str(e)}")
        return None

# دالة التحقق من حالة حساب Reddit
def check_reddit(username):
    url = f"https://www.reddit.com/user/{username}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    try:
        with httpx.Client(follow_redirects=True, timeout=15) as client:
            response = client.get(url, headers=headers)
            html = response.text.lower()

            if response.status_code == 404 or "page not found" in html or "sorry, nobody on reddit goes by that name" in html:
                return "❌ الحساب غير موجود", "not-found", url

            if ("this account has been suspended" in html or 
                "content unavailable" in html or 
                "account suspended" in html or
                re.search(r"<title>.*suspended.*</title>", html)):
                return "🔴 الحساب موقوف", "suspended", url

            if response.status_code == 200 and (f"/user/{username}/" in html or f"u/{username}" in html):
                return "🟢 الحساب نشط", "active", url

            return "⚠️ لم يتم التأكد من الحالة", "unknown", url

    except httpx.TimeoutException:
        return "⚠️ انتهت مهلة الطلب", "unknown", url
    except Exception as e:
        return f"⚠️ خطأ في الاتصال: {str(e)}", "unknown", url

# دالة التحقق من حالة حساب Facebook
def check_facebook(username):
    url = f"https://www.facebook.com/{username}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    try:
        with httpx.Client(follow_redirects=True, timeout=15) as client:
            response = client.get(url, headers=headers)
            html = response.text.lower()

            if response.status_code == 404 or "page not found" in html:
                return "❌ الحساب غير موجود", "not-found", url

            if ("content isn't available" in html or 
                "this page isn't available" in html or
                "this page may have been deleted" in html):
                return "🔴 الحساب محظور أو غير متاح", "suspended", url

            if response.status_code == 200 and (f"facebook.com/{username}" in html or f"fb.com/{username}" in html):
                return "🟢 الحساب نشط", "active", url

            return "⚠️ لم يتم التأكد من الحالة", "unknown", url

    except httpx.TimeoutException:
        return "⚠️ انتهت مهلة الطلب", "unknown", url
    except Exception as e:
        return f"⚠️ خطأ في الاتصال: {str(e)}", "unknown", url

# دالة التحقق من حالة حساب Twitter
def check_twitter(username):
    url = f"https://twitter.com/{username}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    try:
        with httpx.Client(follow_redirects=True, timeout=15) as client:
            response = client.get(url, headers=headers)
            html = response.text.lower()

            if response.status_code == 404 or "page doesn't exist" in html:
                return "❌ الحساب غير موجود", "not-found", url

            if ("account suspended" in html or 
                "هذا الحساب معلق" in html or
                "このアカウントは停止されています" in html):
                return "🔴 الحساب موقوف", "suspended", url

            if response.status_code == 200 and f"twitter.com/{username}" in html:
                return "🟢 الحساب نشط", "active", url

            return "⚠️ لم يتم التأكد من الحالة", "unknown", url

    except httpx.TimeoutException:
        return "⚠️ انتهت مهلة الطلب", "unknown", url
    except Exception as e:
        return f"⚠️ خطأ في الاتصال: {str(e)}", "unknown", url

# واجهة المستخدم
user_input = st.text_input(
    f"أدخل رابط الحساب أو اسم المستخدم على {platform}:",
    placeholder=f"مثال: username أو https://{'reddit.com' if platform == 'Reddit' else 'facebook.com' if platform == 'Facebook' else 'twitter.com'}/username"
)

check_button = st.button("تحقق")

# معالجة النتيجة
if check_button:
    if user_input:
        with st.spinner("جاري التحقق من الحساب..."):
            username = extract_username(user_input, platform)
            
            if username:
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
                
                # إضافة معلومات إضافية حسب الحالة
                if status_class == "active":
                    st.success("تم العثور على الحساب وهو نشط حاليًا.")
                elif status_class == "suspended":
                    st.error("هذا الحساب موقوف أو محظور من قبل المنصة.")
                elif status_class == "not-found":
                    st.warning("لا يوجد حساب بهذا الاسم. تأكد من كتابة اسم المستخدم بشكل صحيح.")
            else:
                st.error("⚠️ لم يتم استخراج اسم مستخدم صحيح. يرجى التأكد من المدخلات.")
    else:
        st.warning("⚠️ يرجى إدخال رابط الحساب أو اسم المستخدم أولاً")

# تذييل الصفحة
st.markdown("---")
st.markdown("""
<p style="text-align: center; color: #666; font-size: 0.9rem;">
    أداة التحقق من حالة الحسابات | تم التطوير باستخدام Python و Streamlit
</p>
""", unsafe_allow_html=True)
