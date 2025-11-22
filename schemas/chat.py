from utils.ma import ma
from marshmallow import fields, validates, ValidationError
from models.chat import Chat

class ChatMensajeSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Chat
        fields = (
            'id_usuario_1',
            'id_usuario_2',
            'mensajes',
            'id_producto'
        )

#Instancia de schemas
chat_mensaje_schema = ChatMensajeSchema()
chat_mensaje_schemas = ChatMensajeSchema(many=True)
