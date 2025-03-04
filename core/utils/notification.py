import requests
from decouple import config
from utils import logger, NOTIFICATION_BASE_URL


class SendSMS:
    @staticmethod
    def send_sms(data):
        url = f"{NOTIFICATION_BASE_URL}/send-sms/"
        headers = {"Content-Type": "application/json"}
        try:
            requests.post(url, headers=headers, json=data)
        except BaseException as e:
            logger.error(f"Error sending SMS: {str(e)}")
    @staticmethod
    def sendVerificationCode(info):
        data = {
            "to":info["number"],
            "body":f"Your code is {info['token']}. Valid for 10 minutes, one-time use only."
        }
        SendSMS.send_sms(data)

class SendPushNotification:
    @staticmethod
    def send_notification(data):
        url = f"http://127.0.0.1:8000/send-notification/"
        headers = {"Content-Type": "application/json"}
        try:
            requests.post(url, headers=headers, json=data)
        except BaseException as e:
            logger.error(f"Error sending Notification: {str(e)}")
    @staticmethod
    def notify(info):
        data = {
            "token":info["token"],
            "title": info["title"],
            "body": info["body"],
            "data": info["data"]
        }
        SendPushNotification.send_notification(data)
