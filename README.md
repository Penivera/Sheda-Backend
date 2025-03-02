# Sheda-Backend
Backend for sheda solution


# **Real Estate Platform Backend(Still under development most fearures are still being worked on)**  

This is the backend for a real estate platform built with **FastAPI**. The platform supports different user roles (e.g., buyers, sellers, agents), property listings, user authentication, and secure transactions.  

## **Features**  

- **User Authentication & Management**  
  - Role-based accounts (Buyer, Seller, Agent, etc.)  
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

5. **View live server @ https://sheda-backend-production.up.railway.app/#/Auth/signup_buyer_auth_signup_buyer_post**  
   

6. **Start the server**  
   ```sh
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload  
   ```

## **API Endpoints**  

### **Authentication**  
- `POST /auth/signup` - Register a new user  
- `POST /auth/login` - Authenticate and get JWT  
- `POST /auth/reset-password` - Request password reset  

### **Users**  
- `PUT /users/update` - Update user profile  
- `GET /users/me` - Get current user details  

### **Properties**  
- `POST /properties/` - Create a property listing  
- `GET /properties/` - Get all properties  
- `GET /properties/{id}` - Get property details  
- `PUT /properties/{id}` - Update a listing  
- `DELETE /properties/{id}` - Remove a listing  

## **Deployment**  

This application can be deployed on **Render, Railway, or Azure VPS**. Ensure the `.env` is correctly configured.  

## **Contributing**  

1. Fork the repository  
2. Create a new branch  
3. Make changes and commit  
4. Push to your fork and create a PR  

## **License**  

MIT License
