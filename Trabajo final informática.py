import mysql.connector

conexion= mysql.connector.connect(host="localhost", user="root", password="")
cursor= conexion.cursor()

cursor.execute("CREATE DATABASE IF NOT EXISTS mantenimiento_equipos")
cursor.execute("USE mantenimiento_equipos")
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    usuario_id INT AUTO_INCREMENT PRIMARY KEY,
    nombreUsuario VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL,
    rol ENUM('Administrador', 'Ingeniero clínico', 'Técnico') NOT NULL
)
""")

print("Base de datos y tabla creadas correctamente.")

cursor= conexion.cursor()
cursor.execute("")
nombre_usuario= input("Ingrese el nombre de usuario: ").strip()
password= input("Ingrese la contraseña: ").strip()
rol= input("Ingrese el rol (Administrador, Ingeniero clínico, Técnico): ").strip()

cursor.execute("SELECT * FROM usuarios WHERE nombreUsuario= %s", (nombre_usuario,))
resultado = cursor.fetchone()

if resultado:
    print("El nombre de usuario ya existe. Intenta con otro.")
else:
    cursor.execute("""INSERT INTO usuarios (nombreUsuario, password, rol)VALUES (%s, %s, %s)""", (nombre_usuario, password, rol))
    conexion.commit()
    print("Usuario agregado exitosamente.")

cursor.close()
conexion.close()


