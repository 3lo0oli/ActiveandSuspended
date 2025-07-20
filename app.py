import streamlit as st
import httpx
from bs4 import BeautifulSoup

st.set_page_config(page_title="فحص حسابات Reddit", page_icon="🔍")
st.title("🔎 أداة فحص حالة حسابات Reddit")
st.markdown("تحقق هل الحساب نشط أم موقوف على Reddit بدون متصفح، عبر تحليل المحتوى مباشرة.")

user_input = st.text_area("✏️ أدخل روابط حسابات Reddit (رابط في كل سطر):")

# فحص الرابط باستخدام httpx و BeautifulSoup
def check_reddit_status_httpx(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        response = httpx.get(url, headers=headers, timeout=10)
        if response.status_code == 404:
            return "❌ غير موجود"
        html = response.text.lower()
        if "this account has been suspended" in html:
            return "🚫 موقوف"
        elif "sorry, nobody on reddit goes by that name" in html:
            return "❌ غير موجود"
        else:
            return "✅ نشط"
    except httpx.RequestError:
        return "⚠️ خطأ في الاتصال"
    except Exception as e:
        return f"⚠️ خطأ: {str(e)}"

if st.button("تحقق الآن"):
    if user_input.strip():
        links = [line.strip() for line in user_input.strip().splitlines() if line.strip()]
        st.subheader("📊 النتائج:")
        with st.spinner("جارٍ التحقق من الحسابات..."):
            for url in links:
                if not url.startswith("https://www.reddit.com/user/"):
                    st.warning(f"الرابط غير صحيح: {url}")
                    continue
                status = check_reddit_status_httpx(url)
                st.write(f"🔗 [{url}]({url}) → {status}")
    else:
        st.warning("يرجى إدخال روابط أولًا.")
