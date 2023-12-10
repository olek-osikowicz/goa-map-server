from pydantic import BaseModel


class TextBox(BaseModel):
    x: int
    y: int
    text: str
    font_size: int
    font_family: str
    fill: str


class Template(BaseModel):
    width: int
    height: int
    background_fill: str
    map_offset: int
    bottom_area_height: int
    text_boxes: list[TextBox] = None


class Area(BaseModel):
    bbox: list[float] = None
    latlon: tuple[float, float] = None
    name: str = None
    radius: int = None


class Poster(BaseModel):
    # bbox: list[float] = None
    dir_name: str
    area: Area
    poster_name: str
    template: Template
    map_layers: dict
