import os
import pytz
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def get_timezone():
    """
    Always returns UTC to ensure database consistency.
    The application stores everything in UTC (0.00 offset).
    """
    return pytz.UTC

def get_current_time():
    """Returns current time in APP_TIMEZONE"""
    tz = get_timezone()
    return datetime.now(tz)

def to_app_propper_time(dt):
    """Converts a naive datetime to APP_TIMEZONE properly"""
    if dt is None: return None
    tz = get_timezone()
    # If naive, assume it was local/utc and localize? Or just attach?
    # Best practice: if naive, assume UTC then convert. 
    # But usually db stores naive. Let's start by just making it timezone aware if it isn't.
    if dt.tzinfo is None:
        return pytz.utc.localize(dt).astimezone(tz)
    return dt.astimezone(tz)
