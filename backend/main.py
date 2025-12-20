from fastapi import FastAPI, Depends
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from . import models, database
import os

load_dotenv()

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Performance Optimizer Backend is running!"}
