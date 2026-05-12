from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, g
from database import init_db, get_db
import hashlib
import os
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER  = os.path.join('static', 'uploads', 'avatars')
ALLOWED_EXTS   = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
app.secret_key = 'tilbil-secret-key-2024'

app.jinja_env.globals['enumerate'] = enumerate

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

with app.app_context():
    init_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─── GOOGLE OAUTH SETUP ───────────────────────────────────────────────────────
from authlib.integrations.flask_client import OAuth

# !! PUT YOUR REAL CREDENTIALS HERE DIRECTLY !!
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")

app.config['GOOGLE_CLIENT_ID']     = GOOGLE_CLIENT_ID
app.config['GOOGLE_CLIENT_SECRET'] = GOOGLE_CLIENT_SECRET

oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# ─── AUTH ────────────────────────────────────────────────
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('landingpage.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        raw_password = request.form.get('password', '')
        if not email or not raw_password:
            flash('Please enter your email and password', 'error')
            return render_template('login.html')
        password = hash_password(raw_password)
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email=? AND password=?', (email, password)).fetchone()
        if user:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['first_name']
            session['mascot_gender'] = user['mascot_gender']
            return redirect(url_for('dashboard'))
        flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        raw_password = request.form.get('password', '')
        mascot_gender = 'male'
        native_language = 'English'
        if not first_name or not last_name or not email or not raw_password:
            flash('Please fill in all fields', 'error')
            return render_template('register.html')
        if len(raw_password) < 8:
            flash('Password must be at least 8 characters', 'error')
            return render_template('register.html')
        password = hash_password(raw_password)
        db = get_db()
        existing = db.execute('SELECT id FROM users WHERE email=?', (email,)).fetchone()
        if existing:
            flash('Email already registered', 'error')
            return render_template('register.html')
        db.execute(
            'INSERT INTO users (first_name, last_name, email, password, mascot_gender, native_language) VALUES (?,?,?,?,?,?)',
            (first_name, last_name, email, password, mascot_gender, native_language)
        )
        db.commit()
        new_user = db.execute('SELECT id FROM users WHERE email=?', (email,)).fetchone()
        db.execute(
            'INSERT INTO user_stats (user_id, words_learned, day_streak, lessons_done, study_time_minutes, game_points, current_level, progress_percent) VALUES (?,0,1,0,0,0,"Beginner",0)',
            (new_user['id'],)
        )
        db.commit()
        session.clear()
        session['user_id'] = new_user['id']
        session['username'] = first_name
        session['mascot_gender'] = mascot_gender
        flash('Account created. Welcome to Tilbil!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─── GOOGLE OAUTH ROUTES ─────────────────────────────────────────────────────
@app.route('/auth/google')
def google_login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/google/callback')
def google_callback():
    try:
        token = google.authorize_access_token()
    except Exception as e:
        flash('Google sign-in failed. Please try again.', 'error')
        return redirect(url_for('login'))

    user_info = token.get('userinfo')
    if not user_info:
        flash('Could not get account info from Google.', 'error')
        return redirect(url_for('login'))

    google_email = user_info['email'].strip().lower()
    first_name   = user_info.get('given_name', 'User')
    last_name    = user_info.get('family_name', '')

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email=?', (google_email,)).fetchone()

    if user is None:
        # New user — create account automatically
        db.execute(
            'INSERT INTO users (first_name, last_name, email, password, mascot_gender, native_language) VALUES (?,?,?,?,?,?)',
            (first_name, last_name, google_email, '', 'male', 'English')
        )
        db.commit()
        user = db.execute('SELECT * FROM users WHERE email=?', (google_email,)).fetchone()
        db.execute(
            'INSERT OR IGNORE INTO user_stats (user_id, words_learned, day_streak, lessons_done, study_time_minutes, game_points, current_level, progress_percent) VALUES (?,0,1,0,0,0,"Beginner",0)',
            (user['id'],)
        )
        db.commit()

    session.clear()
    session['user_id']       = user['id']
    session['username']      = user['first_name']
    session['mascot_gender'] = user['mascot_gender']
    return redirect(url_for('dashboard'))

# ─── MAIN PAGES ──────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    user  = db.execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()
    stats = db.execute('SELECT * FROM user_stats WHERE user_id=?', (session['user_id'],)).fetchone()
    return render_template('dashboard.html', user=user, stats=stats)

@app.route('/games')
@login_required
def games():
    db = get_db()
    leaderboard = db.execute(
        '''SELECT u.id as user_id,
           u.first_name || " " || substr(u.last_name,1,1) || "." as name,
           s.game_points as pts
           FROM users u JOIN user_stats s ON u.id=s.user_id
           ORDER BY s.game_points DESC LIMIT 10'''
    ).fetchall()
    user_stats = db.execute('SELECT * FROM user_stats WHERE user_id=?', (session['user_id'],)).fetchone()
    return render_template('games.html', leaderboard=leaderboard, user_stats=user_stats, current_user_id=session['user_id'])
@app.route('/literature')
@login_required
def literature():
    db = get_db()
    books = db.execute('SELECT * FROM books').fetchall()
    return render_template('literature.html', books=books)

@app.route('/practice')
@login_required
def practice():
    db = get_db()
    user     = db.execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()
    modules  = db.execute('SELECT * FROM learning_modules ORDER BY level_order, id').fetchall()
    progress = db.execute('SELECT module_id, completed FROM user_module_progress WHERE user_id=?', (session['user_id'],)).fetchall()
    progress_dict = {p['module_id']: p['completed'] for p in progress}
    stats    = db.execute('SELECT * FROM user_stats WHERE user_id=?', (session['user_id'],)).fetchone()
    return render_template('practice.html', user=user, modules=modules, progress=progress_dict, stats=stats)

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    db = get_db()
    user_id = session['user_id']

    if request.method == 'POST':
        form_type = request.form.get('form_type')

        # AVATAR UPLOAD
        if form_type == 'avatar':
            file = request.files.get('avatar')
            if not file or file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            ext = file.filename.rsplit('.', 1)[-1].lower()
            if ext not in ALLOWED_EXTS:
                return jsonify({'error': 'File type not allowed'}), 400
            file_bytes = file.read()
            if len(file_bytes) > 5 * 1024 * 1024:
                return jsonify({'error': 'Image must be under 5 MB'}), 400
            file.seek(0)
            # delete old avatar file from disk
            old = db.execute('SELECT avatar FROM users WHERE id=?', (user_id,)).fetchone()
            if old and old['avatar']:
                old_path = os.path.join(UPLOAD_FOLDER, old['avatar'])
                if os.path.exists(old_path):
                    os.remove(old_path)
            # save new file
            filename = f"user_{user_id}_{uuid.uuid4().hex[:8]}.{ext}"
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            db.execute('UPDATE users SET avatar=? WHERE id=?', (filename, user_id))
            db.commit()
            return jsonify({'ok': True}), 200

        # SAVE PROFILE
        elif form_type == 'profile':
            db.execute(
                'UPDATE users SET first_name=?, last_name=?, native_language=?, learning_goal=? WHERE id=?',
                (
                    request.form.get('first_name', '').strip(),
                    request.form.get('last_name', '').strip(),
                    request.form.get('native_language', 'English'),
                    request.form.get('learning_goal', ''),
                    user_id
                )
            )
            db.commit()
            flash('Profile updated', 'success')
            return redirect(url_for('account'))

        # CHANGE PASSWORD
        elif form_type == 'password':
            from werkzeug.security import check_password_hash, generate_password_hash
            row = db.execute('SELECT password FROM users WHERE id=?', (user_id,)).fetchone()
            current = request.form.get('current_password', '')
            new     = request.form.get('new_password', '')
            confirm = request.form.get('confirm_password', '')
            if not check_password_hash(row['password'], current):
                flash('Current password is incorrect', 'error')
            elif new != confirm:
                flash('New passwords do not match', 'error')
            elif len(new) < 8:
                flash('Password must be at least 8 characters', 'error')
            else:
                db.execute('UPDATE users SET password=? WHERE id=?',
                           (generate_password_hash(new), user_id))
                db.commit()
                flash('Password updated', 'success')
            return redirect(url_for('account'))

        # SAVE LANGUAGE
        elif form_type == 'language':
            db.execute('UPDATE users SET app_language=? WHERE id=?',
                       (request.form.get('app_language', 'English'), user_id))
            db.commit()
            return jsonify({'ok': True}), 200

        # DELETE ACCOUNT
        elif form_type == 'delete_account':
            row = db.execute('SELECT avatar FROM users WHERE id=?', (user_id,)).fetchone()
            if row and row['avatar']:
                p = os.path.join(UPLOAD_FOLDER, row['avatar'])
                if os.path.exists(p):
                    os.remove(p)
            db.execute('DELETE FROM user_stats WHERE user_id=?', (user_id,))
            db.execute('DELETE FROM users WHERE id=?', (user_id,))
            db.commit()
            session.clear()
            return redirect(url_for('index'))

    # GET — load user and stats from DB
    user  = db.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
    stats = db.execute('SELECT * FROM user_stats WHERE user_id=?', (user_id,)).fetchone()
    return render_template('account.html', user=user, stats=stats)
# ─── API ROUTES ──────────────────────────────────────────
@app.route('/api/translate', methods=['POST'])
@login_required
def translate():
    data = request.json
    text = data.get('text', '').lower().strip()
    translations = {
        'hello': 'Салам', 'thank you': 'Рахмат',
        'good morning': 'Кутман таң', 'good evening': 'Кечиңиз жакшы',
        'how are you': 'Кандайсыз?', 'my name is': 'Менин атым',
        'water': 'Суу', 'food': 'Тамак', 'house': 'Үй',
        'family': 'Үй-бүлө', 'yes': 'Ооба', 'no': 'Жок',
        'friend': 'Дос', 'mountain': 'Тоо', 'beautiful': 'Сулуу',
        'kyrgyzstan': 'Кыргызстан',
    }
    result = translations.get(text, f'[Translation for "{text}" — add more in the database!]')
    return jsonify({'translation': result})

@app.route('/api/complete_module', methods=['POST'])
@login_required
def complete_module():
    data      = request.json
    module_id = data.get('module_id')
    db        = get_db()
    existing  = db.execute(
        'SELECT id FROM user_module_progress WHERE user_id=? AND module_id=?',
        (session['user_id'], module_id)
    ).fetchone()
    if not existing:
        db.execute(
            'INSERT INTO user_module_progress (user_id, module_id, completed) VALUES (?,?,1)',
            (session['user_id'], module_id)
        )
        db.execute(
            'UPDATE user_stats SET words_learned = words_learned + 15 WHERE user_id=?',
            (session['user_id'],)
        )
        db.commit()
    return jsonify({'success': True})

@app.route('/api/add_points', methods=['POST'])
@login_required
def add_points():
    data   = request.json
    points = data.get('points', 0)
    db     = get_db()
    db.execute('UPDATE user_stats SET game_points = game_points + ? WHERE user_id=?', (points, session['user_id']))
    db.commit()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)