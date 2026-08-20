import httpx
from fastapi import FastAPI, HTTPException
import uvicorn

app = FastAPI(title="VULMS WhatsApp Notification Engine")

# Testing Credentials (Inhe apne setup ke mutabiq change kar lein)
WHATSAPP_GATEWAY_URL = "http://localhost:8080/message/sendText/vulms_bot"
GATEWAY_API_KEY = "your_gateway_key_here"
TEST_PHONE_NUMBER = "923001234567"  # Target WhatsApp number (Country code ke sath)


@app.get("/")
def home():
    return {"status": "online", "system": "VULMS Alert Engine"}


@app.post("/send-test-whatsapp")
async def send_test_whatsapp():
    # Message Body
    payload = {
        "number": TEST_PHONE_NUMBER,
        "text": "🚨 *VULMS Test Alert*\n\nFastAPI server se WhatsApp notification test successfully dispatch ho gaya hai!",
    }

    headers = {"apikey": GATEWAY_API_KEY, "Content-Type": "application/json"}

    async with httpx.AsyncClient() as client:
        try:
            # WhatsApp Gateway ko hit kar rahe hain
            response = await client.post(
                WHATSAPP_GATEWAY_URL, json=payload, headers=headers, timeout=10.0
            )

            if response.status_code in [200, 201]:
                return {
                    "status": "success",
                    "message": "Notification Sent",
                    "gateway_response": response.json(),
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Gateway Rejected Request: {response.text}",
                )

        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=500,
                detail=f"WhatsApp Gateway URL reach nahi ho raha: {str(exc)}",
            )


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)