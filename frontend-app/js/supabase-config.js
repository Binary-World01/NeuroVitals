/**
 * Supabase Configuration — Neuro-Vitals (App)
 * Fetched dynamically from the backend to prevent secret leakage.
 */
(async () => {
    try {
        const resp = await fetch('/api/config/app-config');
        const config = await resp.json();
        
        const SUPABASE_URL = config.supabase_url;
        const SUPABASE_ANON_KEY = config.supabase_anon_key;
        
        if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
            console.error("❌ [Supabase] Config missing from backend");
            return;
        }

        const supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
        window.supabaseClient = supabaseClient;
        
        console.log("✅ [Supabase/App] Client initialized from backend config");
        window.dispatchEvent(new CustomEvent('supabaseReady', { detail: supabaseClient }));
        
    } catch (err) {
        console.error("❌ [Supabase/App] Initialization failed:", err);
    }
})();
