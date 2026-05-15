################################################
# Author                : DINESHKUMAR A
# Created Date          : 09th MAY, 2026
# Last Date Modified    : 09th MAY, 2026
# Last Modified By      : DINESHKUMAR A
# Description           : This file is used to define the common routes.
################################################

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importing API routes
from api.user import user
from api.accounts import accounts
from api.authentication import authentication
from api.categories import category
from api.expanse import expanse



environ = os.getenv("APP_ENV")
is_swagger = os.getenv(f"IS_SWAGGER_ENABLED")
servers = []
cors_allow_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", "").split(",")
    if origin.strip()
]

if not cors_allow_origins and environ == "development":
    cors_allow_origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
    ]

if environ == "development" and is_swagger == "True":
    servers = [
        {"url": "http://localhost:8000", "description": "localhost"},
        {"url": "https://nzbn4dcm-8000.inc1.devtunnels.ms/", "description": "devtunnel"}
    ]


# Initialize FastAPI application
app = FastAPI(
    title="PAISA DOT API",
    version="0.0.1",
    description="💰 PAISA DOT API - Empowering Financial Interactions with FastAPI 🚀",
    docs_url=None if is_swagger == "False" else "/api/docs",
    redoc_url=None if is_swagger == "False" else "/api/redoc",
    openapi_url=None if is_swagger == "False" else "/api/openapi.json",
    servers=servers,
    openapi_tags=[
        {
            "name": "Unauthorized API",
            "description": " 🚫 Access Control-> Open to the public, no authentication required, Security-> No security restrictions, Usage-> Used for public information like weather, news, or open search APIs",
        },
        {
            "name": "Authorized API",
            "description": "   🔐 Access Control-> Requires authentication (JWT, OAuth, API key), Security-> Enforces user identity and permissions, Usage-> Used for protected operations like user data, payments, or admin tasks",
        }
    ],
)

# Include API routes
app.include_router(accounts.router)
app.include_router(authentication.router)
app.include_router(user.router)
app.include_router(category.router)
app.include_router(expanse.router)


# APP Events
@app.on_event("startup")
def startup_event():
    print("Application started with FastAPI.")

@app.on_event("shutdown")
def shutdown_event():
    print("Application shutdown.")



# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allow_origins,
    allow_credentials=bool(cors_allow_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)
