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
# Background (optional image bg.png)
# =========================
def set_background(image_path="bg.png"):
    p = Path(image_path)
    if not p.exists():
        st.markdown("""
        <style>
          .stApp { background: radial-gradient(circle at 30% 20%, #0b1325 0%, #050a14 70%); }
        </style>
        """, unsafe_allow_html=True)
        return

    b64 = base64.b64encode(p.read_bytes()).decode("utf-8")
    st.markdown(f"""
    <style>
      .stApp {{
        background:
          linear-gradient(rgba(5,10,20,.92), rgba(5,10,20,.92)),
          url("data:image/png;base64,{b64}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
        background-position: center;
      }}
    </style>
    """, unsafe_allow_html=True)

set_background("bg.png")

# =========================
# CSS (clean)
# =========================
st.markdown("""
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}
.block-container {max-width: 980px; padding-top: 24px;}

/* Header */
.hero{
  text-align:center;
  margin: 20px 0 26px 0;
}
.hero .icon{
  font-size: 30px;
  margin-bottom: 10px;
  color: #ffffff;
}
.hero .title{
  font-size: 50px;
  font-weight: 900;
  color: #ffffff;   /* أبيض */
  margin: 0;
}

/* Remove any extra bars/rectangles */
.hero::before, .hero::after { display:none !important; }
hr { display:none !important; }

/* Input area container (no ugly rectangle) */
.input-wrap{
  margin: 0 auto;
  width: 100%;
}

/* Textarea styling */
div[data-testid="stTextArea"] > div{
  border: none !important;
  box-shadow: none !important;
}
textarea{
  background: #0f172a !important;
  color: #ffffff !important;
  border: 1px solid rgba(255,255,255,.18) !important;
  border-radius: 16px !important;
  padding: 14px !important;
  font-size: 14px !important;
}
textarea::placeholder{
  color: rgba(255,255,255,.45) !important;
}

/* Controls */
.small-note{
  color: rgba(255,255,255,.70);
  font-size: 12px;
}

/* Buttons */
.stButton>button{
  border-radius: 14px !important;
  font-weight: 800 !important;
  padding: 12px 14px !important;
  border: 0 !important;
}
.btn-primary > button{
  background: #ffffff !important;
  color: #0b1325 !important;
}
.btn-secondary > button{
  background: rgba(255,255,255,.12) !important;
  color: #ffffff !important;
  border: 1px solid rgba(255,255,255,.18) !important;
}

/* Metrics */
.metrics-row{
  display:grid;
  grid-template-columns:repeat(6,1fr);
  gap:10px;
  margin-top: 18px;
}
.metric-card{
  background: rgba(255,255,255,.06);
  border: 1px solid rgba(255,255,255,.12);
  border-radius: 16px;
  padding: 12px 10px;
  text-align: center;
}
.metric-label{
  color: rgba(255,255,255,.82);
  font-size: 12px;
  font-weight: 800;
}
.metric-value{
  color: #ffffff;
  font-size: 24px;
  font-weight: 900;
  margin-top: 6px;
}

/* Table styling on dark */
.table-wrap{
  margin-top: 14px;
  background: rgba(255,255,255,.06);
  border: 1px solid rgba(255,255,255,.12);
  border-radius: 16px;
  padding: 10px;
}
div[data-testid="stDataFrame"] *{
  color:#e5e7eb !important;
}

/* Link color */
a{
  color:#60a5fa !important;
  font-weight: 600;
  text-decoration: none;
}
a:hover{
  color:#93c5fd !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# Header UI
# =========================
st.markdown("""
<div class="hero">
  <div class="icon">🎵</div>
  <h1 class="title">TikTok</h1>
</div>
""", unsafe_allow_html=True)

# =========================
# TikTok logic
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
    return urlunparse(("https", p.netloc.lower(), p.path.rstrip("/"), "", "", ""))

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

    # Step 1: oEmbed (free)
    oembed_url = f"https://www.tiktok.com/oembed?url={profile_url}"
    r = safe_get(oembed_url, timeout=12)

    if r is None:
        return {"Username": clean, "Status": "Error", "Link": profile_url}

    if r.status_code == 200:
        return {"Username": clean, "Status": "Active", "Link": profile_url}

    if r.status_code == 404:
        return {"Username": clean, "Status": "Not Found", "Link": profile_url}

    if r.status_code in (403, 429):
        return {"Username": clean, "Status": "Blocked", "Link": profile_url}

    # Step 2: fallback page
    r2 = safe_get(profile_url, timeout=18)
    if r2 is None:
        return {"Username": clean, "Status": "Error", "Link": profile_url}

    text = (r2.text or "").lower()
    code = r2.status_code

    if code in (403, 429):
        return {"Username": clean, "Status": "Blocked", "Link": profile_url}

    not_found_signals = [
        "couldn't find this account",
        "couldn\u2019t find this account",
        '"statuscode":10202',
    ]
    banned_signals = [
        "this account was banned",
        "account banned",
        "permanently banned",
        "violated our community guidelines",
    ]

    if code == 404 or any(s in text for s in not_found_signals):
        return {"Username": clean, "Status": "Not Found", "Link": profile_url}

    if any(s in text for s in banned_signals):
        return {"Username": clean, "Status": "Banned", "Link": profile_url}

    if code == 200:
        return {"Username": clean, "Status": "Active", "Link": profile_url}

    return {"Username": clean, "Status": "Unknown", "Link": profile_url}

# =========================
# Input
# =========================
st.markdown('<div class="input-wrap">', unsafe_allow_html=True)

urls_input = st.text_area(
    "",
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
    st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
    run = st.button("🎵 فحص TikTok", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
with b2:
    st.markdown('<div class="btn-secondary">', unsafe_allow_html=True)
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
            results.append({"Username": "—", "Status": "Invalid", "Link": url})
        else:
            results.append(check_tiktok(username))

        prog.progress((i + 1) / len(links))
        if i < len(links) - 1 and delay > 0:
            time.sleep(float(delay))

    prog.empty()
    label.empty()

    df = pd.DataFrame(results)

    active = int((df["Status"] == "Active").sum())
    banned = int((df["Status"] == "Banned").sum())
    not_found = int((df["Status"] == "Not Found").sum())
    blocked = int((df["Status"] == "Blocked").sum())
    unknown = int((df["Status"] == "Unknown").sum())
    total = len(df)

    st.markdown(f"""
    <div class="metrics-row">
      <div class="metric-card"><div class="metric-label">✅ Active</div><div class="metric-value">{active}</div></div>
      <div class="metric-card"><div class="metric-label">🚫 Banned</div><div class="metric-value">{banned}</div></div>
      <div class="metric-card"><div class="metric-label">❌ Not Found</div><div class="metric-value">{not_found}</div></div>
      <div class="metric-card"><div class="metric-label">⚠️ Blocked</div><div class="metric-value">{blocked}</div></div>
      <div class="metric-card"><div class="metric-label">❓ Unknown</div><div class="metric-value">{unknown}</div></div>
      <div class="metric-card"><div class="metric-label">📦 Total</div><div class="metric-value">{total}</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="table-wrap">', unsafe_allow_html=True)
    show_df = df[["Username", "Status", "Link"]].copy()
    st.dataframe(show_df, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download CSV",
        data=csv_bytes,
        file_name="tiktok_results.csv",
        mime="text/csv",
        use_container_width=True
    )
