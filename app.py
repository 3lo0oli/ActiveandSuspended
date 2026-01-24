import streamlit as st
import httpx
import time
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="Social Media Status Checker", page_icon="🔍", layout="wide")

st.title("🔍 فحص حالة حسابات السوشيال ميديا")
st.markdown("""
<div style='background-color:#e6f2ff;padding:15px;border-radius:10px;margin-bottom:20px'>
افحص حالة حسابات Twitter, Facebook, Instagram, TikTok, YouTube - دقة عالية
</div>
""", unsafe_allow_html=True)

# ==================== إعدادات RapidAPI ====================
RAPIDAPI_KEY = st.sidebar.text_input("🔑 RapidAPI Key", type="password", help="احصل على المفتاح من https://rapidapi.com")

# ==================== دوال الكشف ====================

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
    """استخراج اسم المستخدم"""
    import re
    url = url.strip()
    
    if platform == 'twitter':
        match = re.search(r'(?:twitter\.com|x\.com)/([^/?]+)', url)
        return match.group(1) if match else url.replace('@', '')
    elif platform == 'facebook':
        match = re.search(r'facebook\.com/([^/?]+)', url)
        return match.group(1) if match else url
    elif platform == 'instagram':
        match = re.search(r'instagram\.com/([^/?]+)', url)
        return match.group(1) if match else url
    elif platform == 'tiktok':
        match = re.search(r'tiktok\.com/@?([^/?]+)', url)
        return match.group(1) if match else url.replace('@', '')
    elif platform == 'youtube':
        if '/channel/' in url:
            return url.split('/channel/')[-1].split('/')[0]
        elif '/@' in url:
            return url.split('/@')[-1].split('/')[0]
        elif '/c/' in url:
            return url.split('/c/')[-1].split('/')[0]
        else:
            match = re.search(r'youtube\.com/([^/?]+)', url)
            return match.group(1) if match else url
    
    return url

# ==================== دوال الفحص بـ RapidAPI ====================

def check_twitter_api(username, api_key):
    """فحص Twitter باستخدام RapidAPI"""
    if not api_key:
        return check_twitter_scrape(username)
    
    url = "https://twitter-api45.p.rapidapi.com/screenname.php"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "twitter-api45.p.rapidapi.com"
    }
    params = {"screenname": username}
    
    try:
        response = httpx.get(url, headers=headers, params=params, timeout=15)
        data = response.json()
        
        if 'error' in data:
            return "❌ غير موجود", f"https://twitter.com/{username}"
        elif data.get('suspended') == True:
            return "🚫 موقوف", f"https://twitter.com/{username}"
        elif data.get('screen_name'):
            return "✅ نشط", f"https://twitter.com/{username}"
        else:
            return "⚠️ غير واضح", f"https://twitter.com/{username}"
    except:
        return check_twitter_scrape(username)

def check_instagram_api(username, api_key):
    """فحص Instagram باستخدام RapidAPI"""
    if not api_key:
        return check_instagram_scrape(username)
    
    url = "https://instagram-scraper-api2.p.rapidapi.com/v1/info"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "instagram-scraper-api2.p.rapidapi.com"
    }
    params = {"username_or_id_or_url": username}
    
    try:
        response = httpx.get(url, headers=headers, params=params, timeout=15)
        data = response.json()
        
        if data.get('status') == 'ok' and data.get('data'):
            user_data = data['data']
            if user_data.get('is_private') is not None:
                return "✅ نشط", f"https://instagram.com/{username}"
            else:
                return "❌ غير موجود", f"https://instagram.com/{username}"
        else:
            return "❌ غير موجود", f"https://instagram.com/{username}"
    except:
        return check_instagram_scrape(username)

def check_tiktok_api(username, api_key):
    """فحص TikTok باستخدام RapidAPI"""
    if not api_key:
        return check_tiktok_scrape(username)
    
    url = "https://tiktok-scraper7.p.rapidapi.com/user/info"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "tiktok-scraper7.p.rapidapi.com"
    }
    params = {"unique_id": username}
    
    try:
        response = httpx.get(url, headers=headers, params=params, timeout=15)
        data = response.json()
        
        if data.get('data') and data['data'].get('user'):
            return "✅ نشط", f"https://tiktok.com/@{username}"
        else:
            return "❌ غير موجود", f"https://tiktok.com/@{username}"
    except:
        return check_tiktok_scrape(username)

def check_youtube_api(username, api_key):
    """فحص YouTube باستخدام RapidAPI"""
    if not api_key:
        return check_youtube_scrape(username)
    
    # يمكن استخدام YouTube Data API v3
    return check_youtube_scrape(username)

# ==================== دوال Scraping المحسنة (Fallback) ====================

def check_twitter_scrape(username):
    """فحص Twitter عن طريق Scraping محسّن"""
    urls_to_try = [
        f"https://x.com/{username}",
        f"https://twitter.com/{username}",
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    }
    
    for url in urls_to_try:
        try:
            with httpx.Client(timeout=20, follow_redirects=True) as client:
                response = client.get(url, headers=headers)
                
                # تحقق من كود الاستجابة
                if response.status_code == 404:
                    continue
                
                # تحقق من عنوان الصفحة
                if "suspended" in response.text.lower():
                    return "🚫 موقوف", url
                elif "doesn't exist" in response.text.lower() or "not found" in response.text.lower():
                    continue
                elif response.status_code == 200:
                    # تحقق من وجود محتوى الحساب
                    if '"followers_count"' in response.text or '"following_count"' in response.text:
                        return "✅ نشط", url
                    elif len(response.text) > 50000:  # صفحة بروفايل عادية
                        return "✅ نشط", url
                    
        except Exception as e:
            continue
    
    return "❌ غير موجود", urls_to_try[0]

