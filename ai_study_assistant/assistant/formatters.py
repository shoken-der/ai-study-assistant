"""
StudyAI — AI Text Formatter
Converts raw AI output into clean, structured, and professional HTML:
- Removes ugly raw markdown asterisks (**, ***)
- Converts sections into beautiful headings
- Formats bullet points into clean, styled lists with icons
- Highlights takeaways into distinct callout cards
"""

import re
import html
from django.utils.safestring import mark_safe


def format_ai_response(text: str) -> str:
    """Format raw AI response text into professional HTML without raw asterisks."""
    if not text or not str(text).strip():
        return ""

    raw_text = str(text).strip()

    # Normalize line endings
    raw_text = raw_text.replace("\r\n", "\n").replace("\r", "\n")

    lines = raw_text.split("\n")
    html_parts = []
    in_bullet_list = False

    def close_list():
        nonlocal in_bullet_list
        if in_bullet_list:
            html_parts.append("</ul>")
            in_bullet_list = False

    for line in lines:
        stripped = line.strip()

        # Blank line
        if not stripped:
            close_list()
            continue

        # Check if line is a section heading:
        # e.g., "**1. Simple Definition:**", "### How It Works", "**Key Points:**", "1. Overview:"
        is_heading = False
        heading_text = ""

        # Match markdown heading ### or ##
        if stripped.startswith("###") or stripped.startswith("##"):
            heading_text = stripped.lstrip("#").strip()
            is_heading = True
        # Match lines wrapped in asterisks like **Heading:** or **Heading**
        elif (
            (stripped.startswith("**") and stripped.endswith("**"))
            or (stripped.startswith("**") and ":**" in stripped)
            or (stripped.startswith("**") and stripped.endswith(":**"))
        ):
            # Clean asterisks
            heading_text = stripped.replace("**", "").replace("###", "").strip()
            is_heading = True
        # Match lines like "1. Overview:" or "Key Takeaway:" or "Simple Definition:"
        elif (
            re.match(r"^(\d+[\.\)]\s*)?[A-Z][A-Za-z\s&–—]+:$", stripped)
            and len(stripped) < 60
        ):
            heading_text = stripped.replace("**", "").strip()
            is_heading = True

        if is_heading:
            close_list()
            # Clean heading text
            clean_title = html.escape(heading_text.rstrip(":"))

            # Determine special icon for heading
            lower_title = clean_title.lower()
            icon = "✦"
            is_takeaway = False
            if "definition" in lower_title or "overview" in lower_title or "what" in lower_title:
                icon = "📖"
            elif "work" in lower_title or "mechanism" in lower_title or "step" in lower_title:
                icon = "⚙️"
            elif "example" in lower_title or "analogy" in lower_title:
                icon = "💡"
            elif "point" in lower_title or "term" in lower_title or "remember" in lower_title:
                icon = "🎯"
            elif "takeaway" in lower_title or "summary" in lower_title:
                icon = "⚡"
                is_takeaway = True

            extra_cls = " ai-takeaway-header" if is_takeaway else ""
            html_parts.append(
                f'<div class="ai-section-heading{extra_cls}">'
                f'<span class="ai-heading-icon">{icon}</span>'
                f'<span class="ai-heading-title">{clean_title}</span>'
                f'</div>'
            )
            continue

        # Check if line is a bullet point:
        # e.g., "* Point", "- Point", "• Point", "1. Point"
        bullet_match = re.match(r"^[\*\-\•]\s+(.*)$", stripped)
        numbered_match = re.match(r"^(\d+)[\.\)]\s+(.*)$", stripped)

        if bullet_match or (numbered_match and not is_heading):
            if not in_bullet_list:
                html_parts.append('<ul class="ai-point-list">')
                in_bullet_list = True

            item_content = bullet_match.group(1) if bullet_match else numbered_match.group(2)

            # Clean any stray **bold** markdown inside the bullet point into clean <strong> tags
            clean_item = _format_inline_markdown(item_content)

            html_parts.append(
                f'<li class="ai-point-item">'
                f'<span class="ai-point-bullet">✦</span>'
                f'<span class="ai-point-text">{clean_item}</span>'
                f'</li>'
            )
            continue

        # Regular paragraph text
        close_list()
        clean_para = _format_inline_markdown(stripped)
        html_parts.append(f'<p class="ai-paragraph">{clean_para}</p>')

    close_list()

    return mark_safe("\n".join(html_parts))


def _format_inline_markdown(text: str) -> str:
    """Safely format inline **bold** and *italic* without leaving raw asterisks."""
    escaped = html.escape(text)

    # Convert **bold** to <strong class="ai-strong">...</strong>
    escaped = re.sub(
        r"\*\*(.+?)\*\*",
        r'<strong class="ai-strong">\1</strong>',
        escaped,
    )

    # Convert single *italic* to <em>...</em>
    escaped = re.sub(
        r"\*([^\*]+?)\*",
        r'<em>\1</em>',
        escaped,
    )

    # Clean any accidental leftover double asterisks
    escaped = escaped.replace("**", "")

    return escaped
