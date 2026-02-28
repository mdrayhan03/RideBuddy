# 🚗 RideBuddy - Premium Community Ride-Sharing

RideBuddy is an ultra-premium, community-focused ride-sharing platform designed to simplify transportation for neighborhoods, campuses, and established communities. Built with **Django** and a state-of-the-art **Progressive Web App (PWA)** architecture, it delivers a seamless, native-app experience directly through the browser.

---

## ✨ Key Features

- **Ultra-Premium Landing Page**: A cinematic, information-rich first impression with glassmorphism design and interactive community metrics.
- **PWA Ready**: Installable on Android, iOS, and Desktop. Supports offline caching and instant notifications.
- **Community Safety**: Built for verified members. Features include "Verified Member Matching" and gender-priority filters.
- **Interactive Matching**: Real-time ride requests and status updates for both Riders and Members.
- **Comprehensive Profiles**: Detailed member and vehicle registration with real-time photo capture (ID Card & License).
- **Responsive Design**: Mobile-first architecture that looks stunning on every screen size.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- `pip` (Python package installer)
- Virtual Environment (`venv`) recommended

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/mdrayhan03/RideBuddy.git
   cd RideBuddy/app/ridebuddy
   ```

2. **Set up Virtual Environment**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**
   Create a `.env` file in the root `ridebuddy/` directory or ensure your settings are configured for your local database.

5. **Database Setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

### Running the Application

1. **Start the Development Server**
   ```bash
   python manage.py runserver
   ```
2. **Access the App**
   Open your browser and navigate to `http://127.0.0.1:8000/`.

---

## 📱 PWA Features

To experience RideBuddy as a native app:
1. Open the app in Chrome/Edge on Mobile or Desktop.
2. Look for the **"Install"** button in the Hero section or the browser's address bar.
3. Once installed, it will appear on your home screen with the official RideBuddy icon and work without the browser interface.

---

## 🛠️ Built With

- **Backend**: Django 6.0.2
- **Frontend**: Vanilla JS, CSS3 (Ultra-Premium Design System), Bootstrap 5
- **Features**: PWA Service Worker, Manifest JSON, Bootstrap Icons

---

## 👨‍💻 Developed By

**Md. Rayhan Hossain**  
*Lead Architect & Full-Stack Developer*

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.