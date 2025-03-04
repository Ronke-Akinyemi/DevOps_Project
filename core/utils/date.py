import re
from datetime import datetime, timedelta
from django.utils import timezone

def is_valid_date_format(date_string):
    pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    return bool(pattern.match(date_string))

class CustomDateFormating:
    @staticmethod
    def start_end_date(param1=None, param2=None):
        if param1 and not is_valid_date_format(param1):
            return (False, 'Invalid start date format. Use YYYY-MM-DD.', False)
        if param2 and not is_valid_date_format(param2):
            return (False, 'Invalid end date format. Use YYYY-MM-DD.', False)
        today = datetime.now().replace(hour=0, minute=0, second=0)
        if param1:
            param1 = datetime.strptime(param1, '%Y-%m-%d')
        start_date =  param1 or today
        if timezone.is_naive(start_date):
            start_date = timezone.make_aware(start_date, timezone.get_default_timezone())
        if param2:
            param2 = datetime.strptime(param2, '%Y-%m-%d')
        end_date = param2 or (today + timedelta(days=1))
        if timezone.is_naive(end_date):
            end_date = timezone.make_aware(end_date, timezone.get_default_timezone())
        days_difference = (end_date - start_date).days
        date_before = start_date - timedelta(days=days_difference)
        return (start_date, end_date, date_before)
    
    def single_day(param=None):
        if timezone.is_naive(param):
            return timezone.make_aware(param, timezone.get_default_timezone())