import mysql.connector

conexion= mysql.connector.connect(host="localhost", user="root", password="")
cursor= conexion.cursor()
cursor.execute("CREATE DATABASE IF NOT EXISTS mantenimiento_equipos")
cursor.execute("USE mantenimiento_equipos")
cursor.execute("""
CREATE TABLE IF NOT EXISTS equipos_biomedicos(
    equipo_id INT AUTO_INCREMENT PRIMARY KEY,
    nombre_equipo VARCHAR(100) NOT NULL,
    tipo ENUM("Equipo de diagnóstico", "Equipo de tratamiento", "Equipos de monitorización", "Equipo de apoyo a la vida", "Equipo de rehabilitación") NOT NULL, 
    clase ENUM("Clase I", "Clase IIA", "Clase IIB", "Clase III") NOT NULL,
    marca VARCHAR(100) NOT NULL,
    modelo VARCHAR(100) NOT NULL,
    ubicacion VARCHAR(100) NOT NULL,
    fecha_ingreso DATE,
    estado VARCHAR(100) NOT NULL,
    tecnico_asignado_id VARCHAR(10) NOT NULL
)
""")
def añadir_equipos(nombre_equipo, tipo, clase, marca, modelo, ubicacion, fecha_ingreso, estado):
    try:
        consulta = """
        INSERT INTO equipos_biomedicos (nombre_equipo, tipo, clase, marca, modelo, ubicacion, fecha_ingreso, estado)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        valores = (nombre_equipo, tipo, clase, marca, modelo, ubicacion, fecha_ingreso, estado)
        cursor.execute(consulta, valores)
        conexion.commit()
        print("Equipo registrado exitosamente")
    except mysql.connector.Error as error:
        print(f"Error al registrar equipo: {error}")
def buscar_equipo_por_id(equipo_id):
    try:
        consulta = "SELECT * FROM equipos_biomedicos WHERE equipo_id = %s"
        cursor.execute(consulta, (equipo_id,))
        resultado = cursor.fetchone()
        if resultado:
            print(f"ID: {resultado[0]}")
            print(f"Nombre: {resultado[1]}")
            print(f"Tipo: {resultado[2]}")
            print(f"Clase: {resultado[3]}")
            print(f"Marca: {resultado[4]}")
            print(f"Modelo: {resultado[5]}")
            print(f"Ubicación: {resultado[6]}")
            print(f"Fecha de ingreso: {resultado[7]}")
            print(f"Estado: {resultado[8]}")
            print(f"Técnico asignado ID: {resultado[9]}")
        else:
            print("No se encontró el equipo con ese ID.")
    except mysql.connector.Error as error:
        print(f"Error al buscar el equipo: {error}")
def ver_equipos():
    try:
        cursor.execute("SELECT * FROM equipos_biomedicos")
        resultados = cursor.fetchall()
        if resultados:
            print("Equipos registrados")
            for equipo in resultados:
                print(equipo)
        else:
            print("No hay equipos registrados")
    except mysql.connector.Error as error:
        print(f"Error al consultar equipos: {error}")
def modificar_equipo(equipo_id, campo, nuevo_valor):
    try:
        consulta = f"UPDATE equipos_biomedicos SET {campo} = %s WHERE equipo_id = %s"
        valores = (nuevo_valor, equipo_id)
        cursor.execute(consulta, valores)
        conexion.commit()
        if cursor.rowcount > 0:
            print("Equipo actualizad")
        else:
            print("No se encontró el equipo con ese ID.")
    except mysql.connector.Error as error:
        print(f"Error al actualizar equipo: {error}")
def eliminar_equipo(equipo_id):
    try:
        consulta = "DELETE FROM equipos_biomedicos WHERE equipo_id = %s"
        valores = (equipo_id,)
        cursor.execute(consulta, valores)
        conexion.commit()
        if cursor.rowcount > 0:
            print("Equipo eliminado con exito")
        else:
            print("No se encontró el equipo con ese ID.")
    except mysql.connector.Error as error:
        print(f"Error al eliminar el equipo: {error}")
def menu_administrador():
    print("""
          1. Añadir equipo
          2. Modificar equipo
          3. Buscar equipo
          4. Eliminar equipo
          5. Ver todos los equipos""")

def menu_ingeniero():
    print("""1. Ver todos los equipos
          2. Buscar equipo""")
def menu_tecnico():
    print("1. Ver equipos asignados")
