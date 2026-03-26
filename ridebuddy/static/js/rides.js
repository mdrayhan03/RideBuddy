// Ride distribution and search logic for Students

const RideSearch = {
    // Current Active Filters
    filters: {
        gender: 'any',
        ac: 'any',
        hasVehicle: false
    },

    async fetchAndRender() {
        const container = document.getElementById('availableShareRides');
        if (!container) return;

        // Show loading state
        container.innerHTML = `
            <div class="p-4 text-center text-muted">
                <span class="spinner-border spinner-border-sm me-2"></span>Refreshing rides...
            </div>
        `;

        try {
            // Include booking_id if available in appState
            let url = routes['active_rides_json'];
            if (appState.currentBookingId) {
                url += `?booking_id=${appState.currentBookingId}`;
            }

            const data = await window.RideBuddyAPI.call(url);
            const activeRides = data.rides || [];

            // Update user's fare badge at the top
            const fareBadge = document.getElementById('userFareBadge');
            if (fareBadge && data.user_fare) {
                fareBadge.textContent = '৳' + data.user_fare;
                fareBadge.classList.remove('d-none');
            }

            // Apply all filters (Gender and AC)
            const filteredRides = activeRides.filter(ride => {
                // 1. Gender Filter
                const rideGender = ride.gender || 'any';
                const genderMatch = (this.filters.gender === 'any') || (rideGender === this.filters.gender);

                // 2. AC Filter (Only for car types)
                let acMatch = true;
                if (this.filters.ac !== 'any') {
                    const isAc = this.filters.ac === 'true';
                    acMatch = ride.ac_available === isAc;
                }

                // 3. Vehicle Provider Filter
                let vehicleMatch = true;
                if (this.filters.hasVehicle) {
                    // IF I want to be the provider, hide rides that already have a vehicle/rider
                    const alreadyHasRider = ride.rider && ride.rider.type !== 'Searching';
                    const alreadyHasVehicle = ride.has_vehicle;
                    vehicleMatch = (!alreadyHasRider && !alreadyHasVehicle);
                }
                // Else (hasVehicle is false): Show everything, I just want to join.

                return genderMatch && acMatch && vehicleMatch;
            });

            if (filteredRides.length > 0) {
                this.renderRides(filteredRides);
            } else {
                container.innerHTML = '<div class="p-4 text-center text-muted">No rides match your current filters.</div>';
            }

        } catch (err) {
            console.error('Ride Search Error:', err);
            container.innerHTML = '<div class="p-4 text-center text-danger">Failed to connect to server.</div>';
        }
    },

    renderRides(rides) {
        const container = document.getElementById('availableShareRides');
        container.innerHTML = '';

        rides.forEach(ride => {
            const card = document.createElement('div');
            card.className = 'ride-card-v2 animate-fade-in';

            // Rider Header Content
            const riderPhotoHtml = ride.rider.photo
                ? `<img src="${ride.rider.photo}" class="w-100 h-100 object-fit-cover">`
                : (ride.rider.name.charAt(0).toUpperCase());

            const matchHtml = ride.similarity
                ? `<span class="match-pill ms-auto">${ride.similarity}% Match</span>`
                : '';

            // Passenger List HTML
            let passengersHtml = '';
            ride.passengers.forEach(p => {
                const pPhoto = p.photo
                    ? `<img src="${p.photo}" class="w-100 h-100 object-fit-cover">`
                    : p.initial;

                passengersHtml += `
                    <div class="passenger-item" onclick="event.stopPropagation(); RideSearch.showProfileInfo(${JSON.stringify(p).replace(/"/g, '&quot;')}, 'passenger')">
                        <div class="passenger-avatar">${pPhoto}</div>
                        <span>${p.name}</span>
                        ${p.is_host ? '<span class="badge-owner" style="background: #e8f0fe; color: #1967d2; border-color: #d2e3fc;">Host</span>' : ''}
                        ${p.is_owner ? '<span class="badge-owner">Owner</span>' : ''}
                    </div>
                `;
            });

            // Scheduling Info
            let timeInfo = 'Active Now';
            let timeLeftHtml = '';

            if (ride.ride_type === 'schedule' && ride.scheduled_start) {
                const date = new Date(ride.scheduled_start);
                timeInfo = `<i class="bi bi-calendar-event me-1"></i>${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
                timeLeftHtml = `<div class="x-small text-muted mt-1" style="font-size: 0.65rem;">Scheduled Creation</div>`;
            } else {
                // Calculation for Instant/Active ride waiting window
                const created = new Date(ride.created_at);
                const now = new Date();
                const diffMins = Math.floor((now - created) / 60000);
                const remaining = Math.max(0, ride.waiting_threshold - diffMins);

                if (remaining > 0) {
                    timeLeftHtml = `<div class="x-small text-primary mt-1 fw-bold" style="font-size: 0.65rem;"><i class="bi bi-hourglass-split me-1"></i>Departs in ${remaining} min</div>`;
                } else {
                    timeLeftHtml = `<div class="x-small text-danger mt-1 fw-bold" style="font-size: 0.65rem;"><i class="bi bi-lightning-fill me-1"></i>Departing Soon</div>`;
                }
            }

            card.innerHTML = `
                <div class="rider-header">
                    <div class="rider-photo" style="background: var(--primary-color)" onclick="event.stopPropagation(); RideSearch.showProfileInfo(${JSON.stringify(ride.rider).replace(/"/g, '&quot;')}, 'rider')">
                        ${riderPhotoHtml}
                    </div>
                    <div>
                        <p class="mb-0 fw-bold">${ride.rider.name}</p>
                        <small class="text-muted">${ride.rider.type}</small>
                    </div>
                    ${matchHtml}
                </div>

                <div class="car-info-bar cursor-pointer hover-scale" onclick="event.stopPropagation(); RideSearch.showProfileInfo(${JSON.stringify(ride.vehicle).replace(/"/g, '&quot;')}, 'vehicle')">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <span class="fw-bold small"><i class="bi bi-car-front-fill me-2"></i>${ride.vehicle.model}</span>
                        <span class="text-success small fw-bold">${ride.available_seats} / ${ride.total_seats} Seats Left</span>
                    </div>
                    <div class="passenger-img-stack">
                        ${passengersHtml}
                    </div>
                </div>

                <div class="footer-bar">
                    <div class="small">
                        <div class="d-flex align-items-center">
                            <span class="text-muted small"><i class="bi bi-clock me-1"></i>${timeInfo}</span>
                            <span class="mx-2 text-silver">|</span>
                            <span class="fw-bold text-dark small">${ride.ride_type.toUpperCase()}</span>
                            ${ride.ac_available ? '<span class="ms-2 badge bg-primary-subtle text-primary border-0 rounded-pill" style="font-size: 0.6rem;">AC</span>' : ''}
                        </div>
                        ${timeLeftHtml}
                    </div>
                    <div class="text-end">
                        <button class="btn btn-dark btn-sm rounded-pill px-4 mb-1" onclick="RideSearch.selectRide(${ride.id})">
                            Join Ride <i class="bi bi-arrow-right ms-1"></i>
                        </button>
                        <div class="small fw-bold text-success" style="font-size: 0.8rem;">
                            Est. Fare: ৳${ride.price}
                        </div>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });
    },

    showProfileInfo(data, type) {
        const modalEl = document.getElementById('infoModal');
        if (!modalEl) return;

        // Use new instance to ensure clean config (fixes backdrop error)
        const modal = new bootstrap.Modal(modalEl);

        // Reset & Get elements
        const nameEl = document.getElementById('infoName');
        const roleEl = document.getElementById('infoRole');
        const avatarEl = document.getElementById('infoAvatar');
        const metaEl = document.getElementById('infoMeta');
        const docSection = document.getElementById('infoDocSection');
        const docImage = document.getElementById('infoDocImage');
        const docLabel = document.getElementById('infoDocLabel');

        if (docSection) docSection.classList.add('d-none');

        if (type === 'vehicle') {
            nameEl.textContent = data.model || "Vehicle";
            roleEl.textContent = "Vehicle Information";
            avatarEl.innerHTML = `<i class="bi bi-car-front-fill" style="font-size: 2rem;"></i>`;

            metaEl.innerHTML = `
                <div class="col-6"><div class="bg-light p-2 rounded-3"><div class="x-small text-muted fw-bold text-uppercase">Plate No</div><div class="fw-bold small">${data.plate_no || 'N/A'}</div></div></div>
                <div class="col-6"><div class="bg-light p-2 rounded-3"><div class="x-small text-muted fw-bold text-uppercase">Capacity</div><div class="fw-bold small">${data.capacity || '4'} Persons</div></div></div>
            `;

            if (data.photo || data.tax_token_photo) {
                docSection.classList.remove('d-none');
                docImage.src = data.photo || data.tax_token_photo;
                docLabel.textContent = "Vehicle Document / Tax Token";
            }
        } else {
            nameEl.textContent = data.name;
            let roleText = 'Student Passenger';
            if (data.is_host && data.is_owner) roleText = 'Host & Vehicle Owner';
            else if (data.is_host) roleText = 'Ride Host';
            else if (data.is_owner) roleText = 'Vehicle Owner';
            else if (type === 'rider') roleText = data.type || 'Community Rider';

            roleEl.textContent = roleText;

            if (data.photo) {
                avatarEl.innerHTML = `<img src="${data.photo}" class="w-100 h-100 object-fit-cover rounded-3 shadow-sm">`;
            } else {
                avatarEl.textContent = data.name.charAt(0).toUpperCase();
            }

            const idLabel = (type === 'rider') ? 'LICENSE' : 'ID NO';
            const idVal = (type === 'rider') ? (data.license_no || 'Community ID') : (data.id_no || 'Student ID');

            metaEl.innerHTML = `
                <div class="col-6"><div class="bg-light p-2 rounded-3"><div class="x-small text-muted fw-bold text-uppercase">${idLabel}</div><div class="fw-bold small">${idVal}</div></div></div>
                <div class="col-6"><div class="bg-light p-2 rounded-3"><div class="x-small text-muted fw-bold text-uppercase">CONTACT</div><div class="fw-bold small">${data.phone || 'N/A'}</div></div></div>
            `;

            const docPic = (type === 'rider') ? data.license_picture : data.id_photo;
            if (docPic) {
                docSection.classList.remove('d-none');
                docImage.src = docPic;
                docLabel.textContent = (type === 'rider') ? "Driving License" : "Verification ID";
            }
        }

        modal.show();
    },

    selectRide(id) {
        showToast("Joining ride...", "info");
        const hasVehicle = this.filters.hasVehicle ? 'true' : 'false';
        setTimeout(() => {
            navigateTo(`confirm_ride_student?ride_id=${id}&has_vehicle=${hasVehicle}`);
        }, 800);
    }
};

