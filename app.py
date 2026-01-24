import streamlit as st
import httpx
import re
import time
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="Social Media Status Checker", page_icon="🔍", layout="wide")

st.title("🔍 فحص حالة حسابات السوشيال ميديا")
st.markdown("""
<div style='background-color:#e6f2ff;padding:15px;border-radius:10px;margin-bottom:20px'>
افحص حالة حسابات Twitter, Facebook, Instagram, TikTok, YouTube
</div>
""", unsafe_allow_html=True)

# ==================== User Agents ====================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
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
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none"
    }

# ==================== دوال الفحص ====================

def check_twitter(username):
    """فحص حساب Twitter/X"""
    urls_to_try = [
        f"https://twitter.com/{username}",
        f"https://x.com/{username}"
    ]
    
    for url in urls_to_try:
        try:
            with httpx.Client(timeout=20, follow_redirects=True) as client:
                response = client.get(url, headers=get_headers())
                
                if response.status_code == 404:
                    continue
                
                content = response.text.lower()
                
                # موقوف
                if "account suspended" in content or '"suspended":true' in content:
                    return "🚫 موقوف", url
                
                # غير موجود
                if "this account doesn't exist" in content or "page does not exist" in content:
                    continue
                
                # نشط - البحث عن علامات JSON
                if any(x in content for x in [
                    '"screen_name"',
                    '"followers_count"', 
                    '"following_count"',
                    'data-testid="primarycolumn"',
                    'followers',
                    'following'
                ]):
                    return "✅ نشط", url
                
                # فحص بناءً على حجم الصفحة
                if response.status_code == 200 and len(content) > 30000:
                    # صفحة كبيرة عادةً تعني بروفايل موجود
                    if 'twitter' in content or 'profile' in content:
                        return "✅ نشط", url
                        
        except Exception as e:
            continue
    
    return "❌ غير موجود", urls_to_try[0]

def check_facebook(username):
    """فحص صفحة/حساب Facebook"""
    url = f"https://www.facebook.com/{username}"
    
    try:
        with httpx.Client(timeout=20, follow_redirects=True) as client:
            response = client.get(url, headers=get_headers())
            
            content = response.text.lower()
            
            # محذوف/معلق
            if any(x in content for x in [
                "content isn't available",
                "page isn't available",
                "content not found",
                "page not found"
            ]):
                if response.status_code == 404:
                    return "❌ غير موجود", url
                return "🚫 معلق/محذوف", url
            
            # نشط
            if response.status_code == 200:
                if any(x in content for x in [
                    "timeline", "photos", "about", 
                    "log in", "sign up", "create new account"
                ]):
                    return "✅ نشط", url
            
            # إذا الصفحة كبيرة = غالباً نشطة
            if len(content) > 10000:
                return "✅ نشط", url
            
            return "⚠️ غير واضح", url
            
    except Exception as e:
        return "❓ خطأ في الاتصال", url

def check_instagram(username):
    """فحص حساب Instagram"""
    url = f"https://www.instagram.com/{username}/"
    
    try:
        with httpx.Client(timeout=20, follow_redirects=True) as client:
            response = client.get(url, headers=get_headers())
            
            content = response.text.lower()
            
            # غير موجود
            if response.status_code == 404:
                return "❌ غير موجود", url
            
            if "sorry, this page isn't available" in content:
                return "❌ غير موجود", url
            
            # نشط - البحث عن JSON data
            if any(x in content for x in [
                '"is_private"',
                '"edge_followed_by"',
                '"edge_follow"',
                '"profile_pic_url"',
                'followers',
                'following',
                'posts'
            ]):
                return "✅ نشط", url
            
            # فحص og:description
            if 'og:description' in content:
                return "✅ نشط", url
            
            # صفحة كبيرة = حساب موجود
            if response.status_code == 200 and len(content) > 15000:
                return "✅ نشط", url
            
            return "⚠️ غير واضح", url
            
    except Exception as e:
        return "❓ خطأ في الاتصال", url

