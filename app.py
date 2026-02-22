import streamlit as st
import httpx
import re
import time
import random
from urllib.parse import urlparse, urlunparse
import pandas as pd
import base64
from pathlib import Path

st.set_page_config(page_title="TikTok Status Checker", page_icon="🎵", layout="wide")

# =========================
# Background
# =========================
def set_bg(image_path="bg.png"):
    p = Path(image_path)
    if not p.exists():
        st.markdown("""
        <style>
        .stApp { background: radial-gradient(circle at 20% 10%, #0b1220 0%, #050a14 100%); }
        </style>
        """, unsafe_allow_html=True)
        return

    b64 = base64.b64encode(p.read_bytes()).decode()
    st.markdown(f"""
    <style>
    .stApp {{
        background:
        linear-gradient(rgba(5,10,20,.94), rgba(5,10,20,.94)),
        url("data:image/png;base64,{b64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    </style>
    """, unsafe_allow_html=True)

set_bg()

# =========================
# CSS
# =========================
st.markdown("""
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}
.block-container {max-width: 950px;}

.hero{
  text-align:center;
  margin-bottom:20px;
}

.big-title{
  font-size:48px;
  font-weight:900;
  color:#f8fafc;
  text-shadow:0 0 20px rgba(255,255,255,.25);
  margin:0;
}

.section{
  background:rgba(255,255,255,.05);
  border:1px solid rgba(255,255,255,.12);
  border-radius:16px;
  padding:16px;
  backdrop-filter: blur(8px);
}

/* remove textarea border */
textarea, div[data-testid="stTextArea"] > div{
  border:none !important;
  outline:none !important;
  box-shadow:none !important;
  background:rgba(255,255,255,.08) !important;
  color:#ffffff !important;
}

/* buttons */
.stButton>button{
  border-radius:12px !important;
  font-weight:800 !important;
  padding:10px 14px !important;
  border:none !important;
}

.primary-btn>button{
  background:#2563eb !important;
  color:#fff !important;
}

.secondary-btn>button{
  background:rgba(255,255,255,.12) !important;
  color:#fff !important;
}

/* metrics */
.metrics-row{
  display:grid;
  grid-template-columns:repeat(6,1fr);
  gap:10px;
  margin-top:15px;
}

.metric-card{
  background:rgba(255,255,255,.06);
  border:1px solid rgba(255,255,255,.12);
  border-radius:14px;
  padding:10px;
  text-align:center;
}

.metric-label{
  color:#cbd5e1;
  font-size:12px;
  font-weight:800;
}

.metric-value{
  color:#ffffff;
  font-size:22px;
  font-weight:900;
}

/* dataframe */
div[data-testid="stDataFrame"] *{
  color:#e5e7eb !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# Header
# =========================
st.markdown("""
<div class="hero">
  <div style="font-size:30px;">🎵</div>
  <h1 class="big-title">TikTok</h1>
</div>
""", unsafe_allow_html=True)

# =========================
# TikTok Logic
# =========================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)",
]

def headers():
    return {"User-Agent": random.choice(USER_AGENTS)}

def normalize(url):
    url=url.strip()
    if not url.startswith("http"):
        url="https://"+url
    p=urlparse(url)
    return urlunparse(("https",p.netloc,p.path.rstrip("/"),"","",""))

def extract_username(url):
    m=re.search(r"tiktok\.com/@([^/?#]+)",url)
    return m.group(1) if m else None

def safe_get(url):
    try:
        with httpx.Client(timeout=15,follow_redirects=True) as c:
            return c.get(url,headers=headers())
    except:
        return None

def check(username):
    url=f"https://www.tiktok.com/@{username}"
    r=safe_get(f"https://www.tiktok.com/oembed?url={url}")

    if r and r.status_code==200:
        return {"Username":username,"Status":"Active","Link":url}
    if r and r.status_code==404:
        return {"Username":username,"Status":"Not Found","Link":url}

    r2=safe_get(url)
    if not r2:
        return {"Username":username,"Status":"Error","Link":url}

    text=r2.text.lower()

    if "banned" in text:
        return {"Username":username,"Status":"Banned","Link":url}
    if "couldn't find this account" in text:
        return {"Username":username,"Status":"Not Found","Link":url}
    if r2.status_code==200:
        return {"Username":username,"Status":"Active","Link":url}

    return {"Username":username,"Status":"Unknown","Link":url}

# =========================
# Input Section
# =========================
st.markdown('<div class="section">', unsafe_allow_html=True)

urls_input=st.text_area("",height=140,placeholder="ضع روابط TikTok هنا (كل رابط في سطر)")

col1,col2=st.columns(2)
with col1:
    run=st.button("🎵 فحص TikTok",use_container_width=True)
with col2:
    clear=st.button("🧹 مسح",use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

if clear:
    st.rerun()

# =========================
# Results
# =========================
if run:
    raw=[u.strip() for u in urls_input.splitlines() if u.strip()]
    if not raw:
        st.warning("حط لينك واحد على الأقل.")
        st.stop()

    results=[]
    for u in raw:
        u=normalize(u)
        username=extract_username(u)
        if not username:
            results.append({"Username":"—","Status":"Invalid","Link":u})
        else:
            results.append(check(username))

    df=pd.DataFrame(results)

    active=(df["Status"]=="Active").sum()
    banned=(df["Status"]=="Banned").sum()
    not_found=(df["Status"]=="Not Found").sum()
    unknown=(df["Status"]=="Unknown").sum()
    total=len(df)

    st.markdown('<div class="section">', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="metrics-row">
      <div class="metric-card"><div class="metric-label">✅ Active</div><div class="metric-value">{active}</div></div>
      <div class="metric-card"><div class="metric-label">🚫 Banned</div><div class="metric-value">{banned}</div></div>
      <div class="metric-card"><div class="metric-label">❌ Not Found</div><div class="metric-value">{not_found}</div></div>
      <div class="metric-card"><div class="metric-label">❓ Unknown</div><div class="metric-value">{unknown}</div></div>
      <div class="metric-card"><div class="metric-label">📦 Total</div><div class="metric-value">{total}</div></div>
    </div>
    """,unsafe_allow_html=True)

    st.dataframe(df[["Username","Status","Link"]],use_container_width=True,hide_index=True)

    st.download_button(
        "⬇️ Download CSV",
        df.to_csv(index=False).encode(),
        "tiktok_results.csv",
        "text/csv",
        use_container_width=True
    )

    st.markdown('</div>', unsafe_allow_html=True)
