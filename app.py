import streamlit as st
import httpx
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urlparse

# إعداد واجهة المستخدم
st.set_page_config(
    page_title="فحص حالة حساب Reddit", 
    page_icon="🔍", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# تصميم الواجهة الرئيسية
st.title("🔎 فحص حالة حساب Reddit")
st.markdown("""
<div style='text-align: center; padding: 20px; background-color: #f0f2f6; border-radius: 10px; margin-bottom: 30px;'>
    <h3 style='color: #FF4500;'>أداة التحقق من حسابات Reddit</h3>
    <p>تحقق من حالة أي حساب Reddit (نشط/موقوف/غير موجود)</p>
</div>
""", unsafe_allow_html=True)

# دوال المعالجة المحسنة
def clean_username(input_text):
    """استخراج اسم المستخدم من النص المدخل"""
    input_text = input_text.strip()
    
    # إزالة الروابط الكاملة واستخراج اسم المستخدم
    if "reddit.com" in input_text:
        match = re.search(r'/(?:u|user)/([^/?]+)', input_text)
        if match:
            return match.group(1)
    
    # إزالة البادئات الشائعة
    input_text = re.sub(r'^(u/|user/|@|/)', '', input_text)
    
    # إزالة الأحرف غير المسموحة
    username = re.sub(r'[^a-zA-Z0-9_-]', '', input_text)
    
    return username

def build_reddit_url(username):
    """بناء رابط Reddit الصحيح"""
    return f"https://www.reddit.com/user/{username}"

def check_reddit_status(username):
    """فحص حالة الحساب مع كشف دقيق للحالات المختلفة"""
    if not username or len(username) < 3:
        return "❌ اسم المستخدم غير صالح", None
    
    url = build_reddit_url(username)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    try:
        with httpx.Client(timeout=20, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            
            # التحقق من كود الحالة أولاً
            if response.status_code == 404:
                return "❌ غير موجود", url
            elif response.status_code == 403:
                return "🚫 محظور أو موقوف", url
            elif response.status_code != 200:
                return f"⚠️ خطأ HTTP: {response.status_code}", url
            
            # تحليل شامل لمحتوى الصفحة
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 1. فحص shreddit-forbidden بالتحديد (الأهم)
            forbidden_div = soup.find('div', {'id': 'shreddit-forbidden'})
            if forbidden_div:
                # البحث عن رسالة الإيقاف داخل هذا العنصر
                suspended_title = forbidden_div.find('h1', {'id': 'shreddit-forbidden-title'})
                if suspended_title and "suspended" in suspended_title.get_text().lower():
                    return "🚫 موقوف", url
                
                # أو فحص النص الكامل في العنصر المحظور
                forbidden_text = forbidden_div.get_text().lower()
                if "suspended" in forbidden_text:
                    return "🚫 موقوف", url
                elif "not found" in forbidden_text or "doesn't exist" in forbidden_text:
                    return "❌ غير موجود", url
            
            # 2. فحص العناصر الأخرى للإيقاف
            suspended_elements = [
                soup.find('div', {'id': re.compile(r'.*suspend.*', re.I)}),
                soup.find('div', {'class': re.compile(r'.*suspend.*', re.I)}),
                soup.find('h1', string=re.compile(r'.*suspended.*', re.I)),
                soup.find('p', string=re.compile(r'.*suspended.*', re.I))
            ]
            
            for element in suspended_elements:
                if element:
                    return "🚫 موقوف", url
            
            # 3. فحص النص الكامل للكلمات المفتاحية
            full_text = soup.get_text(separator=' ', strip=True).lower()
            
            # علامات الحساب الموقوف
            suspended_patterns = [
                "this account has been suspended",
                "account has been suspended", 
                "user has been suspended",
                "suspended account",
                "account suspended",
                "permanently suspended",
                "temporarily suspended",
                "banned account",
                "account banned"
            ]
            
            for pattern in suspended_patterns:
                if pattern in full_text:
                    return "🚫 موقوف", url
            
            # 4. فحص علامات الحساب المحذوف
            deleted_patterns = [
                "this user has deleted their account",
                "account has been deleted",
                "user deleted their account",
                "deleted account",
                "account deleted"
            ]
            
            for pattern in deleted_patterns:
                if pattern in full_text:
                    return "🗑️ محذوف", url
            
            # 5. فحص العناصر التي تدل على حساب نشط
            # البحث عن عناصر الملف الشخصي النشط
            active_selectors = [
                'div[data-testid="user-profile"]',
                'div[data-testid="profile-hover-card"]',
                'section[aria-label*="profile"]',
                'div[class*="profile"]',
                'div[data-testid*="post"]',
                'div[data-testid*="comment"]'
            ]
            
            has_active_elements = False
            for selector in active_selectors:
                if soup.select(selector):
                    has_active_elements = True
                    break
            
            # 6. فحص النص للكلمات المفتاحية للحساب النشط
            active_keywords = [
                "post karma", "comment karma", "joined reddit",
                "cake day", "trophy case", "overview",
                "posts", "comments", "about", "karma:",
                "reddit premium", "achievements"
            ]
            
            has_active_text = any(keyword in full_text for keyword in active_keywords)
            
            # 7. القرار النهائي
            if has_active_elements or has_active_text:
                return "✅ نشط", url
            elif "reddit" in full_text and len(full_text) > 300:
                # التحقق من وجود عناصر الواجهة العامة
                if any(word in full_text for word in ["user", "profile", "redditor"]):
                    return "✅ نشط", url
                else:
                    return "❓ حالة غير واضحة", url
            else:
                return "❌ غير موجود", url
                    
    except httpx.TimeoutException:
        return "⏱️ انتهت مهلة الاتصال", url
    except httpx.ConnectError:
        return "🌐 خطأ في الاتصال بالإنترنت", url
    except Exception as e:
        return f"⚠️ خطأ غير متوقع: {str(e)[:50]}...", url

# واجهة الإدخال المحسنة
col1, col2 = st.columns([3, 1])

with col1:
    user_input = st.text_input(
        "اسم المستخدم أو رابط الحساب:",
        placeholder="مثال: username أو u/username أو https://reddit.com/u/username",
        help="يمكنك إدخال اسم المستخدم بأي صيغة"
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)  # مساحة فارغة للمحاذاة
    check_button = st.button("🔍 فحص الحساب", type="primary")

if check_button and user_input.strip():
    username = clean_username(user_input)
    
    if not username:
        st.error("❌ يرجى إدخال اسم مستخدم صالح")
    else:
        # عرض معلومات الفحص
        st.info(f"🔍 جارٍ فحص الحساب: **{username}**")
        
        # شريط التقدم
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
        
        # فحص الحساب
        status, url = check_reddit_status(username)
        
        # إزالة شريط التقدم
        progress_bar.empty()
        status_text.empty()
        
        # عرض النتيجة مع تصميم مميز
        st.markdown("---")
        st.subheader("📊 نتيجة الفحص:")
        
        if status.startswith("✅"):
            st.success(f"**{status}**")
            st.balloons()  # تأثير بصري للنجاح
            if url:
                st.markdown(f"🔗 [زيارة الحساب]({url})")
        elif status.startswith("🚫"):
            st.error(f"**{status}**")
        elif status.startswith("❌") or status.startswith("🗑️"):
            st.warning(f"**{status}**")
        else:
            st.info(f"**{status}**")
        
        # معلومات إضافية
        with st.expander("📋 تفاصيل الفحص"):
            st.write(f"**اسم المستخدم:** {username}")
            if url:
                st.write(f"**الرابط:** {url}")
            st.write(f"**وقت الفحص:** {time.strftime('%Y-%m-%d %H:%M:%S')}")

elif check_button:
    st.warning("⚠️ يرجى إدخال اسم مستخدم أو رابط الحساب أولاً")



# تذييل الصفحة
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>🛠️ تم تطوير هذه الأداة لمساعدتك في فحص حسابات Reddit بسهولة وسرعة</p>
    <p>💻 مطور بتقنية Streamlit | 🔒 آمن وسريع</p>
</div>
""", unsafe_allow_html=True)
