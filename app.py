import streamlit as st
import httpx
import re
import time
import random
from urllib.parse import urlparse, urlunparse
import csv
import io

# =========================
# Page
# =========================
st.set_page_config(page_title="TikTok Status Checker", page_icon="🎵", layout="wide")

# =========================
# THEME (you can tweak)
# =========================
PRIMARY_BLUE = "#3F6FB6"     # main blue (boxes)
PRIMARY_BLUE_DARK = "#2F5EA4"
BG = "#F4F6FB"               # page background
TEXT = "#0F172A"
CARD_BG = "#FFFFFF"
BORDER = "rgba(15, 23, 42, 0.12)"

# =========================
# CSS
# =========================
st.markdown(f"""
<style>
/* page */
.stApp {{
  background: {BG};
  color: {TEXT};
}}

/* hide default menu/footer */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header {{visibility: hidden;}}

/* make content wider */
.block-container {{
  padding-top: 22px;
  max-width: 1100px;
}}

/* top header */
.hero {{
  background: #0B0F19;
  border-radius: 16px;
  padding: 26px 20px;
  text-align: center;
  box-shadow: 0 10px 30px rgba(0,0,0,.18);
}}
.hero .title {{
  font-size: 28px;
  font-weight: 800;
  color: #fff;
  margin: 0;
  line-height: 1.2;
}}
.hero .subtitle {{
  margin-top: 8px;
  color: rgba(255,255,255,.75);
  font-size: 15px;
}}
.logo-box {{
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: rgba(255,255,255,.08);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  border: 1px solid rgba(255,255,255,.12);
}}
.logo-box span {{
  font-size: 26px;
}}

/* blue section wrappers */
.section-blue {{
  background: {PRIMARY_BLUE};
  border-radius: 16px;
  padding: 18px;
  margin-top: 20px;
  box-shadow: 0 14px 30px rgba(63,111,182,.25);
}}
.section-blue .section-title {{
  color: #fff;
  font-weight: 800;
  font-size: 20px;
  text-align: center;
  margin: 0 0 14px 0;
}}
.section-blue .hint {{
  color: rgba(255,255,255,.85);
  text-align: center;
  font-size: 13px;
  margin-top: -8px;
  margin-bottom: 12px;
}}

/* input card inside blue */
.inner-card {{
  background: rgba(255,255,255,.15);
  border: 1px solid rgba(255,255,255,.25);
  border-radius: 14px;
  padding: 16px;
}}

/* style text area a bit */
textarea {{
  border-radius: 12px !important;
  border: 1px solid rgba(255,255,255,.35) !important;
}}

/* button styling */
.stButton > button {{
  border-radius: 12px !important;
  padding: 10px 14px !important;
  border: 0 !important;
  font-weight: 700 !important;
}}
.primary-btn > button {{
  background: #0B0F19 !important;
  color: #fff !important;
}}
.ghost-btn > button {{
  background: rgba(255,255,255,.18) !important;
  color: #fff !important;
  border: 1px solid rgba(255,255,255,.25) !important;
}}
.primary-btn > button:hover {{
  background: #111827 !important;
}}
.ghost-btn > button:hover {{
  background: rgba(255,255,255,.24) !important;
}}

/* results area */
.results-wrap {{
  background: {PRIMARY_BLUE};
  border-radius: 16px;
  padding: 18px;
  margin-top: 20px;
  box-shadow: 0 14px 30px rgba(63,111,182,.25);
}}
.results-wrap .section-title {{
  color: #fff;
  font-weight: 800;
  font-size: 20px;
  text-align: center;
  margin: 0 0 14px 0;
}}

/* result card */
.r-card {{
  background: {CARD_BG};
  border: 1px solid {BORDER};
  border-radius: 14px;
  padding: 14px 14px;
  margin: 10px 0;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}}
.r-left {{
  display:flex;
  align-items:center;
  gap:10px;
  flex-wrap: wrap;
}}
.badge {{
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
  border: 1px solid {BORDER};
}}
.badge-ok {{ background: rgba(34,197,94,.12); color: #166534; border-color: rgba(34,197,94,.28); }}
.badge-bad {{ background: rgba(239,68,68,.10); color: #7f1d1d; border-color: rgba(239,68,68,.25); }}
.badge-warn {{ background: rgba(245,158,11,.14); color: #7c2d12; border-color: rgba(245,158,11,.28); }}
.badge-unk {{ background: rgba(100,116,139,.14); color: #0f172a; border-color: rgba(100,116,139,.25); }}

.conf {{
  font-size: 12px;
  font-weight: 800;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(15,23,42,.06);
  border: 1px solid {BORDER};
}}

.small {{
  color: rgba(15, 23, 42, .75);
  font-size: 12px;
}}

a {{
  text-decoration: none;
}}
</style>
""", unsafe_allow_html=True)

