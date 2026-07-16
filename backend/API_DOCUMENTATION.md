# Hotel Management Backend API Documentation

> Base URL: `/api`

## Authentication

### Register
- **POST** `/api/auth/register`

**Request (JSON):**
- `full_name` (string)
- `email` (string)
- `phone` (string)
- `password` (string)

**Response:**
- `success: true`

### Login
- **POST** `/api/auth/login`

**Request (JSON):**
- `email`
- `password`

**Response (JSON):**
- `success: true`
- `data` is returned in the existing contract under `extra` as:
  - `token` (access token)
  - `refresh_token` (refresh token)
  - `user` (public user fields)

### Refresh Access Token
- **POST** `/api/auth/refresh`

**Auth:** refresh token

**Response:**
- `success: true`
- `token`: new access token

### Profile
- **GET** `/api/auth/profile`

**Auth:** access token

## Rooms

- **GET** `/api/rooms`
- **GET** `/api/rooms/<room_id>`
- **POST** `/api/rooms`
- **PUT** `/api/rooms/<room_id>`
- **DELETE** `/api/rooms/<room_id>`

## Bookings

- **GET** `/api/bookings`
- **GET** `/api/bookings/<booking_id>`
- **POST** `/api/bookings`
- **PUT** `/api/bookings/<booking_id>`
- **DELETE** `/api/bookings/<booking_id>`

## Payments

- **GET** `/api/payments`
- **GET** `/api/payments/<payment_id>`
- **POST** `/api/payments`
- **PUT** `/api/payments/<payment_id>`
- **DELETE** `/api/payments/<payment_id>`
- **GET** `/api/payments/<payment_id>/invoice`

## Dashboard

- **GET** `/api/dashboard/summary`
- **GET** `/api/dashboard/recent-bookings`
- **GET** `/api/dashboard/recent-payments`
- **GET** `/api/dashboard/monthly-revenue`
- **GET** `/api/dashboard/room-occupancy`
- **GET** `/api/dashboard/booking-status`
- **GET** `/api/dashboard/payment-status`

## Customers

- **GET** `/api/customers`
- **GET** `/api/customers/<customer_id>`
- **POST** `/api/customers`
- **PUT** `/api/customers/<customer_id>`
- **DELETE** `/api/customers/<customer_id>`

## Employees

- **GET** `/api/employees`
- **GET** `/api/employees/<employee_id>`
- **POST** `/api/employees`
- **PUT** `/api/employees/<employee_id>`
- **DELETE** `/api/employees/<employee_id>`

