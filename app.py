import streamlit as st
from playwright.sync_api import sync_playwright
import re
import time
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="Social Media Status Checker Pro", page_icon="🔍", layout="wide")

st.title("🔍 فحص حالة حسابات السوشيال ميديا (Pro)")
st.markdown("""
<div style='background-color:#e6f2ff;padding:15px;border-radius:10px;margin-bottom:20px'>
فحص دقيق جداً باستخدام Playwright - يعمل مثل المتصفح الحقيقي
</div>
""", unsafe_allow_html=True)

# نفس دوال detect_platform و extract_username من الكود السابق
# ... (انسخها من فوق)

def check_with_playwright(url, platform, username):
    """فحص باستخدام Playwright (headless browser)"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        
        try:
            # بناء الـ URL حسب المنصة
            if platform == 'twitter':
                target_url = f"https://twitter.com/{username}"
            elif platform == 'facebook':
                target_url = f"https://facebook.com/{username}"
            elif platform == 'instagram':
                target_url = f"https://instagram.com/{username}/"
            elif platform == 'tiktok':
                target_url = f"https://tiktok.com/@{username}"
            elif platform == 'youtube':
                target_url = f"https://youtube.com/@{username}"
            else:
                return "❓ منصة غير مدعومة", url
            
            # فتح الصفحة
            response = page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(2)  # انتظر تحميل JavaScript
            
            # فحص الحالة حسب المنصة
            if platform == 'twitter':
                if page.locator("text=Account suspended").count() > 0:
                    return "🚫 موقوف", target_url
                elif page.locator("text=doesn't exist").count() > 0:
                    return "❌ غير موجود", target_url
                elif page.locator("[data-testid='primaryColumn']").count() > 0:
                    return "✅ نشط", target_url
                    
            elif platform == 'instagram':
                if "Page Not Found" in page.title():
                    return "❌ غير موجود", target_url
                elif page.locator("text=followers").count() > 0 or page.locator("text=posts").count() > 0:
                    return "✅ نشط", target_url
                    
            elif platform == 'facebook':
                if "Page Not Found" in page.content():
                    return "❌ غير موجود", target_url
                elif "Content Not Found" in page.content():
                    return "🚫 معلق/محذوف", target_url
                elif response.status == 200:
                    return "✅ نشط", target_url
                    
            elif platform == 'tiktok':
                if "Couldn't find this account" in page.content():
                    return "❌ غير موجود", target_url
                elif page.locator("[data-e2e='user-post-item']").count() > 0:
                    return "✅ نشط", target_url
                elif response.status == 200:
                    return "✅ نشط", target_url
                    
            elif platform == 'youtube':
                if "This channel doesn't exist" in page.content():
                    return "❌ غير موجود", target_url
                elif page.locator("#subscriber-count").count() > 0:
                    return "✅ نشط", target_url
                elif response.status == 200:
                    return "✅ نشط", target_url
            
            return "⚠️ غير واضح", target_url
            
        except Exception as e:
            return "❓ خطأ في الاتصال", url
        finally:
            browser.close()

# نفس الواجهة من الكود السابق...
