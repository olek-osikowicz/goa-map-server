from dataclasses import dataclass
import os
import json
from pathlib import Path
import logging as log
import drawsvg as dw
from drawer import drawAreas, drawWays

from fetcher import Fetcher
from recolorer import recolour

CONFIG_DIR = Path("config")
RENDERS_DIR = Path("renders")

class Generator():
    def __init__(self, config: dict) -> None:
        self.bbox = config['place_bbox']
        self.place_name = config['place_name']
        self.theme_name = config['theme_name']
        self.teplate_params = config['template']
        self.map_layers_params = config['map_layers']

        self.dir_path = RENDERS_DIR / self.place_name
        self.dir_path.mkdir(exist_ok=True) #ensure directory exists

        self.file_path = self.dir_path / f"{self.theme_name}.svg"

        #only used if generating from scratch
        self.fetcher = None
        self.map_content = None
        self.template = None

    def generate(self):

        if self.file_path.exists():
            log.debug(f"{self.place_name} in {self.theme_name} already exists")
        elif any(self.dir_path.iterdir()):
            log.info(f"{self.place_name} but in diffrent theme")
            recolour(self.dir_path, self.theme_name, self.map_layers_params, self.teplate_params)
        else:
            log.info(f"{self.place_name} in {self.theme_name} doenst exist yet")
            self.generate_from_scratch()


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

        text_x = self.frame_dims[0]
        #height of frame
        text_y = 2*self.frame_dims[1] + self.frame_dims[3] + p['main_text']['y_offset']

        text_area.append(dw.Text(p['main_text']['text'], font_size=p['main_text']['font_size'], x=text_x, y=text_y, id='main_text', fill=p['main_text']['fill']))

        text_y += p['sub_text']['y_offset']
        text_area.append(dw.Text(p['sub_text']['text'], font_size=p['sub_text']['font_size'], x=text_x, y=text_y, id='sub_text', fill=p['sub_text']['fill']))

        
        # CREATE TEMPLATE AND APPEND
        template = dw.Group(id='template', mask=map_space_mask)
        template.append(bg)
        template.append(tf)
        template.append(text_area)

        self.template = template

    def _init_map_content(self):

        #clip mam content
        clip = dw.ClipPath()
        clip.append(dw.Rectangle(*self.map_space_dims))
        self.map_content = dw.Group(id='map', stroke='none', clip_path = clip)

    def create_map_content(self):
        log.info("Creating map content")
        self._init_map_content()
        self.fetcher = Fetcher(self.bbox, self.map_space_dims)

        for layer_name, layer_info in self.map_layers_params.items():
            log.info(f"Creating layer: {layer_name}")

            match layer_name:
                case "land": #land is a background
                    self.map_content.append(dw.Rectangle(id='land',
                        *self.canvas_dims,  fill=layer_info['fill']))
                case "water": #water must be specially treated
                    self.map_content.append( 
                        drawAreas(self.fetcher.get_waterGDF(),id='water', fill=layer_info['fill'])
                    )
                case "streets": #streets and other ways
                    gdf = self.fetcher.get_streetsGDF()
                    self.map_content.append(drawWays(gdf, layer_info, id=layer_name))

                case _:
                    gdf = self.fetcher.get_osmGDF(tags=layer_info['tags'],)
                    self.map_content.append( 
                        drawAreas(gdf ,id=layer_name, fill=layer_info['fill']))
                    

        log.info("Map content genarated")

    def generate_from_scratch(self):
        log.info("Generating from scratch")

        self._calculate_dimentions()
        self.create_template()
        self.create_map_content()
        
        d = dw.Drawing(*self.canvas_dims[2:], id_prefix='poster')
        d.append(self.map_content)
        d.append(self.template)

        d.save_svg(self.file_path)

        log.info("Map saved")

def main():
    for config_file in os.listdir(CONFIG_DIR):

        with open(CONFIG_DIR / config_file) as file:
            data = json.load(file)
        Generator(data).generate()


if __name__ == "__main__":
    log.basicConfig(format='%(levelname)s:%(asctime)s: %(message)s',level=log.INFO)
    main()
