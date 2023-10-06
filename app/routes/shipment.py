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
