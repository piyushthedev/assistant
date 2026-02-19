import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_socketio import SocketIO, emit


from gtts import gTTS
import os
import datetime
import time
import webbrowser
import wikipedia
import requests
import threading
import ai_service
import base64
import io
from PIL import Image
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from models import db, User, Message, init_db

app = Flask(__name__)
app.config.from_object(Config)


init_db(app)

# Increase max http buffer size for images (10MB)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet', max_http_buffer_size=1e7)

# --- CONFIG ---
WAKE_WORD = Config.WAKE_WORD
LISTEN_LANG = Config.LISTEN_LANG
SPEAK_LANG = Config.SPEAK_LANG

# --- HELPER FUNCTIONS ---

def save_message_to_db(user_id, role, text, image=None):
    """Saves a message to SQLite."""
    if not user_id:
        return
    
    try:
        new_msg = Message(user_id=user_id, role=role, text=text, image=image)
        db.session.add(new_msg)
        db.session.commit()
    except Exception as e:
        print(f"DB Save Error: {e}")

def process_image_data(image_data):
    """Decodes base64 image data to PIL Image."""
    if not image_data:
        return None
    try:
        if "," in image_data:
            image_data = image_data.split(",")[1]
        image_bytes = base64.b64decode(image_data)
        return Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        print(f"Image Error: {e}")
        return None

# --- ROUTES ---

@app.route('/')
def index():
    # Render index.html (which handles auth logic)
    return render_template('index.html', email=session.get('email'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            if check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['email'] = email
                flash("Logged in successfully!", "success")
                return redirect(url_for('index'))
            else:
                flash("Incorrect password.", "error")
        else:
            flash("User not found.", "error")
            
    # On GET or failure, render index (login view is default)
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        
        if password != confirm:
            flash("Passwords do not match.", "error")
            # Redirect to index with signup anchor to show form
            return redirect(url_for('index') + '#signup')

        # Check exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash("Email already registered.", "error")
            return redirect(url_for('index') + '#signup')
        
        # Create
        hashed = generate_password_hash(password)
        new_user = User(email=email, password=hashed)
        db.session.add(new_user)
        db.session.commit()
        
        flash("Account created! Please log in.", "success")
        return redirect(url_for('login'))
        
    return redirect(url_for('index') + '#signup')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/history')
def get_history():
    if not session.get('user_id'):
        return jsonify([])
    
    try:
        uid = session['user_id']
        msgs = Message.query.filter_by(user_id=uid).order_by(Message.timestamp.asc()).limit(50).all()
        
        history = []
        for m in msgs:
            history.append({
                'role': m.role,
                'text': m.text,
                'image': m.image
            })
        return jsonify(history)
    except Exception as e:
        print(f"History Error: {e}")
        return jsonify([])

# --- SOCKET ---

def speak(text, emit_ui=True):
    print(f"Assistant: {text}")
    
    audio_data = None
    try:
        tts = gTTS(text=text, lang=SPEAK_LANG, slow=False)
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        audio_base64 = base64.b64encode(audio_fp.read()).decode('utf-8')
        audio_data = f"data:audio/mp3;base64,{audio_base64}"
    except Exception as e:
        print(f"TTS Error: {e}")

    payload = {'status': 'SPEAKING'}
    if emit_ui:
        payload['text'] = text
    if audio_data:
        payload['audio'] = audio_data
        
    socketio.emit('status_update', payload)


def execute_command(command, image_data=None, user_id=None, reply_audio=False):
    if not command and not image_data:
        return

    # Save User Msg
    if user_id:
        save_message_to_db(user_id, 'user', command, image_data)

    socketio.emit('status_update', {'status': 'THINKING', 'text': command})
    
    # Check local commands
    if not image_data:
        command_lower = command.lower()
        if 'time' in command_lower:
            current_time = datetime.datetime.now().strftime('%I:%M %p')
            response_text = f"Abhi samay hai {current_time}"
            
            # Emit text
            socketio.emit('status_update', {'status': 'SPEAKING', 'text': response_text})
            
            if reply_audio:
                speak(response_text, emit_ui=False)
            else:
                socketio.emit('status_update', {'status': 'IDLE'})
                
            if user_id: save_message_to_db(user_id, 'bot', response_text)
            return
    
    # Gemini (via AI Service)
    image_obj = process_image_data(image_data)
    answer = ai_service.get_response(command, image=image_obj)
    
    if answer:
        if user_id: save_message_to_db(user_id, 'bot', answer)
        formatted = answer.replace("*", "")
        socketio.emit('status_update', {'status': 'SPEAKING', 'text': answer})
        socketio.sleep(0)
        
        if reply_audio:
            speak(formatted, emit_ui=False)
        else:
            # If not speaking, we still validly 'spoke' via text, so set IDLE
            socketio.emit('status_update', {'status': 'IDLE'})
    else:
        if reply_audio:
            speak("Maaf kijiye.")
        else:
             socketio.emit('status_update', {'status': 'IDLE'})

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('text_input')
def handle_text_input(data):
    print(f"DEBUG: Received text_input: {data}")
    text = data.get('text', '')
    image = data.get('image')
    source = data.get('source', 'text') # Default to text
    tts_enabled = data.get('tts_enabled', False)
    user_id = session.get('user_id') 
    
    if text or image:
        # Reply with audio if source was voice OR tts toggle is on
        reply_audio = (source == 'voice') or tts_enabled
        execute_command(text, image, user_id, reply_audio=reply_audio)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database initialized.")
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)
