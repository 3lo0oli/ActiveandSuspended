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
    """فحص حالة الحساب مع كشف دقيق جداً للحالات المختلفة"""
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
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Cache-Control": "no-cache"
    }
    
    try:
        with httpx.Client(timeout=25, follow_redirects=True) as client:
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
            
            # إزالة المساحات الزائدة من HTML
            clean_html = re.sub(r'\s+', ' ', html_content.lower())
            full_text = soup.get_text(separator=' ', strip=True).lower()
            
            # ============ 1. فحص الحسابات الموقوفة أولاً (أولوية عالية) ============
            
            # أ) فحص shreddit-forbidden بالتحديد
            forbidden_div = soup.find('div', {'id': 'shreddit-forbidden'})
            if forbidden_div:
                forbidden_text = forbidden_div.get_text().lower()
                # التأكد من وجود كلمة suspended مع تجاهل الكلمات الأخرى
                if "suspended" in forbidden_text and "account" in forbidden_text:
                    return "🚫 موقوف", url
                # فحص العنوان المحدد
                title_element = forbidden_div.find('h1', {'id': 'shreddit-forbidden-title'})
                if title_element and "suspended" in title_element.get_text().lower():
                    return "🚫 موقوف", url
            
            # ب) فحص العناصر الأخرى للإيقاف
            suspended_selectors = [
                'div[id*="forbidden"]',
                'div[class*="suspended"]',
                'div[data-testid*="suspended"]',
                '.suspended-account',
                '#suspended-message'
            ]
            
            for selector in suspended_selectors:
                elements = soup.select(selector)
                for element in elements:
                    if element and "suspended" in element.get_text().lower():
                        return "🚫 موقوف", url
            
            # ج) فحص النصوص الدالة على الإيقاف بدقة عالية
            suspended_exact_phrases = [
                "this account has been suspended",
                "account has been suspended", 
                "user has been suspended",
                "account is suspended",
                "suspended account",
                "permanently suspended",
                "temporarily suspended"
            ]
            
            for phrase in suspended_exact_phrases:
                if phrase in full_text:
                    return "🚫 موقوف", url
            
            # ============ 2. فحص الحسابات المحذوفة ============
            deleted_exact_phrases = [
                "this user has deleted their account",
                "user deleted their account",
                "account has been deleted",
                "deleted their account"
            ]
            
            for phrase in deleted_exact_phrases:
                if phrase in full_text:
                    return "🗑️ محذوف", url
            
            # ============ 3. فحص الحسابات النشطة (بعد التأكد من عدم الإيقاف) ============
            
            # أ) البحث عن عناصر الملف الشخصي النشط
            active_profile_selectors = [
                'div[data-testid="user-profile"]',
                'div[data-testid="profile-hover-card"]',
                'section[aria-label*="profile"]',
                'div[class*="user-profile"]',
                'main[role="main"]',
                'div[data-testid*="profile"]'
            ]
            
            has_profile_elements = False
            for selector in active_profile_selectors:
                if soup.select(selector):
                    has_profile_elements = True
                    break
            
            # ب) البحث عن محتوى المستخدم
            content_selectors = [
                'div[data-testid*="post"]',
                'div[data-testid*="comment"]',
                'article',
                '.post',
                'div[class*="post"]'
            ]
            
            has_content_elements = False
            for selector in content_selectors:
                if soup.select(selector):
                    has_content_elements = True
                    break
            
            # ج) فحص الكلمات المفتاحية للحساب النشط
            active_keywords = [
                "post karma", "comment karma", "awardee karma",
                "cake day", "joined", "reddit premium",
                "trophy case", "overview", "posts", "comments",
                "about", "karma", "achievements", "badges"
            ]
            
            has_active_keywords = sum(1 for keyword in active_keywords if keyword in full_text)
            
            # د) فحص عناصر التنقل في الملف الشخصي
            navigation_elements = [
                soup.find('nav'),
                soup.find('div', {'role': 'tablist'}),
                soup.select('a[href*="posts"]'),
                soup.select('a[href*="comments"]'),
                soup.select('a[href*="overview"]')
            ]
            
            has_navigation = any(element for element in navigation_elements if element)
            
            # ============ 4. القرار النهائي المحسن ============
            
            # إذا وُجدت عناصر الملف الشخصي + محتوى أو كلمات مفتاحية
            if has_profile_elements and (has_content_elements or has_active_keywords >= 2):
                return "✅ نشط", url
            
            # إذا وُجدت عناصر التنقل + كلمات مفتاحية
            elif has_navigation and has_active_keywords >= 1:
                return "✅ نشط", url
            
            # إذا وُجدت كلمات مفتاحية كثيرة (دليل على النشاط)
            elif has_active_keywords >= 3:
                return "✅ نشط", url
            
            # فحص وجود محتوى Reddit عام
            elif "reddit" in full_text and len(full_text) > 200:
                # التحقق من عدم وجود رسائل خطأ
                error_indicators = ["error", "not found", "doesn't exist", "unavailable"]
                has_errors = any(error in full_text for error in error_indicators)
                
                if not has_errors and any(word in full_text for word in ["user", "profile", "redditor"]):
                    return "✅ نشط", url
                else:
                    return "❓ حالة غير واضحة", url
            
            # إذا لم توجد أي علامات واضحة
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
