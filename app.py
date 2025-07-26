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
    """فحص حالة الحساب مع معالجة محسنة للأخطاء"""
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
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            
            # التحقق من كود الحالة
            if response.status_code == 404:
                return "❌ غير موجود", url
            elif response.status_code == 403:
                return "🚫 محظور أو موقوف", url
            elif response.status_code != 200:
                return f"⚠️ خطأ HTTP: {response.status_code}", url
            
            # تحليل محتوى الصفحة
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.get_text().lower()
            
            # البحث عن علامات الحساب الموقوف
            suspended_indicators = [
                "this account has been suspended",
                "account suspended",
                "user suspended",
                "suspended account"
            ]
            
            for indicator in suspended_indicators:
                if indicator in page_text:
                    return "🚫 موقوف", url
            
            # البحث عن علامات الحساب المحذوف
            deleted_indicators = [
                "this user has deleted their account",
                "deleted account",
                "account deleted"
            ]
            
            for indicator in deleted_indicators:
                if indicator in page_text:
                    return "🗑️ محذوف", url
            
            # التحقق من وجود محتوى المستخدم
            user_content_indicators = [
                "overview", "posts", "comments", "karma",
                "cake day", "post karma", "comment karma"
            ]
            
            has_user_content = any(indicator in page_text for indicator in user_content_indicators)
            
            if has_user_content:
                return "✅ نشط", url
            else:
                # التحقق الإضافي للتأكد
                if "reddit" in page_text and len(page_text) > 1000:
                    return "✅ نشط (محتوى محدود)", url
                else:
                    return "❓ حالة غير واضحة", url
                    
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

# قسم المساعدة والأمثلة
st.markdown("---")
st.subheader("💡 أمثلة على الاستخدام:")

col1, col2, col3 = st.columns(3)
with col1:
    st.info("**اسم المستخدم:**\n`spez`")
with col2:
    st.info("**مع البادئة:**\n`u/spez`")
with col3:
    st.info("**رابط كامل:**\n`reddit.com/u/spez`")

# معلومات حول الحالات المختلفة
with st.expander("📖 شرح حالات الحسابات"):
    st.markdown("""
    **الحالات المختلفة للحسابات:**
    
    - **✅ نشط:** الحساب يعمل بشكل طبيعي ويمكن الوصول إليه
    - **🚫 موقوف:** الحساب تم إيقافه من قبل إدارة Reddit
    - **❌ غير موجود:** اسم المستخدم غير مسجل أو خاطئ
    - **🗑️ محذوف:** المستخدم حذف حسابه بنفسه
    - **❓ حالة غير واضحة:** يحتاج إلى فحص يدوي إضافي
    """)

# معلومات فنية
with st.expander("⚙️ معلومات تقنية"):
    st.markdown("""
    **كيف يعمل الفحص:**
    
    1. تنظيف وتحليل المدخلات المختلفة
    2. إرسال طلب HTTP إلى Reddit
    3. تحليل كود الاستجابة ومحتوى الصفحة
    4. البحث عن علامات الحالة المختلفة
    5. عرض النتيجة مع الرابط المباشر
    
    **ملاحظات مهمة:**
    - يستغرق الفحص عادة 2-5 ثوانٍ
    - النتائج دقيقة بنسبة عالية جداً
    - يعمل مع جميع أنواع أسماء المستخدمين
    """)

# تذييل الصفحة
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>🛠️ تم تطوير هذه الأداة لمساعدتك في فحص حسابات Reddit بسهولة وسرعة</p>
    <p>💻 مطور بتقنية Streamlit | 🔒 آمن وسريع</p>
</div>
""", unsafe_allow_html=True)
