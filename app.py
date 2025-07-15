import os
import zipfile

# إعداد مجلد المشروع
project_dir = "/mnt/data/active_suspended_final"
os.makedirs(project_dir, exist_ok=True)

# كود app.py بعد التحسين
app_py = """import streamlit as st
import requests

st.set_page_config(page_title="Active / Suspended Checker", layout="centered")

st.markdown(\"\"\"
    <style>
    body {
        font-family: Arial;
        background: #f9f9f9;
        text-align: center;
    }
    </style>
\"\"\", unsafe_allow_html=True)

st.title("🔍 تحقق من حالة الحساب")

with st.form("check_form"):
    url = st.text_input("🔗 أدخل رابط الحساب:", placeholder="https://...")
    platform = st.selectbox("🌐 اختر المنصة:", ["twitter", "reddit", "facebook", "instagram", "youtube", "tiktok"])
    submitted = st.form_submit_button("تحقق")

    if submitted:
        try:
            clean_url = url.split("?")[0]  # إزالة تتبع الروابط
            response = requests.get(clean_url, timeout=10)
            content = response.text.lower()

            if platform == "twitter":
                is_suspended = "account suspended" in content

            elif platform == "reddit":
                is_suspended = "this account has been suspended" in content

            elif platform == "facebook":
                is_suspended = "this content isn't available" in content or "page isn't available" in content

            elif platform == "instagram":
                is_suspended = "sorry, this page isn't available" in content

            elif platform == "youtube":
                is_suspended = "this account has been terminated" in content or "channel does not exist" in content

            elif platform == "tiktok":
                is_suspended = "couldn't find this account" in content or "page not available" in content

            else:
                is_suspended = True  # غير معروفة = نعتبرها موقوفة

            if is_suspended:
                st.error("🔴 الحساب موقوف (Suspended)")
            else:
                st.success("🟢 الحساب نشط (Active)")

        except Exception as e:
            st.warning(f"⚠️ حدث خطأ أثناء محاولة الوصول إلى الرابط: {e}")
"""

# requirements.txt
requirements = "streamlit\nrequests\n"

# حفظ الملفات
with open(os.path.join(project_dir, "app.py"), "w", encoding="utf-8") as f:
    f.write(app_py)

with open(os.path.join(project_dir, "requirements.txt"), "w", encoding="utf-8") as f:
    f.write(requirements)

# ضغط الملفات
zip_path = "/mnt/data/active_suspended_final.zip"
with zipfile.ZipFile(zip_path, 'w') as zipf:
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, project_dir)
            zipf.write(file_path, arcname)

zip_path
