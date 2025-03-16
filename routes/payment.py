import requests
from flask import Blueprint, request, redirect, url_for, session, flash
from models import Product  # مدل محصولات را ایمپورت می‌کنیم

bp = Blueprint("payment", __name__)  # ایجاد Blueprint برای پرداخت

ZIBAL_MERCHANT = "YOUR_ZIBAL_MERCHANT"  # کلید درگاه زیبال را اینجا بگذار
CALLBACK_URL = "http://localhost:5000/payment/verify"  # آدرس بازگشت بعد از پرداخت

@bp.route("/payment/pay/<int:product_id>")
def pay(product_id):
    amount = 70000  # مبلغ نردبان (به ریال)
    description = "نردبان محصول در فروشگاه"

    # درخواست به درگاه زیبال
    data = {
        "merchant": ZIBAL_MERCHANT,
        "amount": amount,
        "callbackUrl": CALLBACK_URL,
        "description": description
    }

    response = requests.post("https://api.zibal.ir/v1/request", json=data)
    result = response.json()

    if result["result"] == 100:
        session["product_id"] = product_id  # ذخیره ID محصول برای تأیید بعدی
        return redirect(f"https://gateway.zibal.ir/start/{result['trackId']}")
    else:
        flash("خطا در اتصال به درگاه پرداخت", "danger")
        return redirect(url_for("main.index"))  # تغییر به صفحه اصلی یا هرجایی که مناسب است

@bp.route("/payment/verify")
def verify():
    # واردات db_instance به صورت داینامیک در اینجا
    from app_main import db_instance

    product_id = session.get("product_id")
    track_id = request.args.get("trackId")

    if not track_id or not product_id:
        flash("پرداخت نامعتبر است", "danger")
        return redirect(url_for("main.index"))

    # بررسی وضعیت پرداخت
    data = {"merchant": ZIBAL_MERCHANT, "trackId": track_id}
    response = requests.post("https://api.zibal.ir/v1/verify", json=data)
    result = response.json()

    if result["result"] == 100:
        # نردبان کردن محصول (به‌روز کردن زمان انتشار)
        product = Product.query.get(product_id)
        if product:
            product.updated_at = db_instance.func.current_timestamp()  # آپدیت زمان آخرین تغییر
            db_instance.session.commit()
            flash("محصول شما با موفقیت نردبان شد!", "success")
        else:
            flash("محصول یافت نشد!", "danger")
    else:
        flash("پرداخت ناموفق بود!", "danger")

    return redirect(url_for("main.index"))  # هدایت به صفحه اصلی
