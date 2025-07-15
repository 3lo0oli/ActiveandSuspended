import streamlit as st
import httpx
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup

# إعدادات الصفحة
st.set_page_config(
    page_title="أداة التحقق من حسابات Reddit بدقة",
    page_icon="🔍",
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
    .user-info {
        background: #f0f2f5;
        padding: 15px;
        border-radius: 8px;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)

# عنوان التطبيق
st.markdown("<h1 class='header'>🔍 أداة التحقق من حسابات Reddit بدقة</h1>", unsafe_allow_html=True)

# دالة لاستخراج اسم المستخدم من الرابط
def extract_reddit_username(input_url):
    try:
        if not input_url:
            return None
            
        # تنظيف المدخلات
        input_url = input_url.strip().strip("/").replace("https://", "").replace("http://", "")
        
        if "reddit.com" not in input_url:
            return input_url.split("/")[0].replace("u/", "").replace("@", "")
        
        if "/user/" in input_url:
            return input_url.split("/user/")[-1].split("/")[0]
        elif "/u/" in input_url:
            return input_url.split("/u/")[-1].split("/")[0]
        
        return input_url.split("reddit.com/")[-1].split("/")[0]
    
    except Exception as e:
        st.error(f"حدث خطأ في استخراج اسم المستخدم: {str(e)}")
        return None

# دالة التحقق من حالة الحساب مع فحص محتوى الصفحة
def check_reddit_account(username):
    if not username:
        return "❌ لم يتم تقديم اسم مستخدم صحيح", "unknown", None
    
    url = f"https://www.reddit.com/user/{username}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    try:
        with httpx.Client(follow_redirects=True, timeout=15) as client:
            response = client.get(url, headers=headers)
            
            # تحليل محتوى الصفحة باستخدام BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # البحث عن علامات الحساب الموقوف
            suspended_keywords = [
                "this account has been suspended",
                "account suspended",
                "suspended account",
                "content unavailable"
            ]
            
            # البحث عن علامات الحساب غير موجود
            not_found_keywords = [
                "page not found",
                "sorry, nobody on reddit goes by that name",
                "there's nobody on reddit by that name"
            ]
            
            # النص الكامل للصفحة
            page_text = soup.get_text().lower()
            
            # التحقق من الحساب الموقوف
            if any(keyword in page_text for keyword in suspended_keywords):
                return "🔴 الحساب موقوف (Suspended)", "suspended", url
            
            # التحقق من الحساب غير موجود
            if response.status_code == 404 or any(keyword in page_text for keyword in not_found_keywords):
                return "❌ الحساب غير موجود (404)", "not-found", url
            
            # التحقق من الحساب النشط
            if response.status_code == 200:
                # البحث عن عناصر خاصة بحساب نشط
                user_profile = soup.find("div", {"class": "profile-header"})
                user_posts = soup.find("div", {"id": "profile-posts"})
                
                if user_profile or user_posts:
                    return "🟢 الحساب نشط (Active)", "active", url
            
            # إذا لم يتم التعرف على الحالة
            return "⚠️ لم يتم التأكد من الحالة بدقة", "unknown", url
    
    except httpx.TimeoutException:
        return "⚠️ انتهت مهلة الطلب", "unknown", url
    except Exception as e:
        return f"⚠️ حدث خطأ: {str(e)}", "unknown", url

# واجهة المستخدم
input_url = st.text_input(
    "أدخل رابط حساب Reddit أو اسم المستخدم:",
    placeholder="مثال: hedaa_7 أو https://www.reddit.com/user/hedaa_7/",
    key="user_input"
)

check_button = st.button("تحقق الآن")

# معالجة النتيجة
if check_button:
    if input_url:
        with st.spinner("جاري فحص الحساب بدقة..."):
            username = extract_reddit_username(input_url)
            
            if username:
                status, status_class, profile_url = check_reddit_account(username)
                
                # عرض النتيجة
                st.markdown(
                    f"""
                    <div class="result-box {status_class}">
                        <h3>{status}</h3>
                        <div class="user-info">
                            <p><strong>اسم المستخدم:</strong> {username}</p>
                            <p><strong>رابط الحساب:</strong> <a href="{profile_url}" target="_blank">{profile_url}</a></p>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # إضافة تفسير للحالة
                if status_class == "active":
                    st.success("تم العثور على الحساب وهو نشط. يمكنك زيارة الرابط أعلاه لمشاهدة المحتوى.")
                elif status_class == "suspended":
                    st.error("هذا الحساب موقوف من قبل إدارة Reddit. لا يمكن عرض المحتوى.")
                elif status_class == "not-found":
                    st.warning("لا يوجد حساب بهذا الاسم. تأكد من كتابة اسم المستخدم بشكل صحيح.")
                else:
                    st.info("لم نتمكن من تحديد حالة الحساب بدقة. يمكنك زيارة الرابط للتحقق يدويًا.")
            else:
                st.error("⚠️ لم نتمكن من استخراج اسم مستخدم صحيح من الرابط المدخل")
    else:
        st.warning("⚠️ يرجى إدخال رابط الحساب أو اسم المستخدم أولاً")

# تذييل الصفحة
st.markdown("---")
st.markdown("""
<p style="text-align: center; color: #666; font-size: 0.9rem;">
    أداة متقدمة للتحقق من حسابات Reddit | تعمل بفحص المحتوى الفعلي للصفحات
</p>
""", unsafe_allow_html=True)
