from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from models import User, BusLocation, RouteInfo
from schemas import UserCreate, LocationUpdate, RouteDataSubmit
from typing import List


async def create_bus_driver(db: AsyncSession, user: UserCreate) -> User:
    """Creates a new bus driver in the database."""
    db_user = User(
        username=user.username,
        bus_number=user.bus_number,
        password_hash=user.password_hash,
        route_id=user.route_id,
        status=user.status
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def update_bus_location(db: AsyncSession, location: LocationUpdate) -> BusLocation:
    """Updates the bus location in the database."""
    db_location = BusLocation(
        bus_number=location.bus_number,
        current_lat=location.lat,
        current_lon=location.lon,
    )
    db.add(db_location)
    await db.commit()
    await db.refresh(db_location)
    return db_location

async def create_route_data(db: AsyncSession, route_data: RouteDataSubmit) -> RouteInfo:
    """Creates or updates route data in the database."""
    result = await db.execute(select(RouteInfo).filter(RouteInfo.route_id == route_data.route_id))
    existing_route = result.scalar_one_or_none()

    if existing_route:
        existing_route.current_lat = route_data.current_lat
        existing_route.current_lon = route_data.current_lon
        existing_route.final_lat = route_data.final_lat
        existing_route.final_lon = route_data.final_lon
        existing_route.final_destination = route_data.final_destination
        existing_route.timestamp = route_data.timestamp
        await db.commit()
        await db.refresh(existing_route)
        return existing_route
    else:
        db_route = RouteInfo(
            route_id=route_data.route_id,
            current_lat=route_data.current_lat,
            current_lon=route_data.current_lon,
            final_lat=route_data.final_lat,
            final_lon=route_data.final_lon,
            final_destination=route_data.final_destination,
            timestamp=route_data.timestamp
        )
        db.add(db_route)
        await db.commit()
        await db.refresh(db_route)
        return db_route

async def get_route_coordinates(db: AsyncSession, route_id: str) -> List[dict]:
    """Retrieves route coordinates from the database."""
    result = await db.execute(select(RouteInfo).filter(RouteInfo.route_id == route_id))
    route = result.scalar_one_or_none()
    
    if route:
        return route.coordinates
    else:
        return []

async def get_route_info(db: AsyncSession, route_id: int) -> dict:
    """Retrieves route information including buses and route details."""
    result = await db.execute(
        select(RouteInfo).options(selectinload(RouteInfo.users)).filter(RouteInfo.id == route_id)
    )
    route = result.scalar_one_or_none()

    if route:
        bus_numbers = [user.bus_number for user in route.users]
        total_distance = 0.0  # Placeholder, calculate if needed

        return {
            "route_id": route.route_id,
            "route_name": route.route_name,
            "bus_numbers": bus_numbers,
            "total_distance": total_distance,
        }
    else:
        return None



async def get_bus_locations_on_route(db: AsyncSession, route_id: str) -> List[dict]:
    """Retrieves bus locations for a given route."""
    result = await db.execute(select(User).filter(User.route_id == route_id))
    users = result.scalars().all()

    bus_locations = []
    for user in users:
        location_result = await db.execute(
            select(BusLocation)
            .filter(BusLocation.bus_number == user.bus_number)
            .order_by(BusLocation.last_updated.desc()) #Corrected to last_updated
            .limit(1)
        )
        location = location_result.scalar_one_or_none()
        if location:
            bus_locations.append({
                "bus_number": location.bus_number,
                "current_lat": location.current_lat,
                "current_lon": location.current_lon,
            })
    return bus_locations