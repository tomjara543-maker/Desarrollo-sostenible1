from flask import Flask, request, jsonify, send_from_directory
import sqlite3
from datetime import datetime

app = Flask(__name__, static_folder='static')

def get_db():
    return sqlite3.connect('inventario.db')

def init_db():
    conn = get_db()
    c = conn.cursor()

    # tabla productos
    c.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            cantidad INTEGER,
            precio REAL
        )
    ''')

    # tabla historial
    c.execute('''
        CREATE TABLE IF NOT EXISTS historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            accion TEXT,
            producto TEXT,
            fecha TEXT
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# ---------------- PRODUCTOS ----------------

@app.route('/productos', methods=['GET'])
def get_productos():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM productos')
    data = c.fetchall()
    conn.close()
    return jsonify(data)

@app.route('/productos', methods=['POST'])
def add_producto():
    data = request.json
    conn = get_db()
    c = conn.cursor()

    c.execute('INSERT INTO productos (nombre, cantidad, precio) VALUES (?, ?, ?)',
              (data['nombre'], data['cantidad'], data['precio']))

    # historial
    c.execute('INSERT INTO historial (accion, producto, fecha) VALUES (?, ?, ?)',
              ('Agregado', data['nombre'], datetime.now().strftime("%Y-%m-%d")))

    conn.commit()
    conn.close()
    return jsonify({'mensaje': 'ok'})

@app.route('/productos/<int:id>', methods=['PUT'])
def update_producto(id):
    data = request.json
    conn = get_db()
    c = conn.cursor()

    c.execute('UPDATE productos SET nombre=?, cantidad=?, precio=? WHERE id=?',
              (data['nombre'], data['cantidad'], data['precio'], id))

    # historial
    c.execute('INSERT INTO historial (accion, producto, fecha) VALUES (?, ?, ?)',
              ('Editado', data['nombre'], datetime.now().strftime("%Y-%m-%d")))

    conn.commit()
    conn.close()
    return jsonify({'mensaje': 'actualizado'})

@app.route('/productos/<int:id>', methods=['DELETE'])
def delete_producto(id):
    conn = get_db()
    c = conn.cursor()

    c.execute('DELETE FROM productos WHERE id=?', (id,))

    # historial
    c.execute('INSERT INTO historial (accion, producto, fecha) VALUES (?, ?, ?)',
              ('Eliminado', f'ID {id}', datetime.now().strftime("%Y-%m-%d")))

    conn.commit()
    conn.close()
    return jsonify({'mensaje': 'eliminado'})

# ---------------- HISTORIAL ----------------

@app.route('/historial')
def historial():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM historial ORDER BY id DESC')
    data = c.fetchall()
    conn.close()
    return jsonify(data)

# ---------------- REPORTES ----------------

@app.route('/reportes')
def reportes():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        SELECT fecha, COUNT(*)
        FROM historial
        WHERE accion='Agregado'
        GROUP BY fecha
    """)

    data = c.fetchall()
    conn.close()
    return jsonify(data)

# ---------------- LOGIN ----------------

@app.route('/login')
def login():
    return send_from_directory('static', 'login.html')

@app.route('/login', methods=['POST'])
def validar():
    data = request.json

    if data['usuario'] == 'admin' and data['password'] == '123':
        return jsonify({'status': 'ok'})
    else:
        return jsonify({'status': 'error'})

# ---------------- VISTAS ----------------

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/inventario')
def inventario():
    return send_from_directory('static', 'inventario.html')

if __name__ == '__main__':
    app.run(debug=True)