from dataclasses import dataclass
from pathlib import Path
import logging as log
import subprocess
import drawsvg as dw
from goamapper.drawer import drawAreas, drawWays, drawCircut
from goamapper.models import Poster
from goamapper.fetcher import Fetcher

RENDERS_DIR = Path("renders")


class Generator():
    def __init__(self, poster: Poster) -> None:
        self.poster = poster

        # only used if generating from scratch
        self.fetcher = None
        self.map_content = None
        self.template = None

    def _calculate_map_dimentions(self):

        t = self.poster.template

        # whole page dimentions
        self.canvas_dims = [0, 0, t.width, t.height]

        # dimentions of map space
        map_space_offset = t.map_offset
        self.map_space_dims = [map_space_offset, map_space_offset,
                               t.width-(2*map_space_offset),
                               t.height-(2*map_space_offset)-t.bottom_area_height]

    def create_text_area(self):
        # TEXTS
        self.text_area = dw.Group(id='text_area')

        for tb_params in self.poster.template.text_boxes:

            self.text_area.append(dw.Text(
                # passes all parameters of a text box: position text fill and font
                **dict(tb_params),
                # helps easier positioning
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

        # CREATE TEMPLATE AND APPEND
        template = dw.Group(id='template', mask=map_space_mask)
        template.append(bg)

        self.template = template

    def create_map_content(self):

        log.info("Creating map content")
        self.map_content = dw.Group(id='map')
        self.fetcher = Fetcher(self.poster.area, self.map_space_dims)

        # TODO: make it asyncronous
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
                    gdf = self.fetcher.get_f1GDF(layer_info['selector'])
                    self.map_content.append(
                        drawCircut(gdf, layer_info['style'])
                    )

                case _:

                    log.debug(f"Default case hit with {layer_name}")
                    gdf = self.fetcher.get_osmGDF(tags=layer_info['tags'],)

                    self.map_content.append(
                        drawAreas(gdf, id=layer_name, fill=layer_info['fill']))

        log.info("Map content genarated")

    def generate_from_scratch(self):
        log.info("Generating from scratch")

        self._calculate_map_dimentions()
        d = dw.Drawing(*self.canvas_dims[2:], id_prefix='poster')

        self.create_map_content()
        d.append(self.map_content)

        self.create_template()
        d.append(self.template)

        self.create_text_area()
        d.append(self.text_area)

        d.save_svg(self.svg_file_path)
        log.debug("SVG saved")

        log.info("Map saved")
