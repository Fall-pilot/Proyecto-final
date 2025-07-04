from pymongo import MongoClient

#Conexion a MongoDB

client = MongoClient("mongodb://localhost:27017/")
db = client["PF_Informatica1"]
coleccion_reportes = db["reportes_tecnicos"]

#Funciones CRUD

def insertar_reporte(reporte):
    """
    Inserta un nuevo reporte tecnico en MongoDB
    Pide los datos del reporte y retorna un ObjectId
    """
    return coleccion_reportes.insert_one(reporte).inserted_id

def consultar_reportes_usuario(usuario):
    """
    Consulta reportes segun el rol
    En el argumento se pide el rol y el id
    Retorna la lista de reportes
    """
    if usuario["rol"] == "admin":
        return list(coleccion_reportes.find())
    else:
        return list(coleccion_reportes.find({"tecnico_id":usuario["id"]}))
    
def eliminar_reporte(reporte_id):
    """
    Elimina un reporte por el ID
    """
    return coleccion_reportes.delete_one({"reporte_id":reporte_id})

def actualizar_estado(reporte_id, nuevo_estado):
    """
    Actualiza el "estado" de un reporte
    """
    return coleccion_reportes.update_one(
        {"reporte_id":reporte_id},
        {"$set":{"estado":nuevo_estado}}
    )

def buscar_reporte(reporte_id):
    """
    Busca un reporte por su ID
    Retorna el reporte encontrado o None si no existe
    """
    return coleccion_reportes.find_one({"reporte_id":reporte_id})

def validar_texto(texto):
    """
    Valida si el texto es alfabetico y no es vacio
    """
    return texto.replace(" ","").isalpha() and len(texto) > 0
