# TourMate Nepal - Tour and Travel Management System

A Flask-based TU BCA 6th semester project for tour and travel management.

## Features
- Beautiful tour and travel homepage
- User registration and login
- Admin dashboard
- Tour package listing and booking
- Khalti-style payment flow (demo-ready)
- Mobile banking reference submission
- Cash on arrival
- Recommendation algorithm
- Smart trip cost estimation algorithm

## How to run
1. Open terminal in this folder.
2. Create virtual environment:
   - Windows: `python -m venv venv`
   - Activate: `venv\Scripts\activate`
3. Install dependencies:
   - `pip install -r requirements.txt`
4. Copy `.env.example` to `.env`
5. Run:
   - `python app.py`
6. Open: `http://127.0.0.1:5000`

## Default admin login
- Email: admin@tourmate.com
- Password: admin

## Database
- SQLite database file: `tourmate.db`
- It is created automatically on first run.
