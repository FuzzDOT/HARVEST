import { useState, useEffect } from "react";
import scytheLogo from "./assets/scythewheatlogo.png";
import vineSrc from "./assets/vine.png"; // splash (hero) background vine
import resultsBgSrc from "./assets/vines2.png"; // ← OPTIONAL: your explore page background image

// --- Crop images (local assets) ---
import wheatImg  from "./assets/crops/Wheat.png";
import carrotImg  from "./assets/crops/Carrot.png";
import cornImg   from "./assets/crops/Corn.png";
import riceImg   from "./assets/crops/Rice.png";
import soyImg    from "./assets/crops/Soy.png";
import onionImg    from "./assets/crops/Onion.png";
import barleyImg from "./assets/crops/Barley.png";
import potatoImg from "./assets/crops/Potato.png";
import tomatoImg from "./assets/crops/Tomato.png";
import alfalfaImg from "./assets/crops/Alfalfa.png";
import cottonImg from "./assets/crops/Cotton.png";
import fallbackImg from "./assets/crops/Wheatwinter.png"; // generic photo

const CROP_IMAGE: Record<string, string> = {
    wheat: wheatImg,
    carrot:carrotImg,
    corn: cornImg,
    maize: cornImg,       // alias
    rice: riceImg,
    soy: soyImg,
    onion: onionImg,
    soybean: soyImg,      // alias
    barley: barleyImg,
    potato: potatoImg,
    tomato: tomatoImg,
    alfalfa: alfalfaImg,
    cotton: cottonImg,
};

function getCropImage(name: string): string {
    const key = (name || "").trim().toLowerCase();
    if (CROP_IMAGE[key]) return CROP_IMAGE[key];
    const singular = key.endsWith("s") ? key.slice(0, -1) : key;
    return CROP_IMAGE[singular] || fallbackImg;
}

const ACCENT_FROM = "#d3b78e"; // warm gold
const ACCENT_TO   = "#b38d43"; // deeper amber
const ACCENT_MUTED_FROM = "#c6b287"; // disabled/muted gold
const ACCENT_MUTED_TO   = "#d8c296";

// Backend base URL (set VITE_API_BASE in your .env if you want to override)
const API_BASE = (import.meta as any)?.env?.VITE_API_BASE ?? "https://harvest-5ub4.onrender.com";

// ★ Added "planType"
type FieldKey = "state" | "startMonth" | "initialInvestment" | "landSqft" | "planType";
type Errors = Partial<Record<FieldKey, string>>;

const US_STATES = [
    "Alabama","Alaska","Arizona","Arkansas","California","Colorado","Connecticut","Delaware","District of Columbia",
    "Florida","Georgia","Hawaii","Idaho","Illinois","Indiana","Iowa","Kansas","Kentucky","Louisiana","Maine","Maryland",
    "Massachusetts","Michigan","Minnesota","Mississippi","Missouri","Montana","Nebraska","Nevada","New Hampshire",
    "New Jersey","New Mexico","New York","North Carolina","North Dakota","Ohio","Oklahoma","Oregon","Pennsylvania",
    "Rhode Island","South Carolina","South Dakota","Tennessee","Texas","Utah","Vermont","Virginia","Washington",
    "West Virginia","Wisconsin","Wyoming"
];

// === State → ParcelId mapping (Alabama=P1, Alaska=P2, ... in the order above) ===
const STATE_TO_PARCEL: Record<string, string> = US_STATES.reduce((acc, name, idx) => {
    acc[name] = `P${idx + 1}`; // <- start at 1
    return acc;
}, {} as Record<string, string>);

const MONTHS = [
    "January","February","March","April","May","June","July","August","September","October","November","December"
];

// tiny helpers
const titleCase = (s: string) =>
    s ? s.replace(/\w\S*/g, (w) => w[0].toUpperCase() + w.slice(1).toLowerCase()) : s;

const monthToNumber = (name: string) => {
    const idx = MONTHS.findIndex(m => m.toLowerCase() === name.toLowerCase());
    return idx >= 0 ? idx + 1 : 1;
};

