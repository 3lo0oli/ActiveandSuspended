<!DOCTYPE html>
<html lang="ar">
<head>
  <meta charset="UTF-8">
  <title>Active / Suspended Checker</title>
  <style>
    body { font-family: Arial; padding: 30px; background: #f9f9f9; text-align: center; }
    input, select, button { padding: 10px; margin: 10px; width: 300px; max-width: 90%; }
    button { cursor: pointer; }
    #result { margin-top: 20px; font-size: 20px; font-weight: bold; }
  </style>
</head>
<body>
  <h2>تحقق من حالة الحساب</h2>
  <form method="post" action="https://YOUR_STREAMLIT_APP_URL">
    <input type="text" name="url" placeholder="أدخل رابط الحساب" required>
    <br>
    <select name="platform" required>
      <option value="twitter">Twitter</option>
      <option value="reddit">Reddit</option>
      <option value="facebook">Facebook</option>
      <option value="instagram">Instagram</option>
      <option value="youtube">YouTube</option>
      <option value="tiktok">TikTok</option>
    </select>
    <br>
    <button type="submit">تحقق</button>
  </form>
</body>
</html>
