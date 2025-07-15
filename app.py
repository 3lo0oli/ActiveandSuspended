import streamlit as st
import httpx
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import json

# إعدادات الصفحة
st.set_page_config(
    page_title="أداة التحقق التلقائي من Reddit",
    page_icon="🤖",
    layout="centered"
)

# CSS مخصص
st.markdown("""
<style>
    .header {
        text-align: center;
        color: #FF4500;
        margin-bottom: 30px;
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
    .unknown { border-left: 5px solid #9e9e9e; background-color: #f5f5f5; }
    .stButton>button {
        background-color: #FF4500;
        color: white;
        font-weight: bold;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        width: 100%;
    }
    .debug-info {
        font-family: monospace;
        font-size: 0.8rem;
        background: #f5f5f5;
        padding: 10px;
        border-radius: 4px;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# عنوان التطبيق
st.markdown("<h1 class='header'>🤖 أداة التحقق التلقائي من Reddit</h1>", unsafe_allow_html=True)

# دالة متقدمة لاستخراج اسم المستخدم
def extract_username(input_url):
    try:
        if not input_url:
            return None
            
        input_url = input_url.strip().strip("/")
        
        # إذا كان اسم مستخدم مباشر بدون رابط
        if not any(x in input_url for x in ['http://', 'https://', 'reddit.com']):
            return re.sub(r'[^a-zA-Z0-9_-]', '', input_url.split('?')[0].split('/')[0])
        
        # معالجة الروابط
        parsed = urlparse(input_url)
        if not parsed.scheme:
            parsed = urlparse(f"https://{input_url}")
        
        path_parts = [p for p in parsed.path.split('/') if p]
        
        if 'user' in path_parts:
            return path_parts[path_parts.index('user') + 1]
        elif 'u' in path_parts:
            return path_parts[path_parts.index('u') + 1]
        
        return path_parts[0] if path_parts else None
    
    except Exception as e:
        st.error(f"خطأ في استخراج اسم المستخدم: {str(e)}")
        return None

# دالة التحقق المتقدمة باستخدام تقنيات متعددة
def advanced_reddit_check(username):
    if not username:
        return "❌ اسم مستخدم غير صحيح", "unknown", None, {}
    
    url = f"https://www.reddit.com/user/{username}/"
    api_url = f"https://www.reddit.com/user/{username}/about.json"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    debug_info = {"username": username, "checks": []}
    
    try:
        with httpx.Client(follow_redirects=True, timeout=15) as client:
            # التحقق من واجهة برمجة التطبيقات (API) أولاً
            api_response = client.get(api_url, headers=headers)
            debug_info["api_status"] = api_response.status_code
            
            if api_response.status_code == 200:
                try:
                    data = api_response.json()
                    if 'error' in data and data['error'] == 404:
                        debug_info["checks"].append("API: Account not found")
                        return "❌ الحساب غير موجود", "not-found", url, debug_info
                    if 'data' in data and 'is_suspended' in data['data']:
                        if data['data']['is_suspended']:
                            debug_info["checks"].append("API: Account suspended")
                            return "🔴 الحساب موقوف", "suspended", url, debug_info
                        else:
                            debug_info["checks"].append("API: Account active")
                            return "🟢 الحساب نشط", "active", url, debug_info
                except json.JSONDecodeError:
                    pass
            
            # إذا فشل API نلجأ لفحص الصفحة مباشرة
            response = client.get(url, headers=headers)
            debug_info["page_status"] = response.status_code
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # تحليل محتوى الصفحة بدقة
            page_text = soup.get_text().lower()
            debug_info["page_text_snippet"] = page_text[:200] + "..." if page_text else ""
            
            # قوائم الكلمات المفتاحية لكل حالة
            suspended_keywords = [
                "this account has been suspended",
                "account suspended",
                "suspended account",
                "content unavailable",
                "user suspended",
                "هذا الحساب موقوف"
            ]
            
            not_found_keywords = [
                "page not found",
                "sorry, nobody on reddit goes by that name",
                "there's nobody on reddit by that name",
                "user not found",
                "لا يوجد مستخدم بهذا الاسم"
            ]
            
            active_indicators = [
                f"u/{username}",
                f"user/{username}",
                "post karma",
                "comment karma",
                "cake day",
                "منشورات",
                "تعليقات"
            ]
            
            # التحقق من الحساب الموقوف
            if any(kw in page_text for kw in suspended_keywords):
                debug_info["checks"].append("Page: Suspended keywords found")
                return "🔴 الحساب موقوف", "suspended", url, debug_info
            
            # التحقق من الحساب غير موجود
            if response.status_code == 404 or any(kw in page_text for kw in not_found_keywords):
                debug_info["checks"].append("Page: Not found indicators")
                return "❌ الحساب غير موجود", "not-found", url, debug_info
            
            # التحقق من الحساب النشط
            if response.status_code == 200:
                # البحث عن عناصر وصفية محددة
                profile_header = soup.find("div", {"class": "profile-header"})
                profile_tabs = soup.find("div", {"class": "profile-tabs"})
                
                if any(ind in page_text for ind in active_indicators) or (profile_header and profile_tabs):
                    debug_info["checks"].append("Page: Active indicators found")
                    return "🟢 الحساب نشط", "active", url, debug_info
            
            # إذا لم يتم التعرف على الحالة
            debug_info["checks"].append("Page: No clear indicators")
            return "⚠️ لم يتم التأكد من الحالة", "unknown", url, debug_info
    
    except httpx.TimeoutException:
        debug_info["error"] = "Request timeout"
        return "⚠️ انتهت مهلة الطلب", "unknown", url, debug_info
    except Exception as e:
        debug_info["error"] = str(e)
        return f"⚠️ حدث خطأ: {str(e)}", "unknown", url, debug_info

# واجهة المستخدم
input_url = st.text_input(
    "أدخل رابط حساب Reddit أو اسم المستخدم:",
    placeholder="مثال: nedaa_7 أو https://www.reddit.com/user/nedaa_7/",
    key="user_input"
)

check_button = st.button("تحقق تلقائيًا")

# معالجة النتيجة
if check_button:
    if input_url:
        with st.spinner("جاري التحقق التلقائي بدقة عالية..."):
            username = extract_username(input_url)
            
            if username:
                status, status_class, profile_url, debug_info = advanced_reddit_check(username)
                
                # عرض النتيجة
                st.markdown(
                    f"""
                    <div class="result-box {status_class}">
                        <h3>{status}</h3>
                        <p><strong>اسم المستخدم:</strong> {username}</p>
                        <p><strong>الرابط:</strong> {profile_url}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # إظهار تفاصيل إضافية
                with st.expander("تفاصيل التحقق", expanded=False):
                    st.write("**طريقة التحقق:**")
                    if "API" in str(debug_info.get("checks", [])):
                        st.success("تم استخدام واجهة برمجة التطبيقات (API) للتحقق")
                    else:
                        st.info("تم فحص الصفحة مباشرة")
                    
                    st.write("**معلومات تقنية:**")
                    st.json(debug_info)
            else:
                st.error("⚠️ لم يتم التعرف على اسم مستخدم صحيح")
    else:
        st.warning("⚠️ يرجى إدخال رابط أو اسم مستخدم أولاً")

# تذييل الصفحة
st.markdown("---")
st.markdown("""
<p style="text-align: center; color: #666; font-size: 0.9rem;">
    أداة التحقق التلقائي المتقدمة | لا تحتاج لأي تدخل يدوي
</p>
""", unsafe_allow_html=True)
