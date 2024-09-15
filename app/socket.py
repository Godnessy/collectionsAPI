from app import socketio

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

def send_notification(user_id, notification):
    socketio.emit('new_notification', notification, room=user_id)