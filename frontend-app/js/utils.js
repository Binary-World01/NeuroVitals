// Global state management
const state = {
    currentUser: null,
    isAuthenticated: false
};

// Initialize auth state
function initAuth() {
    const user = localStorage.getItem('neurovitals_currentUser');
    if (user) {
        state.currentUser = JSON.parse(user);
        state.isAuthenticated = true;
    } else {
        state.currentUser = null;
        state.isAuthenticated = false;
    }
    return state.isAuthenticated;
}

/**
 * Fallback: IP-Based Geolocation (No permission popup required)
 */
async function getIPLocation() {
    try {
        const res = await fetch('https://ipapi.co/json/');
        const data = await res.json();
        if (data.error) throw new Error(data.reason);
        
        return {
            latitude: data.latitude,
            longitude: data.longitude,
            location_city: data.city || "Unknown",
            location_region: data.region || "Unknown",
            location_country: data.country_name || "Unknown",
            isFallback: true
        };
    } catch (e) {
        console.error("IP Geolocate failed:", e);
        return null;
    }
}

/**
 * Shared handler for location results (GPS or IP)
 */
async function handleLocationResult(locationData) {
    if (!locationData) return null;

    // Save to localStorage
    localStorage.setItem('neurovitals_location', JSON.stringify(locationData));

    // Sync to Supabase if logged in
    if (state.currentUser && typeof upsertUserProfile === 'function') {
        await upsertUserProfile({
            email: state.currentUser.email,
            ...locationData
        });
        
        // --- ADMIN SYNC (Outbreak Mapping - Anonymous) ---
        if (typeof syncToAdminTable === 'function') {
            await syncToAdminTable({
                ...locationData
            });
        }

        // Update local user object
        state.currentUser = { ...state.currentUser, ...locationData };
        localStorage.setItem('neurovitals_currentUser', JSON.stringify(state.currentUser));
    }

    return locationData;
}

/**
 * Capture user location once and persist to profile
 * @returns {Promise<Object>} - { lat, lon, city, country }
 */
async function captureAndSaveLocation() {
    // 1. Check if we already have it in localStorage
    const stored = localStorage.getItem('neurovitals_location');
    if (stored) {
        console.log("Using cached location.");
        return JSON.parse(stored);
    }

    // 2. Refresh current user to check profile for location
    initAuth();
    if (state.currentUser && state.currentUser.latitude) {
        const loc = {
            latitude: state.currentUser.latitude,
            longitude: state.currentUser.longitude,
            location_city: state.currentUser.location_city,
            location_region: state.currentUser.location_region,
            location_country: state.currentUser.location_country
        };
        localStorage.setItem('neurovitals_location', JSON.stringify(loc));
        return loc;
    }

    // 3. Request from browser
    return new Promise(async (resolve) => {
        if (!navigator.geolocation) {
            console.warn("Geolocation not supported. Trying IP fallback...");
            const ipLoc = await getIPLocation();
            resolve(handleLocationResult(ipLoc));
            return;
        }

        navigator.geolocation.getCurrentPosition(async (position) => {
            const { latitude, longitude } = position.coords;
            
            // Try to reverse geocode (Optional/Best Effort)
            let city = "Unknown", country = "Unknown", region = "Unknown", fullAddr = "Unknown";
            try {
                const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`);
                const data = await res.json();
                city = data.address.city || data.address.town || data.address.village || "Unknown";
                region = data.address.state || data.address.county || "Unknown";
                country = data.address.country || "Unknown";
                fullAddr = data.display_name || `${city}, ${country}`;
            } catch (e) { console.warn("Reverse geocode failed."); }

            const locationData = { 
                latitude, 
                longitude, 
                location_city: city, 
                location_region: region, 
                location_country: country,
                location: fullAddr
            };
            resolve(handleLocationResult(locationData));

        }, async (error) => {
            console.warn("Location access denied or failed. Trying IP fallback...", error);
            const ipLoc = await getIPLocation();
            if (ipLoc) {
                resolve(handleLocationResult(ipLoc));
            } else {
                showToast("Location access denied. Using network defaults.", "error");
                resolve(null);
            }
        }, { timeout: 8000 });
    });
}

/**
 * Force high-accuracy GPS capture for mission-critical reports
 */
async function getHighAccuracyLocation() {
    return new Promise((resolve) => {
        if (!navigator.geolocation) {
            resolve(getIPLocation());
            return;
        }

        navigator.geolocation.getCurrentPosition(
            async (pos) => {
                const { latitude, longitude } = pos.coords;
                const loc = { 
                    latitude, 
                    longitude, 
                    location_city: "Resolving...", 
                    location_region: "Resolving...", 
                    location_country: "Resolving...",
                    location: "Resolving exact address..."
                };
                localStorage.setItem('neurovitals_location', JSON.stringify(loc));
                resolve(loc);
            },
            async () => resolve(await getIPLocation()),
            { enableHighAccuracy: true, timeout: 8000, maximumAge: 10000 }
        );
    });
}

// Check if user is logged in and has completed onboarding
function requireAuth() {
    if (!initAuth()) {
        window.location.href = 'index.html';
        return false;
    }

    if (!state.currentUser.onboardingComplete) {
        window.location.href = 'onboarding.html';
        return false;
    }

    return true;
}

// Get current user's name
function getUserName() {
    return state.currentUser?.profile?.name || state.currentUser?.name || 'User';
}

// Get user profile
function getUserProfile() {
    return state.currentUser?.profile || {};
}

// Logout function
function logout() {
    localStorage.removeItem('neurovitals_currentUser');
    window.location.href = 'index.html';
}

/**
 * Get the standardized API Base URL
 * Detects local vs production vs relative environments
 */
function getApiBase() {
    // If we're on localhost or 127.0.0.1, prioritize the local port 8000
    if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
        return "http://localhost:8000/api";
    }
    // Fallback to relative path which is default for Render/Vercel hosted apps
    return "/api";
}

// API configuration
const API_BASE = getApiBase();
window.getApiBase = getApiBase; // Export to global scope for other scripts

// API helper functions
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        if (!response.ok) {
            throw new Error(`API call failed: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Show loading state
function showLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="flex flex-col items-center justify-center py-16">
                <div class="spinner mb-4"></div>
                <p class="text-slate-400">Loading...</p>
            </div>
        `;
    }
}

// Show error state
function showError(containerId, message) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="flex flex-col items-center justify-center py-16 text-center">
                <span class="material-symbols-outlined text-5xl text-red-400 mb-4">error</span>
                <p class="text-red-400 font-bold mb-2">Error</p>
                <p class="text-slate-400">${message}</p>
            </div>
        `;
    }
}

// Simple toast notification
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `fixed top-6 right-6 z-[9999] px-6 py-4 rounded-xl shadow-2xl animate-slide-in ${type === 'success' ? 'bg-green-500' : 'bg-red-500'
        } text-white font-bold`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Add spinner CSS if not already present
if (!document.querySelector('style#global-spinner')) {
    const style = document.createElement('style');
    style.id = 'global-spinner';
    style.textContent = `
        .spinner {
            border: 3px solid rgba(255, 255, 255, 0.1);
            border-top-color: #667eea;
            border-radius: 50%;
            width: 32px;
            height: 32px;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        @keyframes slide-in {
            from { opacity: 0; transform: translateX(100px); }
            to { opacity: 1; transform: translateX(0); }
        }
        .animate-slide-in {
            animation: slide-in 0.3s ease;
        }
    `;
    document.head.appendChild(style);
}
