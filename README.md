# Sheda-Backend

Backend for sheda solution

# **Real Estate Platform Backend(Still under development most fearures are still being worked on)**

This is the backend for a real estate platform built with **FastAPI**. The platform supports different user roles (e.g., clients, agents, agents), property listings, user authentication, and secure transactions.

## **Features**

- **User Authentication & Management**

  - Role-based accounts (Buyer, agent, Agent, etc.)
  - JWT-based authentication
  - Password reset with OTP verification

- **Property Listings**

  - CRUD operations for properties
  - Image uploads for listings
  - Search and filtering

- **Profile Management**

  - Update profile details (with polymorphic handling)
  - Upload profile pictures

- **Security & Performance**
  - Secure password hashing
  - Redis for caching and temporary storage
  - CORS handling

## **Tech Stack**

- **Backend:** FastAPI, Pydantic, SQLAlchemy
- **Database:** PostgreSQL
- **Caching & Session Management:** Redis
- **Authentication:** JWT

## **Installation**

### **Prerequisites**

- Python 3.10+
- PostgreSQL
- Redis

### **Setup**

1. **Clone the repository**

   ```sh
   git clone https://github.com/SpiDher/Sheda-Backend.git
   cd Sheda-Backend
   ```

2. **Create a virtual environment**

   ```sh
   python -m venv .venv
   source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   ```

3. **Install dependencies**

   ```sh
   pip install -r requirements.txt
   ```

4. **Set up environment variables**  
   Create a `.env` file and configure your database, JWT secret, and Redis settings.

5. **View live server @ https://sheda-backend-production.up.railway.app/**

6. **Start the server**
   ```sh
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

# Real Estate Backend API

## Overview
This is the backend system for the real estate application. It handles user authentication, property listings, appointments, contract creation, chat system, and automated contract expiration management.

## Tech Stack
- **FastAPI** (Backend framework)
- **SQLAlchemy** (ORM for database interactions)
- **PostgreSQL** (Database)
- **APScheduler** (Scheduled tasks)
- **Railway** (Deployment platform)


## System Flow

### 1️⃣ **User Roles**
- **Client:** Can browse properties, book appointments, make payments, and chat.
- **Agent:** Lists properties, manages appointments, confirms payments, and engages with clients.

### 2️⃣ **Property Listings**
- Properties belong to agents.
- Can be available for **rent** or **sale**.
- Includes attributes like price, location, type, status, etc.

### 3️⃣ **Appointments**
- Clients book an appointment with an agent for a property.
- The agent confirms or rejects the appointment.

### 4️⃣ **Payment & Contract Flow**
- After an appointment, the client can **Make Payment** or **Cancel**.
- If **Make Payment**, account details are shown.
- Client confirms payment by clicking **"I have made payment"**.
- The agent then **Accepts** or **Declines** the payment.
- If accepted, a contract is created for **rent** or **sale**.

### 5️⃣ **Automated Contract Expiration**
- APScheduler runs a background job **every 24 hours**.
- It checks contracts that have expired.
- It deactivates the contract and marks the property as available.

## API Endpoints

### **Authentication**
- `POST /auth/register` – Register a new user.
- `POST /auth/login` – Login and get an access token.

### **Properties**
- `GET /properties` – List all properties.
- `GET /properties/{id}` – Get property details.
- `POST /properties` – Create a property (**Agent only**).
- `PATCH /properties/{id}` – Update property details (**Agent only**).
- `DELETE /properties/{id}` – Delete a property (**Agent only**).

### **Appointments**
- `POST /appointments` – Client books an appointment.
- `PATCH /appointments/{id}/confirm` – Agent confirms appointment.
- `DELETE /appointments/{id}` – Cancel appointment.

### **Payments & Contracts**
- `POST /contracts/{property_id}` – Create a contract after payment.
- `PATCH /contracts/{id}/confirm-payment` – Agent confirms payment.
- `PATCH /contracts/{id}/expire` – Mark contract as expired (automated).

### **Chat System**
- `POST /chats` – Send a message.
- `GET /chats/{user_id}` – Retrieve chat history.

## Database Models

### **User (BaseUser abstract model)**
- `id` – Primary key.
- `role` – Can be `client` or `agent`.

### **Property**
- `id` – Primary key.
- `agent_id` – Foreign key to `User`.
- `status` – `available`, `sold`, `rented`.

### **Appointment**
- `id` – Primary key.
- `client_id` – Foreign key to `User`.
- `agent_id` – Foreign key to `User`.
- `property_id` – Foreign key to `Property`.

### **Contract**
- `id` – Primary key.
- `property_id` – Foreign key to `Property`.
- `client_id` – Foreign key to `User`.
- `agent_id` – Foreign key to `User`.
- `is_active` – Becomes `False` when expired.

### **Chat**
- `id` – Primary key.
- `sender_id` – Foreign key to `User`.
- `receiver_id` – Foreign key to `User`.
- `message` – Text content.

## Scheduled Jobs (APScheduler)
- Runs **every 24 hours** to check for expired contracts.
- Marks contracts as inactive and updates property availability.

## Deployment
- Hosted on **Render**.
- Uses PostgreSQL for the database.
- APScheduler runs within the FastAPI application.

## Next Steps
- Implement WebSockets for real-time chat.
- Improve payment verification with webhook integration.
- Enhance notification system for user interactions.

---

This README provides a structured view of the backend logic and endpoints, making it easier for the frontend team to integrate effectively.

