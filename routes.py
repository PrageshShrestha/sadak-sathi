from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from schemas import UserCreate, UserResponse, LocationUpdate, RouteDataSubmit
from database import get_db
from models import User, RouteInfo
from auth import get_current_user, authenticate_user, create_access_token
from schemas import BusLogin
import json
from crud import create_bus_driver, update_bus_location, create_route_data, get_route_coordinates, get_route_info, get_bus_locations_on_route

router = APIRouter()



from fastapi import APIRouter

router = APIRouter()


@router.get("/test_route")
async def test_route():
    return {"message": "Router is working!"}

@router.post("/token")
async def login_for_access_token(login_data: BusLogin, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, login_data.bus_number, login_data.password)
    print(user)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect bus_number or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = await create_access_token(user.bus_number)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"bus_number": current_user.bus_number}

@router.post("/create_bus_driver/", response_model=UserResponse)
async def create_bus_driver_handler(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.bus_number == user.bus_number))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="Bus number already registered")
    new_user = await create_bus_driver(db, user)
    return new_user

@router.post("/submit_route_data/")
async def submit_route_data_handler(route_data: RouteDataSubmit, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RouteInfo).filter(RouteInfo.route_id == route_data.route_id))
    route = result.scalar_one_or_none()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    processed_route_data = await create_route_data(db, route_data)
    return {"message": "Route data successfully received and processed", "route_data": processed_route_data}

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                location_data = json.loads(data)
                location = LocationUpdate(**location_data)
                try:
                    await update_bus_location(db, location)
                    await websocket.send_text(f"Location updated for bus {location.bus_number}")
                except Exception as db_error:
                    await websocket.send_text(f"Database Error: {str(db_error)}")
                    print(f"Database error during update_bus_location: {db_error}")
            except json.JSONDecodeError as json_error:
                await websocket.send_text(f"Invalid JSON: {str(json_error)}")
                print(f"JSON decode error: {json_error}")
            except ValueError as validation_error:
                await websocket.send_text(f"Validation Error: {str(validation_error)}")
                print(f"Validation error: {validation_error}")
            except Exception as e:
                await websocket.send_text(f"Error: {str(e)}")
                print(f"General error: {e}")
    except WebSocketDisconnect:
        print("User disconnected from bus location WebSocket")
    except Exception as overall_error:
        print(f"Overall WebSocket error: {overall_error}")
    finally:
        print("WebSocket connection closed.")

@router.websocket("/ws/route")
async def websocket_route_endpoint(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                route_data = json.loads(data)
                route_data_obj = RouteDataSubmit(**route_data)
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

@router.get("/route_info/{route_id}/")
async def get_route_info_handler(route_id: int, db: AsyncSession = Depends(get_db)):
    try:
        route_data = await get_route_info(db, route_id)
        if not route_data:
            raise HTTPException(status_code=404, detail="Route not found")
        return route_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching route info: {str(e)}")
import logging


# Configure logging
logging.basicConfig(level=logging.ERROR)  # Set logging level to ERROR

@router.get("/route_path/{route_id}/")
async def get_route_path_handler(route_id: str, db: AsyncSession = Depends(get_db)):
    try:
        route_coordinates = await get_route_coordinates(db, route_id)
        bus_locations = await get_bus_locations_on_route(db, route_id)
        return {"route_coordinates": route_coordinates, "bus_locations": bus_locations}
    except Exception as e:
        print(e)
        logging.error(f"Error fetching route path data for route_id {route_id}: {e}", exc_info=True)  # Log detailed error
        raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch route path data. Please check server logs.",
        )