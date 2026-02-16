import streamlit as st
import httpx
import re
import time
import random

st.set_page_config(page_title="Social Media Status Checker", page_icon="🔍", layout="wide")

# ==================== CSS ====================
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px 30px;
        border-radius: 15px;
        margin-bottom: 25px;
        color: white;
        text-align: center;
    }
    .main-header h1 { color: white; margin: 0; font-size: 2em; }
    .main-header p { color: #e8e8e8; margin: 5px 0 0 0; }
    .result-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 15px 20px;
        margin: 8px 0;
        border-left: 5px solid #ddd;
    }
    .result-active { border-left-color: #28a745; background: #f0fff4; }
    .result-suspended { border-left-color: #dc3545; background: #fff5f5; }
    .result-disabled { border-left-color: #6c757d; background: #f5f5f5; }
    .result-error { border-left-color: #ffc107; background: #fffdf0; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>🔍 Social Media Account Checker</h1>
    <p>فحص حالة حسابات Twitter · Facebook · Instagram · TikTok · YouTube — مجاني 100%</p>
</div>
""", unsafe_allow_html=True)

# ==================== User Agents ====================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

# ==================== Helper Functions ====================

def detect_platform(url: str) -> str | None:
    url_lower = url.lower()
    if "twitter.com" in url_lower or "x.com" in url_lower:
        return "twitter"
    if "facebook.com" in url_lower or "fb.com" in url_lower:
        return "facebook"
    if "instagram.com" in url_lower:
        return "instagram"
    if "tiktok.com" in url_lower:
        return "tiktok"
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "youtube"
    return None


def extract_username(url: str, platform: str) -> str | None:
    url = url.strip().rstrip("/")
    patterns = {
        "twitter":   r"(?:twitter\.com|x\.com)/([A-Za-z0-9_]+)",
        "facebook":  r"facebook\.com/(?:profile\.php\?id=)?([A-Za-z0-9_.]+)",
        "instagram": r"instagram\.com/([A-Za-z0-9_.]+)",
        "tiktok":    r"tiktok\.com/@?([A-Za-z0-9_.]+)",
    }
    if platform == "youtube":
        for pat in [r"/@([^/?#]+)", r"/c/([^/?#]+)", r"/user/([^/?#]+)", r"/channel/([^/?#]+)"]:
            m = re.search(pat, url)
            if m:
                return m.group(1)
        return None

    pat = patterns.get(platform)
    if pat:
        m = re.search(pat, url)
        return m.group(1) if m else None
    return None


def get_browser_headers() -> dict:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }


def get_mobile_headers() -> dict:
    return {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }


def make_request(url: str, headers: dict = None, timeout: int = 25) -> httpx.Response | None:
    if headers is None:
        headers = get_browser_headers()

    # Try 1: HTTP/2
    for attempt in range(2):
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True, http2=True, verify=True) as client:
                return client.get(url, headers=headers)
        except Exception:
            if attempt == 0:
                time.sleep(0.5)

    # Try 2: HTTP/1.1 mobile
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True, http2=False, verify=True) as client:
            return client.get(url, headers=get_mobile_headers())
    except Exception:
        pass

    # Try 3: Skip SSL (last resort)
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True, http2=False, verify=False) as client:
            return client.get(url, headers=get_mobile_headers())
    except Exception:
        pass

    return None


# ==================== Platform Checkers ====================

def check_twitter(username: str) -> tuple[str, str, str]:
    url = f"https://x.com/{username}"
    resp = make_request(url)
    if resp is None:
        return "⚠️ تعذر الاتصال", url, "لم نتمكن من الوصول — جرب تاني"

    text = resp.text.lower()
    code = resp.status_code

    if any(s in text for s in ["account is suspended", "account has been suspended", "this account is suspended"]):
        return "🚫 موقوف (Suspended)", url, "الحساب معلّق من تويتر"

    if code == 404 or any(s in text for s in [
        "this account doesn't exist", "this account doesn\u2019t exist",
        "hmm...this page doesn", "page doesn't exist",
    ]):
        return "❌ غير موجود", url, "الحساب مش موجود أو اتحذف"

    if code == 200:
        if any(s in text for s in [f"@{username.lower()}", f"/{username.lower()}", f'"{username.lower()}"']):
            return "✅ نشط (Active)", url, "الحساب شغال"
        return "✅ نشط — غالباً", url, "الصفحة موجودة (محتاجة متصفح للتأكيد)"

    return "❓ غير محدد", url, f"Status: {code}"


def check_facebook(username: str) -> tuple[str, str, str]:
    is_numeric = username.isdigit()
    page_url = f"https://www.facebook.com/profile.php?id={username}" if is_numeric else f"https://www.facebook.com/{username}"

    # ===== Strategy 1: Graph API — profile picture endpoint (free, no key) =====
    graph_url = f"https://graph.facebook.com/{username}/picture?redirect=false"
    try:
        resp = make_request(graph_url, timeout=15)
        if resp is not None:
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    pic_url = data.get("data", {}).get("url", "")
                    if pic_url:
                        return "✅ نشط (Active)", page_url, "الحساب موجود وشغال (Graph API)"
                except Exception:
                    pass

            # Check for "profile doesn't exist" error
            try:
                err_data = resp.json()
                err_msg = err_data.get("error", {}).get("message", "").lower()
                if "does not exist" in err_msg:
                    return "❌ غير موجود", page_url, "الحساب غير موجود"
            except Exception:
                pass
    except Exception:
        pass

    # ===== Strategy 2: Mobile Facebook =====
    m_url = f"https://m.facebook.com/profile.php?id={username}" if is_numeric else f"https://m.facebook.com/{username}"
    resp = make_request(m_url, headers=get_mobile_headers())
    if resp is not None:
        text = resp.text.lower()
        code = resp.status_code

        not_found = [
            "this content isn't available", "this content isn\u2019t available",
            "this page isn't available", "this page isn\u2019t available",
            "the link you followed may be broken", "page not found",
            "the page you requested was not found",
        ]
        if code == 404 or any(s in text for s in not_found):
            return "❌ غير موجود", page_url, "الصفحة مش موجودة أو اتحذفت"

        if any(s in text for s in ["account has been disabled", "violated our community standards"]):
            return "🚫 معطل (Disabled)", page_url, "الحساب اتعطّل لمخالفة القوانين"

        if code == 200:
            profile_signals = [
                'property="og:title"', "profile_header", "timeline",
                "cover_photo", "profile_photo",
            ]
            if not is_numeric:
                profile_signals.append(f"/{username.lower()}")
            else:
                profile_signals.append(f"id={username}")

            if any(s in text for s in profile_signals):
                return "✅ نشط (Active)", page_url, "الحساب شغال وموجود"
            return "✅ نشط — غالباً", page_url, "الصفحة موجودة (تحتاج متصفح للتأكيد 100%)"

        if code in (301, 302):
            return "✅ نشط — غالباً", page_url, "الحساب موجود (يحتاج تسجيل دخول)"

    # ===== Strategy 3: Desktop =====
    resp = make_request(page_url)
    if resp is not None:
        text = resp.text.lower()
        if resp.status_code == 404 or any(s in text for s in [
            "this content isn't available", "this page isn't available",
            "the link you followed may be broken",
        ]):
            return "❌ غير موجود", page_url, "الصفحة مش موجودة"
        if resp.status_code == 200:
            return "✅ نشط — غالباً", page_url, "الصفحة استجابت — الحساب موجود غالباً"

    return "⚠️ تعذر الاتصال", page_url, "لم نتمكن من الوصول — جرب مرة تانية"


def check_instagram(username: str) -> tuple[str, str, str]:
    url = f"https://www.instagram.com/{username}/"

    resp = make_request(url)
    if resp is not None:
        text = resp.text.lower()
        code = resp.status_code

        if code == 404 or any(s in text for s in [
            "sorry, this page isn't available", "sorry, this page isn\u2019t available",
            "the link you followed may be broken",
        ]):
            return "❌ غير موجود", url, "الحساب مش موجود أو اتحذف"

        if any(s in text for s in ["account has been suspended", "account suspended"]):
            return "🚫 موقوف (Suspended)", url, "الحساب معلّق"

        if code == 200:
            if any(s in text for s in [
                f'"{username.lower()}"', f"@{username.lower()}",
                f"instagram.com/{username.lower()}", 'property="og:title"',
                '"profilepage"', "profile_pic_url",
            ]):
                return "✅ نشط (Active)", url, "الحساب شغال وموجود"
            return "✅ نشط — غالباً", url, "الصفحة موجودة (قد تحتاج تسجيل دخول)"

        if code in (301, 302):
            return "✅ نشط — غالباً", url, "الحساب موجود (يحتاج تسجيل دخول)"

    # Mobile fallback
    resp = make_request(url, headers=get_mobile_headers())
    if resp is not None:
        if resp.status_code == 404 or "page isn't available" in resp.text.lower():
            return "❌ غير موجود", url, "الحساب غير موجود"
        if resp.status_code == 200:
            return "✅ نشط — غالباً", url, "الحساب موجود"

    return "⚠️ تعذر الاتصال", url, "لم نتمكن من الوصول — جرب تاني"


def check_tiktok(username: str) -> tuple[str, str, str]:
    clean = username.lstrip("@")
    url = f"https://www.tiktok.com/@{clean}"

    # Strategy 1: oEmbed API (free, reliable)
    oembed_url = f"https://www.tiktok.com/oembed?url={url}"
    try:
        resp = make_request(oembed_url, timeout=15)
        if resp is not None and resp.status_code == 200:
            try:
                data = resp.json()
                author = data.get("author_name", clean)
                return "✅ نشط (Active)", url, f"الحساب شغال — الاسم: {author}"
            except Exception:
                pass
    except Exception:
        pass

    # Strategy 2: Direct page
    resp = make_request(url)
    if resp is not None:
        text = resp.text.lower()
        code = resp.status_code

        if any(s in text for s in ["this account was banned", "account banned", "permanently banned"]):
            return "🚫 محظور (Banned)", url, "الحساب محظور من تيك توك"

        if code == 404 or any(s in text for s in [
            "couldn't find this account", "couldn\u2019t find this account",
            '"statuscode":10202', '"statuscode": 10202',
        ]):
            return "❌ غير موجود", url, "الحساب مش موجود"

        if code == 200:
            if any(s in text for s in [
                f"@{clean.lower()}", f'"uniqueid":"{clean.lower()}"',
                'property="og:title"',
            ]):
                return "✅ نشط (Active)", url, "الحساب شغال"
            return "✅ نشط — غالباً", url, "الصفحة موجودة"

    return "⚠️ تعذر الاتصال", url, "لم نتمكن من الوصول"


def check_youtube(username: str) -> tuple[str, str, str]:
    url_formats = [
        f"https://www.youtube.com/@{username}",
        f"https://www.youtube.com/c/{username}",
        f"https://www.youtube.com/user/{username}",
    ]
    if username.startswith("UC") and len(username) == 24:
        url_formats = [f"https://www.youtube.com/channel/{username}"]

    for page_url in url_formats:
        oembed_url = f"https://www.youtube.com/oembed?url={page_url}&format=json"
        resp = make_request(oembed_url, timeout=15)
        if resp is not None and resp.status_code == 200:
            try:
                data = resp.json()
                title = data.get("author_name", username)
                return "✅ نشط (Active)", page_url, f"القناة شغالة — اسمها: {title}"
            except Exception:
                return "✅ نشط (Active)", page_url, "القناة موجودة"

    direct_url = url_formats[0]
    resp = make_request(direct_url)
    if resp is not None:
        text = resp.text.lower()
        if "this account has been terminated" in text:
            return "🚫 محذوف (Terminated)", direct_url, "القناة اتحذفت"
        if "has been suspended" in text:
            return "🚫 موقوف (Suspended)", direct_url, "القناة معلّقة"
        if resp.status_code == 404:
            return "❌ غير موجود", direct_url, "القناة مش موجودة"
        if resp.status_code == 200:
            return "✅ نشط — غالباً", direct_url, "القناة موجودة"

    return "⚠️ تعذر الاتصال", direct_url, "لم نتمكن من التحقق"


# ==================== Main ====================

CHECKERS = {
    "twitter": check_twitter, "facebook": check_facebook,
    "instagram": check_instagram, "tiktok": check_tiktok, "youtube": check_youtube,
}
PLATFORM_ICONS = {
    "twitter": "🐦", "facebook": "📘", "instagram": "📸",
    "tiktok": "🎵", "youtube": "📺", "unknown": "❓",
}
PLATFORM_NAMES = {
    "twitter": "Twitter / X", "facebook": "Facebook", "instagram": "Instagram",
    "tiktok": "TikTok", "youtube": "YouTube",
}


def check_account(url: str) -> dict:
    platform = detect_platform(url)
    if not platform:
        return {"url": url, "platform": "unknown", "status": "❓ منصة غير مدعومة",
                "link": url, "details": "تأكد من الرابط", "username": "—"}
    username = extract_username(url, platform)
    if not username:
        return {"url": url, "platform": platform, "status": "❓ رابط غير صحيح",
                "link": url, "details": "لم نتمكن من استخراج اسم المستخدم", "username": "—"}
    status, link, details = CHECKERS[platform](username)
    return {"url": url, "platform": platform, "username": username,
            "status": status, "link": link, "details": details}


# ==================== UI ====================

st.subheader("📝 أدخل الروابط (حتى 10 روابط)")
st.info("💡 **مجاني 100%** — Graph API + oEmbed + HTTP Pattern Matching — بدون أي مفتاح مدفوع")

with st.expander("📌 أمثلة للاختبار"):
    st.code("""https://twitter.com/elonmusk
https://www.facebook.com/zuck
https://www.facebook.com/profile.php?id=61556090150113
https://instagram.com/cristiano
https://tiktok.com/@khaby.lame
https://youtube.com/@MrBeast""")

urls_input = st.text_area(
    "ضع كل رابط في سطر منفصل:", height=220,
    placeholder="https://www.facebook.com/username\nhttps://instagram.com/username",
)

col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    check_button = st.button("🔍 فحص الكل", type="primary", use_container_width=True)
with col_btn2:
    clear_button = st.button("🗑️ مسح", use_container_width=True)

if clear_button:
    st.rerun()

if check_button and urls_input.strip():
    urls = [u.strip() for u in urls_input.strip().splitlines() if u.strip()]
    if len(urls) > 10:
        st.warning("⚠️ الحد الأقصى 10 — هيتم فحص أول 10 فقط.")
        urls = urls[:10]

    st.markdown("---")
    st.subheader(f"📊 النتائج ({len(urls)} حساب)")

    progress = st.progress(0)
    status_ph = st.empty()
    results = []

    for i, url in enumerate(urls):
        pname = PLATFORM_NAMES.get(detect_platform(url) or "", url)
        status_ph.text(f"⏳ جارٍ فحص {pname} ... ({i+1}/{len(urls)})")
        results.append(check_account(url))
        progress.progress((i + 1) / len(urls))
        if i < len(urls) - 1:
            time.sleep(2)

    progress.empty()
    status_ph.empty()

    for r in results:
        icon = PLATFORM_ICONS.get(r["platform"], "❓")
        status = r["status"]
        css = "result-active" if "✅" in status else "result-suspended" if "🚫" in status else "result-disabled" if "❌" in status else "result-error"

        st.markdown(f"""
        <div class="result-card {css}">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                <div>
                    <strong style="font-size:1.1em;">{icon} {PLATFORM_NAMES.get(r['platform'], r['platform'].upper())}</strong>
                    &nbsp;·&nbsp; <code style="background:#e9ecef; padding:2px 8px; border-radius:4px;">@{r.get('username','—')}</code>
                </div>
                <div style="font-size:1.15em; font-weight:bold;">{status}</div>
            </div>
            <div style="color:#666; font-size:0.88em; margin-top:8px;">
                📝 {r['details']} &nbsp;&nbsp;·&nbsp;&nbsp;
                <a href="{r['link']}" target="_blank" style="color:#667eea;">🔗 زيارة</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    active = sum(1 for r in results if "✅" in r["status"])
    suspended = sum(1 for r in results if "🚫" in r["status"])
    not_found = sum(1 for r in results if "❌" in r["status"])
    errors = sum(1 for r in results if "⚠️" in r["status"])

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("✅ نشط", active)
    c2.metric("🚫 موقوف", suspended)
    c3.metric("❌ غير موجود", not_found)
    c4.metric("⚠️ خطأ", errors)
    c5.metric("📊 المجموع", len(results))

elif check_button:
    st.warning("⚠️ أدخل رابط واحد على الأقل.")

st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    ### 🎯 دليل النتائج
    | الحالة | المعنى |
    |--------|--------|
    | ✅ **نشط** | الحساب شغال |
    | ✅ **نشط — غالباً** | موجود لكن محتاج متصفح للتأكيد |
    | 🚫 **موقوف/محظور** | معلّق أو محظور |
    | ❌ **غير موجود** | محذوف أو رابط غلط |
    | ⚠️ **تعذر الاتصال** | مشكلة شبكة |
    """)
with col2:
    st.markdown("""
    ### 📌 طرق الفحص
    | المنصة | الطريقة |
    |--------|---------|
    | 🐦 Twitter | HTTP + Pattern Matching |
    | 📘 Facebook | **Graph API** + Mobile + HTTP |
    | 📸 Instagram | HTTP + Mobile Fallback |
    | 🎵 TikTok | **oEmbed API** + HTTP |
    | 📺 YouTube | **oEmbed API** |
    """)

st.caption("🔧 Streamlit + httpx · Free APIs · مجاني 100% · لا يحتاج API Keys")
