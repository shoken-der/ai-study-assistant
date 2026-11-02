from django import template
from assistant.formatters import format_ai_response

register = template.Library()


@register.filter(name="format_ai")
def format_ai_filter(value):
    """Template filter to render AI text in clean, professional points and headings."""
    if not value:
        return ""
    return format_ai_response(str(value))
