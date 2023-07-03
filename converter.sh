# Specify the directory containing the SVG files
DIRECTORY="renders/nyc"
cd "$DIRECTORY"


inkscape --export-type=png svg/*.svg
mkdir -p png
mv svg/*.png png/
