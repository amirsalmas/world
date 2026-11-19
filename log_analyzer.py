# log_analyzer.py
import re
import requests
from datetime import datetime

# ---------------------------------------------------------
# دانلود فایل از تلگرام
# ---------------------------------------------------------
def download_telegram_file(bot_token, file_id):
    """فایل رو از سرور تلگرام دانلود می‌کنه و متنش رو برمی‌گردونه."""
    url = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
    r = requests.get(url, timeout=30).json()
    if not r.get("ok"):
        raise Exception(f"getFile failed: {r}")
    file_path = r["result"]["file_path"]
    file_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
    content = requests.get(file_url, timeout=60).text
    return content


# ---------------------------------------------------------
# تحلیل لاگ Railway
# ---------------------------------------------------------
def analyze_railway_log(log_text):
    """
    خروجی: لیستی از دیکشنری‌ها به شکل
    [{"date": "2026-11-19", "asset": "money", "value": 12000, "raw": "..."}]
    الگوها رو بر اساس فرمت واقعی لاگ خودت تنظیم کن.
    """
    date_re  = re.compile(r"(\d{4}-\d{2}-\d{2})")
    asset_re = re.compile(r"(money|gold|oil|food|iron|troops?)\s*[:=]\s*(\d+)", re.IGNORECASE)

    results = []
    for line in log_text.splitlines():
        d = date_re.search(line)
        a = asset_re.search(line)
        if d and a:
            results.append({
                "date":  d.group(1),
                "asset": a.group(1).lower(),
                "value": int(a.group(2)),
                "raw":   line.strip(),
            })
    return results


# ---------------------------------------------------------
# پیدا کردن آخرین مقدار هر دارایی (برای هر تاریخ)
# ---------------------------------------------------------
def latest_assets_per_date(parsed_rows):
    """
    dict برمی‌گردونه: { "2026-11-19": {"money": 12000, "gold": 50}, ... }
    آخرین مقدار هر دارایی در هر روز رو نگه می‌داره.
    """
    result = {}
    for row in parsed_rows:
        result.setdefault(row["date"], {})[row["asset"]] = row["value"]
    return result


# ---------------------------------------------------------
# اعمال روی داده‌های بازی
# ---------------------------------------------------------
def apply_to_game_state(game_state, parsed_rows):
    """
    game_state: دیکشنری که state بازی توش هست (مثلاً U یا countries).
    این تابع رو دقیقاً مطابق ساختار داده خودت بنویس.

    مثال فرضی:
        game_state["countries"]["IR"]["money"] = ...
    """
    per_date = latest_assets_per_date(parsed_rows)
    if not per_date:
        return False, "چیزی از لاگ استخراج نشد."

    # آخرین تاریخ موجود در لاگ
    latest_date = max(per_date.keys())
    assets = per_date[latest_date]

    # ✏️ اینجا رو با ساختار واقعی ربات خودت تنظیم کن
    # مثلاً:
    # game_state["last_update_date"] = latest_date
    # for asset, val in assets.items():
    #     game_state["assets"][asset] = val

    return True, f"دارایی‌ها برای تاریخ {latest_date} به‌روزرسانی شد: {assets}"


# ---------------------------------------------------------
# تابع یکجا برای صدا زدن از فایل اصلی
# ---------------------------------------------------------
def handle_admin_log_upload(bot_token, file_id, game_state, admin_chat_id, send_message):
    """
    همه چیز رو یکجا انجام می‌ده.
    send_message: تابع ارسال پیام ربات (از فایل اصلی پاس بده).
    """
    try:
        send_message(admin_chat_id, "⏳ در حال دانلود فایل لاگ...")
        text = download_telegram_file(bot_token, file_id)

        send_message(admin_chat_id, f"🔍 در حال تحلیل {len(text.splitlines())} خط لاگ...")
        parsed = analyze_railway_log(text)

        if not parsed:
            send_message(admin_chat_id, "❌ هیچ داده‌ای از لاگ استخراج نشد. الگوها رو چک کن.")
            return

        ok, msg = apply_to_game_state(game_state, parsed)
        send_message(admin_chat_id, ("✅ " if ok else "⚠️ ") + msg)

    except Exception as e:
        send_message(admin_chat_id, f"💥 خطا: {e}")
