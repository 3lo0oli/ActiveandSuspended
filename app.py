import streamlit as st
import httpx
import re
import time
import random
import json

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
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
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


def get_headers() -> dict:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
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


def make_request(url: str, timeout: int = 20) -> httpx.Response | None:
    """Make an HTTP request with retries."""
    for attempt in range(2):
        try:
            with httpx.Client(
                timeout=timeout,
                follow_redirects=True,
                http2=True,
            ) as client:
                resp = client.get(url, headers=get_headers())
                return resp
        except Exception:
            if attempt == 0:
                time.sleep(1)
    return None


# ==================== Platform Checkers ====================

def check_twitter(username: str) -> tuple[str, str, str]:
    """Check Twitter/X account status."""
    url = f"https://x.com/{username}"
    resp = make_request(url)

    if resp is None:
        return "⚠️ تعذر الاتصال", url, "لم نتمكن من الوصول للموقع"

    text = resp.text.lower()
    status_code = resp.status_code

    # ---- Suspended ----
    suspended_signals = [
        "account is suspended",
        "account has been suspended",
        "suspended account",
        "this account is suspended",
        "caution: this account is temporarily restricted",
    ]
    if any(s in text for s in suspended_signals):
        return "🚫 موقوف (Suspended)", url, "الحساب معلّق من المنصة"

    # ---- Not Found ----
    not_found_signals = [
        "this account doesn't exist",
        "this account doesn\u2019t exist",
        "page doesn't exist",
        "hmm...this page doesn",
        "something went wrong. try reloading",
    ]
    if status_code == 404 or any(s in text for s in not_found_signals):
        return "❌ غير موجود", url, "الحساب غير موجود أو تم حذفه"

    # ---- Active ----
    # Check for username in meta tags / title / JSON-LD
    active_signals = [
        f"@{username.lower()}",
        f'"screen_name":"{username.lower()}"',
        f"/{username.lower()}",
        f'content="@{username.lower()}"',
    ]
    if status_code == 200 and any(s in text for s in active_signals):
        return "✅ نشط (Active)", url, "الحساب شغال وموجود"

    # If we got 200 but can't confirm — likely JS-rendered
    if status_code == 200:
        return "✅ نشط (Active) — غالباً", url, "الصفحة موجودة (لكن المحتوى يحتاج متصفح للتأكيد)"

    return "❓ غير محدد", url, f"كود الاستجابة: {status_code}"


def check_facebook(username: str) -> tuple[str, str, str]:
    """Check Facebook account status."""
    url = f"https://www.facebook.com/{username}"
    resp = make_request(url)

    if resp is None:
        return "⚠️ تعذر الاتصال", url, "لم نتمكن من الوصول للموقع"

    text = resp.text.lower()
    status_code = resp.status_code

    not_found_signals = [
        "this content isn't available",
        "this content isn\u2019t available",
        "this page isn't available",
        "this page isn\u2019t available",
        "the link you followed may be broken",
        "page not found",
        "sorry, this content isn",
    ]
    if status_code == 404 or any(s in text for s in not_found_signals):
        return "❌ غير موجود", url, "الصفحة غير موجودة أو محذوفة"

    # Check for disabled/banned
    disabled_signals = [
        "this account has been disabled",
        "account has been disabled",
        "violated our community standards",
    ]
    if any(s in text for s in disabled_signals):
        return "🚫 معطل (Disabled)", url, "الحساب تم تعطيله لمخالفة القوانين"

    # Active check — look for og:title or profile signals
    if status_code == 200:
        active_signals = [
            'property="og:title"',
            'property="og:url"',
            f"facebook.com/{username.lower()}",
        ]
        if any(s in text for s in active_signals):
            return "✅ نشط (Active)", url, "الصفحة موجودة وشغالة"
        # Got 200 but Facebook often requires login
        return "✅ نشط (Active) — غالباً", url, "الصفحة موجودة (قد تحتاج تسجيل دخول للتأكيد)"

    return "❓ غير محدد", url, f"كود الاستجابة: {status_code}"