const currency = (n: number) =>
    new Intl.NumberFormat(undefined, { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(n);

export default function App() {
    const [stateUS, setStateUS] = useState("");
    const [startMonth, setStartMonth] = useState("");
    const [initialInvestment, setInitialInvestment] = useState("");
    const [landSqft, setLandSqft] = useState("");
    // ★ New: plan type (required): "short_term" | "long_term"
    const [planType, setPlanType] = useState("");

    const [errors, setErrors] = useState<Errors>({});
    const [showResults, setShowResults] = useState(false);

    const setField = (key: FieldKey, value: string) => {
        if (key === "state") setStateUS(value);
        if (key === "startMonth") setStartMonth(value);
        if (key === "initialInvestment") setInitialInvestment(value);
        if (key === "landSqft") setLandSqft(value);
        if (key === "planType") setPlanType(value);

        if (value && errors[key]) {
            setErrors((prev) => {
                const { [key]: _omit, ...rest } = prev;
                return rest;
            });
        }
    };

    const focusFirstError = (errs: Errors) => {
        // ★ Include planType in focus order (first in list feels natural)
        const order: FieldKey[] = ["planType", "state", "startMonth", "initialInvestment", "landSqft"];
        const first = order.find((k) => errs[k]);
        if (!first) return;
        setTimeout(() => {
            const el = document.getElementById(first) as HTMLInputElement | HTMLSelectElement | null;
            if (el) {
                el.scrollIntoView({ behavior: "smooth", block: "center" });
                el.focus();
            }
        }, 40);
    };

    const handleExplore = () => {
        const nextErrors: Errors = {};
        if (!planType) nextErrors.planType = "Required";
        if (!stateUS.trim()) nextErrors.state = "Required";
        if (!startMonth) nextErrors.startMonth = "Required";
        if (!initialInvestment) nextErrors.initialInvestment = "Required";
        if (!landSqft || Number(landSqft) <= 0) nextErrors.landSqft = "Enter a positive number";

        setErrors(nextErrors);

        if (Object.keys(nextErrors).length > 0) {
            focusFirstError(nextErrors);
            return;
        }

        setShowResults(true);
        setTimeout(() => {
            document.getElementById("results")?.scrollIntoView({ behavior: "smooth" });
        }, 80);
    };

    return (
        <div style={styles.page}>
            {!showResults && (
                <a
                    href="https://github.com/FuzzDOT/HARVEST"
                    style={styles.githubBubble}
                    title="GitHub"
                    aria-label="GitHub repository"
                >
                    <img
                        src="https://img.icons8.com/ios_filled/512/FFFFFF/github.png"
                        alt="GitHub"
                        style={{ width: 56, height: 56 }}
                    />
                </a>
            )}

            {showResults ? (
                <ResultsScreen
                    onBack={() => setShowResults(false)}
                    errors={errors}
                    onFixNow={() => {
                        setShowResults(false);
                        focusFirstError(errors);
                    }}
                    stateUS={stateUS}
                    startMonth={startMonth}
                    initialInvestment={initialInvestment}
                    landSqft={landSqft}
                    planType={planType}
                    resultsBgSrc={resultsBgSrc}
                />
            ) : (
                <>
                    <Hero
                        scytheLogo={scytheLogo}
                        stateUS={stateUS}
                        startMonth={startMonth}
                        initialInvestment={initialInvestment}
                        landSqft={landSqft}
                        planType={planType}
                        setField={setField}
                        onExplore={handleExplore}
                        errors={errors}
                    />
                    <Details />
                </>
            )}
        </div>
    );
}

function Hero(props: {
    scytheLogo: string;
    stateUS: string;
    startMonth: string;
    initialInvestment: string;
    landSqft: string;
    planType: string;
    setField: (key: FieldKey, value: string) => void;
    onExplore: () => void;
    errors: Errors;
}) {
    const { scytheLogo, stateUS, startMonth, initialInvestment, landSqft, planType, setField, onExplore, errors } = props;

    return (
        <header style={styles.hero}>
            {/* Decorative vine image (background) */}
            <img src={vineSrc} alt="" aria-hidden="true" style={styles.vineImg} />

            <div style={styles.cardWrap}>
                <div style={styles.cardShine} aria-hidden="true" />
                <div style={styles.logoWrap} aria-label="Harvest logo">
                    <img src={scytheLogo} alt="Harvest Logo" style={{ maxWidth: "100%", maxHeight: "100%" }} />
                </div>

                <div style={styles.form}>
                    {/* ★ Plan Type */}
                    <label style={styles.label} htmlFor="planType">
                        Plan Type {errors.planType && <span style={styles.errorText}>{errors.planType}</span>}
                    </label>
                    <select
                        id="planType"
                        style={{ ...styles.input, ...(errors.planType ? styles.inputError : {}) }}
                        aria-invalid={Boolean(errors.planType)}
                        value={planType}
                        onChange={(e) => setField("planType", e.target.value)}
                    >
                        <option value="" disabled>Select plan</option>
                        <option value="short_term">Short-term (monthly actions)</option>
                        <option value="long_term">Long-term (12-month plan)</option>
                    </select>

                    {/* State */}
                    <label style={styles.label} htmlFor="state">
                        State {errors.state && <span style={styles.errorText}>{errors.state}</span>}
                    </label>
                    <select
                        id="state"
                        style={{ ...styles.input, ...(errors.state ? styles.inputError : {}) }}
                        aria-invalid={Boolean(errors.state)}
                        value={stateUS}
                        onChange={(e) => setField("state", e.target.value)}
                    >
                        <option value="" disabled>Select a state</option>
                        {US_STATES.map((s) => (
                            <option key={s}>{s}</option>
                        ))}
                    </select>

                    {/* Start Month */}
                    <label style={styles.label} htmlFor="startMonth">
                        Start Month {errors.startMonth && <span style={styles.errorText}>{errors.startMonth}</span>}
                    </label>
                    <select
                        id="startMonth"
                        style={{ ...styles.input, ...(errors.startMonth ? styles.inputError : {}) }}
                        aria-invalid={Boolean(errors.startMonth)}
                        value={startMonth}
                        onChange={(e) => setField("startMonth", e.target.value)}
                    >
                        <option value="" disabled>Select month</option>
                        {MONTHS.map((m) => (
                            <option key={m}>{m}</option>
                        ))}
                    </select>

                    {/* Initial Investment */}
                    <label style={styles.label} htmlFor="initialInvestment">
                        Initial Investment {errors.initialInvestment && <span style={styles.errorText}>{errors.initialInvestment}</span>}
                    </label>
                    <select
                        id="initialInvestment"
                        style={{ ...styles.input, ...(errors.initialInvestment ? styles.inputError : {}) }}
                        aria-invalid={Boolean(errors.initialInvestment)}
                        value={initialInvestment}
                        onChange={(e) => setField("initialInvestment", e.target.value)}
                    >
                        <option value="" disabled>Select investment range</option>
                        <option>Under $500</option>
                        <option>$500 – $1,000</option>
                        <option>$1,000 – $2,500</option>
                        <option>$2,500 – $5,000</option>
                        <option>$5,000+</option>
                    </select>

                    {/* Land (sqft) */}
                    <label style={styles.label} htmlFor="landSqft">
                        Land Area (sqft) {errors.landSqft && <span style={styles.errorText}>{errors.landSqft}</span>}
                    </label>
                    <input
                        id="landSqft"
                        type="number"
                        inputMode="numeric"
                        min={1}
                        placeholder="e.g., 2000"
                        style={{ ...styles.input, ...(errors.landSqft ? styles.inputError : {}) }}
                        aria-invalid={Boolean(errors.landSqft)}
                        value={landSqft}
                        onChange={(e) => setField("landSqft", e.target.value)}
                    />

                    <button style={styles.cta} onClick={onExplore} title="Explore">
                        Explore
                    </button>
                </div>
            </div>
            <div style={styles.scrollHint}>Scroll</div>
        </header>
    );
}

function Details() {
    return (
        <main id="details" style={styles.main}>
            <section style={styles.section}>
                <h2 style={styles.h2}>Project</h2>
                <p style={styles.p}>
                    Harvest helps land owners choose the most profitable crops using soil, ground profile, local pricing, and
                    weather. The short-term view recommends monthly actions; the long-term view plans the next year using 10-year
                    weather averages.
                </p>
                <ul style={styles.list}>
                    <li>Short-term: immediate actions for this month to maximize for a smaller time period</li>
                    <li>Long-term: 12-month plan using historical climate data for a longer time period</li>
                    <li>Inputs: state, start month, initial investment, land size</li>
                    <li>Outputs: crop recommendations, expected yield & margin</li>
                </ul>
            </section>

            <section style={styles.section}>
                <h2 style={styles.h2}>Team</h2>
                <div style={styles.teamGrid}>
                    {[
                        { name: "Ayaan Mahajan", role: "Frontend Developer", initials: "A" },
                        { name: "Evan Jackson", role: "Frontend Developer", initials: "E" },
                        { name: "Faaz Mohammed", role: "Backend/ML Developer", initials: "F" },
                        { name: "Zhengyao Zhou", role: "Data Management", initials: "Z" },
                    ].map((m) => (
                        <article key={m.name} style={styles.card}>
                            <div style={styles.avatar}>{m.initials}</div>
                            <div>
                                <div style={styles.memberName}>{m.name}</div>
                                <div style={styles.memberRole}>{m.role}</div>
                            </div>
                        </article>
                    ))}
                </div>
            </section>

            <section style={styles.section}>
                <h2 style={styles.h2}>Tech</h2>
                <div style={styles.kvRow}>
                    <div style={styles.kv}>
                        <span style={styles.k}>Frontend</span>
                        <span>React + Vite (TS)</span>
                    </div>
                    <div style={styles.kv}>
                        <span style={styles.k}>Model</span>
                        <span>Rule-based + ML (WIP)</span>
                    </div>
                    <div style={styles.kv}>
                        <span style={styles.k}>Data</span>
                        <span>Weather, crops, prices, soils</span>
                    </div>
                </div>
            </section>

            <footer style={styles.footer}>
                <small>© {new Date().getFullYear()} Harvest. All rights reserved.</small>
            </footer>
        </main>
    );
}

type PlanOption = {
    id: string;                 // local id/index for select value
    label: string;              // human label shown in select
    crop: string;               // crop name
    baseYield: number | null;   // value used for revenue formula
    fertilizerUsed: string | null; // NEW: fertilizer_used for this recommendation
};

function ResultsScreen({
                           onBack,
                           errors,
                           onFixNow,
                           stateUS,
                           startMonth,
                           initialInvestment,
                           landSqft,
                           planType,
                           resultsBgSrc,
                       }: {
    onBack: () => void;
    errors: Errors;
    onFixNow: () => void;
    stateUS: string;
    startMonth: string;
    initialInvestment: string;
    landSqft: string;
    planType: string;
    resultsBgSrc?: string;
}) {
    const missing = Object.keys(errors) as FieldKey[];
    const prettyState = stateUS.trim();
    const prettyMonth = startMonth;
    const prettyInvestment = initialInvestment;
    const prettyLand = landSqft ? Number(landSqft).toLocaleString() : "";
    const acres = landSqft ? Number(landSqft) / 43560 : 0;
    const prettyPlan =
        planType === "short_term" ? "Short-term" :
            planType === "long_term" ? "Long-term" : "";

    // Predicted crop & base yield from backend
    const [predictedCrop, setPredictedCrop] = useState<string>("Wheat");
    const [predictedBaseYield, setPredictedBaseYield] = useState<number | null>(null);
    const [loading, setLoading] = useState(false);
    const [apiError, setApiError] = useState<string | null>(null);

    // Plans from backend + selection
    const [plans, setPlans] = useState<PlanOption[]>([]);
    const [selectedPlanIndex, setSelectedPlanIndex] = useState<number | null>(null);

    // helper to safely coerce a number-looking field
    const num = (v: any): number | null => {
        const n = typeof v === "string" ? Number(v) : typeof v === "number" ? v : NaN;
        return Number.isFinite(n) ? n : null;
    };

    // pull a base-yield-like value from a recommendation object (be tolerant to field names)
    const extractBaseYield = (obj: any): number | null => {
        if (!obj || typeof obj !== "object") return null;
        return (
            num(obj.profit_per_acre) ??
            num(obj.expected_yield) ??
            num(obj.yield_per_acre) ??
            num(obj.yield_lb_per_acre) ??
            num(obj.yield) ??
            null
        );
    };

    const extractFertilizer = (obj: any): string | null => {
        if (!obj || typeof obj !== "object") return null;
        // Try common keys
        return (
            (typeof obj.fertilizer_used === "string" && obj.fertilizer_used) ||
            (typeof obj.fertilizer === "string" && obj.fertilizer) ||
            (typeof obj.recommended_fertilizer === "string" && obj.recommended_fertilizer) ||
            null
        );
    };

    useEffect(() => {
        let cancelled = false;
        async function fetchPrediction() {
            setLoading(true);
            setApiError(null);

            const parcelId = STATE_TO_PARCEL[prettyState] || "P1";
            const monthNum = monthToNumber(prettyMonth || "January");

            try {
                if (planType === "short_term") {
                    const payload = {
                        parcel_id: parcelId,
                        month: monthNum,
                        top_n: 5,
                        ranking_method: "profit",
                        min_confidence: 60,
                    };

                    console.groupCollapsed("🌾 HARVEST API → /api/v1/predict/month");
                    console.log("Request payload:", payload);

                    const res = await fetch(`${API_BASE}/api/v1/predict/month`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload),
                    });
                    console.log("HTTP status:", res.status);

                    const text = await res.text();
                    let json: any = null;
                    try { json = text ? JSON.parse(text) : {}; } catch {
                        console.warn("Non-JSON response body:", text);
                    }
                    console.log("Response body:", json ?? text);

                    if (!res.ok) {
                        console.groupEnd();
                        throw new Error(text || `Request failed with status ${res.status}`);
                    }

                    const recs = Array.isArray(json?.recommendations) ? json.recommendations : [];
                    const planOptions: PlanOption[] = recs.map((r: any, i: number) => ({
                        id: String(i),
                        label: `${i + 1}: ${titleCase(r?.crop_name ?? `Option ${i + 1}`)}`,
                        crop: titleCase(r?.crop_name ?? "Unknown"),
                        baseYield: extractBaseYield(r),
                        fertilizerUsed: extractFertilizer(r),
                    }));

                    if (!cancelled) {
                        setPlans(planOptions);
                        if (planOptions.length > 0) {
                            setSelectedPlanIndex(0);
                            setPredictedCrop(planOptions[0].crop);
                            setPredictedBaseYield(planOptions[0].baseYield ?? null);
                        } else {
                            setSelectedPlanIndex(null);
                            setPredictedBaseYield(null);
                        }
                    }
                    console.groupEnd();
                } else if (planType === "long_term") {
                    const payload = {
                        parcel_id: parcelId,
                        start_month: monthNum,
                        diversification_bonus: 0.1,
                        min_profit_threshold: 0,
                    };

                    console.groupCollapsed("🌾 HARVEST API → /api/v1/plan/annual");
                    console.log("Request payload:", payload);

                    const res = await fetch(`${API_BASE}/api/v1/plan/annual`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload),
                    });
                    console.log("HTTP status:", res.status);

                    const text = await res.text();
                    let json: any = null;
                    try { json = text ? JSON.parse(text) : {}; } catch {
                        console.warn("Non-JSON response body:", text);
                    }
                    console.log("Response body:", json ?? text);

                    if (!res.ok) {
                        console.groupEnd();
                        throw new Error(text || `Request failed with status ${res.status}`);
                    }

                    const seq = Array.isArray(json?.rotation_sequence) ? json.rotation_sequence : [];
                    const planOptions: PlanOption[] = seq.map((r: any, i: number) => {
                        const cropName = r?.recommended_crop ?? r?.crop_name ?? `Option ${i + 1}`;
                        const monthLabel = typeof r?.month === "number" && r.month >= 1 && r.month <= 12
                            ? ` (${MONTHS[r.month - 1]})` : "";
                        return {
                            id: String(i),
                            label: `${i + 1}: ${titleCase(cropName)}${monthLabel}`,
                            crop: titleCase(cropName),
                            baseYield: extractBaseYield(r) ?? extractBaseYield(json) ?? null,
                            fertilizerUsed: extractFertilizer(r),
                        };
                    });

                    if (!cancelled) {
                        setPlans(planOptions);
                        if (planOptions.length > 0) {
                            setSelectedPlanIndex(0);
                            setPredictedCrop(planOptions[0].crop);
                            setPredictedBaseYield(planOptions[0].baseYield ?? null);
                        } else {
                            setSelectedPlanIndex(null);
                            setPredictedBaseYield(null);
                        }
                    }
                    console.groupEnd();
                }
            } catch (e: any) {
                console.error("🌾 HARVEST API error:", e);
                if (!cancelled) setApiError(e?.message ?? "Failed to load predictions");
                if (!cancelled) {
                    setPlans([]);
                    setSelectedPlanIndex(null);
                    setPredictedBaseYield(null);
                }
            } finally {
                if (!cancelled) setLoading(false);
            }
        }

        if (planType && prettyState && prettyMonth) {
            fetchPrediction();
        } else {
            setPlans([]);
            setSelectedPlanIndex(null);
            setPredictedBaseYield(null);
        }
        return () => { cancelled = true; };
    }, [planType, prettyState, prettyMonth]);

    // When user switches plan in the select, reflect that everywhere
    const onPlanSelectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const idx = Number(e.target.value);
        setSelectedPlanIndex(Number.isFinite(idx) ? idx : null);
        const chosen = Number.isFinite(idx) ? plans[idx] : null;
        if (chosen) {
            setPredictedCrop(chosen.crop);
            setPredictedBaseYield(chosen.baseYield ?? null);
        }
    };

    // Expected Revenue = (sqft / 43,560) * (base yield from backend)
    const expectedRevenue = predictedBaseYield != null ? acres * predictedBaseYield : null;

    const selectedPlan = (selectedPlanIndex != null && plans[selectedPlanIndex]) ? plans[selectedPlanIndex] : null;

    return (
        <main id="results" style={styles.resultsWrap}>
            {/* --- background image & readability overlay --- */}
            {resultsBgSrc && <img src={resultsBgSrc} alt="" aria-hidden="true" style={styles.resultsBgImg} />}
            <div style={styles.resultsBgOverlay} />

            <div style={styles.resultsInner}>
                <header style={styles.resultsHeader}>
                    <button style={styles.backChip} onClick={onBack}>
                        ← Back
                    </button>
                    <div style={styles.headerTitleWrap}>
                        <h1 style={styles.headerTitle}>Recommendations</h1>
                        <span style={styles.headerSubtitle}>
              {prettyState || prettyMonth || prettyInvestment || prettyLand || prettyPlan
                  ? `Plan: ${prettyPlan || "—"} • ${prettyState || "your state"} • Start: ${prettyMonth || "—"} • Land: ${prettyLand || "—"} sqft • Investment: ${prettyInvestment || "—"}`
                  : "Based on your inputs"}
            </span>
                    </div>
                </header>

                {missing.length > 0 && (
                    <div style={styles.issuesBanner}>
                        <div>
                            <strong style={{ marginRight: 8 }}>Missing info:</strong>
                            {missing.map((k, i) => (
                                <span key={k} style={styles.issuePill}>
                  {k.charAt(0).toUpperCase() + k.slice(1)}
                                    {i < missing.length - 1 ? " " : ""}
                </span>
                            ))}
                        </div>
                        <button style={styles.fixBtn} onClick={onFixNow}>
                            Fix now
                        </button>
                    </div>
                )}

                <div style={styles.resultsGrid}>
                    <section style={styles.mainCol}>
                        <div style={styles.heroPanel}>
                            <div style={styles.heroLeft}>
                                <div style={styles.cropBadge}>{predictedCrop.toUpperCase()}</div>
                                <h2 style={styles.heroTitle}>Optimal Plan — {prettyMonth || "Month"}</h2>
                                <p style={styles.heroDesc}>
                                    {`${prettyPlan || "Plan TBD"} • High margin • 30–45 day cycle • ${prettyState || "US"} • ${prettyLand ? prettyLand + " sqft" : "land TBD"}`}
                                </p>
                                <div style={styles.heroChips}>
                                    {prettyPlan && <span style={styles.chip}>{prettyPlan}</span>}
                                    {prettyState && <span style={styles.chip}>{prettyState}</span>}
                                    {prettyMonth && <span style={styles.chip}>Start: {prettyMonth}</span>}
                                    {prettyLand && <span style={styles.chip}>{prettyLand} sqft</span>}
                                    {prettyInvestment && <span style={styles.chip}>Investment: {prettyInvestment}</span>}
                                    {loading && <span style={styles.chip}>Loading…</span>}
                                    {apiError && <span style={{...styles.chip, color:"#b91c1c", borderColor:"rgba(185,28,28,.35)"}}>API error</span>}
                                </div>
                            </div>
                            <div style={styles.heroRight}>
                                <div style={styles.cropImgBig}>
                                    <img
                                        src={getCropImage(predictedCrop)}
                                        alt={predictedCrop || "Crop"}
                                        style={{ width: "100%", height: "100%", objectFit: "cover", borderRadius: 16 }}
                                        loading="lazy"
                                        onError={(e) => { console.warn("Image failed:", predictedCrop, (e.target as HTMLImageElement).src); }}
                                    />
                                </div>
                            </div>
                        </div>

                        <div style={styles.metricsRow}>
                            <div style={styles.metricCardAccent}>
                                <div style={styles.statValue}>
                                    {expectedRevenue != null ? currency(expectedRevenue) : "—"}
                                </div>
                                <div style={styles.statLabel}>
                                    Expected Revenue ({prettyState || "your area"})
                                </div>
                            </div>
                        </div>
                    </section>

                    <aside style={styles.sidebarGlass}>
                        <h3 style={{ marginTop: 0, marginBottom: 12, color: "#0f172a" }}>Results</h3>

                        <div style={styles.filterGroup}>
                            <label style={styles.filterLabel}>Plan Type</label>
                            <div>{prettyPlan || "—"}</div>
                        </div>

                        <div style={styles.filterGroup}>
                            <label style={styles.filterLabel}>State</label>
                            <div>{prettyState || "—"}</div>
                        </div>

                        <div style={styles.filterGroup}>
                            <label style={styles.filterLabel}>Start Month</label>
                            <div>{prettyMonth || "—"}</div>
                        </div>

                        <div style={styles.filterGroup}>
                            <label style={styles.filterLabel}>Land (sqft)</label>
                            <div>{prettyLand || "—"}</div>
                        </div>

                        <div style={styles.filterGroup}>
                            <label style={styles.filterLabel}>Initial Investment</label>
                            <div>{prettyInvestment || "—"}</div>
                        </div>

                        {/* ★★ Plans from backend recommendations */}
                        <div style={styles.filterGroup}>
                            <label style={styles.filterLabel}>Plan</label>
                            <select
                                style={styles.select}
                                value={selectedPlanIndex ?? ""}
                                onChange={onPlanSelectChange}
                                disabled={plans.length === 0}
                            >
                                {plans.length === 0 ? (
                                    <option value="">No plans available</option>
                                ) : (
                                    plans.map((p, i) => (
                                        <option key={p.id} value={i}>
                                            {p.label}
                                        </option>
                                    ))
                                )}
                            </select>
                        </div>

                        <div style={styles.filterGroup}>
                            <label style={styles.filterLabel}>Crop Type</label>
                            <div>{predictedCrop}</div>
                        </div>

                        {/* ★★ NEW: show fertilizer for selected plan */}
                        <div style={styles.filterGroup}>
                            <label style={styles.filterLabel}>Fertilizer Type</label>
                            <div>{selectedPlan?.fertilizerUsed ?? "—"}</div>
                        </div>
                    </aside>
                </div>
            </div>
        </main>
    );
}

