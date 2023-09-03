import os
import json
from goamapper.generator import Generator
from goamapper.models import Poster
import logging as log
from pathlib import Path
from multiprocessing import Pool

CONFIG_DIR = Path("config")

def generate_from_file(path: Path):
    log.debug(f"Opening file {path}")
    with open(path, encoding="utf8") as file:
        data = json.load(file)

    p = Poster(**data)
    g = Generator(p, overwrite=False)
    g.generate_svg()
    g.save_png()


def main():

    #get json files
    paths = [p for p in CONFIG_DIR.glob('**/*') if p.suffix == '.json']
    with Pool(processes=16) as pool:
        pool.map(generate_from_file, paths)


if __name__ == "__main__":

    log.basicConfig(format='%(levelname)s:%(asctime)s: %(message)s',level=log.INFO)
    main() 
