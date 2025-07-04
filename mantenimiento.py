import mysql.connector

conexion= mysql.connector.connect(host="localhost", user="root", password="")
cursor= conexion.cursor()
cursor.execute("CREATE DATABASE IF NOT EXISTS mantenimiento_equipos")
cursor = conexion.cursor()
cursor.execute("""
        CREATE TABLE IF NOT EXISTS mantenimientos (
            mmto_id INT AUTO_INCREMENT PRIMARY KEY,
            equipo_id INT NOT NULL,
            tecnico_id INT NOT NULL,
            tipoMmto ENUM('Preventivo', 'Correctivo') NOT NULL,
            fecha_mmto DATE NOT NULL,
            duracion_mmto INT,
            observaciones TEXT)
    """)

def conectar_db():
    return mysql.connector.connect(
        host="localhost",
        user="Informatica1",
        password="info2025_2",
        database="PF_Informatica1"
    )

def registrar_mmto(usuario_id):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        equipo_id = int(input("ID del equipo: "))
        tipoMmto = input("Tipo de mantenimiento (Preventivo/Correctivo): ").strip()
        fecha_mmto = input("Fecha del mantenimiento (YYYY-MM-DD): ").strip()
        duracion_mmto = int(input("Duración (minutos): "))
        observaciones = input("Observaciones: ")

        cursor.execute("""
            INSERT INTO mantenimientos (equipo_id, tecnico_id, tipoMmto, fecha_mmto, duracion_mmto, observaciones)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (equipo_id, usuario_id, tipoMmto, fecha_mmto, duracion_mmto, observaciones))
        conexion.commit()
        print("Mantenimiento registrado.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        conexion.close()











#ver mantenimientos(Ing/admin)
def Historialmmtos():
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT m.mmto_id, e.nombre_equipo, u.nombreUsuario, m.tipoMmto, m.fecha_mmto, m.duracion_mmto, m.observaciones
        FROM mantenimientos m
        JOIN equipos_biomedicos e ON m.equipo_id = e.equipo_id
        JOIN usuarios u ON m.tecnico_id = u.usuario_id
    """)
    registros = cursor.fetchall()
    if registros:
        for r in registros:
            print(r)
    else:
        print("No hay mantenimientos registrados")
    cursor.close()
    conexion.close()
#Ver mantenimientos del tecnico
def ver_mis_mantenimientos(tecnico_id):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT m.mmto_id, e.nombre_equipo, m.tipoMmto, m.fecha_mmto, m.duracion_mmto, m.observaciones
        FROM mantenimientos m
        JOIN equipos_biomedicos e ON m.equipo_id = e.equipo_id
        WHERE m.tecnico_id = %s
    """, (tecnico_id,))
    registros = cursor.fetchall()
    if registros:
        for r in registros:
            print(r)
    else:
        print("No tienes mantenimientos registrados.")
    cursor.close()
    conexion.close()
#Añadir observaciones(ing)
def n_observacion_mmtos():
    conexion = conectar_db()
    cursor = conexion.cursor()
    mmto_id = int(input("ID del mantenimiento a comentar: "))
    observacion_extra = input("Nueva observación: ")

    cursor.execute("SELECT observaciones FROM mantenimientos WHERE mmto_id = %s", (mmto_id,))
    actual = cursor.fetchone()
    if actual:
        nueva_obs = (actual[0] or "") + "\n" + observacion_extra
        cursor.execute("UPDATE mantenimientos SET observaciones = %s WHERE mmto_id = %s", (nueva_obs, mmto_id))
        conexion.commit()
        print("Observación añadida.")
    else:
        print("ID no encontrado.")
    cursor.close()
    conexion.close()



