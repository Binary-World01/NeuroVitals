/**
 * Google Fit API Integration — Neuro-Vitals
 * Complete OAuth 2.0 implementation with fixed sleep data
 */
const GoogleFitAPI = (() => {
    // ─── CONFIG (Fetched from Backend) ──────────────────────────────────────────
    let CLIENT_ID = '';
    const REDIRECT_URI = window.location.origin + '/integrations.html';

    /**
     * INITIALIZATION
     * Fetches the public client configuration from the backend.
     */
    async function init() {
        try {
            const resp = await fetch('/api/config/google-fit');
            const config = await resp.json();
            CLIENT_ID = config.client_id;
            console.log('✅ [GoogleFit] Config initialized from backend');
            return true;
        } catch (err) {
            console.error('❌ [GoogleFit] Failed to fetch config:', err);
            return false;
        }
    }

    const SCOPES = [
        'https://www.googleapis.com/auth/fitness.activity.read',
        'https://www.googleapis.com/auth/fitness.heart_rate.read',
        'https://www.googleapis.com/auth/fitness.sleep.read',
        'https://www.googleapis.com/auth/fitness.body.read',
    ].join(' ');

    const FIT_API = 'https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate';
    const TOKEN_URL = 'https://oauth2.googleapis.com/token';
    const USERINFO_URL = 'https://www.googleapis.com/oauth2/v3/userinfo';

    // ─── STATE ─────────────────────────────────────────────────────────────────
    let accessToken = null;
    let refreshToken = null;
    let pollInterval = null;
    let isConnected = false;
    let userEmail = null;

    // ─── TOKEN PERSISTENCE ────────────────────────────────────────────────────
    function saveTokens(accessToken, refreshToken, expiresIn) {
        const tokenData = {
            access_token: accessToken,
            refresh_token: refreshToken,
            expiry: Date.now() + (expiresIn * 1000),
            created: Date.now(),
            email: userEmail
        };
        localStorage.setItem('gfit_tokens', JSON.stringify(tokenData));
        console.log('✓ Tokens saved to localStorage');
    }

    function loadTokens() {
        const tokenData = localStorage.getItem('gfit_tokens');
        if (!tokenData) return false;

        try {
            const tokens = JSON.parse(tokenData);

            if (tokens.expiry > Date.now()) {
                accessToken = tokens.access_token;
                refreshToken = tokens.refresh_token;
                userEmail = tokens.email;
                console.log('✓ Restored previous session');
                return true;
            } else {
                console.log('Token expired, attempting refresh...');
                if (tokens.refresh_token) {
                    refreshAccessToken(tokens.refresh_token);
                }
                return false;
            }
        } catch (e) {
            console.log('Failed to load tokens');
            return false;
        }
    }

    async function refreshAccessToken(oldRefreshToken) {
        try {
            console.log('Refreshing access token...');

            const response = await fetch('/api/config/google-fit/refresh', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({
                    refresh_token: oldRefreshToken
                })
            });

            if (!response.ok) throw new Error('Refresh failed');

            const data = await response.json();
            accessToken = data.access_token;
            saveTokens(accessToken, oldRefreshToken, data.expires_in);
            console.log('✓ Token refreshed successfully');
            getUserInfoAndStart();

        } catch (error) {
            console.log(`Token refresh failed: ${error.message}`);
            localStorage.removeItem('gfit_tokens');
        }
    }

    // ─── HELPERS ───────────────────────────────────────────────────────────────
    function log(msg, colorClass = 'text-slate-400') {
        const consoleOut = document.getElementById('consoleOutput');
        if (!consoleOut) return;
        const div = document.createElement('div');
        div.className = `mb-1 font-mono text-xs ${colorClass}`;
        div.innerText = `> ${msg}`;
        consoleOut.appendChild(div);
        consoleOut.scrollTop = consoleOut.scrollHeight;
        if (consoleOut.children.length > 60) consoleOut.removeChild(consoleOut.firstChild);
        console.log(msg); // Also log to browser console
    }

    function logDataRow(data) {
        const consoleOut = document.getElementById('consoleOutput');
        if (!consoleOut) return;
        const time = new Date().toISOString().split('T')[1].replace('Z', '');
        const div = document.createElement('div');
        div.className = 'mb-1 font-mono text-[10px] md:text-xs border-l-2 border-transparent hover:border-white/20 pl-2 transition-all';

        const stepsDisplay = data.steps != null ? data.steps.toLocaleString() : '—';
        const hrDisplay = data.heartRate != null ? `${data.heartRate} bpm` : '—';
        const sleepDisplay = data.sleepHours != null ? `${data.sleepHours}h` : '—';
        const calDisplay = data.calories != null ? `${data.calories} kcal` : '—';

        div.innerHTML = `
            <span class="text-slate-600">[${time}]</span>
            <span class="text-green-400 font-bold"> GOOGLE_FIT</span>
            <span class="text-slate-500"> :: </span>
            <span class="text-slate-500">{</span>
            <span class="text-primary"> HR:${hrDisplay}</span>,
            <span class="text-accent-cyan"> STEPS:${stepsDisplay}</span>,
            <span class="text-purple-400"> SLEEP:${sleepDisplay}</span>,
            <span class="text-yellow-400"> CAL:${calDisplay}</span>
            <span class="text-slate-500"> }</span>
            <span class="text-green-500 bg-green-500/10 px-1 rounded ml-1">LIVE</span>
        `;
        consoleOut.appendChild(div);
        consoleOut.scrollTop = consoleOut.scrollHeight;
        if (consoleOut.children.length > 60) consoleOut.removeChild(consoleOut.firstChild);
    }

    // ─── CHECK FOR AUTHORIZATION CODE IN URL ─────────────────────────────────
    function handleOAuthRedirect() {
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const error = urlParams.get('error');

        if (error) {
            log(`OAuth Error: ${error}`, 'text-red-400');
            return false;
        }

        if (code) {
            log('Authorization code received, exchanging for token...', 'text-blue-400');
            exchangeCodeForToken(code);
            return true;
        }
        return false;
    }

    // ─── EXCHANGE CODE FOR TOKEN ─────────────────────────────────────────────
    async function exchangeCodeForToken(code) {
        try {
            log('Exchanging code for token...', 'text-blue-400');

            const response = await fetch('/api/config/google-fit/exchange', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    code: code,
                    redirect_uri: REDIRECT_URI
                })
            });

            if (!response.ok) {
                const errorData = await response.text();
                log(`Token exchange failed: ${response.status} - ${errorData}`, 'text-red-400');
                throw new Error('Token exchange failed');
            }

            const tokenData = await response.json();
            accessToken = tokenData.access_token;
            refreshToken = tokenData.refresh_token;

            log('✓ OAuth successful! Access token received', 'text-green-400');

            window.history.replaceState({}, document.title, window.location.pathname);
            await getUserInfoAndStart();

            if (userEmail) {
                saveTokens(accessToken, refreshToken, tokenData.expires_in);
            }

        } catch (error) {
            log(`Token exchange error: ${error.message}`, 'text-red-400');
        }
    }

    // ─── GET USER INFO AND START ─────────────────────────────────────────────
    async function getUserInfoAndStart() {
        try {
            const response = await fetch(USERINFO_URL, {
                headers: { 'Authorization': `Bearer ${accessToken}` }
            });

            if (response.ok) {
                const userInfo = await response.json();
                userEmail = userInfo.email || 'unknown';
                log(`Authenticated as ${userEmail}`, 'text-blue-400');
                localStorage.setItem('gfit_email', userEmail);
            }

        } catch (error) {
            log(`Could not get user info: ${error.message}`, 'text-yellow-400');
            userEmail = 'unknown';
        }

        setConnectedState(userEmail);

        // Fetch initial data and start polling
        const data = await fetchAllData();
        updateUIBasedOnData(data);
        logDataRow(data);
        await saveToDatabase(data);
        startPolling();
    }

    // ─── API FETCH ─────────────────────────────────────────────────────────────
    async function fetchAggregate(body) {
        if (!accessToken) {
            throw new Error('No access token');
        }

        const res = await fetch(FIT_API, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body),
        });

        if (res.status === 401) {
            log('Token expired, attempting refresh...', 'text-yellow-400');
            const tokens = JSON.parse(localStorage.getItem('gfit_tokens') || '{}');
            if (tokens.refresh_token) {
                await refreshAccessToken(tokens.refresh_token);
                return fetchAggregate(body);
            }
        }

        if (!res.ok) throw new Error(`Fit API ${res.status}: ${res.statusText}`);
        return res.json();
    }

    // ─── FETCH SLEEP DATA (SPECIFIC FIX) ─────────────────────────────────────
    async function fetchSleepData() {
        try {
            const now = Date.now();
            const startOfWeek = now - (7 * 24 * 60 * 60 * 1000); // 7 days ago

            log('Fetching sleep data...', 'text-blue-400');

            const response = await fetchAggregate({
                aggregateBy: [
                    {
                        dataTypeName: 'com.google.sleep.segment',
                        dataSourceId: 'derived:com.google.sleep.segment:com.google.android.gms:merged'
                    }
                ],
                bucketByTime: { durationMillis: String(24 * 60 * 60 * 1000) },
                startTimeMillis: String(startOfWeek),
                endTimeMillis: String(now),
            });

            if (!response.bucket || response.bucket.length === 0) {
                log('No sleep buckets found', 'text-yellow-400');
                return null;
            }

            let totalSleepMs = 0;
            let daysWithSleep = 0;

            response.bucket.forEach((bucket, index) => {
                const points = bucket.dataset?.[0]?.point || [];

                if (points.length > 0) {
                    let daySleepMs = 0;

                    points.forEach(point => {
                        // Sleep segments have start and end times in nanoseconds
                        const startNanos = point.startTimeNanos;
                        const endNanos = point.endTimeNanos;

                        if (startNanos && endNanos) {
                            const durationMs = (parseInt(endNanos) - parseInt(startNanos)) / 1e6;
                            daySleepMs += durationMs;

                            // Log each sleep segment for debugging
                            const sleepType = point.value?.[0]?.intVal;
                            const typeName = sleepType === 1 ? 'Light' : sleepType === 2 ? 'Deep' : sleepType === 3 ? 'REM' : 'Unknown';

                            log(`Sleep segment: ${typeName} - ${(durationMs / (1000 * 60 * 60)).toFixed(2)}h`, 'text-slate-400');
                        }
                    });

                    if (daySleepMs > 0) {
                        totalSleepMs += daySleepMs;
                        daysWithSleep++;
                        log(`Day ${index + 1}: ${(daySleepMs / (1000 * 60 * 60)).toFixed(2)}h sleep`, 'text-green-400');
                    }
                }
            });

            if (totalSleepMs > 0 && daysWithSleep > 0) {
                const avgSleepHours = (totalSleepMs / daysWithSleep) / (1000 * 60 * 60);
                const formattedSleep = avgSleepHours.toFixed(1);
                log(`✓ Average sleep: ${formattedSleep}h over ${daysWithSleep} days`, 'text-green-400');
                return formattedSleep;
            } else {
                log('No sleep data found in the last 7 days', 'text-yellow-400');

                // Try alternative data source
                return await fetchAlternativeSleepData();
            }

        } catch (error) {
            log(`Sleep data error: ${error.message}`, 'text-red-400');
            return null;
        }
    }

    // ─── ALTERNATIVE SLEEP DATA FETCH ────────────────────────────────────────
    async function fetchAlternativeSleepData() {
        try {
            const now = Date.now();
            const startOfWeek = now - (7 * 24 * 60 * 60 * 1000);

            log('Trying alternative sleep data source...', 'text-blue-400');

            const response = await fetchAggregate({
                aggregateBy: [
                    {
                        dataTypeName: 'com.google.sleep.segment'
                    }
                ],
                bucketByTime: { durationMillis: String(24 * 60 * 60 * 1000) },
                startTimeMillis: String(startOfWeek),
                endTimeMillis: String(now),
            });

            if (!response.bucket) return null;

            let totalSleepMs = 0;
            let daysWithSleep = 0;

            response.bucket.forEach(bucket => {
                const points = bucket.dataset?.[0]?.point || [];
                if (points.length > 0) {
                    let daySleepMs = 0;
                    points.forEach(point => {
                        if (point.startTimeNanos && point.endTimeNanos) {
                            daySleepMs += (parseInt(point.endTimeNanos) - parseInt(point.startTimeNanos)) / 1e6;
                        }
                    });
                    if (daySleepMs > 0) {
                        totalSleepMs += daySleepMs;
                        daysWithSleep++;
                    }
                }
            });

            if (totalSleepMs > 0 && daysWithSleep > 0) {
                const avgSleepHours = (totalSleepMs / daysWithSleep) / (1000 * 60 * 60);
                return avgSleepHours.toFixed(1);
            }

            return null;

        } catch (error) {
            log(`Alternative sleep fetch failed: ${error.message}`, 'text-red-400');
            return null;
        }
    }

    // ─── FETCH ALL DATA ───────────────────────────────────────────────────────
    async function fetchAllData() {
        const now = Date.now();
        const startOfDay = new Date();
        startOfDay.setHours(0, 0, 0, 0);
        const startOfWeek = now - (7 * 24 * 60 * 60 * 1000);

        log('Fetching all Google Fit data...', 'text-blue-400');

        const results = { steps: 0, heartRate: null, calories: 0, sleepHours: null };

        // 1. Steps
        try {
            const stepsRes = await fetchAggregate({
                aggregateBy: [{ dataTypeName: 'com.google.step_count.delta' }],
                bucketByTime: { durationMillis: String(24 * 60 * 60 * 1000) },
                startTimeMillis: String(startOfDay.getTime()),
                endTimeMillis: String(now),
            });

            if (stepsRes.bucket) {
                results.steps = stepsRes.bucket.reduce((sum, b) => {
                    return sum + (b.dataset?.[0]?.point || []).reduce((s, p) => {
                        return s + (p.value?.[0]?.intVal || 0);
                    }, 0);
                }, 0);
                log(`Steps today: ${results.steps}`, 'text-green-400');
            }
        } catch (e) {
            log(`Steps error: ${e.message}`, 'text-red-400');
        }

        // 2. Heart Rate
        try {
            const hrRes = await fetchAggregate({
                aggregateBy: [{ dataTypeName: 'com.google.heart_rate.bpm' }],
                bucketByTime: { durationMillis: String(60 * 60 * 1000) },
                startTimeMillis: String(now - (24 * 60 * 60 * 1000)),
                endTimeMillis: String(now),
            });

            if (hrRes.bucket) {
                for (const b of hrRes.bucket.reverse()) {
                    const pts = b.dataset?.[0]?.point || [];
                    if (pts.length > 0) {
                        const latest = pts[pts.length - 1];
                        results.heartRate = Math.round(latest.value?.[0]?.fpVal || 0);
                        log(`Latest heart rate: ${results.heartRate} bpm`, 'text-green-400');
                        break;
                    }
                }
            }
        } catch (e) {
            log(`Heart rate error: ${e.message}`, 'text-red-400');
        }

        // 3. Sleep (using dedicated function)
        results.sleepHours = await fetchSleepData();

        // 4. Calories
        try {
            const calRes = await fetchAggregate({
                aggregateBy: [{ dataTypeName: 'com.google.calories.expended' }],
                bucketByTime: { durationMillis: String(24 * 60 * 60 * 1000) },
                startTimeMillis: String(startOfDay.getTime()),
                endTimeMillis: String(now),
            });

            if (calRes.bucket) {
                results.calories = Math.round(calRes.bucket.reduce((sum, b) => {
                    return sum + (b.dataset?.[0]?.point || []).reduce((s, p) => {
                        return s + (p.value?.[0]?.fpVal || 0);
                    }, 0);
                }, 0));
                log(`Calories today: ${results.calories}`, 'text-green-400');
            }
        } catch (e) {
            log(`Calories error: ${e.message}`, 'text-red-400');
        }

        return results;
    }

    // ─── UPDATE UI ─────────────────────────────────────────────────────────────
    function updateUIBasedOnData(data) {
        const stepsEl = document.getElementById('gfit-steps');
        const hrEl = document.getElementById('gfit-hr');
        const sleepEl = document.getElementById('gfit-sleep');
        const caloriesEl = document.getElementById('gfit-calories');

        if (stepsEl && data.steps) {
            stepsEl.textContent = data.steps.toLocaleString();
            stepsEl.style.color = '#34d399';
            setTimeout(() => { stepsEl.style.color = ''; }, 600);
        }

        if (hrEl && data.heartRate) {
            hrEl.textContent = `${data.heartRate} bpm`;
            hrEl.style.color = '#34d399';
            setTimeout(() => { hrEl.style.color = ''; }, 600);
        }

        if (sleepEl && data.sleepHours) {
            sleepEl.textContent = `${data.sleepHours}h`;
            sleepEl.style.color = '#34d399';
            setTimeout(() => { sleepEl.style.color = ''; }, 600);
            log(`✓ Sleep displayed: ${data.sleepHours}h`, 'text-green-400');
        } else if (sleepEl) {
            sleepEl.textContent = '—';
        }

        if (caloriesEl && data.calories) {
            caloriesEl.textContent = `${data.calories} kcal`;
            caloriesEl.style.color = '#34d399';
            setTimeout(() => { caloriesEl.style.color = ''; }, 600);
        }

        const packetRate = document.getElementById('packetRate');
        if (packetRate && data.heartRate) {
            packetRate.textContent = (data.heartRate * 12 + Math.floor(Math.random() * 50)).toLocaleString();
        }

        const panel = document.getElementById('gfitLivePanel');
        if (panel) {
            panel.classList.remove('hidden');
        }
    }

    // ─── SAVE TO DATABASE ─────────────────────────────────────────────────────
    async function saveToDatabase(data) {
        const currentUser = JSON.parse(localStorage.getItem('neurovitals_currentUser') || '{}');
        const email = userEmail || currentUser.email || localStorage.getItem('gfit_email') || 'unknown@user.com';

        const payload = {
            user_email: email,
            steps: data.steps || 0,
            heart_rate: data.heartRate || 0,
            sleep_hours: data.sleepHours ? parseFloat(data.sleepHours) : 0,
            calories: data.calories || 0,
            source: 'google_fit',
            recorded_at: new Date().toISOString()
        };

        try {
            const response = await fetch('/api/vitals/save-vitals', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                log('✓ Data saved to database', 'text-green-400');
            }
        } catch (error) {
            log(`⚠️ Database error: ${error.message}`, 'text-yellow-400');
        }

        localStorage.setItem('gfit_live_data', JSON.stringify({
            heartRate: data.heartRate,
            steps: data.steps,
            sleepHours: data.sleepHours,
            calories: data.calories,
            updatedAt: new Date().toISOString()
        }));
    }

    function setConnectedState(email) {
        isConnected = true;
        window.isConnected = true;

        const badge = document.getElementById('connectionBadge');
        if (badge) {
            badge.className = 'flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/20 border border-green-500/30 transition-all duration-300 shadow-[0_0_15px_rgba(34,197,94,0.3)]';
            badge.innerHTML = `<span class="material-symbols-rounded text-green-400 text-sm animate-pulse">wifi</span><span class="text-xs font-bold text-green-400">LIVE FEED</span>`;
        }

        const dot = document.getElementById('systemStatusDot');
        if (dot) dot.className = 'w-2 h-2 rounded-full bg-green-500 animate-pulse';

        const statusTxt = document.getElementById('systemStatusText');
        if (statusTxt) {
            statusTxt.className = 'text-xs font-mono text-green-400';
            statusTxt.innerText = 'LIVE';
        }

        const deviceCount = document.getElementById('activeDeviceCount');
        if (deviceCount) deviceCount.innerText = '1';

        const packetIcon = document.getElementById('packetIcon');
        if (packetIcon) packetIcon.className = 'w-10 h-10 rounded-full bg-accent-cyan/10 flex items-center justify-center text-accent-cyan';

        const packetRate = document.getElementById('packetRate');
        if (packetRate) packetRate.className = 'text-2xl font-display font-bold text-accent-cyan';

        const panel = document.getElementById('gfitLivePanel');
        if (panel) {
            panel.classList.remove('hidden');
            panel.style.animation = 'gfit-slide-in 0.5s forwards';
        }

        const btn = document.getElementById('gfitConnectBtn');
        if (btn) {
            const displayName = email && email !== 'unknown' ? email.split('@')[0] : 'User';
            btn.innerHTML = `<span class="material-symbols-rounded text-sm">check_circle</span> Connected as ${displayName}`;
            btn.className = 'w-full py-3 rounded-xl bg-green-500/20 border border-green-500/50 text-green-400 text-sm font-bold transition-all flex items-center justify-center gap-2 cursor-default';
        }
    }

    // ─── POLLING ──────────────────────────────────────────────────────────────
    async function startPolling() {
        if (pollInterval) clearInterval(pollInterval);

        const doFetch = async () => {
            try {
                const data = await fetchAllData();
                updateUIBasedOnData(data);
                logDataRow(data);
                await saveToDatabase(data);
            } catch (err) {
                log(`Polling error: ${err.message}`, 'text-red-400');
            }
        };

        await doFetch();
        pollInterval = setInterval(doFetch, 30000);
    }

    // ─── PUBLIC METHODS ───────────────────────────────────────────────────────
    function connect() {
        if (isConnected) {
            log('Already connected to Google Fit.', 'text-yellow-400');
            return;
        }

        log('Redirecting to Google for authorization...', 'text-blue-400');

        const btn = document.getElementById('gfitConnectBtn');
        if (btn) {
            btn.innerHTML = `<span class="material-symbols-rounded animate-spin text-sm">sync</span> Redirecting...`;
        }

        const authUrl = 'https://accounts.google.com/o/oauth2/v2/auth?' + new URLSearchParams({
            client_id: CLIENT_ID,
            redirect_uri: REDIRECT_URI,
            response_type: 'code',
            scope: SCOPES,
            access_type: 'offline',
            prompt: 'consent',
            include_granted_scopes: 'true'
        });

        window.location.href = authUrl;
    }

    function disconnect() {
        if (pollInterval) clearInterval(pollInterval);
        accessToken = null;
        refreshToken = null;
        isConnected = false;
        window.isConnected = false;
        userEmail = null;

        localStorage.removeItem('gfit_tokens');
        localStorage.removeItem('gfit_email');
        localStorage.removeItem('gfit_live_data');

        const btn = document.getElementById('gfitConnectBtn');
        if (btn) {
            btn.innerHTML = `<span class="material-symbols-rounded text-xs">fitness_center</span> Connect Real API`;
            btn.disabled = false;
            btn.className = 'w-full py-3 rounded-xl bg-primary/20 hover:bg-primary/30 border border-primary/20 text-sm font-semibold text-primary transition-all flex items-center justify-center gap-2 group-hover:shadow-lg shadow-primary/10';
        }

        const panel = document.getElementById('gfitLivePanel');
        if (panel) panel.classList.add('hidden');

        const badge = document.getElementById('connectionBadge');
        if (badge) {
            badge.className = 'flex items-center gap-2 px-3 py-1 rounded-full bg-slate-500/10 border border-slate-500/20';
            badge.innerHTML = `<span class="material-symbols-rounded text-slate-500 text-sm">wifi_off</span><span class="text-xs font-bold text-slate-500">DISCONNECTED</span>`;
        }

        const dot = document.getElementById('systemStatusDot');
        if (dot) dot.className = 'w-2 h-2 rounded-full bg-slate-500';

        const statusTxt = document.getElementById('systemStatusText');
        if (statusTxt) {
            statusTxt.className = 'text-xs font-mono text-slate-400';
            statusTxt.innerText = 'DISCONNECTED';
        }

        const deviceCount = document.getElementById('activeDeviceCount');
        if (deviceCount) deviceCount.innerText = '0';

        const packetRate = document.getElementById('packetRate');
        if (packetRate) {
            packetRate.innerText = '0';
            packetRate.className = 'text-2xl font-display font-bold text-slate-500';
        }

        const packetIcon = document.getElementById('packetIcon');
        if (packetIcon) packetIcon.className = 'w-10 h-10 rounded-full bg-white/5 flex items-center justify-center text-slate-500';

        log('Disconnected from Google Fit.', 'text-yellow-400');
    }

    function init() {
        if (handleOAuthRedirect()) {
            return;
        }

        if (loadTokens()) {
            log('Restored previous session', 'text-blue-400');
            getUserInfoAndStart();
        }
    }

    return { connect, disconnect, init };
})();

window.GoogleFitAPI = GoogleFitAPI;

document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        GoogleFitAPI.init();
    }, 500);
});
