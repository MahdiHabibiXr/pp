# src/texts.py

class MessageTexts:
    # --- General ---
    INVALID_CHOICE = "انتخاب نامعتبر است."
    PACKAGE_NOT_FOUND = "بسته مورد نظر موجود نیست."

    # --- /start command ---
    WELCOME = (
        "Welcome to the Product Placement Bot!\n"
        "Use /generate to create an image.\n"
        "Use /balance to check your credits.\n"
        "Use /buy to purchase credit packages."
    )

    # --- /balance command ---
    BALANCE_CHECK = "Your balance: {credits} credits."

    # --- /buy command ---
    NO_PACKAGES = "بسته‌ای برای نمایش وجود ندارد."

    # --- Photo handling (messages.py) ---
    CAPTION_MISSING = "⚠️ لطفاً تصویر را همراه با توضیح (caption) ارسال کنید."
    PHOTO_DOWNLOAD_ERROR = "❌ خطا در دانلود تصویر. لطفاً دوباره تلاش کنید."
    PHOTO_UPLOAD_ERROR = "❌ خطا در بارگذاری تصویر. لطفاً بعداً امتحان کنید."
    PROMPT_SERVICE_ERROR = "❌ خطا در برقراری ارتباط با سرویس تولید توضیح. لطفاً بعداً امتحان کنید."
    PROMPT_GENERATION_ERROR = "❌ خطا در تولید توضیح تصویر. لطفاً بعداً امتحان کنید."
    IMAGE_GENERATION_SUBMISSION_ERROR = "❌ خطا در ارسال درخواست به سرویس تولید تصویر. لطفاً بعداً امتحان کنید."
    REQUEST_RECEIVED = "✅ درخواست شما دریافت شد (ID: `{gen_uid}`). در حال پردازش است؛ به محض آماده شدن تصویر را دریافت خواهید کرد."

    # --- Payment (callbacks.py) ---
    PAYMENT_CREATION_ERROR = "❌ خطا هنگام ایجاد پرداخت: {err}"
    PURCHASE_PROMPT = "برای خرید **{coins}** اعتبار به ارزش **{price:,}** ریال، لطفاً پرداخت را تکمیل کنید:"
    INVALID_PAYMENT_ID = "شناسه پرداخت نامعتبر است."
    PAYMENT_RECORD_NOT_FOUND = "رکورد پرداخت پیدا نشد."
    PAYMENT_VERIFIED_SUCCESS = "🎉 پرداخت تایید شد! **{pay.package_coins}** اعتبار اضافه شد."
    PAYMENT_ALREADY_VERIFIED = "ℹ️ این پرداخت قبلاً تأیید شده است."
    PAYMENT_VERIFICATION_FAILED = "❌ پرداخت تأیید نشد: {err}"

    # --- Webhooks ---
    GENERATION_NOT_FOUND = "generation record not found"
    GENERATION_FAILED = "⚠️ Generation failed: {error}"


class ButtonLabels:
    COMPLETE_PAYMENT = "🛒 Complete Payment"
    I_HAVE_PAID = "✅ I have paid"


# Instantiate for easy access
messages = MessageTexts()
buttons = ButtonLabels()