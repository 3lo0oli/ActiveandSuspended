import streamlit as st
import httpx
import re
import time
import random
from urllib.parse import urlparse, urlunparse

# =========================
# Streamlit Page
# =========================
st.set_page_config(page_title="TikTok Status Checker", page_icon="🎵", layout="wide")

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
        padding: 18px 24px;
        border-radius: 14px;
        margin-bottom: 18px;
        color: white;
        text-align: center;
    }
    .main-header h1 { color: white; margin: 0; font-size: 1.8em; }
    .main-header p { color: #d1d5db; margin: 6px 0 0 0; }

    .result-card {
        background: #f9fafb;
        border-radius: 12px;
        padding: 14px 18px;
        margin: 10px 0;
        border-left: 6px solid #e5e7eb;
    }
    .ok { border-left-color: #22c55e; background: #f0fdf4; }
    .bad { border-left-color: #ef4444; background: #fff1f2; }
    .warn { border-left-color: #f59e0b; background: #fffbeb; }
    .unk { border-left-color: #6b7280; background: #f3f4f6; }

    .pill {
        display:inline-block;
        padding: 2px 10px;
        border-radius: 999px;
        background: #111827;
        color: white;
        font-size: 12px;
        margin-left: 8px;
    }
    code { background: #e5e7eb; padding: 2px 6px; border-radius: 6px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>🎵 TikTok Account Status Checker</h1>
    <p>يفحص الحسابات من اللينكات ويطلع Status + Confidence — بدون أي API Keys</p>
</div>
""", unsafe_allow_html=True)

# =========================
# User Agents
# =========================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
]

def headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
    }

# =========================
# Helpers
# =========================
def normalize_url(url: str) -> str:
    """
    - force https
    - remove query/fragment
    - trim spaces
    """
    url = url.strip()
    if not url:
        return url
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    p = urlparse(url)
    scheme = "https"
    netloc = p.netloc.lower()
    path = p.path.rstrip("/")
    return urlunparse((scheme, netloc, path, "", "", ""))

def is_tiktok_url(url: str) -> bool:
    u = url.lower()
    return "tiktok.com" in u

def extract_tiktok_username(url: str) -> str | None:
    """
    Supports:
    - https://www.tiktok.com/@username
    - https://tiktok.com/@username
    - https://www.tiktok.com/@username/video/...
    """
    url = normalize_url(url)
    m = re.search(r"tiktok\.com/@([^/?#]+)", url, flags=re.IGNORECASE)
    if m:
        return m.group(1)
    return None

def safe_get(url: str, timeout: int = 20) -> httpx.Response | None:
    try:
        with httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            http2=True,
            verify=True
        ) as client:
            return client.get(url, headers=headers())
    except Exception:
        # retry once with http2 off
        try:
            with httpx.Client(
                timeout=timeout,
                follow_redirects=True,
                http2=False,
                verify=True
            ) as client:
                return client.get(url, headers=headers())
        except Exception:
            return None

# =========================
# TikTok Checker (Status + Confidence)
# =========================
def check_tiktok(username: str) -> dict:
    clean = username.lstrip("@").strip()
    profile_url = f"https://www.tiktok.com/@{clean}"

    # ---- Step 1: oEmbed (free)
    oembed_url = f"https://www.tiktok.com/oembed?url={profile_url}"
    r = safe_get(oembed_url, timeout=15)

    if r is None:
        return {
            "platform": "TikTok",
            "username": clean,
            "status": "⚠️ Connection Error",
            "confidence": 65,
            "link": profile_url,
            "reason": "Could not reach oEmbed endpoint"
        }

    if r.status_code == 200:
        # account exists (very strong signal)
        return {
            "platform": "TikTok",
            "username": clean,
            "status": "✅ Active",
            "confidence": 95,
            "link": profile_url,
            "reason": "Confirmed via oEmbed (HTTP 200)"
        }

    if r.status_code == 404:
        return {
            "platform": "TikTok",
            "username": clean,
            "status": "❌ Not Found",
            "confidence": 95,
            "link": profile_url,
            "reason": "oEmbed returned 404 (profile likely missing)"
        }

    if r.status_code in (403, 429):
        # blocked / rate limited
        return {
            "platform": "TikTok",
            "username": clean,
            "status": "⚠️ Blocked / Rate limited",
            "confidence": 75,
            "link": profile_url,
            "reason": f"oEmbed returned HTTP {r.status_code}"
        }

    # ---- Step 2: Direct page fallback
    r2 = safe_get(profile_url, timeout=20)
    if r2 is None:
        return {
            "platform": "TikTok",
            "username": clean,
            "status": "⚠️ Connection Error",
            "confidence": 60,
            "link": profile_url,
            "reason": "Could not reach profile page"
        }

    text = (r2.text or "").lower()
    code = r2.status_code

    if code in (403, 429):
        return {
            "platform": "TikTok",
            "username": clean,
            "status": "⚠️ Blocked / Rate limited",
            "confidence": 70,
            "link": profile_url,
            "reason": f"Profile returned HTTP {code}"
        }

    # keywords for banned
    banned_keywords = [
        "this account was banned",
        "account banned",
        "permanently banned",
        "violated our community guidelines",
    ]
    if any(k in text for k in banned_keywords):
        return {
            "platform": "TikTok",
            "username": clean,
            "status": "🚫 Banned / Suspended",
            "confidence": 95,
            "link": profile_url,
            "reason": "Ban keywords detected on page"
        }

    # not found signals
    if code == 404 or '"statuscode":10202' in text or "couldn't find this account" in text or "couldn\u2019t find this account" in text:
        return {
            "platform": "TikTok",
            "username": clean,
            "status": "❌ Not Found",
            "confidence": 92,
            "link": profile_url,
            "reason": "Not-found signals detected on page"
        }

    # active signals
    strong_signals = [
        f"@{clean.lower()}",
        '"uniqueid"',
        'property="og:title"',
        'property="og:description"',
    ]
    if code == 200 and any(s in text for s in strong_signals):
        return {
            "platform": "TikTok",
            "username": clean,
            "status": "✅ Likely Active",
            "confidence": 85,
            "link": profile_url,
            "reason": "Profile signals detected on page"
        }

    if code == 200:
        return {
            "platform": "TikTok",
            "username": clean,
            "status": "❓ Unknown (200)",
            "confidence": 70,
            "link": profile_url,
            "reason": "Page loaded but signals were weak (possible wall/AB test)"
        }

    return {
        "platform": "TikTok",
        "username": clean,
        "status": "❓ Unknown",
        "confidence": 65,
        "link": profile_url,
        "reason": f"Unhandled HTTP {code}"
    }

# =========================
# UI
# =========================
st.subheader("📝 أدخل روابط TikTok (كل رابط في سطر)")

with st.expander("📌 أمثلة"):
    st.code("""https://www.tiktok.com/@khaby.lame
https://tiktok.com/@this_user_does_not_exist_123456789
""")

urls_input = st.text_area(
    "الروابط:",
    height=220,
    placeholder="https://www.tiktok.com/@username\nhttps://tiktok.com/@username"
)

c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    max_urls = st.number_input("Max links", min_value=1, max_value=200, value=25, step=1)
with c2:
    delay = st.number_input("Delay بين كل فحص (ثواني)", min_value=0.0, max_value=5.0, value=0.6, step=0.1)
with c3:
    st.caption("💡 لو ظهر Blocked/Rate limited زوّد الـ Delay أو قلّل عدد اللينكات في الدفعة.")

btn1, btn2 = st.columns(2)
with btn1:
    run = st.button("🎵 فحص TikTok", type="primary", use_container_width=True)
with btn2:
    clear = st.button("🗑️ مسح", use_container_width=True)

if clear:
    st.rerun()

def render_card(item: dict):
    status = item["status"]
    conf = item["confidence"]
    if status.startswith("✅"):
        cls = "ok"
    elif status.startswith("❌") or status.startswith("🚫"):
        cls = "bad"
    elif status.startswith("⚠️"):
        cls = "warn"
    else:
        cls = "unk"

    st.markdown(f"""
    <div class="result-card {cls}">
        <div style="display:flex; justify-content:space-between; gap:10px; flex-wrap:wrap; align-items:center;">
            <div>
                <strong style="font-size:1.05em;">🎵 TikTok</strong>
                <span class="pill">{conf}%</span>
                &nbsp;·&nbsp;<code>@{item["username"]}</code>
            </div>
            <div style="font-size:1.05em; font-weight:700;">{status}</div>
        </div>
        <div style="margin-top:8px; color:#374151; font-size:0.92em;">
            📝 {item["reason"]} &nbsp;&nbsp;·&nbsp;&nbsp;
            <a href="{item["link"]}" target="_blank">🔗 Open</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

if run:
    raw = [u.strip() for u in urls_input.splitlines() if u.strip()]
    if not raw:
        st.warning("⚠️ حط لينك واحد على الأقل.")
        st.stop()

    # normalize + filter tiktok only
    cleaned = []
    for u in raw:
        u2 = normalize_url(u)
        if is_tiktok_url(u2):
            cleaned.append(u2)

    if not cleaned:
        st.error("❌ مفيش ولا لينك TikTok صحيح في اللي دخلتهم.")
        st.stop()

    if len(cleaned) > int(max_urls):
        st.info(f"ℹ️ هفحص أول {int(max_urls)} لينك فقط.")
        cleaned = cleaned[: int(max_urls)]

    st.markdown("---")
    st.subheader(f"📊 النتائج ({len(cleaned)} روابط)")

    progress = st.progress(0)
    ph = st.empty()

    results = []
    for i, url in enumerate(cleaned):
        ph.text(f"جارٍ فحص ({i+1}/{len(cleaned)}): {url}")
        username = extract_tiktok_username(url)
        if not username:
            results.append({
                "platform": "TikTok",
                "username": "—",
                "status": "❓ Invalid URL",
                "confidence": 90,
                "link": url,
                "reason": "Could not extract username from URL"
            })
        else:
            results.append(check_tiktok(username))

        progress.progress((i + 1) / len(cleaned))
        if i < len(cleaned) - 1 and delay > 0:
            time.sleep(float(delay))

    progress.empty()
    ph.empty()

    # summary metrics
    active = sum(1 for r in results if r["status"].startswith("✅"))
    banned = sum(1 for r in results if r["status"].startswith("🚫"))
    not_found = sum(1 for r in results if r["status"].startswith("❌"))
    blocked = sum(1 for r in results if r["status"].startswith("⚠️"))
    unknown = len(results) - (active + banned + not_found + blocked)

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("✅ Active", active)
    m2.metric("🚫 Banned", banned)
    m3.metric("❌ Not Found", not_found)
    m4.metric("⚠️ Blocked", blocked)
    m5.metric("❓ Unknown", unknown)
    m6.metric("📦 Total", len(results))

    st.markdown("### 📄 التفاصيل")
    for r in results:
        render_card(r)

    # CSV download
    st.markdown("---")
    import csv
    import io

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["platform", "username", "status", "confidence", "link", "reason"])
    writer.writeheader()
    writer.writerows(results)
    csv_bytes = buf.getvalue().encode("utf-8")

    st.download_button(
        "⬇️ Download CSV",
        data=csv_bytes,
        file_name="tiktok_status_results.csv",
        mime="text/csv",
        use_container_width=True
    )

st.markdown("---")
st.caption("🧰 Streamlit + httpx · TikTok oEmbed + fallback HTML signals · Free (no API keys)")
