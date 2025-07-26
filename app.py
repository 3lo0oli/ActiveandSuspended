import streamlit as st
import httpx
from bs4 import BeautifulSoup

# إعداد واجهة المستخدم
st.set_page_config(page_title="فحص حالة حساب Reddit", page_icon="🔍", layout="centered")
st.title("🔎 فحص حالة حساب Reddit")
st.markdown("أدخل رابط حساب Reddit للتحقق من حالته (نشط/موقوف)")

# دوال المعالجة
def normalize_url(url):
    """معالجة الروابط المدخلة لتكون بصيغة صحيحة"""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        if not url.startswith("u/") and not url.startswith("user/"):
            url = "user/" + url
        url = "https://www.reddit.com/" + url
    return url.rstrip("/")

def check_reddit_status(url):
    """فحص حالة الحساب باستخدام HTTPX"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = httpx.get(url, headers=headers, timeout=10, follow_redirects=True)
        
        # التحقق من حالة الحساب
        if response.status_code == 404:
            return "❌ غير موجود"
        elif "suspended" in response.text.lower():
            return "🚫 موقوف"
        else:
            return "✅ نشط"
    except httpx.RequestError:
        return "⚠️ خطأ في الاتصال"
    except Exception as e:
        return f"⚠️ خطأ: {str(e)}"

# واجهة الإدخال
user_input = st.text_input(
    "أدخل رابط حساب Reddit:",
    placeholder="مثال: u/username أو https://www.reddit.com/user/username",
    help="يمكنك إدخال رابط الحساب بأي صيغة"
)

if st.button("🔍 تحقق الآن"):
    if user_input.strip():
        normalized_url = normalize_url(user_input)
        
        with st.spinner("جارٍ التحقق..."):
            status = check_reddit_status(normalized_url)
            
            # عرض النتيجة
            st.subheader("النتيجة:")
            if status == "✅ نشط":
                st.success(f"{status} - الحساب نشط")
                st.markdown(f"[رابط الحساب]({normalized_url})")
            elif status == "🚫 موقوف":
                st.error(f"{status} - الحساب موقوف")
            elif status == "❌ غير موجود":
                st.warning(f"{status} - الحساب غير موجود")
            else:
                st.error(status)
    else:
        st.warning("يرجى إدخال رابط الحساب أولاً")

# تذييل الصفحة
st.markdown("---")
st.markdown("""
**ملاحظات:**
- الأداة تتحقق من حالة حساب Reddit فقط (نشط/موقوف/غير موجود)
- لا يتم حفظ أي بيانات أو معلومات
""")
