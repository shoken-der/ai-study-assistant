import ast
import json
import logging
import re
from .ai_service import generate_ai_response

logger = logging.getLogger(__name__)


class LearningServiceError(Exception):
    """Raised when flashcard generation, validation, or concept explanation fails."""
    pass


# Allowed audience levels for concept explanations
allowed_levels = {
    "beginner": "a beginner (clear explanations, simple terminology, intuitive everyday analogies)",
    "intermediate": "an intermediate student (practical examples and moderate depth)",
    "advanced": "an advanced student (in-depth analysis, technical accuracy, and edge cases)",
}


def _strip_markdown_asterisks(text: str) -> str:
    """Remove raw markdown bold/italic asterisks from text so it looks clean and professional."""
    if not text:
        return ""
    cleaned = re.sub(r'\*{1,3}', '', str(text))
    return cleaned.strip()


def _fallback_parse_flashcards(raw_text: str) -> list:
    """
    Fallback parser when AI response is not valid JSON.
    Parses plain text, markdown cards, Q&A pairs, or numbered sections into flashcards.
    Ensures the user never sees a raw 'not valid JSON' crash.
    """
    if not raw_text or not raw_text.strip():
        return []

    text = raw_text.strip()
    cards = []

    # 1. Try splitting by explicit Card markers (e.g., "Card 1:", "Flashcard 2:", "---", or "Q1:")
    card_chunks = re.split(
        r'(?i)(?:^|\n+)(?:---+|\*\*\*+|###+\s*|\*\*(?:Card|Flashcard|Question|Item)\s*\d+[\*:]*|(?:Card|Flashcard|Question|Item)\s*\d+[\*:]*|Q\d+[\.:])',
        text
    )
    card_chunks = [c.strip() for c in card_chunks if c.strip()]

    # If splitting by card markers didn't yield multiple chunks, try double newlines
    if len(card_chunks) < 2:
        card_chunks = [c.strip() for c in re.split(r'\n{2,}', text) if c.strip()]

    for chunk in card_chunks:
        # Check if chunk contains Front/Question and Back/Answer
        front_match = re.search(
            r'(?i)(?:front|question|term|prompt)\s*[:\-]\s*(.*?)(?=\n\s*(?:back|answer|definition|explanation|points|key\s*points)\s*[:\-]|\Z)',
            chunk,
            re.DOTALL
        )
        back_match = re.search(
            r'(?i)(?:back|answer|definition|explanation|points|key\s*points)\s*[:\-]\s*(.*)',
            chunk,
            re.DOTALL
        )

        if front_match and back_match:
            f_text = _strip_markdown_asterisks(front_match.group(1).strip())
            b_text = back_match.group(1).strip()
            # Extract bullet points from back
            b_lines = [l.strip() for l in b_text.splitlines() if l.strip()]
            pts = []
            for bl in b_lines:
                cl = _strip_markdown_asterisks(bl.lstrip("•-*0123456789.) "))
                if cl:
                    pts.append(cl)
            if not pts and b_text:
                pts = [_strip_markdown_asterisks(b_text)]
            if f_text and pts:
                cards.append({
                    "front": f_text,
                    "back": "\n".join(f"• {p}" for p in pts),
                    "points": pts
                })
        else:
            # Check for simple "Q: ... A: ..." lines
            lines = [l.strip() for l in chunk.splitlines() if l.strip()]
            if len(lines) >= 2:
                first_line = lines[0]
                rest_lines = lines[1:]
                f_text = _strip_markdown_asterisks(re.sub(r'(?i)^(?:q|question|term|\d+[\.\)])\s*[:\-]?\s*', '', first_line))
                pts = []
                for rl in rest_lines:
                    cl = _strip_markdown_asterisks(re.sub(r'(?i)^(?:a|answer|def|definition)\s*[:\-]?\s*', '', rl).lstrip("•-*0123456789.) "))
                    if cl:
                        pts.append(cl)
                if f_text and pts:
                    cards.append({
                        "front": f_text,
                        "back": "\n".join(f"• {p}" for p in pts),
                        "points": pts
                    })

    if cards:
        return cards

    # 2. Heuristic fallback: split paragraphs into high-yield flashcards
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 20]
    for i, p in enumerate(paragraphs[:6], start=1):
        clean_p = _strip_markdown_asterisks(p)
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_p) if s.strip()]
        if len(sentences) >= 2:
            cards.append({
                "front": sentences[0],
                "back": "\n".join(f"• {s}" for s in sentences[1:]),
                "points": sentences[1:],
            })
        else:
            cards.append({
                "front": f"Key Topic Concept {i}",
                "back": f"• {clean_p}",
                "points": [clean_p],
            })

    return cards


