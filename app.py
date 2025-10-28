from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'clave_secreta_encuestas'



def crear_base_datos():
    conn = sqlite3.connect('encuestas.db')
    print("Base de datos encuestas.db creada")
    
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS encuestas(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descripcion TEXT,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    
    # Tabla preguntas
    conn.execute('''
        CREATE TABLE IF NOT EXISTS preguntas(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_encuesta INTEGER NOT NULL,
            texto_pregunta TEXT NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('texto', 'opcion', 'escala')),
            opciones TEXT,
            FOREIGN KEY (id_encuesta) REFERENCES encuestas(id) ON DELETE CASCADE
        );
    ''')
    
    # Tabla usuarios
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarios(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            correo TEXT UNIQUE NOT NULL,
            rol TEXT DEFAULT 'respondedor'
        );
    ''')
    
    # Tabla respuestas
    conn.execute('''
        CREATE TABLE IF NOT EXISTS respuestas(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_pregunta INTEGER NOT NULL,
            id_usuario INTEGER NOT NULL,
            respuesta_texto TEXT,
            valor INTEGER,
            fecha_respuesta DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_pregunta) REFERENCES preguntas(id) ON DELETE CASCADE,
            FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE
        );
    ''')
    
    # Insertar datos de ejemplo
    conn.execute("INSERT OR IGNORE INTO usuarios (nombre, correo, rol) VALUES ('Admin', 'admin@email.com', 'admin')")
    conn.execute("INSERT OR IGNORE INTO usuarios (nombre, correo, rol) VALUES ('Juan Perez', 'juan@email.com', 'respondedor')")
    
    conn.commit()
    conn.close()
    print("Tablas creadas exitosamente")

# Función para obtener conexión a la BD
def get_db_connection():
    conn = sqlite3.connect('encuestas.db')
    conn.row_factory = sqlite3.Row
    return conn

# ==================== RUTAS PRINCIPALES ====================

@app.route("/")
def inicio():
    conn = get_db_connection()
    encuestas = conn.execute('SELECT * FROM encuestas ORDER BY fecha_creacion DESC').fetchall()
    conn.close()
    return render_template('index.html', encuestas=encuestas)

# ==================== RUTAS ENCUESTAS ====================

@app.route('/encuestas')
def listar_encuestas():
    conn = get_db_connection()
    encuestas = conn.execute('''
        SELECT e.*, COUNT(p.id) as total_preguntas 
        FROM encuestas e 
        LEFT JOIN preguntas p ON e.id = p.id_encuesta 
        GROUP BY e.id
        ORDER BY e.fecha_creacion DESC
    ''').fetchall()
    conn.close()
    return render_template('encuestas/listar.html', encuestas=encuestas)

@app.route('/encuestas/crear', methods=['GET', 'POST'])
def crear_encuesta():
    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        
        if not titulo:
            flash('El título es obligatorio', 'error')
            return render_template('encuestas/crear.html')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO encuestas (titulo, descripcion) VALUES (?, ?)',
                      (titulo, descripcion))
        encuesta_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        flash('Encuesta creada exitosamente', 'success')
        return redirect(url_for('detalle_encuesta', id=encuesta_id))
    
    return render_template('encuestas/crear.html')

@app.route('/encuestas/<int:id>')
def detalle_encuesta(id):
    conn = get_db_connection()
    encuesta = conn.execute('SELECT * FROM encuestas WHERE id = ?', (id,)).fetchone()
    preguntas = conn.execute('SELECT * FROM preguntas WHERE id_encuesta = ?', (id,)).fetchall()
    conn.close()
    
    if encuesta is None:
        flash('Encuesta no encontrada', 'error')
        return redirect(url_for('listar_encuestas'))
    
    return render_template('encuestas/detalle.html', encuesta=encuesta, preguntas=preguntas)

# ==================== RUTAS PREGUNTAS ====================

@app.route('/encuestas/<int:id_encuesta>/preguntas/crear', methods=['GET', 'POST'])
def crear_pregunta(id_encuesta):
    if request.method == 'POST':
        texto_pregunta = request.form['texto_pregunta']
        tipo = request.form['tipo']
        opciones = request.form.get('opciones', '')
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO preguntas (id_encuesta, texto_pregunta, tipo, opciones) 
            VALUES (?, ?, ?, ?)
        ''', (id_encuesta, texto_pregunta, tipo, opciones))
        conn.commit()
        conn.close()
        
        flash('Pregunta agregada exitosamente', 'success')
        return redirect(url_for('detalle_encuesta', id=id_encuesta))
    
    return render_template('preguntas/crear.html', id_encuesta=id_encuesta)

# ==================== RUTAS RESPUESTAS ====================