window.selectFilter = async (category, value, element) => {
    // Condition to freeze AC
    const isFrozenAC = category === 'ac' && (RideSearch.filters.ride_type === 'bike' || (RideSearch.filters.hasVehicle && window.studentHasVehicle));
    const isFrozenRideType = category === 'ride_type' && RideSearch.filters.hasVehicle && window.studentHasVehicle;

    if (isFrozenAC) {
        showToast('AC Filter cannot be changed.', 'warning');
        return;
    }

    if (isFrozenRideType) {
        showToast('Ride type is fixed to your vehicle.', 'warning');
        return;
    }

    // 1. UI: Update selected state within that specific row (parent) only
    const parent = element.parentElement;
    parent.querySelectorAll('.type-pill').forEach(pill => pill.classList.remove('selected'));
    element.classList.add('selected');

    // 2. State: Update the filter state
    RideSearch.filters[category] = value;
    if(category === 'ride_type') {
        appState.selectedRideType = value;
        saveState();
    }

    // 3. Persistence: Update DB if we have an active booking BEFORE fetching matching rides!
    const bId = (window.appState && appState.currentBookingId) || localStorage.getItem('last_booking_id');
    if (bId) {
        console.log("Syncing Pref to DB:", category, value);
        try {
            await window.RideBuddyAPI.call(routes['update_booking_preferences_api'], 'POST', {
                booking_id: bId,
                preferences: { [category]: value }
            });
        } catch (err) {
            console.error("Pref Sync Error:", err);
        }
    }

    // 4. Logic: Fetch new filtered results (after DB is synced)
    if (category === 'ride_type') {
        RideSearch.updateACFilterUI(); // Since ride type changed, AC might be disabled
    }
    RideSearch.fetchAndRender();
    showToast(`Filtering for ${value} ${category}...`, 'info');
};

