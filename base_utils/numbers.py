def safe_decimal_to_float(value):
    """Safely ctainoert Decimal to float, handling None values"""
    if value is None:
        return 0.0
    return float(value)
