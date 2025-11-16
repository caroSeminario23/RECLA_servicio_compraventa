from utils.db import db
from sqlalchemy.dialects.postgresql import JSONB

class Chat(db.Model):
    __tablename__ = 'chat'

    id_chat = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    id_usuario_1 = db.Column(
        db.Integer,
        nullable=True
    )

    id_usuario_2 = db.Column(
        db.Integer,
        nullable=True
    )

    mensajes = db.Column(
        JSONB,
        nullable=True
    )

    #Objeto
    def __init__(
            self,
            id_usuario_1,
            id_usuario_2,
            mensajes):
        self.id_usuario_1 = id_usuario_1
        self.id_usuario_2 = id_usuario_2
        self.mensajes = mensajes