def check_instagram(username: str) -> tuple[str, str, str]:
    """Check Instagram account status."""
    url = f"https://www.instagram.com/{username}/"
    resp = make_request(url)

    if resp is None:
        return "⚠️ تعذر الاتصال", url, "لم نتمكن من الوصول للموقع"

    text = resp.text.lower()
    status_code = resp.status_code

    not_found_signals = [
        "sorry, this page isn't available",
        "sorry, this page isn\u2019t available",
        "the link you followed may be broken",
        "page not found",
    ]
    if status_code == 404 or any(s in text for s in not_found_signals):
        return "❌ غير موجود", url, "الحساب غير موجود أو محذوف"

    suspended_signals = [
        "this account has been suspended",
        "account suspended",
        "violating our terms",
    ]
    if any(s in text for s in suspended_signals):
        return "🚫 موقوف (Suspended)", url, "الحساب معلّق"

    if status_code == 200:
        # Instagram usually has the username in meta tags
        active_signals = [
            f'"{username.lower()}"',
            f"@{username.lower()}",
            f"instagram.com/{username.lower()}",
            'property="og:title"',
        ]
        if any(s in text for s in active_signals):
            return "✅ نشط (Active)", url, "الحساب شغال وموجود"
        # IG might require login for some profiles
        return "✅ نشط (Active) — غالباً", url, "الصفحة موجودة (قد تحتاج تسجيل دخول)"

    # Instagram returns 302 redirect to login sometimes
    if status_code in (301, 302):
        return "✅ نشط (Active) — غالباً", url, "تم التحويل (الحساب موجود لكن يحتاج تسجيل دخول)"

    return "❓ غير محدد", url, f"كود الاستجابة: {status_code}"


def check_tiktok(username: str) -> tuple[str, str, str]:
    """Check TikTok account status."""
    url = f"https://www.tiktok.com/@{username}"
    resp = make_request(url)

    if resp is None:
        return "⚠️ تعذر الاتصال", url, "لم نتمكن من الوصول للموقع"

    text = resp.text.lower()
    status_code = resp.status_code

    not_found_signals = [
        "couldn't find this account",
        "couldn\u2019t find this account",
        "this account was banned",
        "page not available",
        "user not found",
        '"statuscode":10202',
        '"statuscode": 10202',
    ]

    banned_signals = [
        "this account was banned",
        "account banned",
        "permanently banned",
        "account has been banned",
    ]

    if any(s in text for s in banned_signals):
        return "🚫 محظور (Banned)", url, "الحساب محظور من المنصة"

    if status_code == 404 or any(s in text for s in not_found_signals):
        return "❌ غير موجود", url, "الحساب غير موجود"

    if status_code == 200:
        active_signals = [
            f"@{username.lower()}",
            f'"uniqueid":"{username.lower()}"',
            f'"uniqueId":"{username.lower()}"',
            'property="og:title"',
        ]
        if any(s in text for s in active_signals):
            return "✅ نشط (Active)", url, "الحساب شغال وموجود"
        return "✅ نشط (Active) — غالباً", url, "الصفحة موجودة"

    return "❓ غير محدد", url, f"كود الاستجابة: {status_code}"


def check_youtube(username: str) -> tuple[str, str, str]:
    """Check YouTube channel using oembed (free API)."""
    # Try multiple URL formats
    url_formats = [
        f"https://www.youtube.com/@{username}",
        f"https://www.youtube.com/c/{username}",
        f"https://www.youtube.com/user/{username}",
    ]
    # If it looks like a channel ID
    if username.startswith("UC") and len(username) == 24:
        url_formats = [f"https://www.youtube.com/channel/{username}"]

    for page_url in url_formats:
        # Use oembed — free, no API key needed
        oembed_url = f"https://www.youtube.com/oembed?url={page_url}&format=json"
        resp = make_request(oembed_url, timeout=15)

        if resp is not None and resp.status_code == 200:
            try:
                data = resp.json()
                title = data.get("author_name", username)
                return "✅ نشط (Active)", page_url, f"القناة شغالة — اسمها: {title}"
            except Exception:
                return "✅ نشط (Active)", page_url, "القناة موجودة"

    # If oembed failed for all formats, try direct page check
    direct_url = url_formats[0]
    resp = make_request(direct_url)

    if resp is not None:
        text = resp.text.lower()
        if resp.status_code == 404 or "this page isn" in text:
            return "❌ غير موجود", direct_url, "القناة غير موجودة"

        if resp.status_code == 200:
            # Check for termination
            if "this account has been terminated" in text:
                return "🚫 محذوف (Terminated)", direct_url, "القناة تم إنهاؤها لمخالفة القوانين"
            if "has been suspended" in text:
                return "🚫 موقوف (Suspended)", direct_url, "القناة معلّقة"
            return "✅ نشط (Active) — غالباً", direct_url, "القناة موجودة"

    return "❓ غير محدد", direct_url, "لم نتمكن من التحقق"


# ==================== Main Checker ====================

CHECKERS = {
    "twitter":   check_twitter,
    "facebook":  check_facebook,
    "instagram": check_instagram,
    "tiktok":    check_tiktok,
    "youtube":   check_youtube,
}

PLATFORM_ICONS = {
    "twitter": "🐦", "facebook": "📘", "instagram": "📸",
    "tiktok": "🎵", "youtube": "📺", "unknown": "❓",
}


