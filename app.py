from flask import Flask, request, jsonify, send_from_directory
import sqlite3
from datetime import datetime

app = Flask(__name__, static_folder='static')

# ---------------- BASE DE DATOS ----------------

def get_db():
    return sqlite3.connect('inventario.db')

def init_db():

    conn = get_db()

    c = conn.cursor()

    # TABLA PRODUCTOS
    c.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            cantidad INTEGER,
            precio REAL
        )
    ''')

    # TABLA HISTORIAL
    c.execute('''
        CREATE TABLE IF NOT EXISTS historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            accion TEXT,
            producto TEXT,
            fecha TEXT
        )
    ''')

    # TABLA VENTAS
    c.execute('''
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto TEXT,
            cantidad INTEGER,
            precio REAL,
            total REAL,
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

    c.execute(
        'INSERT INTO productos (nombre, cantidad, precio) VALUES (?, ?, ?)',
        (data['nombre'], data['cantidad'], data['precio'])
    )

    # HISTORIAL
    c.execute(
        'INSERT INTO historial (accion, producto, fecha) VALUES (?, ?, ?)',
        (
            'Agregado',
            data['nombre'],
            datetime.now().strftime("%Y-%m-%d")
        )
    )

    conn.commit()

    conn.close()

    return jsonify({'mensaje': 'ok'})

@app.route('/productos/<int:id>', methods=['PUT'])
def update_producto(id):

    data = request.json

    conn = get_db()

    c = conn.cursor()

    c.execute(
        'UPDATE productos SET nombre=?, cantidad=?, precio=? WHERE id=?',
        (data['nombre'], data['cantidad'], data['precio'], id)
    )

    # HISTORIAL
    c.execute(
        'INSERT INTO historial (accion, producto, fecha) VALUES (?, ?, ?)',
        (
            'Editado',
            data['nombre'],
            datetime.now().strftime("%Y-%m-%d")
        )
    )

    conn.commit()

    conn.close()

    return jsonify({'mensaje': 'actualizado'})

@app.route('/productos/<int:id>', methods=['DELETE'])
def delete_producto(id):

    conn = get_db()

    c = conn.cursor()

    c.execute('DELETE FROM productos WHERE id=?', (id,))

    # HISTORIAL
    c.execute(
        'INSERT INTO historial (accion, producto, fecha) VALUES (?, ?, ?)',
        (
            'Eliminado',
            f'ID {id}',
            datetime.now().strftime("%Y-%m-%d")
        )
    )

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

usuario_actual = None

@app.route('/')
def inicio():
    return send_from_directory('static', 'login.html')

@app.route('/login')
def login():
    return send_from_directory('static', 'login.html')

@app.route('/login', methods=['POST'])
def validar():

    global usuario_actual

    data = request.json

    if data['usuario'] == 'admin' and data['password'] == '123':

        usuario_actual = data['usuario']

        return jsonify({
            'status': 'ok',
            'usuario': usuario_actual
        })

    else:

        return jsonify({
            'status': 'error'
        })

@app.route('/usuario')
def usuario():

    global usuario_actual

    return jsonify({
        'usuario': usuario_actual
    })

# ---------------- INVENTARIO ----------------

@app.route('/inventario')
def inventario():
    return send_from_directory('static', 'inventario.html')
@app.route('/index')
def pagina_inicio():
    return send_from_directory('static', 'index.html')

# ---------------- VENTAS ----------------

@app.route('/ventas', methods=['GET'])
def get_ventas():

    conn = get_db()

    c = conn.cursor()

    c.execute('SELECT * FROM ventas ORDER BY id DESC')

    data = c.fetchall()

    conn.close()

    return jsonify(data)

@app.route('/ventas', methods=['POST'])
def registrar_venta():

    data = request.json

    conn = get_db()

    c = conn.cursor()

    producto = data['producto'].strip()

    cantidad = int(data['cantidad'])

    # BUSCAR PRODUCTO
    c.execute(
        'SELECT id, cantidad, precio FROM productos WHERE TRIM(nombre)=?',
        (producto,)
    )

    resultado = c.fetchone()

    if not resultado:

        conn.close()

        return jsonify({
            'mensaje': 'Producto no existe'
        })

    producto_id = resultado[0]

    stock_actual = resultado[1]

    precio = resultado[2]

    # VALIDAR STOCK
    if cantidad > stock_actual:

        conn.close()

        return jsonify({
            'mensaje': 'Stock insuficiente'
        })

    nuevo_stock = stock_actual - cantidad

    total = precio * cantidad

    # ACTUALIZAR STOCK
    c.execute(
        'UPDATE productos SET cantidad=? WHERE id=?',
        (nuevo_stock, producto_id)
    )

    # GUARDAR VENTA
    c.execute('''
        INSERT INTO ventas (
            producto,
            cantidad,
            precio,
            total,
            fecha
        )
        VALUES (?, ?, ?, ?, ?)
    ''', (
        producto,
        cantidad,
        precio,
        total,
        datetime.now().strftime("%Y-%m-%d %H:%M")
    ))

    # HISTORIAL
    c.execute(
        'INSERT INTO historial (accion, producto, fecha) VALUES (?, ?, ?)',
        (
            f'Venta ({cantidad})',
            producto,
            datetime.now().strftime("%Y-%m-%d %H:%M")
        )
    )

    conn.commit()

    conn.close()

    return jsonify({
        'mensaje': 'Venta registrada'
    })
# ---------------- VENTAS ----------------
@app.route('/ventas-page')
def ventas_page():
    return send_from_directory('static', 'ventas.html')


# ---------------- EJECUTAR ----------------

if __name__ == '__main__':
    app.run(debug=True)