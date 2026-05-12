# Tilbil — Learn Kyrgyz

> An interactive web platform for learning the Kyrgyz language through structured lessons, games, classic literature, and cultural context.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

---

## The Problem

Kyrgyz is spoken by over 5 million people, yet there is almost no modern, accessible digital tool to learn it. Existing language apps do not support Kyrgyz at all, or offer only basic phrasebooks with no cultural depth. Learners who want to connect with the language — whether for heritage, travel, or academic reasons — have nowhere to start.

**Tilbil** fills that gap.

---

## What Tilbil Does

Tilbil is a full-stack web application that guides learners from complete beginner to intermediate Kyrgyz through five interconnected modules:

| Module | What it offers |
|---|---|
| **Dashboard** | Personalised learning plan, daily tasks, progress tracking |
| **Practice** | Flashcards, vocabulary sets, writing drills, grammar lessons, topic quizzes |
| **Games** | Vocabulary Race (timed), Picture Matching — earn XP, climb the leaderboard |
| **Literature** | Read Chyngyz Aitmatov and the Epic of Manas with click-to-translate words and cultural notes |
| **Dialect Translator** | Translate between Standard Kyrgyz and 5 regional dialects (Түштүк, Талас, Ысык-Көл, Нарын, Чүй) |
| **Account** | Profile management, avatar upload, password change, language preference |

---

## Live Demo

