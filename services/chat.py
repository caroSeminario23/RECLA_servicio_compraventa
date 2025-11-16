from flask import Blueprint, request, jsonify, make_response
from utils.db import db
from models.chat import Chat
from sqlalchemy import or_
from sqlalchemy.orm.attributes import flag_modified
import datetime
import time
from utils.logger import get_logger
logger = get_logger(__name__)


chat_routes = Blueprint('chat_routes', __name__)

# Ruta para obtener historial (POST)
@chat_routes.route('/chat_historial', methods=['POST'])
def obtener_historial():
    inicio_tiempo = time.time()
    try:
        data = request.get_json()
        id_usuario_1 = data.get('id_usuario_1')
        id_usuario_2 = data.get('id_usuario_2')

        if not id_usuario_1 or not id_usuario_2:
            tiempo_respuesta = time.time() - inicio_tiempo
            logger.error(f"Error chat_historial. Tiempo: {tiempo_respuesta:.2f}s")
            return make_response(jsonify({
                "message": "Faltan IDs de usuario (id_usuario_1, id_usuario_2)",
                "status": 400
            }),400)
        logger.info(f"Solicitando historial entre Usuario 1: {id_usuario_1} y Usuario 2: {id_usuario_2}")

        # 2. Llama a la función local directamente
        messages = obtener_mensaje_entre_usuarios(id_usuario_1, id_usuario_2)
        return jsonify(messages), 200
    except Exception as err:
        tiempo_respuesta = time.time() - inicio_tiempo
        logger.error(f"Error inesperado en chat_historial: {err}. Tiempo: {tiempo_respuesta:.2f}s")
        return make_response(jsonify({
            "message": f"Error procesando la solicitud",
            "status": 500
        }),500)

# Ruta para enviar mensaje
@chat_routes.route('/enviar_mensaje', methods=['POST'])
def enviar_mensaje():
    inicio_tiempo = time.time()
    try:
        data = request.get_json()

        id_usuario_1 = data.get('id_usuario_1')
        id_usuario_2 = data.get('id_usuario_2')
        mensaje = data.get('mensaje')

        if not id_usuario_1 or not id_usuario_2 or not mensaje:
            tiempo_respuesta = time.time() - inicio_tiempo
            logger.error(f"Error validación en enviar_mensaje: Datos incompletos. Tiempo: {tiempo_respuesta:.2f}s")
            return make_response(jsonify({
                "message": "Datos incompletos (id_usuario_1, id_usuario_2, mensaje)",
                "status": 400
            }))
        
        if id_usuario_1 == id_usuario_2:
            tiempo_respuesta = time.time() - inicio_tiempo
            logger.error(f"Error validación en enviar_mensaje: IDs de usuario no pueden ser iguales({id_usuario_1}). Tiempo: {tiempo_respuesta:.2f}s")
            return make_response(jsonify({
                "message": "Los IDs de usuario no pueden ser iguales",
                "status": 400
            }))
        logger.info(f"Intento de enviar mensaje de Usuario 1: {id_usuario_1} a Usuario 2: {id_usuario_2}")

        # 2. Llama a la función local directamente
        new_message = agregar_mensaje(id_usuario_1, id_usuario_2, mensaje)

        if new_message:
            tiempo_respuesta = time.time() - inicio_tiempo
            logger.info(f"Mensaje enviado correctamente de {id_usuario_1} a {id_usuario_2}. Tiempo: {tiempo_respuesta:.2f}s")
            return make_response(jsonify({
                "message": "Mensaje enviado correctamente",
                "status": 201
            }))

            #return jsonify(new_message), 201
        else:
            tiempo_respuesta = time.time() - inicio_tiempo
            logger.error(f"Error al guardar el mensaje entre {id_usuario_1} y {id_usuario_2}(Error de DB). Tiempo: {tiempo_respuesta:.2f}s")
            return make_response(jsonify({
                "message": "No se pudo guardar el mensaje",
                "status": 500
            }))
    except Exception as err:
        tiempo_respuesta = time.time() - inicio_tiempo
        logger.error(f"Error inesperado en enviar_mensaje: {err}. Tiempo: {tiempo_respuesta:.2f}s")
        return make_response(jsonify({
            "message": "Error procesando la solicitud",
            "status": 500
        }), 500)

