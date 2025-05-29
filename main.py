<<<<<<< HEAD
from fastapi import FastAPI, Depends , WebSocket , HTTPException
from typing import List 
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from fastapi.templating import Jinja2Templates 
from fastapi import * 
from database import async_session , init_db 
from typing import AsyncGenerator
from models import * 
from schemas import *
import json
import asyncio
from fastapi.staticfiles import StaticFiles
from sqlalchemy import insert, select ,text
import ast
from config import DATABASE_URL



class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.routes: List[RouteInfo] = []  # Store route information

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)
manager = ConnectionManager()
@asynccontextmanager 
async def lifespan(app:FastAPI):
    await init_db()
    yield
     
app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")


async def get_session()-> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
from math import radians, sin, cos, sqrt, atan2
async def get_route_infos(route_name:str , db:AsyncSession = Depends(get_session)):
    result = await db.execute(select(RouteInfo).filter(RouteInfo.route_name == str(route_name)))
    route_id = result.route_id
    route_bus = await db.execute(select(Bus_route).filter(Bus_route.route_id == route_id and Bus_route.active == True))
    route_bus = route_bus.scalars().all()
    bus_list = []
    for i in route_bus:
        bus_list.append((i.bus_number , i.bi.lat , i.bi.lon , i.bi.stop , i.bi.next_stop , i.bi.eta))
    return {
        "route_coordinates":result.coordinates,
        "route_stops":result.stops,
        "bus_list":bus_list,
    }

async def submit_route_data_handler(route_data: RouteDataSubmit, db: AsyncSession = Depends(get_session)):
    
    result = await db.execute(select(RouteInfo).filter(RouteInfo.route_id == route_data.route_id))
    route = result.scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    stops = route.stops.tolist()
    stops_list = []
    
    curr_lat = route_data.lat 
    curr_lon = route_data.lon 
    temp_list = []
    for stop ,lat,lon,stop_time in stops:
        stops_list.append(str(stop))
        dist = haversine(curr_lat ,curr_lon , lat,lon)
        temp_list.append((dist , stop))
    temp_list.sort(key=lambda x: x[0])
    stop1 = str(temp_list[0][1])
    stop2 = str(temp_list[1][1])
    
    index_stop1 = stops_list.index(stop1)
    index_stop2 = stops_list.index(stop2)
    
    bus_info = await db.execute(select(Bus_info).filter(Bus_info.bus_number == route_data.bus_number))
    next_stop = ""
    if bus_info.route_direction:
        if index_stop1 < index_stop2:
            next_stop = index_stop2 
        else:
            next_stop = index_stop1
    else:
        if index_stop1 < index_stop2:
            next_stop = index_stop2
        else:
            next_stop = index_stop1
    next_stop_time = stops[next_stop][3]
    last_time = bus_info.last_updated
    route_dict = {
        "route_id": route.route_id,
        "lat": route_data.lat,
        "lon": route_data.lon,
        "next_stop": next_stop,

        "last_time": last_time,
    }
    eta = eta_calc(**route_dict)
    bus_info.update_location(
        new_lat=route_data.lat,
        new_lon=route_data.lon,
        eta=eta,
        next_stop=next_stop,
    )
    db.commit()

    return {"message": "Route data successfully received and processed", "route_data": processed_route_data}
