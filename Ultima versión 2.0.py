import mysql.connector
import json
import os
import shutil
from datetime import datetime
from pymongo import MongoClient
import mongo_reportes as mongorep

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

client = MongoClient("mongodb://localhost:27017/")
db = client["PF_Informatica1"]
coleccion_manuales = db["manuales_tecnicos"]
coleccion_bitacoras = db["bitacoras"]

#-----------------FUNCIONES-------------------

def validar(msj):
    """
    Esta función revisa que el input ingresado sea un número entero, en caso de que no, devuelve el error hasta 
    que se ingrese un número entero
    """
    while True:
        try:
            entrada=int(input(msj))
            return entrada
        except ValueError:
            print("Solo números enteros!")

def conectar_db():
    """
    Esta función se conecta la base de datos usando el usuario y contraseña indicados y conectándose a un servidor local
    """
    return mysql.connector.connect(
        host="localhost",
        user="Informatica1",
        password="info2025_2",
        database="PF_Informatica1"
    )

def validar_fecha(fecha_str):
    """
    Valida que el ingreso de la fecha se haga en el formato establecido y que los datos sean coherentes
    """
    try:
        datetime.strptime(fecha_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False
    
def verificar_tecnico(tecnico_id):
    if not tecnico_id or not isinstance(tecnico_id, str):
        return (False, False, None)  
    conexion = None
    cursor = None
    try:
        conexion = conectar_db()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(
            "SELECT nombreUsuario, rol FROM usuarios WHERE usuario_id = %s",
            (tecnico_id,)
        )
        usuario = cursor.fetchone()
        
        if not usuario:
            return (False, False, None)

        es_tecnico = usuario['rol'] == 'Técnico'
        return (True, es_tecnico, usuario['nombreUsuario'])
        
    except mysql.connector.Error as error:
        print(f"Error al verificar técnico: {error}")
        return (False, False, None)
    finally:
        cursor.close()
        conexion.close()
        
def contraseñas_json():
    """
    Esta función crea el archivo json en el que se guardarán las contraseñas ingresadas, con el usuario correspondiente 
    y su ID
    """
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT usuario_id, nombreUsuario, password FROM usuarios")
        usuarios = cursor.fetchall()

        backup = []
        for usuario_id, nombreUsuario, password in usuarios:
            backup.append({
                "usuario_id": usuario_id,
                "nombreUsuario": nombreUsuario,
                "password": password
            })

        with open("contraseñas.json", "w", encoding="utf-8") as f:
            json.dump(backup, f, indent=4)

        print("Backup guardado exitosamente en contraseñas.json.")
    except Exception as e:
        print(f"Error al generar backup: {e}")
    finally:
        cursor.close()
        conexion.close()

def validar_equipos(campo):
    """
    La función valida el ingreso de datos en todos los campos requeridos
    """
    while True:
        valor = input(f"{campo}: ").strip()
        if valor:
            return valor
        print(f"El campo '{campo}' no puede estar vacío.")

#-----------------TABLAS----------------

def tabla_usuario():
    """
    Se conecta la tabla de usuarios llamando a la función ya creada, el cursor sirve como puente para 
    ejecutar sentencias SQL, se ejecuta la tabla que tiene un ID único y automático para cada usuario, 
    tienes los campos de usuario y contraseña como obligatorios, reduce los roles a 3 únicamente y 
    agrega otros campos opcionales para el técnico, con el commit se aplican los cambios y luego se cierra la 
    conexión
    """
    conexion= conectar_db()
    cursor= conexion.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        usuario_id INT AUTO_INCREMENT PRIMARY KEY,
        nombreUsuario VARCHAR(100) NOT NULL,
        password VARCHAR(255) NOT NULL,
        rol ENUM('Administrador', 'Ingeniero clínico', 'Técnico') NOT NULL,
        nombre_completo VARCHAR(100),
        especialidad VARCHAR(100),
        cedula_profesional VARCHAR(20),
        contacto VARCHAR(100)
    )
    """)

    conexion.commit()
    cursor.close()
    conexion.close()

def tabla_equipos():
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipos_biomedicos(
            equipo_id VARCHAR(20) PRIMARY KEY,
            nombre_equipo VARCHAR(100) NOT NULL,
            tipo ENUM('Equipo de diagnóstico', 'Equipo de tratamiento', 'Equipo de monitorización', 
                      'Equipo de apoyo a la vida', 'Equipo de rehabilitación') NOT NULL, 
            clase ENUM('Clase I', 'Clase IIA', 'Clase IIB', 'Clase III') NOT NULL,
            marca VARCHAR(100) NOT NULL,
            modelo VARCHAR(100) NOT NULL,
            ubicacion VARCHAR(100) NOT NULL,
            fecha_ingreso DATE NOT NULL,
            estado ENUM('Disponible', 'En mantenimiento', 'Dado de baja') NOT NULL,
            tecnico_asignado_id INT NOT NULL,
            FOREIGN KEY (tecnico_asignado_id) REFERENCES usuarios(usuario_id)
        )
    """)
        conexion.commit()
        print("Tabla 'equipos_biomedicos' creada correctamente")
    except mysql.connector.Error as error:
        print(f"Error al crear tabla: {error}")
    finally:
        cursor.close() 
        conexion.close()

