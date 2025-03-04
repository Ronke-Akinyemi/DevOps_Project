from hashlib import sha256
import time
import requests
from decouple import config
import os

PUBLIC_KEY = config("VELVE_PUBLIC_KEY")
VELVE_BASE_URL = config("VELVE_BASE_URL")
VELVE_PROJECT_URL = config("VELVE_PROJECT_URL")



class VelvePayment:
    @staticmethod
    def generate_token():
        url = VELVE_PROJECT_URL
        response = requests.request("GET", url)
        response_status = response.status_code
        response_body = response.json()
        if response_status != 200:
            return (False, response_body.get("reason"))
        return (response_body.get("refrence_id"), response_body.get("token"))
    
    
    @staticmethod
    def initiate_payment(data):
        try:
            url = f'{VELVE_BASE_URL}/payment/initiate'
            reference, token = VelvePayment.generate_token()
            if not reference:
                return (False, "Something went wrong internally")
            payload = {
                "title": "Sync Subscription",
                "description":"Payment for sync",
                "chargeCustomer": False,
                "amount": data["amount"],
                "isNaira": True
                }
            headers = {
            'api-key': token,
            'public-key': PUBLIC_KEY,
            'reference-id': reference,
            }

            response = requests.request("POST", url, headers=headers, data=payload)
            response_status = response.status_code
            response_body = response.json()
            if response_status != 200:
                return (False, response_body.get("reason"))
            if response_body.get("status") == "success" and response_body.get("link"):
                return (reference, response_body.get("link"))
            return (False, response_body.get("reason"))
        except BaseException:
            return (False, "Error connecting to bank")
    @staticmethod
    def check_payment(info):
        try:
            url = f'{VELVE_BASE_URL}/payment/collection/transaction/details?transaction_id={info.get("transaction_id")}'
            payload={}
            reference, token = VelvePayment.generate_token()
            headers = {
            'api-key': token,
            'public-key': PUBLIC_KEY,
            'reference-id': reference
            }
            response = requests.request("GET", url, headers=headers, data=payload)
            response_status = response.status_code
            response_body = response.json()
            if response_status != 200:
                return False
            if response_body.get("status") != "success":
                return False
            data = response_body.get("data")
            if not data:
                return False
            payment_status = data.get("status")
            if payment_status == "confirmed":
                return True
            return False
        except BaseException:
            return False

