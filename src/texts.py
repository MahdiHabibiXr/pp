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
    CAPTION_MISSING = "⚠️ Please send the image with a descriptive caption."
    INSUFFICIENT_CREDITS = "⚠️ You do not have enough credits. Your balance is {credits_balance} credits.\nUse /buy to purchase more."
    PHOTO_DOWNLOAD_ERROR = "❌ Error downloading the image. Please try again."
    PHOTO_UPLOAD_ERROR = "❌ Error uploading the image. Please try again later."
    PROMPT_SERVICE_ERROR = "❌ Error contacting the prompt generation service. Please try again later."
    PROMPT_GENERATION_ERROR = "❌ Error generating the image description. Please try again later."
    IMAGE_GENERATION_SUBMISSION_ERROR = "❌ Error submitting the request to the image generation service. Your credits have been refunded."
    REQUEST_RECEIVED = "✅ Your request has been received (ID: `{gen_uid}`). It is now being processed. You will receive the image as soon as it's ready."

    # --- Payment (callbacks.py) ---
    PAYMENT_CREATION_ERROR = "❌ Error creating payment: {err}"
    PURCHASE_PROMPT = "To purchase **{coins}** credits for **{price:,}** Rial, please complete the payment:"
    INVALID_PAYMENT_ID = "Invalid payment ID."
    PAYMENT_RECORD_NOT_FOUND = "Payment record not found."
    PAYMENT_VERIFIED_SUCCESS = "🎉 Payment verified! **{pay.package_coins}** credits have been added."
    PAYMENT_ALREADY_VERIFIED = "ℹ️ This payment has already been verified."
    PAYMENT_NOT_CONFIRMED = (
        "❌ Your payment has not been confirmed by the bank.\n\n"
        "If a deduction was made from your account, it will be returned within 72 hours.\n\n"
        "If you are sure about your payment, please try again in a few minutes or contact support."
    )
    PAYMENT_VERIFICATION_FAILED = "❌ Payment verification failed: {err}"

    # --- Webhooks ---
    GENERATION_NOT_FOUND = "generation record not found"
    GENERATION_FAILED = "⚠️ Generation failed: {error}"

    # --- Zarinpal Client ---
    PAYMENT_REQUEST_TIMEOUT = "The payment request timed out. Please try again in a moment."
    VERIFICATION_REQUEST_TIMEOUT = "The verification request timed out. The server is taking too long to respond. Please try again in a moment."
    COULD_NOT_PARSE_ZARINPAL_ERROR = "Could not parse final Zarinpal error."


class ButtonLabels:
    COMPLETE_PAYMENT = "🛒 Complete Payment"
    I_HAVE_PAID = "✅ I have paid"
    RETRY_VERIFICATION = "🔄 Retry Verification"


# Instantiate for easy access
messages = MessageTexts()
buttons = ButtonLabels()