const styles: Record<string, React.CSSProperties> = {
    page: {
        minHeight: "100vh",
        fontFamily: "Inter, system-ui, Avenir, Helvetica, Arial, sans-serif",
        color: "#0f172a",
        backgroundColor: "#f7f9fc",
    },

    hero: {
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        background:
            "radial-gradient(1200px 600px at 70% -10%, rgba(255,255,255,.70) 0%, rgba(246,248,251,.52) 40%, rgba(233,238,245,.30) 60%, rgba(233,238,245,0) 100%), linear-gradient(135deg, #f6f8fb 0%, #eef2f7 50%, #e9eef5 100%)",
        position: "relative",
        padding: "40px 6vw",
        overflow: "hidden",
    },

    // Splash vine
    vineImg: {
        position: "absolute",
        right: "2vw",
        bottom: "-17vh",
        width: "min(100vw, 200vw)",
        height: "auto",
        opacity: 0.18,
        pointerEvents: "none",
        userSelect: "none",
        zIndex: 0,
        filter: "saturate(0.9) contrast(0.95)",
        mixBlendMode: "multiply",
    } as React.CSSProperties,

    cardWrap: {
        display: "flex",
        flexDirection: "column" as const,
        alignItems: "center",
        gap: 16,
        width: "min(820px, 92vw)",
        padding: 28,
        borderRadius: 28,
        position: "relative",
        zIndex: 1,
        overflow: "hidden",
        background: "linear-gradient(180deg, rgba(255,255,255,.62), rgba(255,255,255,.34))",
        backdropFilter: "blur(16px)",
        WebkitBackdropFilter: "blur(16px)",
        border: "1px solid rgba(255,255,255,.55)",
        boxShadow: "0 24px 64px rgba(2, 6, 23, 0.16), inset 0 1px rgba(255,255,255,.6)",
    },
    cardShine: {
        position: "absolute",
        top: -80,
        left: -40,
        width: "140%",
        height: 200,
        background:
            "radial-gradient(ellipse at top left, rgba(255,255,255,.9) 0%, rgba(255,255,255,.35) 45%, rgba(255,255,255,0) 70%)",
        filter: "blur(6px)",
        pointerEvents: "none",
        transform: "rotate(-2deg)",
    },
    logoWrap: {
        display: "grid",
        placeItems: "center",
        width: 160,
        height: 160,
        filter: "drop-shadow(0 8px 18px rgba(2,6,23,.10))",
    },

    form: {
        width: "100%",
        display: "grid",
        gap: 12,
    },
    label: {
        fontSize: 12,
        letterSpacing: 0.6,
        textTransform: "uppercase" as const,
        color: "#0f172a",
        opacity: 0.8,
        display: "flex",
        alignItems: "center",
        gap: 8,
    },
    errorText: {
        fontSize: 11,
        fontWeight: 800,
        color: "#dc2626",
        background: "rgba(220,38,38,.10)",
        border: "1px solid rgba(220,38,38,.25)",
        padding: "2px 6px",
        borderRadius: 999,
    },
    input: {
        width: "100%",
        height: 44,
        padding: "0 14px",
        borderRadius: 14,
        border: "1px solid rgba(15,23,42,.10)",
        background: "rgba(255,255,255,.82)",
        fontSize: 14,
        boxShadow: "inset 0 2px 6px rgba(2,6,23,.05), inset 0 1px rgba(255,255,255,.6)",
        outline: "none",
    },
    inputError: {
        border: "1px solid rgba(220,38,38,.6)",
        boxShadow: "0 0 0 4px rgba(220,38,38,.12), inset 0 2px 6px rgba(2,6,23,.05)",
    },

    cta: {
        marginTop: 8,
        height: 52,
        borderRadius: 14,
        border: "1px solid rgba(255,255,255,.35)",
        background: `linear-gradient(135deg, ${ACCENT_FROM}, ${ACCENT_TO})`,
        color: "white",
        fontSize: 16,
        fontWeight: 800,
    },
    ctaDisabled: {
        opacity: 0.55,
        cursor: "not-allowed",
        transform: "none",
        boxShadow: "inset 0 1px rgba(255,255,255,.18)",
        background: `linear-gradient(135deg, ${ACCENT_MUTED_FROM}, ${ACCENT_MUTED_TO})`,
        border: "1px solid rgba(255,255,255,.22)",
    },

    main: {
        display: "grid",
        gap: 28,
        padding: "56px 6vw 96px",
        background: "#fff",
    },
    section: {
        width: "min(1000px, 100%)",
        margin: "0 auto",
        background: "linear-gradient(180deg, rgba(255,255,255,.92), rgba(255,255,255,.86))",
        border: "1px solid #e2e8f0",
        borderRadius: 20,
        padding: 24,
        boxShadow: "0 10px 24px rgba(2,6,23,.06)",
    },
    h2: { margin: 0, fontSize: 24, color: "#0f172a" },
    p: { lineHeight: 1.6, color: "#0f172a", opacity: 0.85 },
    list: { marginTop: 8 },
    teamGrid: {
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
        gap: 16,
        marginTop: 12,
    },
    card: {
        display: "flex",
        gap: 12,
        alignItems: "center",
        background: "#fff",
        border: "1px solid #e2e8f0",
        borderRadius: 16,
        padding: 14,
    },
    avatar: {
        width: 44,
        height: 44,
        borderRadius: "50%",
        background: `linear-gradient(135deg, ${ACCENT_FROM}, ${ACCENT_TO})`,
        color: "#1f2937",
        display: "grid",
        placeItems: "center",
        fontWeight: 800,
        boxShadow: "0 6px 18px rgba(2,6,23,.12)",
    },
    memberName: { fontWeight: 700, color: "#0f172a" },
    memberRole: { color: "#475569", fontSize: 14 },
    kvRow: {
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
        gap: 12,
        marginTop: 12,
    },
    kv: {
        display: "flex",
        justifyContent: "space-between",
        background: "#fff",
        border: "1px solid #e2e8f0",
        borderRadius: 14,
        padding: "10px 14px",
    },
    k: { fontWeight: 700, marginRight: 8, color: "#6e8a4b" },
    footer: {
        width: "min(1000px, 100%)",
        margin: "0 auto",
        textAlign: "center" as const,
        color: "#85b686",
    },

    /* RESULTS PAGE */
    resultsWrap: {
        minHeight: "100vh",
        background: "linear-gradient(135deg, #f6f8fb 0%, #eef2f7 50%, #e9eef5 100%)",
        position: "relative",
        overflow: "hidden",
    },
    resultsBgImg: {
        position: "absolute",
        right: "11vw",
        bottom: "-100vh",
        width: "min(75vw, 150vw)",
        height: "auto",
        opacity: 0.18,
        pointerEvents: "none",
        userSelect: "none",
        transform: "rotate(90deg)",
        zIndex: 0,
        filter: "saturate(0.9) contrast(0.95)",
        mixBlendMode: "multiply",
    } as React.CSSProperties,
    resultsBgOverlay: {
        position: "absolute",
        inset: 0,
        zIndex: 1,
        background:
            "radial-gradient(1200px 600px at 70% -10%, rgba(255,255,255,.50) 0%, rgba(246,248,251,.45) 40%, rgba(233,238,245,.35) 60%, rgba(233,238,245,.25) 100%)",
    },

    resultsInner: {
        padding: "20px 24px 40px",
        maxWidth: "1200px",
        margin: "0 auto",
        position: "relative",
        zIndex: 2,
    },
    resultsHeader: {
        position: "sticky",
        top: 16,
        zIndex: 20,
        display: "grid",
        gridTemplateColumns: "auto 1fr",
        alignItems: "center",
        gap: 12,
        padding: "12px 16px",
        borderRadius: 16,
        background: "rgba(255,255,255,.60)",
        backdropFilter: "blur(10px)",
        WebkitBackdropFilter: "blur(10px)",
        border: "1px solid rgba(15,23,42,.06)",
        boxShadow: "0 10px 30px rgba(2,6,23,.08)",
    },
    backChip: {
        padding: "8px 12px",
        borderRadius: 999,
        border: "1px solid rgba(15,23,42,.12)",
        background: "rgba(255,255,255,.95)",
        cursor: "pointer",
        fontWeight: 700,
    },
    headerTitleWrap: {
        display: "flex",
        flexDirection: "column",
        gap: 2,
    },
    headerTitle: {
        margin: 0,
        fontSize: 22,
        letterSpacing: 0.2,
        fontWeight: 800,
        color: "#0f172a",
    },
    headerSubtitle: {
        fontSize: 12,
        color: "#64748b",
    },

    issuesBanner: {
        marginTop: 14,
        marginBottom: 8,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 12,
        padding: "12px 14px",
        borderRadius: 14,
        background: "linear-gradient(180deg, rgba(254,242,242,.80), rgba(254,242,242,.62))",
        border: "1px solid rgba(220,38,38,.25)",
        backdropFilter: "blur(8px)",
        WebkitBackdropFilter: "blur(8px)",
    },
    issuePill: {
        display: "inline-block",
        marginRight: 6,
        padding: "4px 8px",
        fontSize: 12,
        borderRadius: 999,
        background: "rgba(220,38,38,.12)",
        border: "1px solid rgba(220,38,38,.2)",
        color: "#991b1b",
        fontWeight: 700,
    },
    fixBtn: {
        padding: "8px 12px",
        borderRadius: 10,
        border: "1px solid rgba(220,38,38,.3)",
        background: "linear-gradient(135deg, #ef4444, #dc2626)",
        color: "#fff",
        fontWeight: 800,
        cursor: "pointer",
        boxShadow: "0 8px 16px rgba(220,38,38,.25)",
    },

    resultsGrid: {
        display: "grid",
        gridTemplateColumns: "1fr minmax(260px, 320px)",
        gap: 20,
        marginTop: 20,
    },

    sidebarGlass: {
        position: "sticky",
        top: 84,
        alignSelf: "start",
        background: "linear-gradient(180deg, rgba(255,255,255,.56), rgba(255,255,255,.28))",
        backdropFilter: "blur(14px)",
        WebkitBackdropFilter: "blur(14px)",
        border: "1px solid rgba(255,255,255,.55)",
        boxShadow: "0 20px 40px rgba(2,6,23,.12), inset 0 1px rgba(255,255,255,.6)",
        borderRadius: 20,
        padding: 18,
        maxHeight: "calc(100vh - 120px)",
        overflow: "auto",
        color: "#0f172a",
    },
    filterGroup: { marginBottom: 12 },
    filterLabel: {
        fontSize: 12,
        textTransform: "uppercase",
        letterSpacing: 0.8,
        color: "#334155",
        marginBottom: 6,
        display: "block",
    },
    select: {
        width: "100%",
        height: 40,
        padding: "0 10px",
        borderRadius: 10,
        border: "1px solid rgba(15,23,42,.12)",
        background: "rgba(255,255,255,.92)",
    },

    mainCol: {
        display: "grid",
        gap: 20,
    },
    heroPanel: {
        display: "grid",
        gridTemplateColumns: "1.2fr .8fr",
        gap: 16,
        padding: 20,
        borderRadius: 24,
        background: "linear-gradient(180deg, rgba(255,255,255,.96), rgba(255,255,255,.82))",
        border: "1px solid rgba(15,23,42,.06)",
        boxShadow: "0 16px 40px rgba(2,6,23,.10)",
    },
    heroLeft: {},
    cropBadge: {
        alignSelf: "start",
        display: "inline-block",
        padding: "6px 10px",
        borderRadius: 999,
        background: `linear-gradient(135deg, ${ACCENT_FROM}, ${ACCENT_TO})`,
        color: "#FFFFFF",
        fontWeight: 800,
        fontSize: 12,
        letterSpacing: 1.1,
    },
    heroTitle: {
        margin: "8px 0 6px",
        fontSize: 26,
        fontWeight: 800,
        color: "#0f172a",
    },
    heroDesc: { margin: 0, color: "#475569" },
    heroChips: { marginTop: 12, display: "flex", flexWrap: "wrap", gap: 8 },
    chip: {
        padding: "6px 10px",
        borderRadius: 999,
        background: "rgba(15,23,42,.06)",
        border: "1px solid rgba(15,23,42,.08)",
        fontSize: 13,
    },
    heroRight: { display: "grid", placeItems: "center" },
    cropImgBig: {
        width: "100%",
        height: 220,
        borderRadius: 16,
        background: "linear-gradient(135deg, #e2e8f0, #f1f5f9)",
        border: "1px solid rgba(15,23,42,.06)",
        display: "grid",
        placeItems: "center",
        color: "#475569",
    },

    metricsRow: {
        display: "grid",
        gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
        gap: 64,
        alignItems: "end",
    },
    metricCard: {
        padding: 18,
        borderRadius: 40,
        background: `linear-gradient(135deg, ${ACCENT_FROM}, ${ACCENT_TO})`,
        border: "1px solid rgba(15,23,42,.06)",
        boxShadow: "0 12px 32px rgba(2,6,23,.08)",
    },
    metricCardAccent: {
        padding: 18,
        borderRadius: 20,
        background: `linear-gradient(135deg, ${ACCENT_FROM}, ${ACCENT_TO})`,
        border: "1px solid rgba(255,255,255,.35)",
        color: "#1f2937",
    },
    statValue: { fontSize: 28, fontWeight: 800 },
    statLabel: { color: "#475569", fontSize: 13 },

    chartPanel: {
        minHeight: 220,
        borderRadius: 20,
        background: "rgba(255,255,255,.92)",
        border: "1px solid rgba(15,23,42,.06)",
        boxShadow: "0 12px 32px rgba(2,6,23,.08)",
        display: "grid",
        placeItems: "center",
        color: "#334155",
    },

    githubBubble: {
        position: "fixed",
        right: 22,
        bottom: 22,
        width: 80,
        height: 80,
        borderRadius: "50%",
        background: `linear-gradient(135deg, ${ACCENT_FROM}, ${ACCENT_TO})`,
        display: "grid",
        placeItems: "center",
        textDecoration: "none",
        boxShadow: "0 12px 28px rgba(2, 6, 23, 0.25)",
        zIndex: 50,
    },
    scrollHint: {
        position: "absolute",
        bottom: 18,
        left: "50%",
        transform: "translateX(-50%)",
        fontSize: 12,
        color: "#475569",
        letterSpacing: 1.2,
        textTransform: "uppercase",
    },

    pillRow: { display: "flex", flexWrap: "wrap", gap: 8 },
    pill: {
        padding: "8px 12px",
        borderRadius: 999,
        border: "1px solid rgba(15,23,42,.12)",
        background: "rgba(255,255,255,.8)",
        cursor: "pointer",
        fontWeight: 700,
    },
    pillActive: {
        background: "#0f172a",
        color: "#fff",
        border: "1px solid rgba(255,255,255,.3)",
        boxShadow: "0 6px 18px rgba(2,6,23,.18)",
    },
};
