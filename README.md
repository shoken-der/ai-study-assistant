# 🧠 AI Study Assistant

> A powerful, AI-driven study companion built with Django and Google Gemini — helping students learn smarter through smart notes, auto-generated quizzes, flashcards, concept explanations, and personalized learning progress tracking.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📝 **Smart Notes** | Create, edit, and manage your study notes |
| 📄 **AI Summarizer** | Instantly summarize long notes using Google Gemini |
| ❓ **Quiz Generator** | Auto-generate multiple-choice quizzes from your notes |
| 🃏 **Flashcard Lab** | Turn your notes into interactive flashcards |
| 💡 **Concept Explainer** | Get clear, simple explanations for complex topics |
| 📊 **Learning Progress** | Track your quiz history and performance over time |
| 🔐 **Authentication** | Secure user registration, login, and logout |

---

## 🛠️ Tech Stack

- **Backend**: [Django 6.1](https://www.djangoproject.com/)
- **AI Engine**: [Google Gemini API](https://ai.google.dev/) via `google-genai`
- **Database**: SQLite (development)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **3D Effects**: [Three.js](https://threejs.org/)
- **Environment**: `python-dotenv`

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- A [Google Gemini API Key](https://aistudio.google.com/app/apikey)

### 1. Clone the Repository

```bash
git clone https://github.com/shoken-der/ai-study-assistant.git
cd ai-study-assistant
```

### 2. Create & Activate a Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
cd ai_study_assistant
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=*
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Create a Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 7. Start the Development Server

```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000** in your browser 🎉

---

## 📁 Project Structure

```
ai-study-assistant/
├── ai_study_assistant/
│   ├── assistant/                  # Main Django app
│   │   ├── templates/assistant/    # HTML templates
│   │   ├── templatetags/           # Custom template tags
│   │   ├── models.py               # Note & QuizAttempt models
│   │   ├── views.py                # All view logic
│   │   ├── forms.py                # Django forms
│   │   ├── urls.py                 # URL routing
│   │   ├── ai_service.py           # Gemini AI integration
│   │   ├── quiz_service.py         # Quiz generation logic
│   │   ├── learning_service.py     # Progress tracking logic
│   │   └── formatters.py          # Response formatters
│   ├── config/                     # Django project config
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── static/                     # CSS & JS assets
│   │   ├── css/style.css
│   │   └── js/                     # Three.js & custom 3D scripts
│   ├── templates/                  # Base templates
│   │   ├── base.html
│   │   └── registration/           # Login & register pages
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
└── README.md
```

---

## 🌐 URL Routes

| URL | View | Description |
|---|---|---|
| `/` | `home` | Landing page |
| `/register/` | `register` | User registration |
| `/login/` | `LoginView` | User login |
| `/dashboard/` | `dashboard` | User dashboard |
| `/notes/` | `notes_list` | View all notes |
| `/notes/new/` | `note_create` | Create a new note |
| `/summarizer/` | `summarizer` | AI-powered summarizer |
| `/quiz/` | `quiz_generator` | Generate quiz from notes |
| `/flashcards/` | `flashcard_lab` | Interactive flashcard lab |
| `/concept-explainer/` | `concept_explainer` | AI concept explainer |
| `/progress/` | `learning_progress` | View learning progress |

---

## 🔒 Security Notes

- **Never commit your `.env` file** — it's in `.gitignore` ✅
- Change `SECRET_KEY` to a strong, random value in production
- Set `DEBUG=False` in production
- Restrict `ALLOWED_HOSTS` to your domain in production

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

<div align="center">Made with ❤️ using Django and Google Gemini</div>
