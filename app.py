import streamlit as st
import httpx

# إعداد واجهة المستخدم
st.set_page_config(page_title="أداة التحقق من الحسابات", page_icon="🔍")
st.title("🔎 أداة التحقق من حالة الحسابات")
st.markdown("تحقق من حالة الروابط التالية: Reddit، Twitter، Facebook، Instagram، TikTok، Telegram، YouTube")

# استقبال روابط من المستخدم
urls = st.text_area("أدخل الروابط (رابط في كل سطر):")

def check_status(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = httpx.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return "✅ نشط"
        elif response.status_code in [404, 410]:
            return "❌ غير موجود أو محذوف"
        elif response.status_code in [401, 403]:
            return "⚠️ موقوف أو خاص"
        else:
            return f"❓ غير معروف (HTTP {response.status_code})"
    except Exception as e:
        return f"❌ خطأ: {e}"

# عند الضغط على زر التحقق
if st.button("تحقق الآن"):
    if urls.strip():
        st.write("### النتائج:")
        for line in urls.strip().splitlines():
            status = check_status(line.strip())
            st.write(f"🔗 {line.strip()} → {status}")
    else:
        st.warning("يرجى إدخال الروابط أولاً.")
