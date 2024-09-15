from app import socketio
from flask import request
from flask_socketio import join_room, leave_room

connected_users = {}

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    user_id = connected_users.get(request.sid)
    if user_id:
        leave_room(user_id)
        del connected_users[request.sid]
    print('Client disconnected')

@socketio.on('register')
def handle_register(data):
    user_id = data['user_id']
    connected_users[request.sid] = user_id
    join_room(user_id)
    print(f'User {user_id} registered')

def send_live_notification(user_id, notification):
    print(f"Sending notification to user {user_id}: {notification}")
    socketio.emit('new_notification', notification, room=user_id)

def is_user_active(user_id):
    return str(user_id) in connected_users.values()