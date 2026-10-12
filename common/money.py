"""Limited monetary parsing; preserve meaning or return unknown.

Markup accepts signed decimal/exponent numbers (100 significant digits,
adjusted exponents -100..100). Visible money additionally supports unambiguous
US/EU grouping and two-place comma decimals. No arbitrary text is stripped.
"""
import re
from decimal import Decimal, InvalidOperation

_NUMBER = re.compile(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\Z')


def markup_money(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        return None
    text = str(value).strip()
    if len(text) > 128 or not _NUMBER.fullmatch(text):
        return None
    try:
        number = Decimal(text)
    except InvalidOperation:
        return None
    if not number.is_finite() or len(number.as_tuple().digits) > 100 or not -100 <= number.adjusted() <= 100:
        return None
    return number


def visible_money(value):
    if not isinstance(value, str):
        return markup_money(value)
    text = value.strip()
    if len(text) > 128:
        return None
    # Supported currency markers must occupy the edge of a monetary token.
    text = re.sub(r'^(?:USD|EUR|GBP|INR|JPY|AUD|CAD|Rs\.?|[$€£₹¥])\s*', '', text)
    text = re.sub(r'\s*(?:USD|EUR|GBP|INR|JPY|AUD|CAD)$', '', text)
    if re.fullmatch(r'[+-]?\d{1,3}(?:,\d{3})+(?:\.\d{2})?', text):
        text = text.replace(',', '')
    elif re.fullmatch(r'[+-]?\d{1,3}(?:\.\d{3})+,\d{2}', text):
        text = text.replace('.', '').replace(',', '.')
    elif re.fullmatch(r'[+-]?\d+,\d{2}', text):
        text = text.replace(',', '.')
    elif ',' in text:
        return None
    return markup_money(text)
