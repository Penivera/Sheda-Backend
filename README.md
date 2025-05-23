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
```markdown
## WebSocket for Real-time Chat  

The chat system enables real-time messaging using WebSockets. Below is how to interact with it.  

### **WebSocket Endpoint**  

```
ws://https://sheda-backend-production.up.railway.app/chat/{user_id}
```

### **Authentication & Connection**  

- The `{user_id}` should be replaced with the authenticated user's ID.  
- Clients must establish a WebSocket connection to send and receive messages in real time.  

### **Message Format**  

Messages sent to the WebSocket should follow this **JSON format**:  

```json
{
  "sender_id": 1,
  "receiver_id": 2,
  "message": "Hello!"
}
```

### **Receiving Messages**  

Incoming messages from the WebSocket are structured as:  

```json
{
  "sender_id": 1,
  "message": "Hello!"
}
```

### **Chat History Endpoint**  

To retrieve past messages, make a **GET** request to:  

```
GET https://sheda-backend-production.up.railway.app/chat-history
```

#### **Response Format**  

```json
[
  {
    "sender_id": 1,
    "receiver_id": 2,
    "message": "Hello!",
    "timestamp": "2025-03-17T12:34:56Z"
  }
]
```

### **Disconnection Handling**  

When a user disconnects, their WebSocket session is removed from active connections, ensuring clean resource management.  
```
## Deployment
- Hosted on **Railway**.
- Uses PostgreSQL for the database.
- APScheduler runs within the FastAPI application.

## Next Steps
- Implement WebSockets for real-time chat.
- Improve payment verification with webhook integration.
- Enhance notification system for user interactions.



---

## 🔐 Admin Role and Permissions

### Overview

The system supports a distinct `admin` role. This role provides elevated privileges across the platform and is granted through the `role` field on the user object.

* `role` values: `"user"` (default), `"admin"`
* Admins may have associated accounts (e.g., buyer/seller), but their elevated privileges are determined by the `role` field, not the account type.

### 🔧 Promoting a User to Admin

Any registered user can be granted admin privileges by directly updating their `role` in the database:

```sql
UPDATE users SET role = 'admin' WHERE id = '<user_id>';
```

> ⚠️ This does **not** change other attributes. Admins will retain any existing buyer/seller accounts unless explicitly handled.

After this update:

* Tokens issued to that user will include the `"admin"` scope.
* The user will be able to access admin-only routes if they are active.

---

### Token Scopes

Tokens issued to users now include a `scopes` claim. For admin users, this will include the `"admin"` scope.

Example token payload:

```json
{
  "sub": "user_id",
  "scopes": ["admin"]
}
```

To gain access to admin-only features, the token must include the `"admin"` scope, and the user must have the `admin` role **and** be active.

### Authorization Logic

All protected routes check scopes and roles like so:

* If the route requires `"admin"` scope:

  * The token must include `"admin"`
  * The user’s `role` must be `admin`
  * The user must be active

Failing any of these conditions will result in a `403 Forbidden`.

---

## 🔒 Admin-Only Endpoint

### Upload Media File

**Endpoint:**
`POST /api/media/file-upload/{type}`

**Description:**
Upload a media file of the specified type. Only admin users can access this endpoint.

**Path Parameters:**

* `type`: string — the category/type of the file to be uploaded.

**Authentication Required:**

* Bearer token with `"admin"` scope

**Responses:**

* `201 Created`: File uploaded successfully
* `401 Unauthorized`: Missing or invalid token
* `403 Forbidden`: User is not an active admin

---

## 🔑 Available Token Scopes

The following scopes define what a user can do within the system. Scopes are embedded in access tokens and are used to enforce permission checks.

| **Scope** | **Description**                        |
| --------- | -------------------------------------- |
| `admin`   | Admin access to all endpoints          |
| `agent`   | Allows creating and managing products  |
| `client`  | Allows viewing and purchasing products |
| `otp`     | Temporary access for OTP verification  |

> **Note:**
>
> * User `role` values: `user`, `admin`, `moderator`
> * User `user_type` values: `client`, `agent`

---



