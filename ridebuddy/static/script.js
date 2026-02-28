// App State
let appState = {
    isLoggedIn: false,
    userType: null, // 'student' or 'rider'
    currentUser: null,
    loginType: 'student',
    accountType: 'student',
    selectedRideType: null,
    currentRating: 0,
    ratingContext: null,
    currentLocation: null,
    users: []
};

const defaultConfig = {
    app_title: 'RideBuddy'
};

let config = { ...defaultConfig };
let locationWatchId = null;
let lastGeocodedPos = null;
let searchTimeout = null;
let deferredPrompt = null;

// ==========================================
// PWA INSTALL LOGIC
// ==========================================
window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent the mini-infobar from appearing on mobile
    e.preventDefault();
    // Stash the event so it can be triggered later.
    deferredPrompt = e;
    // Update UI to notify the user they can install the PWA
    showInstallBanner();
});

function showInstallBanner() {
    const banner = document.getElementById('pwaInstallBanner');
    if (banner) banner.classList.remove('d-none');
}

async function installApp() {
    if (!deferredPrompt) return;
    // Show the install prompt
    deferredPrompt.prompt();
    // Wait for the user to respond to the prompt
    const { outcome } = await deferredPrompt.userChoice;
    console.log(`User response to the install prompt: ${outcome}`);
    // We've used the prompt, and can't use it again, throw it away
    deferredPrompt = null;
    // Hide the banner
    const banner = document.getElementById('pwaInstallBanner');
    if (banner) banner.classList.add('d-none');
}

window.addEventListener('appinstalled', (evt) => {
    showToast('RideBuddy installed successfully!', 'success');
});

// ==========================================
// 1. STATE & INITIALIZATION
// ==========================================
function loadState() {
    const savedState = localStorage.getItem('rideBuddyState');
    if (savedState) {
        appState = JSON.parse(savedState);
    }
}

// Save state to localStorage
function saveState() {
    localStorage.setItem('rideBuddyState', JSON.stringify(appState));
}

// Initialize Element SDK
if (window.elementSdk) {
    window.elementSdk.init({
        defaultConfig,
        onConfigChange: async (newConfig) => {
            config = { ...defaultConfig, ...newConfig };
            document.title = config.app_title;
        },
        mapToCapabilities: (cfg) => ({
            recolorables: [],
            borderables: [],
            fontEditable: undefined,
            fontSizeable: undefined
        }),
        mapToEditPanelValues: (cfg) => new Map([
            ['app_title', cfg.app_title || defaultConfig.app_title]
        ])
    });
}

// Initialize Data SDK
const dataHandler = {
    onDataChanged(data) {
        appState.users = data;
        saveState();
    }
};

async function initDataSdk() {
    if (window.dataSdk) {
        const result = await window.dataSdk.init(dataHandler);
        if (!result.isOk) {
            console.error('Failed to initialize Data SDK');
        }
    }
}

initDataSdk();
loadState();

