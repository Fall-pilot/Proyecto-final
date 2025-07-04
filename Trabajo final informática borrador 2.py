import mysql.connector
import json
from mantenimiento import *
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

def tabla_mantenimiento():
    conexion= conectar_db()
    cursor= conexion.cursor()
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
    conexion.commit()
    cursor.close()
    conexion.close()

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
        while True:
            fecha_ingreso= input("Fecha de ingreso (YYYY-MM-DD): ").strip() 
            if validar_fecha(fecha_ingreso):
                break
            else:
                print("Formato de fecha inválido")
                
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
    
def ver_equipos_asignados(usuario_nombre):
    try:
        cursor.execute("""
        SELECT e.equipo_id, e.nombre_equipo, e.tipo_equipo, e.ubicacion
        FROM equipos_biomedicos e
        JOIN asignaciones a ON e.equipo_id = a.equipo_id
        JOIN usuarios u ON a.usuario_id = u.usuario_id
        WHERE u.nombreUsuario = %s
        """, (usuario_nombre,))
        equipos = cursor.fetchall()
        if equipos:
            for j in equipos:
                print(f"- ID: {j[0]} / {j[1]} ({j[2]}) en {j[3]}")
        else:
            print("Sin equipos asignados.")
    
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
        
def verificar_equipo(equipo_id):
    if not equipo_id.startswith('EQ-') or len(equipo_id.split('-')) != 3:
        return False
    
    try:
        conexion = conectar_db()
        cursor = conexion.cursor()
        cursor.execute("SELECT 1 FROM equipos_biomedicos WHERE equipo_id = %s", (equipo_id,))
        return cursor.fetchone() is not None
    finally:
        cursor.close()
        conexion.close()
        
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

def subir_reporte_mongo(usuario_id,nombre_usuario):
    reporte = {
        "reporte_id": input("ID del reporte: "),
        "mmto_id" : int(input("ID del mantenimiento relacionado: ")),
        "equipo_id": input("ID del equipo: "),
        "nombre_equipo": input("Nombre del equipo: "),
        "Tipo_reporte": input("Tipo de mantenimiento (Preventivo/Correctivo): "),
        "reporte_fecha": datetime.now(),
        "tecnico_id": usuario_id,
        "tecnico_nombre": nombre_usuario,
        "Resumen": input("Resumen del problema y solución: "),
        "Notas_tecnicas": [],
        "estado": "Pendiente",
        "Rutas": {
            "manual_pdf": input("Ruta del manual técnico (PDF): "),
            "reporte_pdf": input("Ruta del archivo PDF del reporte: ")
        }
    }

    nt = int(input("¿Cuántas notas técnicas desea ingresar?: "))
    for i in range(nt):
        nota = input(f"Nota técnica {i+1}: ")
        reporte["Notas_tecnicas"].append(nota)

    reporte_id_mongo = mongorep.insertar_reporte(reporte)
    print(f"Reporte subido correctamente. ID en MongoDB: {reporte_id_mongo}")
    
def login():
    conexion= conectar_db()
    cursor= conexion.cursor()
    nombre_usuario= input("Usuario: ").strip()
    password= input("Contraseña: ").strip()

    cursor.execute("SELECT usuario_id, password, rol FROM usuarios WHERE nombreUsuario= %s", (nombre_usuario,))
    resultado= cursor.fetchone()

    if resultado:
        usuario_id, password_json, rol= resultado
        password_bd= json.loads(password_json)["password"]
        
        if password== password_bd:
            while True:
                print(f"\nBienvenido, {nombre_usuario}. Rol: {rol}")

                if rol== "Administrador":
                    print("Menú Administrador\n1. Crear/Modificar/Eliminar equipos \n2. Registrar/editar/eliminar usuario \n3. Ver mantenimientos \n4. Cargar manuales técnicos \n5. Gestión de bitácoras y reportes \n6. Cerrar sesión ")
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
                        print("\m1. Ver todos los mantenimientos")
                        print("2. Ver mantenimientos por tecnico")
                        subop = input("Elija una opcion: ")
                        if subop == "1":
                            Historialmmtos()
                        elif subop == "2":
                            tecnico = input("Ingrese el usuario del técnico ligado al mantenimiento: ")
                            cursor.execute("SELECT usuario_id FROM usuarios WHERE nombreUsuario = %s",(tecnico,))
                            tecnico_id = cursor.fetchone()
                            if tecnico_id:
                                ver_mis_mantenimientos(tecnico_id[0])
                            else:
                                print("Tecnico no encontrado")
                        else:
                            print("Opcion invalida")
                    
                    if opcion==4:
                        try:
                            while True:
                                equipo_id = input("ID del equipo (formato EQ-ABC-1234): ").strip()
                                if not equipo_id.startswith('EQ-') or len(equipo_id.split('-')) != 3:
                                    print("Formato incorrecto. Debe ser EQ-XXX-XXXX (ej: EQ-ICU-0032)")
                                else:
                                    break
                            equipo_id = input("ID del equipo asociado al manual: ")
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
                        except Exeption as e:
                            print(f"Error inesperado: {e}")
                    
                    if opcion==5:
                        print("Submenu \n1.Ver reportes tecnicos \n2.Modificar estado de reporte tecnico \n3.Eliminar reporte tecnico")
                        subop = input("Elija una opcion: ")

                        if subop == "1":
                            for i in mongorep.consultar_reportes_usuario({"rol":"Administrador","id":nombre_usuario}):
                                print(f"{i["reporte_id"]} / {i["nombre_equipo"]} / {i["estado"]}")

                        elif subop == "2":
                            rep_id = input("ID del reporte a eliminar: ")
                            mongorep.eliminar_reporte(rep_id)
                            print("Reporte eliminado correctamente")
                        
                        elif subop == "3":
                            rep_id = input("ID del reporte a modificar: ")
                            nuevo_estado = input("Nuevo estado: ")
                            mongorep.actualizar_estado(rep_id,nuevo_estado)
                            print("Estado del reporte actualizado correctamente")
                        
                        else:
                            print("Opcion invalida")
                        
                    if opcion==6:
                        print("Sesion cerrada correctamente")
                        break

                    else:
                        print("Opción inválida")
                        continue 
                    
                elif rol== "Ingeniero clínico":
                    print("Menú Ingeniero Clínico \n1. Ver equipos \n2. Ver historial de mantenimiento \n3. Ver reportes técnicos \n4. Descargar manuales y bitácoras \n5. Buscar por palabra clave \n6. Cerrar sesión")
                    opcion= int(input("Elija una opcion: "))
                    
                    if opcion==1:
                        ver_equipos()

                    elif opcion==2:
                        Historialmmtos()

                    elif opcion ==3:
                        for i in mongorep.consultar_reportes_usuario({"rol":"Ingeniero Clinico","id":nombre_usuario}):
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
                        print("Manuales Tecnicos")
                        for i in mongorep.obtener_manuales():
                            print(f"{i['manual_id']} / {i['nombre_equipo']} / v{i['version']}")
                            print(f"Ruta: {i['file_path']}")
                            print(f" Notas: {i['notas']}")

                        print("Bitacoras")
                        ...


                    elif opcion==5:
                        tag = input("Ingrese palabra clave a buscar: ")
                        resultados = mongorep.buscar_por_tag(tag)
                        if resultados:
                            print("\n Resultados encontrados:")
                        for r in resultados:
                            print(f"- {r['reporte_id']} / {r['nombre_equipo']} / {r['Resumen']}")
                        else:
                            print("No se encontraron reportes con esa palabra clave")



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