# =========================
# Header UI (same "system" as your mock)
# =========================
st.markdown("""
<div class="hero">
  <div class="logo-box"><span>🎵</span></div>
  <h1 class="title">TikTok</h1>
  <div class="subtitle">هنا مكتوب وتحط اللوجو — فحص حالة الحساب من اللينكات</div>
</div>
""", unsafe_allow_html=True)

# =========================
# TikTok checker logic (Free, no keys)
# =========================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
]

def req_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
    }

def normalize_url(url: str) -> str:
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

def is_tiktok(url: str) -> bool:
    return "tiktok.com" in url.lower()

def extract_username(url: str) -> str | None:
    url = normalize_url(url)
    m = re.search(r"tiktok\.com/@([^/?#]+)", url, flags=re.IGNORECASE)
    return m.group(1) if m else None

def safe_get(url: str, timeout: int = 18) -> httpx.Response | None:
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True, http2=True, verify=True) as client:
            return client.get(url, headers=req_headers())
    except Exception:
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True, http2=False, verify=True) as client:
                return client.get(url, headers=req_headers())
        except Exception:
            return None

def check_tiktok(username: str) -> dict:
    clean = username.lstrip("@").strip()
    profile_url = f"https://www.tiktok.com/@{clean}"

    # 1) oEmbed
    oembed_url = f"https://www.tiktok.com/oembed?url={profile_url}"
    r = safe_get(oembed_url, timeout=12)

    if r is None:
        return {"username": clean, "status": "⚠️ Error", "confidence": 65, "link": profile_url, "reason": "Connection error (oEmbed)"}

    if r.status_code == 200:
        return {"username": clean, "status": "✅ Active", "confidence": 95, "link": profile_url, "reason": "Confirmed via oEmbed (200)"}

    if r.status_code == 404:
        return {"username": clean, "status": "❌ Not Found", "confidence": 95, "link": profile_url, "reason": "oEmbed returned 404"}

    if r.status_code in (403, 429):
        return {"username": clean, "status": "⚠️ Blocked", "confidence": 75, "link": profile_url, "reason": f"oEmbed HTTP {r.status_code}"}

    # 2) page fallback
    r2 = safe_get(profile_url, timeout=18)
    if r2 is None:
        return {"username": clean, "status": "⚠️ Error", "confidence": 60, "link": profile_url, "reason": "Connection error (profile)"}

    text = (r2.text or "").lower()
    code = r2.status_code

    if code in (403, 429):
        return {"username": clean, "status": "⚠️ Blocked", "confidence": 70, "link": profile_url, "reason": f"Profile HTTP {code}"}

    banned_keywords = [
        "this account was banned",
        "account banned",
        "permanently banned",
        "violated our community guidelines",
    ]
    if any(k in text for k in banned_keywords):
        return {"username": clean, "status": "🚫 Banned", "confidence": 95, "link": profile_url, "reason": "Ban keywords detected"}

    if code == 404 or '"statuscode":10202' in text or "couldn't find this account" in text or "couldn\u2019t find this account" in text:
        return {"username": clean, "status": "❌ Not Found", "confidence": 92, "link": profile_url, "reason": "Not-found signals detected"}

    strong_signals = [f"@{clean.lower()}", '"uniqueid"', 'property="og:title"', 'property="og:description"']
    if code == 200 and any(s in text for s in strong_signals):
        return {"username": clean, "status": "✅ Likely Active", "confidence": 85, "link": profile_url, "reason": "Profile signals detected"}

    if code == 200:
        return {"username": clean, "status": "❓ Unknown", "confidence": 70, "link": profile_url, "reason": "Loaded but weak signals (possible wall/AB test)"}

    return {"username": clean, "status": "❓ Unknown", "confidence": 65, "link": profile_url, "reason": f"Unhandled HTTP {code}"}

