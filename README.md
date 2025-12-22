# RECLA - MICROSERVICIO COMPRAVENTA

## 1. Descripción del proyecto
RECLA es una plataforma que implementa mecanismos de gamificación para promover la adopción del hábito de reciclaje en los ciudadanos limeños. De esta manera, buscar aportar al logro de las ODS 12 (Producción y consumo responsables) y 13 (Acción por el clima) de la Agenda 2030. En este repositorio se presenta el microservicio **compraventa** (modelos, esquemas, servicios y test).

### Funcionalidades
- Registrar producto
- Buscar productos
- Mostrar producto
- Comprar producto
- Enviar mensaje
- Mostrar historial de mensajes
- Mostrar conversaciones

## 2. Estado del proyecto
![Badge Finalizado](https://img.shields.io/badge/ESTADO-FINALIZADO-yellow)

## 3. Tecnologías utilizadas
![Windows 11](https://img.shields.io/badge/Windows%2011-%230079d5.svg?style=for-the-badge&logo=Windows%2011&logoColor=white)
![Visual Studio Code](https://img.shields.io/badge/Visual%20Studio%20Code-217346.svg?style=for-the-badge&logo=visual-studio-code&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)

## 4. Guía de instalación
1. Clonar el repositorio en su IDE:
    ```
    https://github.com/caroSeminario23/RECLA_servicio_compraventa.git
    ```

2. Si se desea ejecutar en local, descomentar este fragmento de código de **app.py**:
    ```
    if __name__ == '__main__':
        port = int(os.environ.get('PORT', 5002))
        app.run(host='0.0.0.0', debug=False, port=port)
    ```

3. Crear un archivo **.env** y registrar los valores correspondientes (según la estructura plasmada en: **env.txt**).

4. Crear un entorno virtual con virtualvenv y activarlo:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   ```

5. Instalar las dependencias del archivo **requirements.txt**:
   ```
   pip install -r requirements.txt
   ```

5. Para iniciar el microservicio (en localhost) digitar en la terminal: 
   ```
   python app.py
   ```


## 5. Licencia
[![Licencia](https://img.shields.io/github/license/Ileriayo/markdown-badges?style=for-the-badge)](./LICENSE)