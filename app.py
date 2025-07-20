import streamlit as st
import httpx
from bs4 import BeautifulSoup

# إعداد الصفحة
st.set_page_config(page_title="فحص حسابات Reddit", page_icon="🔍")
st.title("🔎 أداة فحص حالة حسابات Reddit")
st.markdown("تحقق هل الحساب نشط أم موقوف على Reddit بدون متصفح، عبر تحليل النسخة القديمة من الموقع مباشرة.")

# إدخال الروابط
user_input = st.text_area("✏️ أدخل روابط حسابات Reddit (رابط في كل سطر):")

# الدالة التي تتحقق من حالة الحساب
def check_reddit_status_httpx(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    # التحويل إلى نسخة Reddit القديمة
    url = url.replace("https://www.reddit.com", "https://old.reddit.com")

    try:
        response = httpx.get(url, headers=headers, timeout=10)
        if response.status_code == 404:
            return "❌ غير موجود"

        html = response.text.lower()

        # تحليل النص
        if "this account has been suspended" in html:
            return "🚫 موقوف"
        elif "nobody on reddit goes by that name" in html:
            return "❌ غير موجود"
        else:
            return "✅ نشط"
    except httpx.RequestError:
        return "⚠️ خطأ في الاتصال"
    except Exception as e:
        return f"⚠️ خطأ: {str(e)}"

# عند الضغط على الزر
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
