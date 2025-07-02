import mysql.connector
import json

conexion= mysql.connector.connect(
    host="localhost",
    user="root", 
    password=""   
)

cursor= conexion.cursor()
cursor.execute("CREATE DATABASE IF NOT EXISTS PF_Informatica1")

cursor.execute("CREATE USER IF NOT EXISTS 'Informatica1'@'localhost' IDENTIFIED BY 'info2025_2';")
cursor.execute("GRANT ALL PRIVILEGES ON *.* TO 'Informatica1'@'localhost';")
cursor.execute("FLUSH PRIVILEGES;")
conexion.commit()

def conectar_db():
    return mysql.connector.connect(
        host="localhost",
        user="Informatica1",
        password="info2025_2",
        database="PF_Informatica1"
    )

def tabla_usuario():
    conexion= conectar_db()
    cursor= conexion.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        usuario_id INT AUTO_INCREMENT PRIMARY KEY,
        nombreUsuario VARCHAR(100) NOT NULL,
        password VARCHAR(255) NOT NULL,
        rol ENUM('Administrador', 'Ingeniero clínico', 'Técnico') NOT NULL
    )
    """)
    conexion.commit()
    cursor.close()
    conexion.close()

def tabla_equipos():
    conexion= conectar_db()
    cursor= conexion.cursor()
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
    conexion.commit()
    cursor.close()
    conexion.close()
    

def registrar_usuario():
    conexion= conectar_db()
    cursor= conexion.cursor()
    nombre_usuario= input("Ingrese el nombre de usuario: ").strip()
    password= input("Ingrese la contraseña: ").strip()
    password_json= json.dumps({"password": password})
    
    rol_opciones= {"1": "Administrador", "2": "Ingeniero clínico", "3": "Técnico"}
    rol_input= input("Ingrese el rol (1. Administrador, 2. Ingeniero clínico, 3. Técnico): ").strip()
    rol= rol_opciones.get(rol_input)
    
    if not rol:
        print("Rol inválido.")
        return

    cursor.execute("SELECT * FROM usuarios WHERE nombreUsuario= %s", (nombre_usuario,))
    resultado= cursor.fetchone()

    if resultado:
        print("El nombre de usuario ya existe. Intenta con otro.")
    else:
        cursor.execute("INSERT INTO usuarios (nombreUsuario, password, rol) VALUES (%s, %s, %s)", 
                       (nombre_usuario, password_json, rol))
        conexion.commit()
        print("Usuario registrado exitosamente.")

    cursor.close()
    conexion.close()

def editar_usuario():
    conexion= conectar_db()
    cursor= conexion.cursor()
    
    nombre_usuario= input("Ingrese el nombre del usuario que desea editar: ").strip()
    
    cursor.execute("SELECT usuario_id, password, rol FROM usuarios WHERE nombreUsuario = %s", (nombre_usuario,))
    resultado= cursor.fetchone()
    
    if not resultado:
        print("Usuario no encontrado.")
        cursor.close()
        conexion.close()
        return
    
    usuario_id, password_json, rol_actual = resultado
    password_actual = json.loads(password_json)["password"]
    
    print(f"\nUsuario: {nombre_usuario}")
    print(f"Rol actual: {rol_actual}")
    print(f"Contraseña actual: {password_actual}")

    nuevo_password= input("Ingrese nueva contraseña (o presione Enter para no cambiarla): ").strip()
    nuevo_rol_opcion= input("Ingrese nuevo rol (1. Administrador, 2. Ingeniero clínico, 3. Técnico) o Enter para dejar igual: ").strip()

    nuevo_password_json = json.dumps({"password": nuevo_password}) if nuevo_password else password_json
    nuevo_rol= {"1": "Administrador", "2": "Ingeniero clínico", "3": "Técnico"}.get(nuevo_rol_opcion, rol_actual)

    cursor.execute("""
        UPDATE usuarios SET password= %s, rol= %s WHERE usuario_id= %s
    """, (nuevo_password_json, nuevo_rol, usuario_id))
    
    conexion.commit()
    print("Usuario actualizado correctamente.")
    
    cursor.close()
    conexion.close()

def eliminar_usuario():
    conexion= conectar_db()
    cursor= conexion.cursor()
    nombre_usuario = input("Ingrese el nombre del usuario que desea eliminar: ").strip()
    cursor.execute("SELECT usuario_id, rol FROM usuarios WHERE nombreUsuario= %s", (nombre_usuario,))
    resultado = cursor.fetchone()
    if not resultado:
        print("Usuario no encontrado.")
        cursor.close()
        conexion.close()
        return
    
    usuario_id, rol= resultado
    print(f"\nUsuario encontrado: {nombre_usuario} (Rol: {rol})")
    cursor.execute("DELETE FROM usuarios WHERE usuario_id= %s", (usuario_id,))
    conexion.commit()
    print("Usuario eliminado correctamente.")
    
    cursor.close()
    conexion.close()

def añadir_equipos():
    conexion= conectar_db()
    cursor= conexion.cursor()
    try:
        print("\nRegistro de nuevo equipo:")
        nombre_equipo= input("Nombre del equipo: ")
        tipo_opciones= {"1": "Equipo de diagnóstico", "2": "Tratamiento", "3": "Monitorización", "4":"Vida", "5":"Rehabilitación"}
        tipo_input= input("Tipo (1. Equipo de diagnóstico / 2. Tratamiento / 3. Monitorización / 4. Vida / 5. Rehabilitación): ").strip()
        tipo= tipo_opciones.get(tipo_input)
        if not tipo:
            print("Rol inválido.")
            return
        clase_opciones={"1":"I", "2":"IIA", "3":"IIB", "4":"III"}
        clase_input= input("Clase (1. I / 2. IIA / 3. IIB / 4. III): ")
        clase= clase_opciones.get(clase_input)
        marca= input("Marca: ")
        modelo= input("Modelo: ")
        ubicacion= input("Ubicación: ")
        fecha_ingreso= input("Fecha de ingreso (YYYY-MM-DD): ")
        estado= input("Estado actual: ")
        tecnico_asignado_id=input("Ingrese la id del técnico asignado: ")
        consulta= """
        INSERT INTO equipos_biomedicos (nombre_equipo, tipo, clase, marca, modelo, ubicacion, fecha_ingreso, estado, tecnico_asignado_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        valores= (nombre_equipo, tipo, clase, marca, modelo, ubicacion, fecha_ingreso, estado, tecnico_asignado_id)
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
    
def login():
    conexion= conectar_db()
    cursor= conexion.cursor()
    nombre_usuario= input("Usuario: ").strip()
    password= input("Contraseña: ").strip()

    cursor.execute("SELECT password, rol FROM usuarios WHERE nombreUsuario= %s", (nombre_usuario,))
    resultado= cursor.fetchone()

    if resultado:
        password_json, rol= resultado
        password_bd= json.loads(password_json)["password"]
        
        if password== password_bd:
            while True:
                print(f"\nBienvenido, {nombre_usuario}. Rol: {rol}")
                if rol== "Administrador":
                    print("Menú Administrador\n1. Crear/Modificar/Eliminar equipo \n2. Registrar/editar/eliminar usuario \n3. Ver mantenimientos \n4. Cargar manuales técnicos \n5. Gestión de bitácoras y reportes \n6. Cerrar sesión ")
                    opcion= int(input("Elija una opción: "))
                    if opcion==1:
                        print("Submenu \n1. Crear equipo \n2. Modificar equipo \n3. Eliminar equipo")
                        subopcion= int(input("Elija una opción: "))
                        if subopcion==1:
                            añadir_equipos()
                        if subopcion==2:
                            modificar_equipo()
                        if subopcion==3:
                            eliminar_equipo()
                    if opcion==2:
                        print("Submenu \n1. Registrar usuario \n2. Editar usuario \n3. Eliminar usuario")
                        subopcion= int(input("Elija una opción: "))
                        if subopcion== 1:
                            registrar_usuario()
                        if subopcion== 2:
                            editar_usuario()
                        if subopcion== 3:
                            eliminar_usuario()
                    
                    if opcion==3:
                        tecnico=input("Ingrese el usuario del técnico ligado al mantenimiento: ")
                    
                    if opcion==6:
                        print("Saliendo")
                        break
                    else:
                        print("Opción inválida")
                        continue 
                    
                elif rol== "Ingeniero clínico":
                    print("Menú Ingeniero Clínico \n1. Ver equipos \n2. Ver historial de mantenimiento \n3. Ver reportes técnicos \n4. Descarga de manuales y bitácoras \n5. Buscar palabras clave \n6. Cerrar sesión ")
                    opcion= int(input("Elija una opcion: "))
                    if opcion==1:
                        print()
                elif rol== "Técnico":
                    print("Menú Técnico")
            else:
                print("Contraseña incorrecta.")
        else:
            print("Usuario no encontrado.")

    cursor.close()
    conexion.close()

tabla_usuario()
tabla_equipos()
while True:
    opcion= input("\n¿Deseas (1) Registrar usuario o (2) Iniciar sesión? ")
    
    if opcion== "1":
        registrar_usuario()
    elif opcion== "2":
        login()
    else:
        print("Opción inválida.")
























