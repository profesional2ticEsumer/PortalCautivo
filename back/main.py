# Librerías
import datetime
from fastapi import FastAPI, File, Request, Response, UploadFile
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl
import os
import json

# Inicializar FastAPI
app = FastAPI()

# Carpeta donde se guardarán los archivos
UPLOAD_FOLDER = "files/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Archivo donde se guardará la selección de archivos para el carrusel
CAROUSEL_FILE = "files/carousel_files.json"

# Montar la carpeta static en la fastapi
app.mount("/static", StaticFiles(directory="../front/static"), name="static")

# Montar la carpeta de subidas en la fastapi
app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")

# Cargar la vista de inicio del portal cautivo
@app.get("/")
async def vista_inicio():
    return FileResponse("../front/views/portal.html")

# Cargar vista de administración para subir los archivos y estilos del portal cautivo
@app.get("/administration")
async def vista_administration():
    return FileResponse("../front/views/administration.html")

# Endpoint para subir archivos
@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    # Obtener la fecha y hora actuales
    now = datetime.datetime.now()
    # Formatear la fecha y hora
    timestamp = now.strftime("%d-%m-%Y-%H-%M-%S")
    # Crear el nuevo nombre del archivo
    filename = f"IMG-{timestamp}{os.path.splitext(file.filename)[1]}"
    file_location = os.path.join(UPLOAD_FOLDER, filename)
    with open(file_location, "wb") as f:
        f.write(file.file.read())
    return JSONResponse(content={"message": f"Archivo {filename} subido con éxito."})


# Endpoint para obtener la lista de archivos
@app.get("/files/")
async def get_files():
    files = os.listdir(UPLOAD_FOLDER)
    return JSONResponse(content={"files": files})

# Endpoint para eliminar archivos
@app.delete("/delete_file/")
async def delete_file(filename: str):
    file_location = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_location):
        os.remove(file_location)
        
        # Actualizar el archivo carousel_files.json
        if os.path.exists(CAROUSEL_FILE):
            with open(CAROUSEL_FILE, "r") as f:
                data = json.load(f)
            
            # Eliminar el archivo de la lista y del diccionario de URLs
            if filename in data["files"]:
                data["files"].remove(filename)
            if filename in data["urls"]:
                del data["urls"][filename]
            
            # Guardar los cambios
            with open(CAROUSEL_FILE, "w") as f:
                json.dump(data, f, indent=4)
        
        return JSONResponse(content={"message": f"Archivo {filename} eliminado con éxito."})
    return JSONResponse(content={"message": f"Archivo {filename} no encontrado."}, status_code=404)

class CarouselFiles(BaseModel):
    files: list[str]
    urls: dict[str, HttpUrl] = {}

@app.post("/set_carousel_files/")
async def set_carousel_files(carousel_files: CarouselFiles):
    if not (1 <= len(carousel_files.files) <= 3):
        return JSONResponse(content={"message": "Debes seleccionar entre 1 y 3 archivos."}, status_code=400)
    
    # Convertir HttpUrl a cadena
    urls = {file: str(url) for file, url in carousel_files.urls.items()}
    
    data = {
        "files": carousel_files.files,
        "urls": urls
    }
    with open(CAROUSEL_FILE, "w") as f:
        json.dump(data, f, indent=4)  # Añadir indentación para facilitar la lectura
    return JSONResponse(content={"message": "Selección de archivos guardada con éxito."})

@app.get("/carousel_files/")
async def get_carousel_files():
    """Devuelve la lista de archivos seleccionados para el carrusel."""
    if os.path.exists(CAROUSEL_FILE):
        with open(CAROUSEL_FILE, "r") as f:
            data = json.load(f)
        return JSONResponse(content=data)
    return JSONResponse(content={"files": [], "urls": {}})

@app.get("/file/{filename}")
async def get_file(filename: str, request: Request):
    """Devuelve un archivo específico con soporte para Range Requests."""
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(file_path):
        return JSONResponse(content={"error": "Archivo no encontrado"}, status_code=404)

    if filename.endswith(".mp4"):
        file_size = os.path.getsize(file_path)
        range_header = request.headers.get("range")

        if range_header:
            try:
                start, end = range_header.replace("bytes=", "").split("-")
                start = int(start)
                end = int(end) if end else file_size - 1
            except ValueError:
                return JSONResponse(content={"error": "Invalid range request"}, status_code=416)

            if start >= file_size or start > end:
                return JSONResponse(content={"error": "Requested range not satisfiable"}, status_code=416)

            end = min(end, file_size - 1)
            chunk_size = end - start + 1

            with open(file_path, "rb") as f:
                f.seek(start)
                data = f.read(chunk_size)

            headers = {
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(chunk_size),
                "Content-Type": "video/mp4",
            }
            return Response(data, status_code=206, headers=headers)

        return Response(open(file_path, "rb").read(), media_type="video/mp4")

    return FileResponse(file_path)

@app.post("/grant_access/")
async def grant_access():
    """Otorga acceso al usuario y lo redirige a la red"""
    # Aquí deberías ejecutar el comando o lógica que habilita el acceso.
    # Por ejemplo, modificar reglas de firewall, insertar en base de datos, etc.
    
    return JSONResponse(content={"message": "Acceso concedido. Puede navegar ahora."})