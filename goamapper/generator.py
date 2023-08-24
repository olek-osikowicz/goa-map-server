from dataclasses import dataclass
from pathlib import Path
import logging as log
import subprocess
import drawsvg as dw
from goamapper.drawer import drawAreas, drawWays, drawCircut
from goamapper.models import Poster
from goamapper.fetcher import Fetcher
from goamapper.recolorer import recolour

RENDERS_DIR = Path("renders")


class Generator():
    def __init__(self, poster: Poster, overwrite: bool = False) -> None:
        self.poster = poster
        self.overwrite = overwrite

        # self.map_layers_params = config['map_layers']

        self.prepare_folders()

        # only used if generating from scratch
        self.fetcher = None
        self.map_content = None
        self.template = None

    def prepare_folders(self):
        dir_path = RENDERS_DIR / self.poster.dir_name
        dir_path.mkdir(exist_ok=True)  # ensure directory exists

        svg_dir_path = dir_path / 'svg'
        svg_dir_path.mkdir(exist_ok=True)
        self.svg_file_path = svg_dir_path / f"{self.poster.poster_name}.svg"

        png_dir_path = dir_path / 'png'
        png_dir_path.mkdir(exist_ok=True)
        self.png_file_path = png_dir_path / f"{self.poster.poster_name}.png"

    def generate_svg(self):

        log.debug(
            f"Generating {self.poster.dir_name} in {self.poster.poster_name}")

        if self.svg_file_path.exists() and not self.overwrite:
            log.info(
                f"{self.poster.dir_name} in {self.poster.poster_name} already exists")

        else: #generate from scratch
            log.info(
                f"{self.poster.dir_name} in {self.poster.poster_name} doenst exist yet")
            self.generate_from_scratch()

    def save_png(self, max_size: int | None = None):

        if self.png_file_path.exists() and not self.overwrite:
            log.debug("PNG file already exists")
            return
        log.info(f"Saving png to {self.png_file_path}")
        w = self.poster.template.width
        h = self.poster.template.height

        if max_size:
            scale = max(w, h)/max_size
            w /= scale
            h /= scale

        subprocess.run(args=["inkscape",
                             "-w", str(int(w)),
                             "-h", str(int(h)),
                             "-o",
                             str(self.png_file_path),
                             str(self.svg_file_path)
                             ], capture_output=True)

    def _calculate_dimentions(self):

        t = self.poster.template
        t.map_frame.width

        # whole page dimentions
        self.canvas_dims = [0, 0, t.width, t.height,]

        # dimentions of frame around map space
        frame_offset = t.map_frame.offset
        self.frame_dims = [frame_offset, frame_offset,  # x, y
                           t.width-2*frame_offset,  # w
                           t.height-(2*frame_offset)-t.bottom_area_height]  # h

        # dimentions of map space
        map_space_offset = frame_offset + t.map_frame.width
        self.map_space_dims = [map_space_offset, map_space_offset,
                               t.width-(2*map_space_offset),
                               t.height-(2*map_space_offset)-t.bottom_area_height]

    def create_text_area(self):
        # TEXTS
        self.text_area = dw.Group(id='text_area')

        for tb in self.poster.template.text_boxes:

            self.text_area.append(dw.Text(
                text=tb.text,
                x=tb.x,
                y=tb.y,
                fill=tb.fill,
                font_size=tb.font_size,
                font_family=tb.font_family,
                dominant_baseline='hanging',
                text_anchor='middle'
            ))

    def create_template(self):

        # CREATE MAP MASK

        map_space_mask = dw.Mask()
        map_space_mask.append(  # visible part
            dw.Rectangle(*self.canvas_dims, fill='white'))

        map_space_mask.append(  # hidden part, to see map from below
            dw.Rectangle(*self.map_space_dims, fill='black'))

        # CREATE BACKGROUND AND FRAME

        t = self.poster.template
        # background rectangle filling whole page
        bg = dw.Rectangle(*self.canvas_dims, id='bg',
                          fill=t.background_fill)

        # create frame
        tf = dw.Rectangle(*self.frame_dims, id='frame',
                          fill=t.map_frame.fill)

        # CREATE TEMPLATE AND APPEND
        template = dw.Group(id='template', mask=map_space_mask)
        template.append(bg)
        template.append(tf)

        self.template = template

    def _init_map_content(self):

        # clip mam content
        clip = dw.ClipPath()
        clip.append(dw.Rectangle(*self.map_space_dims))
        self.map_content = dw.Group(id='map', stroke='none', clip_path=clip)

    def create_map_content(self):
        log.info("Creating map content")
        self._init_map_content()
        self.fetcher = Fetcher(self.poster.bbox, self.map_space_dims)

        for layer_name, layer_info in self.poster.map_layers.items():
            log.info(f"Creating layer: {layer_name}")

            match layer_name:
                case "land":  # land is a background
                    self.map_content.append(dw.Rectangle(id='land',
                                                         *self.canvas_dims,  fill=layer_info['fill']))
                case "water":  # water must be specially treated
                    self.map_content.append(
                        drawAreas(self.fetcher.get_waterGDF(),
                                  id='water', fill=layer_info['fill'])
                    )
                case "streets":  # streets and other ways
                    street_types = list(layer_info['types'].keys())
                    gdf = self.fetcher.get_streetsGDF(street_types)
                    self.map_content.append(
                        drawWays(gdf, layer_info, id=layer_name))
                    
                case "circut":
                    gdf = self.fetcher.get_f1GDF(layer_info['name'])
                    self.map_content.append(
                        drawCircut(gdf, layer_info)
                    )

                case _:
                    gdf = self.fetcher.get_osmGDF(tags=layer_info['tags'],)
                    # if gdf.
                    
                    self.map_content.append(
                        drawAreas(gdf, id=layer_name, fill=layer_info['fill']))

        log.info("Map content genarated")

    def generate_from_scratch(self):
        log.info("Generating from scratch")

        self._calculate_dimentions()
        d = dw.Drawing(*self.canvas_dims[2:], id_prefix='poster')

        self.create_map_content()
        d.append(self.map_content)

        self.create_template()
        d.append(self.template)

        self.create_text_area()
        d.append(self.text_area)

        d.save_svg(self.svg_file_path)
        log.debug("SVG saved")
        # d.save_png(self.png_file_path.__str__())
        # log.debug("PNG saved")

        log.info("Map saved")
