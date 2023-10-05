from fastapi import APIRouter, HTTPException, Depends
from app.models.models import UserResetPass, UserForgotPassword, User, UserCreateShipment
from app.config.db import conn, users_collection, shipments_collection, device_collection, verification_collection
from app.utils import Hash, create_access_token, get_current_user, decode_token, clear_access_token_cookie, get_current_user_from_cookie
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


###### ----------Route for createshipment----------######
###### ----------createshipment->myshipment----------######

@user.post("/createshipment", response_class=HTMLResponse)
async def createshipment(
        request: Request,
        shipment_no: str = Form(...),
        route_details: str = Form(...),
        device: str = Form(...),
        po_no: str = Form(...),
        ndc_no: str = Form(...),
        serial_no: str = Form(...),
        container_no: str = Form(...),
        goods_type: str = Form(...),
        expected_delivery: str = Form(...),
        delivery_no: str = Form(...),
        batch_id: str = Form(...),
        shipment_des: str = Form(...),
        current_user: dict = Depends(get_current_user_from_cookie)):

    try:
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

        # Check if the shipment is already registered
        existing_shipment = shipments_collection.find_one(
            {"shipment_no": shipment_no})
        if existing_shipment:
            # raise HTTPException(status_code=400, detail="Shipment already exists")
            return templates.TemplateResponse("createshipment.html", {"request": request, "error_message": "Shipment already exists"})

        # Create a new shipment document
        new_shipment = {
            # Associate the shipment with the current user
            "username": current_user["username"],
            "email": current_user["email"],
            "shipment_no": shipment_no,
            "route_details": route_details,
            "device": device,
            "po_no": po_no,
            "ndc_no": ndc_no,
            "serial_no": serial_no,
            "container_no": container_no,
            "goods_type": goods_type,
            "expected_delivery": expected_delivery,
            "delivery_no": delivery_no,
            "batch_id": batch_id,
            "shipment_des": shipment_des
        }

        # Insert the new shipment into the MongoDB collection
        shipments_collection.insert_one(new_shipment)

        # Redirect the user to the "myshipment" page after creating the shipment
        return RedirectResponse("/myshipment", status.HTTP_302_FOUND)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {str(e)}")


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
