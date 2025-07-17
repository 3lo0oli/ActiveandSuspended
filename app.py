import streamlit as st
import httpx
from bs4 import BeautifulSoup

st.set_page_config(page_title="أداة التحقق من حالة الحسابات", page_icon="🔍")
st.title("🔎 أداة التحقق من حالة الحسابات")
st.markdown("تحقق من حالة الروابط التالية: **Reddit, Twitter, Facebook, Instagram, TikTok, Telegram, YouTube**")

urls = st.text_area("✏️ أدخل الروابط (رابط في كل سطر):")

# دالة عامة لتحليل الرد
def check_status(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = httpx.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.get_text().lower()

            # تحليل خاص لكل موقع
            if "reddit.com" in url:
                if "this account has been suspended" in page_text:
                    return "🚫 موقوف (Reddit)"
                elif "sorry, nobody on reddit goes by that name" in page_text:
                    return "❌ غير موجود (Reddit)"
                else:
                    return "✅ نشط (Reddit)"

            elif "twitter.com" in url:
                if "account suspended" in page_text:
                    return "🚫 موقوف (Twitter)"
                elif "this account doesn’t exist" in page_text:
                    return "❌ غير موجود (Twitter)"
                else:
                    return "✅ نشط (Twitter)"

            elif "facebook.com" in url:
                if "content isn't available" in page_text or "page isn't available" in page_text:
                    return "❌ غير موجود أو محذوف (Facebook)"
                else:
                    return "✅ نشط (Facebook)"

            elif "instagram.com" in url:
                if "sorry, this page isn't available" in page_text:
                    return "❌ غير موجود أو محذوف (Instagram)"
                else:
                    return "✅ نشط (Instagram)"

            elif "tiktok.com" in url:
                if "couldn't find this account" in page_text or "page isn't available" in page_text:
                    return "❌ غير موجود أو محذوف (TikTok)"
                elif "this account is private" in page_text:
                    return "⚠️ خاص (TikTok)"
                else:
                    return "✅ نشط (TikTok)"

            elif "t.me" in url or "telegram.me" in url:
                if "this channel can't be displayed" in page_text or "not found" in page_text:
                    return "❌ غير موجود أو محذوف (Telegram)"
                else:
                    return "✅ نشط (Telegram)"

            elif "youtube.com" in url:
                if "this channel does not exist" in page_text or "has been terminated" in page_text:
                    return "❌ غير موجود أو موقوف (YouTube)"
                else:
                    return "✅ نشط (YouTube)"

            else:
                return f"✅ نشط (غير معروف بدقة)"

        elif response.status_code in [404, 410]:
            return "❌ غير موجود أو محذوف"
        elif response.status_code in [401, 403]:
            return "⚠️ ربما موقوف أو خاص"
        else:
            return f"❓ غير معروف (HTTP {response.status_code})"

    except Exception as e:
        return f"❌ خطأ في التحقق: {e}"

# عند الضغط على الزر
if st.button("تحقق الآن"):
    if urls.strip():
        st.write("## النتائج:")
        for line in urls.strip().splitlines():
            url = line.strip()
            if url:
                status = check_status(url)
                st.write(f"🔗 [{url}]({url}) → {status}")
    else:
        st.warning("يرجى إدخال الروابط أولًا.")
