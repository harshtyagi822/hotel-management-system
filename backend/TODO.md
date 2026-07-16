# Hotel Management Backend - Implementation Checklist

## Phase 1: Flask backend foundation
- [ ] Create backend/requirements.txt
- [ ] Create backend/.env.example
- [ ] Create backend/config.py
- [ ] Create backend/database.py
- [ ] Create backend/app.py
- [ ] Create backend/README.md (backend-specific)
- [ ] Create models/ package and model modules (scaffold with SQLAlchemy models)
- [ ] Create routes/ package and route blueprints (health + auth stub endpoints)
- [ ] Create centralized error handlers returning consistent JSON
- [ ] Implement GET /api/health endpoint
- [ ] Ensure Blueprints registration in app.py
- [ ] Ensure Flask-Migrate initialization
- [ ] Ensure Flask-JWT-Extended configuration
- [ ] Ensure Flask-CORS config uses FRONTEND_URL

