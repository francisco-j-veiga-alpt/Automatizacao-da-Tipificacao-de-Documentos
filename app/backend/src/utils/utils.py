from dateutil.relativedelta import relativedelta
from datetime import date, datetime, time

def string_to_date(date_string):
    """
    Converts a date string in the format "DD Month YYYY" (e.g., "1 de Janeiro 2024")
    to a date object.

    Args:
        date_string: The date string to convert.

    Returns:
        A datetime.date object representing the parsed date, or None if the input
        string is invalid or cannot be parsed.  Handles potential errors.
    """

    month_names = {
        "janeiro": 1,
        "fevereiro": 2,
        "março": 3,
        "abril": 4,
        "maio": 5,
        "junho": 6,
        "julho": 7,
        "agosto": 8,
        "setembro": 9,
        "outubro": 10,
        "novembro": 11,
        "dezembro": 12,
    }

    try:
        day, _, month_name, year = date_string.split()

        try:
            day = int(day)
            year = int(year)
        except ValueError as e:
            raise

        month = month_names.get(month_name.lower())

        if month is None:
            raise ValueError("String to date None!")

        try:
            date_object = datetime(year, month, day)
            return date_object
        except Exception as e:
            raise

    except Exception as e:
        e.add_note("String to date Exception!")
        raise


def parse_date(date_string: str) -> datetime:
    try:
        return datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError as e:
        e.add_note("Incorrect date format. Please use YYYY-MM-DD.")
        raise


def subtract_n_months_and_get_first_day(num_of_months=2):
    try:
        today = date.today()
        two_months_ago = today - relativedelta(months=num_of_months)
        first_day = two_months_ago.replace(day=1)
        return datetime.combine(first_day, time.min)
    except Exception as e:
        e.add_note("Error subtract n months and get first_day!")
        raise

