# RideBuddy AWS Hosting Guide (Free Tier Edition)

This guide outlines the complete steps to deploy the RideBuddy Django application on AWS using **only AWS Free Tier eligible services**. 

> **⚠️ IMPORTANT WARNING regarding 1000 Users vs. Free Tier**
> The AWS Free Tier provides `t2.micro` or `t3.micro` instances, which have **1 vCPU and 1 GB of RAM**. While this is perfectly fine for testing and small loads, supporting 1,000 active, concurrent users on a single 1GB RAM server is highly unlikely. If traffic spikes, the server will run out of memory. This guide focuses on getting you running for *free* first. Once you hit performance limits, you can easily upgrade these instances to `medium` or `large` sizes (which will incur costs).

---

## Architecture Overview (Free Tier)

*   **App Hosting (Compute):** Amazon EC2 (`t2.micro` or `t3.micro`) - 750 hours/month.
*   **Database:** Amazon RDS PostgreSQL (`db.t3.micro`) - 750 hours/month + 20 GB Storage.
*   **Cache & Queue:** Amazon ElastiCache Redis (`cache.t2.micro` or `cache.t3.micro`) - 750 hours/month.
*   **Media & Static Files:** Amazon S3 - 5 GB Storage, 20,000 Get Requests/month.

---

## Step 1: Handling Storage (Amazon S3)

In a production environment, user-uploaded files (like profile pictures or ID scans) cannot be stored on your application server. They must be uploaded directly to S3.

### 1. Create an S3 Bucket
1. Go to the **S3 Console** in AWS.
2. Click **Create bucket**.
3. Name it (e.g., `ridebuddy-media-bucket-2026`).
4. Uncheck **"Block all public access"** (you need users to be able to see the images). Note: Acknowledge the warning.
5. Click **Create bucket**.
6. Go to the bucket's **Permissions** tab and add this **Bucket Policy** to make objects publicly readable:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::ridebuddy-media-bucket-2026/*"
        }
    ]
}
```

### 2. Create IAM User for S3
1. Go to **IAM Console** -> **Users** -> **Add user**. Name it `ridebuddy-s3-user`.
2. Attach the existing policy: `AmazonS3FullAccess`.
3. After creation, generate **Access Keys** for this user. Save the `Access Key ID` and `Secret Access Key`.

### 3. Django Configuration
You need to install two libraries in your environment/Dockerfile:
`pip install boto3 django-storages`

Update your `settings.py`:
```python
# settings.py
import os

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = 'ridebuddy-media-bucket-2026'
AWS_S3_REGION_NAME = 'us-east-1' # change to your region
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None

# For Media Files
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# For Static Files (Optional: If you still want to use WhiteNoise, leave STATICFILES_STORAGE as is)
# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
```

---

## Step 2: Handling the Database (Amazon RDS Free Tier)

Do not run your database inside a Docker container on EC2 for production. Use Amazon RDS so AWS handles backups and updates.

### 1. Create a PostgreSQL Database
1. Go to the **RDS Console** -> **Create database**.
2. Select **Standard create** -> **PostgreSQL**.
3. **Templates**: Select **Free tier**. (This enforces valid free-tier settings).
4. Enter DB instance identifier (e.g., `ridebuddy-db`).
5. Set Master username (e.g., `postgres`) and a strong master password. Save these!
6. **Instance configuration**: Leave as `db.t3.micro` or `db.t2.micro`.
7. **Storage**: Leave at 20 GB. Uncheck "Enable storage autoscaling" to prevent accidental charges.
8. Under **Connectivity**, ensure "Public access" is **No** (best practice). It must be accessed only by your EC2 instance. Ensure the VPC is default.
9. Click **Create database** (It will take 5-10 minutes).
10. Once created, note the **Endpoint URL** (e.g., `ridebuddy-db.xxxx.us-east-1.rds.amazonaws.com`).

### 2. Django Configuration
Set these environment variables inside your server, which Django reads in `settings.py`:
```env
DATABASE_URL=postgres://postgres:YOUR_PASSWORD@YOUR_ENDPOINT_URL:5432/postgres
```

---

## Step 3: Handling Caching/Celery (Amazon ElastiCache Redis)

If you use Redis for caching or as a Celery message broker.

### 1. Create a Redis Cluster
1. Go to **ElastiCache Console** -> **Redis caches** -> **Create Redis cache**.
2. Select **Design your own cache** -> **Cluster mode disabled**.
3. Name it e.g., `ridebuddy-redis`.
4. **Node type**: Choose `cache.t2.micro` or `cache.t3.micro` (this is the free tier eligible node).
5. Number of replicas: **0** (Replica nodes are NOT free tier covered).
6. Expand **Advanced settings**, assign to the default VPC, and ensure the Security Group allows access.
7. Click **Create**. Note the **Primary Endpoint** URL.

### 2. Django Configuration
Update your `.env` and `settings.py`:
```env
REDIS_URL=redis://YOUR_REDIS_ENDPOINT:6379/1
```
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
    }
}
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1')
```

---

## Step 4: Hosting the Application (Amazon EC2 Free Tier)

Since you have Dockerized your application, the easiest way to launch the app code is running `docker-compose` on an EC2 instance.