#Obtener mensajes entre dos usuarios

def obtener_mensaje_entre_usuarios(id_usuario_1, id_usuario_2):
    logger.info(f"[Lógica interna] Obtener mensajes entre Usuario 1: {id_usuario_1} y Usuario 2: {id_usuario_2}")
    chat = chat_entre_2_usuarios(id_usuario_1, id_usuario_2)
    
    if chat and chat.mensajes:
        logger.info(f"[Lógica interna] chat {chat.id_chat} encontrado con {len(chat.mensajes)} mensajes.")
        return chat.mensajes
    else:
        logger.info(f"[Lógica interna] No se encontraron mensajes entre Usuario 1: {id_usuario_1} y Usuario 2: {id_usuario_2}.")
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
            logger.info(f"[Lógica interna] Agregando mensaje al chat existente: {chat.id_chat}")
            if chat.mensajes is None:
                chat.mensajes = [new_message_data]
            else:
                updated_messages = list(chat.mensajes)
                updated_messages.append(new_message_data)
                chat.mensajes = updated_messages
        else:
            # 3b. Si el chat no existe, crea una nueva instancia
            logger.info(f"[Lógica interna] Creando nuevo chat entre Usuario 1: {id_usuario_1} y Usuario 2: {id_usuario_2}")
            chat = Chat(
                id_usuario_1=id_usuario_1,
                id_usuario_2=id_usuario_2,
                mensajes=[new_message_data]
            )
            db.session.add(chat)
            
        # 4. Guarda los cambios
        db.session.commit()
        logger.info(f"[Lógica interna] Mensaje enviado y guardado en DB")
        return new_message_data
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"[Lógica interna] Error al agregar mensaje: {e}")
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
    inicio_tiempo = time.time()
    data = request.get_json()
    id_usuario = data.get('id_usuario')

    if not id_usuario:
        tiempo_respuesta = time.time() - inicio_tiempo
        logger.error(f"Error validación en mis_conversaciones: Falta id_usuario. Tiempo: {tiempo_respuesta:.2f}s")
        return make_response(jsonify({
            "message": "Falta el ID del usuario (id_usuario)",
            "status": 400
        }), 400)

    try:
        # Busca todos los chats donde el usuario participa
        logger.info(f"Obteniendo últimas conversaciones para Usuario: {id_usuario}")
        chats = Chat.query.filter(
            or_(
                Chat.id_usuario_1 == id_usuario,
                Chat.id_usuario_2 == id_usuario
            )
        ).all()

        if not chats:
            tiempo_respuesta = time.time() - inicio_tiempo
            logger.warning(f"No se encontraron chats para el Usuario: {id_usuario}. Tiempo: {tiempo_respuesta:.2f}s")
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
                    "id_chat": chat.id_chat,
                    "id_usuario_1": chat.id_usuario_1,
                    "id_usuario_2": chat.id_usuario_2,
                    "ultimo_mensaje": ultimo_mensaje
                })
        tiempo_respuesta = time.time() - inicio_tiempo
        logger.info(f"Últimos mensajes obtenidos para Usuario: {id_usuario}. Tiempo: {tiempo_respuesta:.2f}s")
        
        return make_response(jsonify({
            "message": "Últimos mensajes obtenidos correctamente",
            "status": 200,
            "data": ultimos_mensajes
        }), 200)

    except Exception as e:
        tiempo_respuesta = time.time() - inicio_tiempo
        logger.error(f"Error inesperado en mis_conversaciones para Usuario: {id_usuario}: {e}. Tiempo: {tiempo_respuesta:.2f}s")
        return make_response(jsonify({
            "message": f"Error al obtener los últimos mensajes: {e}",
            "status": 500
        }), 500)