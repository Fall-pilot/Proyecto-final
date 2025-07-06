import mysql.connector
import json
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

def contraseñas_json():
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
            json.dump(backup, f, indent=4, ensure_ascii=False)

        print("Backup guardado exitosamente en contraseñas.json.")
    except Exception as e:
        print(f"Error al generar backup: {e}")
    finally:
        cursor.close()
        conexion.close()

def validar_equipos(campo):
    while True:
        valor = input(f"{campo}: ").strip()
        if valor:
            return valor
        print(f"El campo '{campo}' no puede estar vacío.")

def validar(msj):
    while True:
        contador=0
        try:
            entrada=int(input(msj))
            return entrada
        except ValueError:
            print("Solo números enteros!")
            contador+=1
        if contador==3:
            print("No se permiten más intentos")
            break

def conectar_db():
    return mysql.connector.connect(
        host="localhost",
        user="Informatica1",
        password="info2025_2",
        database="PF_Informatica1"
    )

def validar_fecha(fecha_str):
    try:
        datetime.strptime(fecha_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def tabla_usuario():
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
            equipo_id VARCHAR(15) PRIMARY KEY,
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
    cursor.close()
    conexion.close()

def registrar_usuario():
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
            cedula= input("Cédula profesional: ").strip()
            contacto= input("Contacto: ").strip()

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
    
    print(f"\n--- Información actual del usuario ---")
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
        nueva_cedula = input("Cédula profesional (Enter para no cambiarla): ").strip()
        nuevo_contacto = input("Contacto (Enter para no cambiarlo): ").strip()
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

def equipo_id(tipo_input):
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
                        else:
                            print("Opcion invalida")
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
                            print("Opción inválida.")
                    
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
                        except Exception as e:
                            print(f"Error inesperado: {e}")
                    
                    elif opcion=="5":
                        print("Submenu \n1.Ver reportes tecnicos \n2.Modificar estado de reporte tecnico \n3.Eliminar reporte tecnico")
                        subop = input("Elija una opcion: ")

                        if subop == "1":
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

                        elif subop == "2":
                            rep_id = input("ID del reporte a modificar: ")
                            nuevo_estado = input("Nuevo estado (ej. Disponible, En mantenimiento, Dado de baja): ")
    
                            if mongorep.actualizar_estado(rep_id, nuevo_estado):
                                print("Estado del reporte actualizado correctamente")
                            else:
                                print("No se encontró el reporte o no se actualizó.")
                            
                        elif subop == "3":
                            rep_id = input("ID del reporte a eliminar: ")
                            mongorep.eliminar_reporte(rep_id)
                            print("Reporte eliminado correctamente")
                        
                        else:
                            print("Opcion invalida")
                        
                    elif opcion=="6":
                        print("Sesion cerrada correctamente")
                        break

                    else:
                        print("Opción inválida")
                        continue 
                    
                elif rol== "Ingeniero clínico":
                    print("Menú Ingeniero Clínico \n1. Ver equipos \n2. Ver historial de mantenimiento \n3. Ver reportes técnicos \n4. Descargar manuales y bitácoras \n5. Buscar por palabra clave \n6. Cerrar sesión")
                    print()
                    opcion = input("Elija una opción (1-6): ").strip()
                    if opcion not in {"1", "2", "3", "4", "5", "6"}:
                        print("Opción inválida. Intente de nuevo.")
                        continue
                    
                    if opcion=="1":
                        ver_equipos()

                    elif opcion=="2":
                        Historialmmtos()

                    elif opcion =="3":
                        reportes = mongorep.consultar_reportes_usuario({"rol":"Ingeniero Clinico","id":nombre_usuario}) 
                        if reportes:
                            for i in reportes:
                                print(f"\nID del reporte: {i['reporte_id']}") 
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

                    elif opcion =="4":
                        print()
                        print("Manuales Tecnicos")
                        print()
                        for i in mongorep.obtener_manuales():
                            print(f"{i['manual_id']} / {i['nombre_equipo']} / v{i['version']}")
                            print(f"Ruta: {i['file_path']}")
                            print(f"Notas: {i['notas']}")

                        print("Bitacoras")
                        ...


                    elif opcion=="5":
                        tag = input("Ingrese palabra clave a buscar: ")
                        resultados = mongorep.buscar_por_tag(tag)
                        if resultados:
                            print("\n Resultados encontrados:")
                        for r in resultados:
                            print(f"- {r['reporte_id']} / {r['nombre_equipo']} / {r['Resumen']}")
                        else:
                            print("No se encontraron reportes con esa palabra clave")
                    
                    elif opcion == "6":
                        print("Sesión cerrada correctamente.")
                        break



                elif rol== "Técnico":
                    print("Menú Técnico \n1.Ver equipos asignados \n2.Registrar mantenimiento preventivo \n3.Registrar mantenimiento correctivo \n4.Subir reporte tecnico \n5.Consultar reportes anteriores \n6.Cerrar cesion")
                    opcion = input("Elija una opción (1-6): ").strip()
                    if opcion not in {"1", "2", "3", "4", "5", "6"}:
                        print("Opción inválida. Intente de nuevo.")
                        continue
                    if opcion == "1":
                        ver_equipos_asignados(nombre_usuario)

                    elif opcion == "2":
                        registrar_mmto(usuario_id,"Preventivo")

                    elif opcion == "3":
                        registrar_mmto(usuario_id,"Correctivo")

                    elif opcion == "4":
                        subir_reporte_mongo(usuario_id,nombre_usuario)
                    
                    elif opcion == "5":
                        reportes = mongorep.consultar_reportes_usuario({"rol":"Tecnico","id":usuario_id})
                        if reportes:
                            for i in reportes:
                                print(f"\nID del reporte: {i['reporte_id']}")
                                print(f"Fecha: {i['reporte_fecha']}")
                                print(f"Tipo: {i['Tipo_reporte']}")
                                print(f"Equipo: {i['nombre_equipo']}")
                                print(f"Estado: {i['estado']}")
                                print(f"Resumen: {i['Resumen']}")
                                print("Notas tecnicas:")
                                for nota in i["Notas_tecnicas"]:
                                    print(f"{nota}")
                                print("Manual tecnico:", i['Rutas']['manual_pdf'])
                                print("Reporte PDF:", i['Rutas']['reporte_pdf'])
                        else:
                            print("Sin reportes registrados")
                    elif opcion == "6":
                        print("Sesión cerrada correctamente.")
                        break

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
    print()
    print("------- BIENVENID@ AL SISTEMA DE GESTION DE MANTENIMIENTO PREVENTIVO Y CORRECTIVO DE EQUIPOS BIOMEDICOS HOSPITALARIOS -------")
    opcion= input("\n¿Deseas (1) Registrar usuario o (2) Iniciar sesión? ")
    
    if opcion== "1":
        registrar_usuario()
    elif opcion== "2":
        login()
    else:
        print("Opción inválida.")