
# Specify the directory containing the SVG files
DIRECTORY="renders/barcelona"
cd "$DIRECTORY"


inkscape --export-type=pdf *.svg
mkdir -p pdf
mv *.pdf pdf/
