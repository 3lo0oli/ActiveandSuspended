import streamlit as st
import httpx
from bs4 import BeautifulSoup

# إعداد واجهة المستخدم مع خلفية داكنة
st.set_page_config(page_title="فحص حسابات Reddit", page_icon="🔍", layout="wide")
st.title("🔎 أداة فحص حالة حسابات Reddit")
st.markdown("""
تحقق من حالة حسابات Reddit (نشط/موقوف/غير موجود) باستخدام النسخة القديمة من الموقع.
""")

# أسلوب CSS مخصص للواجهة الداكنة والروابط السوداء
st.markdown("""
<style>
    /* الخلفية العامة */
    .stApp {
        background-color: #1E1E1E;
        color: #FFFFFF;
    }
    
    /* منطقة إدخال النص */
    .stTextArea textarea {
        min-height: 150px;
        background-color: #2D2D2D;
        color: #FFFFFF;
        border: 1px solid #444;
    }
    
    /* شريط التقدم */
    .stProgress > div > div > div {
        background-color: #FF4B4B;
    }
    
    /* الروابط */
    a {
        color: #000000 !important;  /* روابط سوداء */
        text-decoration: underline;
    }
    
    /* الأزرار */
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 24px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 4px;
    }
    
    /* البطاقات */
    .stAlert {
        background-color: #2D2D2D;
        border-left: 4px solid #4CAF50;
    }
    
    /* العناوين */
    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)

# دوال المعالجة
def normalize_url(url):
    """معالجة الروابط المدخلة لتكون بصيغة صحيحة"""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        if not url.startswith("u/"):
            url = "u/" + url
        url = "https://www.reddit.com/" + url
    return url.replace("www.reddit.com", "old.reddit.com").rstrip("/")

def check_reddit_status_httpx(url):
    """فحص حالة الحساب باستخدام HTTPX"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = httpx.get(url, headers=headers, timeout=15, follow_redirects=True)
        html = response.text.lower()
        
        if "this account has been suspended" in html:
            return "🚫 موقوف"
        elif "nobody on reddit goes by that name" in html or response.status_code == 404:
            return "❌ غير موجود"
        else:
            return "✅ نشط"
    except httpx.RequestError:
        return "⚠️ خطأ في الاتصال"
    except Exception as e:
        return f"⚠️ خطأ: {str(e)}"

# واجهة الإدخال
with st.expander("🎯 كيفية الاستخدام", expanded=True):
    st.markdown("""
    - أدخل أسماء المستخدمين أو الروابط (سطر لكل حساب)
    - أمثلة:
        ```
        u/username
        https://www.reddit.com/user/username
        username
        ```
    """)

user_input = st.text_area(
    "✏️ أدخل أسماء المستخدمين أو الروابط:",
    placeholder="أدخل هنا...\nمثال:\nu/username\nhttps://www.reddit.com/user/username",
    help="يمكنك إدخال قائمة بعدة حسابات (سطر لكل حساب)"
)

# معالجة النتائج
if st.button("🔍 تحقق الآن", type="primary"):
    if user_input.strip():
        links = [line.strip() for line in user_input.strip().splitlines() if line.strip()]
        results = []
        stats = {"✅ نشط": 0, "🚫 موقوف": 0, "❌ غير موجود": 0, "⚠️ أخطاء": 0}
        
        with st.spinner("جارٍ التحقق من الحسابات..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, url in enumerate(links):
                try:
                    normalized_url = normalize_url(url)
                    status = check_reddit_status_httpx(normalized_url)
                    results.append((normalized_url, status))
                    stats[status.split()[0]] += 1
                    
                    progress = (i + 1) / len(links)
                    progress_bar.progress(progress)
                    status_text.text(f"جارٍ معالجة {i+1}/{len(links)} - {url[:30]}...")
                except Exception as e:
                    results.append((url, f"⚠️ خطأ: {str(e)}"))
                    stats["⚠️ أخطاء"] += 1
        
        st.success("✅ تم الانتهاء من التحقق!")
        
        # عرض الإحصائيات
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("الحسابات النشطة", stats["✅ نشط"])
        col2.metric("الحسابات الموقوفة", stats["🚫 موقوف"])
        col3.metric("الحسابات غير الموجودة", stats["❌ غير موجود"])
        col4.metric("الأخطاء", stats["⚠️ أخطاء"])
        
        # عرض النتائج التفصيلية
        st.subheader("📊 النتائج التفصيلية:")
        for url, status in results:
            st.markdown(f"- **{status}**: [{url}]({url})", unsafe_allow_html=True)
        
        # زر نسخ النتائج
        result_text = "\n".join([f"{status}: {url}" for url, status in results])
        st.download_button(
            label="📋 نسخ النتائج",
            data=result_text,
            file_name="reddit_status_results.txt",
            mime="text/plain"
        )
    else:
        st.warning("⚠️ يرجى إدخال روابط أو أسماء مستخدمين أولاً")

# تذييل الصفحة
st.markdown("---")
st.markdown("""
**ملاحظات:**
- يعمل التطبيق عن طريق تحليل النسخة القديمة من Reddit (old.reddit.com)
- الروابط تظهر باللون الأسود للوضوح
- الخلفية الداكنة لتجربة مستخدم أفضل
""")
