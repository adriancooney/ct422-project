from sqlalchemy.sql import text
from project.src.model import *
from project.src.config import engine

# Drop all the tables
# Base.metadata.drop_all(engine)

# Create the database
Base.metadata.create_all(engine)