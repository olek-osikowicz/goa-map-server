from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse, HTMLResponse
import base64
import asyncio
from goamapper.generator import Generator
from goamapper.models import Poster
import logging as log
import json
from pydantic import BaseModel

log.basicConfig(format='%(levelname)s:%(asctime)s: %(message)s',level=log.DEBUG)

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def png2base64(path):
    with open(path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())

    return encoded_string


@app.get("/")
def root():
    return {'data': "Hello World"}


@app.post("/png")
async def file(p: Poster):

    # return {"msg": f"{p}"}
    g = Generator(p, overwrite=True)
    g.generate_svg()
    IMAGE_MAX_SIZE = 1000 #px
    g.save_png(max_size=IMAGE_MAX_SIZE)
    data = png2base64(g.png_file_path)
    return {"data": data}
    # return FileResponse(path=g.png_file_path)