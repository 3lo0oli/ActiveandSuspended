import streamlit as st
import httpx
import re

def check_reddit_status(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = httpx.get(url, headers=headers, timeout=10)

        if response.status_code == 404:
            return "❌ الحساب غير موجود", "orange"

        # نتحقق إذا الصفحة فيها رسالة suspension
        if re.search(r"(?i)this account has been suspended", response.text):
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
