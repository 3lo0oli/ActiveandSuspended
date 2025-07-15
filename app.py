import streamlit as st
import httpx
import re

def check_reddit_status(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = httpx.get(url, headers=headers, timeout=10)
        html = response.text.lower()

        if response.status_code == 404 or "page not found" in html:
            return "❌ الحساب غير موجود (404)", "orange"

        # التحقق من الحساب الموقوف
        if "this account has been suspended" in html or \
           "content unavailable" in html or \
           "sorry, nobody on reddit goes by that name" in html or \
           re.search(r"<title>\s*user.*suspended\s*</title>", html):
            return "🔴 الحساب موقوف (Suspended)", "red"

        if response.status_code == 200:
            return "🟢 الحساب نشط (Active)", "green"

        return "⚠️ لم يتم التأكد من الحالة بدقة", "gray"

    except Exception as e:
        return f"⚠️ حدث خطأ: {str(e)}", "gray"

# واجهة Streamlit
st.set_page_config(page_title="تحقق من حالة الحساب", page_icon="🔍")
st.markdown("<h1 style='text-align: center;'>🔍 تحقق من حالة الحساب</h1>", unsafe_allow_html=True)

url = st.text_input("📎 أدخل رابط الحساب:", placeholder="https://www.reddit.com/user/username")
platform = st.selectbox("🌐 اختر المنصة:", ["reddit"])

if st.button("تحقق"):
    if url and platform == "reddit":
        with st.spinner("🔎 جاري التحقق..."):
            status, color = check_reddit_status(url)
            if color == "green":
                st.success(status)
            elif color == "red":
                st.error(status)
            elif color == "orange":
                st.warning(status)
            else:
                st.info(status)
    else:
        st.warning("⚠️ من فضلك أدخل رابط الحساب أولاً.")
