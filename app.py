import streamlit as st
import httpx
import re
from urllib.parse import urlparse

def extract_reddit_username(url_or_username):
    """استخراج اسم مستخدم Reddit من الرابط أو النص المدخل"""
    if not url_or_username:
        return None
    
    # إذا كان إدخال اسم مستخدم مباشر (بدون رابط)
    if not url_or_username.startswith(('http://', 'https://')):
        return url_or_username.split('/')[0].strip('@')
    
    try:
        parsed = urlparse(url_or_username)
        if 'reddit.com' in parsed.netloc:
            path_parts = parsed.path.split('/')
            if len(path_parts) >= 3 and path_parts[1] == 'user':
                return path_parts[2]
            elif len(path_parts) >= 2:
                return path_parts[1]
    except:
        pass
    
    return url_or_username.strip('/')

def check_reddit_status(username):
    try:
        if not username:
            return "❌ لم يتم تقديم اسم مستخدم صحيح", "gray", None
        
        url = f"https://www.reddit.com/user/{username}/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        with httpx.Client(follow_redirects=True) as client:
            response = client.get(url, headers=headers, timeout=15)
            html = response.text.lower()

            # الحساب غير موجود
            if (response.status_code == 404 or 
                "page not found" in html or 
                "sorry, nobody on reddit goes by that name" in html or
                "there's nobody on reddit by that name" in html):
                return "❌ الحساب غير موجود (404)", "orange", url

            # الحساب موقوف
            if ("this account has been suspended" in html or 
                "content unavailable" in html or 
                re.search(r"<title>\s*user.*suspended\s*</title>", html, re.IGNORECASE) or
                "account suspended" in html or
                "suspended account" in html):
                return "🔴 الحساب موقوف (Suspended)", "red", url

            # الحساب محذوف
            if ("this account has been deleted" in html or 
                "user deleted" in html or
                "deleted account" in html):
                return "⚫ الحساب محذوف (Deleted)", "black", url

            # الحساب النشط
            if (response.status_code == 200 and 
                (f"/user/{username}/" in html.lower() or 
                 f"u/{username}" in html.lower() or
                 f"author={username}" in html.lower())):
                return "🟢 الحساب نشط (Active)", "green", url

            # إذا لم يتطابق مع أي حالة معروفة
            return "⚠️ لم يتم التأكد من الحالة بدقة", "gray", url

    except httpx.TimeoutException:
        return "⚠️ انتهت مهلة الطلب (Timeout)", "gray", url
    except httpx.HTTPError as e:
        return f"⚠️ خطأ في الاتصال: {str(e)}", "gray", url
    except Exception as e:
        return f"⚠️ حدث خطأ غير متوقع: {str(e)}", "gray", url

# واجهة Streamlit
st.set_page_config(
    page_title="تحقق من حالة الحساب", 
    page_icon="🔍", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS مخصص
st.markdown("""
<style>
    .stTextInput input {
        direction: ltr;
        text-align: left;
    }
    .stButton button {
        width: 100%;
    }
    .result-box {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .active { background-color: #e6f7e6; border-left: 5px solid #4CAF50; }
    .suspended { background-color: #ffebee; border-left: 5px solid #F44336; }
    .not-found { background-color: #fff3e0; border-left: 5px solid #FF9800; }
    .deleted { background-color: #f1f1f1; border-left: 5px solid #607D8B; }
    .unknown { background-color: #f5f5f5; border-left: 5px solid #9E9E9E; }
</style>
""", unsafe_allow_html=True)

# عنوان التطبيق
st.markdown("<h1 style='text-align: center; margin-bottom: 1.5rem;'>🔍 تحقق من حالة حساب Reddit</h1>", unsafe_allow_html=True)

# مربع الإدخال
input_col, button_col = st.columns([4, 1])
with input_col:
    user_input = st.text_input(
        "أدخل رابط الحساب أو اسم المستخدم:",
        placeholder="مثال: nedaa_7 أو https://www.reddit.com/user/nedaa_7/",
        key="user_input"
    )

with button_col:
    st.write("")  # للتباعد
    check_button = st.button("تحقق الآن", type="primary")

# عرض النتائج
if check_button:
    if user_input:
        username = extract_reddit_username(user_input)
        if username:
            with st.spinner("جاري التحقق من الحساب..."):
                status, color, profile_url = check_reddit_status(username)
                
                # تحديد فئة CSS بناءً على اللون
                css_class = {
                    "green": "active",
                    "red": "suspended",
                    "orange": "not-found",
                    "black": "deleted",
                    "gray": "unknown"
                }.get(color, "unknown")
                
                # عرض النتيجة في مربع مخصص
                st.markdown(
                    f"""
                    <div class="result-box {css_class}">
                        <h3 style="margin-top: 0;">{status}</h3>
                        <p><strong>اسم المستخدم:</strong> {username}</p>
                        <p><a href="{profile_url}" target="_blank">رابط الحساب على Reddit</a></p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # إضافة بعض المعلومات الإضافية
                if color == "green":
                    st.info("💡 هذا الحساب نشط ويظهر محتواه بشكل طبيعي.")
                elif color == "red":
                    st.error("⚠️ هذا الحساب موقوف من قبل إدارة Reddit.")
                elif color == "orange":
                    st.warning("🔎 لم يتم العثور على حساب بهذا الاسم. تأكد من كتابة اسم المستخدم بشكل صحيح.")
        else:
            st.warning("⚠️ لم يتم التعرف على اسم المستخدم. تأكد من إدخال رابط أو اسم مستخدم صحيح.")
    else:
        st.warning("⚠️ يرجى إدخال رابط الحساب أو اسم المستخدم أولاً.")

# تذييل الصفحة
st.markdown("---")
st.markdown("""
<p style="text-align: center; color: #666; font-size: 0.9rem;">
    أداة التحقق من حسابات Reddit | تم التطوير باستخدام Python و Streamlit
</p>
""", unsafe_allow_html=True)