async def eta_calc(**route_data):
    # Extract the route data
    route_id = route_data["route_id"]
    lat = route_data["lat"]
    lon = route_data["lon"]
    next_stop = route_data["next_stop"]
    last_time = route_data["last_time"]
    return 30
    
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters

    phi1, phi2 = radians(lat1), radians(lat2)
    delta_phi = radians(lat2 - lat1)
    delta_lambda = radians(lon2 - lon1)

    a = sin(delta_phi / 2)**2 + cos(phi1) * cos(phi2) * sin(delta_lambda / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c  # in meters
    return distance
@app.get("/add_bus_page")
async def add_bus_page(request:Request , db:AsyncSession = Depends(get_session)):
    print("add bus page")
    stmt = select(RouteInfo)
    result =await db.execute(stmt)
    print(result)
    if result is None:
        print("No routes found")
    try:
        data = result.scalars().all()
    
        route_list = [(route.route_name , route.route_id) for route in data]
        return templates.TemplateResponse("bus_driver.html", {"request": request , "route_list": route_list})
    except Exception as e:
        print(f"Error fetching routes: {e}")
        return templates.TemplateResponse("bus_driver.html", {"request": request})
@app.post("/add_bus")
async def add_bus(data:bus_add , db:AsyncSession = Depends(get_session)):
    name = data.name
    password = data.password
    bus_number = data.bus_number
    route_id = data.route_id
    password_name = data.password_name
    try:
        sel = await db.execute(select(User_authorized).filter(User_authorized.name == name))
        user  = sel.scalars().all()
        user = user[0] if user else None
        print(name)
        print(user.authorized , user.password)
        print(password_name)
        if user.authorized == True and user.password == password_name:
            bus_route = Bus_route(bus_number=bus_number, route_id=int(route_id), password=password)
            db.add(bus_route)
            await db.commit()
            print(f"Bus {bus_number} added to route {route_id}")
            return {"details": f"Bus added successfully {bus_number}"}
        else:
            print(f"User {name} not authorized to add bus")
            return {"details": "User not authorized to add bus"}
    except Exception as e:
        print(f"Error adding bus: {e}")
        return {"details": "Error adding bus, please check the input data"}
@app.get("/")
async def home(request:Request , db:AsyncSession = Depends(get_session)):
    try:
        sel = await db.execute(text("SELECT * FROM user_authorized"))
        sel = sel.scalars().all()
        
    except Exception as e:
        print(f"Error fetching users: {e}")
        sel = []
    print(sel)
    if len(sel)==0:
    
        sel = User_authorized(name="Pragesh", password="12345678", authorized=True)
        db.add(sel)
        await db.commit()
        print("new added")
    return templates.TemplateResponse("index.html", {"request": request})
@app.get("/ask_location")
def ask_location(request:Request):
    return templates.TemplateResponse("ask_location.html", {"request": request})
@app.post("/send-location")
async def receive_location(location: UserBase):
    print("inside location")
    print(location)
    print(f"Received location: {location.curr_lat}, {location.curr_lon}")
    # Do something with data (save, process, etc.)
    return {"message": "Location received", "your_location": location}
@app.get("/add_route")
async def add_location(request:Request):
    return templates.TemplateResponse("add_route.html" , {"request": request})
import json

@app.post("/add-route")
async def add_route(route: Route , db:AsyncSession = Depends(get_session)):
    print("we here")
    try:
        # Expecting JSON arrays, so use json.loads
        coords_list = route.coordinates
        stops_list = route.stops
        route_name = route.routeName
        name = route.name
        password = route.password
        sel = await db.execute(select(User_authorized).filter(User_authorized.name == name))
        user  = sel.scalars().all()
        user = user[0] if user else None
        if user.authorized == True and user.password == password:
            
            to_save = RouteInfo(
                route_name=route_name , 
                coordinates=coords_list,
                stops=stops_list,
                added_by=name)
            
            db.add(to_save)
            await db.commit()
            return {"details": f"Route added successfully {route_name}"}
        else:
            return {"details": "User not authorized to add route"}
    except Exception as e:
        print(route)
        print(f"Error: {e}")
        return {"details": "Invalid format for coordinates or stops"}







@app.websocket("ws/{route_name}")
async def ask_server(websocket:WebSocket , route_name:str):
    await websocket.accept()
    
    try:
        while True:
            
            
            some_infos = await get_route_infos(route_name)
            # Example: send a dictionary back to the user
            response_data = {"status": "success", "echo": some_infos}
            await websocket.send_text(json.dumps(response_data))
            await asyncio.sleep(.5)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast("disconnected for user \n")
@app.websocket("ws/submit_route_data/")
async def submit_route(websocket:WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            data = data
            done = await submit_route_data_handler(data)
            await websocket.send_text(json.dumps({"status": "done", "data": done}))
            await asyncio.sleep(.5)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast("disconnected \n")
from fastapi import Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import init_db as get_session
from models import User_authorized, RouteInfo, Bus_info
templates = Jinja2Templates(directory="templates")

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: AsyncSession = Depends(get_session)):
    users = (await db.execute(select(User_authorized))).scalars().all()
    routes = (await db.execute(select(RouteInfo))).scalars().all()
    buses = (await db.execute(select(Bus_info))).scalars().all()
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "users": users,
        "routes": routes,
        "buses": buses
    })

@app.post("/update-user")
async def update_user(user_id: int = Form(...), field: str = Form(...), value: str = Form(...), db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(User_authorized).filter(User_authorized.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return {"details": "User not found"}
    if field == "authorized":
        value = value.lower() == "true"
    setattr(user, field, value)
    await db.commit()
    return {"details": f"User {field} updated!"}

@app.post("/update-route")
async def update_route(route_id: int = Form(...), field: str = Form(...), value: str = Form(...), db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(RouteInfo).filter(RouteInfo.route_id == route_id))
    route = result.scalar_one_or_none()
    if not route:
        return {"details": "Route not found"}
    setattr(route, field, value)
    await db.commit()
    return {"details": f"Route {field} updated!"}

@app.post("/update-bus")
async def update_bus(bus_number: str = Form(...), field: str = Form(...), value: str = Form(...), db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Bus_info).filter(Bus_info.bus_number == bus_number))
    bus = result.scalar_one_or_none()
    if not bus:
        return {"details": "Bus not found"}
    if field in ["lat", "lon", "speed", "eta"]:
        value = float(value)
    elif field == "route_direction":
        value = value.lower() == "true"
    setattr(bus, field, value)
    await db.commit()
    return {"details": f"Bus {field} updated!"}
=======
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
#app.mount("/static", StaticFiles(directory="static"), name="static")

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

@app.get("/driver_location")
async def render_driver(request: Request):
    return templates.TemplateResponse("driver_location.html", {"request": request})

@app.get("/login")
async def render_login(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
>>>>>>> 818a14e1226f981c3d9864e53ac84e04fd6561e1
