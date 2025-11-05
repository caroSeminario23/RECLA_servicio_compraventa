from flask import Blueprint, request, jsonify, make_response
from utils.db import db
from models.chat import Chat
from sqlalchemy import or_
from sqlalchemy.orm.attributes import flag_modified
import datetime


chat_routes = Blueprint('chat_routes', __name__)

# Ruta para obtener historial (POST)
@chat_routes.route('/chat_historial', methods=['POST'])
def obtener_historial():
    data = request.get_json()
    id_usuario_1 = data.get('id_usuario_1')
    id_usuario_2 = data.get('id_usuario_2')

    if not id_usuario_1 or not id_usuario_2:
        return make_response(jsonify({
            "message": "Faltan IDs de usuario (id_usuario_1, id_usuario_2)",
            "status": 400
        }))

    # 2. Llama a la función local directamente
    messages = obtener_mensaje_entre_usuarios(id_usuario_1, id_usuario_2)
    print(f"Respuesta (Historial): {messages}")
    return jsonify(messages), 200

# Ruta para enviar mensaje
@chat_routes.route('/enviar_mensaje', methods=['POST'])
def enviar_mensaje():
    data = request.get_json()
    print(f"Body recibido: {data}")

    id_usuario_1 = data.get('id_usuario_1')
    id_usuario_2 = data.get('id_usuario_2')
    mensaje = data.get('mensaje')

    if not id_usuario_1 or not id_usuario_2 or not mensaje:
        return make_response(jsonify({
            "message": "Datos incompletos (id_usuario_1, id_usuario_2, mensaje)",
            "status": 400
        }))
    
    if id_usuario_1 == id_usuario_2:
        return make_response(jsonify({
            "message": "Los IDs de usuario no pueden ser iguales",
            "status": 400
        }))

    # 2. Llama a la función local directamente
    new_message = agregar_mensaje(id_usuario_1, id_usuario_2, mensaje)

    if new_message:
        return make_response(jsonify({
            "message": "Mensaje enviado correctamente",
            "status": 201
        }))

        #return jsonify(new_message), 201
    else:
        return make_response(jsonify({
            "message": "No se pudo guardar el mensaje",
            "status": 500
        })) 
    
#Obtener mensajes entre dos usuarios

def obtener_mensaje_entre_usuarios(id_usuario_1, id_usuario_2):

    chat = chat_entre_2_usuarios(id_usuario_1, id_usuario_2)
    
    if chat and chat.mensajes:
        return chat.mensajes
    else:
        return []

#Agregar mensaje entre dos usuarios o crear nuevo chat
def agregar_mensaje(id_usuario_1, id_usuario_2, mensaje):
    
    # 1. Busca la sesión de chat existente
    chat = chat_entre_2_usuarios(id_usuario_1, id_usuario_2)
    
    # 2. Define la estructura del nuevo mensaje
    hora_peruana = datetime.datetime.utcnow() - datetime.timedelta(hours=5)
    new_message_data = {
        "id_usuario": id_usuario_1,
        "mensaje": mensaje,
        "fecha_hora": hora_peruana.isoformat()
    }
    
    try:
        if chat:
            # 3a. Si el chat existe, agrega el mensaje al JSONB
            if chat.mensajes is None:
                chat.mensajes = [new_message_data]
            else:
                updated_messages = list(chat.mensajes)
                updated_messages.append(new_message_data)
                chat.mensajes = updated_messages
        else:
            # 3b. Si el chat no existe, crea una nueva instancia
            chat = Chat(
                id_usuario_1=id_usuario_1,
                id_usuario_2=id_usuario_2,
                mensajes=[new_message_data]
            )
            db.session.add(chat)
            
        # 4. Guarda los cambios
        db.session.commit()
        return new_message_data
        
    except Exception as e:
        db.session.rollback()
        return make_response(jsonify({
            "message": f"Error al agregar mensaje: {e}",
            "status": 500
        }))

# Función auxiliar para encontrar un chat entre dos usuarios
def chat_entre_2_usuarios(id_usuario_1, id_usuario_2):
    chat_session = Chat.query.filter(
        or_(
            (Chat.id_usuario_1 == id_usuario_1) & (Chat.id_usuario_2 == id_usuario_2),
            (Chat.id_usuario_1 == id_usuario_2) & (Chat.id_usuario_2 == id_usuario_1)
        )
    ).first()
    
    return chat_session

# Ruta para obtener el último mensaje de cada conversación de un usuario
@chat_routes.route('/mis_conversaciones', methods=['POST'])
def obtener_ultimo_mensaje():
    data = request.get_json()
    id_usuario = data.get('id_usuario')

    if not id_usuario:
        return make_response(jsonify({
            "message": "Falta el ID del usuario (id_usuario)",
            "status": 400
        }), 400)

    try:
        # Busca todos los chats donde el usuario participa
        chats = Chat.query.filter(
            or_(
                Chat.id_usuario_1 == id_usuario,
                Chat.id_usuario_2 == id_usuario
            )
        ).all()

        if not chats:
            return make_response(jsonify({
                "message": "No se encontraron chats para este usuario",
                "status": 404
            }), 404)

        # Obtiene el último mensaje de cada chat
        ultimos_mensajes = []
        for chat in chats:
            if chat.mensajes:
                ultimo_mensaje = chat.mensajes[-1]  # Último mensaje en el JSONB
                ultimos_mensajes.append({
                    "id_chat": chat.id,
                    "id_usuario_1": chat.id_usuario_1,
                    "id_usuario_2": chat.id_usuario_2,
                    "ultimo_mensaje": ultimo_mensaje
                })

        return make_response(jsonify({
            "message": "Últimos mensajes obtenidos correctamente",
            "status": 200,
            "data": ultimos_mensajes
        }), 200)

    except Exception as e:
        return make_response(jsonify({
            "message": f"Error al obtener los últimos mensajes: {e}",
            "status": 500
        }), 500)