>**Classmate feedback**
[![Watch feedback](https://img.youtube.com/vi/mr2FmbqG6wk/maxresdefault.jpg)](https://youtu.be/mr2FmbqG6wk)
---


## Architecture

```
┌─────────────────────────────────────────┐
│              Client (Browser)            │
│    HTML5 · CSS3 · Vanilla JavaScript     │
└────────────────┬────────────────────────┘
                 │  HTTP (GET / POST / JSON)
┌────────────────▼────────────────────────┐
│           Flask Server (app.py)          │
│   Routing · Session auth · REST API     │
└────────────────┬────────────────────────┘
                 │  sqlite3 (Python stdlib)
┌────────────────▼────────────────────────┐
│         SQLite Database (tilbil.db)      │
│  users · user_stats · vocabulary · ...  │
└─────────────────────────────────────────┘
```

### Request flow
1. User makes a request from the browser
2. Flask route handles authentication via `session['user_id']`
3. Route queries SQLite, renders a Jinja2 template or returns JSON
4. Browser renders the response; JS handles interactivity client-side

---

## Features & Functionality

### Authentication
- Register with first name, last name, email, password (hashed with Werkzeug)
- Login / logout with Flask session management
- Google OAuth login (optional)
- Flash messages for validation errors

### Dashboard
- Personalised plan setup (7-question onboarding quiz)
- Recommends Light / Standard / Deep track based on answers
- Today's tasks, weekly activity chart, level progress bar

### Practice
- **Flashcards** — 10 cards with photos, pronunciation, example sentences. Flip animation, rate each card (Got it / Didn't know / Skip)
- **Learn by heart** — 5 themed word sets (Greetings, Family, Nature, Food, Numbers)
- **Writing drill** — translate 8 English sentences into Kyrgyz, auto-checked
- **Grammar** — 4 lessons (Greetings, Plurals, Dative case, Pronouns) each with examples and a mini quiz
- **Topic quizzes** — Family, Shopping, Weather, Directions (7–8 questions each, shuffled)
- **Dialect translator** — local dictionary of 35+ dialect words across 5 regions, with fallback to Claude AI API

### Games
- **Vocabulary Race** — 30-second timed translation game, colour-coded timer bar, XP posted to leaderboard
- **Picture Matching** — match real Unsplash photos to Kyrgyz words
- **Leaderboard** — weekly XP rankings with highlighted current user row

### Literature
- 6 books (Jamila, The White Ship, Epic of Manas, Mother's Field, First Stories, The Scaffold)
- Each book has unique Kyrgyz text with colour-coded clickable words (verb / noun / adjective)
- Word tooltip shows translation, pronunciation, grammar type, and an example sentence
- Audio companion panel, cultural context, vocabulary list, key terms — all per book
- Chapter navigation, progress bar, font size toggle, keyboard shortcuts

### Account
- Avatar upload (JPG/PNG, max 5 MB, stored on server)
- Edit name, native language, learning goal
- Change password with strength indicator
- App language switcher (English / Russian / Kyrgyz) with flag icons
- Progress summary (words, lessons, streak, level bar)
- Account deletion

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10+, Flask 3.0 |
| Database | SQLite 3 (Python `sqlite3` stdlib — no ORM) |
| Auth | Flask sessions, Werkzeug password hashing |
| Frontend | HTML5, CSS3, Vanilla JavaScript (no frameworks) |
| Fonts | Google Fonts — Inter, DM Serif Display |
| Images | Unsplash (free CDN links) |
| AI API | Anthropic Claude (dialect translator fallback) |
| File storage | Local filesystem (`static/uploads/avatars/`) |

---

## Database Schema

```sql
users
  id, first_name, last_name, email, password,
  native_language, learning_goal, app_language,
  avatar, mascot_gender, created_at

user_stats
  user_id, words_learned, day_streak, lessons_done,
  study_time_minutes, game_points,
  current_level, progress_percent

books
  id, title, author, description,
  level, cover_color, total_pages, chapter_count

learning_modules
  id, title, level, level_order, locked

user_module_progress
  user_id, module_id, completed

vocabulary
  id, kyrgyz, english, category, level
```

---

## Setup & Run

### Prerequisites
- Python 3.10 or higher
- Git

### 1 — Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/tilbil.git
cd tilbil
```

### 2 — Create a virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac / Linux
python -m venv venv
source venv/bin/activate
```

### 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### 4 — Set environment variables

Create a `.env` file in the project root:
```
SECRET_KEY=your-secret-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here
```

### 5 — Run the app
```bash
python app.py
```

### 6 — Open in browser
```
http://127.0.0.1:5000
```

The SQLite database (`tilbil.db`) is created and seeded automatically on first run.

---

## Project Structure

```
tilbil/
├── app.py                  # Flask routes, session logic, API endpoints
├── database.py             # DB init, schema, seed data
├── requirements.txt        # Python dependencies
├── .env                    # Secret keys (not committed)
├── .gitignore
├── README.md
├── tilbil.db               # SQLite database (auto-created, not committed)
│
├── static/
│   ├── css/
│   │   └── style.css       # Global styles
│   └── uploads/
│       └── avatars/        # User avatar uploads (not committed)
│
└── templates/
    ├── base.html           # Shared navbar, layout, flash messages
    ├── landingpage.html    # Public landing page
    ├── login.html          # Sign in
    ├── register.html       # Create account
    ├── dashboard.html      # Main dashboard + onboarding plan
    ├── games.html          # Games + leaderboard
    ├── literature.html     # Book reader
    ├── practice.html       # Flashcards, quizzes, translator
    └── account.html        # Profile, security, settings
```

---

## API Endpoints

| Method | Route | Description |
|---|---|---|
| `POST` | `/api/translate` | Dialect translator (Claude fallback) |
| `POST` | `/api/add_points` | Add game XP to user stats |
| `POST` | `/api/complete_module` | Mark a learning module as done |
| `POST` | `/account` | Profile / password / avatar / language update |

---

## Key Technical Decisions

**No ORM** — raw `sqlite3` was chosen over SQLAlchemy to keep the dependency footprint small and make the SQL explicit and readable for a learning project.

**No JS framework** — all interactivity (modals, flashcard flip, quiz logic, dialect translator) is built in vanilla JS to demonstrate DOM mastery without abstractions.

**Inline SVGs over icon libraries** — every icon in the UI is a hand-written SVG path, keeping the bundle zero-dependency and pixel-perfect at any size.

**Local file storage** — avatar uploads are stored on the local filesystem rather than a cloud bucket to keep the setup simple and self-contained.

---

## Author

**Elaman Abdulloev**
AUCA — Web Programming Final Project · Spring 2026