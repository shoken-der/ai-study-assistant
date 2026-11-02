import logging
import os
from dotenv import load_dotenv
from google import genai
from google.genai import errors

logger = logging.getLogger(__name__)

# Load environment variables from the project-root .env file.
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
load_dotenv(os.path.join(BASE_DIR, ".env"))

API_KEY = os.getenv("GEMINI_API_KEY")
DEFAULT_MODEL = "gemini-3.5-flash-lite"
MODEL_NAME = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)

# Fallback models in priority order if primary model is unavailable or rate-limited
FALLBACK_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3-flash-preview",
    "gemini-3.5-flash",
]


def generate_ai_response(prompt: str) -> str:
    """Generate a text response using the Gemini API with automatic model fallback."""
    api_key = os.getenv("GEMINI_API_KEY") or API_KEY
    if not api_key:
        load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)
        api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. "
            "Check the .env file beside manage.py."
        )
    if not prompt or not prompt.strip():
        raise ValueError("Please enter some text.")

    client = genai.Client(api_key=api_key)

    primary_model = os.getenv("GEMINI_MODEL") or MODEL_NAME or DEFAULT_MODEL
    models_to_try = [primary_model] + [
        m for m in FALLBACK_MODELS if m != primary_model
    ]

    last_error = None
    for model in models_to_try:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt.strip(),
            )
            answer = response.text
            if not answer:
                raise RuntimeError(
                    f"Gemini model {model} returned an empty response. Try again."
                )
            return answer.strip()
        except (errors.ServerError, errors.APIError, Exception) as exc:
            last_error = exc
            logger.warning(
                "Gemini generation with model '%s' failed: %s. Attempting fallback model...",
                model,
                exc,
            )

    raise RuntimeError(
        f"All Gemini models failed. Last error: {last_error}"
    ) from last_error