window.toggleUserVehicle = (hasVehicle) => {
    // Only set true if student actually has a vehicle registered on server
    if (hasVehicle && !window.studentHasVehicle) {
        hasVehicle = false;
        const toggle = document.getElementById('userHasVehicleToggle');
        if (toggle) toggle.checked = false;
    }

    RideSearch.filters.hasVehicle = hasVehicle;
    localStorage.setItem('userHasVehicleWithMe', hasVehicle);

    let prefAC = 'any';
    let prefType = RideSearch.filters.ride_type;

    if (hasVehicle) {
        showToast('You are now set as a vehicle provider.', 'success');
        
        // Auto-select type based on vehicle
        if (typeof window.studentVehicleType !== 'undefined') {
            prefType = window.studentVehicleType.toLowerCase();
            RideSearch.filters.ride_type = prefType;
            if (window.appState) {
                appState.selectedRideType = prefType;
                saveState();
            }
        }

        // Freeze AC filter to match user's vehicle
        if (typeof window.studentVehicleAC !== 'undefined') {
            prefAC = window.studentVehicleAC ? 'true' : 'false';
            RideSearch.filters.ac = prefAC;
        }
    } else {
        showToast('Vehicle provider mode disabled.', 'info');
        RideSearch.filters.ac = 'any';
    }

    // Update DB
    const bId = (window.appState && appState.currentBookingId) || localStorage.getItem('last_booking_id');
    if (bId) {
        console.log("Syncing Toggle Pref to DB:", hasVehicle);
        window.RideBuddyAPI.call(routes['update_booking_preferences_api'], 'POST', {
            booking_id: bId,
            preferences: {
                hasVehicle: hasVehicle,
                ac: RideSearch.filters.ac,
                ride_type: RideSearch.filters.ride_type
            }
        }).catch(err => console.error("Pref Sync Error:", err));
    }

    const vOptions = document.getElementById('vehicleOptions');
    if (vOptions) {
        vOptions.style.display = hasVehicle ? 'block' : 'none';
        if (hasVehicle) vOptions.classList.add('animate-slide-up');
    }

    if (typeof RideSearch.updateRideTypeFilterUI === 'function') RideSearch.updateRideTypeFilterUI();
    RideSearch.updateACFilterUI();
    RideSearch.fetchAndRender();
};

