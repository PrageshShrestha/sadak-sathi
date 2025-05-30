
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
