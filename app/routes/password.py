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


# To create an instance of APIRouter for user-related routes
user = APIRouter()

# Initialize Jinja2Templates to handle HTML templates in the "templates" directory
templates = Jinja2Templates(directory="templates")


###### ----------Route for forgot password page----------######
###### ----------forgotpass->pass reset link to registered email id(resetpass page->resetlink page(redirect to login page))----------######

@user.post("/forgotpassword", response_class=HTMLResponse)
async def forgot_password(request: Request, email: str = Form(...)):
    try:
        user = users_collection.find_one({'email': email})

        if user:
            # Generate a reset password token
            reset_password_token = secrets.token_urlsafe(16)

            # Store the reset password token and user's email in the database
            reset_password_data = {
                "email": email,
                "reset_password_token": reset_password_token,
            }
            # Insert into verification_collection
            verification_collection.insert_one(reset_password_data)

            # Send the reset password email with the token
            # Function to send the email
            send_passreset_email(email, reset_password_token)

            # Redirect to forgotpasslink.html
            return templates.TemplateResponse("forgotpasslink.html", {"request": request})

        else:
            return templates.TemplateResponse("forgotpassword.html", {"request": request, "error_message": "Email id not registered"})

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {str(e)}")


###### ----------Route for reset password----------######
###### ----------resetpass page->resetlink page(redirect to login page)----------######

@user.post("/resetpassword", response_class=HTMLResponse)
async def resetpassword(request: Request, token: str = Form(...), password: str = Form(...),
                        confirm_password: str = Form(...)):
    try:
        # Check if the reset password token exists in the database
        reset_password_data = verification_collection.find_one(
            {"reset_password_token": token})

        if not reset_password_data:
            return templates.TemplateResponse("resetpass.html", {"request": request, "error_message": "Invalid reset password token"})

        email = reset_password_data["email"]

        # Validate password requirements
        if not re.search(r"[A-Z]", password):
            return templates.TemplateResponse("resetpass.html", {"request": request, "error_message": "Password must contain at least at least 8 characters long, one uppercase letter, one digit, one special character "})
        # \d Matches any digit character. Equivalent to [0-9].
        if not re.search(r"\d", password):
            return templates.TemplateResponse("resetpass.html", {"request": request, "error_message": "Password must contain at least one digit"})
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>-_+=]", password):
            return templates.TemplateResponse("resetpass.html", {"request": request, "error_message": "Password must contain at least one special character"})
        if len(password) < 8:
            return templates.TemplateResponse("resetpass.html", {"request": request, "error_message": "Password must be at least 8 characters long"})

        # Check if new passwords match
        if password != confirm_password:
            return templates.TemplateResponse("resetpass.html", {"request": request, "error_message": "Passwords do not match"})

        # Hash the new password
        hashed_password = Hash.hash_password(password)

        # Update the user's password
        users_collection.update_one(
            {"email": email}, {"$set": {"password": hashed_password}})

        # Delete the reset password data from the database
        verification_collection.delete_one({"reset_password_token": token})

        return templates.TemplateResponse("resetlink.html", {"request": request})
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {str(e)}")


###### ----------Route for updatepassword----------######
###### ----------myaccount-->update password----------######

@user.post("/updatepassword", response_class=HTMLResponse)
async def updatepassword(request: Request, oldpassword: str = Form(...), password: str = Form(...),
                            confirm_password: str = Form(...),
                            current_user: dict = Depends(get_current_user_from_cookie)):
    try:
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

        # Retrieve the user's email from the current user data
        email = current_user.get("email")

        # Check if the old password matches the user's current password
        user = users_collection.find_one({"email": email})
        if not Hash.verify_password(oldpassword, user["password"]):
            return templates.TemplateResponse("updatepassword.html", {"request": request, "error_message": "Incorrect old password"})

        # Validate password requirements (same as before)
        if not re.search(r"[A-Z]", password):
            return templates.TemplateResponse("updatepassword.html", {"request": request, "error_message": "Password must contain at least at least 8 characters long, one uppercase letter, one digit, one special character "})
        # \d Matches any digit character. Equivalent to [0-9].
        if not re.search(r"\d", password):
            return templates.TemplateResponse("updatepassword.html", {"request": request, "error_message": "Password must contain at least one digit"})
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>-_+=]", password):
            return templates.TemplateResponse("updatepassword.html", {"request": request, "error_message": "Password must contain at least one special character"})
        if len(password) < 8:
            return templates.TemplateResponse("updatepassword.html", {"request": request, "error_message": "Password must be at least 8 characters long"})

        # Validate the new password and confirm_password
        if password != confirm_password:
            return templates.TemplateResponse("updatepassword.html", {"request": request, "error_message": "Passwords do not match"})

        # Hash the new password
        hashed_password = Hash.hash_password(password)

        # Update the user's password in the database
        users_collection.update_one(
            {"email": email}, {"$set": {"password": hashed_password}})

        # Redirect the user to a password updated page or dashboard
        return templates.TemplateResponse("successpass.html", {"request": request})

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {str(e)}")


###### ----------route to display the password reset was successful----------######

@user.get("/resetlink")
async def resetlink(request: Request):
    return templates.TemplateResponse("resetlink.html", {"request": request})


###### ----------route to get forgotre page----------######
###### ----------when the user enters an email in the forgot password page, it will redirect to this page----------######

@user.get("/forgotpasslink")
async def forgotre(request: Request):
    return templates.TemplateResponse("forgotpasslink.html", {"request": request})


###### ----------route to get forgotpassword page----------######

@user.get("/forgotpassword")
async def forgotpassword(request: Request):
    return templates.TemplateResponse("forgotpassword.html", {"request": request})


###### ----------route to get reset password page----------######

@user.get("/resetpassword", response_class=HTMLResponse)
async def resetpassword(request: Request, token: str):
    try:
        # Check if the reset password token exists in the database
        reset_password_data = verification_collection.find_one(
            {"reset_password_token": token})
        if not reset_password_data:
            return templates.TemplateResponse("resetpass.html", {"request": request})

        # Render the resetpassword page with the token as a hidden input field
        return templates.TemplateResponse("resetpass.html", {"request": request, "token": token})

    except Exception as e:
        return templates.TemplateResponse("resetpass.html", {"request": request, "error_message": f"Internal Server Error: {str(e)}"})


###### ----------route to get sucesspass page----------######

@user.get("/successpass")
async def successpass(request: Request):
    return templates.TemplateResponse("successpass.html", {"request": request})


###### ----------route to update password after user login in my account----------######

@user.get("/updatepassword", response_class=HTMLResponse)
async def updatepassword(request: Request, current_user: dict = Depends(get_current_user_from_cookie)):
    try:
        if current_user is None:
            return templates.TemplateResponse("login.html", {"request": request})

        return templates.TemplateResponse("updatepassword.html", {"request": request})

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {str(e)}")
