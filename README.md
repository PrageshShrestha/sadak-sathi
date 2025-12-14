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