RideSearch.updateACFilterUI = function () {
    const acContainer = document.getElementById('acFilterContainer');
    if (!acContainer) return;

    const pills = acContainer.querySelectorAll('.type-pill');
    let currentAcFilter = this.filters.ac;

    // Conditions to freeze
    const isFrozenDueToVehicle = this.filters.hasVehicle && window.studentHasVehicle;
    const isFrozenDueToBike = this.filters.ride_type === 'bike';
    const isFrozen = isFrozenDueToVehicle || isFrozenDueToBike;

    if (isFrozenDueToBike) {
        currentAcFilter = 'any';
        this.filters.ac = 'any';
    }

    pills.forEach(pill => {
        const onclickText = pill.getAttribute('onclick') || '';
        const matchesValue = onclickText.includes(`'${currentAcFilter}'`);

        if (matchesValue) {
            pill.classList.add('selected');
            pill.style.opacity = isFrozenDueToBike ? '0.4' : '1';
            pill.style.pointerEvents = isFrozen ? 'none' : 'auto';
        } else {
            pill.classList.remove('selected');
            if (isFrozen) {
                pill.style.opacity = '0.4';
                pill.style.pointerEvents = 'none';
            } else {
                pill.style.opacity = '1';
                pill.style.pointerEvents = 'auto';
            }
        }
    });
};

RideSearch.updateRideTypeFilterUI = function () {
    const container = document.getElementById('rideTypeFilterContainer');
    if (!container) return;

    const pills = container.querySelectorAll('.type-pill');
    const currentType = this.filters.ride_type;
    const isFrozen = this.filters.hasVehicle && window.studentHasVehicle;

    pills.forEach(pill => {
        const matchesValue = (pill.getAttribute('onclick') || '').includes(`'${currentType}'`);
        if (matchesValue) {
            pill.classList.add('selected');
            pill.style.opacity = '1';
            pill.style.pointerEvents = isFrozen ? 'none' : 'auto';
        } else {
            pill.classList.remove('selected');
            pill.style.opacity = isFrozen ? '0.4' : '1';
            pill.style.pointerEvents = isFrozen ? 'none' : 'auto';
        }
    });
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('studentRidePage')) {
        // Force vehicle provider to OFF by default
        localStorage.removeItem('userHasVehicleWithMe');
        const savedHasVehicle = false;
        RideSearch.filters.hasVehicle = savedHasVehicle;

        const toggle = document.getElementById('userHasVehicleToggle');
        if (toggle) toggle.checked = savedHasVehicle;

        // Apply initial freeze if needed
        if (savedHasVehicle && typeof window.studentVehicleAC !== 'undefined') {
            RideSearch.filters.ac = window.studentVehicleAC ? 'true' : 'false';
        }
        
        // Initialize ride type pill based on app state
        const rideTypeContainer = document.getElementById('rideTypeFilterContainer');
        if (rideTypeContainer) {
            const initialType = appState.selectedRideType || 'car';
            RideSearch.filters.ride_type = initialType;
            if (typeof RideSearch.updateRideTypeFilterUI === 'function') {
                RideSearch.updateRideTypeFilterUI();
            }
        }

        setTimeout(() => {
            RideSearch.updateACFilterUI();
            RideSearch.fetchAndRender(); // Initial load
        }, 100);

        // Auto-refresh every 15 seconds
        const refreshInterval = setInterval(() => {
            if (document.getElementById('studentRidePage')) {
                RideSearch.fetchAndRender();
            } else {
                clearInterval(refreshInterval);
            }
        }, 15000);
    }
});
