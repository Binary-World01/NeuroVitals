/**
 * Vitals Streamer - Minimal Placeholder
 * This script handles real-time vitals updates and emits events for the dashboard.
 */

const VitalsStreamer = {
    interval: null,
    
    start: function() {
        console.log("Vitals Streamer started...");
        this.interval = setInterval(() => {
            const data = JSON.parse(localStorage.getItem('gfit_live_data'));
            if (data) {
                window.dispatchEvent(new CustomEvent('vitalsUpdated', { detail: data }));
            }
        }, 1000);
    },
    
    stop: function() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
    }
};

// Start streaming if data exists
if (localStorage.getItem('gfit_live_data')) {
    VitalsStreamer.start();
}