// ==========================================
// 2. CORE UTILITIES (Toasts, Navigation)
// ==========================================
function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'custom-toast';

    const iconMap = {
        success: 'bi-check-circle-fill text-success',
        error: 'bi-x-circle-fill text-danger',
        warning: 'bi-exclamation-circle-fill text-warning',
        info: 'bi-info-circle-fill text-primary'
    };

    toast.innerHTML = `
        <i class="bi ${iconMap[type]} fs-4"></i>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Route Map - will be populated by templates if needed
let routes = {};

// Page Navigation
function navigateTo(page) {
    saveState();
    // If it's a known route, use it. Otherwise, assume it's a path.
    const url = routes[page] || (page.startsWith('/') ? page : '/' + page + '/');
    window.location.href = url;
}

function showPage(pageId) {
    // For compatibility with existing calls in HTML
    if (pageId === 'loginPage') navigateTo('login');
    else if (pageId === 'createAccountPage') navigateTo('signup');
    else if (pageId === 'welcomePage') navigateTo('index');
    else {
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        const el = document.getElementById(pageId);
        if (el) el.classList.add('active');
    }
}

// ==========================================
// 3. AUTHENTICATION & ACCOUNT
// ==========================================

// Login type selection
function selectLoginType(type, element) {
    appState.loginType = type;
    document.querySelectorAll('.user-type-btn').forEach(btn => btn.classList.remove('active'));
    element.classList.add('active');

    if (type === 'student') {
        document.getElementById('studentLoginField').classList.remove('d-none');
        document.getElementById('riderLoginField').classList.add('d-none');
    } else {
        document.getElementById('studentLoginField').classList.add('d-none');
        document.getElementById('riderLoginField').classList.remove('d-none');
    }
    saveState();
}

// Account type selection
function selectAccountType(type, element) {
    appState.accountType = type;
    document.querySelectorAll('.user-type-btn').forEach(btn => btn.classList.remove('active'));
    element.classList.add('active');

    if (type === 'student') {
        document.getElementById('studentFields').classList.remove('d-none');
        document.getElementById('riderFields').classList.add('d-none');
    } else {
        document.getElementById('studentFields').classList.add('d-none');
        document.getElementById('riderFields').classList.remove('d-none');
    }
    saveState();
}

// Handle image upload
function handleImageUpload(input) {
    if (input.files && input.files[0]) {
        const icon = document.getElementById('imageIcon');
        if (icon) icon.className = 'bi bi-check-circle fs-2 text-success';
    }
}

// Handle Login
async function handleLogin(event) {
    event.preventDefault();

    let identifier;
    if (appState.loginType === 'student') {
        identifier = document.getElementById('loginIubId').value.trim();
        if (!identifier) {
            showToast('Please enter your Member ID', 'error');
            return;
        }
    } else {
        identifier = document.getElementById('loginLicenceNo').value.trim();
        if (!identifier) {
            showToast('Please enter your license number', 'error');
            return;
        }
    }

    // Find user in data
    const user = appState.users.find(u =>
        (appState.loginType === 'student' && u.iub_id === identifier) ||
        (appState.loginType === 'rider' && u.licence_no === identifier)
    );

    if (user) {
        appState.isLoggedIn = true;
        appState.userType = user.type;
        appState.currentUser = user;
        saveState();
        showMainApp();
        showToast('Welcome back, ' + user.name + '!', 'success');
    } else {
        // Demo login for testing
        appState.isLoggedIn = true;
        appState.userType = appState.loginType;
        appState.currentUser = {
            type: appState.loginType,
            name: appState.loginType === 'student' ? 'Demo Student' : 'Demo Rider',
            iub_id: appState.loginType === 'student' ? identifier : '',
            licence_no: appState.loginType === 'rider' ? identifier : '',
            rating: 4.5,
            wallet: 500
        };
        saveState();
        showMainApp();
        initLocationTracking();
        showToast('Logged in as demo user', 'info');
    }
}

// Handle Create Account
async function handleCreateAccount(event) {
    event.preventDefault();

    const btn = document.getElementById('createAccountBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Creating...';

    let userData = {
        type: appState.accountType,
        created_at: new Date().toISOString(),
        rating: 5.0,
        wallet: 0
    };

    if (appState.accountType === 'student') {
        const iubId = document.getElementById('regIubId').value.trim();
        const name = document.getElementById('regStudentName').value.trim();
        const gender = document.getElementById('regStudentGender').value;
        const phone = document.getElementById('regStudentPhone').value.trim();
        const email = document.getElementById('regStudentEmail').value.trim();
        const emergency = document.getElementById('regStudentEmergency').value.trim();
        const address = document.getElementById('regStudentAddress').value.trim();

        if (!iubId || !name || !gender || !phone || !email || !emergency || !address) {
            showToast('Please fill in all required fields', 'error');
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-person-plus me-2"></i>Create Account';
            return;
        }

        userData = {
            ...userData,
            iub_id: iubId,
            name: name,
            gender: gender,
            phone: phone,
            email: email,
            emergency_contact: emergency,
            home_address: address,
            licence_no: '',
            image: ''
        };
    } else {
        const licenceNo = document.getElementById('regLicenceNo').value.trim();
        const name = document.getElementById('regRiderName').value.trim();
        const gender = document.getElementById('regRiderGender').value;
        const phone = document.getElementById('regRiderPhone').value.trim();
        const email = document.getElementById('regRiderEmail').value.trim();
        const emergency = document.getElementById('regRiderEmergency').value.trim();

        if (!licenceNo || !name || !gender || !phone || !email || !emergency) {
            showToast('Please fill in all required fields', 'error');
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-person-plus me-2"></i>Create Account';
            return;
        }

        userData = {
            ...userData,
            licence_no: licenceNo,
            name: name,
            gender: gender,
            phone: phone,
            email: email,
            emergency_contact: emergency,
            iub_id: '',
            home_address: '',
            image: ''
        };
    }

    if (window.dataSdk) {
        const result = await window.dataSdk.create(userData);
        if (result.isOk) {
            showToast('Account created successfully!', 'success');
            appState.isLoggedIn = true;
            appState.userType = userData.type;
            appState.currentUser = userData;
            saveState();
            showMainApp();
        } else {
            showToast('Failed to create account. Please try again.', 'error');
        }
    } else {
        // Demo mode
        appState.isLoggedIn = true;
        appState.userType = userData.type;
        appState.currentUser = userData;
        saveState();
        showMainApp();
        initLocationTracking();
        showToast('Account created (demo mode)', 'success');
    }

    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-person-plus me-2"></i>Create Account';
}

// ==========================================
// 4. LOCATION SERVICES
// ==========================================

// Geolocation Tracking
function initLocationTracking() {
    if (!navigator.geolocation) {
        showToast("Geolocation is not supported by your browser", "warning");
        return;
    }

    if (locationWatchId) {
        navigator.geolocation.clearWatch(locationWatchId);
    }

    const options = { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 };

    locationWatchId = navigator.geolocation.watchPosition(
        (pos) => {
            const { latitude, longitude } = pos.coords;
            appState.currentLocation = { lat: latitude, lng: longitude, timestamp: Date.now() };
            saveState();

            // Only update address name if moved > 50 meters or first time
            if (!lastGeocodedPos || calculateDistance(latitude, longitude, lastGeocodedPos.lat, lastGeocodedPos.lng) > 0.05) {
                lastGeocodedPos = { lat: latitude, lng: longitude };
                updateLocationName(latitude, longitude);
            }
        },
        (err) => {
            if (err.code === 1 || err.code === 2) {
                showToast("Location is OFF. Please turn ON GPS.", "warning");
                appState.currentLocation = null;
                saveState();
            }
        },
        options
    );
}

// Convert Lat/Lng to human-readable address
async function updateLocationName(lat, lng) {
    const pickupInput = document.getElementById('pickupLocation');
    if (pickupInput && !pickupInput.value) {
        pickupInput.value = "Locating...";
    }

    try {
        const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}`, {
            headers: { 'Accept-Language': 'en' }
        });
        const data = await response.json();

        if (data && data.address) {
            const addr = data.address;
            const locationName = [
                addr.road || addr.suburb || addr.neighbourhood,
                addr.city || addr.town || addr.village
            ].filter(Boolean).join(', ');

            if (pickupInput && (pickupInput.value === "Locating..." || pickupInput.value === "Current Location" || !pickupInput.value)) {
                pickupInput.value = locationName || data.display_name.split(',')[0];
                validateRideSearch();
            }
        }
    } catch (error) {
        console.error("Geocoding error:", error);
    }
}