def check_facebook_scrape(username):
    """فحص Facebook محسّن"""
    url = f"https://www.facebook.com/{username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    try:
        with httpx.Client(timeout=20, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            
            if response.status_code == 404:
                return "❌ غير موجود", url
            
            text = response.text.lower()
            
            # علامات الحساب المحذوف/المعلق
            if "content isn't available" in text or "page isn't available" in text:
                return "🚫 معلق أو محذوف", url
            elif "you must log in" in text or response.status_code == 200:
                return "✅ نشط", url
            
            return "⚠️ غير واضح", url
    except:
        return "❓ خطأ في الاتصال", url

def check_instagram_scrape(username):
    """فحص Instagram محسّن"""
    url = f"https://www.instagram.com/{username}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    try:
        with httpx.Client(timeout=20, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            
            if response.status_code == 404:
                return "❌ غير موجود", url
            
            text = response.text.lower()
            
            if "page not found" in text or "sorry, this page" in text:
                return "❌ غير موجود", url
            elif '"is_private"' in text or '"edge_followed_by"' in text:
                return "✅ نشط", url
            elif response.status_code == 200 and len(response.text) > 10000:
                return "✅ نشط", url
            
            return "⚠️ غير واضح", url
    except:
        return "❓ خطأ في الاتصال", url

def check_tiktok_scrape(username):
    """فحص TikTok محسّن"""
    url = f"https://www.tiktok.com/@{username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        with httpx.Client(timeout=20, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            
            if response.status_code == 404:
                return "❌ غير موجود", url
            
            text = response.text.lower()
            
            if "couldn't find" in text or "user not found" in text:
                return "❌ غير موجود", url
            elif '"followerCount"' in text or '"videoCount"' in text:
                return "✅ نشط", url
            elif response.status_code == 200:
                return "✅ نشط", url
            
            return "⚠️ غير واضح", url
    except:
        return "❓ خطأ في الاتصال", url

def check_youtube_scrape(username):
    """فحص YouTube محسّن"""
    urls = [
        f"https://www.youtube.com/@{username}",
        f"https://www.youtube.com/c/{username}",
        f"https://www.youtube.com/user/{username}"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    for url in urls:
        try:
            with httpx.Client(timeout=20, follow_redirects=True) as client:
                response = client.get(url, headers=headers)
                
                if response.status_code == 404:
                    continue
                
                text = response.text.lower()
                
                if '"subscribercount"' in text or '"videoscount"' in text:
                    return "✅ نشط", url
                elif response.status_code == 200 and len(response.text) > 50000:
                    return "✅ نشط", url
        except:
            continue
    
    return "❌ غير موجود", urls[0]

# ==================== دالة الفحص الرئيسية ====================

def check_account(url, api_key):
    """فحص الحساب بناءً على المنصة"""
    platform = detect_platform(url)
    
    if not platform:
        return url, "❓ منصة غير مدعومة", url, "unknown"
    
    username = extract_username(url, platform)
    
    if not username:
        return url, "❓ رابط غير صحيح", url, platform
    
    # اختيار طريقة الفحص (API أو Scraping)
    if api_key and platform in ['twitter', 'instagram', 'tiktok']:
        checkers = {
            'twitter': lambda: check_twitter_api(username, api_key),
            'facebook': lambda: check_facebook_scrape(username),
            'instagram': lambda: check_instagram_api(username, api_key),
            'tiktok': lambda: check_tiktok_api(username, api_key),
            'youtube': lambda: check_youtube_api(username, api_key)
        }
    else:
        checkers = {
            'twitter': lambda: check_twitter_scrape(username),
            'facebook': lambda: check_facebook_scrape(username),
            'instagram': lambda: check_instagram_scrape(username),
            'tiktok': lambda: check_tiktok_scrape(username),
            'youtube': lambda: check_youtube_scrape(username)
        }
    
    status, final_url = checkers[platform]()
    
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

# معلومات في الـ Sidebar
with st.sidebar:
    st.markdown("### ℹ️ معلومات")
    if RAPIDAPI_KEY:
        st.success("✅ API مفعّل - دقة عالية")
    else:
        st.warning("⚠️ بدون API - دقة متوسطة")
    
    st.markdown("""
    **للحصول على دقة أعلى:**
    1. سجل في [RapidAPI](https://rapidapi.com)
    2. اشترك في APIs التالية:
       - Twitter API45
       - Instagram Scraper
       - TikTok Scraper
    3. ضع API Key هنا ☝️
    """)

st.subheader("📝 أدخل الروابط (حتى 10 روابط)")

urls_input = st.text_area(
    "ضع كل رابط في سطر منفصل:",
    height=200,
    placeholder="https://twitter.com/username\nhttps://facebook.com/pagename\nhttps://instagram.com/username\n..."
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
        st.warning("⚠️ الحد الأقصى 10 روابط. سيتم فحص أول 10 فقط.")
        urls = urls[:10]
    
    st.markdown("---")
    st.subheader(f"📊 النتائج ({len(urls)} حساب)")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(check_account, url, RAPIDAPI_KEY) for url in urls]
        
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
    
    # ملخص
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

st.markdown("---")
st.caption("🔧 تم التطوير باستخدام Streamlit | مدعوم بـ RapidAPI & Web Scraping")
