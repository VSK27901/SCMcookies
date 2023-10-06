from fastapi import APIRouter, HTTPException, Depends
from app.models.models import UserResetPass, UserForgotPassword, User, UserCreateShipment
from app.config.db import conn, users_collection
from app.utils import Hash, create_access_token, clear_access_token_cookie
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


# To create an instance of APIRouter for user-related routes
user = APIRouter()

# Initialize Jinja2Templates to handle HTML templates in the "templates" directory
templates = Jinja2Templates(directory="templates")


###### ----------Route to get home page----------######

@user.get("/")
async def home_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


###### ----------Route for login with auth----------######
###### ----------login->dashboard page, will store the cookie of the current user----------######

@user.post("/login", response_class=HTMLResponse)
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        user = users_collection.find_one({"email": form_data.username})

        if user is None:
            # Render the login page with an error message
            return templates.TemplateResponse("login.html", {"request": request, "error_message": "User not found!"})

        if not Hash.verify_password(form_data.password, user["password"]):
            # Render the login page with an error message
            return templates.TemplateResponse("login.html", {"request": request, "error_message": "Incorrect password"})

        current_user = {
            "username": user["username"],
            "email": user["email"]
        }
        access_token = create_access_token(
            data={"sub": user["username"], "email": user["email"]})

        response = RedirectResponse("/dashboard", status.HTTP_302_FOUND)
        response.set_cookie(key="access_token",
                            value=access_token, httponly=True)

        return response
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {str(e)}")


###### ----------Route to get login page----------######

@user.get("/login")
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


###### ----------Logout of the user from the dashboard by clearing the cookies(JWT tokens of the session) of the current user----------######

@user.get("/logout")
async def logout(request: Request, access_token: str = Cookie(None)):
    try:
        # Clear the access token cookie to log the user out
        response = RedirectResponse(url="/")
        # Call the function to clear the access token cookie
        clear_access_token_cookie(response)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {str(e)}")
