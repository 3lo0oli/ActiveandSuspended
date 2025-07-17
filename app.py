import streamlit as st
import httpx
from bs4 import BeautifulSoup

# إعداد الصفحة
st.set_page_config(page_title="أداة التحقق من الحسابات", page_icon="🔍")
st.title("🔍 أداة التحقق من حالة الحسابات")
st.markdown("تحقق من حالة الروابط التالية: Reddit, Twitter, Instagram, TikTok, Facebook, Telegram, YouTube")

urls = st.text_area("✏️ أدخل الروابط (رابط في كل سطر):")

# دالة تحليل ذكي لحالة الرابط
def smart_check(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = httpx.get(url, headers=headers, timeout=10)
        html = r.text.lower()
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator=' ', strip=True)

        # تحليل حسب المنصة
        if "reddit.com" in url:
            if "this account has been suspended" in text:
                return "🚫 موقوف (Reddit)"
            elif "sorry, nobody on reddit goes by that name" in text:
                return "❌ غير موجود (Reddit)"
            else:
                return "✅ نشط (Reddit)"

        elif "twitter.com" in url:
            if "account suspended" in text:
                return "🚫 موقوف (Twitter)"
            elif "doesn’t exist" in text or "this account doesn’t exist" in text:
                return "❌ غير موجود (Twitter)"
            else:
                return "✅ نشط (Twitter)"

        elif "instagram.com" in url:
            if "sorry, this page isn't available" in text:
                return "❌ غير موجود (Instagram)"
            elif "private" in text:
                return "⚠️ خاص (Instagram)"
            else:
                return "✅ نشط (Instagram)"

        elif "facebook.com" in url:
            if "this content isn't available" in text or "page isn't available" in text:
                return "❌ غير موجود (Facebook)"
            else:
                return "✅ نشط (Facebook)"

        elif "tiktok.com" in url:
            if "couldn’t find this account" in text or "page isn't available" in text:
                return "❌ غير موجود (TikTok)"
            elif "this account is private" in text:
                return "⚠️ خاص (TikTok)"
            else:
                return "✅ نشط (TikTok)"

        elif "t.me" in url or "telegram.me" in url:
            if "channel can't be displayed" in text or "not found" in text:
                return "❌ غير موجود (Telegram)"
            else:
                return "✅ نشط (Telegram)"

        elif "youtube.com" in url:
            if "has been terminated" in text or "channel does not exist" in text:
                return "❌ غير موجود (YouTube)"
            else:
                return "✅ نشط (YouTube)"

        else:
            return f"✅ نشط (منصة غير معروفة)"

    except Exception as e:
        return f"❌ خطأ في الاتصال: {e}"

# واجهة النتائج
if st.button("تحقق الآن"):
    if urls.strip():
        st.subheader("🔎 النتائج:")
        for url in urls.strip().splitlines():
            if url.strip():
                result = smart_check(url.strip())
                st.write(f"🔗 [{url.strip()}]({url.strip()}) → {result}")
    else:
        st.warning("يرجى إدخال روابط أولًا.")
