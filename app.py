import streamlit as st
import httpx
import re
import time
import random
from urllib.parse import urlparse, urlunparse
import pandas as pd
import base64
from pathlib import Path

# =========================
# Page
# =========================
st.set_page_config(page_title="TikTok Status Checker", page_icon="🎵", layout="wide")

# =========================
# Background image helper
# Put bg.png next to app.py
# =========================
def set_bg_image(image_path: str = "bg.png"):
    p = Path(image_path)
    if not p.exists():
        # If not found, just set dark bg
        st.markdown("""
        <style>
          .stApp { background: radial-gradient(circle at 20% 10%, #111827 0%, #0b1220 55%, #060b14 100%); }
        </style>
        """, unsafe_allow_html=True)
        return

    b64 = base64.b64encode(p.read_bytes()).decode("utf-8")
    st.markdown(f"""
    <style>
      .stApp {{
        background:
          linear-gradient(rgba(6,11,20,.92), rgba(6,11,20,.92)),
          url("data:image/png;base64,{b64}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-position: center;
      }}
    </style>
    """, unsafe_allow_html=True)

set_bg_image("bg.png")

# =========================
# CSS (dark theme + clean sections)
# =========================
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.block-container {padding-top: 22px; max-width: 980px;}

.hero{
  background: rgba(10, 16, 30, .82);
  border: 1px solid rgba(255,255,255,.10);
  border-radius: 18px;
  padding: 22px 18px;
  text-align: center;
  box-shadow: 0 10px 30px rgba(0,0,0,.35);
  backdrop-filter: blur(8px);
}
.hero .logo{
  width: 52px; height: 52px; border-radius: 14px;
  display:flex; align-items:center; justify-content:center;
  margin: 0 auto 10px auto;
  background: rgba(255,255,255,.08);
  border: 1px solid rgba(255,255,255,.12);
  font-size: 26px;
}
.hero h1{
  margin: 0;
  color: #fff;
  font-size: 26px;
  font-weight: 900;
}
.hero p{
  margin: 8px 0 0 0;
  color: rgba(255,255,255,.75);
  font-size: 13px;
}

.section{
  margin-top: 16px;
  background: rgba(10, 16, 30, .72);
  border: 1px solid rgba(255,255,255,.10);
  border-radius: 18px;
  padding: 16px;
  box-shadow: 0 10px 30px rgba(0,0,0,.30);
  backdrop-filter: blur(8px);
}

.stButton > button{
  border-radius: 12px !important;
  padding: 10px 14px !important;
  border: 0 !important;
  font-weight: 800 !important;
}
.primary-btn > button{
  background: #2563eb !important;
  color: #fff !important;
}
.secondary-btn > button{
  background: rgba(255,255,255,.10) !important;
  color: #fff !important;
  border: 1px solid rgba(255,255,255,.18) !important;
}

.small-note{
  color: rgba(255,255,255,.70);
  font-size: 12px;
}

.metrics-wrap{
  background: rgba(255,255,255,.06);
  border: 1px solid rgba(255,255,255,.10);
  border-radius: 14px;
  padding: 10px 12px;
}

