import frappe
import requests

@frappe.whitelist()
def send_whatsapp_message(number, text):
    number = number.replace("+", "").replace(" ", "")
    # requests.post(
    #     "https://api.evo.uat.rolaface.com/message/sendText/hrms-instance",
    #     headers={"apikey": "429683C4C977415CAAFCCE10F7D57E11", "Content-Type": "application/json"},
    #     json={"number": number, "text": text},
    #     timeout=10
    # )