def check_account(url: str) -> dict:
    platform = detect_platform(url)
    if not platform:
        return {"url": url, "platform": "unknown", "status": "❓ منصة غير مدعومة",
                "link": url, "details": "المنصة غير معروفة — تأكد من الرابط"}

    username = extract_username(url, platform)
    if not username:
        return {"url": url, "platform": platform, "status": "❓ رابط غير صحيح",
                "link": url, "details": "لم نتمكن من استخراج اسم المستخدم"}

    checker = CHECKERS.get(platform)
    status, link, details = checker(username)

    return {
        "url": url,
        "platform": platform,
        "username": username,
        "status": status,
        "link": link,
        "details": details,
    }


# ==================== UI ====================

st.subheader("📝 أدخل الروابط (حتى 10 روابط)")

st.info("💡 **مجاني 100%** — يعتمد على تحليل HTTP Status + Pattern Matching بدون أي API مدفوع")

with st.expander("📌 أمثلة للاختبار"):
    st.code("""https://twitter.com/elonmusk
https://facebook.com/zuck
https://instagram.com/cristiano
https://tiktok.com/@khaby.lame
https://youtube.com/@MrBeast""")

urls_input = st.text_area(
    "ضع كل رابط في سطر منفصل:",
    height=220,
    placeholder="https://twitter.com/username\nhttps://instagram.com/username\nhttps://youtube.com/@channel",
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
        st.warning("⚠️ الحد الأقصى 10 روابط — هيتم فحص أول 10 فقط.")
        urls = urls[:10]

    st.markdown("---")
    st.subheader(f"📊 النتائج ({len(urls)} حساب)")

    progress = st.progress(0)
    status_placeholder = st.empty()

    results = []
    for i, url in enumerate(urls):
        status_placeholder.text(f"⏳ جارٍ فحص {i + 1}/{len(urls)} ...")
        result = check_account(url)
        results.append(result)
        progress.progress((i + 1) / len(urls))
        if i < len(urls) - 1:
            time.sleep(1.5)  # rate limiting

    progress.empty()
    status_placeholder.empty()

    # ---------- Display Results ----------
    for r in results:
        icon = PLATFORM_ICONS.get(r["platform"], "❓")
        status = r["status"]

        # Pick CSS class
        if "✅" in status:
            css_class = "result-active"
        elif "🚫" in status:
            css_class = "result-suspended"
        elif "❌" in status:
            css_class = "result-disabled"
        else:
            css_class = "result-error"

        username_display = r.get("username", "—")

        st.markdown(f"""
        <div class="result-card {css_class}">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
                <div>
                    <strong>{icon} {r['platform'].upper()}</strong> &nbsp;·&nbsp;
                    <code>@{username_display}</code>
                </div>
                <div style="font-size:1.15em; font-weight:bold;">
                    {status}
                </div>
            </div>
            <div style="color:#666; font-size:0.9em; margin-top:5px;">
                {r['details']} &nbsp;·&nbsp;
                <a href="{r['link']}" target="_blank">🔗 زيارة</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ---------- Summary ----------
    st.markdown("---")
    active = sum(1 for r in results if "✅" in r["status"])
    suspended = sum(1 for r in results if "🚫" in r["status"])
    disabled = sum(1 for r in results if "❌" in r["status"])
    other = len(results) - active - suspended - disabled

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("✅ نشط", active)
    c2.metric("🚫 موقوف", suspended)
    c3.metric("❌ غير موجود", disabled)
    c4.metric("❓ غير محدد", other)
    c5.metric("📊 المجموع", len(results))

elif check_button:
    st.warning("⚠️ أدخل رابط واحد على الأقل.")

# ==================== Footer ====================
st.markdown("---")
st.markdown("""
### 🎯 كيف يشتغل؟

| الحالة | المعنى |
|--------|--------|
| ✅ **نشط** | الحساب شغال وموجود |
| 🚫 **موقوف/محظور** | الحساب معلّق أو محظور من المنصة |
| ❌ **غير موجود** | الحساب محذوف أو الرابط غلط |
| ⚠️ **تعذر الاتصال** | مشكلة في الشبكة — جرب تاني |

### 📌 المنصات المدعومة
🐦 **Twitter/X** · 📘 **Facebook** · 📸 **Instagram** · 🎵 **TikTok** · 📺 **YouTube**

### ⚠️ ملاحظات مهمة
- بعض المنصات (خصوصاً Instagram و Facebook) ممكن تطلب تسجيل دخول لعرض البروفايل
- النتيجة "غالباً نشط" معناها إن الصفحة موجودة لكن المنصة محتاجة browser كامل للتأكيد 100%
- الفحص مجاني بالكامل ولا يحتاج أي API Key
""")

st.caption("🔧 Built with Streamlit + httpx · مجاني 100% · لا يحتاج API Keys")
