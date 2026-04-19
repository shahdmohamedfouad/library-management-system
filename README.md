# Library Management System 
A backend API built with FastAPI for managing a digital library system.
The project allows users to browse books, borrow and return them, and track borrowing history, with secure authentication and role-based access control.

🚀 Project Overview

This system provides a complete library management solution where users can interact with books efficiently while maintaining proper tracking and restrictions. It supports two types of users: Admin (Librarian) and Member, each with different permissions.

🧩 Key Features
📖 CRUD operations for managing books
🔄 Borrow and return system with availability validation
🚫 Prevention of borrowing unavailable books
📊 Tracking of borrowing history per user
👥 Role-based access control:
Admin: Manage books and view all records
Member: Borrow, return, and view personal history
🔐 Secure authentication using JWT
⚡ Performance optimization using Redis caching
🧪 API testing with pytest
🛠️ Tech Stack
FastAPI
PostgreSQL / SQLite (depending on setup)
Redis (Caching)
JWT Authentication
Pytest (Testing)
📌 Project Goal

The goal of this project is to demonstrate a scalable and well-structured backend system following modern software engineering practices, including RESTful API design, authentication, caching, logging, and testing.
