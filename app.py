import streamlit as st
import httpx
import re
import time
from mistralai import Mistral

st.set_page_config(page_title="Social Media Status Checker AI", page_icon="🔍", layout="wide")

st.title("🔍 فحص حالة حسابات السوشيال ميديا - AI Powered")
st.markdown("""
<div style='background-color:#e6f2ff;padding:15px;border-radius:10px;margin-bottom:20px'>
افحص حالة حسابات Twitter, Facebook, Instagram, TikTok, YouTube بذكاء اصطناعي
</div>
""", unsafe_allow_html=True)

# ==================== إعدادات Mistral AI ====================
MISTRAL_API_KEY = "W1orVB6xgdmK35su8wU4v3yU7c7TwbGa"
mistral_client = Mistral(api_key=MISTRAL_API_KEY)

# ==================== User Agents ====================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# ==================== دوال مساعدة ====================

def detect_platform(url):
    """كشف المنصة من الرابط"""
    url = url.lower()
    if 'twitter.com' in url or 'x.com' in url:
        return 'twitter'
    elif 'facebook.com' in url or 'fb.com' in url:
        return 'facebook'
    elif 'instagram.com' in url:
        return 'instagram'
    elif 'tiktok.com' in url:
        return 'tiktok'
    elif 'youtube.com' in url or 'youtu.be' in url:
        return 'youtube'
    return None

def extract_username(url, platform):
    """استخراج اسم المستخدم من الرابط"""
    url = url.strip()
    
    if platform == 'twitter':
        match = re.search(r'(?:twitter\.com|x\.com)/([^/?#]+)', url)
        return match.group(1) if match else url.replace('@', '').strip('/')
    
    elif platform == 'facebook':
        match = re.search(r'facebook\.com/(?:profile\.php\?id=)?([^/?#]+)', url)
        return match.group(1) if match else url.strip('/')
    
    elif platform == 'instagram':
        match = re.search(r'instagram\.com/([^/?#]+)', url)
        return match.group(1) if match else url.strip('/')
    
    elif platform == 'tiktok':
        match = re.search(r'tiktok\.com/@?([^/?#]+)', url)
        return match.group(1) if match else url.replace('@', '').strip('/')
    
    elif platform == 'youtube':
        if '/channel/' in url:
            match = re.search(r'/channel/([^/?#]+)', url)
            return match.group(1) if match else None
        elif '/@' in url:
            match = re.search(r'/@([^/?#]+)', url)
            return match.group(1) if match else None
        elif '/c/' in url:
            match = re.search(r'/c/([^/?#]+)', url)
            return match.group(1) if match else None
        elif '/user/' in url:
            match = re.search(r'/user/([^/?#]+)', url)
            return match.group(1) if match else None
    
    return url

def get_headers():
    """إنشاء headers واقعية"""
    import random
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "DNT": "1",
        "Connection": "keep-alive",
    }

# ==================== دالة Mistral AI للتحليل ====================

def analyze_with_mistral(page_content, username, platform):
    """تحليل محتوى الصفحة باستخدام Mistral AI - منطق بسيط"""
    
    # قص المحتوى 
    content_sample = page_content[:4000] if len(page_content) > 4000 else page_content
    
    prompt = f"""أنت محلل صفحات ويب. مهمتك بسيطة جداً:

اسم المستخدم المطلوب: {username}
المنصة: {platform}

محتوى الصفحة:
---
{content_sample}
---

السؤال البسيط:
هل اسم المستخدم "{username}" موجود وظاهر في هذه الصفحة؟

القواعد:
1. إذا وجدت اسم المستخدم ظاهر في الصفحة (في أي مكان) = أجب: ACTIVE
2. إذا الصفحة تقول "suspended" أو "موقوف" أو "banned" = أجب: SUSPENDED
3. إذا الصفحة تقول "not found" أو "doesn't exist" أو "page not available" = أجب: NOT_FOUND
4. في أي حالة أخرى = أجب: NOT_FOUND

أجب بكلمة واحدة فقط: ACTIVE أو SUSPENDED أو NOT_FOUND"""

    try:
        response = mistral_client.chat.complete(
            model="mistral-large-latest",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1  # دقة أعلى
        )
        
        result = response.choices[0].message.content.strip().upper()
        
        # تحويل النتيجة
        if "ACTIVE" in result:
            return "✅ نشط"
        elif "SUSPENDED" in result:
            return "🚫 موقوف"
        else:
            return "❌ معطل"
        
    except Exception as e:
        return "❓ خطأ في التحليل"

# ==================== دوال الفحص ====================

