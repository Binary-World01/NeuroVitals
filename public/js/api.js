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


const GROQ_API_KEY = "YOUR_GROQ_API_KEY_HERE";
const GROQ_URL = "https://api.groq.com/openai/v1/chat/completions";

/**
 * Orchestrates the Adversarial Debate (Gemini vs Groq)
 * @param {Object} data - Patient data
 * @returns {Promise<Object>} - Prosecutor and Defense arguments
 */
async function generateAdversarialDebate(data) {
    // 1. PROSECUTOR (Gemini) - Argues for the most likely common diagnosis
    const prosecutorPrompt = `
        You are the 'Prosecutor AI' in a medical diagnosis debate.
        Patient: Age ${data.age}, ${data.gender}, Symptoms: "${data.symptoms}".
        
        Your Goal: aggressive advocacy for the MOST LIKELY standard diagnosis (e.g., Multiple Sclerosis, Migraine, Stroke).
        
        Return JSON safely:
        {
            "diagnosis": "Name of Diagnosis",
            "hypothesis": "Short 1-sentence hypothesis.",
            "confidence": <Calculated Number 0-100 based on evidence strength>,
            "points": [
                { "title": "Evidence A", "description": "Why this supports your diagnosis." },
                { "title": "Evidence B", "description": "Why this supports your diagnosis." }
            ]
        }
        IMPORTANT: Do not use real newlines in string values. Use escaped \\n only.
        IMPORTANT: "confidence" MUST be a dynamic number (e.g. 88, 92, 74) reflecting how well the symptoms match the diagnosis. Do not use 85.
    `;

    // 2. DEFENSE (Groq/Llama3) - Argues for a rare/alternative diagnosis
    // We construct this logic to run sequentially or parallel. For better context, sequential is smarter but slower.
    // Let's run Prosecutor first.

    let prosecutorResult = null;
    let usedFallback = false;

    // ATTEMPT 1: GEMINI (Primary)
    try {
        const geminiResp = await fetchWithRetry(`${GEMINI_URL}?key=${GEMINI_API_KEY}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                contents: [{ parts: [{ text: prosecutorPrompt }] }],
                generationConfig: { responseMimeType: "application/json" }
            })
        });
        const geminiJson = await geminiResp.json();
        prosecutorResult = cleanAndParseJSON(geminiJson.candidates[0].content.parts[0].text);
    } catch (e) {
        console.warn("Prosecutor (Gemini) Failed. Attempting Fallback to Groq...", e);
        usedFallback = true;
    }

    // ATTEMPT 2: GROQ (Fallback for Prosecutor) if Gemini failed
    if (!prosecutorResult && usedFallback) {
        try {
            const fallbackResp = await fetchWithRetry(GROQ_URL, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${GROQ_API_KEY}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    model: "llama-3.1-8b-instant",
                    messages: [{ role: "user", content: prosecutorPrompt }]
                })
            });
            const fallbackJson = await fallbackResp.json();
            prosecutorResult = cleanAndParseJSON(fallbackJson.choices[0].message.content);
            if (prosecutorResult) {
                // Annotate that this came from fallback
                prosecutorResult.hypothesis += " (Generated via Fallback Model due to High Traffic)";
            }
        } catch (fallbackError) {
            console.error("Prosecutor Fallback also failed:", fallbackError);
        }
    }

    // Fallback if Prosecutor fails
    if (!prosecutorResult) {
        prosecutorResult = {
            diagnosis: "Diagnosis Unavailable",
            hypothesis: "Unable to generate hypothesis due to connection error.",
            confidence: 0,
            points: []
        };
    }

    // 3. DEFENSE (Groq) calls
    const defensePrompt = `
        You are the 'Defense AI' in a medical debate.
        Patient: Age ${data.age}, ${data.gender}, Symptoms: "${data.symptoms}".
        
        The Prosecutor AI has argued for: "${prosecutorResult.diagnosis}".
        
        Your Goal: Find a RARE or ALTERNATIVE diagnosis that fits the facts but contradicts the Prosecutor. Be creative and critical.
        
        Return JSON only:
        {
            "diagnosis": "Alternative Diagnosis Name",
            "hypothesis": "Why the Prosecutor might be wrong.",
            "confidence": <Calculated Number 0-100 based on plausibility>,
            "points": [
                { "title": "Counter-Point A", "description": "Evidence typical for this rare condition." },
                { "title": "Counter-Point B", "description": "Why the prosecutor's evidence is flawed." }
            ]
        }
        IMPORTANT: Do not use real newlines in string values. Use escaped \\n only.
        IMPORTANT: "confidence" MUST be a dynamic number (e.g. 65, 78, 40) reflecting the plausibility of this alternative. Do not use 75.
    `;

    let defenseResult = null;
    try {
        const groqResp = await fetchWithRetry(GROQ_URL, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${GROQ_API_KEY}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                model: "llama-3.1-8b-instant",
                messages: [{ role: "user", content: defensePrompt }]
            })
        });
        const groqJson = await groqResp.json();
        defenseResult = cleanAndParseJSON(groqJson.choices[0].message.content);
    } catch (e) {
        console.error("Defense Error:", e);
    }

    // Fallback if Defense fails
    if (!defenseResult) {
        defenseResult = {
            diagnosis: "Challenge Unavailable",
            hypothesis: "Defense system offline.",
            confidence: 0,
            points: []
        };
    }

    return {
        prosecutor: prosecutorResult,
        defense: defenseResult
    };
}


// Export for module usage (if using modules) or window global
/**
 * JUDGE AI (Gemini) - Synthesizes the debate and renders a verdict
 * @param {Object} data - Patient data
 * @param {Object} prosecutor - Prosecutor's argument
 * @param {Object} defense - Defense's argument
 * @returns {Promise<Object>} - Final verdict
 */
async function generateJudgeVerdict(data, prosecutor, defense) {
    const judgePrompt = `
        You are the 'Judge AI', a supreme medical authority.
        Review the following case and the arguments from the Prosecutor and Defense AI models.
        
        Patient: Age ${data.age}, ${data.gender}, Symptoms: "${data.symptoms}".
        
        1. Prosecutor Argument (Standard Diagnosis): "${prosecutor.diagnosis}"
           - Points: ${JSON.stringify(prosecutor.points)}
           
        2. Defense Argument (Alternative Diagnosis): "${defense.diagnosis}"
           - Points: ${JSON.stringify(defense.points)}
        
        Your Goal: Evaluate which diagnosis is more clinically probable based on the evidence. 
        Note: If the Prosecutor's standard diagnosis is strong, favour it. If the Defense highlights a critical red flag (e.g. "but the patient has no fever"), favour the alternative.
        
        Return JSON only:
        {
            "verdict": "Name of the Winning Diagnosis",
            "confidence": <Calculated Number 0-100 based on certainty>,
            "synthesis": "Brief explanation of why you chose this verdict over the other.",
            "next_step": "The single most important next test or action."
        }
        IMPORTANT: Do not use real newlines in string values. Use escaped \\n only.
        IMPORTANT: "confidence" MUST be a dynamic number reflecting your certainty. Do not use 92.
    `;

    let judgeResult = null;
    let usedFallback = false;

    // ATTEMPT 1: Gemini (Primary Judge)
    try {
        const response = await fetchWithRetry(`${GEMINI_URL}?key=${GEMINI_API_KEY}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                contents: [{ parts: [{ text: judgePrompt }] }],
                generationConfig: { responseMimeType: "application/json" }
            })
        });

        const result = await response.json();
        judgeResult = cleanAndParseJSON(result.candidates[0].content.parts[0].text);

        if (!judgeResult) throw new Error("Failed to parse Judge response");

    } catch (e) {
        console.warn("Judge (Gemini) Failed. Fallback to Groq...", e);
        usedFallback = true;
    }

    // ATTEMPT 2: Groq (Fallback Judge)
    if (!judgeResult && usedFallback) {
        try {
            const fallbackResp = await fetchWithRetry(GROQ_URL, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${GROQ_API_KEY}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    model: "llama-3.1-8b-instant",
                    messages: [{ role: "user", content: judgePrompt }]
                })
            });
            const fallbackJson = await fallbackResp.json();
            judgeResult = cleanAndParseJSON(fallbackJson.choices[0].message.content);
            if (judgeResult) {
                judgeResult.synthesis += " (Verdict rendered by Backup System)";
            }
        } catch (fallbackError) {
            console.error("Judge Fallback also failed:", fallbackError);
        }
    }

    // Final Fallback
    if (!judgeResult) {
        return {
            verdict: "Verdict Unavailable",
            confidence: 0,
            synthesis: "The Judge could not reach a verdict due to connection issues.",
            next_step: "Consult a human specialist."
        };
    }

    return judgeResult;
}

// Export for module usage (if using modules) or window global
window.neuroApi = {
    analyzeSymptoms,
    generateAdversarialDebate,
    generateJudgeVerdict
};
