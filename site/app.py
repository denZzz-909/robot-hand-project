from flask import Flask, render_template, redirect, request, url_for
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'

# Включаем логирование для отладки WebSocket-соединений
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

URL_TO_STATE = {
    "compressed": "сжато",
    "expanded": "разжато",
    # Поддержка старых значений в URL
    "сжато": "сжато",
    "разжато": "разжато",
}
STATE_TO_URL = {
    "сжато": "compressed",
    "разжато": "expanded",
}

current_state = "сжато"

def update_state(new_state):
    global current_state
    if new_state == current_state:
        return
    current_state = new_state
    print(f"🔄 Состояние изменено на: {current_state} | Рассылаю всем клиентам...")
    socketio.emit('state_update', {'state': current_state})

@app.route('/')
def index():
    # Поддержка изменения через адресную строку: /?state=compressed|expanded
    raw_state = (request.args.get('state') or '').strip().lower()
    state_from_url = URL_TO_STATE.get(raw_state, raw_state)
    if state_from_url in ('сжато', 'разжато'):
        update_state(state_from_url)
    return render_template('index.html')

@app.route('/state/<value>')
def set_state_from_url(value):
    # Поддержка короткого URL: /state/compressed или /state/expanded
    raw_state = (value or '').strip().lower()
    new_state = URL_TO_STATE.get(raw_state, raw_state)
    if new_state in ('сжато', 'разжато'):
        update_state(new_state)
    return redirect(url_for('index', state=STATE_TO_URL.get(current_state, current_state)))

@socketio.on('connect')
def handle_connect():
    print(f"🔌 Клиент подключился. Отправляем текущее состояние: {current_state}")
    emit('state_update', {'state': current_state})

@socketio.on('change_state')
def handle_change_state(data):
    raw_state = data.get('state')
    new_state = URL_TO_STATE.get(raw_state, raw_state)
    if new_state in ('сжато', 'разжато'):
        update_state(new_state)

if __name__ == '__main__':
    # ВАЖНО: запускаем ТОЛЬКО через socketio.run, а не app.run или flask run
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)