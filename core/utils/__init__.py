from decouple import config
import requests
import logging

NOTIFICATION_BASE_URL = config("NOTIFICATION_URL")

logger = logging.getLogger(__name__)