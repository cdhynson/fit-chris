import uvicorn
from fastapi import FastAPI, Request, Response, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uuid
from typing import Dict
from contextlib import asynccontextmanager

from database import (
    setup_database,
    get_user_by_username,
    get_user_by_id,
    create_session,
    get_session,
    delete_session,
    create_user,
)

# TODO: 1. create your own user
INIT_USERS = [
    {"fullname": "Alice Johnson",   "username": "alice", 
     "password": "pass123",         "location": "New York"},

    {"fullname": "Bob Smith",       "username": "bob", 
     "password": "pass456",         "location": "California"},

    {"fullname": "Chris Evans",     "username": "chris", 
     "password": "password",        "location": "Texas"}
]



# REMOVE ALL INSTANCES OF THIS FUNCTION
def get_error_html(username: str) -> str:
    error_html = read_html("./static/error.html")
    return error_html.replace("{username}", username)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for managing application startup and shutdown.
    Handles database setup and cleanup in a more structured way.
    """
    # Startup: Setup resources
    try:
        await setup_database(INIT_USERS)  # Make sure setup_database is async
        print("Database setup completed")
        yield
    finally:
        print("Shutdown completed")



# Create FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

# Mount the "static" folder so it's accessible at "/static"
app.mount("/static", StaticFiles(directory="static"), name="static")

# Static file helpers
def read_html(file_path: str) -> str:
    with open(file_path, "r") as f:
        return f.read()


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

# @app.post("/login")
# async def login(request: Request):
#     """Validate credentials and create a new session if valid"""
#     # TODO: 4. Get username and password from form data (handled via FastAPI's Form)
#     # Extract form data manually
#     form_data = await request.form()
#     username = form_data.get("username")
#     password = form_data.get("password")

#     print(f"Attempting login for user: {username} with password: {password}")

#     if not username or not password:
#         return JSONResponse(
#             content={"error": "Username and password are required."},
#             status_code=status.HTTP_400_BAD_REQUEST
#         )
    
#     # TODO: 5. Check if username exists and password matches
#     # Retrieve user from the database using the username
#     user = await get_user_by_username(username)

#     print(f"Retrieved user from database: {user}")  # Debugging step

#     # Ensure user exists and password matches
#     if not user or user["password"] != password:
#         print(f"Login failed: Incorrect password for user {username}")  # Debugging step
#         return JSONResponse(
#             content={"error": "Invalid username or password."},
#             status_code=status.HTTP_403_FORBIDDEN
#         )

#     # Retrieve user ID from the user data
#     user_id = user["id"]

#     # TODO: 6. Create a new session
#     session_id = str(uuid.uuid4())
#     await create_session(user_id=user_id, session_id=session_id)

#     # TODO: 7. Create response with:
#     #   - redirect to /user/{username}
#     #   - set cookie with session ID
#     #   - return the response
#     response = JSONResponse(content={"message": "Login successful!", "redirect": f"/user/{username}"})
#     response.set_cookie(key="sessionId", value=session_id, httponly=True)
#     # response = RedirectResponse(url=f"/user/{username}", status_code=status.HTTP_303_SEE_OTHER)
#     # response.set_cookie(key="sessionId", value=session_id, httponly=True)

#     print(f"User {username} successfully logged in with session ID: {session_id}")  # Debugging step
#     return response

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
async def signup_page(request: Request):
    return read_html("./static/dashboard.html")



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

if __name__ == "__main__":
    uvicorn.run("app:app", host="localhost", port=8000, reload=True)