import logging
from datetime import timedelta
from django.db.models import Avg, Max, Sum
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, NoteForm
from .models import Note, QuizAttempt
from .ai_service import generate_ai_response
from .quiz_service import generate_quiz, QuizGenerationError
from .learning_service import (
    LearningServiceError,
    explain_concept,
    generate_flashcards,
)

logger = logging.getLogger(__name__)


def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "assistant/home.html")


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = RegisterForm()
    return render(
        request,
        "assistant/register.html",
        {"form": form},
    )


@login_required
def dashboard(request):
    user_notes = Note.objects.filter(user=request.user)
    notes_count = user_notes.count()
    recent_notes = user_notes[:5]
    return render(
        request,
        "assistant/dashboard.html",
        {
            "notes_count": notes_count,
            "recent_notes": recent_notes,
        },
    )


@login_required
def notes_list(request):
    notes = Note.objects.filter(user=request.user)
    return render(
        request,
        "assistant/notes_list.html",
        {"notes": notes},
    )


@login_required
def note_create(request):
    if request.method == "POST":
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.user = request.user
            note.save()
            return redirect("notes_list")
    else:
        form = NoteForm()
    return render(
        request,
        "assistant/note_form.html",
        {"form": form, "page_title": "Create a Note", "action": "Create"},
    )


