from functools import wraps
from typing import Callable, Optional, Dict, Any, List, Tuple
from fastapi import Request, Response, HTTPException, Depends
from fastapi.responses import RedirectResponse
import inspect
import mysql.connector
from mysql.connector import pooling
import secrets
import hashlib
import uuid
import time
import json
from datetime import datetime, timedelta
from pydantic import BaseModel
from database import get_session, get_user_by_id, delete_session

def auth_required(func: Callable) -> Callable:
    """
    Universal authentication decorator for FastAPI route handlers.
    Works with both sync and async functions.
    
    Usage:
    ```
    @app.get("/protected")
    @auth_required
    def protected_route(request: Request):
        return {"message": "This is a protected route"}
    
    @app.get("/protected-async")
    @auth_required
    async def protected_async_route(request: Request):
        return {"message": "This is a protected async route"}
    ```
    """
    is_async = inspect.iscoroutinefunction(func)
    
    if is_async:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract the FastAPI request object from arguments
            request = _extract_request(args, kwargs)

            # Retrieve session ID from cookies
            session_id = request.cookies.get("sessionId")

            # If no session ID is found, redirect to login page
            if not session_id:
                return RedirectResponse(url="/login", status_code=303)

            # Retrieve session details from the database
            session = await get_session(session_id)

            # If session is not found, redirect to login
            if not session:
                return RedirectResponse(url="/login", status_code=303)

            # Retrieve user details from the database using session's user ID
            user = await get_user_by_id(session["user_id"])

            # If user is not found (e.g., deleted), delete session and redirect to login
            if not user:
                await delete_session(session_id)
                return RedirectResponse(url="/login", status_code=303)

            # Attach user details to the request state, making it accessible in the route function
            request.state.user = user  

            # Proceed with the original route function
            return await func(*args, **kwargs)

        return async_wrapper
    else:
        # If the function is synchronous, use a sync wrapper
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Extract the FastAPI request object from arguments
            request = _extract_request(args, kwargs)

            # Retrieve session ID from cookies
            session_id = request.cookies.get("sessionId")

            # If no session ID is found, redirect to login page
            if not session_id:
                return RedirectResponse(url="/login", status_code=303)

            # Retrieve session details from the database
            session = get_session(session_id)

            # If session is not found, redirect to login
            if not session:
                return RedirectResponse(url="/login", status_code=303)

            # Retrieve user details from the database using session's user ID
            user = get_user_by_id(session["user_id"])

            # If user is not found (e.g., deleted), delete session and redirect to login
            if not user:
                delete_session(session_id)
                return RedirectResponse(url="/login", status_code=303)

            # Attach user details to the request state, making it accessible in the route function
            request.state.user = user  

            # Proceed with the original route function
            return func(*args, **kwargs)

        return sync_wrapper
    

def _extract_request(args, kwargs):
    """
    Extracts the FastAPI Request object from function arguments.
    This ensures that the decorator can be applied to both sync and async routes.
    """
    for arg in args:
        if isinstance(arg, Request):
            return arg  # Return the found Request object

    if "request" in kwargs:
        return kwargs["request"]  # Return the Request object from kwargs

    # Raise an error if the request object is missing
    raise HTTPException(status_code=500, detail="Request object not found in function arguments")

async def is_authenticated(request):
    """Checks if a user is authenticated based on session ID."""
    session_id = request.cookies.get("sessionId")

    if not session_id:
        return None

    session = await get_session(session_id)
    if not session:
        return None

    # Check if session is expired
    if session["expires_at"] < datetime.utcnow():
        await delete_session(session_id)  # Auto-delete expired session
        return None

    return await get_user_by_id(session["user_id"])

def auth_required(func):
    """Decorator to protect routes and redirect unauthorized users to login."""
    @wraps(func)
    async def wrapper(request, *args, **kwargs):
        user = await is_authenticated(request)
        if not user:
            return RedirectResponse(url="/login")

        request.state.user = user
        return await func(request, *args, **kwargs)
    return wrapper
