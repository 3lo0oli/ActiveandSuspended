import streamlit as st
import requests
from bs4 import BeautifulSoup

def check_reddit_account_status(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 404 or "nobody on Reddit goes by that name" in response.text:
            return "❌ الحساب غير موجود", "orange"
        
        soup = BeautifulSoup(response.text, "html.parser")

        if "this account has been suspended" in soup.text.lower():
            return "🔴 الحساب موقوف (Suspended)", "red"
        elif response.status_code == 200:
            return "🟢 الحساب نشط (Active)", "green"
        else:
            return "⚠️ لم يتم التأكد من الحالة بدقة", "gray"

    except Exception as e:
        return f"⚠️ حدث خطأ: {str(e)}", "gray"


st.set_page_config(page_title="تحقق من حالة الحساب", page_icon="🔍")
st.markdown("<h1 style='text-align: center;'>🔍 تحقق من حالة الحساب</h1>", unsafe_allow_html=True)

url = st.text_input("📎 أدخل رابط الحساب:", placeholder="https://www.reddit.com/user/username")
platform = st.selectbox("🌐 اختر المنصة:", ["reddit"])

if st.button("تحقق"):
    if url:
        with st.spinner("🔎 جاري التحقق..."):
            status, color = check_reddit_account_status(url)
            if color == "green":
                st.success(status)
            elif color == "red":
                st.error(status)
            else:
                st.warning(status)
    else:
        st.warning("⚠️ من فضلك أدخل رابط الحساب أولاً.")
