# Gaming Collection Manager

A web application for managing video game collections, platforms, peripherals, and related data. Built with Python and Flask, using Alembic for database migrations.

## Features
- Manage games, platforms (consoles), and peripherals
- Admin dashboard for digital/physical status, ownership, and more
- Database migrations with Alembic
- Responsive web interface with HTML templates and custom CSS

## Project Structure
- `src/` — Application source code (Flask app, models, routes)
- `migrations/` — Alembic migration scripts for database schema
- `templates/` — HTML templates for admin, dashboard, games, peripherals, and platforms
- `static/` — Static assets (CSS)
- `requirements.txt` — Python dependencies
- `Dockerfile`, `docker-compose.yml` — Containerization and deployment

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set up the database and run migrations:
   ```bash
   alembic upgrade head
   ```
3. Run the application:
   ```bash
   python src/run.py
   ```

## Development
- Use Alembic for database migrations:
  ```bash
  alembic revision --autogenerate -m "Your message"
  alembic upgrade head
  ```
- Static files are in `static/`, templates in `templates/`.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
