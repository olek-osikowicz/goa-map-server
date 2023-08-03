from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from dotenv import load_dotenv
import os
load_dotenv()

app = FastAPI()
app.mount("/", StaticFiles(directory=os.environ.get('RENDERS_PATH')), name="static")