from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
import base64
import asyncio
from goamapper.generator import Generator
import logging as log
import json

log.basicConfig(format='%(levelname)s:%(asctime)s: %(message)s',level=log.DEBUG)

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

origins = ["*"]

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
async def file(request: Request):
    # await asyncio.sleep(5)
    body = await request.json()
    if body is str:
        body = json.loads(body)
        
    assert isinstance(body, dict), "Body is not dict"
    log.debug(f"{body = }")

    g = Generator(body)
    g.generate_svg()
    IMAGE_MAX_SIZE = 1200 #px
    g.save_png(max_size=IMAGE_MAX_SIZE)
    data = png2base64(g.png_file_path)
    return {"data": data}
