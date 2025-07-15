import streamlit as st
import requests

st.set_page_config(page_title="Active / Suspended Checker", layout="centered")

st.markdown("""
    <style>
    body {
        font-family: Arial;
        background: #f9f9f9;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🔍 تحقق من حالة الحساب")

with st.form("check_form"):
    url = st.text_input("🔗 أدخل رابط الحساب:", placeholder="https://...")
    platform = st.selectbox("🌐 اختر المنصة:", ["twitter", "reddit", "facebook", "instagram", "youtube", "tiktok"])
    submitted = st.form_submit_button("تحقق")

    if submitted:
        try:
            response = requests.get(url, timeout=10)
            content = response.text.lower()

            if platform == "twitter":
                if "account suspended" in content:
                    st.error("🔴 الحساب موقوف (Suspended)")
                else:
                    st.success("🟢 الحساب نشط (Active)")

            elif platform == "reddit":
                if "nobody on reddit goes by that name" in content or "page not found" in content:
                    st.error("🔴 الحساب موقوف (Suspended)")
                else:
                    st.success("🟢 الحساب نشط (Active)")

            elif platform == "facebook":
                if "this content isn't available" in content or "page isn't available" in content:
                    st.error("🔴 الحساب موقوف أو غير موجود")
                else:
                    st.success("🟢 الحساب نشط (Active)")

            elif platform == "instagram":
                if "sorry, this page isn't available" in content:
                    st.error("🔴 الحساب موقوف أو غير موجود")
                else:
                    st.success("🟢 الحساب نشط (Active)")

            elif platform == "youtube":
                if "this account has been terminated" in content or "channel does not exist" in content:
                    st.error("🔴 القناة موقوفة أو غير موجودة")
                else:
                    st.success("🟢 القناة نشطة (Active)")

            elif platform == "tiktok":
                if "couldn't find this account" in content or "page not available" in content:
                    st.error("🔴 الحساب موقوف أو غير موجود")
                else:
                    st.success("🟢 الحساب نشط (Active)")

            else:
                st.warning("⚠️ منصة غير مدعومة حاليًا")

        except Exception as e:
            st.warning(f"⚠️ حدث خطأ أثناء محاولة الوصول إلى الرابط: {e}")
