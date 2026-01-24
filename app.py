import streamlit as st
import httpx
from bs4 import BeautifulSoup
import re
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

st.set_page_config(page_title="Social Media Status Checker", page_icon="🔍", layout="wide")

st.title("🔍 فحص حالة حسابات السوشيال ميديا")
st.markdown("""
<div style='background-color:#e6f2ff;padding:15px;border-radius:10px;margin-bottom:20px'>
افحص حالة حسابات Twitter, Facebook, Instagram, TikTok, YouTube - نشطة أم معلقة
</div>
""", unsafe_allow_html=True)

# ==================== دوال التنظيف ====================

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

def clean_username(url, platform):
    """استخراج اسم المستخدم من الرابط"""
    url = url.strip()
    
    if platform == 'twitter':
        url = re.sub(r"(https?://)?(www\.)?(x|twitter)\.com/", "", url)
        url = re.sub(r"^@", "", url)
    elif platform == 'facebook':
        url = re.sub(r"(https?://)?(www\.)?facebook\.com/", "", url)
        url = re.sub(r"(https?://)?(www\.)?fb\.com/", "", url)
    elif platform == 'instagram':
        url = re.sub(r"(https?://)?(www\.)?instagram\.com/", "", url)
    elif platform == 'tiktok':
        url = re.sub(r"(https?://)?(www\.)?tiktok\.com/@?", "", url)
    elif platform == 'youtube':
        if '/channel/' in url:
            url = url.split('/channel/')[-1]
        elif '/c/' in url:
            url = url.split('/c/')[-1]
        elif '/@' in url:
            url = url.split('/@')[-1]
        else:
            url = re.sub(r"(https?://)?(www\.)?youtube\.com/", "", url)
    
    url = url.split("?")[0].split("/")[0]
    return url

# ==================== دوال الفحص ====================

def check_twitter(username):
    """فحص حساب Twitter"""
    url = f"https://twitter.com/{username}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            
            if response.status_code == 404:
                return "❌ غير موجود", url
            
            text = response.text.lower()
            
            if "account suspended" in text or "suspended" in text:
                return "🚫 موقوف", url
            elif "this account doesn't exist" in text:
                return "❌ غير موجود", url
            elif "followers" in text or "following" in text:
                return "✅ نشط", url
            
            return "⚠️ غير واضح", url
    except:
        return "❓ خطأ في الاتصال", url

def check_facebook(username):
    """فحص حساب Facebook"""
    url = f"https://www.facebook.com/{username}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            
            text = response.text.lower()
            
            if "this content isn't available" in text or "page not found" in text:
                return "❌ غير موجود", url
            elif "this page isn't available" in text:
                return "🚫 معلق أو محذوف", url
            elif response.status_code == 200:
                return "✅ نشط", url
            
            return "⚠️ غير واضح", url
    except:
        return "❓ خطأ في الاتصال", url

def check_instagram(username):
    """فحص حساب Instagram"""
    url = f"https://www.instagram.com/{username}/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            
            if response.status_code == 404:
                return "❌ غير موجود", url
            
            text = response.text.lower()
            
            if "sorry, this page isn't available" in text:
                return "❌ غير موجود", url
            elif "posts" in text or "followers" in text:
                return "✅ نشط", url
            
            return "⚠️ غير واضح", url
    except:
        return "❓ خطأ في الاتصال", url

def check_tiktok(username):
    """فحص حساب TikTok"""
    url = f"https://www.tiktok.com/@{username}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            
            if response.status_code == 404:
                return "❌ غير موجود", url
            
            text = response.text.lower()
            
            if "couldn't find this account" in text or "user not found" in text:
                return "❌ غير موجود", url
            elif "banned" in text or "account banned" in text:
                return "🚫 محظور", url
            elif response.status_code == 200:
                return "✅ نشط", url
            
            return "⚠️ غير واضح", url
    except:
        return "❓ خطأ في الاتصال", url

