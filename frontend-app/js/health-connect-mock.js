/**
 * Google Health Connect Simulation
 * Mocks the authentication and data sync process for the hackathon demo.
 */

const HealthConnect = {
    isConnected: false,

    // Simulated Data Points
    mockData: {
        heartRate: [72, 75, 71, 68, 74, 78, 82, 79, 75, 72, 70, 68, 65, 69, 72, 76, 80, 85, 82, 78, 74, 71, 69, 67, 70, 73, 75, 77, 79, 81],
        sleep: [6.5, 7.0, 5.5, 6.0, 7.5, 8.0, 7.2, 6.8, 5.0, 6.2, 7.1, 7.8, 8.2, 7.5, 6.0, 5.8, 6.5, 7.0, 7.5, 8.0, 7.8, 6.5, 5.5, 6.0, 7.2, 7.5, 8.0, 7.8, 7.5, 7.2],
        steps: [3500, 4200, 3800, 5000, 4500, 6000, 8000, 7500, 4000, 3200, 5500, 6200, 7000, 6500, 4000, 3500, 5000, 8500, 9000, 7500, 6000, 4500, 3000, 4000, 5500, 6500, 7200, 8000, 8500, 9200]
    },

    // Trigger the connection flow
    connect: function () {
        if (this.isConnected) {
            alert("Already connected to Google Health Connect!");
            return;
        }

        // Show Modal
        const modal = document.getElementById('healthConnectModal');
        if (modal) modal.classList.remove('hidden');
        else if (typeof selectSimulation === 'function') {
            // If the specific modal doesn't exist, use the multi-source selector from the new UI
            selectSimulation();
        }
    },

    // Handle "Authorize" click
    authorize: function () {
        const btn = document.getElementById('authorizeBtn');
        const status = document.getElementById('syncStatus');
        const progressBar = document.getElementById('syncProgress');
        const progressContainer = document.getElementById('syncProgressContainer');

        // UI Loading State
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = `<span class="material-symbols-rounded animate-spin">sync</span> Connecting...`;
        }
        if (status) {
            status.innerText = "Requesting permissions from Google Account...";
            status.classList.remove('hidden');
        }

        // Simulate Delays
        setTimeout(() => {
            if (status) status.innerText = "Verifying OAuth2 credentials...";
        }, 1000);

        setTimeout(() => {
            if (status) status.innerText = "Fetching 30-day historical data...";
            if (progressContainer) progressContainer.classList.remove('hidden');

            // Animate Progress Bar
            let width = 0;
            const interval = setInterval(() => {
                if (width >= 100) {
                    clearInterval(interval);
                    this.completeSync();
                } else {
                    width += 5;
                    if (progressBar) progressBar.style.width = width + '%';
                }
            }, 100);

        }, 2500);
    },

    // Finalize Sync
    completeSync: function () {
        this.isConnected = true;

        // Hide Modal
        setTimeout(() => {
            const modal = document.getElementById('healthConnectModal');
            if (modal) modal.classList.add('hidden');
            this.updateDashboard();
        }, 500);
    },

    // Update the UI with "Real" Data
    updateDashboard: function () {
        // 1. Update Connection Status Badge
        const badge = document.getElementById('healthConnectBadge');
        if (badge) {
            badge.innerHTML = `<span class="material-symbols-rounded text-green-500">check_circle</span> synced`;
            badge.className = "px-3 py-1 rounded-full bg-green-500/10 text-green-500 text-xs font-bold border border-green-500/20 flex items-center gap-1";
        }

        // 2. Update Stability Score (Improve it to show benefit of data)
        const scoreElement = document.getElementById('stabilityScore');
        if (scoreElement) {
            this.animateValue(scoreElement, 96.4, 98.2, 2000);
        }

        // 3. Populate "Active Neural Protocols" with real data sources
        const protocols = document.getElementById('activeProtocolsList');
        if (protocols) {
            protocols.innerHTML = `
                <div class="flex items-center justify-between p-3 rounded-xl bg-green-500/5 border border-green-500/10 animate-slide-in">
                    <div class="flex items-center gap-3">
                        <span class="material-symbols-rounded text-green-500 bg-green-500/20 p-1 rounded-lg">directions_walk</span>
                        <div>
                            <p class="text-xs font-bold text-white">Physical Activity</p>
                            <p class="text-[10px] text-slate-400">Source: Google Fit</p>
                        </div>
                    </div>
                    <span class="text-xs font-black text-white">9,200 steps</span>
                </div>
                <div class="flex items-center justify-between p-3 rounded-xl bg-accent-blue/5 border border-accent-blue/10 animate-slide-in" style="animation-delay: 0.1s">
                    <div class="flex items-center gap-3">
                        <span class="material-symbols-rounded text-accent-blue bg-accent-blue/20 p-1 rounded-lg">bedtime</span>
                        <div>
                            <p class="text-xs font-bold text-white">Sleep Quality</p>
                            <p class="text-[10px] text-slate-400">Source: Health Connect</p>
                        </div>
                    </div>
                    <span class="text-xs font-black text-white">7h 12m</span>
                </div>
                <div class="flex items-center justify-between p-3 rounded-xl bg-red-500/5 border border-red-500/10 animate-slide-in" style="animation-delay: 0.2s">
                    <div class="flex items-center gap-3">
                        <span class="material-symbols-rounded text-red-500 bg-red-500/20 p-1 rounded-lg">favorite</span>
                        <div>
                            <p class="text-xs font-bold text-white">Heart Rate Variability</p>
                            <p class="text-[10px] text-slate-400">Source: Pixel Watch</p>
                        </div>
                    </div>
                    <span class="text-xs font-black text-white">42ms</span>
                </div>
            `;
        }

        // 4. Show Notification (Optional toggle)
        console.log("Success! 30 days of biometric data synced from Google Health Connect.");
    },

    // Helper to animate numbers
    animateValue: function (obj, start, end, duration) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            obj.innerHTML = (progress * (end - start) + start).toFixed(1) + "%";
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }
};

window.HealthConnect = HealthConnect;
