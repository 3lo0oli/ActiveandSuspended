import requests

def check_facebook_account(username_or_id):
    url = f"https://www.facebook.com/{username_or_id}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            if "content=\"0; URL=/" in response.text or "This Page Isn't Available" in response.text:
                return "❌ الحساب غير متاح أو موقوف (Suspended/Deleted)"
            else:
                return "✅ الحساب نشط (Active)"
        elif response.status_code == 404:
            return "❌ الحساب غير موجود (Not Found)"
        else:
            return f"⚠️ حالة غير معروفة - كود الاستجابة: {response.status_code}"

    except requests.exceptions.RequestException as e:
        return f"🚫 خطأ في الاتصال: {e}"

# مثال على الاستخدام:
account_username = "zuck"  # ضع اسم المستخدم أو ID
result = check_facebook_account(account_username)
print(result)
