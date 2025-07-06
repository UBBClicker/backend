import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import os

from app import api
from app.database import SessionLocal
from app import crud

fastapi_app = FastAPI(title="UBBClicker API")

# Add CORS middleware - more permissive for development
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "http://localhost:3000",  # Alternative frontend ports
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
)

fastapi_app.include_router(api.root_router)

# Health check endpoint for testing CORS
@fastapi_app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Backend is running with CORS enabled"}

# Initialize database with items
def initialize_items():
    """Load items from items.json into database if they don't exist"""
    db = SessionLocal()
    try:
        # Check if items already exist
        existing_items = crud.item.get_all_items(db)
        if existing_items:
            print(f"Database already has {len(existing_items)} items")
            return
        
        # Load items from JSON file
        items_file = os.path.join(os.path.dirname(__file__), "items.json")
        if os.path.exists(items_file):
            with open(items_file, 'r') as f:
                items_data = json.load(f)
            
            # Create items in database using the schemas
            from app.schemas.item import ItemCreate
            for item_data in items_data:
                item_create = ItemCreate(**item_data)
                crud.item.create(db, item_create)
                print(f"Created item: {item_data['name']}")
            
            print(f"Loaded {len(items_data)} items into database")
        else:
            print("items.json file not found")
    except Exception as e:
        print(f"Error initializing items: {e}")
    finally:
        db.close()

# Startup event
@fastapi_app.on_event("startup")
async def startup_event():
    print("Starting UBBClicker backend...")
    initialize_items()
    print("Backend startup complete")


def main():
    # SQLite tables are already created in app/__init__.py
    uvicorn.run("main:fastapi_app", port=3001, reload=True)


if __name__ == "__main__":
    main()
