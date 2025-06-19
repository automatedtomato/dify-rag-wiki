"""
database.py

This module defines the configuration for the database connection.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Load environment variables from .env
load_dotenv()

# Get database connection details from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

# `create_engine` is the entrypoint for the database
engine = create_engine(DATABASE_URL)

# `sessionmaker` configures the database conversations (sessions)
# Each session is an independent transaction
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# `declarative_base` offers a base class for the creation of each DB table
# All DB models should inherit from this class
Base = declarative_base()
