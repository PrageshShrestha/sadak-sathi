# models.py
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, Time, JSON
from sqlalchemy.orm import relationship
from datetime import datetime,time
from database import Base  # Import Base from base.py
from math import radians, sin, cos, sqrt, atan2


class User_authorized(Base):
    __tablename__ = "user_authorized"
    
    id = Column(Integer, primary_key=True, index=True)
    name=Column(String , nullable=False)
    password = Column(String,nullable = False)
    authorized = Column(Boolean, default=False)
   
        
class RouteInfo(Base):
    __tablename__ = "route_info"
    
    route_id = Column(Integer, unique=True,primary_key=True, nullable=False , autoincrement=True)
    route_name = Column(String, nullable=False)#banepa_panauti
    coordinates = Column(String, default=[])#[(lat,lng),(next_lat,lng),....]
    stops = Column(String , default = [])#[(name , lat,lng,stop_time)....]
    added_by = Column(String)
    added_at = Column(Time, default=lambda:datetime.now().time())
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from base import Base  # Import Base from base.py


class Bus_route(Base):
    __tablename__ = "bus_route"
    bus_number = Column(String, primary_key=True, nullable=False)
    password = Column(String , nullable=False)
    route_id = Column(Integer, ForeignKey("route_info.route_id"))
    active = Column(Boolean, default=True)
    bi = relationship("Bus_info", back_populates="br")
class Bus_info(Base):
    __tablename__ = "bus_info"
    bus_number = Column(String, ForeignKey("bus_route.bus_number"), primary_key=True, nullable=False )    
    br = relationship("Bus_route", back_populates="bi")
    route_id = Column(Integer, ForeignKey("route_info.route_id"))
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    speed = Column(Float, nullable=False)
    next_stop = Column(String, nullable=False)
    eta = Column(Float,default = 30 , nullable=False)#number of seconds
    last_updated_eta = Column(Time)
    last_updated = Column(Time, default=lambda : datetime.now().time())    
    route_direction = Column(Boolean, default = False)#false as actual route direction else opposite route
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371000  # Earth radius in meters

        phi1, phi2 = radians(lat1), radians(lat2)
        delta_phi = radians(lat2 - lat1)
        delta_lambda = radians(lon2 - lon1)

        a = sin(delta_phi / 2)**2 + cos(phi1) * cos(phi2) * sin(delta_lambda / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance = R * c  # in meters
        return distance    
    def update_location(self, **kwargs):
        new_lat = kwargs.get('new_lat')
        new_lon = kwargs.get('new_lon')
        eta = kwargs.get('eta') 
        next_stop = kwargs.get('next_stop')
        last_upadated = kwargs.get('last_updated') or self.last_updated
        if new_lat is None or new_lon is None:
            raise ValueError("new_lat and new_lon are required")

        self.speed = self.haversine(self.lat, self.lon, new_lat, new_lon) * 3.6  # m/s to km/h
        self.lat = new_lat
        self.lon = new_lon
        self.eta = eta
        self.next_stop = next_stop
        self.last_updated = datetime.now().time()

        
        
        
        

