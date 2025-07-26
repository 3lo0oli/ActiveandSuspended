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
    """فحص حالة الحساب مع كشف دقيق جداً بدون الاعتماد على أكواد HTTP"""
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
            
            # لا نعتمد على كود الحالة - نحلل المحتوى مباشرة
            if response.status_code == 404:
                return "❌ غير موجود", url
            
            # حتى لو كان 403 أو أي كود آخر، نحلل المحتوى
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # إزالة المساحات الزائدة من HTML
            full_text = soup.get_text(separator=' ', strip=True).lower()
            
            # ============ 1. فحص الحسابات الموقوفة بدقة عالية ============
            
            # أ) فحص shreddit-forbidden مع التحقق الدقيق
            forbidden_div = soup.find('div', {'id': 'shreddit-forbidden'})
            if forbidden_div:
                forbidden_text = forbidden_div.get_text().lower()
                # التأكد من وجود النص الدقيق للإيقاف
                if ("suspended" in forbidden_text and "account" in forbidden_text) or \
                   ("this account has been suspended" in forbidden_text):
                    return "🚫 موقوف", url
                
                # فحص العنوان المحدد
                title_element = forbidden_div.find('h1', {'id': 'shreddit-forbidden-title'})
                if title_element:
                    title_text = title_element.get_text().lower()
                    if "suspended" in title_text:
                        return "🚫 موقوف", url
            
            # ب) فحص النصوص الدالة على الإيقاف بدقة عالية جداً
            suspended_exact_phrases = [
                "this account has been suspended",
                "account has been suspended", 
                "user has been suspended",
                "account is suspended",
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
            
            # ============ 3. فحص الحسابات النشطة (الأولوية للنشاط) ============
            
            # أ) البحث عن عناصر الملف الشخصي النشط
            active_profile_indicators = [
                # عناصر الملف الشخصي
                soup.find('div', {'data-testid': 'user-profile'}),
                soup.find('div', {'data-testid': 'profile-hover-card'}),
                soup.find('section', {'aria-label': lambda x: x and 'profile' in x.lower()}),
                soup.find('main', {'role': 'main'}),
                
                # عناصر المحتوى
                soup.select('div[data-testid*="post"]'),
                soup.select('div[data-testid*="comment"]'),
                soup.select('article'),
                
                # عناصر التنقل
                soup.find('nav'),
                soup.select('a[href*="posts"]'),
                soup.select('a[href*="comments"]'),
                soup.select('a[href*="overview"]')
            ]
            
            has_profile_elements = any(indicator for indicator in active_profile_indicators if indicator)
            
            # ب) فحص الكلمات المفتاحية للحساب النشط
            active_keywords = [
                "post karma", "comment karma", "awardee karma",
                "cake day", "joined", "reddit premium",
                "trophy case", "overview", "posts", "comments",
                "about", "karma", "achievements", "badges",
                "submitted", "gilded", "saved"
            ]
            
            active_keyword_matches = sum(1 for keyword in active_keywords if keyword in full_text)
            
            # ج) فحص عناصر واجهة Reddit النشطة
            ui_elements = [
                soup.find('button'),
                soup.find('input'),
                soup.select('[class*="vote"]'),
                soup.select('[class*="karma"]'),
                soup.select('[data-testid]')
            ]
            
            has_ui_elements = any(element for element in ui_elements if element)
            
            # د) فحص وجود محتوى المستخدم
            user_content_indicators = [
                "redditor for", "joined reddit", "reddit birthday",
                "post history", "comment history", "user since"
            ]
            
            has_user_content = any(indicator in full_text for indicator in user_content_indicators)
            
            # ============ 4. القرار النهائي المحسن (أولوية للنشاط) ============
            
            # إذا وُجدت عناصر الملف الشخصي أو كلمات مفتاحية كثيرة
            if has_profile_elements or active_keyword_matches >= 2:
                return "✅ نشط", url
            
            # إذا وُجدت عناصر واجهة المستخدم + محتوى المستخدم
            elif has_ui_elements and has_user_content:
                return "✅ نشط", url
            
            # إذا وُجدت كلمات مفتاحية للنشاط
            elif active_keyword_matches >= 1:
                return "✅ نشط", url
            
            # فحص وجود محتوى Reddit عام (حتى لو محدود)
            elif "reddit" in full_text and len(full_text) > 100:
                # التحقق من عدم وجود رسائل خطأ واضحة
                clear_error_indicators = [
                    "page not found", "user not found", "doesn't exist",
                    "no longer available", "been removed"
                ]
                has_clear_errors = any(error in full_text for error in clear_error_indicators)
                
                if not has_clear_errors:
                    # إذا كان هناك أي إشارة للمستخدم
                    if any(word in full_text for word in ["user", "profile", "redditor", "account"]):
                        return "✅ نشط", url
                    else:
                        return "❓ حالة غير واضحة", url
                else:
                    return "❌ غير موجود", url
            
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
