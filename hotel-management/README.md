# 🏨 Royal Palace Luxury Hotel Management System

> **Experience Luxury Beyond Expectations**

A full-stack Hotel Management System developed using **Flask, MySQL, HTML5, CSS3, JavaScript, and Bootstrap 5**. The application provides a modern luxury hotel website with a secure backend for managing rooms, bookings, customers, employees, payments, invoices, and dashboard analytics.

---

# ✨ Features

## 🔐 Authentication
- User Registration
- User Login
- JWT Authentication
- Refresh Token Support
- Secure Password Hashing
- User Profile API

---

## 🏨 Room Management
- Add New Room
- Update Room Details
- Delete Room
- View All Rooms
- Search Rooms
- Filter Rooms
- Sort Rooms
- Room Availability Status
- Room Capacity Management

---

## 📅 Booking Management
- Create Booking
- Update Booking
- Cancel Booking
- Check-In
- Check-Out
- Booking Status
- Automatic Room Status Update
- Booking Validation

---

## 💳 Payment Management
- Payment Processing
- Payment History
- Payment Status
- Invoice Generation
- Payment Validation
- Booking Payment Integration

---

## 👥 Customer Management
- Add Customer
- Edit Customer
- Delete Customer
- Customer Search
- Pagination
- Validation

---

## 👨‍💼 Employee Management
- Employee CRUD
- Department Management
- Designation
- Salary Details
- Employee Status

---

## 📊 Dashboard
- Total Rooms
- Available Rooms
- Booked Rooms
- Maintenance Rooms
- Total Customers
- Total Employees
- Total Bookings
- Monthly Revenue
- Booking Statistics
- Payment Statistics
- Recent Bookings
- Recent Payments

---

# 🎨 Frontend Features

- Premium Luxury UI
- Gold & Black Theme
- Fully Responsive Design
- Bootstrap 5 Layout
- GSAP Animations
- AOS Scroll Animations
- Swiper.js Testimonials
- Gallery Filter
- Lightbox Gallery
- Font Awesome Icons
- SEO Friendly Pages
- OpenGraph Support
- JSON-LD Structured Data

---

# 🛠 Technology Stack

## Frontend
- HTML5
- CSS3
- JavaScript (ES6)
- Bootstrap 5
- GSAP
- AOS
- Swiper.js
- Chart.js
- Font Awesome

## Backend
- Python 3
- Flask
- SQLAlchemy
- Flask-JWT-Extended
- Flask-Migrate
- Flask-CORS
- Flask-Limiter
- PyMySQL

## Database
- MySQL

---

# 📂 Project Structure

```
hotel_management_system/
│
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── database.py
│   ├── requirements.txt
│   ├── .env
│   ├── models/
│   ├── routes/
│   ├── utils/
│   ├── services/
│   ├── logs/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── gunicorn.conf.py
│
├── hotel-management/
│   ├── index.html
│   ├── rooms.html
│   ├── amenities.html
│   ├── restaurant.html
│   ├── gallery.html
│   ├── booking.html
│   ├── dashboard.html
│   ├── login.html
│   ├── register.html
│   ├── contact.html
│   ├── about.html
│   ├── css/
│   ├── js/
│   ├── images/
│   └── assets/
│
└── README.md
```

---

# 🚀 Installation

## 1. Clone Repository

```bash
git clone https://github.com/yourusername/hotel-management-system.git
```

---

## 2. Open Backend

```bash
cd backend
```

---

## 3. Create Virtual Environment

### Windows

```bash
python -m venv .venv
```

---

## 4. Activate Virtual Environment

### Windows

```bash
.venv\Scripts\activate
```

---

## 5. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🗄 Database Configuration

Create a MySQL database:

```sql
CREATE DATABASE hotel_management;
```

Update the `.env` file:

```env
FRONTEND_URL=http://127.0.0.1:5500

SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DATABASE=hotel_management
MYSQL_USER=root
MYSQL_PASSWORD=

DEBUG=True
```

---

# ▶ Run the Backend

```bash
python app.py
```

Backend URL

```
http://127.0.0.1:5000
```

Health Check

```
http://127.0.0.1:5000/api/health
```

Expected Response

```json
{
    "success": true,
    "message": "Hotel Management Backend Running"
}
```

---

# 🌐 Run the Frontend

Open the **hotel-management** folder using the **Live Server** extension in Visual Studio Code.

Example URL:

```
http://127.0.0.1:5500/hotel-management/index.html
```

---

# 🔗 REST API

## Authentication

| Method | Endpoint |
|---------|----------|
| POST | /api/auth/register |
| POST | /api/auth/login |
| POST | /api/auth/refresh |
| GET | /api/auth/profile |

---

## Rooms

| Method | Endpoint |
|---------|----------|
| GET | /api/rooms |
| GET | /api/rooms/<id> |
| POST | /api/rooms |
| PUT | /api/rooms/<id> |
| DELETE | /api/rooms/<id> |

---

## Bookings

| Method | Endpoint |
|---------|----------|
| GET | /api/bookings |
| GET | /api/bookings/<id> |
| POST | /api/bookings |
| PUT | /api/bookings/<id> |
| DELETE | /api/bookings/<id> |

---

## Payments

| Method | Endpoint |
|---------|----------|
| GET | /api/payments |
| GET | /api/payments/<id> |
| POST | /api/payments |
| PUT | /api/payments/<id> |
| DELETE | /api/payments/<id> |
| GET | /api/payments/<id>/invoice |

---

## Dashboard

| Method | Endpoint |
|---------|----------|
| GET | /api/dashboard/summary |
| GET | /api/dashboard/monthly-revenue |
| GET | /api/dashboard/recent-bookings |
| GET | /api/dashboard/recent-payments |
| GET | /api/dashboard/booking-status |
| GET | /api/dashboard/payment-status |
| GET | /api/dashboard/room-occupancy |

---

# 🖼 Images

Place your hotel images in:

```
hotel-management/images/
```

Suggested filenames:

- hero.mp4
- rooms-hero.jpg
- gallery-hero.jpg
- booking-hero.jpg
- amenities-hero.jpg
- restaurant-hero.jpg
- deluxe.jpg
- executive.jpg
- family-suite.jpg
- presidential.jpg
- pool.jpg
- spa.jpg
- lobby.jpg
- dining.jpg
- guest1.jpg
- guest2.jpg
- guest3.jpg

---

# 🔒 Security

- JWT Authentication
- Refresh Tokens
- Password Hashing
- SQLAlchemy ORM
- CORS Protection
- Environment Variables
- Secure API Design

---

# 📈 Future Improvements

- Role-Based Access Control (RBAC)
- Online Payment Gateway Integration
- Email Notifications
- SMS Notifications
- PDF Invoice Download
- Room Image Upload
- Booking Calendar
- Advanced Reports
- Analytics Dashboard
- Multi-language Support

---

# 🧪 Testing

The backend API can be tested using:

- Browser (Health Endpoint)
- Postman
- Thunder Client

Health API:

```
GET /api/health
```

Expected Output:

```json
{
  "success": true,
  "message": "Hotel Management Backend Running"
}
```

---

# 👨‍💻 Developer

**Harsh Tyagi**

B.Tech – Computer Science Engineering

Raj Kumar Goel Institute of Technology & Management

---

# 📜 License

This project is developed for **educational, academic, and portfolio purposes**.

© 2026 Harsh Tyagi. All rights reserved.