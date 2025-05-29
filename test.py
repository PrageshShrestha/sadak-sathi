# auth.py
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from jose import JWTError, jwt
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from sqlalchemy.ext.asyncio import AsyncSession
from crud import get_user_by_bus_number
from database import get_db
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def authenticate_user(db: AsyncSession, bus_number: str, password: str):
    user = await get_user_by_bus_number(db, bus_number)
    if not user or not pwd_context.verify(password, user.password_hash):
        return False
    return user

async def create_access_token(bus_number: str):
    expire = datetime.utcnow() + timedelta(days=1)  # Token valid for 24 hours
    to_encode = {"sub": bus_number, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        bus_number: str = payload.get("sub")
        if bus_number is None:
            raise credentials_exception
        user = await get_user_by_bus_number(db, bus_number)
        if user is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return user
# config.py
DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # Token expires in 24 hours (1440 minutes)
# crud.py
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import User, BusLocation
from schemas import UserCreate, LocationUpdate
from datetime import datetime
from sqlalchemy.orm import selectinload
import json

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Function to create a new bus driver (user)

async def create_bus_driver(db: AsyncSession, user: UserCreate):
    hashed_password = pwd_context.hash(user.password)
    new_user = User(
        username=user.username,
        bus_number=user.bus_number,
        route_id=user.route_id,
        password_hash=hashed_password,
        status=True  # Default status is "available"
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

# Function to update the bus location
async def update_bus_location(db: AsyncSession, location: LocationUpdate):
    result = await db.execute(select(BusLocation).filter(BusLocation.bus_number == location.bus_number))
    bus_location = result.scalar_one_or_none()

    new_location = {"lat": location.lat, "lon": location.lon, "timestamp": datetime.utcnow().isoformat()}

    if bus_location:
        # Shift locations in history
        if bus_location.last_5_sec_locations:
            locations = json.loads(bus_location.last_5_sec_locations)
        else:
            locations = []

        locations.append(new_location)
        if len(locations) > 5:  # Keep only last 5 locations
            locations.pop(0)

        bus_location.last_5_sec_locations = json.dumps(locations)
        bus_location.last_25_sec_location = bus_location.last_15_sec_location
        bus_location.last_15_sec_location = new_location
        bus_location.current_lat = location.lat
        bus_location.current_lon = location.lon
        bus_location.last_updated = datetime.utcnow()
    else:
        # First-time insert
        bus_location = BusLocation(
            bus_number=location.bus_number,
            current_lat=location.lat,
            current_lon=location.lon,
            last_5_sec_locations=json.dumps([new_location]),
            last_15_sec_location=new_location,
            last_25_sec_location=None,
            last_updated=datetime.utcnow()
        )
        db.add(bus_location)
    
    await db.commit()
    return bus_location

# database.py



from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/dbname")

# ✅ Define Base here to prevent circular imports
Base = declarative_base()

engine = create_async_engine(DATABASE_URL, echo=True)

# Asynchronous session maker
async_session_maker = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

# Utility function to get DB session
async def get_db():
    async with async_session_maker() as session:
        yield session

# main.py
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from routes import router as api_router  # Import your router
from database import get_db, engine  # Import get_db and engine from your database file
from sqlalchemy.future import select
from models import RouteInfo, User  # Import RouteInfo and User models
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from base import Base
from sqlalchemy import insert
import hashlib

# Initialize FastAPI app
app = FastAPI()

# Initialize Jinja2 templates for rendering HTML
templates = Jinja2Templates(directory="templates")

# Serve static files (for example, for JavaScript, CSS, etc.)
# app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routes (Make sure you have a routes.py file with your API routes)
app.include_router(api_router)

# Function to populate route data if the routes are empty
async def populate_routes_if_empty():
    async for session in get_db():
        # Check if routes already exist in the database
        result = await session.execute(select(RouteInfo))
        existing_routes = result.scalars().all()

        # If no routes exist, insert demo data
        if not existing_routes:
            route_data = [
                # Route 1: Panauti-Banepa
                {
                    "route_id": "route_1",
                    "route_name": "Panauti-Banepa",
                    "coordinates": [
                       
                        {"lat": 27.594185, "lon": 85.519209},
                        {"lat": 27.594432, "lon": 85.519713},
                        {"lat": 27.594908, "lon": 85.520689},
                        {"lat": 27.595583, "lon": 85.521119},
                        {"lat": 27.596106, "lon": 85.521655},
                        {"lat": 27.596363, "lon": 85.521827},
                        {"lat": 27.596619, "lon": 85.522310},
                        {"lat": 27.597019, "lon": 85.522943},
                        {"lat": 27.597798, "lon": 85.523736},
                        {"lat": 27.598445, "lon": 85.524123},
                        {"lat": 27.598873, "lon": 85.524455},
                        {"lat": 27.599529, "lon": 85.524713},
                        {"lat": 27.599938, "lon": 85.524970},
                        {"lat": 27.600261, "lon": 85.525442},
                        {"lat": 27.600556, "lon": 85.526150},
                        {"lat": 27.600708, "lon": 85.526526},
                        {"lat": 27.600907, "lon": 85.527352},
                        {"lat": 27.601221, "lon": 85.528221},
                        {"lat": 27.602239, "lon": 85.529144},
                        {"lat": 27.602952, "lon": 85.529530},
                        {"lat": 27.603560, "lon": 85.529648},
                        {"lat": 27.604425, "lon": 85.529541},
                        {"lat": 27.605167, "lon": 85.529401},
                        {"lat": 27.605956, "lon": 85.529777},
                        {"lat": 27.606546, "lon": 85.530131},
                        {"lat": 27.607040, "lon": 85.530313},
                        {"lat": 27.607696, "lon": 85.530775},
                        {"lat": 27.608428, "lon": 85.530549},
                        {"lat": 27.609131, "lon": 85.530957},
                        {"lat": 27.609721, "lon": 85.531021},
                        {"lat": 27.610177, "lon": 85.530485},
                        {"lat": 27.611394, "lon": 85.530185},
                        {"lat": 27.612640, "lon": 85.529836},
                        {"lat": 27.613329, "lon": 85.530093},
                        {"lat": 27.613861, "lon": 85.530120},
                        {"lat": 27.614184, "lon": 85.529718},
                        {"lat": 27.615672, "lon": 85.528827},
                        {"lat": 27.616808, "lon": 85.528302},
                        {"lat": 27.617982, "lon": 85.527534},
                        {"lat": 27.618729, "lon": 85.526853},
                        {"lat": 27.619579, "lon": 85.525737},
                        {"lat": 27.620991, "lon": 85.524922},
                        {"lat": 27.621680, "lon": 85.524160},
                        {"lat": 27.622213, "lon": 85.524037},
                        {"lat": 27.623154, "lon": 85.523908},
                        {"lat": 27.624698, "lon": 85.523366},
                        {"lat": 27.625663, "lon": 85.523034},
                        {"lat": 27.626752, "lon": 85.522889},
                        {"lat": 27.627840, "lon": 85.522814},
                        {"lat": 27.628073, "lon": 85.523286},
                        {"lat": 27.629941, "lon": 85.523908},
                    ],
                },
                # Route 2: Banepa-Panauti (reverse of Route 1)
                {
                    "route_id": "route_2",
                    "route_name": "Banepa-Panauti",
                    "coordinates": [
                        {"lat": 27.629941, "lon": 85.523908},
                        {"lat": 27.628073, "lon": 85.523286},
                        {"lat": 27.627840, "lon": 85.522814},
                        {"lat": 27.626752, "lon": 85.522889},
                        {"lat": 27.625663, "lon": 85.523034},
                        {"lat": 27.624698, "lon": 85.523366},
                        {"lat": 27.623154, "lon": 85.523908},
                        {"lat": 27.622213, "lon": 85.524037},
                        {"lat": 27.621680, "lon": 85.524160},
                        {"lat": 27.620991, "lon": 85.524922},
                        {"lat": 27.619579, "lon": 85.525737},
                        {"lat": 27.618729, "lon": 85.526853},
                        {"lat": 27.617982, "lon": 85.527534},
                        {"lat": 27.616808, "lon": 85.528302},
                        {"lat": 27.615672, "lon": 85.528827},
                        {"lat": 27.614184, "lon": 85.529718},
                        {"lat": 27.613861, "lon": 85.530120},
                        {"lat": 27.613329, "lon": 85.530093},
                        {"lat": 27.612640, "lon": 85.529836},
                        {"lat": 27.611394, "lon": 85.530185},
                        {"lat": 27.610177, "lon": 85.530485},
                        {"lat": 27.609721, "lon": 85.531021},
                        {"lat": 27.609131, "lon": 85.530957},
                        {"lat": 27.608428, "lon": 85.530549},
                        {"lat": 27.607696, "lon": 85.530775},
                        {"lat": 27.607040, "lon": 85.530313},
                        {"lat": 27.606546, "lon": 85.530131},
                        {"lat": 27.605956, "lon": 85.529777},
                        {"lat": 27.605167, "lon": 85.529401},
                        {"lat": 27.604425, "lon": 85.529541},
                        {"lat": 27.603560, "lon": 85.529648},
                        {"lat": 27.602952, "lon": 85.529530},
                        {"lat": 27.602239, "lon": 85.529144},
                        {"lat": 27.601221, "lon": 85.528221},
                        {"lat": 27.600907, "lon": 85.527352},
                        {"lat": 27.600708, "lon": 85.526526},
                        {"lat": 27.600556, "lon": 85.526150},
                        {"lat": 27.600261, "lon": 85.525442},
                        {"lat": 27.599938, "lon": 85.524970},
                        {"lat": 27.599529, "lon": 85.524713},
                        {"lat": 27.598873, "lon": 85.524455},
                        {"lat": 27.598445, "lon": 85.524123},
                        {"lat": 27.597798, "lon": 85.523736},
                        {"lat": 27.597019, "lon": 85.522943},
                        {"lat": 27.596619, "lon": 85.522310},
                        {"lat": 27.596363, "lon": 85.521827},
                        {"lat": 27.596106, "lon": 85.521655},
                        {"lat": 27.595583, "lon": 85.521119},
                        {"lat": 27.594908, "lon": 85.520689},
                        {"lat": 27.594432, "lon": 85.519713},
                        {"lat": 27.594185, "lon": 85.519209},
                        {"lat": 27.593672, "lon": 85.518458},
                        {"lat": 27.592816, "lon": 85.517117},
                        {"lat": 27.591998, "lon": 85.516870},
                        {"lat": 27.591437, "lon": 85.516934},
                        {"lat": 27.590677, "lon": 85.516816},
                        {"lat": 27.590410, "lon": 85.516731},
                        {"lat": 27.590173, "lon": 85.516645},
                        {"lat": 27.589459, "lon": 85.515840},
                        {"lat": 27.588994, "lon": 85.514703},
                        {"lat": 27.603475, "lon": 85.529637},
                        {"lat": 27.602578, "lon": 85.529511},
                        {"lat": 27.5987, "lon": 85.5364},
                    ],
                },
                # Route 3: Panauti-Ratnapark
                {
                    "route_id": "route_3",
                    "route_name": "Panauti-Ratnapark",
                    "coordinates": [
                        {"lat": 27.5987, "lon": 85.5364},
                        {"lat": 27.5965, "lon": 85.5377},
                        {"lat": 27.5950, "lon": 85.5391},
                        {"lat": 27.5938, "lon": 85.5405},
                        {"lat": 27.5915, "lon": 85.5420},
                        {"lat": 27.5890, "lon": 85.5433},
                        {"lat": 27.5872, "lon": 85.5442},
                        {"lat": 27.5858, "lon": 85.5450},
                        {"lat": 27.5841, "lon": 85.5460},
                        {"lat": 27.5827, "lon": 85.5473},
                        {"lat": 27.5815, "lon": 85.5480},
                        {"lat": 27.5802, "lon": 85.5492},
                        {"lat": 27.5788, "lon": 85.5503},
                    ],
                },
                # Route 4: Ratnapark-Panauti (reverse of Route 3)
                {
                    "route_id": "route_4",
                    "route_name": "Ratnapark-Panauti",
                    "coordinates": [
                        {"lat": 27.5788, "lon": 85.5503},
                        {"lat": 27.5802, "lon": 85.5492},
                        {"lat": 27.5815, "lon": 85.5480},
                        {"lat": 27.5827, "lon": 85.5473},
                        {"lat": 27.5841, "lon": 85.5460},
                        {"lat": 27.5858, "lon": 85.5450},
                        {"lat": 27.5872, "lon": 85.5442},
                        {"lat": 27.5890, "lon": 85.5433},
                        {"lat": 27.5915, "lon": 85.5420},
                        {"lat": 27.5938, "lon": 85.5405},
                        {"lat": 27.5950, "lon": 85.5391},
                        {"lat": 27.5965, "lon": 85.5377},
                        {"lat": 27.5987, "lon": 85.5364},
                    ],
                },
            ]

            # Insert demo data into the RouteInfo table
            for route in route_data:
                db_route = RouteInfo(**route)
                session.add(db_route)

            # Commit the changes
            await session.commit()

async def populate_users_if_empty():
    async for session in get_db():
        result = await session.execute(select(User))
        existing_users = result.scalars().all()

        if not existing_users:
            users_data = []
            for i in range(1, 5):
                for j in range(1, 6):
                    username = f"user_{i}_{j}"
                    bus_number = f"bus_{i}_{j}"
                    route_id = i
                    password = "password123"
                    password_hash = hashlib.sha256(password.encode()).hexdigest()

                    users_data.append({
                        "username": username,
                        "bus_number": bus_number,
                        "route_id": str(route_id),
                        "password_hash": password_hash,
                        "status": True
                    })

            for user in users_data:
                db_user = User(**user)
                session.add(db_user)

            await session.commit()

# Register the function to run on application startup
@app.on_event("startup")
async def startup():
    # Create tables in the database if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Populate route data if no routes are present
    await populate_routes_if_empty()
    await populate_users_if_empty()

# Render the map page (mainpage.html) when accessing the root URL
@app.get("/")
async def render_map(request: Request):
    return templates.TemplateResponse("mainpage.html", {"request": request})

@app.get("/create_bus")
async def render_cb(request: Request):
    return templates.TemplateResponse("bus_driver.html", {"request": request})
    
    
#models.py
# models.py
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from base import Base  # Import Base from base.py

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    bus_number = Column(String, unique=True, index=True)
    route_id = Column(String)
    password_hash = Column(String)
    status = Column(Boolean, default=True)
    
    bus_info = relationship("BusLocation", back_populates="bus", uselist=False)

class BusLocation(Base):
    __tablename__ = "bus_locations"
    
    id = Column(Integer, primary_key=True, index=True)
    bus_number = Column(String, ForeignKey("users.bus_number"), unique=True, nullable=False)
    current_lat = Column(Float, nullable=False)
    current_lon = Column(Float, nullable=False)
    last_5_sec_locations = Column(JSON, default=[])
    last_15_sec_location = Column(JSON, nullable=True)
    last_25_sec_location = Column(JSON, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    bus = relationship("User", back_populates="bus_info")

class RouteInfo(Base):
    __tablename__ = "route_info"
    
    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(String, unique=True, nullable=False)
    route_name = Column(String, nullable=False)
    coordinates = Column(JSON, default=[])
    
    def add_coordinates(self, new_coords):
        self.coordinates.extend(new_coords)

# routes.py
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from crud import create_bus_driver, update_bus_location, create_route_data
from schemas import UserCreate, UserResponse, LocationUpdate, RouteDataSubmit
from database import get_db
from models import User, BusLocation, RouteInfo
from geopy.distance import geodesic
import json

router = APIRouter()

# Create new bus driver
@router.post("/submit_route_data/")
async def submit_route_data(route_data: RouteDataSubmit, db: AsyncSession = Depends(get_db)):
    # Check if the route exists using route_id
    result = await db.execute(select(RouteInfo).filter(RouteInfo.route_id == route_data.route_id))
    route = result.scalar_one_or_none()

    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    # Process the route data (store or handle it)
    processed_route_data = await create_route_data(db, route_data)

    return {
        "message": "Route data successfully received and processed",
        "route_data": processed_route_data
    }

@router.post("/create_bus_driver/", response_model=UserResponse)
async def create_bus_driver_handler(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.bus_number == user.bus_number))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="Bus number already registered")
    
    new_user = await create_bus_driver(db, user)
    return new_user

# WebSocket for live location updates for bus drivers
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                location_data = json.loads(data)
                location = LocationUpdate(**location_data)
                await update_bus_location(db, location)
                await websocket.send_text(f"Location updated for bus {location.bus_number}")
            except Exception as e:
                await websocket.send_text(f"Error: {str(e)}")
    except WebSocketDisconnect:
        print("User disconnected from bus location WebSocket")

# Route data submission (non-authenticated, for route users)
@router.post("/submit_route_data/")
async def submit_route_data_handler(route_data: RouteDataSubmit, db: AsyncSession = Depends(get_db)):
    try:
        route_info = await create_route_data(db, route_data)
        return {"message": "Route data submitted successfully", "route_info": route_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting route data: {str(e)}")

# WebSocket for live route data updates (non-authenticated, for route users)
@router.websocket("/ws/route")
async def websocket_route_endpoint(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                route_data = json.loads(data)
                route_data_obj = RouteDataSubmit(**route_data)

                # Check if the route already exists
                result = await db.execute(select(RouteInfo).filter(RouteInfo.route_id == route_data_obj.route_id))
                existing_route = result.scalar_one_or_none()

                if existing_route:
                    existing_route.current_lat = route_data_obj.current_lat
                    existing_route.current_lon = route_data_obj.current_lon
                    existing_route.final_lat = route_data_obj.final_lat
                    existing_route.final_lon = route_data_obj.final_lon
                    existing_route.final_destination = route_data_obj.final_destination
                    existing_route.timestamp = route_data_obj.timestamp
                else:
                    new_route = RouteInfo(
                        route_id=route_data_obj.route_id,
                        current_lat=route_data_obj.current_lat,
                        current_lon=route_data_obj.current_lon,
                        final_lat=route_data_obj.final_lat,
                        final_lon=route_data_obj.final_lon,
                        final_destination=route_data_obj.final_destination,
                        timestamp=route_data_obj.timestamp
                    )
                    db.add(new_route)
                
                await db.commit()
                await websocket.send_text(f"Route data for route {route_data_obj.route_id} updated successfully!")
            except Exception as e:
                await websocket.send_text(f"Error: {str(e)}")
    except WebSocketDisconnect:
        print("User disconnected from route WebSocket")

# New API for route information: buses in each route, route name, total distance of the route
@router.get("/route_info/{route_id}/")
async def get_route_info(route_id: int, db: AsyncSession = Depends(get_db)):
    try:
        # Get route info for the given route_id
        route_info = await db.execute(select(RouteInfo).filter(RouteInfo.route_id == route_id))
        route = route_info.scalar_one_or_none()

        if not route:
            raise HTTPException(status_code=404, detail="Route not found")

        # Calculate total distance for the route
        route_coordinates = route.coordinates
        total_distance = 0

        if route_coordinates and len(route_coordinates) > 1:
            for i in range(1, len(route_coordinates)):
                start_point = route_coordinates[i - 1]
                end_point = route_coordinates[i]
                total_distance += geodesic((start_point["lat"], start_point["lon"]), (end_point["lat"], end_point["lon"])).kilometers

        # Get the number of buses running this route (number of users linked to the route)
        buses_on_route = await db.execute(select(User).filter(User.route_id == route_id))
        bus_count = len(buses_on_route.scalars().all())

        return {
            "route_name": route.route_name,
            "total_buses_on_route": bus_count,
            "total_distance_km": total_distance
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching route info: {str(e)}")

@router.get("/route_path/{route_id}/")
async def get_route_path(route_id: str, db: AsyncSession = Depends(get_db)):
    print(f"route is {route_id}")
    try:
        # Fetch route info for the given route_id
        route_info = await db.execute(select(RouteInfo).filter(RouteInfo.route_id == route_id))
        route = route_info.scalar_one_or_none()

        if not route:
            raise HTTPException(status_code=404, detail="Route not found")

        # Ensure route.coordinates is a list of dictionaries
        if route.coordinates and isinstance(route.coordinates, str):
            try:
                coordinates = json.loads(route.coordinates)
                if not isinstance(coordinates, list):
                    raise ValueError("Coordinates must be a list")
                for coord in coordinates:
                    if not isinstance(coord, dict) or "lat" not in coord or "lon" not in coord:
                        raise ValueError("Each coordinate must be a dict with 'lat' and 'lon'")
            except (json.JSONDecodeError, ValueError) as e:
                raise HTTPException(status_code=500, detail=f"Invalid coordinate data: {e}")

            return {
                "route_coordinates": json.loads(route.coordinates),
            }
        elif route.coordinates and isinstance(route.coordinates, list):
            return {
                "route_coordinates": route.coordinates
            }
        else:
            return {
                "route_coordinates": []
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching route path data: {str(e)}")


# schemas.py

from pydantic import BaseModel
from typing import Optional

# Pydantic model for creating a bus driver
class UserCreate(BaseModel):
    username: str
    bus_number: str
    route_id: str
    password: str

# Pydantic model for returning user info after creation
class UserResponse(BaseModel):
    id: int
    username: str
    bus_number: str
    route_id: str
    status: bool
    
    class Config:
        orm_mode = True

# Pydantic model for location updates
class LocationUpdate(BaseModel):
    bus_number: str
    lat: float
    lon: float

# Pydantic model for route data submission
class RouteDataSubmit(BaseModel):
    route_id: str
    current_lat: float
    current_lon: float
    final_lat: Optional[float] = None
    final_lon: Optional[float] = None
    final_destination: Optional[str] = None
