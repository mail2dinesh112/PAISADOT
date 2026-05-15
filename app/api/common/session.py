################################################
# Author                : DINESHKUMAR A
# Created Date          : 09th MAY, 2026
# Last Date Modified    : 09th MAY, 2026
# Last Modified By      : DINESHKUMAR A
# Description           : This file is used to create a database session.
################################################

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

required_env_vars = [
    "DATABASE_NAME",
    "DATABASE_HOST",
    "DATABASE_PORT",
    "DATABASE_PASSWORD",
    "DATABASE_USER",
]
missing_env_vars = [env_var for env_var in required_env_vars if not os.getenv(env_var)]

if missing_env_vars:
    raise RuntimeError(
        "Missing database environment variables: " + ", ".join(missing_env_vars)
    )

CONNECTION_URL = "postgresql://{DB_UserName}:{DB_Password}@{DB_Host}:{DB_Port}/{DB_Name}".format(
  DB_Name     = os.getenv(f"DATABASE_NAME"),
  DB_Host     = os.getenv(f"DATABASE_HOST"),
  DB_Port     = os.getenv(f"DATABASE_PORT"),
  DB_Password = os.getenv(f"DATABASE_PASSWORD"),
  DB_UserName = os.getenv(f"DATABASE_USER"),
)

engine = create_engine(
    CONNECTION_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=5,
    pool_timeout=300,
    pool_recycle=1800,
    pool_pre_ping=True
)
Session   = sessionmaker(bind=engine)


def get_db():
    session = Session()
    try:
        yield session
    finally:
        session.close()
