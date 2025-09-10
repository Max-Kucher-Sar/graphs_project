from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from src.models.User import users_router
from src.models.Well import wells_router
from src.models.Data_processing import data_router

app = FastAPI(timeout=60*20)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Для разработки
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router, prefix="/api")
app.include_router(wells_router, prefix="/api")
app.include_router(data_router, prefix="/api")


@app.get("/")
def main_page():
    return {"msg": "запустилось"}