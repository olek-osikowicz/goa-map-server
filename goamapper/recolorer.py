from pathlib import Path
import xml.etree.ElementTree as ET
import json

def get_fill_swaps(map_layers_config, template_config):
    return {
        #all non street layers
        k: v.get('fill') for k,v in map_layers_config.items()} | {

    #static template
    "bg": template_config['background_fill'],
    "frame": template_config['map_frame']['fill'],
    "main_text": template_config['main_text']['fill'],
    "sub_text": template_config['sub_text']['fill'],
    }

def get_stroke_swaps(map_layers_config):
    #all types of streets
    return {k: v['stroke'] for k,v 
           in map_layers_config['streets']['types'].items()}


def recolour_elements(attribute_name: str, swaps: dict, root):
    xpath = f".//*[@{attribute_name}]"
    
    for el in root.findall(xpath):
        id = el.get('id')
        new_val = swaps.get(id)
        if new_val:
            el.set(attribute_name, new_val)


def recolour(dir_path: Path, theme_name, map_layers_params, template_params):

    #parse existing
    first_file_path = dir_path.iterdir().__next__()
    tree = ET.parse(first_file_path)

    root = tree.getroot()

    recolour_elements('fill', get_fill_swaps(map_layers_params, template_params), root)
    recolour_elements('stroke', get_stroke_swaps(map_layers_params), root)
    output_path = dir_path / f"{theme_name}.svg"
    tree.write(output_path)


if __name__ == '__main__':
    with open("config/bar2.json") as file:
        config = json.load(file)

    DIR_PATH = Path("renders") / 'barcelona'
    recolour(DIR_PATH, config)
