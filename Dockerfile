FROM python:3.11

# download water polygons and put it in assets directory
RUN mkdir /assets
RUN wget -P ./assets https://osmdata.openstreetmap.de/download/water-polygons-split-4326.zip 
RUN unzip ./assets/water-polygons-split-4326.zip -d ./assets

RUN pip install --no-cache-dir --upgrade -r "requirements.txt"

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