def check_tiktok(username):
    """فحص حساب TikTok"""
    url = f"https://www.tiktok.com/@{username}"
    
    try:
        with httpx.Client(timeout=20, follow_redirects=True) as client:
            response = client.get(url, headers=get_headers())
            
            content = response.text.lower()
            
            # غير موجود
            if response.status_code == 404:
                return "❌ غير موجود", url
            
            if any(x in content for x in [
                "couldn't find this account",
                "user not found",
                "page not available"
            ]):
                return "❌ غير موجود", url
            
            # محظور
            if "banned" in content or "account banned" in content:
                return "🚫 محظور", url
            
            # نشط
            if any(x in content for x in [
                '"followercount"',
                '"videocount"',
                '"uniqueid"',
                'followers',
                'following',
                'likes'
            ]):
                return "✅ نشط", url
            
            if response.status_code == 200 and len(content) > 10000:
                return "✅ نشط", url
            
            return "⚠️ غير واضح", url
            
    except Exception as e:
        return "❓ خطأ في الاتصال", url

def check_youtube(username):
    """فحص قناة YouTube"""
    urls_to_try = [
        f"https://www.youtube.com/@{username}",
        f"https://www.youtube.com/c/{username}",
        f"https://www.youtube.com/user/{username}",
    ]
    
    for url in urls_to_try:
        try:
            with httpx.Client(timeout=20, follow_redirects=True) as client:
                response = client.get(url, headers=get_headers())
                
                if response.status_code == 404:
                    continue
                
                content = response.text.lower()
                
                if "this channel doesn't exist" in content:
                    continue
                
                # نشط
                if any(x in content for x in [
                    '"subscribercount"',
                    '"videoscount"',
                    '"channelid"',
                    'subscribers',
                    'videos'
                ]):
                    return "✅ نشط", url
                
                if response.status_code == 200 and len(content) > 50000:
                    return "✅ نشط", url
                        
        except Exception as e:
            continue
    
    return "❌ غير موجود", urls_to_try[0]

# ==================== دالة الفحص الرئيسية ====================

def check_account(url):
    """فحص الحساب بناءً على المنصة"""
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

st.subheader("📝 أدخل الروابط (حتى 10 روابط)")

with st.expander("💡 أمثلة للاختبار"):
    st.code("""https://twitter.com/elonmusk
https://facebook.com/zuck
https://instagram.com/cristiano
https://tiktok.com/@khaby.lame
https://youtube.com/@MrBeast""")

urls_input = st.text_area(
    "ضع كل رابط في سطر منفصل:",
    height=250,
    placeholder="https://twitter.com/username\nhttps://facebook.com/pagename\nhttps://instagram.com/username\nhttps://tiktok.com/@username\nhttps://youtube.com/@channelname"
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
        futures = [executor.submit(check_account, url) for url in urls]
        
        for i, future in enumerate(futures):
            result = future.result()
            results.append(result)
            
            progress = (i + 1) / len(urls)
            progress_bar.progress(progress)
            status_text.text(f"جارٍ الفحص... {i+1}/{len(urls)}")
            
            if i < len(futures) - 1:
                time.sleep(0.5)
    
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
    unclear = sum(1 for _, status, _, _ in results if "⚠️" in status or "❓" in status)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("✅ نشطة", active)
    with col2:
        st.metric("🚫 معلقة/محذوفة", suspended)
    with col3:
        st.metric("⚠️ غير واضح", unclear)
    with col4:
        st.metric("📊 المجموع", len(results))

elif check_button:
    st.warning("⚠️ يرجى إدخال روابط أولاً.")

st.markdown("---")
st.markdown("""
### 💡 نصائح:

✅ استخدم الروابط الكاملة للحسابات  
✅ النتائج "غير واضح" = يحتاج تسجيل دخول للتأكد  
✅ لا تفحص بسرعة كبيرة (قد تُحظر مؤقتاً)  

### 📌 المنصات المدعومة:
🐦 **Twitter/X** | 📘 **Facebook** | 📸 **Instagram** | 🎵 **TikTok** | 📺 **YouTube**
""")

st.caption("🔧 تم التطوير باستخدام Streamlit + httpx")
