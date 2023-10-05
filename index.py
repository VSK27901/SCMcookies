from fastapi import FastAPI
from app.routes.postroutes import user as postroutes
from app.routes.getroutes import user as getroutes
from fastapi.staticfiles import StaticFiles 
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.include_router(postroutes)
app.include_router(getroutes)

app.mount("/static", StaticFiles(directory="static"), name="static")


