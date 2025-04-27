from . import schemas, models, crud, utils
from .config import config
from .database import Base, engine

# Create all database tables
Base.metadata.create_all(bind=engine)
