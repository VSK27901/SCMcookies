from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles 
from fastapi.templating import Jinja2Templates
from app.routes.dashboard import user as dashboard   # Import the user routers from app routes
from app.routes.devicedata import user as devicedata
from app.routes.login import user as login
from app.routes.password import user as password
from app.routes.shipment import user as shipment
from app.routes.signup import user as signup


# Create a FastAPI instance
app = FastAPI()

app.include_router(dashboard)   # User dashboard routes
app.include_router(devicedata)  # Device data routes
app.include_router(login)       # Login Route
app.include_router(password)    # Password-related routes
app.include_router(shipment)    # Shipment-related routes
app.include_router(signup)      # Signup and verification routes

# Mount a directory for serving static files (CSS, JavaScript)
app.mount("/static", StaticFiles(directory="static"), name="static")


