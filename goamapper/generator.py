from dataclasses import dataclass
from pathlib import Path
import logging as log
import subprocess
import drawsvg as dw
from goamapper.drawer import drawAreas, drawPaths, drawWays, drawCircut
from goamapper.models import Poster
from goamapper.fetcher import Fetcher

RENDERS_DIR = Path("renders")


class Generator():
    def __init__(self, poster: Poster) -> None:
        self.poster = poster

    # calculates and sets dimentions that map takes on the poster
    def _set_map_dimentions(self):

        t = self.poster.template

        # whole page dimentions
        self.canvas_dims = [0, 0, t.width, t.height]

        # dimentions of map space
        map_space_offset = t.map_offset
        self.map_space_dims = [map_space_offset, map_space_offset,
                               t.width-(2*map_space_offset),
                               t.height-(2*map_space_offset)-t.bottom_area_height]

    def _get_text_area(self) -> dw.Group:
        # TEXTS
        text_area = dw.Group(id='text_area')

        for tb_params in self.poster.template.text_boxes:

            text_area.append(dw.Text(
                # passes all parameters of a text box: position text fill and font
                **dict(tb_params),
                # helps easier positioning
                dominant_baseline='hanging',
                text_anchor='middle'
            ))

        return text_area

    def _get_template(self) -> dw.Group:

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

        return template

    def _get_map_content(self):

        log.info("Creating map content")
        map_content = dw.Group(id='map')
        fetcher = Fetcher(self.poster.area, self.canvas_dims)

        # TODO: make it asyncronous
        for layer_name, layer_info in self.poster.map_layers.items():
            log.info(f"Creating layer: {layer_name}")

            match layer_name:
                case "land":  # land is a background
                    map_content.append(dw.Rectangle(id='land',
                                                    *self.canvas_dims,  fill=layer_info['fill']))

                case "water":  # water must be specially treated
                    map_content.append(
                        drawAreas(fetcher.get_waterGDF(),
                                  id='water', fill=layer_info['fill']))

                case "streets":  # streets and other ways
                    street_types = list(layer_info['types'].keys())
                    gdf = fetcher.get_streetsGDF(street_types)
                    map_content.append(
                        drawWays(gdf, layer_info, id=layer_name))

                case "circut":
                    gdf = fetcher.get_f1GDF(layer_info['selector'])
                    map_content.append(
                        drawCircut(gdf, layer_info['style']))

                case _:
                    log.debug(f"Default case hit with {layer_name}")
                    gdf = fetcher.get_osmGDF(tags=layer_info['tags'],)

                    map_content.append(
                        drawAreas(gdf, id=layer_name, fill=layer_info['fill']))

        log.info("Map content genarated")
        return map_content

    def create_map(self) -> dw.Drawing:
        log.info("Starting creating map")

        self._set_map_dimentions()
        d = dw.Drawing(*self.canvas_dims[2:], id_prefix='poster')

        groups = [self._get_map_content(),
                  self._get_template(),
                  self._get_text_area()]

        d.extend(groups)
        log.info("Map created!")
        return d

    def generate_greenery_paths(area, canvas_dims) -> str:

        log.info("Generating greenery paths")
        fetcher = Fetcher(area, canvas_dims)
        GREENERY_TAGS = {
            "leisure": "park",
            "landuse": [
                "forest",
                "village_green"
            ],
            "natural": "wood"
        }

        log.info("Fetching greenery paths")
        gdf = fetcher.get_osmGDF(tags=GREENERY_TAGS)

        log.info("Drawing greenery paths")
        return drawPaths(gdf)

    def generate_water_paths(area, canvas_dims) -> str:

        log.info("Generating water paths")
        fetcher = Fetcher(area, canvas_dims)

        log.info("Fetching water paths")
        gdf = fetcher.get_waterGDF()
        log.info("Drawing water paths")
        return drawPaths(gdf)
