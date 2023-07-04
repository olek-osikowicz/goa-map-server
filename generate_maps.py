import os
import json
from goamapper.generator import Generator
import logging as log
from pathlib import Path

CONFIG_DIR = Path("config")

def main():

    for file in CONFIG_DIR.glob('**/*'):
        if file.is_file():
            with open(file) as file:
                data = json.load(file)

            g = Generator(data)
            g.generate_svg()
            g.save_png()


if __name__ == "__main__":
    log.basicConfig(format='%(levelname)s:%(asctime)s: %(message)s',level=log.DEBUG)
    main()