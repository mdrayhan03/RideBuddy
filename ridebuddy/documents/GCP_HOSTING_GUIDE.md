# RideBuddy: Google Cloud (GCP) Deployment Guide

This guide explains how to deploy the RideBuddy application to Google Cloud using your $300 free trial credits. Because we have a fully configured `docker-compose.yml` (featuring Django, Gunicorn, PostgreSQL, health checks, and resource limits), **Google Compute Engine (VPS)** is the most efficient and robust hosting method.

## Why Google Compute Engine?
Serverless architectures (like Google Cloud Run) wipe container data on restarts, which requires paying for a separate expensive managed Database. By renting a standard Compute Engine virtual machine (VPS), you can run both your Web Server and Database simultaneously inside Docker Compose, keeping your data safe on a standard hard drive and saving your free credits.

---

## Step 1: Create the Virtual Machine
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Navigate to **Compute Engine > VM Instances**.
3. Click **Create Instance**.
4. **Configuration:**
   - **Name:** `ridebuddy-prod-server`
   - **Region:** Choose the region closest to your users.
   - **Machine Configuration:** Select **E2 Series**. A `e2-micro` (1GB RAM) or `e2-small` (2GB RAM) is perfectly fine because our `docker-compose.yml` limits containers to 512MB RAM!
   - **Boot Disk:** Change the OS to **Ubuntu 22.04 LTS**. Give the disk at least 20GB of storage.
   - **Firewall:** Check both **Allow HTTP traffic** and **Allow HTTPS traffic**.
5. Click **Create** and wait a few moments. Once finished, note down your server's **External IP Address**.

---

## Step 2: Set Up the Server
Click the **SSH** button next to your new VM in the Google Cloud console to open a terminal directly in your browser.

1. **Install Docker and Docker Compose:**
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose

2. **Allow your user to run Docker without `sudo`:**
sudo usermod -aG docker $USER
newgrp docker

---

## Step 3: Deploy the Code
You need to get the RideBuddy code onto the server. 

**Option A: Git Clone (Recommended)**
git clone https://github.com/yourusername/RideBuddy.git
cd RideBuddy/app/ridebuddy

**Option B: Secure Copy (SCP) from Local**
If your code isn't on GitHub, open a terminal on your *local computer* and copy it to the server IP:
scp -r ./app/ridebuddy username@YOUR_EXTERNAL_IP:~/ridebuddy

---

## Step 4: Configure Environments
Before starting the servers, you must create your production `.env` file on the server exactly like on your local machine.

nano .env

Paste in your credentials:

DEBUG=0
SECRET_KEY='your-production-secret-key-here'
# Database (This matches the docker-compose setup we just built)
DATABASE_URL='postgres://ridebuddy_user:ridebuddy_password@db:5432/ridebuddy_db'

Save and exit (`Ctrl+O`, `Enter`, `Ctrl+X`).

---

## Step 5: Start the Platform!
Because the `docker-compose.yml` file is configured perfectly with health checks, you just run one command:

docker-compose up -d --build

**What happens now?**
1. Docker builds the Python image and pulls Postgres.
2. Django actively waits until Postgres is healthy and ready.
3. Django boots up securely on Gunicorn.

To apply database migrations and create an admin user on your live server, execute commands directly inside the running web container:
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic --noinput

---

## Step 6: Go Live
Your app is now fully running! You can visit it in a browser directly at your server's IP address:
http://YOUR_EXTERNAL_IP:8000