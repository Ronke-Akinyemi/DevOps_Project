from fastapi import HTTPException, status
import random
import string
import re
from db.models import Marketer, MarketterPasswordResetToken
from datetime import datetime, timedelta
import pytz


def generate_random_password(length=10):
    characters = string.ascii_letters + string.digits + string.digits
    password = ''.join(random.choice(characters) for _ in range(length))
    return password

credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def check_password(new_password):
    if re.search('[A-Z]', new_password) is None:
        raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Password must contain One Uppercase Alphabet",
    )

    if re.search('[a-z]', new_password) is None:
        raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Password must contain One Lowercase Alphabet",
    )

    if re.search('[0-9]', new_password) is None:
        raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Password must contain One Numeric Character",
    )

    if re.search(r"[@$!%*#?&]", new_password) is None:
        raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Password must contain One Special Character",
    )
    return True

def is_valid_date_format(date_str: str) -> bool:
    """Check if a string is in YYYY-MM-DD format."""
    try:
        datetime.strptime(str(date_str), '%Y-%m-%d')
        return True
    except ValueError:
        return False
class CustomDateFormatting:
    @staticmethod
    def start_end_date(param1: str = None, param2: str = None, tz: str = 'UTC'):
        """Parse start and end dates, ensuring correct timezone handling."""
        # Validate date formats
        if param1 and not is_valid_date_format(param1):
            return False, 'Invalid start date format. Use YYYY-MM-DD.', False
        if param2 and not is_valid_date_format(param2):
            return False, 'Invalid end date format. Use YYYY-MM-DD.', False
        

        # Get the timezone
        timezone = pytz.timezone(tz)

        # Set default to today's date at midnight
        today = datetime.now(timezone).replace(hour=0, minute=0, second=0, microsecond=0)

        # Parse start_date
        start_date = datetime.strptime(str(param1), '%Y-%m-%d').replace(tzinfo=timezone) if param1 else today

        # Parse end_date or default to next day
        end_date = datetime.strptime(str(param2), '%Y-%m-%d').replace(tzinfo=timezone) if param2 else today + timedelta(days=1)

        # Calculate date_before
        days_to_subtract = (end_date - start_date).days
        date_before = start_date - timedelta(days=days_to_subtract)

        return start_date, end_date, date_before

    @staticmethod
    def single_day(param: datetime, tz: str = 'UTC'):
        """Ensure a datetime is timezone-aware."""
        timezone = pytz.timezone(tz)
        if param.tzinfo is None or param.tzinfo.utcoffset(param) is None:
            return timezone.localize(param)
        return param
