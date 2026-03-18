# 🏎️ F1 Data API & Analytics Platform

## 📌 Project Overview

This project is a full-stack data-driven web application that provides a RESTful API for Formula 1 data, alongside an interactive frontend dashboard.

The system allows users to explore F1 data including drivers, constructors, circuits, and races, while also supporting advanced features such as authentication, favourites, and admin-controlled data management.

The API is designed following REST principles and supports full CRUD operations for key entities, as well as analytical endpoints for data insights.

---

## 🚀 Key Features

- RESTful API with full CRUD functionality
- JWT-based authentication (user & admin roles)
- User favourites system
- Admin dashboard with protected endpoints
- Analytical endpoints (driver performance, rankings)
- FastAPI backend with automatic validation
- React frontend for interactive user experience

---

## 🏗️ System Architecture

Frontend (React)  
↓  
FastAPI Backend (API Layer)  
↓  
Authentication Layer (JWT)  
↓  
Database (SQL)

This architecture ensures separation of concerns, scalability, and maintainability.

---

## 🧰 Technology Stack

### Backend
- Python (FastAPI)
- SQL Database (SQLite / PostgreSQL)
- JWT Authentication

### Frontend
- React (Vite)
- CSS

### Tools
- Git & GitHub (version control)
- Swagger UI (API testing)
- Postman (optional)

---

## 📦 Installation & Setup

### 1. Clone the repository

git clone https://github.com/YOUR_USERNAME/F1-api.git  
cd F1-api  

---

### 2. Backend Setup

cd backend   (or root folder if backend is there)

python -m venv .venv  
source .venv/bin/activate   (Mac/Linux)  
.venv\Scripts\activate      (Windows)  

pip install -r requirements.txt  

---

### 3. Run Backend

uvicorn app.main:app --reload  

Backend will run at:  
http://127.0.0.1:8000  

Swagger docs:  
http://127.0.0.1:8000/docs  

---

### 4. Frontend Setup

cd frontend  
npm install  
npm run dev  

Frontend will run at:  
http://localhost:5173  

---

## 🔐 Authentication

The system uses JWT-based authentication.

### User
- Register and login via `/auth/login`

### Admin
- Endpoint: `/auth/admin/login`
- Admin can:
  - Create, update, delete data
  - Access protected endpoints

---

## 📡 API Endpoints (Examples)

### Drivers
GET /drivers  
GET /drivers/{slug}  
POST /drivers (admin)  
PATCH /drivers/{slug} (admin)  
DELETE /drivers/{slug} (admin)  

### Constructors
GET /constructors  
POST /constructors (admin)  

### Circuits
GET /circuits  
POST /circuits (admin)  

### Races
GET /races  

### Analytics
GET /analytics/top-drivers  
GET /analytics/constructor-performance  

---

## 🧪 Testing

The API was tested using:
- Swagger UI (FastAPI built-in)
- Manual testing via frontend
- Validation of edge cases (invalid input, unauthorized access)

---

## 📄 API Documentation

Full API documentation is available in:

/docs/API_Documentation.pdf  

---

## 📘 Technical Report

The technical report is included in:

/docs/Technical_Report.pdf  

---

## 🤖 Generative AI Usage

Generative AI tools were used for:
- Debugging and troubleshooting
- Exploring architecture and design decisions
- Improving documentation and structure

All outputs were critically evaluated and adapted before use.

---

## 🔮 Future Improvements

- Cloud deployment (Render / Railway)
- More advanced analytics
- Real-time data integration
- Improved admin features

---

## 👤 Author

Adam Bakeer  
University of Leeds – Computer Science
