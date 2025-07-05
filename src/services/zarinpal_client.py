import httpx
import logfire
from uuid import uuid4

from src.config import settings

# یک‌بار لاگ‌فای را پیکربندی می‌کنیم
logfire.configure(token=settings.LOGFIRE_TOKEN)

class ZarinpalClient:
    """
    Client for creating and verifying payments via Zarinpal,
    با پشتیبانی از پاسخ‌های آرایه‌ای و تشخیص کدهای 100/101 در Verify.
    """
    def __init__(self):
        self.merchant_id  = settings.ZARINPAL_MERCHANT_ID
        self.callback_url = settings.ZARINPAL_CALLBACK_URL
        self.request_url  = settings.ZARINPAL_REQUEST_URL
        self.verify_url   = settings.ZARINPAL_VERIFY_URL
        self.payment_base = settings.ZARINPAL_PAYMENT_BASE

    def _headers(self):
        return {"Content-Type": "application/json", "Accept": "application/json"}

    async def create_payment(
        self,
        chat_id: int,
        amount: int,
        package_coins: int,
        description: str
    ) -> dict:
        """
        Initiates a Zarinpal payment.
        Returns:
          - success: bool
          - payment_link, authority, payment_uid  (on success)
          - error, status                       (on failure)
        """
        uid = str(uuid4())
        payload = {
            "merchant_id": self.merchant_id,
            "amount": amount,
            "callback_url": self.callback_url,
            "description": description,
            "metadata": {"chat_id": chat_id, "package_coins": package_coins},
        }
        logfire.info(f"🔄 Zarinpal create_payment payload: {payload}")

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                res = await client.post(self.request_url, json=payload, headers=self._headers())
            res.raise_for_status()
            resp_json = res.json()
        except httpx.TimeoutException:
            msg = "Timeout while connecting to Zarinpal"
            logfire.error(f"❌ {msg}")
            return {"success": False, "error": msg}
        except httpx.HTTPError as e:
            msg = f"HTTP error: {e}"
            logfire.error(f"❌ {msg}")
            return {"success": False, "error": msg}

        logfire.info(f"✅ Zarinpal raw response: {resp_json}")

        # اگر پاسخ لیست است، عنصر اول را بگیر
        if isinstance(resp_json, list) and resp_json:
            resp_json = resp_json[0]

        # مسیر موفقیت: data.code == 100
        data = resp_json.get("data", {})
        code = data.get("code")
        if code == 100:
            authority    = data["authority"]
            payment_link = f"{self.payment_base}{authority}"
            return {
                "success": True,
                "payment_link": payment_link,
                "payment_uid": uid,
                "authority": authority
            }

        # مسیر خطا: اگر data وجود دارد، از آن استفاده کن
        if data:
            err_msg = data.get("message") or f"خطای نامشخص (code={code})"
            logfire.error(f"❌ Zarinpal create error in data: {err_msg} (code={code})")
            return {"success": False, "error": err_msg, "status": code}

        # مسیر خطا کلیدهای سطح‌بالا
        status = resp_json.get("status")
        err_msg = resp_json.get("message") or resp_json.get("error") or f"Error (status={status})"
        logfire.error(f"❌ Zarinpal create top-level error: {err_msg} (status={status})")
        return {"success": False, "error": err_msg, "status": status}

    async def verify_payment(self, authority: str, amount: int) -> dict:
        """
        Verifies a Zarinpal payment.
        On success:
          - code==100: پرداخت جدیداً تأیید شد
          - code==101: پرداخت قبلاً تأیید شده
        Returns dict with:
          success: bool
          ref_id: int  (when code in [100,101])
          status: int  (the code)
          error: str   (on failure)
        """
        payload = {"merchant_id": self.merchant_id, "amount": amount, "authority": authority}
        logfire.info(f"🔄 Zarinpal verify_payment payload: {payload}")

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                res = await client.post(self.verify_url, json=payload, headers=self._headers())
            res.raise_for_status()
            resp_json = res.json()
        except httpx.TimeoutException:
            msg = "Timeout while verifying with Zarinpal"
            logfire.error(f"❌ {msg}")
            return {"success": False, "error": msg}
        except httpx.HTTPError as e:
            msg = f"HTTP error: {e}"
            logfire.error(f"❌ {msg}")
            return {"success": False, "error": msg}

        logfire.info(f"✅ Zarinpal verify raw response: {resp_json}")

        # اگر پاسخ لیست است، عنصر اول را بگیر
        if isinstance(resp_json, list) and resp_json:
            resp_json = resp_json[0]

        data = resp_json.get("data", {})
        code = data.get("code")

        if code in (100, 101):
            ref_id = data.get("ref_id")
            return {"success": True, "ref_id": ref_id, "status": code}

        # خطا در data
        if data:
            err_msg = data.get("message") or f"Verification failed (code={code})"
            logfire.error(f"❌ Zarinpal verify error in data: {err_msg} (code={code})")
            return {"success": False, "error": err_msg, "status": code}

        # خطا کلیدهای سطح‌بالا
        status = resp_json.get("status")
        err_msg = resp_json.get("message") or resp_json.get("error") or f"Verification error (status={status})"
        logfire.error(f"❌ Zarinpal verify top-level error: {err_msg} (status={status})")
        return {"success": False, "error": err_msg, "status": status}