// Simple distance helper (km)
function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
        Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

// Show Main App
function showMainApp() {
    if (appState.userType === 'student') {
        navigateTo('home_student');
    } else {
        navigateTo('home_rider');
    }
}

// Update profile displays
function updateProfileDisplays() {
    if (appState.currentUser) {
        const initial = appState.currentUser.name ? appState.currentUser.name.charAt(0).toUpperCase() : 'U';

        if (appState.userType === 'student') {
            const nameDisp = document.getElementById('studentNameDisplay');
            if (nameDisp) nameDisp.textContent = appState.currentUser.name || 'Student';

            const avatarSmall = document.getElementById('studentAvatarSmall');
            if (avatarSmall) avatarSmall.textContent = initial;

            const profAvatar = document.getElementById('studentProfileAvatar');
            if (profAvatar) profAvatar.textContent = initial;

            const profName = document.getElementById('studentProfileName');
            if (profName) profName.textContent = appState.currentUser.name || 'Student Name';

            const profId = document.getElementById('studentProfileId');
            if (profId) profId.textContent = 'Member ID: ' + (appState.currentUser.iub_id || 'N/A');
        } else {
            const nameDisp = document.getElementById('riderNameDisplay');
            if (nameDisp) nameDisp.textContent = appState.currentUser.name || 'Rider';

            const avatarSmall = document.getElementById('riderAvatarSmall');
            if (avatarSmall) avatarSmall.textContent = initial;

            const profAvatar = document.getElementById('riderProfileAvatar');
            if (profAvatar) profAvatar.textContent = initial;

            const profName = document.getElementById('riderProfileName');
            if (profName) profName.textContent = appState.currentUser.name || 'Rider Name';

            const profLic = document.getElementById('riderProfileLicence');
            if (profLic) profLic.textContent = 'License: ' + (appState.currentUser.licence_no || 'N/A');
        }
    }
}

