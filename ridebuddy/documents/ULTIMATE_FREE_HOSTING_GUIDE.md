# The Ultimate 100% Free Hosting Guide for Django

This guide outlines how to host your entire Django application (RideBuddy) for exactly **$0.00 per month, indefinitely**. 

To achieve a fully free production environment, we use a "Microservices" approach. Instead of paying one cloud provider for everything, we stitch together the generous "Always Free" tiers of specialized cloud services.

## Architecture Outline
*   **Web Server (Compute):** Google Cloud Platform (GCP)  - `e2-micro` Instance
*   **Database (PostgreSQL):** Supabase (Managed Postgres)
*   **Cache & Queue (Redis):** Upstash (Serverless Redis)
*   **Media Storage (Images):** Cloudinary

---

## Step 1: Setup the Database (Supabase)

Supabase provides a generous free tier of 500MB for PostgreSQL databases, complete with daily backups and a great UI.

1. Go to [Supabase](https://supabase.com/) and create an account.
2. Click **New Project** and select an organization.
3. Name your project (e.g., `ridebuddy-db`) and create a strong database password. Keep this password safe!
4. Choose a region closest to your users and click **Create new project**.
5. Once created, go to **Project Settings** (gear icon) -> **Database**.
6. Scroll down to **Connection String** and select **URI**.
7. Copy the connection string. It will look like this:
   `postgres://postgres.xxxxx:YOUR_PASSWORD@aws-0-eu-central-1.pooler.supabase.com:5432/postgres`

*Save this URL for Step 5.*

---

## Step 2: Setup Redis (Upstash)

Upstash offers a "serverless" Redis database where the free tier allows up to 10,000 commands per day.

1. Go to [Upstash](https://upstash.com/) and create an account.
2. Navigate to the **Redis** section and click **Create Database**.
3. Name it (e.g., `ridebuddy-redis`).
4. Select a region and check the box for **Free**.
5. Once created, scroll down to the **Connect to your database** section.
6. Copy the **Redis URL**. It looks like this:
   `rediss://default:xxxxx@eu1-upstash.io:30501`

*Save this URL for Step 5.*

---

## Step 3: Setup Media Storage (Cloudinary)

For user-uploaded files (profile pics), Docker containers are ephemeral, meaning uploads will be deleted if the server restarts. Cloudinary offers free, robust cloud storage.

1. Go to [Cloudinary](https://cloudinary.com/) and sign up.
2. Go to your Dashboard and copy your **CLOUDINARY_URL** (API Environment variable).
   It looks like this: `cloudinary://123456789:abcdefg@your_cloud_name`
3. **In your Django code**, you need to install the package:
   `pip install django-cloudinary-storage`
4. Update your `settings.py`:
   ```python
   INSTALLED_APPS = [
       ...
       'cloudinary',
       'cloudinary_storage',
       ...
   ]

   DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
   ```

*Save the CLOUDINARY_URL for Step 5.*

---

## Step 4: Setup the Web Server (Google Cloud "Always Free")

We will use GCP for compute. As long as you follow the exact parameters below, your VM will be completely free forever.

1. Go to the [Google Cloud Console](https://console.cloud.google.com/) -> **Compute Engine**.
2. Click **Create Instance**.
3. **Name:** `ridebuddy-web`
4. **⚠️ REGION (CRITICAL):** You **MUST** select one of these three regions to qualify for "Always Free":
   *   `us-central1` (Iowa)
   *   `us-west1` (Oregon)
   *   `us-east1` (South Carolina)
5. **Machine Configuration:** Select **E2 series** and choose the **`e2-micro`** machine type.
6. **Boot Disk:** Click Change. Select **Ubuntu 22.04 LTS**. Ensure "Disk Type" is **Standard persistent disk** and size is **max 30 GB**.
7. **Firewall:** Check both **Allow HTTP** and **Allow HTTPS**.
8. Click **Create**. Note down your server's **External IP**.

---

## Step 5: Connect Everything & Deploy

Now we connect the brain (GCP) to the limbs (Supabase, Upstash, Cloudinary).

1. Click the **SSH** button next to your GCP virtual machine.
2. Install Docker:
   ```bash
   sudo apt update && sudo apt install -y docker.io docker-compose git
   sudo usermod -aG docker $USER
   newgrp docker
   ```
3. Clone your code:
   ```bash
   git clone https://github.com/yourusername/RideBuddy.git
   cd RideBuddy/app/ridebuddy
   ```
4. Create the magical `.env` file that connects your microservices:
   ```bash
   nano .env
   ```
   Paste the following:
   ```env
   DEBUG=0
   SECRET_KEY=your_super_secret_key
   ALLOWED_HOSTS=YOUR_GCP_EXTERNAL_IP,yourdomain.com

   # Connections from Step 1, 2, and 3:
   DATABASE_URL=postgres://postgres.xxxxx:YOUR_PASSWORD@aws-0-eu-central-1.pooler.supabase.com:5432/postgres
   REDIS_URL=rediss://default:xxxxx@eu1-upstash.io:30501
   CLOUDINARY_URL=cloudinary://123456789:abcdefg@your_cloud_name
   ```
   Save (`Ctrl+O`, `Enter`, `Ctrl+X`).

### Step 6: Modifying Docker-Compose
Since your Database and Redis are now hosted externally, your GCP server **should not** run Postgres or Redis containers. It only needs to run the Django app!

Modify your `docker-compose.prod.yml` to remove the `db` and `redis` services entirely. Your new `docker-compose` should look very simple, only building the `web` and `celery` containers.

Start the app:
```bash
docker-compose up -d --build
```

### Apply Migrations Live
Because your database is external, you only run these on the web server once:
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic --noinput
```

**Congratulations!** 
Your app is now live, handles state securely on managed external Free Tier services, processes queues externally via Serverless Redis, and serves its application logic via an Always Free Google Cloud server. Total Cost: $0.00.
