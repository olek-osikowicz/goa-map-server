import re
import time
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse, HTMLResponse
from goamapper.generator import Generator
from goamapper.models import Area, Poster
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


async def get_map(p: Poster):

    start_time = time.perf_counter()

    g = Generator(p)
    d = g.create_map()
    svg_str = d.as_svg()
    svg_str = delete_width_and_height(svg_str)

    elapsed_time = time.perf_counter() - start_time
    log.info(f"Time spent generating the map: {elapsed_time:.4f} seconds")

    # TODO use ENV variable
    with open("renders/latest.svg", "w") as f:
        f.write(svg_str)

    return {"svg_string": svg_str}


# async def file(p: Poster):
@app.post("/v1/map")
async def map(area: Area | None = None):

    with open("example_config.json", encoding="utf8") as file:
        data = json.load(file)
    p = Poster(**data)

    log.info(f"Got new {area=}")
    if area:
        p.area = area

    return await get_map(p)
