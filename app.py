from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
import os  # <--- Importante para leer variables de entorno
import psycopg2
import psycopg2.extras

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'clave-secreta-sistema-2024'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=2)

CORS(app, resources={r"/api/*": {"origins": "*"}})

jwt = JWTManager(app)

def get_db():
    database_url = os.environ.get(
        'DATABASE_URL', 
        'postgresql://postgres:011124@localhost:5432/PARCIAL_DB'
    )
    return psycopg2.connect(database_url, cursor_factory=psycopg2.extras.RealDictCursor)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({'error': 'Credenciales requeridas'}), 400

    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, username, nombre_completo FROM usuarios WHERE username=%s AND password=%s",
                (username, password)
            )
            user = cur.fetchone()
        conn.close()
    except Exception as e:
        return jsonify({'error': f'Error de base de datos: {str(e)}'}), 500

    if not user:
        return jsonify({'error': 'Usuario o contraseña incorrectos'}), 401

    token = create_access_token(identity=user['username'])
    return jsonify({
        'token': token,
        'nombre': user['nombre_completo'],
        'username': user['username']
    }), 200

@app.route('/api/producto/<codigo>', methods=['GET'])
@jwt_required()
def buscar_producto(codigo):
    try:
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM productos WHERE codigo=%s", (codigo,))
            producto = cur.fetchone()
        conn.close()
    except Exception as e:
        return jsonify({'error': f'Error de base de datos: {str(e)}'}), 500

    if not producto:
        return jsonify({'error': f'Producto con código "{codigo}" no encontrado'}), 404

    return jsonify(producto), 200

@app.route('/api/logout', methods=['POST'])
@jwt_required()
def logout():
    return jsonify({'message': 'Sesión cerrada correctamente'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)