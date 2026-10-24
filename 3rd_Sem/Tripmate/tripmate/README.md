# TripMate: Travel Planning and Booking System

A Flask + SQLite web app where users explore destinations, plan trips and manage bookings.

## Features
- Destination catalogue with photos, prices (INR per person), ratings
- Filter by **budget** and **category**, plus search and sort
- **Trip plans** with dates and multiple destinations (cost estimate included)
- **Bookings**: create, view and cancel (total is computed on the server)
- **Authentication**: register / login / logout (hashed passwords, session cookies)
- **Personal dashboard**: stats, bookings, trip plans

## Run it
```bash
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000. The database (`tripmate.db`) and 14 sample destinations are created on first run.

Optional: `SECRET_KEY=your-secret python app.py` (set a real secret for anything beyond local use).

## Project structure
```
app.py                 Flask app: schema, seed data, pages, REST API
templates/             base, index, login, register, plan, dashboard
static/css/style.css   styling
static/js/app.js       frontend logic (fetch calls to the API)
```

## API
| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| POST | `/api/register`, `/api/login`, `/api/logout` | – | Authentication |
| GET | `/api/me` | yes | Current user |
| GET | `/api/destinations?category=&min_price=&max_price=&q=&sort=` | – | List/filter destinations (`sort`: `rating`, `price_asc`, `price_desc`) |
| GET | `/api/destinations/<id>` | – | One destination |
| GET | `/api/categories` | – | Categories and price range |
| GET / POST | `/api/trips` | yes | List / create trip plans |
| DELETE | `/api/trips/<id>` | yes | Delete a trip plan |
| GET / POST | `/api/bookings` | yes | List / create bookings |
| POST | `/api/bookings/<id>/cancel` | yes | Cancel a booking |
| GET | `/api/dashboard` | yes | Stats, trips and bookings for the dashboard |

## Notes
- Destination photos load from loremflickr.com by keyword, so they need internet access. If one fails, a gradient placeholder shows instead. You can replace the `image_url` values in `app.py` with your own images (e.g. files in `static/img/`).
- Payment is not implemented; bookings are confirmed immediately (suitable for a project demo).
