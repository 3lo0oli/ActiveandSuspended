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
    """فحص حالة الحساب مع كشف دقيق ومتوازن"""
    if not username or len(username) < 3:
        return "❌ اسم المستخدم غير صالح", None
    
    url = build_reddit_url(username)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        with httpx.Client(timeout=20, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            
            # فحص 404 بس (الوحيد المؤكد)
            if response.status_code == 404:
                return "❌ غير موجود", url
            
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            full_text = soup.get_text(separator=' ', strip=True).lower()
            
            # ============ 1. فحص الإيقاف أولاً (صارم جداً) ============
            
            # أ) فحص shreddit-forbidden مع التأكد المطلق
            forbidden_div = soup.find('div', {'id': 'shreddit-forbidden'})
            if forbidden_div:
                forbidden_text = forbidden_div.get_text().strip().lower()
                # التأكد من النص الدقيق
                if "this account has been suspended" in forbidden_text:
                    return "🚫 موقوف", url
                
                # فحص العنوان بدقة
                title_h1 = forbidden_div.find('h1')
                if title_h1:
                    title_text = title_h1.get_text().strip().lower()
                    if "suspended" in title_text and "account" in title_text:
                        return "🚫 موقوف", url
            
            # ب) فحص النصوص الدقيقة للإيقاف
            suspended_phrases = [
                "this account has been suspended",
                "account has been suspended",
                "user has been suspended",
                "permanently suspended",
                "temporarily suspended"
            ]
            
            for phrase in suspended_phrases:
                if phrase in full_text:
                    return "🚫 موقوف", url
            
            # ج) فحص العناصر المخصصة للإيقاف
            if soup.find('div', {'class': lambda x: x and 'suspended' in x.lower()}):
                return "🚫 موقوف", url
            
            # ============ 2. فحص الحذف ============
            deleted_phrases = [
                "this user has deleted their account",
                "user deleted their account",
                "account has been deleted"
            ]
            
            for phrase in deleted_phrases:
                if phrase in full_text:
                    return "🗑️ محذوف", url
            
            # ============ 3. فحص النشاط (معايير صارمة) ============
            
            # عدد النقاط المطلوبة للحكم بالنشاط
            activity_score = 0
            
            # أ) عناصر الملف الشخصي القوية (+3 نقاط)
            strong_profile_elements = [
                soup.find('div', {'data-testid': 'user-profile'}),
                soup.select('div[data-testid*="profile"]'),
                soup.find('main', {'role': 'main'})  # الصفحة الرئيسية للمستخدم
            ]
            
            if any(element for element in strong_profile_elements if element):
                activity_score += 3
            
            # ب) محتوى المستخدم (+2 نقاط)
            user_content_elements = [
                soup.select('div[data-testid*="post"]'),
                soup.select('div[data-testid*="comment"]'),
                soup.select('article')
            ]
            
            if any(element for element in user_content_elements if element):
                activity_score += 2
            
            # ج) كلمات مفتاحية قوية (+1 نقطة لكل كلمة)
            strong_keywords = [
                "post karma", "comment karma", "awardee karma",
                "cake day", "joined reddit", "reddit premium"
            ]
            
            for keyword in strong_keywords:
                if keyword in full_text:
                    activity_score += 1
            
            # د) كلمات مفتاحية متوسطة (+0.5 نقطة لكل كلمة)
            medium_keywords = [
                "trophy case", "overview", "posts", "comments",
                "about", "achievements", "submitted"
            ]
            
            medium_score = sum(0.5 for keyword in medium_keywords if keyword in full_text)
            activity_score += medium_score
            
            # هـ) عناصر التنقل (+1 نقطة)
            navigation_elements = [
                soup.find('nav'),
                soup.select('a[href*="posts"]'),
                soup.select('a[href*="comments"]'),
                soup.select('a[href*="overview"]')
            ]
            
            if any(element for element in navigation_elements if element):
                activity_score += 1
            
            # و) عناصر التفاعل (+1 نقطة)
            interaction_elements = [
                soup.find('button'),
                soup.select('[class*="vote"]'),
                soup.select('[class*="karma"]')
            ]
            
            if any(element for element in interaction_elements if element):
                activity_score += 1
            
            # ============ 4. القرار النهائي بناءً على النقاط ============
            
            # نشط: يحتاج 4+ نقاط
            if activity_score >= 4:
                return "✅ نشط", url
            
            # نشاط محدود: 2-3 نقاط
            elif activity_score >= 2:
                # التحقق من عدم وجود علامات خطأ
                error_signs = [
                    "not found", "doesn't exist", "unavailable",
                    "removed", "no longer exists"
                ]
                has_errors = any(error in full_text for error in error_signs)
                
                if not has_errors:
                    return "✅ نشط", url
                else:
                    return "❌ غير موجود", url
            
            # نقاط قليلة: فحص إضافي
            elif activity_score >= 1:
                # إذا كان هناك محتوى Reddit كافي بدون أخطاء
                if "reddit" in full_text and len(full_text) > 300:
                    error_signs = ["not found", "doesn't exist", "error"]
                    has_errors = any(error in full_text for error in error_signs)
                    
                    if not has_errors and "user" in full_text:
                        return "❓ حالة غير واضحة", url
                    else:
                        return "❌ غير موجود", url
                else:
                    return "❌ غير موجود", url
            
            # لا توجد نقاط كافية
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