# =========================
# Middle blue input box (like your mock)
# =========================
st.markdown("""
<div class="section-blue">
  <div class="section-title">هنا مكان اختبار اللينكات</div>
  <div class="hint">اكتب كل لينك TikTok في سطر لوحده</div>
  <div class="inner-card">
""", unsafe_allow_html=True)

urls_input = st.text_area(
    label="",
    height=170,
    placeholder="https://www.tiktok.com/@username\nhttps://tiktok.com/@username",
)

c1, c2, c3 = st.columns([1.1, 1.1, 2.2])
with c1:
    max_urls = st.number_input("Max links", min_value=1, max_value=200, value=25, step=1)
with c2:
    delay = st.number_input("Delay (sec)", min_value=0.0, max_value=5.0, value=0.6, step=0.1)
with c3:
    st.caption("💡 لو ظهر Blocked كتير: زوّد الـ Delay أو قلّل عدد اللينكات في الدفعة.")

b1, b2 = st.columns(2)
with b1:
    st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
    run = st.button("🎵 فحص TikTok", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
with b2:
    st.markdown('<div class="ghost-btn">', unsafe_allow_html=True)
    clear = st.button("🧹 مسح", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("</div></div></div>", unsafe_allow_html=True)

if clear:
    st.rerun()

# =========================
# Results big blue area (like your mock)
# =========================
def badge_class(status: str) -> str:
    if status.startswith("✅"):
        return "badge-ok"
    if status.startswith("🚫") or status.startswith("❌"):
        return "badge-bad"
    if status.startswith("⚠️"):
        return "badge-warn"
    return "badge-unk"

def render_result(r: dict):
    cls = badge_class(r["status"])
    st.markdown(f"""
    <div class="r-card">
      <div class="r-left">
        <div class="badge {cls}">{r["status"]}</div>
        <div class="conf">{r["confidence"]}%</div>
        <div><code>@{r["username"]}</code></div>
      </div>
      <div class="small">
        {r["reason"]} &nbsp;·&nbsp;
        <a href="{r["link"]}" target="_blank">Open</a>
      </div>
    </div>
    """, unsafe_allow_html=True)

if run:
    raw = [u.strip() for u in urls_input.splitlines() if u.strip()]
    if not raw:
        st.warning("⚠️ حط لينك واحد على الأقل.")
        st.stop()

    cleaned = []
    for u in raw:
        u2 = normalize_url(u)
        if is_tiktok(u2):
            cleaned.append(u2)

    if not cleaned:
        st.error("❌ مفيش ولا لينك TikTok صحيح.")
        st.stop()

    if len(cleaned) > int(max_urls):
        cleaned = cleaned[: int(max_urls)]

    results = []
    progress = st.progress(0)
    status_line = st.empty()

    for i, url in enumerate(cleaned):
        status_line.write(f"جارٍ الفحص: {i+1}/{len(cleaned)}")
        username = extract_username(url)
        if not username:
            results.append({"username": "—", "status": "❓ Invalid URL", "confidence": 90, "link": url, "reason": "Could not extract username"})
        else:
            results.append(check_tiktok(username))

        progress.progress((i + 1) / len(cleaned))
        if i < len(cleaned) - 1 and delay > 0:
            time.sleep(float(delay))

    progress.empty()
    status_line.empty()

    active = sum(1 for r in results if r["status"].startswith("✅"))
    banned = sum(1 for r in results if r["status"].startswith("🚫"))
    not_found = sum(1 for r in results if r["status"].startswith("❌"))
    blocked = sum(1 for r in results if r["status"].startswith("⚠️"))
    unknown = len(results) - (active + banned + not_found + blocked)

    st.markdown("""
    <div class="results-wrap">
      <div class="section-title">هنا النتائج تطلع</div>
    </div>
    """, unsafe_allow_html=True)

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("✅ Active", active)
    m2.metric("🚫 Banned", banned)
    m3.metric("❌ Not Found", not_found)
    m4.metric("⚠️ Blocked", blocked)
    m5.metric("❓ Unknown", unknown)
    m6.metric("📦 Total", len(results))

    # results list inside the big blue section
    st.markdown(f"""
    <div class="results-wrap">
      <div class="section-title">تفاصيل النتائج</div>
    </div>
    """, unsafe_allow_html=True)

    for r in results:
        render_result(r)

    # download csv
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["username", "status", "confidence", "link", "reason"])
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

st.caption("Streamlit + httpx · TikTok oEmbed + HTML fallback · مجاني بدون API Keys")
