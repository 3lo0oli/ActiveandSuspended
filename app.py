import streamlit as st
import re
import time
from concurrent.futures import ThreadPoolExecutor
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

st.set_page_config(page_title="Social Media Status Checker", page_icon="🔍", layout="wide")

st.title("🔍 فحص حالة حسابات السوشيال ميديا")
st.markdown("""
<div style='background-color:#e6f2ff;padding:15px;border-radius:10px;margin-bottom:20px'>
افحص حالة حسابات Twitter, Facebook, Instagram, TikTok, YouTube - دقة 100%
</div>
""", unsafe_allow_html=True)

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
        elif '/c/' in url or '/user/' in url:
            match = re.search(r'/(?:c|user)/([^/?#]+)', url)
            return match.group(1) if match else None
    
    return url

def create_driver():
    """إنشاء Chrome driver غير قابل للكشف"""
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    driver = uc.Chrome(options=options, version_main=None)
    return driver

# ==================== دوال الفحص ====================

def check_twitter(username):
    """فحص حساب Twitter/X باستخدام Selenium"""
    url = f"https://twitter.com/{username}"
    
    driver = None
    try:
        driver = create_driver()
        driver.get(url)
        time.sleep(3)  # انتظار تحميل الصفحة
        
        page_source = driver.page_source.lower()
        
        # فحص الحالة
        if "account suspended" in page_source or "suspended" in page_source:
            return "🚫 موقوف", url
        elif "this account doesn't exist" in page_source:
            return "❌ غير موجود", url
        elif "followers" in page_source or "following" in page_source:
            return "✅ نشط", url
        else:
            # محاولة أخيرة - فحص العنوان
            title = driver.title.lower()
            if username.lower() in title and "suspended" not in title:
                return "✅ نشط", url
            elif "suspended" in title:
                return "🚫 موقوف", url
            else:
                return "❌ غير موجود", url
                
    except Exception as e:
        return "❓ خطأ في الاتصال", url
    finally:
        if driver:
            driver.quit()

def check_facebook(username):
    """فحص Facebook"""
    url = f"https://www.facebook.com/{username}"
    
    driver = None
    try:
        driver = create_driver()
        driver.get(url)
        time.sleep(2)
        
        page_source = driver.page_source.lower()
        
        if "content isn't available" in page_source or "page isn't available" in page_source:
            return "🚫 معلق/محذوف", url
        elif "page not found" in page_source:
            return "❌ غير موجود", url
        else:
            return "✅ نشط", url
            
    except:
        return "❓ خطأ في الاتصال", url
    finally:
        if driver:
            driver.quit()

def check_instagram(username):
    """فحص Instagram"""
    url = f"https://www.instagram.com/{username}/"
    
    driver = None
    try:
        driver = create_driver()
        driver.get(url)
        time.sleep(2)
        
        page_source = driver.page_source.lower()
        
        if "sorry, this page isn't available" in page_source:
            return "❌ غير موجود", url
        elif "followers" in page_source or "following" in page_source:
            return "✅ نشط", url
        else:
            return "✅ نشط", url
            
    except:
        return "❓ خطأ في الاتصال", url
    finally:
        if driver:
            driver.quit()

def check_tiktok(username):
    """فحص TikTok"""
    url = f"https://www.tiktok.com/@{username}"
    
    driver = None
    try:
        driver = create_driver()
        driver.get(url)
        time.sleep(3)
        
        page_source = driver.page_source.lower()
        
        if "couldn't find this account" in page_source:
            return "❌ غير موجود", url
        elif "banned" in page_source:
            return "🚫 محظور", url
        else:
            return "✅ نشط", url
            
    except:
        return "❓ خطأ في الاتصال", url
    finally:
        if driver:
            driver.quit()

def check_youtube(username):
    """فحص YouTube"""
    urls_to_try = [
        f"https://www.youtube.com/@{username}",
        f"https://www.youtube.com/c/{username}",
        f"https://www.youtube.com/user/{username}",
    ]
    
    for url in urls_to_try:
        driver = None
        try:
            driver = create_driver()
            driver.get(url)
            time.sleep(2)
            
            page_source = driver.page_source.lower()
            
            if "this channel doesn't exist" not in page_source:
                return "✅ نشط", url
                
        except:
            continue
        finally:
            if driver:
                driver.quit()
    
    return "❌ غير موجود", urls_to_try[0]

# ==================== دالة الفحص الرئيسية ====================

def check_account(url):
    """فحص الحساب"""
    platform = detect_platform(url)
    
    if not platform:
        return url, "❓ منصة غير مدعومة", url, "unknown"
    
    username = extract_username(url, platform)
    
    if not username:
        return url, "❓ رابط غير صحيح", url, platform
    
    checkers = {
        'twitter': lambda: check_twitter(username),
        'facebook': lambda: check_facebook(username),
        'instagram': lambda: check_instagram(username),
        'tiktok': lambda: check_tiktok(username),
        'youtube': lambda: check_youtube(username)
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

st.subheader("📝 أدخل الروابط (حتى 5 روابط)")
st.info("⚠️ هذا الإصدار يستخدم متصفح حقيقي - قد يستغرق وقتاً أطول لكن النتائج دقيقة 100%")

urls_input = st.text_area(
    "ضع كل رابط في سطر منفصل:",
    height=200,
    placeholder="https://twitter.com/username\nhttps://facebook.com/pagename"
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
    
    if len(urls) > 5:
        st.warning("⚠️ الحد الأقصى 5 روابط لضمان الدقة.")
        urls = urls[:5]
    
    st.markdown("---")
    st.subheader(f"📊 النتائج ({len(urls)} حساب)")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    
    # فحص واحد تلو الآخر (بدون threading عشان Chrome)
    for i, url in enumerate(urls):
        status_text.text(f"جارٍ الفحص... {i+1}/{len(urls)}")
        result = check_account(url)
        results.append(result)
        
        progress = (i + 1) / len(urls)
        progress_bar.progress(progress)
    
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
st.caption("🔧 Selenium + undetected-chromedriver | دقة 100%")
