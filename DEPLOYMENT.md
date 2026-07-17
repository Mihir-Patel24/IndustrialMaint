# Deployment Guide

This document outlines the standard operating procedures for deploying the **IndustrialMaint AI Platform** in a production environment.

## 1. Streamlit Community Cloud (Hosted SaaS)

Streamlit Community Cloud provides a seamless, auto-updating deployment link connected directly to the GitHub repository.

### Prerequisites
1. **GitHub Repository**: The code must be pushed to a public or private GitHub repository.
2. **Supabase Setup**: The Supabase Edge PostgreSQL database must be live, and you must have your `SUPABASE_URL` and `SUPABASE_ANON_KEY`.

### Steps:
1. Go to [share.streamlit.io](https://share.streamlit.io) and link your GitHub account.
2. Click **New App** and select the target repository.
3. Configuration:
   - **Main file path**: `dashboard/app.py`
   - **Python version**: `3.11`
4. **Environment Secrets**: 
   - Click `Advanced settings...` before deploying.
   - Paste the required variables into the `Secrets` TOML box.
   
```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "your-supabase-anon-key-here"
SECRET_KEY = "your-randomly-generated-secret-string"
DEMO_MODE = "true"
```
5. Click **Deploy!**

---

## 2. Docker Compose (Self-Hosted / On-Premise)

For enterprise security standards, data localization, or air-gapped factories, the platform can run totally self-hosted via Docker.

### Prerequisites
1. Docker Engine installed.
2. Docker Compose installed.

### Steps:
1. Clone the repository to the host server.
2. Create your environment file:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` with your secure variables (Supabase isn't strictly required if falling back to SQLite, but is highly recommended).
4. Run the compose environment in detached mode:
   ```bash
   docker-compose up -d --build
   ```
5. The dashboard is now live at `http://localhost:8501`.

### Maintenance:
- **View Logs**: `docker-compose logs -f app`
- **Rebuild after pulled changes**: `docker-compose up -d --build`
- **Stop**: `docker-compose down`

---

## 3. Verifying Deployment (Smoke Tests)

Whether running on bare metal, self-hosted Docker, or an external CI pipeline, we provide a `smoke_test.py` script.

To verify the codebase and dependencies are strictly intact before routing live operator traffic to the updated container:
```bash
python scripts/smoke_test.py
```
A successful output will indicate `✅ All smoke tests passed successfully!`.
