import streamlit as st
import httpx
import re

def check_reddit_status(username_or_url):
    try:
        # استخراج اسم المستخدم من الرابط إذا تم إدخال رابط
        if "reddit.com" in username_or_url:
            username = username_or_url.split("/user/")[-1].strip("/")
        else:
            username = username_or_url.strip("/")
        
        if not username:
            return "❌ لم يتم تقديم اسم مستخدم صحيح", "gray"
        
        url = f"https://www.reddit.com/user/{username}/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = httpx.get(url, headers=headers, timeout=10, follow_redirects=True)
        html = response.text.lower()

        # التحقق من الحساب غير موجود
        if response.status_code == 404 or "page not found" in html or "sorry, nobody on reddit goes by that name" in html:
            return "❌ الحساب غير موجود (404)", "orange"

        # التحقق من الحساب الموقوف
        if ("this account has been suspended" in html or 
            "content unavailable" in html or 
            re.search(r"<title>\s*user.*suspended\s*</title>", html) or
            "account suspended" in html):
            return "🔴 الحساب موقوف (Suspended)", "red"

        # التحقق من الحساب المحذوف
        if ("this account has been deleted" in html or 
            "user deleted" in html):
            return "⚫ الحساب محذوف (Deleted)", "black"

        # التحقق من الحساب النشط
        if response.status_code == 200 and ("user" in html or "u/" in html):
            return "🟢 الحساب نشط (Active)", "green"

        return "⚠️ لم يتم التأكد من الحالة بدقة", "gray"

    except httpx.TimeoutException:
        return "⚠️ انتهت مهلة الطلب (Timeout)", "gray"
    except httpx.RequestError as e:
        return f"⚠️ خطأ في الاتصال: {str(e)}", "gray"
    except Exception as e:
        return f"⚠️ حدث خطأ غير متوقع: {str(e)}", "gray"

# واجهة Streamlit
st.set_page_config(page_title="تحقق من حالة الحساب", page_icon="🔍", layout="wide")
st.markdown("<h1 style='text-align: center;'>🔍 تحقق من حالة الحساب</h1>", unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])
with col1:
    user_input = st.text_input("📎 أدخل رابط الحساب أو اسم المستخدم:", placeholder="https://www.reddit.com/user/username أو username")
with col2:
    platform = st.selectbox("🌐 اختر المنصة:", ["reddit"])

if st.button("تحقق", type="primary"):
    if user_input:
        with st.spinner("🔎 جاري التحقق..."):
            status, color = check_reddit_status(user_input)
            
            # عرض النتيجة مع تنسيق مناسب
            result_container = st.container()
            if color == "green":
                result_container.success(f"## {status}")
            elif color == "red":
                result_container.error(f"## {status}")
            elif color == "orange":
                result_container.warning(f"## {status}")
            elif color == "black":
                result_container.markdown(f"## {status}", unsafe_allow_html=True)
            else:
                result_container.info(f"## {status}")
            
            # عرض رابط الحساب
            if "reddit.com" in user_input:
                account_url = user_input
            else:
                account_url = f"https://www.reddit.com/user/{user_input}/"
            
            st.markdown(f"🔗 [رابط الحساب على Reddit]({account_url})", unsafe_allow_html=True)
    else:
        st.warning("⚠️ من فضلك أدخل رابط الحساب أو اسم المستخدم أولاً.")

# تذييل الصفحة
st.markdown("---")
st.markdown("""
<style>
.footer {
    font-size: 0.8em;
    text-align: center;
    color: #666;
}
</style>
<div class="footer">
    تم التطوير باستخدام Streamlit و Python | يمكنك إضافة منصات أخرى في المستقبل
</div>
""", unsafe_allow_html=True)