@login_required
def note_edit(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    if request.method == "POST":
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            return redirect("notes_list")
    else:
        form = NoteForm(instance=note)
    return render(
        request,
        "assistant/note_form.html",
        {"form": form, "note": note, "page_title": "Edit Note", "action": "Edit"},
    )


@login_required
def note_delete(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    if request.method == "POST":
        note.delete()
        return redirect("notes_list")
    return render(
        request,
        "assistant/note_confirm_delete.html",
        {"note": note},
    )


@login_required
def summarizer(request):
    notes = Note.objects.filter(user=request.user)
    summary = None
    selected_note_id = request.GET.get("note", "")
    error_message = None
    if request.method == "POST":
        selected_note_id = request.POST.get("note_id", "")
        try:
            note_id = int(selected_note_id)
        except (TypeError, ValueError):
            note_id = None
        note = notes.filter(pk=note_id).first() if note_id else None
        if not note:
            error_message = "Please select one of your saved notes."
        elif not note.content.strip():
            error_message = "This note has no content to summarize."
        else:
            prompt = (
                "You are a friendly, clear study assistant. Summarize the following study notes in a clean, professional, and easy-to-understand format.\n\n"
                "Follow this EXACT structure:\n\n"
                "1. Overview:\n"
                "A simple 1-2 sentence introduction explaining what this note is about.\n\n"
                "2. Key Points:\n"
                "• Point 1: clear explanation\n"
                "• Point 2: clear explanation\n"
                "• Point 3: clear explanation\n"
                "• Point 4: clear explanation\n\n"
                "3. Important Terms:\n"
                "• Term Name: Simple explanation\n"
                "• Term Name: Simple explanation\n\n"
                "4. Main Takeaway:\n"
                "One simple sentence capturing the most important lesson to remember.\n\n"
                "Formatting Rules:\n"
                "- Write in simple, natural language so any student can understand.\n"
                "- Do NOT use markdown asterisks (no **, no ***) on headings. Use clean heading lines like 'Overview:', 'Key Points:', 'Important Terms:', and 'Main Takeaway:'.\n"
                "- Use '• ' for every bullet point.\n"
                "- Be factually accurate based only on the notes provided.\n\n"
                f"NOTE TITLE: {note.title}\n\n"
                f"NOTE CONTENT:\n{note.content}"
            )
            try:
                summary = generate_ai_response(prompt)
            except Exception:
                # Log the actual exception on the server, not in the UI.
                import logging
                logging.getLogger(__name__).exception(
                    "Gemini summarization failed"
                )
                error_message = (
                    "Gemini could not generate a summary right now. "
                    "Please check your API configuration or quota "
                    "and try again."
                )
    return render(
        request,
        "assistant/summarizer.html",
        {
            "notes": notes,
            "summary": summary,
            "selected_note_id": selected_note_id,
            "error_message": error_message,
        },
    )


@login_required
def quiz_generator(request):
    notes = Note.objects.filter(user=request.user)
    error_message = None
    quiz_questions = None
    note_title = None
    selected_note_id = request.GET.get("note", "")

    if request.method == "POST":
        selected_note_id = request.POST.get("note_id", "")
        question_count = request.POST.get("question_count", "5")
        try:
            question_count = int(question_count)
        except (TypeError, ValueError):
            question_count = 0
        note = notes.filter(pk=selected_note_id).first()
        if not note:
            error_message = "Please select one of your saved notes."
        elif question_count not in range(3, 11):
            error_message = "Choose between 3 and 10 questions."
        elif not note.content.strip():
            error_message = "This note has no content to make a quiz from."
        else:
            try:
                questions = generate_quiz(
                    note_title=note.title,
                    note_content=note.content,
                    question_count=question_count,
                )
                # Store the answer key server-side in the Django session.
                request.session["active_quiz"] = {
                    "note_id": note.pk,
                    "note_title": note.title,
                    "questions": questions,
                }
                return redirect("quiz_submit")
            except QuizGenerationError as err:
                error_message = str(err)
            except Exception:
                logger.exception("Gemini quiz generation failed")
                error_message = (
                    "Gemini could not generate a quiz right now. "
                    "Please check your API configuration or quota "
                    "and try again."
                )

    return render(
        request,
        "assistant/quiz_generator.html",
        {
            "notes": notes,
            "selected_note_id": selected_note_id,
            "error_message": error_message,
        },
    )


@login_required
def quiz_submit(request):
    active_quiz = request.session.get("active_quiz")
    if not active_quiz:
        return redirect("quiz_generator")

    # Verify note ownership
    note_id = active_quiz.get("note_id")
    if not Note.objects.filter(pk=note_id, user=request.user).exists():
        request.session.pop("active_quiz", None)
        return redirect("quiz_generator")

    questions = active_quiz.get("questions", [])
    if not questions:
        return redirect("quiz_generator")

    if request.method == "POST":
        score = 0
        results = []
        for index, q in enumerate(questions):
            user_ans = request.POST.get(f"answer_{index}")
            if user_ans is None:
                user_ans = request.POST.get(f"question_{index}")
            try:
                user_ans_idx = int(user_ans)
            except (TypeError, ValueError):
                user_ans_idx = None

            is_correct = (user_ans_idx == q.get("correct_answer"))
            if is_correct:
                score += 1

            results.append({
                "index": index + 1,
                "question": q.get("question", ""),
                "options": q.get("options", []),
                "selected_answer": user_ans_idx if user_ans_idx is not None else -1,
                "user_answer": user_ans_idx,
                "correct_answer": q.get("correct_answer"),
                "explanation": q.get("explanation", ""),
                "is_correct": is_correct,
            })

        total = len(questions)
        percentage = round((score / total) * 100) if total > 0 else 0

        # Save the completed quiz for permanent progress tracking.
        quiz = active_quiz
        quiz_note = Note.objects.filter(
            pk=quiz.get("note_id"),
            user=request.user,
        ).first()
        QuizAttempt.objects.create(
            user=request.user,
            note=quiz_note,
            note_title=str(quiz.get("note_title", "Study Quiz"))[:200],
            total_questions=len(questions),
            correct_answers=score,
            percentage=percentage,
        )

        # Remove from active session after grading to prevent resubmission
        request.session.pop("active_quiz", None)
        request.session.modified = True

        context = {
            "note_title": active_quiz.get("note_title", "Quiz"),
            "score": score,
            "total": total,
            "percentage": percentage,
            "results": results,
        }
        return render(request, "assistant/quiz_result.html", context)

    # If accessed via GET with an active quiz in session
    safe_questions = [
        {
            "index": index,
            "question": q.get("question", ""),
            "options": q.get("options", []),
        }
        for index, q in enumerate(questions)
    ]

    return render(
        request,
        "assistant/quiz_take.html",
        {
            "note_title": active_quiz.get("note_title", "Quiz"),
            "quiz_questions": safe_questions,
            "questions": safe_questions,
            "total": len(safe_questions),
        },
    )


# Alias in case URLs or templates reference quiz_take
quiz_take = quiz_submit


@login_required
def flashcard_generator(request):
    notes = Note.objects.filter(user=request.user)
    error_message = None
    flashcards = None
    selected_note_id = request.GET.get("note", "")
    card_count = 4

    if request.method == "POST":
        selected_note_id = request.POST.get("note_id", "")
        raw_card_count = request.POST.get("card_count", "4")
        try:
            card_count = int(raw_card_count)
        except (TypeError, ValueError):
            card_count = 4

        try:
            note_id = int(selected_note_id)
        except (TypeError, ValueError):
            note_id = None
        note = notes.filter(pk=note_id).first() if note_id else None
        if not note:
            error_message = "Please select one of your saved notes."
        elif not note.content.strip():
            error_message = "This note has no content to generate flashcards from."
        else:
            try:
                flashcards = generate_flashcards(
                    note_title=note.title,
                    note_content=note.content,
                    count=card_count,
                    card_count=card_count,
                )
            except LearningServiceError as exc:
                error_message = str(exc)
            except Exception:
                import logging
                logging.getLogger(__name__).exception(
                    "Unexpected flashcard generation error"
                )
                error_message = (
                    "Unable to generate flashcards right now. "
                    "Please try again."
                )

    return render(
        request,
        [
            "assistant/flashcard_lab.html",
            "assistant/flashcards.html",
            "assistant/flashcard_generator.html",
        ],
        {
            "notes": notes,
            "cards": flashcards,
            "flashcards": flashcards,
            "card_count": card_count,
            "selected_note_id": selected_note_id,
            "error_message": error_message,
        },
    )


# Aliases for flexibility with different calling conventions and URL names
flashcard_lab = flashcard_generator
flashcards = flashcard_generator


@login_required
def concept_explainer(request):
    explanation = None
    error_message = None
    concept = ""
    level = "beginner"
    if request.method == "POST":
        concept = request.POST.get("concept", "").strip()
        level = request.POST.get("level", "beginner")
        try:
            explanation = explain_concept(concept, level)
        except LearningServiceError as exc:
            error_message = str(exc)
        except Exception:
            import logging
            logging.getLogger(__name__).exception(
                "Unexpected concept explanation error"
            )
            error_message = (
                "Unable to explain this concept right now. "
                "Please try again."
            )
    return render(
        request,
        "assistant/concept_explainer.html",
        {
            "concept": concept,
            "level": level,
            "explanation": explanation,
            "error_message": error_message,
        },
    )


@login_required
def learning_progress(request):
    notes = Note.objects.filter(user=request.user)
    attempts = QuizAttempt.objects.filter(user=request.user)
    stats = attempts.aggregate(
        average_score=Avg("percentage"),
        best_score=Max("percentage"),
        total_questions=Sum("total_questions"),
        correct_answers=Sum("correct_answers"),
    )
    total_quizzes = attempts.count()
    average_score = stats["average_score"] or 0
    best_score = stats["best_score"] or 0
    total_questions = stats["total_questions"] or 0
    correct_answers = stats["correct_answers"] or 0
    today = timezone.localdate()
    activity = []
    for days_ago in range(6, -1, -1):
        day = today - timedelta(days=days_ago)
        quiz_count = attempts.filter(
            created_at__date=day
        ).count()
        notes_count = notes.filter(
            created_at__date=day
        ).count()
        activity.append({
            "label": day.strftime("%a"),
            "date": day.strftime("%d %b"),
            "count": quiz_count + notes_count,
        })
    maximum_activity = max(
        (item["count"] for item in activity),
        default=0,
    )
    for item in activity:
        item["height"] = (
            round(item["count"] / maximum_activity * 100)
            if maximum_activity else 0
        )
    return render(
        request,
        "assistant/learning_progress.html",
        {
            "notes_count": notes.count(),
            "total_quizzes": total_quizzes,
            "average_score": round(average_score, 1),
            "best_score": round(best_score, 1),
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "activity": activity,
            "recent_attempts": attempts[:10],
        },
    )



