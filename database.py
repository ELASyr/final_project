import sqlite3
from flask import g
import os

DATABASE = 'tilbil.db'

def get_db():
    from flask import current_app
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            native_language TEXT DEFAULT 'English',
            learning_goal TEXT DEFAULT 'Daily conversation',
            app_language TEXT DEFAULT 'English',
            avatar TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS user_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            words_learned INTEGER DEFAULT 0,
            day_streak INTEGER DEFAULT 0,
            lessons_done INTEGER DEFAULT 0,
            study_time_minutes INTEGER DEFAULT 0,
            game_points INTEGER DEFAULT 0,
            current_level TEXT DEFAULT 'Beginner',
            progress_percent INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            description TEXT,
            level TEXT DEFAULT 'Intermediate',
            cover_color TEXT DEFAULT '#6B48FF',
            total_pages INTEGER DEFAULT 100,
            chapter_count INTEGER DEFAULT 10
        );

        CREATE TABLE IF NOT EXISTS learning_modules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            level TEXT NOT NULL,
            level_order INTEGER DEFAULT 1,
            locked INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS user_module_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            module_id INTEGER,
            completed INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (module_id) REFERENCES learning_modules(id)
        );

        CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kyrgyz TEXT NOT NULL,
            english TEXT NOT NULL,
            category TEXT,
            level TEXT DEFAULT 'Beginner'
        );
    ''')

    # Seed books
    books_exist = cursor.execute('SELECT COUNT(*) FROM books').fetchone()[0]
    if books_exist == 0:
        cursor.executemany('INSERT INTO books (title, author, description, level, cover_color, total_pages, chapter_count) VALUES (?,?,?,?,?,?,?)', [
            ('Jamila', 'Chyngyz Aitmatov', 'A timeless love story set in wartime Kyrgyzstan — one of the most translated Soviet-era novels.', 'Intermediate', '#2D6A4F', 148, 12),
            ('The White Ship', 'Chyngyz Aitmatov', 'A poetic tale of a boy in the Tian Shan mountains who finds refuge in fairy tales.', 'Advanced', '#1B4F72', 192, 16),
            ('Manas Epic', 'Traditional', 'The world\'s longest epic poem — the national saga of the Kyrgyz people spanning 500,000 lines.', 'Advanced', '#7B341E', 500, 40),
            ('Mother\'s Field', 'Chyngyz Aitmatov', 'A moving story about a woman\'s sacrifice and devotion during WWII.', 'Intermediate', '#5C4033', 120, 10),
        ])

    # Seed learning modules
    modules_exist = cursor.execute('SELECT COUNT(*) FROM learning_modules').fetchone()[0]
    if modules_exist == 0:
        cursor.executemany('INSERT INTO learning_modules (title, level, level_order, locked) VALUES (?,?,?,?)', [
            ('Greetings & Introductions', 'Beginner', 1, 0),
            ('Numbers & Counting', 'Beginner', 1, 0),
            ('Family Members', 'Beginner', 1, 0),
            ('Colors & Shapes', 'Beginner', 1, 0),
            ('Daily Routines', 'Pre-Intermediate', 2, 0),
            ('Shopping & Money', 'Pre-Intermediate', 2, 0),
            ('Directions & Places', 'Pre-Intermediate', 2, 0),
            ('Weather & Seasons', 'Pre-Intermediate', 2, 0),
            ('Business Communication', 'Intermediate', 3, 0),
            ('Cultural Traditions', 'Intermediate', 3, 0),
            ('Literature & Poetry', 'Intermediate', 3, 1),
            ('Advanced Grammar', 'Intermediate', 3, 1),
        ])

    # Seed vocabulary
    vocab_exist = cursor.execute('SELECT COUNT(*) FROM vocabulary').fetchone()[0]
    if vocab_exist == 0:
        cursor.executemany('INSERT INTO vocabulary (kyrgyz, english, category, level) VALUES (?,?,?,?)', [
            ('Салам', 'Hello', 'Greetings', 'Beginner'),
            ('Рахмат', 'Thank you', 'Greetings', 'Beginner'),
            ('Кечиресиз', 'Excuse me / Sorry', 'Greetings', 'Beginner'),
            ('Суу', 'Water', 'Nouns', 'Beginner'),
            ('Тамак', 'Food', 'Nouns', 'Beginner'),
            ('Үй', 'House', 'Nouns', 'Beginner'),
            ('Дос', 'Friend', 'Nouns', 'Beginner'),
            ('Тоо', 'Mountain', 'Nature', 'Beginner'),
            ('Кыргызстан', 'Kyrgyzstan', 'Geography', 'Beginner'),
            ('Ата', 'Father', 'Family', 'Beginner'),
            ('Апа', 'Mother', 'Family', 'Beginner'),
            ('Бала', 'Child', 'Family', 'Beginner'),
        ])

    db.commit()
    db.close()
    print(" Database initialized!")