def check_youtube(username):
    """فحص قناة YouTube"""
    # جرب عدة صيغ للرابط
    urls = [
        f"https://www.youtube.com/@{username}",
        f"https://www.youtube.com/c/{username}",
        f"https://www.youtube.com/user/{username}"
    ]
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    for url in urls:
        try:
            with httpx.Client(timeout=15, follow_redirects=True) as client:
                response = client.get(url, headers=headers)
                
                if response.status_code == 404:
                    continue
                
                text = response.text.lower()
                
                if "this channel doesn't exist" in text or "404" in text:
                    continue
                elif "subscribers" in text or "videos" in text:
                    return "✅ نشط", url
                elif response.status_code == 200:
                    return "✅ نشط", url
        except:
            continue
    
    return "❌ غير موجود", urls[0]

def check_account(url):
    """فحص الحساب حسب المنصة"""
    platform = detect_platform(url)
    
    if not platform:
        return url, "❓ منصة غير مدعومة", url, "unknown"
    
    username = clean_username(url, platform)
    
    if not username:
        return url, "❓ رابط غير صحيح", url, platform
    
    # اختيار دالة الفحص المناسبة
    checkers = {
        'twitter': check_twitter,
        'facebook': check_facebook,
        'instagram': check_instagram,
        'tiktok': check_tiktok,
        'youtube': check_youtube
    }
    
    status, final_url = checkers[platform](username)
    
    return url, status, final_url, platform

# ==================== الواجهة ====================

# أيقونات المنصات
platform_icons = {
    'twitter': '🐦',
    'facebook': '📘',
    'instagram': '📸',
    'tiktok': '🎵',
    'youtube': '📺',
    'unknown': '❓'
}

# إدخال الروابط
st.subheader("📝 أدخل الروابط (حتى 10 روابط)")

urls_input = st.text_area(
    "ضع كل رابط في سطر منفصل:",
    height=200,
    placeholder="https://twitter.com/username\nhttps://facebook.com/pagename\nhttps://instagram.com/username\n..."
)

col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    check_button = st.button("🔍 فحص الكل", type="primary", use_container_width=True)
with col2:
    clear_button = st.button("🗑️ مسح", use_container_width=True)

if clear_button:
    st.rerun()

if check_button and urls_input.strip():
    urls = [url.strip() for url in urls_input.strip().split('\n') if url.strip()]
    
    if len(urls) > 10:
        st.warning("⚠️ الحد الأقصى 10 روابط. سيتم فحص أول 10 فقط.")
        urls = urls[:10]
    
    st.markdown("---")
    st.subheader(f"📊 النتائج ({len(urls)} حساب)")
    
    # شريط التقدم
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    
    # فحص متوازي للحسابات
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(check_account, url) for url in urls]
        
        for i, future in enumerate(futures):
            result = future.result()
            results.append(result)
            
            progress = (i + 1) / len(urls)
            progress_bar.progress(progress)
            status_text.text(f"جارٍ الفحص... {i+1}/{len(urls)}")
            
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
            elif status.startswith("🚫") or status.startswith("❌"):
                st.error(status)
            elif status.startswith("⚠️"):
                st.warning(status)
            else:
                st.info(status)
        
        with col3:
            st.markdown(f"[🔗 زيارة]({final_url})")
        
        st.markdown("---")
    
    # ملخص النتائج
    active = sum(1 for _, status, _, _ in results if "✅" in status)
    suspended = sum(1 for _, status, _, _ in results if "🚫" in status or "❌" in status)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("✅ نشطة", active)
    with col2:
        st.metric("🚫 معلقة/محذوفة", suspended)
    with col3:
        st.metric("📊 المجموع", len(results))

elif check_button:
    st.warning("⚠️ يرجى إدخال روابط أولاً.")

# معلومات إضافية
st.markdown("---")
st.markdown("""
### 📌 المنصات المدعومة:
- 🐦 **Twitter/X** - تحقق من حالة الحساب
- 📘 **Facebook** - فحص الصفحات والحسابات
- 📸 **Instagram** - التحقق من البروفايلات
- 🎵 **TikTok** - فحص حسابات المستخدمين
- 📺 **YouTube** - التحقق من القنوات

### 💡 نصائح:
- يمكنك فحص حتى 10 حسابات دفعة واحدة
- ضع كل رابط في سطر منفصل
- يعمل مع الروابط الكاملة أو أسماء المستخدمين
""")

st.caption("🔧 تم التطوير باستخدام Streamlit | مدعوم بـ httpx & BeautifulSoup")
