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


###### ----------Route for updating user role ----------######
###### ----------myaccount --> update user role ----------######

@user.post("/updaterole", response_class=HTMLResponse)
async def updaterole(request: Request, email: str = Form(...), newrole: str = Form(...),
                        current_user: dict = Depends(get_current_user_from_cookie)):
    try:
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

        user = users_collection.find_one({"email": email})

        if user is None:
            return templates.TemplateResponse("updaterole.html", {"request": request, "error_message": "User not found!"})

        # Get the role of the current user
        role = current_user.get('role')

        # Check if the user has the 'admin' role, if not, return an error message
        if role != "admin":
            error_message = f"Sorry {current_user.get('username')}, you are not allowed to update user roles."
            return templates.TemplateResponse("myaccount.html", {"request": request, "error_message": error_message})

        # Update the user's role in the database
        users_collection.update_one(
            {"email": email}, {"$set": {"role": newrole}})

        return templates.TemplateResponse("updaterole.html", {"request": request, "message": "User Role Updated Successfully"})

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {str(e)}")

###### ----------route to get dashboard page----------######


@user.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: dict = Depends(get_current_user_from_cookie)):
    try:
        if current_user is None:
            # Handle unauthenticated user, redirect or raise an exception
            return templates.TemplateResponse("login.html", {"request": request})

        return templates.TemplateResponse("dashboard.html", {"request": request, "username": current_user["username"]})
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {str(e)}")


###### ----------route to get myaccount page in the dashboard----------######

@user.get("/myaccount", response_class=HTMLResponse)
async def myaccount(request: Request, current_user: dict = Depends(get_current_user_from_cookie)):

    try:
        if current_user is None:
            # Handle unauthenticated user, redirect or raise an exception
            return templates.TemplateResponse("login.html", {"request": request})

        # Fetch user account data from the database
        user_data = users_collection.find_one({"email": current_user["email"]})

        # Extract username, email and role from the user data
        username = user_data["username"]
        email = user_data["email"]
        role = user_data["role"]
        creation_date = user_data["creation_date"]
        creation_time = user_data["creation_time"]

        if role != "admin":  # Check the role here
            return templates.TemplateResponse("myaccount.html", {"request": request, "username": username, "email": email, "role": role, "creation_date": creation_date, "creation_time": creation_time})

        return templates.TemplateResponse("adminacc.html", {"request": request, "username": username, "email": email, "role": role, "creation_date": creation_date, "creation_time": creation_time})

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {str(e)}")


###### ----------route to change the role after login(Only by admin)---------######

@user.get("/updaterole", response_class=HTMLResponse)
async def updaterolerole(request: Request, current_user: dict = Depends(get_current_user_from_cookie)):

    try:

        if current_user is None:
            return templates.TemplateResponse("login.html", {"request": request})

        # Fetch user account data from the database
        user_data = users_collection.find_one({"email": current_user["email"]})

        # Extract username, email and role from the user data
        username = user_data["username"]
        email = user_data["email"]
        role = user_data["role"]

        role = current_user.get('role')
        if role != "admin":  # Check the role here
            return templates.TemplateResponse("myaccount.html", {"request": request, "username": username, "email": email, "role": role})

        else:
            return templates.TemplateResponse("updaterole.html", {"request": request})

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {str(e)}")