def _extract_json(raw_text: str):
    """
    Extract and parse JSON data from raw AI response text with multiple layers of repair.
    If JSON parsing completely fails, seamlessly invokes _fallback_parse_flashcards.
    """
    text = raw_text.strip()

    # 1. If wrapped in markdown code fence, extract block content
    code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if code_block_match:
        block_content = code_block_match.group(1).strip()
    else:
        block_content = text

    # Try direct parse on block content and on raw text with strict=False
    for target in (block_content, text):
        try:
            return json.loads(target, strict=False)
        except Exception:
            pass

    # 2. Attempt to locate JSON array [ ... ]
    start_arr = text.find("[")
    end_arr = text.rfind("]")
    if start_arr != -1 and end_arr != -1 and end_arr > start_arr:
        candidate = text[start_arr : end_arr + 1]
        try:
            return json.loads(candidate, strict=False)
        except Exception:
            pass
        # Remove trailing commas: e.g. [ {...,}, ]
        cleaned_arr = re.sub(r',\s*([\]}])', r'\1', candidate)
        try:
            return json.loads(cleaned_arr, strict=False)
        except Exception:
            pass
        # Try python ast literal eval in case of single quotes
        try:
            parsed = ast.literal_eval(candidate)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass

    # 3. Attempt to locate JSON object { ... } (e.g. {"flashcards": [...]} or {"cards": [...]})
    start_obj = text.find("{")
    end_obj = text.rfind("}")
    if start_obj != -1 and end_obj != -1 and end_obj > start_obj:
        candidate = text[start_obj : end_obj + 1]
        for c in (candidate, re.sub(r',\s*([\]}])', r'\1', candidate)):
            try:
                data = json.loads(c, strict=False)
                if isinstance(data, dict):
                    for key in ("flashcards", "cards", "data", "items", "questions", "notes"):
                        if key in data and isinstance(data[key], list):
                            return data[key]
            except Exception:
                pass
        try:
            data = ast.literal_eval(candidate)
            if isinstance(data, dict):
                for key in ("flashcards", "cards", "data", "items", "questions"):
                    if key in data and isinstance(data[key], list):
                        return data[key]
        except Exception:
            pass

    # 4. If structured JSON is not found, fallback to parsing text/markdown cards
    fallback_cards = _fallback_parse_flashcards(text)
    if fallback_cards:
        return fallback_cards

    raise LearningServiceError("The AI did not provide flashcards in a readable format. Please try again.")


def validate_flashcards(flashcards) -> list:
    """Validate and clean AI-generated flashcards into professional, easy-to-understand cards."""
    if not isinstance(flashcards, list) or not flashcards:
        raise LearningServiceError("The AI did not return any flashcards. Please try again.")

    validated = []
    for item in flashcards:
        if not isinstance(item, dict):
            continue

        front = item.get("front") or item.get("question") or item.get("term") or ""
        raw_back = item.get("back") or item.get("answer") or item.get("definition") or ""
        raw_points = item.get("points") or []

        # Remove raw markdown asterisks, hashes, and prefix labels from front
        front_clean = _strip_markdown_asterisks(str(front))
        front_clean = re.sub(r'^(?:Question|Term|Prompt|\d+[\.\)])\s*:\s*', '', front_clean, flags=re.IGNORECASE).strip()

        # Clean points into concise, simple, easy-to-understand revision points
        points = []
        if isinstance(raw_points, list):
            for p in raw_points:
                cleaned_p = _strip_markdown_asterisks(str(p))
                cleaned_p = cleaned_p.lstrip("•-*0123456789.) ").strip()
                if cleaned_p:
                    points.append(cleaned_p)
        elif isinstance(raw_back, list):
            for p in raw_back:
                cleaned_p = _strip_markdown_asterisks(str(p))
                cleaned_p = cleaned_p.lstrip("•-*0123456789.) ").strip()
                if cleaned_p:
                    points.append(cleaned_p)
        elif isinstance(raw_back, str):
            lines = [l.strip() for l in raw_back.splitlines() if l.strip()]
            for l in lines:
                cleaned_p = _strip_markdown_asterisks(l)
                cleaned_p = cleaned_p.lstrip("•-*0123456789.) ").strip()
                if cleaned_p:
                    points.append(cleaned_p)

        if not points:
            single_p = _strip_markdown_asterisks(str(raw_back)).strip()
            if single_p:
                points = [single_p]
            else:
                points = ["Key study takeaway from your notes."]

        if not front_clean:
            front_clean = points[0] if points else "Study Question"

        # Format back string with clean bullet points
        back_text = "\n".join(f"• {p}" for p in points)

        validated.append({
            "front": front_clean,
            "back": back_text,
            "points": points,
            "question": front_clean,
            "answer": back_text,
            "term": front_clean,
            "definition": back_text,
        })

    if not validated:
        raise LearningServiceError("Could not format flashcards from the response. Please try again.")

    return validated


