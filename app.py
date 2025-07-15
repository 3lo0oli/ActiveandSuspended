import os
import zipfile

# إعداد مجلد المشروع بعد إعادة التشغيل
project_dir = "/mnt/data/active_suspended_advanced"
os.makedirs(project_dir, exist_ok=True)

# كود app.py المتقدم لفحص عناصر محددة بدقة
app_py = """import streamlit as st
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Active / Suspended Checker", layout="centered")

st.title("🔍 تحقق من حالة الحساب")

platform_phrases = {
    "twitter": [
        "account suspended", "profile doesn’t exist"
    ],
    "reddit": [
        "this account has been suspended", "nobody on reddit", "page not found"
    ],
    "facebook": [
        "this content isn't available", "page isn't available"
    ],
    "instagram": [
        "sorry, this page isn't available"
    ],
    "youtube": [
        "this account has been terminated", "channel does not exist"
    ],
    "tiktok": [
        "couldn't find", "page not available", "account was banned"
    ]
}

def detect_platform_from_url(url):
    url = url.lower()
    if "twitter.com" in url:
        return "twitter"
    elif "reddit.com" in url:
        return "reddit"
    elif "facebook.com" in url:
        return "facebook"
    elif "instagram.com" in url:
        return "instagram"
    elif "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    elif "tiktok.com" in url:
        return "tiktok"
    return None

with st.form("check_form"):
    url = st.text_input("🔗 أدخل رابط الحساب:", placeholder="https://...")
    detected_platform = detect_platform_from_url(url)
    platform = st.selectbox("🌐 اختر المنصة (أو اترك المكتشفة):", list(platform_phrases.keys()), index=list(platform_phrases.keys()).index(detected_platform) if detected_platform else 0)
    submitted = st.form_submit_button("تحقق")

    if submitted:
        try:
            clean_url = url.split("?")[0]
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(clean_url, timeout=10, headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")

            # استخراج أجزاء محددة
            title = soup.title.string.lower() if soup.title else ""
            h1_texts = " ".join([h.get_text() for h in soup.find_all("h1")]).lower()
            meta_desc = ""
            meta_tag = soup.find("meta", attrs={"name": "description"})
            if meta_tag and meta_tag.get("content"):
                meta_desc = meta_tag["content"].lower()
            body_text = soup.body.get_text(separator=" ", strip=True).lower() if soup.body else ""

            full_text = " ".join([title, h1_texts, meta_desc, body_text])

            suspended_phrases = platform_phrases.get(platform, [])
            is_suspended = any(phrase.lower() in full_text for phrase in suspended_phrases)

            if is_suspended:
                st.error("🔴 الحساب موقوف (Suspended)")
            else:
                st.success("🟢 الحساب نشط (Active)")

        except Exception as e:
            st.warning(f"⚠️ حدث خطأ أثناء محاولة الوصول إلى الرابط: {e}")
"""

# requirements.txt
requirements = "streamlit\nrequests\nbeautifulsoup4\n"

# حفظ الملفات
with open(os.path.join(project_dir, "app.py"), "w", encoding="utf-8") as f:
    f.write(app_py)

with open(os.path.join(project_dir, "requirements.txt"), "w", encoding="utf-8") as f:
    f.write(requirements)

# ضغط الملفات
zip_path = "/mnt/data/active_suspended_advanced.zip"
with zipfile.ZipFile(zip_path, 'w') as zipf:
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, project_dir)
            zipf.write(file_path, arcname)

zip_path
