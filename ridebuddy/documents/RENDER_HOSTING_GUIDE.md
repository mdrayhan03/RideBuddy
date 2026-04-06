# RideBuddy: Render Deployment Guide (Free Tier)

This guide explains how to deploy the Dockerized version of RideBuddy completely for free using [Render.com](https://render.com). Because Render is a managed PaaS (Platform as a Service), we do not use `docker-compose.yml`. Instead, we deploy the web container and the database as two separate native Render services. 

---

## Step 1: Push Your Code to GitHub
Render pulls code directly from your repository. Ensure your entire RideBuddy project (including the `Dockerfile` and `requirements.txt`) is pushed to a GitHub repository.

*(Note: Never commit your `.env` file or SQLite database to GitHub!)*

---

## Step 2: Create a Free PostgreSQL Database
1. Log into your Render Dashboard.
2. Click **New +** and select **PostgreSQL**.
3. **Configuration:**
   - **Name:** `ridebuddy-db`
   - **Region:** Ohio (or closest to you)
   - **Instance Type:** Free ($0/month)
4. Click **Create Database**.
5. Once created, scroll down to the **"Internal Database URL"** section. Copy this URL! It will look something like: `postgres://ridebuddy_db_user:password@hostname/ridebuddy_db`.

---

## Step 3: Deploy the Docker Web Service
1. Go back to your Render Dashboard, click **New +** and select **Web Service**.
2. Connect your GitHub repository.
3. **Configuration:**
   - **Name:** `ridebuddy-app`
   - **Region:** Same region as your database.
   - **Environment:** Select **Docker** (Render will automatically find your `Dockerfile`!).
   - **Instance Type:** Free ($0/month)
4. **DO NOT** click deploy yet! Scroll down to the Advanced section.

---

## Step 4: Add Environment Variables
Render needs the secret values from your `.env` file to inject into the Docker container. Expand the **Environment Variables** section and add the following:

| Key | Value |
| :--- | :--- |
| `DATABASE_URL` | *(Paste the Internal Database URL you copied in Step 2)* |
| `DEBUG` | `False` |
| `SECRET_KEY` | *(A long, random string of text - do not use your default local one!)* |

*(If you are setting up emails, add your `EMAIL_HOST`, `EMAIL_HOST_USER`, etc., variables here as well!)*

---

## Step 5: Build and Deploy!
1. Click **Create Web Service**. 
2. Render will spin up its servers, read your `Dockerfile`, automatically run `manage.py collectstatic --noinput`, and start the Gunicorn web server.
3. This process takes about 2 to 5 minutes on the free tier.

---

## Step 6: Initializing the Database (Migrations)
Unlike local Docker where you use `docker compose exec`, Render provides a web-based terminal for your live environment.

1. Once the deploy says **"Live"**, click the **Shell** tab on your Render Web Service dashboard.
2. Inside that black terminal box, your Docker container is running! Type the following commands to initialize your brand new PostgreSQL database:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser

## Step 7: Go Live
Click the main Web Service URL (e.g., https://ridebuddy-app.onrender.com). Your fully Dockerized application is now live on the internet!

(Note: Render's Free Tier spins down the server after 15 minutes of inactivity. When the next user opens the app, it will take roughly 30 seconds to wake the server back up).