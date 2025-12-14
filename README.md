# Sadak Sathi 🚌  
*A Real-Time Public Transportation Tracking System*

**Sadak Sathi** is a real-time public transportation monitoring system designed to track buses, visualize routes, and stream live location data using modern backend and mobile technologies.

The project focuses on improving **transparency**, **efficiency**, and **reliability** of public transport through live tracking, route intelligence, and centralized monitoring.

---

## 📌 Project Overview

Sadak Sathi is built as a **distributed real-time system** consisting of a backend API and a mobile client.

### Core Technologies
- **FastAPI** — High-performance asynchronous backend
- **Flutter** — Cross-platform mobile application
- **WebSockets** — Real-time bidirectional communication
- **PostgreSQL** — Persistent relational storage
- **OpenStreetMap (OSM)** — Map rendering and geospatial data

Buses continuously transmit GPS coordinates to the backend, which processes and broadcasts structured route and bus data back to connected clients in real time.

---

## 🧠 Key Features

- 🚌 Live bus location tracking
- 🗺️ Route visualization using OpenStreetMap
- 🔁 Real-time updates via WebSockets
- 📍 Nearby bus stop detection and display
- 🚏 Support for multiple buses per route with direction
- 🔐 Authentication using bus number credentials
- 📊 Admin panel with summarized statistics
- ⚡ Fully asynchronous backend for high concurrency

---

## 🏗️ System Architecture

Flutter App ── WebSocket ──▶ FastAPI Backend ──▶ PostgreSQL
▲ │
└──────── Route & Bus Data ◀────────┘

yaml
Copy code

---

## 📁 Repository Structure

sadak-sathi/
├── backend/
│ ├── app/
│ │ ├── models.py
│ │ ├── websocket/
│ │ ├── routes/
│ │ └── database.py
│ └── main.py
│
├── flutter_app/
│ ├── lib/
│ │ ├── screens/
│ │ ├── services/
│ │ └── widgets/
│ └── pubspec.yaml
│
├── docs/
│ └── diagrams, notes
│
└── README.md

yaml
Copy code

> ⚠️ The structure may evolve as new features are added.

---

## ⚙️ Backend Technology Stack

- FastAPI
- Async SQLAlchemy
- PostgreSQL
- WebSockets
- OpenStreetMap / Geospatial data
- Haversine distance calculations for speed & ETA

---

## 📱 Flutter Application Features

- Live bus tracking on OpenStreetMap
- Route and bus stop plotting
- Automatic map centering on active bus
- Single persistent WebSocket connection
- Settings for route and bus configuration
- Instant UI updates without polling

---

## 🚀 Getting Started

### Backend Setup

```bash
git clone https://github.com/PrageshShrestha/sadak-sathi.git
cd sadak-sathi/backend
Create and activate a virtual environment:

bash
Copy code
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
Run the development server:

bash
Copy code
uvicorn main:app --reload
Flutter App Setup
bash
Copy code
cd flutter_app
flutter pub get






You said:
i meant in readme.md even for those heading or yaml


ChatGPT said:
Got it 👍
You want a single, polished README.md where even the headings, sections, structure, and code/YAML/JSON blocks are clean, consistent, and professional—no mixed styles, no rough edges.

Below is a fully refined, publication-quality README.md (raw Markdown).
You can paste this as-is.

markdown
Copy code
# Sadak Sathi 🚌
### Real-Time Public Transportation Tracking System

Sadak Sathi is a real-time public transportation monitoring platform designed to track buses, visualize routes, and stream live location data using modern backend and mobile technologies.

The project aims to improve **visibility**, **efficiency**, and **reliability** of public transportation systems through live tracking, intelligent routing, and centralized monitoring.

---

## Table of Contents
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

## Overview

Sadak Sathi is built as a distributed system consisting of:

- A high-performance asynchronous backend
- A cross-platform mobile application
- A real-time communication layer using WebSockets

Buses continuously transmit GPS coordinates to the backend, which processes location data, computes route intelligence, and broadcasts updates to connected clients in real time.

---

## Key Features

- Real-time bus location tracking
- Interactive route visualization using OpenStreetMap
- Low-latency WebSocket-based updates
- Nearby bus stop detection
- Multiple buses per route with direction handling
- Bus-level authentication
- Administrative monitoring and statistics
- Scalable asynchronous backend architecture

---

## System Architecture

```text
Flutter App  ── WebSocket ──▶ FastAPI Backend ──▶ PostgreSQL
     ▲                                   │
     └──────── Route & Bus Data ◀────────┘
Repository Structure
yaml
Copy code
sadak-sathi:
  backend:
    app:
      models.py: Database models
      websocket: WebSocket handlers
      routes: API routes
      database.py: Database connection
    main.py: Application entry point

  flutter_app:
    lib:
      screens: UI screens
      services: WebSocket & API services
      widgets: Reusable UI components
    pubspec.yaml: Flutter dependencies

  docs:
    - diagrams
    - notes

  README.md: Project documentation
Technology Stack
Backend
FastAPI

Async SQLAlchemy

PostgreSQL

WebSockets

OpenStreetMap (OSM)

Haversine distance calculations

Mobile Application
Flutter

flutter_map

WebSocket client

Location services

Flutter Application
The Flutter client:

Displays live bus locations on OSM

Plots routes and bus stops

Maintains a persistent WebSocket connection

Updates the UI instantly without polling

Allows route and bus configuration via settings

Getting Started
Backend Setup
bash
Copy code
git clone https://github.com/PrageshShrestha/sadak-sathi.git
cd sadak-sathi/backend
Create a virtual environment and install dependencies:

bash
Copy code
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
Run the development server:

bash
Copy code
uvicorn main:app --reload
Flutter Setup
bash
Copy code
cd flutter_app
flutter pub get
flutter run
Ensure location permissions are enabled on the device or emulator.

WebSocket API
Endpoint
text
Copy code
/ws/bus/{bus_number}
Client → Server Payload
json
Copy code
{
  "route_id": 1,
  "lat": 27.7172,
  "lon": 85.3240
}
Server → Client Response
json
Copy code
{
  "route_coordinates": [],
  "stops": [],
  "other_buses": [],
  "bus_location": {},
  "route_name": "Route A"
}
Disclaimer
This project is under active development and intended for:

Academic projects

Research and experimentation

Smart transportation system prototyping

It is not production-ready without additional testing, security hardening, and operational safeguards.

Future Work
Improved ETA prediction models

Passenger-facing mobile application

Traffic-aware routing

Analytics and reporting dashboard

Role-based access control

Containerized and cloud deployment

Author
Pragesh Shrestha
GitHub: https://github.com/PrageshShrestha
