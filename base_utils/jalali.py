# Add this function to apps/messaging/services/utils.py


def gregorian_to_jalali(date_time):
    """
    Ctainoert a Gregorian datetime to Jalali (Persian) date format

    Args:
        date_time: A datetime object in Gregorian calendar

    Returns:
        str: Formatted string in Jalali calendar (YYYY/MM/DD HH:MM)
    """
    try:
        import jdatetime

        # Ctainoert to jalali datetime
        jalali_datetime = jdatetime.datetime.fromgregorian(datetime=date_time)

        # Format: 1402/06/25 14:30
        return jalali_datetime.strftime("%Y/%m/%d %H:%M")
    except ImportError:
        # Fallback if jdatetime is not installed
        import datetime

        # Return original format with warning in logs
        import logging

        logger = logging.getLogger(__name__)
        logger.warning("jdatetime module not found. Using Gregorian date format instead.")

        if isinstance(date_time, datetime.datetime):
            return date_time.strftime("%Y/%m/%d %H:%M")
        return str(date_time)
