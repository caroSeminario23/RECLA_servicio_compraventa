from flask import Flask
from flask_cors import CORS
from utils.db import db
import os

from flask_sqlalchemy import SQLAlchemy
from config import DATABASE_CONNECTION

from services.producto import producto_routes
from services.venta import venta_routes

app = Flask(__name__)

CORS(
    app, 
    origins = ['http://localhost:*', 'http://127.0.0.1:*'], #dirección del front-end
    methods = ['GET', 'POST', 'PUT', 'DELETE'],
    allow_headers = ['Content-Type', 'Authorization']
)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_CONNECTION

db.init_app(app)

app.register_blueprint(producto_routes, url_prefix='/producto_routes')
app.register_blueprint(venta_routes, url_prefix='/venta_routes')

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', debug=True, port=port)