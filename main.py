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


# Krakow
DEFAULT_AREA = Area(bbox=[
    19.864953,
    50.003372,
    20.009857,
    50.116317
])

DEFAULT_CANVAS_DIMS = [0, 0, 4960, 7016]


class Paths(BaseModel):
    layer_name: str
    area: Area | None = None


@app.post("/v3/paths")
async def paths(p: Paths):
    start_time = time.perf_counter()

    if not p.area:
        p.area = DEFAULT_AREA

    ret = Generator.generate_paths(p.layer_name, p.area, DEFAULT_CANVAS_DIMS)
    elapsed_time = time.perf_counter() - start_time

    log.info(
        f"Generating paths for {p.layer_name} took {elapsed_time:.4f} seconds")

    with open(f"renders/{p.layer_name}.txt", "w") as f:
        f.write(ret)

    return ret
