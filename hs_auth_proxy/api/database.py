import os

from sqlalchemy import create_engine

DATABASE_URL = os.environ.get("HS_DATABASE_URL")
engine = create_engine(DATABASE_URL)
