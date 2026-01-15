# Download water polygon data

echo "Downloading water polygon data..."
mkdir -p ./assets
wget -P ./assets https://osmdata.openstreetmap.de/download/water-polygons-split-4326.zip
unzip ./assets/water-polygons-split-4326.zip -d ./assets
rm ./assets/water-polygons-split-4326.zip
