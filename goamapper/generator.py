from dataclasses import dataclass
from pathlib import Path
import logging as log
import subprocess
import drawsvg as dw
from goamapper.drawer import drawAreas, drawWays
import cairosvg
from goamapper.fetcher import Fetcher
from goamapper.recolorer import recolour

RENDERS_DIR = Path("renders")


class Generator():
    def __init__(self, config: dict) -> None:
        self.bbox = config['place_bbox']
        self.place_name = config['place_name']
        self.theme_name = config['theme_name']
        self.teplate_params = config['template']
        self.map_layers_params = config['map_layers']

        self.prepare_folders()

        # only used if generating from scratch
        self.fetcher = None
        self.map_content = None
        self.template = None

    def prepare_folders(self):
        dir_path = RENDERS_DIR / self.place_name
        dir_path.mkdir(exist_ok=True)  # ensure directory exists

        svg_dir_path = dir_path / 'svg'
        svg_dir_path.mkdir(exist_ok=True)
        self.svg_file_path = svg_dir_path / f"{self.theme_name}.svg"

        png_dir_path = dir_path / 'png'
        png_dir_path.mkdir(exist_ok=True)
        self.png_file_path = png_dir_path / f"{self.theme_name}.png"

    def generate_svg(self):

        log.debug(f"Generating {self.place_name} in {self.theme_name}")
        if self.svg_file_path.exists():
            log.info(f"{self.place_name} in {self.theme_name} already exists")
        else:
            log.info(f"{self.place_name} in {self.theme_name} doenst exist yet")
            self.generate_from_scratch()

    def save_png(self, max_size: int | None = None):

        if self.png_file_path.exists():
            log.debug("PNG file already exists")
            return
        log.info(f"Saving png to {self.png_file_path}")
        w = self.teplate_params['width']
        h = self.teplate_params['height']

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

        p = self.teplate_params

        # whole page dimentions
        self.canvas_dims = [0, 0, p['width'], p['height'],]

        # dimentions of frame around map space
        frame_offset = p['map_frame']['offset']
        self.frame_dims = [frame_offset, frame_offset,  # x, y
                           p['width']-2*frame_offset,  # w
                           p['height']-(2*frame_offset)-p['bottom_area_height']]  # h

        # dimentions of map space
        map_space_offset = frame_offset + p['map_frame']['width']
        self.map_space_dims = [map_space_offset, map_space_offset,
                               p['width']-(2*map_space_offset),
                               p['height']-(2*map_space_offset)-p['bottom_area_height']]

    def create_template(self):

        # CREATE MAP MASK

        map_space_mask = dw.Mask()
        map_space_mask.append(  # visible part
            dw.Rectangle(*self.canvas_dims, fill='white'))

        map_space_mask.append(  # hidden part, to see map from below
            dw.Rectangle(*self.map_space_dims, fill='black'))

        # CREATE BACKGROUND AND FRAME

        p = self.teplate_params
        # background rectangle filling whole page
        bg = dw.Rectangle(*self.canvas_dims, id='bg',
                          fill=p['background_fill'])

        # create frame
        tf = dw.Rectangle(*self.frame_dims, id='frame',
                          fill=p['map_frame']['fill'])

        # TEXTS
        text_area = dw.Group(id='text_area')

        text_x = self.map_space_dims[0]
        # height of frame
        text_y = p['height'] - p['bottom_area_height'] + \
            p['main_text']['y_offset']
        log.debug(f"Main text: {text_x=}, {text_y=}")
        text_area.append(dw.Text(p['main_text']['text'], font_size=p['main_text']['font_size'], x=text_x, y=text_y,
                         id='main_text', fill=p['main_text']['fill'], font_family=p['main_text']['font_family'], dominant_baseline='hanging'))

        if 'sub_text' in p:
            text_y += p['sub_text']['y_offset']

            log.debug(f"Sub text: {text_x=}, {text_y=}")
            text_area.append(dw.Text(p['sub_text']['text'], font_size=p['sub_text']['font_size'], x=text_x, y=text_y,
                             id='sub_text', fill=p['sub_text']['fill'], font_family=p['sub_text']['font_family'], dominant_baseline='hanging'))

        # CREATE TEMPLATE AND APPEND
        template = dw.Group(id='template', mask=map_space_mask)
        template.append(bg)
        template.append(tf)
        template.append(text_area)

        self.template = template

    def _init_map_content(self):

        # clip mam content
        clip = dw.ClipPath()
        clip.append(dw.Rectangle(*self.map_space_dims))
        self.map_content = dw.Group(id='map', stroke='none', clip_path=clip)

    def create_map_content(self):
        log.info("Creating map content")
        self._init_map_content()
        self.fetcher = Fetcher(self.bbox, self.map_space_dims)

        for layer_name, layer_info in self.map_layers_params.items():
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

                case _:
                    gdf = self.fetcher.get_osmGDF(tags=layer_info['tags'],)
                    self.map_content.append(
                        drawAreas(gdf, id=layer_name, fill=layer_info['fill']))

        log.info("Map content genarated")

    def generate_from_scratch(self):
        log.info("Generating from scratch")

        self._calculate_dimentions()
        self.create_template()
        self.create_map_content()

        d = dw.Drawing(*self.canvas_dims[2:], id_prefix='poster')
        d.append(self.map_content)
        d.append(self.template)

        d.save_svg(self.svg_file_path)
        log.debug("SVG saved")
        # d.save_png(self.png_file_path.__str__())
        # log.debug("PNG saved")

        log.info("Map saved")
