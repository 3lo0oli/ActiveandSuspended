import streamlit as st
import httpx
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup

# إعدادات الصفحة
st.set_page_config(
    page_title="أداة التحقق الفعلي من الحسابات",
    page_icon="🌐",
    layout="wide"
)

# CSS مخصص
st.markdown("""
<style>
    .header {
        text-align: center;
        color: #2b5876;
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
    .deleted { border-left: 5px solid #607d8b; background-color: #eceff1; }
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
    .tab-content {
        padding: 20px;
        background: #f9f9f9;
        border-radius: 8px;
        margin-top: 10px;
    }
    .screenshot {
        max-width: 100%;
        border: 1px solid #ddd;
        border-radius: 4px;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# عنوان التطبيق
st.markdown("<h1 class='header'>🌐 أداة التحقق الفعلي من حالة الحسابات</h1>", unsafe_allow_html=True)

# تبويب المنصات
platform = st.selectbox(
    "اختر المنصة:",
    ["Reddit", "Facebook", "Twitter", "Instagram", "LinkedIn"],
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
        
        elif platform == "Instagram":
            if "instagram.com" not in url:
                return url.split("/")[0].replace("@", "")
            return url.split("instagram.com/")[-1].split("/")[0].split("?")[0]
        
        elif platform == "LinkedIn":
            if "linkedin.com" not in url:
                return url.split("/")[0].replace("@", "")
            return url.split("linkedin.com/in/")[-1].split("/")[0].split("?")[0]
    
    except Exception as e:
        st.error(f"حدث خطأ في استخراج اسم المستخدم: {str(e)}")
        return None

# دالة لفحص المحتوى الفعلي للصفحة
def check_page_content(url, platform):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    try:
        with httpx.Client(follow_redirects=True, timeout=20) as client:
            response = client.get(url, headers=headers)
            html = response.text.lower()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # إزالة النصوص المخفية وغير الضرورية
            for script in soup(["script", "style", "noscript", "meta", "link"]):
                script.decompose()
            
            visible_text = soup.get_text().lower()
            
            if platform == "Reddit":
                if response.status_code == 404 or "page not found" in visible_text:
                    return "❌ الحساب غير موجود", "not-found"
                
                if ("suspended" in visible_text or 
                    "content unavailable" in visible_text or
                    "this account has been suspended" in visible_text):
                    return "🔴 الحساب موقوف", "suspended"
                
                if response.status_code == 200 and ("karma" in html or "cake day" in html):
                    return "🟢 الحساب نشط", "active"
            
            elif platform == "Facebook":
                if response.status_code == 404 or "page not found" in visible_text:
                    return "❌ الحساب غير موجود", "not-found"
                
                if ("content isn't available" in visible_text or 
                    "this page isn't available" in visible_text or
                    "تم حظر هذه الصفحة" in visible_text):
                    return "🔴 الحساب محظور", "suspended"
                
                if response.status_code == 200 and ("timeline" in html or "posts" in html):
                    return "🟢 الحساب نشط", "active"
            
            elif platform == "Twitter":
                if response.status_code == 404 or "page doesn't exist" in visible_text:
                    return "❌ الحساب غير موجود", "not-found"
                
                if ("account suspended" in visible_text or 
                    "هذا الحساب معلق" in visible_text or
                    "このアカウントは停止されています" in visible_text):
                    return "🔴 الحساب موقوف", "suspended"
                
                if response.status_code == 200 and ("tweets" in html or "following" in html):
                    return "🟢 الحساب نشط", "active"
            
            elif platform == "Instagram":
                if response.status_code == 404 or "page not found" in visible_text:
                    return "❌ الحساب غير موجود", "not-found"
                
                if ("sorry, this page isn't available" in visible_text or 
                    "عذرًا، هذه الصفحة غير متوفرة" in visible_text):
                    return "🔴 الحساب محظور", "suspended"
                
                if response.status_code == 200 and ("posts" in html or "followers" in html):
                    return "🟢 الحساب نشط", "active"
            
            elif platform == "LinkedIn":
                if response.status_code == 404 or "page not found" in visible_text:
                    return "❌ الحساب غير موجود", "not-found"
                
                if ("this profile is unavailable" in visible_text or 
                    "هذا الملف غير متاح" in visible_text):
                    return "🔴 الحساب محظور", "suspended"
                
                if response.status_code == 200 and ("experience" in html or "education" in html):
                    return "🟢 الحساب نشط", "active"
            
            return "⚠️ لم يتم التأكد من الحالة", "unknown"
    
    except httpx.TimeoutException:
        return "⚠️ انتهت مهلة الطلب", "unknown"
    except Exception as e:
        return f"⚠️ خطأ في الاتصال: {str(e)}", "unknown"

# واجهة المستخدم
user_input = st.text_input(
    f"أدخل رابط الحساب أو اسم المستخدم على {platform}:",
    placeholder=f"مثال: username أو https://{'reddit.com' if platform == 'Reddit' else 'facebook.com' if platform == 'Facebook' else 'twitter.com' if platform == 'Twitter' else 'instagram.com' if platform == 'Instagram' else 'linkedin.com'}/username"
)

check_button = st.button("تحقق الآن")

# معالجة النتيجة
if check_button:
    if user_input:
        with st.spinner("جاري فتح الرابط والتحقق من المحتوى الفعلي..."):
            username = extract_username(user_input, platform)
            
            if username:
                if platform == "Reddit":
                    url = f"https://www.reddit.com/user/{username}/"
                elif platform == "Facebook":
                    url = f"https://www.facebook.com/{username}/"
                elif platform == "Twitter":
                    url = f"https://twitter.com/{username}/"
                elif platform == "Instagram":
                    url = f"https://instagram.com/{username}/"
                elif platform == "LinkedIn":
                    url = f"https://linkedin.com/in/{username}/"
                
                status, status_class = check_page_content(url, platform)
                
                # عرض النتيجة
                st.markdown(
                    f"""
                    <div class="result-box {status_class}">
                        <h3>{status}</h3>
                        <p><strong>اسم المستخدم:</strong> {username}</p>
                        <p><strong>رابط الحساب:</strong> <a href="{url}" target="_blank">{url}</a></p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # عرض معلومات إضافية
                with st.expander("تفاصيل إضافية", expanded=False):
                    st.write(f"**كود الحالة:** {status.split(' ')[0]}")
                    st.write(f"**الرابط الذي تم فحصه:** [{url}]({url})")
                    
                    if status_class == "active":
                        st.success("تم العثور على الحساب وهو نشط. يمكنك زيارة الرابط أعلاه لمشاهدة المحتوى.")
                    elif status_class == "suspended":
                        st.error("الحساب موقوف أو محظور. هذا يعني أن المنصة قد قامت بتعطيل الحساب.")
                    elif status_class == "not-found":
                        st.warning("الحساب غير موجود أو تم حذفه. تأكد من صحة اسم المستخدم.")
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
    أداة متقدمة للتحقق من حالة الحسابات | تعمل بفحص المحتوى الفعلي للصفحات
</p>
""", unsafe_allow_html=True)