// ==========================================
// 5. RIDE & DRIVER OPERATIONS
// ==========================================

// Switch Nav Tab
function switchNavTab(tab) {
    if (tab === 'home') navigateTo(appState.userType === 'student' ? 'home_student' : 'home_rider');
    else if (tab === 'activity') navigateTo(appState.userType === 'student' ? 'activity_student' : 'activity_rider');
    else if (tab === 'history') navigateTo(appState.userType === 'student' ? 'history_student' : 'history_rider');
    else if (tab === 'account') navigateTo(appState.userType === 'student' ? 'account_student' : 'account_rider');
}

// Show Student Page
function showStudentPage(page) {
    const pageMap = {
        'home': 'home_student',
        'ride': 'ride_student',
        'confirmRide': 'confirm_ride_student',
        'shareRide': 'share_ride_student',
        'availableRide': 'available_ride_student',
        'activity': 'activity_student',
        'history': 'history_student',
        'individualHistory': 'individual_history_student',
        'account': 'account_student'
    };
    if (pageMap[page]) navigateTo(pageMap[page]);
}

// Show Rider Page
function showRiderPage(page) {
    const pageMap = {
        'home': 'home_rider',
        'rideStart': 'ride_start_rider',
        'activity': 'activity_rider',
        'history': 'history_rider',
        'individualHistory': 'individual_history_rider',
        'account': 'account_rider'
    };
    if (pageMap[page]) navigateTo(pageMap[page]);
}

// Select Ride Type
function selectRideType(type, element) {
    appState.selectedRideType = type;
    document.querySelectorAll('.ride-option').forEach(opt => opt.classList.remove('selected'));
    element.classList.add('selected');
    saveState();
    validateRideSearch();
}

function cancelSearch() {
    appState.isWaiting = false;
    appState.rideStatus = null;
    saveState();
    showToast('Ride request cancelled.', 'info');
    navigateTo('home_student');
}

function applyGenderFilter() {
    const selected = document.querySelector('input[name="genderPref"]:checked')?.value || 'any';
    appState.genderFilter = selected;
    saveState();

    const badge = document.getElementById('genderPrefBadge');
    if (badge) {
        if (selected === 'male') {
            badge.innerHTML = '<i class="bi bi-gender-male me-1"></i>Only Male';
            badge.classList.remove('bg-primary-subtle', 'text-primary');
            badge.classList.add('bg-blue-subtle', 'text-blue');
        } else if (selected === 'female') {
            badge.innerHTML = '<i class="bi bi-gender-female me-1"></i>Only Female';
            badge.classList.remove('bg-primary-subtle', 'text-primary');
            badge.classList.add('bg-pink-subtle', 'text-pink');
        } else {
            badge.innerHTML = '<i class="bi bi-gender-ambiguous me-1"></i>Any Gender';
        }
    }
    showToast(`Filtering by ${selected} gender`, 'info');
}

function showFilterModal() {
    const modal = new bootstrap.Modal(document.getElementById('filterModal'));
    modal.show();
}

// Go to Ride Page
function goToRidePage() {
    const pickupInput = document.getElementById('pickupLocation');
    const dropInput = document.getElementById('dropLocation');

    if (!pickupInput || !dropInput) return;

    const pickup = pickupInput.value.trim();
    const drop = dropInput.value.trim();

    if (!pickup || !drop || !appState.selectedRideType) {
        showToast('Please fill all details and select a ride type', 'warning');
        return;
    }

    // Save to localStorage so ride_student.html can pick it up
    localStorage.setItem('pickupLoc', pickup);
    localStorage.setItem('dropLoc', drop);
    saveState();

    navigateTo('ride_student');
}

// Validate Ride Search Form
function validateRideSearch() {
    const pickupInput = document.getElementById('pickupLocation');
    const dropInput = document.getElementById('dropLocation');
    const findBtn = document.getElementById('findRidesBtn');

    if (!pickupInput || !dropInput || !findBtn) return;

    const isPickupFilled = pickupInput.value.trim().length > 0;
    const isDropFilled = dropInput.value.trim().length > 0;
    const isTypeSelected = appState.selectedRideType !== null;

    if (isPickupFilled && isDropFilled && isTypeSelected) {
        findBtn.disabled = false;
        findBtn.style.opacity = "1";
    } else {
        findBtn.disabled = true;
        findBtn.style.opacity = "0.7";
    }
}

