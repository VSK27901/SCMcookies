from fastapi import APIRouter, HTTPException, Depends
from app.models.models import UserResetPass, UserForgotPassword, User
from app.config.db import conn, users_collection, shipments_collection, device_collection, verification_collection
from app.utils import Hash, create_access_token, get_current_user, decode_token, clear_access_token_cookie, get_current_user_from_cookie
from datetime import timedelta
from fastapi import Request, Depends, Form, HTTPException, status, Cookie, Response, Query
from jose import jwt, JWTError
from fastapi.responses import HTMLResponse, RedirectResponse
import requests
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime, date

user = APIRouter()

templates = Jinja2Templates(directory="templates")


###### ----------Route to get home page----------######

@user.get("/")
async def home_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


###### ----------Route to get login page----------######

@user.get("/login")
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


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


###### ----------route to get createshipment page in the dashboard----------######

@user.get("/createshipment", response_class=HTMLResponse)
async def createshipment(request: Request, current_user: dict = Depends(get_current_user_from_cookie)):
    try:
        if current_user is None:
            return templates.TemplateResponse("login.html", {"request": request})

        return templates.TemplateResponse("createshipment.html", {"request": request})
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {str(e)}")


###### ----------route to display my shipment page after shipment created successfully----------######

@user.get("/myshipment", response_class=HTMLResponse)
async def myshipment(request: Request, current_user: dict = Depends(get_current_user_from_cookie)):
    try:
        if current_user is None:
            return templates.TemplateResponse("login.html", {"request": request})

        # Fetch shipment data for the current user from the MongoDB collection
        user_shipments = shipments_collection.find(
            {"username": current_user["username"]})

        # Pass the data to the HTML template
        return templates.TemplateResponse("myshipment.html", {"request": request, "user_shipments": user_shipments})
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


###### ----------route to view all shipments in the db(Only admins are allowed)----------######

@user.get("/viewallshipments", response_class=HTMLResponse)
async def viewallshipments(request: Request, current_user: dict = Depends(get_current_user_from_cookie)):

    if current_user is None:
        return templates.TemplateResponse("login.html", {"request": request})

    # Fetch shipment data for the current user from the MongoDB collection
    user_shipments = shipments_collection.find({})

    role = current_user.get('role')

    if role != "admin":  # Check the role here
        # raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. Only admins are allowed.")
        error_message = f"Sorry {current_user.get('username')}, you are allowed to access this page"
        return templates.TemplateResponse("dashboard.html", {"request": request, "error_message": error_message})

    # Pass the username and email from current_user to user_data
    user_data = {
        "username": current_user["username"], "email": current_user["email"]}

    return templates.TemplateResponse("viewallshipments.html", {"request": request, "user_data": user_data, "user_shipments": user_shipments})


###### ----------To display all user(only admins can see)----------######

@user.get("/userslist", response_class=HTMLResponse)
async def userslist(request: Request, current_user: dict = Depends(get_current_user_from_cookie)):
    try:
        if current_user is None:
            return templates.TemplateResponse("login.html", {"request": request})

        user_db = users_collection.find({})

        role = current_user.get('role')

        if role != "admin":  # Check the role here
            # raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. Only admins are allowed.")
            error_message = f"Sorry {current_user.get('username')}, you are allowed to access this page"
            return templates.TemplateResponse("dashboard.html", {"request": request, "error_message": error_message})

        # Fetch user account data from the database
        user_data = {
            "username": current_user["username"], "email": current_user["email"]}

        return templates.TemplateResponse("userslist.html", {"request": request, "user_data": user_data, "user_db": user_db})

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {str(e)}")


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