@app.route('/encuestas/<int:id_encuesta>/responder', methods=['GET', 'POST'])
def responder_encuesta(id_encuesta):
    conn = get_db_connection()
    
    if request.method == 'POST':
        # Obtener usuario (en un caso real, sería el usuario logueado)
        usuario_id = 2  # Juan Perez
        
        # Procesar cada respuesta
        for key, value in request.form.items():
            if key.startswith('pregunta_'):
                pregunta_id = key.replace('pregunta_', '')
                
                # Determinar si es texto o valor numérico
                if value.isdigit():
                    conn.execute('''
                        INSERT INTO respuestas (id_pregunta, id_usuario, valor) 
                        VALUES (?, ?, ?)
                    ''', (pregunta_id, usuario_id, int(value)))
                else:
                    conn.execute('''
                        INSERT INTO respuestas (id_pregunta, id_usuario, respuesta_texto) 
                        VALUES (?, ?, ?)
                    ''', (pregunta_id, usuario_id, value))
        
        conn.commit()
        conn.close()
        flash('Encuesta respondida exitosamente', 'success')
        return redirect(url_for('inicio'))
    
    # GET: Mostrar formulario de respuesta
    encuesta = conn.execute('SELECT * FROM encuestas WHERE id = ?', (id_encuesta,)).fetchone()
    preguntas = conn.execute('SELECT * FROM preguntas WHERE id_encuesta = ?', (id_encuesta,)).fetchall()
    conn.close()
    
    return render_template('respuestas/responder.html', encuesta=encuesta, preguntas=preguntas)

# ==================== RUTAS REPORTES ====================

@app.route('/encuestas/<int:id>/resultados')
def resultados_encuesta(id):
    conn = get_db_connection()
    
    # Encuesta - CONVERTIR A DICT
    encuesta_row = conn.execute('SELECT * FROM encuestas WHERE id = ?', (id,)).fetchone()
    encuesta = dict(encuesta_row) if encuesta_row else None
    
    if not encuesta:
        flash('Encuesta no encontrada', 'error')
        return redirect(url_for('listar_encuestas'))
    
    # Preguntas - CONVERTIR A LISTA DE DICTS
    preguntas_rows = conn.execute('SELECT * FROM preguntas WHERE id_encuesta = ?', (id,)).fetchall()
    preguntas = [dict(row) for row in preguntas_rows]
    
    # Estadísticas - CONVERTIR A LISTA DE DICTS
    estadisticas = []
    for pregunta in preguntas:
        if pregunta['tipo'] == 'escala':
            stats_row = conn.execute('''
                SELECT AVG(valor) as promedio, COUNT(*) as total_respuestas
                FROM respuestas WHERE id_pregunta = ?
            ''', (pregunta['id'],)).fetchone()
            stats = dict(stats_row) if stats_row else {'promedio': 0, 'total_respuestas': 0}
        else:
            stats_row = conn.execute('''
                SELECT COUNT(*) as total_respuestas
                FROM respuestas WHERE id_pregunta = ?
            ''', (pregunta['id'],)).fetchone()
            stats = dict(stats_row) if stats_row else {'total_respuestas': 0}
        
        estadisticas.append(stats)
    
    conn.close()
    
    # DEBUG: Ver datos en consola
    print("=== DEBUG RESULTADOS ===")
    print("Encuesta:", encuesta)
    print("Preguntas:", preguntas)
    print("Estadísticas:", estadisticas)
    
    return render_template('reportes/resultados.html', 
                         encuesta=encuesta, 
                         preguntas=preguntas, 
                         estadisticas=estadisticas)
# ==================== API PARA GRÁFICOS ====================


@app.route('/api/encuestas/<int:id>/datos-grafico')
def datos_grafico(id):
    conn = get_db_connection()
    
    datos = conn.execute('''
        SELECT p.texto_pregunta, AVG(r.valor) as promedio, COUNT(r.id) as total
        FROM preguntas p
        LEFT JOIN respuestas r ON p.id = r.id_pregunta
        WHERE p.id_encuesta = ? AND p.tipo = 'escala'
        GROUP BY p.id
    ''', (id,)).fetchall()
    
    conn.close()
    
    # Convertir a lista de diccionarios
    datos_dict = [dict(d) for d in datos]
    
    return jsonify({
        'labels': [f"P{i+1}" for i in range(len(datos_dict))],
        'data': [float(d['promedio']) if d['promedio'] else 0 for d in datos_dict]
    })

# ==================== INICIALIZACIÓN ====================

if __name__ == "__main__":
    # Crear base de datos al iniciar
    crear_base_datos()
    print("Servidor iniciado en http://localhost:5000")
    app.run(debug=True)