.dataframe-wrap{
  background: rgba(255,255,255,.06);
  border: 1px solid rgba(255,255,255,.10);
  border-radius: 14px;
  padding: 12px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# Header
# =========================
st.markdown("""
<div class="hero">
  <div class="logo">🎵</div>
  <h1>TikTok</h1>
  <p>افحص حالة الحسابات من الروابط — بدون API Keys</p>
</div>
""", unsafe_allow_html=True)

# =========================
# TikTok checker (free)
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

    # 1) oEmbed (strong signal)
    oembed_url = f"https://www.tiktok.com/oembed?url={profile_url}"
    r = safe_get(oembed_url, timeout=12)

    if r is None:
        return {"Username": clean, "Status": "Error", "Confidence": 65, "Link": profile_url}

    if r.status_code == 200:
        return {"Username": clean, "Status": "Active", "Confidence": 95, "Link": profile_url}

    if r.status_code == 404:
        return {"Username": clean, "Status": "Not Found", "Confidence": 95, "Link": profile_url}

    if r.status_code in (403, 429):
        return {"Username": clean, "Status": "Blocked", "Confidence": 75, "Link": profile_url}

    # 2) page fallback
    r2 = safe_get(profile_url, timeout=18)
    if r2 is None:
        return {"Username": clean, "Status": "Error", "Confidence": 60, "Link": profile_url}

    text = (r2.text or "").lower()
    code = r2.status_code

    if code in (403, 429):
        return {"Username": clean, "Status": "Blocked", "Confidence": 70, "Link": profile_url}

    banned_keywords = [
        "this account was banned",
        "account banned",
        "permanently banned",
        "violated our community guidelines",
    ]
    not_found_signals = [
        "couldn't find this account",
        "couldn\u2019t find this account",
        '"statuscode":10202',
    ]

    # IMPORTANT: prefer Not Found if its signals appear
    if code == 404 or any(s in text for s in not_found_signals):
        return {"Username": clean, "Status": "Not Found", "Confidence": 92, "Link": profile_url}

    if any(k in text for k in banned_keywords):
        return {"Username": clean, "Status": "Banned", "Confidence": 92, "Link": profile_url}

    strong_signals = [f"@{clean.lower()}", '"uniqueid"', 'property="og:title"']
    if code == 200 and any(s in text for s in strong_signals):
        return {"Username": clean, "Status": "Active", "Confidence": 85, "Link": profile_url}

    if code == 200:
        return {"Username": clean, "Status": "Unknown", "Confidence": 70, "Link": profile_url}

    return {"Username": clean, "Status": "Unknown", "Confidence": 65, "Link": profile_url}

# =========================
# Input section (NO extra text lines)
# =========================
st.markdown('<div class="section">', unsafe_allow_html=True)

urls_input = st.text_area(
    label="",
    height=160,
    placeholder="ضع روابط TikTok هنا (كل رابط في سطر)",
)

c1, c2, c3 = st.columns([1.2, 1.2, 2.6])
with c1:
    max_urls = st.number_input("Max links", min_value=1, max_value=200, value=25, step=1)
with c2:
    delay = st.number_input("Delay (sec)", min_value=0.0, max_value=5.0, value=0.6, step=0.1)
with c3:
    st.markdown('<div class="small-note">💡 لو ظهر Blocked كتير: زوّد الـ Delay أو قلّل عدد اللينكات.</div>', unsafe_allow_html=True)

b1, b2 = st.columns(2)
with b1:
    st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
    run = st.button("🎵 فحص TikTok", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
with b2:
    st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
    clear = st.button("🧹 مسح", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

if clear:
    st.rerun()

# =========================
# Results
# =========================
if run:
    raw = [u.strip() for u in urls_input.splitlines() if u.strip()]
    if not raw:
        st.warning("حط لينك واحد على الأقل.")
        st.stop()

    links = [normalize_url(u) for u in raw]
    # keep tiktok only (soft)
    links = [u for u in links if "tiktok.com" in u.lower()]

    if not links:
        st.error("مفيش ولا لينك TikTok صحيح.")
        st.stop()

    if len(links) > int(max_urls):
        links = links[: int(max_urls)]

    results = []
    prog = st.progress(0)
    label = st.empty()

    for i, url in enumerate(links):
        label.write(f"جارٍ الفحص: {i+1}/{len(links)}")
        username = extract_username(url)
        if not username:
            results.append({"Username": "—", "Status": "Invalid URL", "Confidence": 90, "Link": url})
        else:
            results.append(check_tiktok(username))

        prog.progress((i + 1) / len(links))
        if i < len(links) - 1 and delay > 0:
            time.sleep(float(delay))

    prog.empty()
    label.empty()

    df = pd.DataFrame(results)

    # counts
    active = int((df["Status"] == "Active").sum())
    banned = int((df["Status"] == "Banned").sum())
    not_found = int((df["Status"] == "Not Found").sum())
    blocked = int((df["Status"] == "Blocked").sum())
    unknown = int((df["Status"] == "Unknown").sum())
    total = len(df)

    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.markdown('<div class="metrics-wrap">', unsafe_allow_html=True)
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("✅ Active", active)
    m2.metric("🚫 Banned", banned)
    m3.metric("❌ Not Found", not_found)
    m4.metric("⚠️ Blocked", blocked)
    m5.metric("❓ Unknown", unknown)
    m6.metric("📦 Total", total)
    st.markdown('</div>', unsafe_allow_html=True)

    # table: Username | Status | Link
    st.markdown('<div class="dataframe-wrap">', unsafe_allow_html=True)
    show_df = df[["Username", "Status", "Link"]].copy()
    st.dataframe(show_df, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # CSV
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download CSV",
        data=csv_bytes,
        file_name="tiktok_status_results.csv",
        mime="text/csv",
        use_container_width=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

st.caption("Streamlit + httpx · TikTok oEmbed + HTML fallback · Free (no API Keys)")