### 1. Launch EC2 Instance
1. Go to **EC2 Console** -> **Instances** -> **Launch instances**.
2. Name it `ridebuddy-web-server`.
3. Choose **Ubuntu Server 22.04 LTS** as the OS.
4. **Instance type**: Select **t2.micro** (Free tier eligible).
5. Create a new **Key pair** (e.g., `ridebuddy-key.pem`), download it. You need this to SSH into the server later.
6. **Network settings**: Check **Allow SSH traffic**, **Allow HTTP traffic**, and **Allow HTTPS traffic**.
7. Click **Launch instance**.

### 2. Configure the Security Groups
Important: Your EC2 instance needs to be able to talk to your RDS database and Redis instance.
1. Find the Security Group assigned to your RDS instance.
2. Edit Inbound Rules: Add a PostgreSQL rule (Port 5432), and set the source to the Security Group ID of your EC2 instance.
3. Repeat the same for your Redis Security Group (Allow Port 6379 from the EC2 Security Group).

### 3. Deploy the App to EC2
Using your terminal (if using Windows, use Git Bash or PowerShell):
```bash
# Connect to your server
ssh -i "ridebuddy-key.pem" ubuntu@YOUR_EC2_PUBLIC_IP
```

Once inside the server, setup Docker:
```bash
# Install Docker and Git
sudo apt update
sudo apt install git docker.io docker-compose -y

# Allow ubuntu user to run docker
sudo usermod -aG docker ubuntu
```
*Logout and SSH back in for the docker group to apply.*

Clone your code and setup the environment variables:
```bash
git clone https://github.com/your-username/ridebuddy.git
cd ridebuddy/app/ridebuddy

# Create the .env file with production details
nano .env
```
Inside `.env` paste your AWS credentials and endpoints:
```env
DEBUG=False
SECRET_KEY=YOUR_SECURE_RANDOM_KEY
ALLOWED_HOSTS=YOUR_EC2_PUBLIC_IP,yourdomain.com

# RDS Database
DATABASE_URL=postgres://postgres:STRONG_PASSWORD@ridebuddy-db.xxxxx.us-east-1.rds.amazonaws.com:5432/postgres

# Redis Cache
REDIS_URL=redis://ridebuddy-redis.xxxxx.use1.cache.amazonaws.com:6379/1

# S3
AWS_ACCESS_KEY_ID=YOUR_IAM_ACCESS_KEY
AWS_SECRET_ACCESS_KEY=YOUR_IAM_SECRET_KEY
```

Run Docker Compose:
```bash
# Build and run in the background
docker-compose -f docker-compose.prod.yml up -d --build
```
*(You should have a production-ready docker-compose file that binds Gunicorn to port 80/443 or uses NGINX as a reverse proxy).*

## Scaling Up
When your traffic exceeds the Free Tier capability (1GB RAM):
1. **EC2**: Go to EC2 console, Stop Instance -> Change Instance Type (e.g. `t3.medium`) -> Start Instance.
2. **RDS**: Modify DB Instance -> Change DB Instance Class (e.g., `db.t3.medium`) -> Apply immediately. 

This infrastructure seamlessly separates the Application Code, Database, Caching, and Media Storage, laying out the exact architecture needed for professional deployments, scaling horizontally easily in the future.

---

## Alternative: "All-In-One" Docker Compose (Using AWS Credits)

If you have **AWS Startup/Educate Credits (e.g., $200+)**, you are not strictly limited to the `t2.micro` Free Tier instances. You can run your entire stack (Django, PostgreSQL, Redis) on a single, more powerful EC2 instance. This is the simplest deployment method.

### 1. The Architecture
*   **Single Server:** You deploy a single **`t3.medium`** (2 vCPUs, 4GB RAM) or **`t3.large`** EC2 instance.
*   **Docker Compose:** Your `docker-compose.yml` runs the Web App, PostgreSQL, and Redis containers all on this same machine.

### 2. Pros & Cons
*   ✅ **Pros:** Extremely simple setup (exactly mirrors local development), very cheap (a `t3.medium` is ~$30/month, meaning $200 in credits lasts over 6 months).
*   ❌ **Cons:** **No automatic database backups**. If the EC2 instance gets corrupted or terminated, you lose all database data unless you manually write a backup script (`pg_dump` mapped to S3). Harder to scale horizontally.

### 3. Deployment Steps
1. Launch an **Ubuntu Server 22.04 LTS** EC2 instance, but choose **`t3.medium`** instead of `t2.micro`.
2. Ensure Security Group allows **SSH (22), HTTP (80), and HTTPS (443)**. (No need to open Postgres/Redis ports since they communicate internally via Docker).
3. SSH into the server and install Docker/Docker-Compose as shown in Step 4.
4. Clone your repository: `git clone https://github.com/your-username/ridebuddy.git`
5. Configure `.env` to point DB and Redis to the local Docker containers:
    ```env
    DATABASE_URL=postgres://POSTGRES_USER:POSTGRES_PASSWORD@db:5432/POSTGRES_DB
    REDIS_URL=redis://redis:6379/1
    ```
6. Run everything:
    ```bash
    docker-compose up -d --build
    ```
This method skips Step 2 (RDS) and Step 3 (ElastiCache) entirely!
