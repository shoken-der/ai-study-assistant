from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import Note, QuizAttempt


class AssistantSecurityAndCRUDTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="student1",
            password="TestPass123!",
        )
        self.other_user = User.objects.create_user(
            username="student2",
            password="TestPass123!",
        )

    def test_user_registration(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newstudent",
                "password1": "SecurePass123!",
                "password2": "SecurePass123!",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            User.objects.filter(username="newstudent").exists()
        )

    def test_login_protection(self):
        protected_urls = [
            reverse("dashboard"),
            reverse("notes_list"),
            reverse("note_create"),
        ]
        for url in protected_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn("/accounts/login/", response.url)

    def test_note_creation(self):
        self.client.login(
            username="student1",
            password="TestPass123!",
        )
        response = self.client.post(
            reverse("note_create"),
            {
                "title": "Java OOP",
                "content": "Classes, objects, and encapsulation.",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Note.objects.filter(
                user=self.user,
                title="Java OOP",
            ).exists()
        )

    def test_users_cannot_edit_another_users_note(self):
        other_note = Note.objects.create(
            user=self.other_user,
            title="Private Notes",
            content="This belongs to another student.",
        )
        self.client.login(
            username="student1",
            password="TestPass123!",
        )
        response = self.client.get(
            reverse("note_edit", args=[other_note.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_users_cannot_delete_another_users_note(self):
        other_note = Note.objects.create(
            user=self.other_user,
            title="Private Notes",
            content="Do not delete this.",
        )
        self.client.login(
            username="student1",
            password="TestPass123!",
        )
        response = self.client.post(
            reverse("note_delete", args=[other_note.pk])
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            Note.objects.filter(pk=other_note.pk).exists()
        )

    def test_quiz_submission_saves_attempt(self):
        note = Note.objects.create(
            user=self.user,
            title="Django Testing",
            content="Writing unit tests for Django views.",
        )
        self.client.login(username="student1", password="TestPass123!")
        session = self.client.session
        session["active_quiz"] = {
            "note_id": note.pk,
            "note_title": note.title,
            "questions": [
                {
                    "question": "What framework is this?",
                    "options": ["Flask", "Django", "FastAPI", "Express"],
                    "correct_answer": 1,
                    "explanation": "Django is a Python web framework.",
                }
            ],
        }
        session.save()

        response = self.client.post(
            reverse("quiz_submit"),
            {"answer_0": "1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            QuizAttempt.objects.filter(
                user=self.user,
                note=note,
                correct_answers=1,
                total_questions=1,
                percentage=100.0,
            ).exists()
        )

    def test_learning_progress_view_and_user_isolation(self):
        # User 1 attempt
        QuizAttempt.objects.create(
            user=self.user,
            note_title="Student 1 Quiz",
            total_questions=5,
            correct_answers=4,
            percentage=80.0,
        )
        # User 2 attempt (should NOT appear for User 1)
        QuizAttempt.objects.create(
            user=self.other_user,
            note_title="Secret Student 2 Quiz",
            total_questions=5,
            correct_answers=1,
            percentage=20.0,
        )

        self.client.login(username="student1", password="TestPass123!")
        response = self.client.get(reverse("learning_progress"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Student 1 Quiz")
        self.assertNotContains(response, "Secret Student 2 Quiz")
        self.assertEqual(response.context["total_quizzes"], 1)
        self.assertEqual(response.context["average_score"], 80.0)
        self.assertEqual(response.context["best_score"], 80.0)

