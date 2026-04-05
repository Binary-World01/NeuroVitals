/**
 * Vitals Streamer - Real-time Data Relay
 * Handles the background polling of local/synced vitals and broadcasts 
 * them to the dashboard components via CustomEvents.
 */
class VitalsStreamer {
    constructor() {
        this.interval = null;
        this.refreshRate = 1000; // 1 second
    }

    init() {
        console.log("📡 Vitals Streamer Initializing...");
        this.start();
    }

    start() {
        if (this.interval) clearInterval(this.interval);
        
        this.interval = setInterval(() => {
            this.broadcast();
        }, this.refreshRate);
        
        // Initial broadcast
        this.broadcast();
    }

    broadcast() {
        try {
            const rawData = localStorage.getItem('gfit_live_data');
            if (!rawData) return;

            const data = JSON.parse(rawData);
            
            // Dispatch to window so dashboard listeners can pick it up
            window.dispatchEvent(new CustomEvent('vitalsUpdated', { 
                detail: data,
                bubbles: true,
                composed: true
            }));
            
        } catch (e) {
            console.warn("Vitals Streamer: Broadcast error", e);
        }
    }

    stop() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
            console.log("📡 Vitals Streamer Stopped.");
        }
    }
}

// Global instance check
if (typeof window !== 'undefined') {
    window.VitalsStreamer = VitalsStreamer;
}