def check_account_with_ai(username, platform):
    """فحص الحساب باستخدام httpx + Mistral AI"""
    
    # بناء الرابط حسب المنصة
    if platform == 'twitter':
        urls_to_try = [
            f"https://twitter.com/{username}",
            f"https://x.com/{username}"
        ]
    elif platform == 'facebook':
        urls_to_try = [f"https://www.facebook.com/{username}"]
    elif platform == 'instagram':
        urls_to_try = [f"https://www.instagram.com/{username}/"]
    elif platform == 'tiktok':
        urls_to_try = [f"https://www.tiktok.com/@{username}"]
    elif platform == 'youtube':
        urls_to_try = [
            f"https://www.youtube.com/@{username}",
            f"https://www.youtube.com/c/{username}",
            f"https://www.youtube.com/user/{username}"
        ]
    else:
        return "❓ منصة غير مدعومة", ""
    
    for url in urls_to_try:
        try:
            with httpx.Client(timeout=20, follow_redirects=True) as client:
                response = client.get(url, headers=get_headers())
                
                # فحص سريع
                if response.status_code == 404:
                    continue
                
                # تحليل المحتوى باستخدام Mistral
                status = analyze_with_mistral(response.text, username, platform)
                
                # إذا النتيجة نشط، نرجع مباشرة
                if status == "✅ نشط":
                    return status, url
                    
                # إذا مش نشط ولسه في URLs تانية، نجرب
                if url != urls_to_try[-1]:
                    continue
                    
                return status, url
                
        except Exception as e:
            continue
    
    return "❌ معطل", urls_to_try[0]

# ==================== دالة الفحص الرئيسية ====================

def check_account(url):
    """فحص الحساب بناءً على المنصة"""
    platform = detect_platform(url)
    
    if not platform:
        return url, "❓ منصة غير مدعومة", url, "unknown"
    
    username = extract_username(url, platform)
    
    if not username:
        return url, "❓ رابط غير صحيح", url, platform
    
    status, final_url = check_account_with_ai(username, platform)
    
    return url, status, final_url, platform

# ==================== الواجهة ====================

platform_icons = {
    'twitter': '🐦',
    'facebook': '📘',
    'instagram': '📸',
    'tiktok': '🎵',
    'youtube': '📺',
    'unknown': '❓'
}

st.subheader("📝 أدخل الروابط (حتى 10 روابط)")

st.info("🤖 منطق بسيط: إذا Username ظاهر = نشط | مش ظاهر = معطل")

with st.expander("💡 أمثلة للاختبار"):
    st.code("""https://twitter.com/elonmusk
https://facebook.com/zuck
https://instagram.com/cristiano
https://tiktok.com/@khaby.lame
https://youtube.com/@MrBeast""")

urls_input = st.text_area(
    "ضع كل رابط في سطر منفصل:",
    height=250,
    placeholder="https://twitter.com/username\nhttps://facebook.com/pagename\nhttps://instagram.com/username"
)

col1, col2 = st.columns([1, 1])
with col1:
    check_button = st.button("🔍 فحص الكل", type="primary", use_container_width=True)
with col2:
    clear_button = st.button("🗑️ مسح", use_container_width=True)

if clear_button:
    st.rerun()

if check_button and urls_input.strip():
    urls = [url.strip() for url in urls_input.strip().split('\n') if url.strip()]
    
    if len(urls) > 10:
        st.warning("⚠️ الحد الأقصى 10 روابط.")
        urls = urls[:10]
    
    st.markdown("---")
    st.subheader(f"📊 النتائج ({len(urls)} حساب)")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    
    # فحص متسلسل
    for i, url in enumerate(urls):
        status_text.text(f"🤖 جارٍ التحليل... {i+1}/{len(urls)}")
        
        result = check_account(url)
        results.append(result)
        
        progress = (i + 1) / len(urls)
        progress_bar.progress(progress)
        
        if i < len(urls) - 1:
            time.sleep(1)
    
    progress_bar.empty()
    status_text.empty()
    
    # عرض النتائج
    for original_url, status, final_url, platform in results:
        icon = platform_icons.get(platform, '❓')
        
        col1, col2, col3 = st.columns([2, 3, 1])
        
        with col1:
            st.markdown(f"**{icon} {platform.upper()}**")
        
        with col2:
            if status.startswith("✅"):
                st.success(status)
            elif status.startswith("🚫"):
                st.error(status)
            elif status.startswith("❌"):
                st.error(status)
            else:
                st.info(status)
        
        with col3:
            st.markdown(f"[🔗 زيارة]({final_url})")
        
        st.markdown("---")
    
    # ملخص
    active = sum(1 for _, status, _, _ in results if "✅" in status)
    suspended = sum(1 for _, status, _, _ in results if "🚫" in status)
    disabled = sum(1 for _, status, _, _ in results if "❌" in status)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("✅ نشطة", active)
    with col2:
        st.metric("🚫 موقوفة", suspended)
    with col3:
        st.metric("❌ معطلة", disabled)
    with col4:
        st.metric("📊 المجموع", len(results))

elif check_button:
    st.warning("⚠️ يرجى إدخال روابط أولاً.")

st.markdown("---")
st.markdown("""
### 🎯 المنطق البسيط:

✅ **نشط** = Username ظاهر في الصفحة  
🚫 **موقوف** = الصفحة تقول suspended/banned  
❌ **معطل** = Username مش موجود في الصفحة  

### 📌 المنصات المدعومة:
🐦 **Twitter/X** | 📘 **Facebook** | 📸 **Instagram** | 🎵 **TikTok** | 📺 **YouTube**
""")

st.caption("🔧 Streamlit + httpx + Mistral AI | منطق بسيط ودقيق")