// Search Individual Ride
function searchIndividualRide() {
    showToast('Searching for individual rides...', 'info');
    setTimeout(() => {
        navigateTo('confirm_ride_student');
    }, 1500);
}

// Search Share Ride
function searchShareRide() {
    navigateTo('share_ride_student');
}

// Select Share Ride
function selectShareRide(rideId) {
    navigateTo('available_ride_student');
}

// Create New Share Ride
function createNewShareRide() {
    showToast('Creating new share ride...', 'info');
    setTimeout(() => {
        showToast('Share ride created! Waiting for passengers.', 'success');
    }, 1000);
}

// Confirm Ride
function confirmRide() {
    showToast('Ride confirmed! Your rider is on the way.', 'success');
    appState.rideStatus = 'active';
    saveState();
    setTimeout(() => {
        navigateTo('activity_student');
    }, 500);
}

// Confirm Share Ride
function confirmShareRide() {
    showToast('You have joined the share ride!', 'success');
    appState.rideStatus = 'active';
    saveState();
    setTimeout(() => {
        navigateTo('activity_student');
    }, 500);
}

// Look for More Riders
function lookForMoreRiders() {
    showToast('Searching for more options...', 'info');
    setTimeout(() => {
        navigateTo('confirm_ride_student');
        showToast('Found another rider!', 'success');
    }, 3000);
}

// Emergency Call
function emergencyCall() {
    showToast('Contacting emergency services...', 'warning');
}

// Show Individual History
function showIndividualHistory(userType, historyId) {
    if (userType === 'student') {
        navigateTo('individual_history_student');
    } else {
        navigateTo('individual_history_rider');
    }
}

// Show Rating Page
function showRatingPage(context) {
    appState.ratingContext = context;
    appState.currentRating = 0;
    saveState();
    navigateTo('rating');
}

// Go Back From Rating
function goBackFromRating() {
    navigateTo(appState.userType === 'student' ? 'history_student' : 'history_rider');
}

// Set Rating
function setRating(rating) {
    appState.currentRating = rating;
    saveState();

    document.querySelectorAll('#ratingStars i').forEach((star, index) => {
        if (index < rating) {
            star.classList.remove('bi-star');
            star.classList.add('bi-star-fill');
            star.style.color = '#ffc107';
        } else {
            star.classList.remove('bi-star-fill');
            star.classList.add('bi-star');
            star.style.color = '#e8eaed';
        }
    });
}

// Submit Rating
function submitRating() {
    if (appState.currentRating === 0) {
        showToast('Please select a rating', 'warning');
        return;
    }

    showToast('Thank you for your feedback!', 'success');
    setTimeout(() => {
        navigateTo(appState.userType === 'student' ? 'history_student' : 'history_rider');
    }, 1000);
}

// Rider Functions
function toggleRiderStatus() {
    const toggle = document.getElementById('riderOnlineToggle');
    if (toggle.checked) {
        showToast('You are now online', 'success');
    } else {
        showToast('You are now offline', 'info');
    }
}

function showRideRequestDetail(requestId) {
    showToast('Loading ride details...', 'info');
}

function acceptRide(rideId) {
    showToast('Ride accepted! Navigate to pickup location.', 'success');
    appState.riderRideStatus = 'pending';
    saveState();
    setTimeout(() => {
        navigateTo('activity_rider');
    }, 500);
}

function startRide() {
    showToast('Ride started!', 'success');
    navigateTo('ride_start_rider');
}

function finishRide() {
    showToast('Ride completed! Earnings added to wallet.', 'success');
    appState.riderRideStatus = 'none';
    saveState();
    setTimeout(() => {
        showRatingPage('rider');
    }, 1000);
}

// Shared Functions
function showWalletPage() {
    navigateTo('wallet');
}

function showSettingsPage() {
    navigateTo('settings');
}

function showAboutPage() {
    navigateTo('about');
}

function showFilterModal() {
    showToast('Filter options coming soon!', 'info');
}

function handleLogout() {
    if (locationWatchId) {
        navigator.geolocation.clearWatch(locationWatchId);
        locationWatchId = null;
    }
    appState.isLoggedIn = false;
    appState.userType = null;
    appState.currentUser = null;
    localStorage.removeItem('rideBuddyState');
    navigateTo('index');
}

// Debounce helper for search
function debounceSearch(query, resultId) {
    clearTimeout(searchTimeout);
    if (!query || query.length < 3) {
        document.getElementById(resultId).classList.add('d-none');
        return;
    }
    searchTimeout = setTimeout(() => fetchSuggestions(query, resultId), 500);
}

