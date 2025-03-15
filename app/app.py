import uvicorn
import os
from mysql.connector import connect
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request, Response, HTTPException, status, Form, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uuid
from typing import Dict
from contextlib import asynccontextmanager
from pydantic import BaseModel
import asyncio
import requests
from datetime import datetime
from decorators import auth_required
from dotenv import load_dotenv
from database import (
    setup_database,
    get_user_by_username,
    get_user_by_id,
    create_session,
    get_session,
    delete_session,
    create_user,
    get_user_by_session,
    get_devices_by_user_id,
    create_device,
    get_wardrobe_items,
    create_wardrobe_item,
    update_wardrobe_item,
    delete_wardrobe_item,
    delete_device,

)
import json
import asyncio
active_connections = set()

# TODO: 1. create your own user
INIT_USERS = [
    {"fullname": "Alice Johnson",   "username": "alice", 
     "password": "pass123",         "location": "New York"},

    {"fullname": "Bob Smith",       "username": "bob", 
     "password": "pass456",         "location": "California"},

    {"fullname": "Chris Evans",     "username": "chris", 
     "password": "password",        "location": "California"}
]

INIT_DEVICES = [
    {"name": "Alice's ESP32", "serial": "A123", "username": "alice"},

    {"name": "Bob's ESP32", "serial": "B123", "username": "bob"},
    
    {"name": "Chris' ESP32", "serial": "C123", "username": "chris"},
    {"name": "Chris' Arduino", "serial": "C202", "username": "chris"}
]

def get_db_connection():
    return connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
    )


class DeviceCreate(BaseModel):
    name: str
    serial: str

# REMOVE ALL INSTANCES OF THIS FUNCTION
def get_error_html(username: str) -> str:
    error_html = read_html("./static/error.html")
    return error_html.replace("{username}", username)


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """
#     Lifespan context manager for managing application startup and shutdown.
#     Handles database setup and cleanup in a more structured way.
#     """
#     # Startup: Setup resources
#     try:
#         await setup_database(INIT_USERS, INIT_DEVICES)  # Make sure setup_database is async
#         print("Database setup completed")
#         yield
#     finally:
#         print("Shutdown completed")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for managing application startup and shutdown.
    """
    try:
        # Run the blocking setup_database in a separate thread
        await asyncio.to_thread(setup_database, INIT_USERS, INIT_DEVICES)
        print("Database setup completed")
        yield
    finally:
        print("Shutdown completed")

load_dotenv()

# Create FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AI_API_EMAIL = os.getenv("AI_API_EMAIL")
AI_API_PID = os.getenv("AI_API_PID")


# Mount the "static" folder so it's accessible at "/static"
app.mount("/static", StaticFiles(directory="static"), name="static")

# Static file helpers
def read_html(file_path: str) -> str:
    with open(file_path, "r") as f:
        return f.read()

# @app.get("/user-info")
# @auth_required
# async def user_info(request: Request):
#     """Returns the logged-in user's full name."""
#     user = request.state.user
#     return JSONResponse(content={"fullname": user["fullname"]})

@app.get("/user-info")
@auth_required
async def user_info(request: Request):
    """Return logged-in user's full name"""
    session_id = request.cookies.get("sessionId")

    if not session_id:
        return JSONResponse(content={"error": "User not authenticated"}, status_code=401)

    user = await get_user_by_session(session_id)
    if not user:
        return JSONResponse(content={"error": "Invalid session"}, status_code=401)

    return {"fullname": user["fullname"]}


# def get_error_html(username: str) -> str:
#     error_html = read_html("./static/error.html")
#     return error_html.replace("{username}", username) 



###########################################################
## ----------------------------------------------------- ##
## -------------------- LANDING PAGE ------------------- ##
## ----------------------------------------------------- ##
###########################################################
@app.get("/")
async def root():
    """Redirect users to /home"""
    # TODO: 2. Implement this route
    return RedirectResponse(url="/home")

@app.get("/home", response_class=HTMLResponse)
async def landing_page(request: Request):
    return read_html("./static/home.html")



###########################################################
## ----------------------------------------------------- ##
## ---------------- SIGNUP FUNCTIONALITY --------------- ##
## ----------------------------------------------------- ##
###########################################################
@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return read_html("./static/signup.html")

@app.get("/check-username")
async def check_username(username: str):
    """Checks if the username is already taken in the database."""
    existing_user = await get_user_by_username(username)

    return JSONResponse(content={"exists": existing_user is not None})

