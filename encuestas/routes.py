from flask import render_template, request, redirect, url_for, flash
from . import encuestas_bp
from app import get_db_connection

@encuestas_bp.route('/')
def listar_encuestas():
    conn = get_db_connection()
    encuestas = conn.execute('SELECT * FROM encuestas').fetchall()
    conn.close()
    return render_template('encuestas/listar.html', encuestas=encuestas)

@encuestas_bp.route('/crear', methods=['GET', 'POST'])
def crear_encuesta():
    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        
        conn = get_db_connection()
        conn.execute('INSERT INTO encuestas (titulo, descripcion) VALUES (?, ?)',
                    (titulo, descripcion))
        conn.commit()
        conn.close()
        
        flash('Encuesta creada exitosamente', 'success')
        return redirect(url_for('encuestas.listar_encuestas'))
    
    return render_template('encuestas/crear.html')