def tabla_mantenimiento():
    conexion= conectar_db()
    cursor= conexion.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mantenimientos (
        mmto_id INT AUTO_INCREMENT PRIMARY KEY,
        equipo_id VARCHAR(15) NOT NULL,
        tecnico_id VARCHAR(10) NOT NULL,
        tipoMmto ENUM('Preventivo', 'Correctivo') NOT NULL,
        fecha_mmto DATE NOT NULL,
        duracion_mmto INT,
        observaciones TEXT)
    """)
    conexion.commit()
    print("Tabla 'mantenimientos' creada correctamente")
    cursor.close()
    conexion.close()

#------------------USUARIOS---------------

def registrar_usuario():
    """
    Las funciones de usuario se ejecutan solo para el administrador, primero se conecta a la base de datos, usa el cursor, 
    pide los datos necesarios, en el caso de los roles pide un número como clave y con un diccionario en la tabla se usa el rol al que corresponde, 
    en caso de que no exista, se marca el error. Luego, busca el usuario ingresado y en caso de que no lo encuentre, 
    lo registra, de lo contrario, marca el error. Además, si el rol es de técnico, pide los datos adicionales y los guarda.
    
    """
    conexion= conectar_db()
    cursor= conexion.cursor()   
    nombre_usuario= input("Ingrese el nombre de usuario: ").strip()
    password= input("Ingrese la contraseña: ").strip()
    rol_opciones= {"1": "Administrador", "2": "Ingeniero clínico", "3": "Técnico"}
    rol_input= input("Ingrese el rol (1. Administrador, 2. Ingeniero clínico, 3. Técnico): ").strip()
    rol= rol_opciones.get(rol_input)
    
    if not rol:
        print("Rol inválido.")
        return

    cursor.execute("SELECT * FROM usuarios WHERE nombreUsuario = %s", (nombre_usuario,))
    resultado = cursor.fetchone()

    if resultado:
        print("El nombre de usuario ya existe. Intenta con otro.")
    else:
        cursor.execute(
            "INSERT INTO usuarios (nombreUsuario, password, rol) VALUES (%s, %s, %s)",
            (nombre_usuario, password, rol)
        )
        conexion.commit()
        print("Usuario registrado exitosamente.")
        
        if rol== "Técnico":
            tecnico_id= cursor.lastrowid
            nombre_completo= input("Nombre completo del técnico: ").strip()
            especialidad= input("Especialidad: ").strip()
            cedula= validar("Cédula profesional: ").strip()
            contacto= validar("Contacto: ").strip()

            cursor.execute("""
                UPDATE usuarios SET 
                    nombre_completo = %s, 
                    especialidad = %s,
                    cedula_profesional = %s, 
                    contacto = %s 
                WHERE usuario_id = %s
            """, (nombre_completo, especialidad, cedula, contacto, tecnico_id))
            conexion.commit()

    cursor.close()
    conexion.close()

def editar_usuario():
    """
    Establece la conexión, comprueba la existencia del usuario por medio del nombre de usuario, extrae la información
    actual del usuario y la imprime, además, si es técnico imprime los datos adicionales, luego, se piden los nuevos datos
    a cambiar, o si se quieren dejar en blanco se puede usar enter, también se piden los nuevos valores para el técnico. 
    Luego guarda estos datos y los actualiza.
    """
    conexion= conectar_db()
    cursor= conexion.cursor()
    nombre_usuario= input("Ingrese el nombre del usuario que desea editar: ").strip()
    cursor.execute("""
        SELECT usuario_id, nombreUsuario, password, rol, nombre_completo, especialidad, cedula_profesional, contacto 
        FROM usuarios WHERE nombreUsuario = %s
    """, (nombre_usuario,))
    
    resultado= cursor.fetchone()
    
    if not resultado:
        print("Usuario no encontrado.")
        cursor.close()
        conexion.close()
        return
    
    usuario_id, nombre_actual, password, rol_actual, nombre_completo, especialidad, cedula, contacto= resultado
    password_actual= password
    
    print("\n--- Información actual del usuario ---")
    print(f"Nombre de usuario: {nombre_actual}")
    print(f"Rol: {rol_actual}")
    print(f"Contraseña: {password_actual}")
    
    if rol_actual== "Técnico":
        print(f"Nombre completo: {nombre_completo}")
        print(f"Especialidad: {especialidad}")
        print(f"Cédula profesional: {cedula}")
        print(f"Contacto: {contacto}")
    
    nuevo_usuario = input("Nuevo nombre de usuario (Enter para no cambiarlo): ").strip()
    nuevo_password = input("Nueva contraseña (Enter para no cambiarla): ").strip()
    nuevo_rol_opcion = input("Nuevo rol (1. Administrador, 2. Ingeniero clínico, 3. Técnico) o Enter para dejar igual: ").strip() 
    nuevo_usuario = nuevo_usuario if nuevo_usuario else nombre_actual
    nuevo_password_edicion = nuevo_password if nuevo_password else password
    nuevo_rol = {"1": "Administrador", "2": "Ingeniero clínico", "3": "Técnico"}.get(nuevo_rol_opcion, rol_actual)
    cursor.execute("""
        UPDATE usuarios SET nombreUsuario = %s, password = %s, rol = %s WHERE usuario_id = %s
    """, (nuevo_usuario, nuevo_password_edicion, nuevo_rol, usuario_id))
    
    if nuevo_rol == "Técnico":
        print("\n--- Información profesional del técnico ---")
        nuevo_nombre_completo = input("Nombre completo (Enter para no cambiarlo): ").strip()
        nueva_especialidad = input("Especialidad (Enter para no cambiarla): ").strip()
        nueva_cedula = validar("Cédula profesional (Enter para no cambiarla): ").strip()
        nuevo_contacto = validar("Contacto (Enter para no cambiarlo): ").strip()
        nuevo_nombre_completo = nuevo_nombre_completo if nuevo_nombre_completo else nombre_completo
        nueva_especialidad = nueva_especialidad if nueva_especialidad else especialidad
        nueva_cedula = nueva_cedula if nueva_cedula else cedula
        nuevo_contacto = nuevo_contacto if nuevo_contacto else contacto
        cursor.execute("""UPDATE usuarios SET  nombre_completo = %s, especialidad = %s, cedula_profesional = %s, contacto = %s WHERE usuario_id = %s""", (nuevo_nombre_completo, nueva_especialidad, nueva_cedula, nuevo_contacto, usuario_id))

    conexion.commit()
    print("Usuario actualizado correctamente.")
    contraseñas_json()
    
    cursor.close()
    conexion.close()

def eliminar_usuario():
    """
    De igual forma, se verifica la existencia del usuario por el nombre, en caso de que no exista se indica como 
    tal y en caso de que si utiliza el comando DELETE para eliminar al usuario y los datos que corresponden a este
    """
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

#-------------------------EQUIPOS------------------------
def equipo_id(tipo_input):
    """"
    Esta función crea automaticamente la ID del equipo al seleccionar un tipo de equipo
    """
    conexion = conectar_db()
    cursor = conexion.cursor()

    tipo_codigos = {
        "1": ("Equipo de diagnóstico", "DIA"),
        "2": ("Equipo de tratamiento", "TRA"),
        "3": ("Equipo de monitorización", "MON"),
        "4": ("Equipo de apoyo a la vida", "VID"),
        "5": ("Equipo de rehabilitación", "REH")
    }

    tipo_info = tipo_codigos.get(tipo_input)
    if not tipo_info:
        print("Tipo inválido")
        return None, None

    tipo_nombre, codigo = tipo_info
    cursor.execute("SELECT COUNT(*) FROM equipos_biomedicos WHERE tipo = %s", (tipo_nombre,))
    cantidad = cursor.fetchone()[0] + 1

    equipo_id = f"EQ-{codigo}-{str(cantidad).zfill(4)}"
    cursor.close()
    conexion.close()
    return equipo_id, tipo_nombre

def añadir_equipos():
    """
    Añadir, editar y elimar equipos sun funciones del administrador, para añadir, se solicita el tipo de equipo, a partir
    del que se crea la ID automaticamente, además, solicita la infromación de clase, marca, modelo y ubicación, asegurando
    que no se puedan dejar vacíos, además, valida la fecha de ingreso y el estado. Por último, solicita un técnico al que 
    asignar el equipo y asegura que el técnico exista en el sistema. Luego. añade toda esta información a la tabla
    """
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        print("\n--- Registro de nuevo equipo ---")

        tipo_opciones = {
            "1": "Equipo de diagnóstico",
            "2": "Equipo de tratamiento", 
            "3": "Equipo de monitorización",
            "4": "Equipo de apoyo a la vida",
            "5": "Equipo de rehabilitación"
        }

        while True:
            print("\nSeleccione el tipo de equipo:")
            for key, value in tipo_opciones.items():
                print(f"{key}. {value}")
            tipo_input = input("Opción (1-5): ").strip()
            equipo_id_generado, tipo = equipo_id(tipo_input)
            if equipo_id_generado:
                break
            print("Opción inválida, intente nuevamente.")

        print(f"ID generado: {equipo_id_generado}")
        nombre_equipo = validar_equipos("Nombre del equipo")

        clase_opciones = {
            "1": "Clase I",
            "2": "Clase IIA",
            "3": "Clase IIB", 
            "4": "Clase III"
        }
        while True:
            print("\nSeleccione la clase del equipo:")
            for key, value in clase_opciones.items():
                print(f"{key}. {value}")
            clase_input = input("Opción: ").strip()
            clase = clase_opciones.get(clase_input)
            if clase:
                break
            print("Opción inválida.")

        marca = validar_equipos("Marca")
        modelo = validar_equipos("Modelo")
        ubicacion = validar_equipos("Ubicación")

        while True:
            fecha_ingreso = input("Fecha de ingreso (YYYY-MM-DD): ").strip()
            if validar_fecha(fecha_ingreso):
                break
            else:
                print("Formato de fecha inválido. Use YYYY-MM-DD")

        estado_opciones = {
            "1": "Disponible",
            "2": "En mantenimiento",
            "3": "Dado de baja"
        }
        while True:
            print("\nSeleccione el estado del equipo:")
            for key, value in estado_opciones.items():
                print(f"{key}. {value}")
            estado_input = input("Opción: ").strip()
            estado = estado_opciones.get(estado_input)
            if estado:
                break
            print("Opción inválida.")

        while True:
            tecnico_asignado_id = input("ID del técnico asignado: ").strip()
            cursor.execute("SELECT 1 FROM usuarios WHERE usuario_id = %s AND rol = 'Técnico'", (tecnico_asignado_id,))
            if cursor.fetchone():
                break
            print("Técnico no válido o no existe.")

        consulta = """
            INSERT INTO equipos_biomedicos 
            (equipo_id, nombre_equipo, tipo, clase, marca, modelo, ubicacion, fecha_ingreso, estado, tecnico_asignado_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        valores = (
            equipo_id_generado, nombre_equipo, tipo, clase, marca, 
            modelo, ubicacion, fecha_ingreso, estado, tecnico_asignado_id
        )
        cursor.execute(consulta, valores)
        conexion.commit()
        print(f"\nEquipo registrado exitosamente con ID: {equipo_id_generado}")

    except mysql.connector.Error as error:
        print(f"Error al registrar equipo: {error}")
    finally:
        cursor.close()
        conexion.close()
        
def verificar_equipo(equipo_id):
    """
    Esta función verifica que el formateo de la ID de los equipos sea correcta, isinstance confirma que sea de tipo string,
    con startswith se confirma que empiece por EQ y con len que tenga 3 partes separadas por-, si no se cumplen retorna
    que el argumento es falso
    """
    if not isinstance(equipo_id, str) or not equipo_id.startswith('EQ-') or len(equipo_id.split('-')) != 3:
        return False
    conexion = None
    cursor = None
    try:
        conexion = conectar_db()
        cursor = conexion.cursor()
        cursor.execute("SELECT 1 FROM equipos_biomedicos WHERE equipo_id = %s", (equipo_id,))
        return cursor.fetchone() is not None
    except mysql.connector.Error as error:
        print(f"Error al verificar equipo: {error}")
        return False
    finally:
        cursor.close() 
        conexion.close() 
        
def buscar_equipo_por_id(equipo_id):
    """
    Esta función permite buscar equipos ingresando su ID, si la ID existe muestra los resultados, de lo contrario
    marca que no existe. Función para ingeniero clínico
    """
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
    """"
    Esta función muestra todos los equipos registrados en el sistema, en caso de que no hayan, se marca. Función para 
    ingeniero clínico
    """
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT * FROM equipos_biomedicos")
        equipos = cursor.fetchall()

        if equipos:
            print("\n Lista de Equipos Registrados:\n")
            for e in equipos:
                print(f"""
                      ID: {e[0]}
                      Nombre: {e[1]}
                      Tipo: {e[2]}
                      Clase: {e[3]}
                      Marca: {e[4]} | Modelo: {e[5]}
                      Ubicación: {e[6]}
                      Fecha ingreso: {e[7]}
                      Estado: {e[8]}
                      Técnico asignado (ID): {e[9]}
                      {""}
                      """)
        else:
            print("No hay equipos registrados.")
    except Exception as e:
        print(f"Error al consultar equipos: {e}")
    finally:
        cursor.close()
        conexion.close()
    
def ver_equipos_asignados(nombre_usuario):
    """
    Función para técnicos, permite que de acuerdo a su nombre de usuario, se puedan ver los equipos conectados a este.
    """
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        cursor.execute("""
        SELECT e.equipo_id, e.nombre_equipo, e.tipo, e.ubicacion, e.estado
        FROM equipos_biomedicos e
        JOIN usuarios u ON e.tecnico_asignado_id = u.usuario_id
        WHERE u.nombreUsuario = %s
        """, (nombre_usuario,))
        equipos = cursor.fetchall()
        if equipos:
            print("\nEquipos asignados:")
            for eq in equipos:
                print(f"ID: {eq[0]} / Nombre: {eq[1]} / Tipo: {eq[2]} / Ubicación: {eq[3]} / Estado: {eq[4]}")
        else:
            print("Sin equipos asignados.")
    
    except mysql.connector.Error as error:
        print(f"Error al consultar equipos: {error}")
    finally:
        cursor.close()
        conexion.close()
        
def modificar_equipo(equipo_id, campo, nuevo_valor):
    """
    Esta función garantiza que el usuario ingrese un campo permitido y un ID existente, de lo contrario, marca el error.
    """
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        campos_permitidos = {
            "nombre_equipo", "clase", "marca", 
            "modelo", "ubicacion", "estado"
        }

        if campo not in campos_permitidos:
            print("No se permite modificar ese campo.")
            return False

        cursor.execute("SELECT 1 FROM equipos_biomedicos WHERE equipo_id = %s", (equipo_id,))
        if not cursor.fetchone():
            print("No existe un equipo con ese ID.")
            return False

        if nuevo_valor.strip() == "":
            print("El nuevo valor no puede estar vacío.")
            return False

        consulta = f"UPDATE equipos_biomedicos SET {campo} = %s WHERE equipo_id = %s"
        cursor.execute(consulta, (nuevo_valor, equipo_id))
        conexion.commit()

        if cursor.rowcount > 0:
            print(f"Equipo {equipo_id} actualizado correctamente.")
            return True
        else:
            print("No se realizaron cambios.")
            return False

    except mysql.connector.Error as error:
        print(f"Error al actualizar equipo: {error}")
        return False
    finally:
        cursor.close()
        conexion.close()
        
def eliminar_equipo():
    """
    Verifica que existan equipos, si los hay pregunta por el ID y evalúa su formateo, luego, pregunta por confirmación
    y si S, se cancela la operación, de lo contrario, se elimina el equipo
    """
    conexion = None
    cursor = None
    try:
        conexion = conectar_db()
        cursor = conexion.cursor()
        print("\nEquipos registrados:")
        cursor.execute("SELECT equipo_id, nombre_equipo FROM equipos_biomedicos")
        equipos = cursor.fetchall()
        if not equipos:
            print("No hay equipos registrados.")
            return
        
        for equipo in equipos:
            print(f"- ID: {equipo[0]} | Nombre: {equipo[1]}")
        
        equipo_id = input("\nIngrese el ID del equipo a eliminar (EQ-XXX-XXXX): ").strip()

        if not verificar_equipo(equipo_id):
            print("Formato de ID invalido o no existe. Use el formato EQ-XXX-XXXX.")
            return
        confirmacion = input(f"¿Está seguro de eliminar el equipo {equipo_id}? (S/N): ").strip().upper()
        if confirmacion != 'S':
            print("Operación cancelada.")
            return
        
        cursor.execute("DELETE FROM equipos_biomedicos WHERE equipo_id = %s", (equipo_id,))
        conexion.commit()
        
        if cursor.rowcount > 0:
            print(f"Equipo {equipo_id} eliminado exitosamente.")
        else:
            print("No se encontro el equipo con ese ID.")
            
    except mysql.connector.Error as error:
        print(f"Error al eliminar equipo: {error}")
    finally:
            cursor.close()
            conexion.close()

#-------------------------MANTENIMIENTO----------------------------

def registrar_mmto(usuario_id, tipoMmto):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        while True:
            equipo_id = input("ID del equipo (formato EQ-XXX-XXXX): ").strip()
            if verificar_equipo(equipo_id):
                break
            print("ID de equipo inválido o no existe. Intenta nuevamente.")

        fecha_mmto = input("Fecha del mantenimiento (YYYY-MM-DD): ").strip()
        if not validar_fecha(fecha_mmto):
            print("Fecha inválida.")
            return

        duracion_mmto = validar("Duración (minutos): ")
        observaciones = input("Observaciones: ")

        cursor.execute("""
            INSERT INTO mantenimientos (equipo_id, tecnico_id, tipoMmto, fecha_mmto, duracion_mmto, observaciones)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (equipo_id, usuario_id, tipoMmto, fecha_mmto, duracion_mmto, observaciones))
        
        conexion.commit()
        print(f"Mantenimiento {tipoMmto.lower()} registrado.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        conexion.close()
        
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
        print("\n Historial de Mantenimientos Registrados:\n")
        for r in registros:
            mmto_id, equipo, tecnico, tipo, fecha, duracion, observaciones = r
            print(f"""
Mantenimiento ID: {mmto_id}
Equipo: {equipo}
Técnico: {tecnico}
Tipo: {tipo}
Fecha: {fecha.strftime('%Y-%m-%d')}
Duración: {duracion} minutos
Observaciones: {observaciones}
{""}
""")
    else:
        print("No hay mantenimientos registrados.")
        
    cursor.close()
    conexion.close()

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
        print("\n Mantenimientos realizados:")
        for r in registros:
            mmto_id, nombre_equipo, tipo, fecha, duracion, observaciones = r
            print(f"""
Mantenimiento ID: {mmto_id}
Equipo: {nombre_equipo}
Tipo: {tipo}
Fecha: {fecha.strftime('%Y-%m-%d')}
Duración: {duracion} minutos
Observaciones: {observaciones}
{""}
""")
    else:
        print("Sin mantenimientos registrados.")
    cursor.close()
    conexion.close()

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

#--------------------REPORTES------------------

def subir_reporte_mongo(usuario_id,nombre_usuario):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        mmto_id = input("ID del mantenimiento relacionado: ").strip()
        cursor.execute("""
            SELECT m.equipo_id, e.nombre_equipo, m.tipoMmto, e.estado
            FROM mantenimientos m
            JOIN equipos_biomedicos e ON m.equipo_id = e.equipo_id
            WHERE m.mmto_id = %s
        """, (mmto_id,))
        resultado = cursor.fetchone()
        if not resultado:
            print("Mantenimiento no encontrado")
            return
        equipo_id,nombre_equipo,tipoMmto,estado_equipo = resultado
        reporte_id = input("ID del reporte: ").strip()
        if mongorep.buscar_reporte(reporte_id):
            print(f"El ID {reporte_id} ya existe. Usa uno diferente")
            return
        resumen = input("Resumen del problema y solucion: ").strip()
        notas_tecnicas = []
        nt = int(input("¿Cuántas notas técnicas desea ingresar?: "))
        for i in range(nt):
            nota = input(f"Nota técnica {i+1}: ")
            notas_tecnicas.append(nota)
        manual_pdf = input("Ruta del manual tecnico (PDF): ").strip()
        reporte_pdf = input("Ruta del archivo PDF del reporte tecnico: ").strip()

        reporte = {
            "reporte_id": reporte_id,
            "mmto_id" : int(mmto_id),
            "equipo_id": equipo_id,
            "nombre_equipo": nombre_equipo,
            "Tipo_reporte": tipoMmto,
            "reporte_fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tecnico_id": usuario_id,
            "tecnico_nombre": nombre_usuario,
            "Resumen": resumen,
            "Notas_tecnicas": notas_tecnicas,
            "estado": estado_equipo,
            "Rutas": {
                "manual_pdf": manual_pdf,
                "reporte_pdf": reporte_pdf
            }   
        }

        reporte_id_mongo = mongorep.insertar_reporte(reporte)
        print()
        print("Subiendo el reporte...")
        print(f"Reporte subido correctamente. ID en MongoDB: {reporte_id_mongo}")

    except Exception as e:
        print(f"Error al subir el reporte: {e}")
    finally:
        cursor.close()
        conexion.close()

#--------------------------BITACORAS------------------------

def crear_bitacora():
    try:
        equipo_id = input("Ingrese el ID del equipo (EQ-XXX-XXXX): ").strip().upper()
        if not verificar_equipo(equipo_id):
            print("El equipo no existe o el ID tiene formato incorrecto")
            return None
        while True:
            tecnico_id = input("ID del técnico que registra: ").strip()
            existe, es_tecnico, nombre_tecnico = verificar_tecnico(tecnico_id)
            
            if not existe:
                print("Usuario no encontrado. Intente nuevamente o presione enter para cancelar")
                if input("¿Desea intentar con otro ID? (S/N): ").strip().upper() != 'S':
                    return None
                continue
                
            if not es_tecnico:
                print("Error: El usuario no tiene rol de Técnico")
                if input("¿Desea intentar con otro ID? (S/N): ").strip().upper() != 'S':
                    return None
                continue
            break
        
        print(f"\nRegistrando bitácora a nombre de: {nombre_tecnico}")
        
        bitacora_id = f"bf-{equipo_id}-{datetime.now().strftime('%Y%m%d')}"

        if coleccion_bitacoras.find_one({"bitacora_id": bitacora_id}):
            print("Ya existe una bitacora para este equipo hoy. ¿Desea agregar entradas? (S/N)")
            if input().strip().upper() == 'S':
                return agregar_entrada_bitacora(bitacora_id)
            return None

        bitacora = {
            "bitacora_id": bitacora_id,
            "equipo_id": equipo_id,
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "entradas": [],
            "registro_por": tecnico_id,
            "nombre_tecnico": nombre_tecnico
        }
        
        coleccion_bitacoras.insert_one(bitacora)
        print(f"Bitácora creada exitosamente. ID: {bitacora_id}")
        return bitacora_id
        
    except Exception as e:
        print(f"Error al crear bitacora: {e}")
        return None

def agregar_entrada_bitacora(bitacora_id=None):
    try:
        if not bitacora_id:
            bitacora_id = input("Ingrese ID de la bitácora: ").strip()
        
        if not bitacora_id.startswith('bf-'):
            print("Error: ID de bitácora inválido. Debe comenzar con 'bf-'")
            return False

        bitacora = coleccion_bitacoras.find_one({"bitacora_id": bitacora_id})
        if not bitacora:
            print("Error: Bitácora no encontrada")
            return False

        while True:
            tecnico_id = input("ID del técnico que registra: ").strip()
            existe, es_tecnico, nombre_tecnico = verificar_tecnico(tecnico_id)
            
            if not existe:
                print("Error: Usuario no encontrado. Intente nuevamente o presione Enter para cancelar")
                if input("¿Desea intentar con otro ID? (S/N): ").strip().upper() != 'S':
                    return False
                continue
                
            if not es_tecnico:
                print("Error: El usuario no tiene rol de Técnico")
                if input("¿Desea intentar con otro ID? (S/N): ").strip().upper() != 'S':
                    return False
                continue
                
            break

        while True:
            evento = input("Descripción detallada del evento/falla: ").strip()
            if len(evento) < 10:
                print("La descripción debe tener al menos 10 caracteres")
                continue
            break
        
        nueva_entrada = {
            "fecha": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "evento": evento,
            "registrado_por": tecnico_id,
            "nombre_tecnico": nombre_tecnico
        }

        resultado = coleccion_bitacoras.update_one(
            {"bitacora_id": bitacora_id},
            {
                "$push": {"entradas": nueva_entrada},
                "$set": {
                    "ultima_actualizacion": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "registro_por": tecnico_id,
                    "nombre_tecnico": nombre_tecnico
                }
            }
        )
        
        if resultado.modified_count > 0:
            print("\nEntrada agregada exitosamente")
            return True
            
        print("\nNo se pudo agregar la entrada")
        return False
        
    except Exception as e:
        print(f"\nError al agregar entrada: {e}")
        return False

def eliminar_bitacora():
    try:
        print("\nELIMINAR BITÁCORA DE FALLAS")
        bitacora_id = input("Ingrese el ID de la bitacora a eliminar: ").strip()
        
        if not bitacora_id.startswith('bf-'):
            print("Error: ID de bitacora inválido. Debe comenzar con 'bf-'")
            return False
        
        bitacora = coleccion_bitacoras.find_one({"bitacora_id": bitacora_id})
        if not bitacora:
            print("Error: Bitácora no encontrada")
            return False
        
        print("\nBitácora encontrada:")
        print(f"ID: {bitacora['bitacora_id']}")
        print(f"Equipo: {bitacora['equipo_id']}")
        print(f"Fecha: {bitacora['fecha']}")
        print(f"Entradas registradas: {len(bitacora['entradas'])}")
        
        confirmacion = input("\n¿Está seguro que desea eliminar esta bitácora? (S/N): ").strip().upper()
        if confirmacion != 'S':
            print("Operación cancelada")
            return False

        resultado = coleccion_bitacoras.delete_one({"bitacora_id": bitacora_id})
        
        if resultado.deleted_count > 0:
            print("Bitácora eliminada exitosamente")
            return True
        else:
            print("No se pudo eliminar la bitácora")
            return False
            
    except Exception as e:
        print(f"Error al eliminar bitácora: {e}")
        return False

def consultar_bitacoras():
    try:
        print("CONSULTA DE BITÁCORAS DE FALLAS".center(60))
        print("\nOpciones de consulta:")
        print("1. Mostrar todas las bitácoras")
        print("2. Buscar por ID de equipo")
        print("3. Buscar por técnico responsable")
        print("4. Buscar por rango de fechas")
        print("5. Buscar por contenido en entradas")
        print("6. Volver al menú anterior")
        
        opcion = input("\nSeleccione una opción (1-6): ").strip()

        filtro = {"bitacora_id": {"$regex": "^bf-"}}
        if opcion == "1":
            pass
            
        elif opcion == "2":
            equipo_id = input("Ingrese el ID del equipo (EQ-XXX-XXXX): ").strip().upper()
            if not verificar_equipo(equipo_id):
                print("Error: El equipo no existe o el formato es incorrecto")
                return
            filtro["equipo_id"] = equipo_id
            
        elif opcion == "3":
            tecnico_id = input("Ingrese el ID del técnico: ").strip()
            existe, es_tecnico, _ = verificar_tecnico(tecnico_id)
            if not existe or not es_tecnico:
                print("Error: Técnico no válido")
                return
            filtro["registro_por"] = tecnico_id
            
        elif opcion == "4":
            fecha_inicio = input("Fecha inicial (YYYY-MM-DD): ").strip()
            fecha_fin = input("Fecha final (YYYY-MM-DD): ").strip()
            
            if not validar_fecha(fecha_inicio) or not validar_fecha(fecha_fin):
                print("Error: Formato de fecha inválido. Use YYYY-MM-DD")
                return
                
            filtro["fecha"] = {
                "$gte": fecha_inicio,
                "$lte": fecha_fin
            }
            
        elif opcion == "5":
            palabra_clave = input("Ingrese palabra clave a buscar en entradas: ").strip().lower()
            if not palabra_clave:
                print("Error: Debe ingresar un término de búsqueda")
                return
                
            filtro["entradas.evento"] = {"$regex": palabra_clave, "$options": "i"}
            
        elif opcion == "6":
            return
        else:
            print("Opción inválida")
            return
        bitacoras = list(coleccion_bitacoras.find(filtro).sort("fecha", -1))

        if not bitacoras:
            print("\nNo se encontraron bitácoras con los criterios especificados")
            return
            
        print(f"\n{'RESULTADOS DE BÚSQUEDA':^60}")
        print(f"{'='*60}")
        print(f"{'ID Bitácora':<20} | {'Equipo':<12} | {'Fecha':<12} | {'Entradas':<8} | {'Técnico'}")
        print("-"*60)
        
        for bit in bitacoras:
            print(f"{bit['bitacora_id']:<20} | {bit['equipo_id']:<12} | {bit['fecha']:<12} | "
                  f"{len(bit['entradas']):<8} | {bit.get('nombre_tecnico', 'N/A')}")

        ver_detalle = input("\n¿Desea ver el detalle de alguna bitácora? (ID o Enter para continuar): ").strip()
        if ver_detalle:
            mostrar_detalle_bitacora(ver_detalle)
            
    except Exception as e:
        print(f"\nError en la consulta: {str(e)}")

def mostrar_detalle_bitacora(bitacora_id):
    try:
        if not bitacora_id.startswith('bf-'):
            print("Error: ID de bitácora inválido")
            return
            
        bitacora = coleccion_bitacoras.find_one({"bitacora_id": bitacora_id})
        if not bitacora:
            print("Bitácora no encontrada")
            return
            
        print(f"DETALLE DE BITÁCORA: {bitacora_id}")
        print("="*80)
        print(f"Equipo: {bitacora['equipo_id']}")
        print(f"Fecha creación: {bitacora['fecha']}")
        print(f"Técnico responsable: {bitacora.get('nombre_tecnico', 'N/A')} ({bitacora['registro_por']})")
        print(f"Total entradas: {len(bitacora['entradas'])}")
        print(f"Última actualización: {bitacora.get('ultima_actualizacion', 'N/A')}")
        
        print("\nENTRADAS REGISTRADAS:")
        if not bitacora['entradas']:
            print("No hay entradas registradas")
        else:
            for i, entrada in enumerate(bitacora['entradas'], 1):
                print(f"\n[{i}] {entrada['fecha']}")
                print(f"   Registrado por: {entrada.get('nombre_tecnico', 'N/A')}")
                print(f"   Evento: {entrada['evento']}")
    except Exception as e:
        print(f"Error al mostrar detalle: {str(e)}")

def listar_bitacoras_disponibles():
    try:
        print("\n--- BITÁCORAS DISPONIBLES ---")
        print("Opciones de filtrado:")
        print("1. Mostrar todas")
        print("2. Filtrar por equipo")
        print("3. Filtrar por fecha")
        print("4. Cancelar")
        
        filtro = input("\nSeleccione opción de filtrado (1-4): ").strip()
        
        if filtro == "4":
            return
        
        query = {}
        
        if filtro == "2":
            equipo_id = input("Ingrese ID del equipo (EQ-XXX-XXXX): ").strip().upper()
            if not verificar_equipo(equipo_id):
                print("ID de equipo no válido o no existe.")
                return
            query["equipo_id"] = equipo_id
            
        elif filtro == "3":
            fecha_inicio = input("Fecha inicial (YYYY-MM-DD): ").strip()
            fecha_fin = input("Fecha final (YYYY-MM-DD): ").strip()
            
            if not (validar_fecha(fecha_inicio) and validar_fecha(fecha_fin)):
                print("Formato de fecha inválido. Use YYYY-MM-DD")
                return
                
            query["fecha"] = {"$gte": fecha_inicio, "$lte": fecha_fin}
        
        elif filtro != "1":
            print("Opción no válida.")
            return

        bitacoras = list(coleccion_bitacoras.find(query).sort("fecha", -1))
        
        if not bitacoras:
            print("\nNo hay bitácoras con los criterios seleccionados.")
            return
        
        print(f"\n{'ID Bitácora':<20} | {'Equipo':<15} | {'Fecha':<12} | {'Entradas':<8} | {'Técnico':<20}")
        print("-" * 80)
        
        for bit in bitacoras:
            bit_id = bit.get('bitacora_id', 'N/A')
            equipo = bit.get('equipo_id', 'Desconocido')
            fecha = bit.get('fecha', 'N/A')
            entradas = len(bit.get('entradas', []))
            tecnico = bit.get('nombre_tecnico', 'N/A')
            
            print(f"{bit_id:<20} | {equipo:<15} | {fecha:<12} | "
                  f"{entradas:<8} | {tecnico[:20]}")
    
    except Exception as e:
        print(f"\nError al listar bitácoras: {str(e)}")
        print(f"Tipo de error: {type(e).__name__}")
        if hasattr(e, 'details'):
            print(f"Detalles MongoDB: {e.details}")

def descargar_bitacora(bitacora_id, destino=None): 
    try:
        bitacora = coleccion_bitacoras.find_one({"bitacora_id": bitacora_id})
        if not bitacora:
            print("Bitácora no encontrada.")
            return False

        contenido = f"BITÁCORA DE FALLAS - {bitacora_id}\n"
        contenido += "="*50 + "\n"
        contenido += f"Equipo: {bitacora['equipo_id']}\n"
        contenido += f"Fecha creación: {bitacora['fecha']}\n"
        contenido += f"Técnico responsable: {bitacora.get('nombre_tecnico', 'N/A')}\n\n"
        contenido += "ENTRADAS REGISTRADAS:\n"

        for i, entrada in enumerate(bitacora['entradas'], 1):
            contenido += f"\nEntrada #{i}\n"
            contenido += f"Fecha: {entrada['fecha']}\n"
            contenido += f"Registrado por: {entrada.get('nombre_tecnico', 'N/A')}\n"
            contenido += f"Evento: {entrada['evento']}\n"

        if not destino:
            carpeta_descargas = os.path.join(os.path.expanduser('~'), 'Downloads')
            nombre_archivo = f"bitacora_{bitacora_id}.txt"
            destino = os.path.join(carpeta_descargas, nombre_archivo)

        with open(destino, 'w', encoding='utf-8') as archivo:
            archivo.write(contenido)

        print(f"Bitácora descargada exitosamente en: {destino}")
        return True

    except Exception as e:
        print(f"Error al descargar bitácora: {str(e)}")
        return False

#------------------------MANUALES------------------------

def listar_manuales_disponibles():
    try:
        print("\n--- MANUALES TÉCNICOS DISPONIBLES ---")
        manuales = list(coleccion_manuales.find().sort("nombre_equipo", 1))
        
        if not manuales:
            print("No hay manuales técnicos registrados.")
            return
        
        print(f"\n{'ID Manual':<20} | {'Equipo':<30} | {'Versión':<10} | {'Fecha Carga':<12}")
        print("-" * 80)
        
        for manual in manuales:
            manual_id = manual.get('manual_id', 'N/A')
            nombre = manual.get('nombre_equipo', 'Desconocido')
            version = manual.get('version', '0')
            fecha = manual.get('fecha_Carga', '')[:10] if 'fecha_Carga' in manual else 'N/A'
            
            print(f"{manual_id:<20} | {nombre[:30]:<30} | v{version:<9} | {fecha}")
    
    except Exception as e:
        print(f"\nError al listar manuales: {str(e)}")
        print(f"Tipo de error: {type(e).__name__}")
        if hasattr(e, 'details'):
            print(f"Detalles: {e.details}")

def descargar_manual(manual_id=None):
    try:
        if manual_id is None:
            listar_manuales_disponibles()
            manual_id = input("\nIngrese el ID del manual que desea descargar: ").strip()

        manual = coleccion_manuales.find_one({"manual_id": manual_id})

        if not manual:
            print("Manual no encontrado en la base de datos.")
            return

        ruta_origen = manual.get("file_path")
        if not ruta_origen or not os.path.isfile(ruta_origen):
            print(f" El archivo no existe en la ruta: {ruta_origen}")
            return

        carpeta_descargas = os.path.join(os.path.expanduser("~"), "Downloads")
        nombre_archivo = f"manual_{manual.get('nombre_equipo', 'Equipo')}_v{manual.get('version', 'X')}.pdf"
        destino = os.path.join(carpeta_descargas, nombre_archivo)

        shutil.copy2(ruta_origen, destino)
        print(f" Manual descargado exitosamente en: {destino}")

    except Exception as e:
        print(f" Error al descargar manual: {e}")


#--------------------------MENUS----------------------------

def login():
    conexion= conectar_db()
    cursor= conexion.cursor()
    nombre_usuario= input("Usuario: ").strip()
    password_input= input("Contraseña: ").strip()

    cursor.execute("SELECT usuario_id, password, rol FROM usuarios WHERE nombreUsuario= %s", (nombre_usuario,))
    resultado= cursor.fetchone()

    if resultado:
        usuario_id, password_bd, rol= resultado
        
        if password_input== password_bd:
            while True:
                print(f"\nBienvenido, {nombre_usuario}. Rol: {rol}")

                if rol== "Administrador":
                    print("Menú Administrador\n1. Crear/Modificar/Eliminar equipos \n2. Registrar/editar/eliminar usuario \n3. Ver mantenimientos \n4. Cargar manuales técnicos \n5. Gestión de bitácoras y reportes \n6. Cerrar sesión ")
                    opcion = input("Elija una opción (1-6): ").strip()
                    if opcion not in {"1", "2", "3", "4", "5", "6"}:
                        print("Opción inválida. Intente de nuevo.")
                        continue

                    elif opcion=="1":
                        print("Submenu \n1. Crear equipo \n2. Modificar equipo \n3. Eliminar equipo")
                        subopcion= input("Elija una opción (1-3): ").strip()
                        if subopcion not in {"1", "2", "3"}:
                            print("Opcion inválida. Intente de nuevo")
                        if subopcion=="1":
                            añadir_equipos()
                        elif subopcion == "2":
                            equipo_id = input("ID del equipo a modificar (EQ-XXX-XXXX): ") 
                            print("\nCampos modificables:")
                            print("1. Nombre del equipo")
                            print("2. Clase")
                            print("3. Marca")
                            print("4. Modelo")
                            print("5. Ubicación")
                            print("6. Estado")

                            opcion_campo = input("Seleccione el campo a modificar (1-6): ")

                            campos = {
                                '1': 'nombre_equipo',
                                '2': 'clase',
                                '3': 'marca',
                                '4': 'modelo',
                                '5': 'ubicacion',
                                '6': 'estado'
                            }

                            campo = campos.get(opcion_campo)
                            if not campo:
                                print("Opción inválida")
                                return
                            else:
                                if campo == "clase":
                                    clase_opciones = {
                                        "1": "Clase I",
                                        "2": "Clase IIA",
                                        "3": "Clase IIB",
                                        "4": "Clase III"
                                    }
                                    print("\nClases disponibles:")
                                    for key, value in clase_opciones.items():
                                        print(f"{key}. {value}")
                                    clase_input = input("Seleccione la nueva clase: ").strip()
                                    nuevo_valor = clase_opciones.get(clase_input)
                                    if not nuevo_valor:
                                        print("Opción inválida.")
                                        return
                                elif campo == "estado":
                                    estado_opciones = {
                                        "1": "Disponible",
                                        "2": "En mantenimiento",
                                        "3": "Dado de baja"
                                    }
                                    print("\nEstados disponibles:")
                                    for key, value in estado_opciones.items():
                                        print(f"{key}. {value}")
                                    estado_input = input("Seleccione el nuevo estado: ").strip()
                                    nuevo_valor = estado_opciones.get(estado_input)
                                    if not nuevo_valor:
                                        print("Opción inválida.")
                                        return
                                else:
                                    while True:
                                        nuevo_valor = input(f"Nuevo valor para {campo}: ").strip()
                                        if nuevo_valor:
                                            break
                                        else:
                                            print("Este campo no puede quedar vacío.")
        
                                if modificar_equipo(equipo_id, campo, nuevo_valor):
                                    print("Equipo actualizado correctamente.")
                                else:
                                    print("Error al modificar el equipo.") 
                        elif subopcion=="3": 
                            eliminar_equipo()
                            
                    elif opcion=="2":
                        print("Submenu \n1. Registrar usuario \n2. Editar usuario \n3. Eliminar usuario")
                        subopcion= int(input("Elija una opción: "))
                        if subopcion== 1:
                            registrar_usuario()
                        elif subopcion== 2:
                            editar_usuario()
                        elif subopcion== 3:
                            eliminar_usuario()
                        else:
                            print("Opcion invalida")
                    
                    elif opcion=="3":
                        print("\n1. Ver todos los mantenimientos")
                        print("2. Ver mantenimientos por tecnico")
                        subop = input("Elija una opción: ").strip()
                        if subop not in {"1", "2", "3"}:
                            print("Opcion inválida. Intente de nuevo")
                            continue
                        
                        if subop == "1":
                            Historialmmtos()

                        elif subop == "2":
                            tecnico_user = input("Ingrese el nombre de usuario del técnico: ").strip()

                            cursor.execute("""
                                SELECT usuario_id FROM usuarios 
                                WHERE nombreUsuario = %s AND rol = 'Técnico'
                                """, (tecnico_user,))
        
                            resultado = cursor.fetchone()

                            if resultado:
                                tecnico_id = resultado[0]
                                ver_mis_mantenimientos(tecnico_id)
                            else:
                                print("Técnico no encontrado o no tiene rol de 'Técnico'")
                        else:
                            print("Opción inválida. Intente nuevamente.")
                            continue
                            
                    elif opcion=="4":
                        try:
                            equipo_id = input("ID del equipo asociado al manual(EQ-XXX-XXXX): ")
                            if not verificar_equipo(equipo_id): 
                                print("El ID del equipo no existe en la base de datos") 
                            else: 
                                conexion = conectar_db()
                                cursor = conexion.cursor()
                                cursor.execute("SELECT nombre_equipo FROM equipos_biomedicos WHERE equipo_id = %s", (equipo_id,))
                                nombre_equipo = cursor.fetchone()[0]
                                cursor.close()
                                conexion.close() 
                                version = input("Versión del manual (ej: 1.2): ").strip() 
                                manual_id = f"man-{equipo_id.replace('EQ-', 'EQ-')}-v{version}"

                                manual = {
                                    "manual_id": manual_id,
                                    "equipo_id": equipo_id,
                                    "nombre_equipo": nombre_equipo,
                                    "version": version,
                                    "fecha_Carga": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                                    "Cargado_por": nombre_usuario,
                                    "file_path": input("Ruta del archivo PDF (ej: /uploads/manuals/): ").strip(),
                                    "notas": input("Notas adicionales: ").strip() or "Sin notas"
                                }
                                db.manuales_tecnicos.insert_one(manual)
                                print("Manual del equipo cargado con exito")
                                print(f"Id del manual: {manual_id}")
                        except Exception as e:
                            print(f"Error inesperado: {e}")
                    
                    elif opcion=="5":
                        print("\nSubmenu \n1. Gestion de bitacora de fallas \n2. Gestión de reportes tecnicos \n3. Volver al menú anterior")
                        subopcion= input("Elija una opción (1-3): ").strip()
                        
                        if subopcion =="1":
                            while True:
                                print("GESTIÓN DE BITÁCORAS DE FALLAS")
                                print("1. Crear nueva bitácora")
                                print("2. Agregar entrada a bitácora")
                                print("3. Consultar bitácoras")
                                print("4. Ver detalle completo")
                                print("5. Eliminar bitácora")
                                print("6. Volver al menú anterior")
                                
                                subop = input("\nSeleccione una opción (1-6): ").strip()
                                
                                if subop == "1":
                                    crear_bitacora()
                                elif subop == "2":
                                    agregar_entrada_bitacora()
                                elif subop == "3":
                                    consultar_bitacoras()
                                elif subop == "4":
                                    bitacora_id = input("Ingrese ID de la bitácora: ").strip()
                                    mostrar_detalle_bitacora(bitacora_id)
                                elif subop == "5":
                                    eliminar_bitacora()
                                elif subop == "6":
                                    print("Regresando...")
                                    break
                        elif subopcion=="2":
                            while True:
                                print("Submenu \n1.Ver reportes tecnicos \n2.Modificar estado de reporte tecnico \n3.Eliminar reporte tecnico \n4. Volver al menú anterior")
                                reportes_subop= input("Elija una opcion: ")

                                if reportes_subop == "1":
                                    reportes = mongorep.consultar_reportes_usuario({"rol":"Administrador", "id":nombre_usuario})
                                    if reportes:
                                        print(f"\nTotal de reportes encontrados: {len(reportes)}")
                                        for r in reportes:
                                            print(f"\nID Reporte: {r['reporte_id']}")
                                            print(f"Mantenimiento ID: {r['mmto_id']}")
                                            print(f"Fecha: {r['reporte_fecha']}")
                                            print(f"Equipo: {r['equipo_id']} - {r['nombre_equipo']}")
                                            print(f"Tipo: {r['Tipo_reporte']}")
                                            print(f"Técnico: {r['tecnico_id']} - {r['tecnico_nombre']}")
                                            print(f"Estado: {r['estado']}")
                                            print(f"Resumen: {r['Resumen']}")
                                            print("Notas técnicas:")
                                            for nota in r.get("Notas_tecnicas", []):
                                                print(f"   - {nota}")
                                            print(f"Manual PDF: {r['Rutas']['manual_pdf']}")
                                            print(f"Reporte PDF: {r['Rutas']['reporte_pdf']}")
                                    else:
                                        print("No hay reportes registrados.")

                                elif reportes_subop == "2":
                                    rep_id = input("ID del reporte a modificar: ")
                                    nuevo_estado = input("Nuevo estado (ej. Disponible, En mantenimiento, Dado de baja): ")
            
                                    if mongorep.actualizar_estado(rep_id, nuevo_estado):
                                        print("Estado del reporte actualizado correctamente")
                                    else:
                                        print("No se encontró el reporte o no se actualizó.")
                                    
                                elif reportes_subop == "3":
                                    rep_id = input("ID del reporte a eliminar: ")
                                    mongorep.eliminar_reporte(rep_id)
                                    print("Reporte eliminado correctamente")
                                
                                elif reportes_subop == "4":
                                    print("Regresando...")
                                    break
                                else:
                                    print("Opcion invalida")
                                    continue
                        else:
                            print("Opción inválida")
                            continue 

                    elif opcion=="6":
                        print("Sesion cerrada correctamente")
                        break

                    else:
                        print("Opción inválida")
                        continue 
                    
                elif rol== "Ingeniero clínico":
                    print("Menú Ingeniero Clínico \n1. Ver equipos \n2. Ver historial de mantenimiento \n3. Ver reportes técnicos \n4. Descargar manuales y bitácoras \n5. Buscar por palabra clave \n6. Cerrar sesión")
                    opcion= int(input("Elija una opcion: "))
                    
                    if opcion==1:
                        print("1. Ver equipos por ID, 2. Ver todos los equipos")
                        subop=input("Elija una opción: ")
                        if subop not in {"1","2"}:
                            print("Opción inválida. Intente de nuevo")
                        elif subop=="1":
                            equipo_id= input("Ingrese la ID del equipo a buscar (EQ-XXX-XXXX): ")
                            buscar_equipo_por_id(equipo_id)
                        elif subop=="2":
                            ver_equipos()
                        

                    elif opcion==2:
                        Historialmmtos()

                    elif opcion ==3:
                        reportes = mongorep.consultar_reportes_usuario({"rol":"Ingeniero Clinico","id":nombre_usuario}) 
                        if reportes:
                            for i in reportes:
                                print(f"\n ID del reporte: {i['reporte_id']}") 
                                print(f"Fecha: {i['reporte_fecha']}")
                                print(f"Tipo: {i['Tipo_reporte']}")
                                print(f"Equipo: {i["nombre_equipo"]}")
                                print(f"Estado: {i['estado']}")
                                print(f"Resumen: {i['Resumen']}")
                                print("Notas tecnicas:")
                                for nota in i["Notas_tecnicas"]:
                                    print(f"{nota}")
                                    print("Manual tecnico:", i['Rutas']['manual_pdf'])
                                    print("Reporte PDF:", i['Rutas']['reporte_pdf'])
                            else:
                                print("Sin reportes registrados")
                    elif opcion ==4:
                        while True:
                            print("DESCARGAR MANUALES Y BITÁCORAS")
                            print("1. Listar manuales técnicos disponibles")
                            print("2. Descargar manual técnico")
                            print("3. Listar bitácoras disponibles")
                            print("4. Descargar bitácora")
                            print("5. Volver al menú principal")
                            
                            opcion = input("\nSeleccione una opción (1-5): ").strip()
                            
                            if opcion == "1":
                                listar_manuales_disponibles()
                            elif opcion == "2":
                                descargar_manual()
                            elif opcion == "3":
                                listar_bitacoras_disponibles()
                            elif opcion == "4":
                                bitacora_id = input("Ingrese el ID de la bitácora a descargar: ").strip() 
                                descargar_bitacora(bitacora_id)
                            elif opcion == "5":
                                print("Volviendo al menú principal...")
                                break
                            else:
                                print("Opción inválida. Intente nuevamente.")
                    elif opcion==5:
                        tag = input("Ingrese palabra clave a buscar: ")
                        resultados = mongorep.buscar_por_tag(tag)
                        if resultados:
                            print("\n Resultados encontrados:")
                        for r in resultados:
                            print(f"- {r['reporte_id']} / {r['nombre_equipo']} / {r['Resumen']}")
                        else:
                            print("No se encontraron reportes con esa palabra clave")
                    elif opcion==6:
                        print("Sesion cerrada correctamente")
                        break
                    else:
                        print("Opción inválida. Intente nuevamente.")
                        continue

                elif rol== "Técnico":
                    print("Menú Técnico \n1.Ver equipos asignados \n2.Registrar mantenimiento preventivo \n3.Registrar mantenimiento correctivo \n4.Subir reporte tecnico \n5.Consultar reportes anteriores \n6.Cerrar cesion")
                    opcion = input("Elija una opcion: ")
                    if opcion == "1":
                        ver_equipos_asignados(nombre_usuario)

                    elif opcion == "2":
                        registrar_mmto(usuario_id)

                    elif opcion == "3":
                        registrar_mmto(usuario_id)

                    elif opcion == "4":
                        subir_reporte_mongo(usuario_id)
                    
                    elif opcion == "5":
                        reportes = mongorep.consultar_reportes_usuario({"rol":"Tecnico","id":usuario_id})
                        if reportes:
                            for i in reportes:
                                print(f"ID del reporte: {i['reporte_id']}")
                                print(f"Fecha: {i['reporte_fecha']}")
                                print(f"Tipo: {i['Tipo_reporte']}")
                                print(f"Equipo: {i["nombre_equipo"]}")
                                print(f"Estado: {i['estado']}")
                                print(f"Resumen: {i['Resumen']}")
                                print("Notas tecnicas:")
                                for nota in i["Notas_tecnicas"]:
                                    print(f"{nota}")
                                print("Manual tecnico:", i['Rutas']['manual_pdf'])
                                print("Reporte PDF:", i['Rutas']['reporte_pdf'])
                        else:
                            print("Sin reportes registrados")
                    
                    elif opcion=="6":
                        print("Sesion cerrada correctamente")
                        break
                    else:
                        print("Opción inválida. Intente nuevamente.")
                        continue
        else:
            print("Contraseña incorrecta.")
    else:
        print("Usuario no encontrado.")

    cursor.close()
    conexion.close()

tabla_usuario()
tabla_equipos()
tabla_mantenimiento()
while True:
    opcion= input("\n¿Deseas (1) Registrar usuario,  (2) Iniciar sesión o (3) Salir del programa? ")
    
    if opcion== "1":
        registrar_usuario()
    elif opcion== "2":
        login()
    elif opcion== "3":
        print("Saliendo del programa...")
        break
    else:
        print("Opción inválida.")