@app.post("/signup")
async def signup(
    request: Request,
    fullname: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    location: str = Form(...)
):
    """Handles user signup and redirects to login."""
    existing_user = await get_user_by_username(username)
    if existing_user:
        return JSONResponse(
            content={"error": "Username already exists."},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # Store password in plain text (⚠️ Only if you really don't want hashing)
    new_user = await create_user(fullname, username, password, location)

    if not new_user:
        return JSONResponse(
            content={"error": "User creation failed."},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return JSONResponse(
        content={"message": "Signup successful!", "redirect": "/login"},
        status_code=status.HTTP_200_OK
    )



###########################################################
## ----------------------------------------------------- ##
## ---------------- LOGIN FUNCTIONALITY ---------------- ##
## ----------------------------------------------------- ##
###########################################################
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Show login if not logged in, or redirect to profile page"""
    # TODO: 3. check if sessionId is in attached cookies and validate it
    session_id = request.cookies.get("sessionId")

    if session_id:
        session = await get_session(session_id)
        if session:
            user = await get_user_by_username(session["user_id"])
            if user:
                return RedirectResponse(url=f"/user/{user['username']}")

    # if all valid, redirect to /user/{username}
    # if not, show login page
    return read_html("./static/login.html")

@app.post("/login")
async def login(request: Request):
    """Validate credentials and create a new session if valid."""
    form_data = await request.form()
    username = form_data.get("username")
    password = form_data.get("password")

    if not username or not password:
        return JSONResponse(
            content={"error": "Username and password are required."},
            status_code=status.HTTP_400_BAD_REQUEST
        )

    user = await get_user_by_username(username)

    if not user or user["password"] != password:
        return JSONResponse(
            content={"error": "Invalid username or password."},
            status_code=status.HTTP_403_FORBIDDEN
        )

    user_id = user["id"]
    session_id = str(uuid.uuid4())
    await create_session(user_id=user_id, session_id=session_id)

    response = JSONResponse(
        content={"message": "Login successful!", "redirect": f"/user/{username}"}
    )
    response.set_cookie(key="sessionId", value=session_id, httponly=True)

    return response

@app.get("/user/{username}", response_class=HTMLResponse)
async def user_page(username: str, request: Request):
    """Show user profile if authenticated, error if not"""
    # TODO: 11. Get sessionId from cookies
    session_id = request.cookies.get("sessionId")
    print(f"Checking session for {username}, session ID: {session_id}")  # Debugging step

    # TODO: 12. Check if sessionId exists and is valid
    #   - if not, redirect to /login
    if not session_id:
        return RedirectResponse(url="/login")

    session = await get_session(session_id)
    if not session:
        print(f"No session found for session ID: {session_id}")  # Debugging step
        return RedirectResponse(url="/login")

    # TODO: 13. Check if session username matches URL username
    #   - if not, return error page using get_error_html with 403 status
    user = await get_user_by_id(session["user_id"])
    print(f"Session user: {user}")  # Debugging step

    if not user or user["username"] != username:
        print(f"Session mismatch: {user['username']} != {username}")  # Debugging step
        return HTMLResponse(get_error_html(username), status_code=status.HTTP_403_FORBIDDEN)

    # TODO: 14. If all valid, show profile page
    return read_html("./static/dashboard.html")





###########################################################
## ----------------------------------------------------- ##
## ------------ USER DASHBOARD FUNCTIONALITY ----------- ##
## ----------------------------------------------------- ##
###########################################################
@app.get("/dashboard", response_class=HTMLResponse)
@auth_required
async def signup_page(request: Request):
    return read_html("./static/dashboard.html")



###########################################################
## ----------------------------------------------------- ##
## ---------------- PROFILE FUNCTIONALITY -------------- ##
## ----------------------------------------------------- ##
###########################################################
@app.get("/profile", response_class=HTMLResponse)
@auth_required
async def profile_page(request: Request):
    session_id = request.cookies.get("sessionId")

    # ✅ If no session, redirect to login
    if not session_id:
        return RedirectResponse(url="/login")

    # ✅ Check if session is valid
    user = await get_user_by_session(session_id)
    if not user:
        return RedirectResponse(url="/login")

    return HTMLResponse(open("./static/profile.html").read())

# ✅ Fetch all devices for the logged-in user
@app.get("/devices")
async def get_devices(request: Request):
    session_id = request.cookies.get("sessionId")

    if not session_id:
        return JSONResponse(content={"error": "User not authenticated"}, status_code=401)

    user = await get_user_by_session(session_id)
    if not user:
        return JSONResponse(content={"error": "Invalid session"}, status_code=401)

    devices = await get_devices_by_user_id(user["id"])  # Fetch devices for the user
    return devices  # Return devices in JSON format

# ✅ Add a new device for the logged-in user
@app.post("/devices")
async def add_device(request: Request, device: DeviceCreate):
    session_id = request.cookies.get("sessionId")

    if not session_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    user = await get_user_by_session(session_id)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")

    # ✅ Store the device in the database
    await create_device(user_id=user["id"], name=device.name, serial=device.serial)
    return {"message": "Device added successfully"}

@app.delete("/devices/{serial}")
async def remove_device(request: Request, serial: str):
    session_id = request.cookies.get("sessionId")

    if not session_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    user = await get_user_by_session(session_id)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")

    # ✅ Delete the device from the database
    success = await delete_device(user_id=user["id"], serial=serial)

    if success:
        return {"message": f"Device {serial} removed successfully."}
    else:
        raise HTTPException(status_code=404, detail="Device not found or deletion failed")

###########################################################
## ----------------------------------------------------- ##
## ---------------- LOGOUT FUNCTIONALITY --------------- ##
## ----------------------------------------------------- ##
###########################################################
@app.post("/logout")
async def logout(request: Request):
    """Clear session and redirect to login page"""
    # TODO: 8. Create redirect response to /login
    response = RedirectResponse(url="/home", status_code=status.HTTP_303_SEE_OTHER)

    # TODO: 9. Delete sessionId cookie
    session_id = request.cookies.get("sessionId")

    if session_id:
        await delete_session(session_id)

    response.delete_cookie("sessionId")

    # TODO: 10. Return response
    return response


@app.get("/wardrobe", response_class=HTMLResponse)
@auth_required
async def wardrobe_page(request: Request):
    return read_html("./static/wardrobe.html")
###########################################################
## ----------------------------------------------------- ##
## -------------------- Weather API -------------------- ##
## ----------------------------------------------------- ##
###########################################################


@app.get("/api/weather")
async def weather(request: Request):
    
    session_id = request.cookies.get("sessionId")
    if not session_id:
        return RedirectResponse(url="/login")

    session = await get_session(session_id)
    if not session:
        return RedirectResponse(url="/login")

    user = await get_user_by_id(session["user_id"])
    if not user:
        return RedirectResponse(url="/login")


    city = user.get("location", "San Diego")

   
    try:
        nominatim_url = "https://nominatim.openstreetmap.org/search"
        nom_params = {"q": city, "format": "json"}
        nom_response = requests.get(nominatim_url, params=nom_params, headers={"User-Agent": "FIT-App"})
        nom_data = nom_response.json()
        if not nom_data:
            return {"error": f"No location found for {city}"}
        lat = nom_data[0]["lat"]
        lon = nom_data[0]["lon"]
    except Exception as e:
        return {"error": f"Error fetching geolocation: {str(e)}"}

    
    try:
        points_url = f"https://api.weather.gov/points/{lat},{lon}"
        points_resp = requests.get(points_url, headers={"User-Agent": "FIT-App"})
        points_data = points_resp.json()
        daily_forecast_url = points_data["properties"]["forecast"]  
    except Exception as e:
        return {"error": f"Error fetching forecast URL: {str(e)}"}

    
    try:
        forecast_resp = requests.get(daily_forecast_url, headers={"User-Agent": "FIT-App"})
        forecast_data = forecast_resp.json()
        periods = forecast_data["properties"]["periods"] 

        if not periods:
            return {"error": "No forecast periods available."}

        first_period = periods[0]
        temperature = first_period["temperature"]  
        icon = first_period["icon"]
        unit = "F"

    except Exception as e:
        return {"error": f"Error fetching daily forecast: {str(e)}"}

   
    return {
        "city": city,
        "temperature": temperature,
        "unit": unit,
        "icon": icon
    }           

@app.post("/api/recommendation")
async def recommendation(request: Request):
   
    body = await request.json()
    prompt = body.get("prompt", "What should I wear today?")
    
    headers = {
        "email": AI_API_EMAIL, 
        "pid": AI_API_PID,     
        "Content-Type": "application/json"
    }
    ai_api_url = "https://ece140-wi25-api.frosty-sky-f43d.workers.dev/api/v1/ai/complete"
    payload = {"prompt": prompt}
    
    response = requests.post(ai_api_url, headers=headers, json=payload)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="AI API error")
    
    suggestion = response.json()
    print("External AI API response:", suggestion)
    
    if suggestion.get("success") and "result" in suggestion and "response" in suggestion["result"]:
        suggestion_text = suggestion["result"]["response"]
    else:
        suggestion_text = str(suggestion)
    
    return {"message": suggestion_text}





@app.post("/api/ai/image")
async def generate_image(request: Request):
   
    body = await request.json()
    prompt = body.get("prompt", "A stylish outfit")
    width = body.get("width", 512)
    height = body.get("height", 512)

    headers = {
        "email": AI_API_EMAIL,
        "pid": AI_API_PID,
        "Content-Type": "application/json"
    }
    image_api_url = "https://ece140-wi25-api.frosty-sky-f43d.workers.dev/api/v1/ai/image"
    payload = {"prompt": prompt, "width": width, "height": height}

    response = requests.post(image_api_url, headers=headers, json=payload)
    
   
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="AI Image API error: " + response.text)
    
    try:
        json_data = response.json()
    except Exception as e:
        
        print("Error decoding JSON from AI Image API:", e)
        print("Response text:", response.text)
        raise HTTPException(status_code=500, detail="Error decoding JSON from AI Image API")
    
    return json_data





















SENSOR_TYPES = ["temperature"]

@app.get("/api/{sensor_type}")
def get_sensor_data(
    sensor_type: str,
    order_by: str = Query(None, alias="order-by"),
    start_date: str = Query(None, alias="start-date"),
    end_date: str = Query(None, alias="end-date")
):
    if sensor_type not in SENSOR_TYPES:
        raise HTTPException(status_code=404, detail="Invalid sensor type")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = f"SELECT * FROM {sensor_type}"
    conditions = []
    params = []

    if start_date:
        conditions.append("timestamp >= %s")
        params.append(start_date)
    if end_date:
        conditions.append("timestamp <= %s")
        params.append(end_date)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    if order_by in ["value", "timestamp"]:
        query += f" ORDER BY {order_by}"

    cursor.execute(query, params)
    results = cursor.fetchall()

    
    for row in results:
        row["timestamp"] = row["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

    cursor.close()
#     conn.close()

    return results

@app.post("/api/{sensor_type}")
def insert_sensor_data(sensor_type: str, data: dict):
    if sensor_type not in SENSOR_TYPES:
        raise HTTPException(status_code=404, detail="Invalid sensor type")

    conn = get_db_connection()
    cursor = conn.cursor()

    timestamp = data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))  
    value = data.get("value")
    unit = data.get("unit")

    if value is None or unit is None:
        raise HTTPException(status_code=400, detail="Missing required fields: value, unit")

    query = f"INSERT INTO {sensor_type} (timestamp, value, unit) VALUES (%s, %s, %s)"
    cursor.execute(query, (timestamp, value, unit))
    conn.commit()
    inserted_id = cursor.lastrowid

    cursor.close()
    conn.close()
    return {"id": inserted_id}

@app.websocket("/ws/sensor/{sensor_type}")
async def websocket_endpoint(websocket: WebSocket, sensor_type: str):
    await websocket.accept()
    active_connections.add(websocket)

    try:
        while True:
            await asyncio.sleep(2)  # Update Every 2 Seconds
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            query = f"SELECT * FROM {sensor_type} ORDER BY timestamp DESC LIMIT 10"
            cursor.execute(query)
            results = cursor.fetchall()

            for row in results:
                row["timestamp"] = row["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

            cursor.close()
            conn.close()

            data = json.dumps(results)
            await websocket.send_text(data)

    except WebSocketDisconnect:
        active_connections.remove(websocket)

















@app.put("/api/{sensor_type}/{id}")
def update_sensor_data(sensor_type: str, id: int, data: dict):
    if sensor_type not in SENSOR_TYPES:
        raise HTTPException(status_code=404, detail="Invalid sensor type")

    conn = get_db_connection()
    cursor = conn.cursor()

    update_fields = []
    params = []

    if "value" in data:
        update_fields.append("value = %s")
        params.append(data["value"])
    if "unit" in data:
        update_fields.append("unit = %s")
        params.append(data["unit"])
    if "timestamp" in data:
        update_fields.append("timestamp = %s")
        params.append(data["timestamp"])

    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    params.append(id)
    query = f"UPDATE {sensor_type} SET {', '.join(update_fields)} WHERE id = %s"

    cursor.execute(query, tuple(params))
    conn.commit()

    cursor.close()
    conn.close()
    return {"message": "Data updated successfully"}

@app.delete("/api/{sensor_type}/{id}")
def delete_sensor_data(sensor_type: str, id: int):
    if sensor_type not in SENSOR_TYPES:
        raise HTTPException(status_code=404, detail="Invalid sensor type")

    conn = get_db_connection()
    cursor = conn.cursor()

    query = f"DELETE FROM {sensor_type} WHERE id = %s"
    cursor.execute(query, (id,))
    conn.commit()

    cursor.close()
    conn.close()
    return {"message": "Data deleted successfully"}















###########################################################
## ---------------- WARDROBE CRUD ENDPOINTS -------------- ##
###########################################################

@app.post("/api/wardrobe")
async def add_clothing(request: Request):
    """
    Add a new clothing item to the wardrobe for the currently logged-in user.
    Expects a JSON body with "name" and "type".
    """
    session_id = request.cookies.get("sessionId")
    if not session_id:
        return RedirectResponse(url="/login")
    
    session = await get_session(session_id)
    if not session:
        return RedirectResponse(url="/login")
    
    user = await get_user_by_id(session["user_id"])
    if not user:
        return RedirectResponse(url="/login")
    
    body = await request.json()
    name = body.get("name")
    type_ = body.get("type")
    if not name or not type_:
        raise HTTPException(status_code=400, detail="Name and type are required")
    
    new_item = await create_wardrobe_item(user["id"], name, type_)
    if not new_item:
        raise HTTPException(status_code=500, detail="Error creating wardrobe item")
    
    
    if "created_at" in new_item and isinstance(new_item["created_at"], datetime):
        new_item["created_at"] = new_item["created_at"].isoformat()
    
    return JSONResponse(content=new_item, status_code=201)


@app.get("/api/wardrobe")
async def get_wardrobe(request: Request):
    """
    Retrieve all wardrobe items for the currently logged-in user.
    """
    session_id = request.cookies.get("sessionId")
    if not session_id:
        return RedirectResponse(url="/login")
    
    session = await get_session(session_id)
    if not session:
        return RedirectResponse(url="/login")
    
    user = await get_user_by_id(session["user_id"])
    if not user:
        return RedirectResponse(url="/login")
    
    # Retrieve wardrobe items from the database for the current user.
    items = await get_wardrobe_items(user["id"])
    
    # Convert datetime fields (e.g., created_at) to ISO strings.
    for item in items:
        if "created_at" in item and isinstance(item["created_at"], datetime):
            item["created_at"] = item["created_at"].isoformat()
    
    return JSONResponse(content=items)


@app.put("/api/wardrobe/{item_id}")
async def update_clothing(item_id: int, request: Request):
    """
    Update an existing clothing item for the logged-in user.
    Expects a JSON body with "name" and/or "type".
    """
    session_id = request.cookies.get("sessionId")
    if not session_id:
        return RedirectResponse(url="/login")
    
    session = await get_session(session_id)
    if not session:
        return RedirectResponse(url="/login")
    
    user = await get_user_by_id(session["user_id"])
    if not user:
        return RedirectResponse(url="/login")
    
    body = await request.json()
    name = body.get("name")
    type_ = body.get("type")
    
    updated_item = await update_wardrobe_item(item_id, user["id"], name, type_)
    if not updated_item:
        raise HTTPException(status_code=404, detail="Item not found or nothing to update")
    
    if "created_at" in updated_item and isinstance(updated_item["created_at"], datetime):
        updated_item["created_at"] = updated_item["created_at"].isoformat()
    
    return JSONResponse(content=updated_item)



@app.delete("/api/wardrobe/{item_id}")
async def delete_clothing(item_id: int, request: Request):
    """
    Delete a clothing item for the logged-in user.
    """
    session_id = request.cookies.get("sessionId")
    if not session_id:
        return RedirectResponse(url="/login")
    
    session = await get_session(session_id)
    if not session:
        return RedirectResponse(url="/login")
    
    user = await get_user_by_id(session["user_id"])
    if not user:
        return RedirectResponse(url="/login")
    
    success = await delete_wardrobe_item(item_id, user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return JSONResponse(content={"detail": "Item deleted"})














if __name__ == "__main__":
   uvicorn.run(app="app.main:app", host="0.0.0.0", port=8000, reload=True)
