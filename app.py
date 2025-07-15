import streamlit as st
import httpx
import re
from urllib.parse import urlparse

def extract_reddit_username(url_or_username):
    """استخراج اسم مستخدم Reddit من الرابط أو النص المدخل"""
    if not url_or_username:
        return None
    
    # تنظيف المدخلات من المسافات والأحرف غير المرغوب فيها
    cleaned_input = url_or_username.strip().strip("/").replace("https://", "").replace("http://", "")
    
    # إذا كان إدخال اسم مستخدم مباشر (بدون رابط)
    if not cleaned_input.startswith(('www.reddit.com', 'reddit.com')):
        return cleaned_input.split('/')[0].strip('@')
    
    try:
        # معالجة الروابط المختلفة
        if cleaned_input.startswith('www.reddit.com/user/'):
            return cleaned_input.split('www.reddit.com/user/')[1].split('/')[0]
        elif cleaned_input.startswith('reddit.com/user/'):
            return cleaned_input.split('reddit.com/user/')[1].split('/')[0]
        elif cleaned_input.startswith('www.reddit.com/u/'):
            return cleaned_input.split('www.reddit.com/u/')[1].split('/')[0]
        elif cleaned_input.startswith('reddit.com/u/'):
            return cleaned_input.split('reddit.com/u/')[1].split('/')[0]
    except:
        pass
    
    return cleaned_input.split('/')[0]

def check_reddit_status(username):
    if not username:
        return "❌ لم يتم تقديم اسم مستخدم صحيح", "gray", None
    
    url = f"https://www.reddit.com/user/{username}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    try:
        with httpx.Client(follow_redirects=True, timeout=20) as client:
            response = client.get(url, headers=headers)
            html = response.text.lower()

            # الكشف عن الحساب الموقوف - تحسين النمط
            suspended_patterns = [
                r"this account has been suspended",
                r"account suspended",
                r"<title>.*suspended.*</title>",
                r"content unavailable",
                r"suspended account",
                r"this user account has been suspended"
            ]
            
            if any(re.search(pattern, html) for pattern in suspended_patterns):
                return "🔴 الحساب موقوف (Suspended)", "red", url

            # الحساب غير موجود
            not_found_patterns = [
                r"page not found",
                r"sorry, nobody on reddit goes by that name",
                r"there's nobody on reddit by that name",
                r"user not found"
            ]
            
            if (response.status_code == 404 or 
                any(pattern in html for pattern in not_found_patterns)):
                return "❌ الحساب غير موجود (404)", "orange", url

            # الحساب محذوف
            deleted_patterns = [
                r"this account has been deleted",
                r"user deleted",
                r"deleted account",
                r"account deleted"
            ]
            
            if any(pattern in html for pattern in deleted_patterns):
                return "⚫ الحساب محذوف (Deleted)", "black", url

            # الحساب النشط
            active_patterns = [
                f"/user/{username}/",
                f"u/{username}",
                f"author={username}",
                f"data-username=\"{username}\"",
                f"data-user=\"{username}\""
            ]
            
            if (response.status_code == 200 and 
                any(pattern in html for pattern in active_patterns)):
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
    page_title="تحقق من حالة حساب Reddit", 
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
        background-color: #FF4500;
        color: white;
        font-weight: bold;
    }
    .result-box {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .active { border-left: 5px solid #4CAF50; background-color: #e8f5e9; }
    .suspended { border-left: 5px solid #f44336; background-color: #ffebee; }
    .not-found { border-left: 5px solid #ff9800; background-color: #fff3e0; }
    .deleted { border-left: 5px solid #607d8b; background-color: #eceff1; }
    .unknown { border-left: 5px solid #9e9e9e; background-color: #f5f5f5; }
    .header {
        color: #FF4500;
        text-align: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# عنوان التطبيق
st.markdown("<h1 class='header'>🔍 تحقق من حالة حساب Reddit</h1>", unsafe_allow_html=True)

# مربع الإدخال
user_input = st.text_input(
    "أدخل رابط الحساب أو اسم المستخدم:",
    placeholder="مثال: somoud22 أو https://www.reddit.com/user/somoud22/",
    key="user_input"
)

check_button = st.button("تحقق الآن")

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
                
                # إضافة صورة توضيحية للحالة
                if color == "red":
                    st.image("https://www.redditstatic.com/desktop2x/img/id-cards/suspended@2x.png", 
                            caption="حساب موقوف على Reddit", width=200)
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