// Fetch suggested locations from Photon API (biasing near user)
async function fetchSuggestions(query, resultId) {
    const container = document.getElementById(resultId);

    // Show loading state
    container.innerHTML = '<div class="p-3 text-center small text-muted"><span class="spinner-border spinner-border-sm me-2"></span>Searching locations...</div>';
    container.classList.remove('d-none');

    let url = `https://photon.komoot.io/api/?q=${encodeURIComponent(query)}&limit=5`;

    // Bias results near user if location is available
    if (appState.currentLocation) {
        url += `&lat=${appState.currentLocation.lat}&lon=${appState.currentLocation.lng}`;
    }

    try {
        const response = await fetch(url);
        const data = await response.json();

        container.innerHTML = '';
        if (data.features && data.features.length > 0) {
            data.features.forEach(feature => {
                const props = feature.properties;
                const name = props.name || props.street || '';
                const city = props.city || props.district || props.state || '';
                const country = props.country || '';
                const subtitle = city ? `${city}, ${country}` : country;

                const item = document.createElement('div');
                item.className = 'suggestion-item';
                item.innerHTML = `
                    <div class="suggestion-icon"><i class="bi bi-geo-alt"></i></div>
                    <div class="suggestion-content">
                        <div class="suggestion-title">${name}</div>
                        <div class="suggestion-subtitle">${subtitle}</div>
                    </div>
                `;
                item.onclick = () => {
                    const inputId = resultId.replace('Suggestions', 'Location');
                    const fullLabel = name + (city ? ', ' + city : '');
                    document.getElementById(inputId).value = fullLabel;

                    // Save coordinates for the specific field
                    const type = inputId.includes('pickup') ? 'pickup' : 'drop';
                    localStorage.setItem(`${type}Lat`, feature.geometry.coordinates[1]);
                    localStorage.setItem(`${type}Lng`, feature.geometry.coordinates[0]);

                    container.classList.add('d-none');
                    validateRideSearch();
                };
                container.appendChild(item);
            });
            container.classList.remove('d-none');
        } else {
            container.innerHTML = '<div class="p-3 text-center small text-muted">No locations found.</div>';
        }
    } catch (error) {
        console.error("Search error:", error);
        container.innerHTML = '<div class="p-3 text-center small text-danger">Error loading suggestions.</div>';
        setTimeout(() => container.classList.add('d-none'), 2000);
    }
}

// Close suggestions when clicking elsewhere
document.addEventListener('click', (e) => {
    if (!e.target.closest('.position-relative')) {
        document.querySelectorAll('.suggestions-dropdown').forEach(el => el.classList.add('d-none'));
    }
});

// Auto-init for specific pages
document.addEventListener('DOMContentLoaded', () => {
    updateProfileDisplays();

    // Set active tab in bottom nav based on page filename
    const path = window.location.pathname;
    const segments = path.split('/').filter(s => s.length > 0);
    const page = segments[segments.length - 1] || 'index';

    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        const tab = item.getAttribute('data-tab');
        if (page.includes(tab)) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    // Special logic for activity page states
    if (page === 'activity_student') {
        const searching = document.getElementById('searchingState');
        const active = document.getElementById('activeRideState');
        const none = document.getElementById('noActivityState');

        if (appState.isWaiting) {
            searching?.classList.remove('d-none');
            active?.classList.add('d-none');
            none?.classList.add('d-none');

            const broadcast = document.getElementById('broadcastText');
            if (broadcast) {
                const pickup = localStorage.getItem('pickupLoc')?.split(',')[0] || "Your location";
                const drop = localStorage.getItem('dropLoc')?.split(',')[0] || "Destination";
                broadcast.textContent = `${pickup} → ${drop}`;
            }
        } else if (appState.rideStatus === 'active') {
            active?.classList.remove('d-none');
            searching?.classList.add('d-none');
            none?.classList.add('d-none');
        } else {
            none?.classList.remove('d-none');
            searching?.classList.add('d-none');
            active?.classList.add('d-none');
        }
    } else if (page === 'activity_rider') {
        if (appState.riderRideStatus === 'pending') {
            document.getElementById('riderActiveRide').classList.remove('d-none');
            document.getElementById('riderNoActivity').classList.add('d-none');
        }
    }
    // Auto-init location if logged in
    const isHome = page.includes('home_student') || page.includes('home_rider');
    if (appState.isLoggedIn && isHome) {
        initLocationTracking();
    }
});
