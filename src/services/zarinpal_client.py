# src/services/zarinpal_client.py

import httpx
import logfire
import json
from uuid import uuid4

from src.config import settings
from src.texts import messages

# Configure Logfire once
logfire.configure(token=settings.LOGFIRE_TOKEN)


class ZarinpalClient:
    """
    Client for creating and verifying payments via Zarinpal, with robust
    error handling for timeouts, HTTP errors, and nested error messages.
    """
    def __init__(self):
        self.merchant_id  = settings.ZARINPAL_MERCHANT_ID
        self.callback_url = settings.ZARINPAL_CALLBACK_URL
        self.request_url  = settings.ZARINPAL_REQUEST_URL
        self.verify_url   = settings.ZARINPAL_VERIFY_URL
        self.payment_base = settings.ZARINPAL_PAYMENT_BASE
        # Increased timeout to 20 seconds
        self.timeout = 20.0

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
        """
        uid = str(uuid4())
        payload = {
            "merchant_id": self.merchant_id,
            "amount": amount,
            "callback_url": self.callback_url,
            "description": description,
            "metadata": {
                "mobile": settings.ZARINPAL_MERCHANT_MOBILE,
                "email": settings.ZARINPAL_MERCHANT_EMAIL,
            },
        }
        logfire.info(f"🔄 Zarinpal create_payment payload: {payload}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(self.request_url, json=payload, headers=self._headers())
            res.raise_for_status()
            resp_json = res.json()

        except httpx.TimeoutException:
            msg = messages.PAYMENT_REQUEST_TIMEOUT
            logfire.error(f"❌ Zarinpal create timeout: {msg}")
            return {"success": False, "error": msg, "status": "TIMEOUT"}
        except httpx.HTTPStatusError as e:
            msg = f"HTTP error {e.response.status_code}: {e.response.text}"
            logfire.error(f"❌ {msg}")
            return {"success": False, "error": e.response.text, "status": e.response.status_code}
        except Exception as e:
            msg = f"An unexpected error occurred: {e}"
            logfire.error(f"❌ {msg}")
            return {"success": False, "error": msg}

        logfire.info(f"✅ Zarinpal create raw response: {resp_json}")
        errors = resp_json.get("errors")
        data = resp_json.get("data")

        if errors and errors != []:
            err_msg = errors.get("message", "Unknown error")
            err_code = errors.get("code")
            return {"success": False, "error": err_msg, "status": err_code}

        if data and data.get("code") == 100:
            authority = data["authority"]
            payment_link = f"{self.payment_base}{authority}"
            return {"success": True, "payment_link": payment_link, "payment_uid": uid, "authority": authority}

        err_msg = (data.get("message") if data else "Invalid response")
        err_code = (data.get("code") if data else None)
        return {"success": False, "error": err_msg, "status": err_code}

    async def verify_payment(self, authority: str, amount: int) -> dict:
        """
        Verifies a Zarinpal payment, with robust error handling for the specific n8n workflow response.
        """
        payload = {"merchant_id": self.merchant_id, "amount": amount, "authority": authority}
        logfire.info(f"🔄 Zarinpal verify_payment payload: {payload}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(self.verify_url, json=payload, headers=self._headers())
            res.raise_for_status()
            resp_json = res.json()

        except httpx.TimeoutException:
            msg = messages.VERIFICATION_REQUEST_TIMEOUT
            logfire.error(f"❌ Zarinpal verify timeout: {msg}")
            return {"success": False, "error": msg, "status": "TIMEOUT"}
        
        except httpx.HTTPStatusError as e:
            logfire.error(f"❌ Zarinpal verify HTTP error ({e.response.status_code})... attempting to parse nested error.")
            
            try:
                # Step 1: Parse the outer JSON object from the n8n error response.
                n8n_error_data = e.response.json()
                
                # Step 2: Extract the 'message' string, which itself contains JSON.
                message_with_nested_json = n8n_error_data.get("error", {}).get("message", e.response.text)

                # Step 3: Find the start and end of the nested JSON within the string.
                json_start_index = message_with_nested_json.find('{')
                json_end_index = message_with_nested_json.rfind('}')
                
                if json_start_index == -1:
                    raise ValueError("Nested JSON start not found")

                # Step 4: Extract the raw, escaped JSON string.
                raw_json_part = message_with_nested_json[json_start_index : json_end_index + 1]
                
                # Step 5: Unescape characters like \\" to " and parse the clean string.
                cleaned_json_string = raw_json_part.replace('\\"', '"')
                final_data = json.loads(cleaned_json_string)
                
                # Step 6: Extract the real error message and code from the innermost 'errors' object.
                final_errors = final_data.get("errors", {})
                message = final_errors.get("message", messages.COULD_NOT_PARSE_ZARINPAL_ERROR)
                code = final_errors.get("code")
                
                logfire.info(f"✅ Successfully parsed nested Zarinpal error. Code: {code}, Message: {message}")
                return {"success": False, "error": message, "status": code}

            except Exception as parse_error:
                # Fallback if the robust parsing fails for any reason
                logfire.error(f"💥 Failed to parse nested error, falling back to raw text. Parse Error: {parse_error}")
                return {"success": False, "error": e.response.text, "status": e.response.status_code}

        except Exception as e:
            logfire.exception(f"💥 Unexpected error during Zarinpal verification: {e}")
            return {"success": False, "error": str(e)}

        logfire.info(f"✅ Zarinpal verify raw response: {resp_json}")
        errors = resp_json.get("errors")
        data = resp_json.get("data")

        if errors and errors != []:
            return {"success": False, "error": errors.get("message"), "status": errors.get("code")}

        if data and data.get("code") in (100, 101):
            return {"success": True, "ref_id": data.get("ref_id"), "status": data.get("code")}

        err_msg = (data.get("message") if data else "Invalid response structure")
        err_code = (data.get("code") if data else None)
        return {"success": False, "error": err_msg, "status": err_code}