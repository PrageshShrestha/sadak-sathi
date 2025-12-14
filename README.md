# Sadak Sathi 🚌🚍

### Real-Time Public Transportation Tracking System 📍

Sadak Sathi is a real-time public transportation monitoring platform designed to track buses, visualize routes, and stream live location data using modern backend and mobile technologies.

The project aims to improve **visibility**, **efficiency**, and **reliability** of public transportation systems through live tracking, intelligent routing, and centralized monitoring.
## 📑 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Repository Structure](#repository-structure)
- [Technology Stack](#technology-stack)
- [Flutter Application](#flutter-application)
- [Getting Started](#getting-started)
- [WebSocket API](#websocket-api)
- [Disclaimer](#disclaimer)
- [Future Work](#future-work)
- [Author](#author)
- [Contributions](#contributions)

---
## 📖 Overview

Sadak Sathi is built as a distributed system consisting of:

- A high-performance asynchronous backend ⚙️
- A cross-platform mobile application 📱
- A real-time communication layer using WebSockets 🔌

Buses continuously transmit GPS coordinates to the backend, which processes location data, computes route intelligence, and broadcasts updates to connected clients in real time.

---
## ✨ Key Features

- 🚌 Real-time bus location tracking
- 🗺️ Interactive route visualization using OpenStreetMap
- ⚡ Low-latency WebSocket-based updates
- 🚏 Nearby bus stop detection
- 🔀 Multiple buses per route with direction handling
- 🔐 Bus-level authentication
- 📊 Administrative monitoring and statistics
- 🏗️ Scalable asynchronous backend architecture

---
## 🏗️ System Architecture
Flutter App 📱 ── WebSocket 🔌 ──▶ FastAPI Backend ⚙️ ──▶ PostgreSQL 🗄️
▲                                 │
└──────── Route & Bus Data ◀──────┘

## 🛠️ Technology Stack

### Backend ⚙️
- FastAPI 🚀
- Async SQLAlchemy 🔄
- PostgreSQL 🗄️
- WebSockets 🔌
- OpenStreetMap (OSM) 🗺️ / Geospatial data 🌍
- Haversine distance calculations 📏

### Mobile Application 📱
- Flutter 🐦
- flutter_map (for OpenStreetMap integration) 🗺️
- WebSocket client 🔌
- Location services 📍

---
## 📱 Flutter Application

The Flutter client provides:

- 🚌 Live bus locations displayed on OpenStreetMap
- 🛣️ Route and bus stop plotting
- 🎯 Automatic map centering on the active bus
- 🔌 Persistent single WebSocket connection
- ⚡ Instant UI updates without polling
- ⚙️ Settings for route and bus configuration

---

## 🚀 Getting Started
## 📂 Repository Structure

```yaml
sadak-sathi:
  backend:
    app:
      models.py: Database models 🗄️
      websocket: WebSocket handlers 🔌
      routes: API routes 🛣️
      database.py: Database connection 🔗
    main.py: Application entry point 🚀
  flutter_app:
    lib:
      screens: UI screens 🖥️
      services: WebSocket & API services 🔌
      widgets: Reusable UI components 🧩
    pubspec.yaml: Flutter dependencies 📦
  docs:
    - diagrams 📊
    - notes 📝
  README.md: Project documentation 📄

```
### Backend Setup ⚙️

```bash
git clone https://github.com/PrageshShrestha/sadak-sathi.git
cd sadak-sathi/backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the development server
uvicorn main:app --reload
cd ../flutter_app
flutter pub get
flutter run
```
## 🔌 WebSocket API

### Endpoint

### Client → Server Payload
```json
{
  "route_id": 1,
  "lat": 27.7172,
  "lon": 85.3240
}
{
  "route_coordinates": [],
  "stops": [],
  "other_buses": [],
  "bus_location": {},
  "route_name": "Route A"
}

```
## ⚠️ Disclaimer

This project is under active development and intended for:

- Academic projects 🎓
- Research and experimentation 🔬
- Smart transportation system prototyping 🛠️

It is **not production-ready** without additional testing, security hardening, and operational safeguards.

---
## 🔮 Future Work

- ⏱️ Improved ETA prediction models
- 📱 Passenger-facing mobile application
- 🚦 Traffic-aware routing
- 📈 Analytics and reporting dashboard
- 👥 Role-based access control
- ☁️ Containerized and cloud deployment

---
## 👤 Author

**Pragesh Shrestha**  
GitHub: [https://github.com/PrageshShrestha](https://github.com/PrageshShrestha)

---
```

