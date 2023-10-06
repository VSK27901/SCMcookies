from fastapi import APIRouter, HTTPException, Depends
from app.models.models import UserResetPass, UserForgotPassword, User, UserCreateShipment
from app.config.db import conn, users_collection, shipments_collection, device_collection, verification_collection
from app.utils import Hash, create_access_token, get_current_user, decode_token, get_current_user_from_cookie, clear_access_token_cookie
from bson import ObjectId
from datetime import timedelta
from pydantic import EmailStr
from fastapi import Request, Depends, Form, HTTPException, status, Cookie, Response
from jose import jwt, JWTError
from fastapi.responses import HTMLResponse, RedirectResponse
import re
import requests
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.email.emailver import send_verification_email
from app.email.resetpass import send_passreset_email
import secrets
from datetime import datetime, date


user = APIRouter()

templates = Jinja2Templates(directory="templates")



###### ----------Route for devicedata post method----------######

@user.post("/devicedata", response_class=HTMLResponse)
async def devicedata(request: Request, current_user: dict = Depends(get_current_user_from_cookie),
                        deviceid: int = Form(...)):
    try:

        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

        # Get the role of the current user
        role = current_user.get('role')

        # Check if the user has the 'admin' role, if not, return an error message
        if role != "admin":
            # return templates.TemplateResponse("dashboard.html", {"request": request, "error_message": "Access denied. Only admins are allowed!"})
            error_message = f"Sorry {current_user.get('username')}, you are allowed to access this page"
            return templates.TemplateResponse("dashboard.html", {"request": request, "error_message": error_message})

        # Fetch device data from the MongoDB collection based on the selected device ID
        device_data = device_collection.find({"Device_Id": deviceid})

        # Return an HTML template response with the device dat
        return templates.TemplateResponse("devicedata.html", {"request": request, "device_data": device_data})
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {str(e)}")


###### ----------route to display devicedata (Only admins are allowed)----------######

@user.get("/devicedata", response_class=HTMLResponse)
async def devicedata(request: Request, current_user: dict = Depends(get_current_user_from_cookie)):
    try:
        if current_user is None:
            return templates.TemplateResponse("login.html", {"request": request})

        # # Fetch device data from the MongoDB collection
        # device_data = device_collection.find({})

        role = current_user.get('role')
        if role != "admin":  # Check the role here
            # raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. Only admins are allowed.")
            error_message = f"Sorry {current_user.get('username')}, you are allowed to access this page"
            return templates.TemplateResponse("dashboard.html", {"request": request, "error_message": error_message})

        else:
            return templates.TemplateResponse("devicedata.html", {"request": request})
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {str(e)}")
