from fastapi import APIRouter, HTTPException, Depends, Query
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
import secrets
from datetime import datetime, date


# To create an instance of APIRouter for user-related routes
user = APIRouter()

# Initialize Jinja2Templates to handle HTML templates in the "templates" directory
templates = Jinja2Templates(directory="templates")


###### ----------Route for signup page----------######
###### ----------signup->accverification page after successful registration----------######
###### ----------(verification link to registered email id(verificationpage->login page))----------######

@user.post("/signup", response_class=HTMLResponse)
async def signup(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...),
                    confirm_password: str = Form(...)):
    try:
        # Check if the email is already registered
        existing_user = users_collection.find_one({"email": email})  # db query
        if existing_user:
            return templates.TemplateResponse("signup.html", {"request": request, "error_message": "Email already registered!"})

        # Confirm pass
        if password != confirm_password:
            return templates.TemplateResponse("signup.html", {"request": request, "error_message": "Passwords do not match"})

        # Validate password requirements
        if not re.search(r"[A-Z]", password):
            return templates.TemplateResponse("signup.html", {"request": request, "error_message": "Password must contain at least at least 8 characters long, one uppercase letter, one digit, one special character "})
        # \d Matches any digit character. Equivalent to [0-9].
        if not re.search(r"\d", password):
            return templates.TemplateResponse("signup.html", {"request": request, "error_message": "Password must contain at least one digit"})
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>-_+=]", password):
            return templates.TemplateResponse("signup.html", {"request": request, "error_message": "Password must contain at least one special character"})
        if len(password) < 8:
            return templates.TemplateResponse("signup.html", {"request": request, "error_message": "Password must be at least 8 characters long"})

        # Hash the password
        hashed_password = Hash.hash_password(password)

        # Generate a verification token
        verification_token = secrets.token_urlsafe(16)

        # creation date/time
        creation_date = str(date.today())

        # Store the current time in HH:MM:SS format
        creation_time = datetime.now().time().strftime("%H:%M:%S")

        # Store the verification token and user's email in the database
        verification_data = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "verification_token": verification_token,
            "creation_date": creation_date,
            "creation_time": creation_time

        }

        # Insert into verification_collection
        verification_collection.insert_one(verification_data)

        # Send the verification email with the token
        # Function to send the email
        send_verification_email(username, email, verification_token)

        # Redirect the accverfication page
        return templates.TemplateResponse("accverification.html", {"request": request})
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {str(e)}")


###### ----------Route to get signup page----------######

@user.get("/signup")
async def signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


###### ----------Route to get accverification page----------######

@user.get("/accverification")
async def accverification(request: Request):
    return templates.TemplateResponse("accverification.html", {"request": request})


###### ----------Route to get verification page----------######
###### ----------for account verification and login redirection after verification by email----------######

@user.get("/verification")
async def verification(request: Request, token: str = Query(...)):
    try:
        # Check if the verification token exists in the database
        verification_data = verification_collection.find_one(
            {"verification_token": token})
        if not verification_data:
            return templates.TemplateResponse("dashboard.html", {"request": request, "error_message": "Invalid verification token"})

        # Mark the email as verified (you can update the user's status in the database)
        users_collection.update_one({"email": verification_data["email"]}, {
                                    "$set": {"verified": True}})

        # Delete the verification token from the database
        verification_collection.delete_one({"verification_token": token})

        # Now that the email is verified, insert the user's data into the database(after verfication)
        new_user = {
            "username": verification_data["username"],
            "email": verification_data["email"],
            "password": verification_data["password"],
            "role": "User",
            "verified": True,  # Set the verified status to True
            "creation_date": verification_data["creation_date"],
            "creation_time": verification_data["creation_time"]

        }

        users_collection.insert_one(new_user)

        # Redirect the user to a "Verification Successful" page
        return templates.TemplateResponse("verification.html", {"request": request})
    except Exception as e:
        return templates.TemplateResponse("verification.html", {"request": request, "error_message": f"Internal Server Error: {str(e)}"})
