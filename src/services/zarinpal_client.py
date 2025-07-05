# src/services/zarinpal_client.py

import httpx
import logfire
from uuid import uuid4

from src.config import settings

# یک‌بار لاگ‌فای را پیکربندی می‌کنیم
logfire.configure(token=settings.LOGFIRE_TOKEN)

class ZarinpalClient:
    """
    Client for creating and verifying payments via Zarinpal,
    with metadata limited to mobile and email only.
    """

    def __init__(self):
        self.merchant_id  = settings.ZARINPAL_MERCHANT_ID
        self.callback_url = settings.ZARINPAL_CALLBACK_URL
        self.request_url  = settings.ZARINPAL_REQUEST_URL
        self.verify_url   = settings.ZARINPAL_VERIFY_URL
        self.payment_base = settings.ZARINPAL_PAYMENT_BASE

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def create_payment(
        self,
        chat_id: int,
        amount: int,
        package_coins: int,
        description: str
    ) -> dict:
        """
        Initiates a Zarinpal payment.
        
        Parameters:
        - chat_id: Telegram chat ID (for logging/reference only)
        - amount: amount in IRR
        - package_coins: number of credits (not sent in metadata)
        - description: text description of the package
        
        Returns a dict with:
        - success: bool
        - payment_link, authority, payment_uid  (on success)
        - error, status                         (on failure)
        """
        payment_uid = str(uuid4())
        payload = {
            "merchant_id": self.merchant_id,
            "amount": amount,
            "callback_url": self.callback_url,
            "description": description,
            "metadata": {
                "mobile": settings.ZARINPAL_MERCHANT_MOBILE,
                "email":  settings.ZARINPAL_MERCHANT_EMAIL
            }
        }
        logfire.info(f"🔄 Zarinpal create_payment payload: {payload}")

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    self.request_url,
                    json=payload,
                    headers=self._headers()
                )
            response.raise_for_status()
            resp_json = response.json()
        except httpx.TimeoutException:
            msg = "Timeout while connecting to Zarinpal"
            logfire.error(f"❌ {msg}")
            return {"success": False, "error": msg}
        except httpx.HTTPStatusError as e:
            # لاگ کامل پاسخ خطا
            try:
                err_body = e.response.json()
                logfire.error(f"❌ Zarinpal HTTP {e.response.status_code}: {err_body}")
                # تلاش برای استخراج پیام از بدنه JSON
                err_msg = (
                    err_body.get("data", {}).get("errors", {}).get("message")
                    or err_body.get("message")
                    or str(err_body)
                )
            except Exception:
                err_msg = str(e)
            return {"success": False, "error": err_msg, "status": e.response.status_code}
        except Exception as e:
            msg = f"HTTP error: {e}"
            logfire.error(f"❌ {msg}")
            return {"success": False, "error": msg}

        logfire.info(f"✅ Zarinpal raw create response: {resp_json}")

        # پاسخ ممکن است در قالب لیست باشد
        if isinstance(resp_json, list) and resp_json:
            resp_json = resp_json[0]

        data = resp_json.get("data", {})
        code = data.get("code")

        if code == 100:
            authority    = data["authority"]
            payment_link = f"{self.payment_base}{authority}"
            return {
                "success": True,
                "payment_link": payment_link,
                "payment_uid": payment_uid,
                "authority": authority
            }

        # استخراج پیام خطا از data
        err_msg = data.get("message") or f"خطای نامشخص (code={code})"
        logfire.error(f"❌ Zarinpal create error in data: {err_msg} (code={code})")
        return {"success": False, "error": err_msg, "status": code}

    async def verify_payment(
        self,
        authority: str,
        amount: int
    ) -> dict:
        """
        Verifies a Zarinpal payment.

        Returns a dict with:
        - success: bool
        - ref_id: int      (when code in [100,101])
        - status: int      (the Zarinpal code)
        - error: str       (on failure)
        """
        payload = {
            "merchant_id": self.merchant_id,
            "amount": amount,
            "authority": authority
        }
        logfire.info(f"🔄 Zarinpal verify_payment payload: {payload}")

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    self.verify_url,
                    json=payload,
                    headers=self._headers()
                )
            response.raise_for_status()
            resp_json = response.json()
        except httpx.TimeoutException:
            msg = "Timeout while verifying with Zarinpal"
            logfire.error(f"❌ {msg}")
            return {"success": False, "error": msg}
        except httpx.HTTPStatusError as e:
            try:
                err_body = e.response.json()
                logfire.error(f"❌ Zarinpal HTTP {e.response.status_code}: {err_body}")
                err_msg = (
                    err_body.get("data", {}).get("errors", {}).get("message")
                    or err_body.get("message")
                    or str(err_body)
                )
            except Exception:
                err_msg = str(e)
            return {"success": False, "error": err_msg, "status": e.response.status_code}
        except Exception as e:
            msg = f"HTTP error: {e}"
            logfire.error(f"❌ {msg}")
            return {"success": False, "error": msg}

        logfire.info(f"✅ Zarinpal raw verify response: {resp_json}")

        # پاسخ ممکن است در قالب لیست باشد
        if isinstance(resp_json, list) and resp_json:
            resp_json = resp_json[0]

        data = resp_json.get("data", {})
        code = data.get("code")

        if code in (100, 101):
            ref_id = data.get("ref_id")
            return {"success": True, "ref_id": ref_id, "status": code}

        # استخراج پیام خطا از data
        err_msg = data.get("message") or f"Verification failed (code={code})"
        logfire.error(f"❌ Zarinpal verify error in data: {err_msg} (code={code})")
        return {"success": False, "error": err_msg, "status": code}
