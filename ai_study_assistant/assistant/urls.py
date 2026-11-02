from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", auth_views.LoginView.as_view(), name="login_direct"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout_direct"),
    path("register/", views.register, name="register"),
    path("dashboard/", views.dashboard, name="dashboard"),
    # Notes CRUD
    path("notes/", views.notes_list, name="notes_list"),
    path("notes/new/", views.note_create, name="note_create"),
    path("notes/<int:pk>/edit/", views.note_edit, name="note_edit"),
    path("notes/<int:pk>/delete/", views.note_delete, name="note_delete"),
    # Gemini AI
    path("summarizer/", views.summarizer, name="summarizer"),
    path("quiz/", views.quiz_generator, name="quiz_generator"),
    path("quiz/submit/", views.quiz_submit, name="quiz_submit"),
    path(
        "flashcards/",
        views.flashcard_lab,
        name="flashcard_lab",
    ),
    path(
        "concept-explainer/",
        views.concept_explainer,
        name="concept_explainer",
    ),
    path("progress/", views.learning_progress, name="learning_progress"),
    path("learning-progress/", views.learning_progress, name="learning_progress_alias"),
    path("learning_progress/", views.learning_progress, name="learning_progress_alias2"),
]

