import re
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse, HTMLResponse
from goamapper.generator import Generator
from goamapper.models import Poster
import logging as log
import json
import drawsvg as dw
from pydantic import BaseModel

log.basicConfig(
    format='%(levelname)s:%(asctime)s: %(message)s', level=log.DEBUG)

app = FastAPI()


def delete_width_and_height(text):
    pattern = r'width="\d+" height="\d+"'
    result = re.sub(pattern, '', text, count=1)
    return result


@app.get("/")
def read_root():
    return {"Hello": "World"}


# async def file(p: Poster):
@app.get("/v1/map")
async def file():

    with open("example_config.json", encoding="utf8") as file:
        data = json.load(file)
    p = Poster(**data)
    g = Generator(p, overwrite=False)
    g._calculate_dimentions()
    d = dw.Drawing(*g.canvas_dims[2:], id_prefix='poster')

    g.create_map_content()
    d.append(g.map_content)

    g.create_template()
    d.append(g.template)

    g.create_text_area()
    d.append(g.text_area)
    svg_str = d.as_svg()
    svg_str = delete_width_and_height(svg_str)
    return {"svg_string": svg_str}
