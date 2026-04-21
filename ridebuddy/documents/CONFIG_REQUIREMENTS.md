# Minimum Viable Production Infrastructure: RideBuddy

**Project:** RideBuddy Application
**Target Scale:** ~1,000 Users
**Objective:** To outline the leanest, most cost-effective server configuration required to smoothly launch the RideBuddy application, handle user traffic, and secure data without over-provisioning resources.

---

## 1. Web Application Server (Compute)
To host the Django server and Gunicorn processes securely. We can keep the compute footprint lean by using a single optimized instance rather than a load-balanced cluster.

*   **Requirement:** 1x Virtual Machine (VPS).
*   **Target Specifications:** 2 vCPUs, 2 GB RAM.
*   **OS:** Ubuntu 22.04 LTS.
*   **Justification:** A 2GB RAM instance is the sweet spot for a single monolithic Django application. It provides enough memory overhead for Gunicorn to run 3-4 synchronous worker processes to handle concurrent ride requests from users smoothly, without facing Out-Of-Memory (OOM) crashes.

## 2. Primary Database (PostgreSQL)
The relational database is where all users, rides, commissions, and transaction data are stored.

*   **Requirement:** 1x Managed PostgreSQL Database Instance.
*   **Target Specifications:** 1 vCPU, 2 GB RAM.
*   **Storage:** 20 GB to 30 GB SSD.
*   **Justification:** Using a Managed Database separates our critical data from the web application server, providing automated daily backups and preventing data loss. For 1,000 users querying the database, 2 GB of RAM is sufficient for PostgreSQL to keep frequent queries and ride indexes in memory for fast retrieval.

## 3. In-Memory Cache (Redis)
To speed up the application and reduce load on the primary database, a caching layer is required.

*   **Requirement:** 1x Managed Redis Instance.
*   **Target Specifications:** 1 vCPU, 512 MB to 1 GB RAM.
*   **Justification:** Redis will store frequently accessed data (like user sessions and static ride options) directly in RAM. This ensures the web server can retrieve this data instantly without forcing the PostgreSQL database to perform repetitive queries. A small footprint of 512MB-1GB is plenty for pure caching purposes at this scale.

## 4. Media & Object Storage (Cloud Storage)
User-uploaded media such as profile images, vehicle pictures, and driving license scans cannot be stored safely on the web server's ephemeral disk.

*   **Requirement:** S3-Compatible Object Storage Bucket.
*   **Target Specifications:** 10 GB initial storage capacity.
*   **Justification:** Separating media assets into dedicated object storage is mandatory in modern web development. It guarantees that user uploads are permanent and won't be deleted during server updates or application restarts. 

## 4. Networking & DNS
*   **Domain Name Registration:** A custom domain (e.g., `ridebuddy.com`).
*   **SSL Certificates:** Standard Let's Encrypt automated certificates (HTTPS) directly installed on the Web Application Server.
*   **Justification:** Essential for allowing users to find the application and ensuring that all data (including passwords and ride details) passed between the user's phone and our server is strictly encrypted.

## 5. Transactional Email Service
For sending critical user communications such as verification emails and account resets.

*   **Requirement:** SMTP / Email API Provider.
*   **Volume Limits:** Minimum tier supporting up to 10,000 emails.
*   **Justification:** Django requires a third-party email service to reliably reach user inboxes without being flagged as spam by Google or Apple.

---

## Infrastructure Summary
This configuration strips away advanced high-availability tools (like Load Balancers) in favor of a lean, highly efficient architecture. 

By strategically allocating **2 vCPUs/2GB RAM** to the Web layer, dedicating **1 vCPU/2GB RAM** to the Database layer, and utilizing a lightweight **Redis Cache**, RideBuddy can easily support 1,000 users at the absolute lowest baseline hardware requirements while maintaining ultra-fast response times and professional data safety boundaries.
