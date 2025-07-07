from pymongo import MongoClient
from datetime import datetime

#Conexion a MongoDB

client = MongoClient("mongodb://localhost:27017/")
db = client["PF_Informatica1"]
coleccion_reportes = db["reportes_tecnicos"]
coleccion_manuales = db["manuales_tecnicos"]
coleccion_bitacoras = db["bitacoras"]

#Funciones CRUD

def insertar_reporte(reporte):
    """
    Inserta un nuevo reporte tecnico en MongoDB
    Pide los datos del reporte y retorna un ObjectId
    Usa el campo "reporte_id" como _id
    """
    reporte["_id"] = reporte["reporte_id"]
    return coleccion_reportes.insert_one(reporte).inserted_id


def consultar_reportes_usuario(usuario):
    """
    Consulta reportes segun el rol
    En el argumento se pide el rol y el id
    Retorna la lista de reportes
    """
    if usuario["rol"] in ["Administrador","Ingeniero Clinico"]:
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
    resultado = coleccion_reportes.update_one(
        {"reporte_id": reporte_id},
        {"$set": {"estado": nuevo_estado}}
    )
    return resultado.modified_count > 0

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

def insertar_manual(manual_data):
    coleccion = db["manuales_tecnicos"]
    coleccion.insert_one(manual_data)
    print("Manual cargado correctamente")

def buscar_por_tag(tag):
    coleccion = db["reportes_tecnicos"]
    resultados = coleccion.find({
        "$or": [
            {"Resumen": {"$regex": tag, "$options": "i"}},
            {"Notas_tecnicas": {"$elemMatch": {"$regex": tag, "$options": "i"}}},
            {"nombre_equipo": {"$regex": tag, "$options": "i"}}
        ]
    })
    return list(resultados)

def obtener_manuales():
    return list(coleccion_manuales.find())

def buscar_reporte(reporte_id):
    return coleccion_reportes.find_one({"reporte_id": reporte_id})

