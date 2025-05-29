from django.template import Library

register = Library()


@register.filter(is_safe=True)
def card_number_slicer(value, display_last=4):
    """
       Formats a card number for secure display.
       Examples:
           {{ "1234567890123456"|format_card_number }} → **** **** **** 3456
           {{ "1234567890123456"|format_card_number:6 }} → **** **** **23456
       """
    try:
        # Remove any non-digit characters
        cleaned = ''.join(c for c in str(value) if c.isdigit())

        if not cleaned:
            return ""

        length = len(cleaned)
        display_last = min(int(display_last), length)

        # Format with asterisks and show last N digits
        masked = '*' * (length - display_last)
        visible_part = cleaned[-display_last:]

        # Add spacing every 4 characters for better readability
        formatted = []
        for i in range(0, len(masked + visible_part), 4):
            part = (masked + visible_part)[i:i + 4]
            if part:
                formatted.append(part)

        return ' '.join(formatted)
    except (ValueError, TypeError):
        return str(value)
