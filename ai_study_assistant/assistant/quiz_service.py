import ast
import json
import logging
import re
from .ai_service import generate_ai_response

logger = logging.getLogger(__name__)


class QuizGenerationError(Exception):
    """Raised when quiz generation or response parsing fails."""
    pass


def validate_quiz(questions):
    """Validate that the AI-generated questions match the expected quiz schema."""
    if not isinstance(questions, list) or not questions:
        raise QuizGenerationError("The AI did not return any quiz questions.")

    validated = []
    for item in questions:
        if not isinstance(item, dict):
            raise QuizGenerationError("An AI question was invalid.")
        question = item.get("question")
        options = item.get("options")
        correct_answer = item.get("correct_answer")
        explanation = item.get("explanation", "")
        if not isinstance(question, str) or not question.strip():
            raise QuizGenerationError("A question was missing its text.")
        if (
            not isinstance(options, list)
            or len(options) != 4
            or not all(isinstance(option, str) and option.strip()
                       for option in options)
        ):
            raise QuizGenerationError(
                "A question did not have four valid options."
            )
        if (
            isinstance(correct_answer, bool)
            or not isinstance(correct_answer, int)
            or correct_answer not in range(4)
        ):
            raise QuizGenerationError(
                "A question had an invalid correct answer."
            )
        if not isinstance(explanation, str):
            explanation = ""
        validated.append({
            "question": question.strip(),
            "options": [option.strip() for option in options],
            "correct_answer": correct_answer,
            "explanation": explanation.strip(),
        })
    return validated


# Aliases for flexibility with different calling conventions
validate_quiz_data = validate_quiz
validate_questions = validate_quiz


def _extract_json(raw_text: str):
    """Extract and parse JSON data from raw AI response text with multi-layer resilience."""
    text = raw_text.strip()

    # 1. Strip markdown code fences anywhere in the string
    code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if code_block_match:
        block_content = code_block_match.group(1).strip()
    else:
        block_content = text

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
        for c in (candidate, re.sub(r',\s*([\]}])', r'\1', candidate)):
            try:
                return json.loads(c, strict=False)
            except Exception:
                pass
        try:
            parsed = ast.literal_eval(candidate)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass

    # 3. Attempt to locate JSON object { ... } in case response is wrapped in {"questions": [...]}
    start_obj = text.find("{")
    end_obj = text.rfind("}")
    if start_obj != -1 and end_obj != -1 and end_obj > start_obj:
        candidate = text[start_obj : end_obj + 1]
        for c in (candidate, re.sub(r',\s*([\]}])', r'\1', candidate)):
            try:
                data = json.loads(c, strict=False)
                if isinstance(data, dict):
                    for key in ("questions", "quiz", "data", "items"):
                        if key in data and isinstance(data[key], list):
                            return data[key]
            except Exception:
                pass
        try:
            data = ast.literal_eval(candidate)
            if isinstance(data, dict):
                for key in ("questions", "quiz", "data", "items"):
                    if key in data and isinstance(data[key], list):
                        return data[key]
        except Exception:
            pass

    raise QuizGenerationError("The AI did not provide quiz questions in a readable format.")


def generate_quiz(
    content: str = "",
    title: str = "",
    num_questions: int = 5,
    note=None,
    note_title: str = "",
    note_content: str = "",
    question_count: int = None,
    **kwargs,
) -> list:
    """
    Generate a validated multiple-choice quiz based on study note content.

    Accepts note content directly or a Note model instance.
    Uses the existing generate_ai_response() function to query Gemini.
    """
    if question_count is not None:
        num_questions = question_count
    elif "question_count" in kwargs:
        num_questions = kwargs["question_count"]

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
        title = kwargs.get("note_title", title)

    if not content or not str(content).strip():
        raise QuizGenerationError("The note has no content to generate a quiz from.")

    prompt = (
        "You are an expert study assistant and quiz creator. "
        f"Generate a multiple-choice practice quiz with {num_questions} questions "
        "based strictly on the student study notes below.\n\n"
        f"NOTE TITLE: {title}\n\n"
        f"NOTE CONTENT:\n{content}\n\n"
        "RESPONSE FORMAT:\n"
        "- Respond with a raw JSON array of question objects only.\n"
        "- Do not include markdown ticks, explanations, or conversational text.\n"
        "- Each question object must follow this exact structure:\n"
        "  {\n"
        '    "question": "Question text here?",\n'
        '    "options": ["Option 0", "Option 1", "Option 2", "Option 3"],\n'
        '    "correct_answer": 0,\n'
        '    "explanation": "Why this answer is correct."\n'
        "  }\n"
        "- 'options' must be a list of exactly 4 strings.\n"
        "- 'correct_answer' must be an integer (0, 1, 2, or 3).\n"
        "- 'explanation' must be a short explanation string."
    )

    try:
        raw_response = generate_ai_response(prompt)
    except Exception as exc:
        logger.exception("Gemini call failed during quiz generation")
        raise QuizGenerationError(f"AI service error: {exc}") from exc

    parsed = _extract_json(raw_response)
    if isinstance(parsed, dict) and "questions" in parsed:
        parsed = parsed["questions"]

    return validate_quiz(parsed)


# Alias in case the tutorial imports generate_quiz_from_note or generate_quiz_from_notes
generate_quiz_from_note = generate_quiz
generate_quiz_from_notes = generate_quiz
