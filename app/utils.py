"""Small helper functions shared across AgriAuction."""


def format_zmw(amount):
    """Format a number as Zambian Kwacha for display."""
    if amount is None:
        return "ZMW 0.00"
    return f"ZMW {amount:,.2f}"
