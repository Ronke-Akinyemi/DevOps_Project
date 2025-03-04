from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from utils import logger, NOTIFICATION_BASE_URL
import requests

class SendMail:

    @staticmethod
    def send_email(data, html=None):
        url = f"{NOTIFICATION_BASE_URL}/send-email/"
        payload = {"email": data["user"], "title": data["subject"], "message": data["body"]}
        headers = {"Content-Type": "application/json"}
        try:
            requests.post(url, headers=headers, json=payload)
        except BaseException as e:
            logger.error(f"Error sending email: {str(e)}")
    @staticmethod
    def sendVerificationCode(info):
        data = {}
        data["subject"] = f"{info.get('subject', 'Sync360')}"
        data["body"] = f"Your code is {info['token']}. Valid for 10 minutes, one-time use only."
        data["user"] = info["email"]
        SendMail.send_email(data)
    @staticmethod
    def send_invite_mail(info):
        data = {}
        data["subject"] = "Admin Invitation"
        data["body"] = f'Your Login details is\n\nEmail: {info["email"]}\nPassowrd: {info["password"]}'
        data["user"] = info["email"]
        SendMail.send_email(data)
    @staticmethod
    def send_attendance_email(info):
        data = {}
        data["subject"] = "New attendant addended"
        data["body"]= f'{info["name"]} has been added to your business with the following credentials:\n\n email:\t{info["email"]}\n\nDefault password:\t{info["password"]}\n\nThey are to reset this password before logging in'
        data["user"] = info["business_email"]
        SendMail.send_email(data)

    @staticmethod
    def send_welcome_mail(data):
        SendMail.send_email(data)

    @staticmethod
    def send_loan_notification_email(info):
        frontend_url = config("FRONTEND_URL")
        html_content = render_to_string('mail.html', {
            "frontend_url":frontend_url,
            })
        data = {
            "subject": "",
            "body": html_content,
            "user": info["email"]
        }
        SendMail.send_email(data, html=True)

        # SendMail.send_email(data, html=True)

    @staticmethod
    def send_email_verification_mail(info):
        data = {}
        data["subject"] = "Email verification"
        message = f"Dear {info['firstname']} {info['lastname']}\n\nYour Verification code is {info['token']}"
        data["body"] = message
        data["user"] = info["user"]
        SendMail.send_email(data)

    @staticmethod
    def send_password_reset_mail(info):
        data = {}
        message = f"Please use the this code to reset your password {info['token']}"
        data['body'] = message
        data["user"] = info["email"]
        data["subject"] = "Reset password email"
        SendMail.send_email(data)