# Aliases for flexibility with different calling conventions
validate_flashcard_data = validate_flashcards
validate_cards = validate_flashcards


def generate_flashcards(
    content: str = "",
    title: str = "",
    num_cards: int = 5,
    note=None,
    note_title: str = "",
    note_content: str = "",
    card_count: int = None,
    count: int = None,
    **kwargs,
) -> list:
    """
    Generate validated study flashcards based on note content or a topic.

    Accepts note content directly or a Note model instance.
    Uses the existing generate_ai_response() function to query Gemini.
    """
    if card_count is not None:
        num_cards = card_count
    elif count is not None:
        num_cards = count
    elif "card_count" in kwargs:
        num_cards = kwargs["card_count"]
    elif "count" in kwargs:
        num_cards = kwargs["count"]

    if note_title:
        title = note_title
    if note_content:
        content = note_content

    # Support passing a Note model instance
    if note is not None:
        title = getattr(note, "title", title)
        content = getattr(note, "content", content)
    elif hasattr(content, "content"):
        title = getattr(content, "title", "")
        content = getattr(content, "content", "")
    elif not content and "note_content" in kwargs:
        content = kwargs.get("note_content", "")

    if not content or not str(content).strip():
        raise LearningServiceError("Study note content cannot be empty.")

    try:
        num_cards = max(1, min(int(num_cards), 20))
    except (TypeError, ValueError):
        num_cards = 5

    prompt = f"""You are a helpful study tutor. Generate {num_cards} simple, easy-to-understand study flashcards from this material.
Keep language clear and simple for students. Do not use difficult technical jargon. Never use markdown asterisks (**) in your headings or points.

STUDY NOTE TITLE: {title or 'Study Note'}
STUDY NOTE CONTENT:
{content}

RULES:
1. Return ONLY a valid JSON array of {num_cards} objects. Do not write introductory text, markdown code blocks, or extra words.
2. Each object in the array must have:
   - "front": A simple, clear question or concept name (plain text, no asterisks).
   - "points": A JSON array of 2 to 4 simple, high-yield bullet point strings explaining the answer clearly.
   - "back": A simple 1-2 sentence plain text summary of the answer.
3. Every point must be clear, bite-sized, and easy to memorize.

Example:
[
  {{
    "front": "What does photosynthesis do?",
    "points": [
      "Plants use sunlight, water, and air to make their own food.",
      "Produces glucose sugar to give the plant energy.",
      "Releases fresh oxygen into the air."
    ],
    "back": "Plants use sunlight to make food and release fresh oxygen."
  }}
]
"""
    try:
        raw_response = generate_ai_response(prompt)
    except Exception as exc:
        logger.exception("Gemini flashcard generation failed")
        raise LearningServiceError(
            "Gemini could not generate flashcards right now. "
            "Please check your API configuration or quota and try again."
        ) from exc

    if not raw_response or not raw_response.strip():
        raise LearningServiceError(
            "Gemini returned an empty response. Please try again."
        )

    parsed_data = _extract_json(raw_response)
    return validate_flashcards(parsed_data)


def explain_concept(concept: str, level: str = "beginner") -> str:
    """
    Explain a complex concept for a specific student level.

    Levels: 'beginner', 'intermediate', 'advanced'
    Uses the existing generate_ai_response() function to query Gemini.
    """
    if not concept or not str(concept).strip():
        raise LearningServiceError("Please provide a concept to explain.")

    concept = str(concept).strip()
    if level not in allowed_levels:
        level = "beginner"

    prompt = f"""You are a patient, friendly, and clear study tutor.
Explain this concept for {allowed_levels[level]}.
Concept: {concept}

Follow this EXACT structure:

1. Simple Definition:
Explain what this means in 1-2 simple sentences using everyday words.

2. How It Works:
• Step 1: clear explanation
• Step 2: clear explanation
• Step 3: clear explanation

3. Everyday Example:
Give a simple real-world story or analogy that makes this easy to visualize.

4. Key Points to Remember:
• Quick recap point 1
• Quick recap point 2
• Quick recap point 3

Formatting Rules:
- Write in simple, student-friendly language.
- Do NOT use markdown asterisks (no **, no ***) on headings. Use clean heading lines like 'Simple Definition:', 'How It Works:', 'Everyday Example:', and 'Key Points to Remember:'.
- Use '• ' for all bullet points.
- If the concept is ambiguous, state the interpretation you are using.
- Do not invent facts."""
    try:
        answer = generate_ai_response(prompt)
    except Exception as exc:
        raise LearningServiceError(
            "Gemini could not explain this concept right now. "
            "Please try again."
        ) from exc
    if not answer.strip():
        raise LearningServiceError(
            "Gemini returned an empty explanation. Please try again."
        )
    return answer.strip()
