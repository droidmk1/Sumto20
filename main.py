from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, send, join_room, leave_room, emit
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
socketio = SocketIO(app)

# Mantener un registro de usuarios por sala
rooms = {}

# Mantener un registro de la suma del juego por sala
game_sums = {}

# Mantener un registro de cuál jugador tiene el turno
player_turn = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat/<room>/<username>')
def chat(room, username):
    return render_template('chat.html', room=room, username=username)

@socketio.on('join')
def handle_join(data):
    room = data['room']
    username = data['username']

    if room and username:
        join_room(room)
        send(f'Usuario {username} se ha unido a la sala {room}.', room=room)

        if room not in rooms:
            rooms[room] = []
            game_sums[room] = 0
            player_turn[room] = username

        rooms[room].append(username)
        users_in_room = rooms[room]
        emit('user_list', users_in_room, room=room)
        emit('player_turn', player_turn[room], room=room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    message = data['message']
    username = data['username']

    if room and message and username:
        if game_sums[room] >= 20:
            send('¡Juego terminado! ' + username + ' es el ganador.', room=room)
            return

        if username == player_turn[room]:
            # Intenta convertir el mensaje en un número
            try:
                num_jugador = int(message)
                if num_jugador < 1 or num_jugador > 3:
                    send('Debes ingresar un número entre 1 y 3.', room=room)
                    return
                if game_sums[room] + num_jugador <= 20:
                    game_sums[room] += num_jugador
                    send(f'{username} ingresó {num_jugador}, suma: {game_sums[room]}', room=room)
                    if game_sums[room] == 20:
                        send('¡Juego terminado! ' + username + ' es el ganador.', room=room)
                    else:
                        # Cambiar el turno al otro jugador
                        player_turn[room] = [user for user in rooms[room] if user != username][0]
                        emit('player_turn', player_turn[room], room=room)
                else:
                    send('No puedes sumar más de 20.', room=room)
            except ValueError:
                send('Debes ingresar un número válido.', room=room)
        else:
            send('Espera tu turno para jugar.', room=room)

# Función para generar un código único de 6 dígitos
def generate_unique_code():
    return ''.join(random.choices('0123456789', k=6))

if __name__ == '__main__':
    # configuracion solo para subir al servidor
    app.run(host='0.0.0.0', port=8080)