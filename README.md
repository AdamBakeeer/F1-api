# 🏎️ F1 Data API & Analytics Platform

## 📌 Project Overview

This project is a full-stack web application that provides a RESTful API for Formula 1 data, alongside an interactive frontend dashboard.

The system allows users to explore F1 data including drivers, constructors, circuits, and races. It also includes authentication and admin-controlled data management, enabling secure creation, updating, and deletion of data.

The API follows RESTful design principles and supports CRUD operations for core entities, as well as analytical endpoints to provide additional insights.

---

## 🚀 Key Features

- RESTful API with CRUD operations for drivers, constructors, and circuits
- JWT-based authentication for secure admin access
- Protected admin endpoints for data management
- Analytical endpoints (e.g. top drivers, constructor performance)
- FastAPI backend with automatic validation and Swagger documentation
- React frontend for interactive data exploration

---

## 🏗️ System Architecture

Frontend (React)  
↓  
FastAPI Backend (API Layer)  
↓  
JWT Authentication  
↓  
SQLite Database  

The system follows a layered architecture to ensure separation of concerns and maintainability.

---

## 🧰 Technology Stack

### Backend
- Python (FastAPI)
- PostgreSQL
- JWT Authentication

### Frontend
- React (Vite)
- CSS

### Tools
- Git & GitHub (version control)
- Swagger UI (API documentation and testing)

---

## 📦 Installation & Setup

### 1. Clone the repository

git clone https://github.com/adambakeeer/F1-api.git  
cd F1-api  

---

### 2. Backend Setup

python -m venv .venv  
source .venv/bin/activate      # Mac/Linux  
.venv\Scripts\activate         # Windows  

pip install -r requirements.txt  

---

### 3. Run Backend

uvicorn app.main:app --reload  

Backend runs at:  
http://127.0.0.1:8000  

Swagger documentation:  
http://127.0.0.1:8000/docs  

---

### 4. Frontend Setup

cd frontend  
npm install  
npm run dev  

Frontend runs at:  
http://localhost:5173  

---

## 🔐 Authentication

The system uses JWT-based authentication.

### Admin Login  
POST /auth/admin/login  

Authenticated admin users can:  
- Create data  
- Update data  
- Delete data  

All protected endpoints require a valid Bearer token.

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
- Swagger UI (interactive endpoint testing)  
- Manual testing through the frontend interface  
- Validation of edge cases (invalid input, authentication errors)  

---

## 📄 API Documentation

Full API documentation is provided in:  

/docs/API_Documentation.pdf  

---

## 📘 Technical Report

The technical report is provided in:  

/docs/Technical_Report.pdf  

---

## 🚀 Deployment

The backend API is deployed using Render, making it accessible via a public URL.

This allows real-world interaction with the API, including authentication, data retrieval, and admin operations, beyond a local development environment.

---

## 🔮 Future Improvements

- Performance optimisation (e.g. caching)  
- More advanced analytical endpoints  
- Enhanced frontend user experience  
- Expanded role-based access control  

---

## 👤 Author

Adam Bakeer  
University of Leeds – Computer Science
