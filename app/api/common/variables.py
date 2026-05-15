################################################
# Author                : DINESHKUMAR A
# Created Date          : 09th MAY, 2026
# Last Date Modified    : 09th MAY, 2026
# Last Modified By      : DINESHKUMAR A
# Description           : This file is used to define common variables for the API.
################################################

import os
from dotenv import load_dotenv

load_dotenv()

# Database variables
DATABASE_NAME     = os.getenv(f"DATABASE_NAME")
DATABASE_HOST     = os.getenv(f"DATABASE_HOST")
DATABASE_PORT     = os.getenv(f"DATABASE_PORT")
DATABASE_PASSWORD = os.getenv(f"DATABASE_PASSWORD")
DATABASE_USER     = os.getenv(f"DATABASE_USER")


# Security variables
JWT_SECRET_KEY              = os.getenv(f"JWT_SECRET_KEY")
JWT_ALGORITHM               = os.getenv(f"JWT_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv(f"ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_DAYS   = int(os.getenv(f"REFRESH_TOKEN_EXPIRE_DAYS"))