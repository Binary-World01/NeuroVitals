/**
 * Neuro-Vitals API Layer
 * Handles interactions with Google Gemini High-Performance AI
 */

const GEMINI_API_KEY = "YOUR_GOOGLE_GEMINI_API_KEY_HERE";
const GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent";

/**
 * Analyzes symptoms using Google Gemini Flash
 * @param {Object} data - Patient data (age, gender, symptoms, severity, history)
 * @returns {Promise<Object>} - Analysis result
 */

/**
 * Helper to clean AI response text (removes markdown code blocks)
 */
function cleanAndParseJSON(text) {
    try {
        // 1. Remove markdown code blocks
        let cleaned = text.replace(/```json/g, '').replace(/```/g, '').trim();

        // 2. Extract JSON object if there is extra text
        const firstBrace = cleaned.indexOf('{');
        const lastBrace = cleaned.lastIndexOf('}');

        if (firstBrace !== -1 && lastBrace !== -1) {
            cleaned = cleaned.substring(firstBrace, lastBrace + 1);
        }

        return JSON.parse(cleaned);
    } catch (e) {
        console.error("JSON Parse Error:", e);
        console.log("Failed Text:", text);
        return null;
    }
}

/**
 * Fetch wrapper with exponential backoff retry for 429/500 errors
 */
async function fetchWithRetry(url, options, retries = 3, backoff = 2000) {
    try {
        const response = await fetch(url, options);
        if (response.ok) return response;

        // Retry on Rate Limit (429) or Server Error (5xx)
        if (retries > 0 && (response.status === 429 || response.status >= 500)) {
            console.warn(`Retrying API call (${response.status})... Attempts left: ${retries}`);
            await new Promise(r => setTimeout(r, backoff));
            return fetchWithRetry(url, options, retries - 1, backoff * 2);
        }

        throw new Error(`API Error ${response.status}: ${await response.text()}`);
    } catch (e) {
        if (retries > 0) {
            console.warn(`Retrying network error... ${e.message}`);
            await new Promise(r => setTimeout(r, backoff));
            return fetchWithRetry(url, options, retries - 1, backoff * 2);
        }
        throw e;
    }
}

async function analyzeSymptoms(data) {
    try {
        console.log("🚀 [API] Routing symptom analysis through backend...");
        
        // Transform frontend data to match backend PatientProfile schema
        const backendData = {
            age: parseInt(data.age),
            gender: data.gender,
            symptoms: [
                {
                    description: data.symptoms,
                    severity: parseInt(data.severity),
                    duration_days: 1 // Default if not provided
                }
            ],
            medical_history: data.history ? [data.history] : [],
            current_medications: []
        };

        const response = await fetch("/api/diagnosis/analyze", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(backendData)
        });

        if (!response.ok) {
            throw new Error(`Backend Error: ${response.status}`);
        }

        const result = await response.json();
        
        // Map backend DiagnosisResult to frontend expected format
        return {
            diagnosis: result.primary_diagnosis,
            confidence: Math.round(result.confidence * 100),
            summary: result.reasoning[0] || "Analysis completed.",
            reasoning: result.reasoning.map((r, i) => ({
                icon: i === 0 ? "neurology" : (i === 1 ? "history" : "description"),
                title: `Observation ${i + 1}`,
                description: r
            })),
            recommendation: result.recommendations.join(". ")
        };

    } catch (error) {
        console.error("Analyze Error (Backend Redirect):", error);
        return {
            diagnosis: "Analysis Error",
            confidence: 0,
            summary: "Could not connect to backend analysis engine.",
            reasoning: [],
            recommendation: "Ensure backend is running and try again."
        };
    }
}


/**
 * Orchestrates the Adversarial Debate (Now routed through backend)
 * @param {Object} data - Patient data
 * @returns {Promise<Object>} - Prosecutor and Defense arguments
 */
async function generateAdversarialDebate(data) {
    try {
        console.log("🚀 [API] Routing adversarial debate through backend...");
        
        const backendData = {
            age: parseInt(data.age),
            gender: data.gender,
            symptoms: [
                {
                    description: data.symptoms,
                    severity: 3, // Default for debate
                    duration_days: 1
                }
            ],
            medical_history: data.history ? [data.history] : [],
            current_medications: []
        };

        const response = await fetch("/api/adversarial/debate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(backendData)
        });

        if (!response.ok) {
            throw new Error(`Backend Error: ${response.status}`);
        }

        const result = await response.json();
        
        // Cache the verdict for the next call to generateJudgeVerdict
        window._lastDebatResult = result;

        // Map back to expected format
        return {
            prosecutor: {
                diagnosis: result.prosecutor.diagnosis,
                confidence: result.prosecutor.confidence,
                points: result.prosecutor.points
            },
            defense: {
                diagnosis: result.defense.diagnosis,
                confidence: result.defense.confidence,
                points: result.defense.points
            }
        };

    } catch (error) {
        console.error("Adversarial Debate Error:", error);
        throw error;
    }
}

/**
 * JUDGE AI - Returns the verdict from the cached backend result
 */
async function generateJudgeVerdict(data, prosecutor, defense) {
    // If we have a cached result from the same session, use it
    if (window._lastDebatResult) {
        const v = window._lastDebatResult.verdict;
        return {
            verdict: v.verdict,
            confidence: v.confidence,
            synthesis: v.synthesis,
            next_step: v.next_step,
            highlights: v.highlights || []
        };
    }
    
    // Fallback if called directly without generateAdversarialDebate (unlikely)
    return {
        verdict: "Verdict Delayed",
        confidence: 0,
        synthesis: "The Judge requires a full debate to conclude.",
        next_step: "Restart the simulation."
    };
}

// Export for window global
window.neuroApi = {
    analyzeSymptoms,
    generateAdversarialDebate,
    generateJudgeVerdict
};
