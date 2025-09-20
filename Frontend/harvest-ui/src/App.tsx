import { useState } from "react";
import scytheLogo from "./assets/scythewheatlogo.png";

export default function App() {
    const [location, setLocation] = useState("");
    const [soil, setSoil] = useState("");
    const [ground, setGround] = useState("");
    const [price, setPrice] = useState("");

    const handleExplore = () => {
        const el = document.getElementById("details");
        el?.scrollIntoView({ behavior: "smooth", block: "start" });
    };

    return (
        <div style={styles.page}>
            {/* HERO / SPLASH */}
            <header style={styles.hero}>
                <div style={styles.cardWrap}>
                    <div style={styles.logoWrap} aria-label="Harvest logo">
                        <img src={scytheLogo} alt="Harvest Logo" style={{ maxWidth: "100%", maxHeight: "100%" }} />
                    </div>

                    <div style={styles.form}>
                        <label style={styles.label} htmlFor="location">Location</label>
                        <input
                            id="location"
                            placeholder="City / Town, State"
                            style={styles.input}
                            value={location}
                            onChange={(e) => setLocation(e.target.value)}
                        />

                        <label style={styles.label} htmlFor="soil">Soil Type</label>
                        <select
                            id="soil"
                            style={styles.input}
                            value={soil}
                            onChange={(e) => setSoil(e.target.value)}
                        >
                            <option value="" disabled>
                                Select soil type
                            </option>
                            <option>Sandy</option>
                            <option>Loamy</option>
                            <option>Clay</option>
                            <option>Silt</option>
                            <option>Peat</option>
                            <option>Chalky</option>
                        </select>

                        <label style={styles.label} htmlFor="ground">Ground Type</label>
                        <select
                            id="ground"
                            style={styles.input}
                            value={ground}
                            onChange={(e) => setGround(e.target.value)}
                        >
                            <option value="" disabled>
                                Select ground type
                            </option>
                            <option>Flat</option>
                            <option>Gentle Slope</option>
                            <option>Hilly</option>
                            <option>Terraced</option>
                        </select>

                        <label style={styles.label} htmlFor="price">Price Range</label>
                        <select
                            id="price"
                            style={styles.input}
                            value={price}
                            onChange={(e) => setPrice(e.target.value)}
                        >
                            <option value="" disabled>
                                Choose budget (monthly)
                            </option>
                            <option>Under $500</option>
                            <option>$500 – $1,000</option>
                            <option>$1,000 – $2,500</option>
                            <option>$2,500 – $5,000</option>
                            <option>$5,000+</option>
                        </select>

                        <button style={styles.cta} onClick={handleExplore}>Explore</button>
                    </div>
                </div>
                {/* GitHub logo bubble */}
                <a href="#" style={styles.githubBubble} title="GitHub Link">
                    <img
                        src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"
                        alt="GitHub"
                        style={{ width: 48, height: 48 }}
                    />
                </a>

                <div style={styles.scrollHint}>Scroll</div>
            </header>

            {/* DETAILS */}
            <main id="details" style={styles.main}>
                <section style={styles.section}>
                    <h2 style={styles.h2}>Project</h2>
                    <p style={styles.p}>
                        Harvest helps land owners choose the most profitable crops using soil, ground
                        profile, local pricing, and weather. The short‑term view recommends monthly
                        actions; the long‑term view plans the next year using 10‑year weather normals.
                    </p>
                    <ul style={styles.list}>
                        <li>Short‑term: immediate actions for this month</li>
                        <li>Long‑term: 12‑month plan using historical climate</li>
                        <li>Inputs: location, soil, ground type, budget</li>
                        <li>Outputs: crop recommendations, expected yield & margin</li>
                    </ul>
                </section>

                <section style={styles.section}>
                    <h2 style={styles.h2}>Team</h2>
                    <div style={styles.teamGrid}>
                        {[
                            { name: "弟弟", role: "Product & Data", initials: "D" },
                            { name: "Teammate A", role: "Backend / ML", initials: "A" },
                            { name: "Teammate B", role: "Frontend", initials: "B" },
                            { name: "Teammate C", role: "Research", initials: "C" },
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
                    <h2 style={styles.h2}>Tech & Status</h2>
                    <div style={styles.kvRow}>
                        <div style={styles.kv}><span style={styles.k}>Frontend</span><span>React + Vite (TS)</span></div>
                        <div style={styles.kv}><span style={styles.k}>Model</span><span>Rule‑based + ML (WIP)</span></div>
                        <div style={styles.kv}><span style={styles.k}>Data</span><span>Weather, crops, prices, soils</span></div>
                    </div>
                    <p style={styles.p}>Demo screens are read‑only for now; Explore triggers a smooth scroll. Backend wiring comes next.</p>
                </section>

                <footer style={styles.footer}>
                    <small>© {new Date().getFullYear()} Harvest. All rights reserved.</small>
                </footer>
            </main>
        </div>
    );
}

const styles: Record<string, React.CSSProperties> = {
    page: {
        minHeight: "100svh",
        display: "flex",
        flexDirection: "column",
        background: "#f3f5f7",
        fontFamily: "Inter, system-ui, Avenir, Helvetica, Arial, sans-serif",
        color: "#0f172a",
    },
    hero: {
        minHeight: "100svh",
        display: "grid",
        placeItems: "center",
        position: "relative",
        background: "radial-gradient(1200px 600px at 70% -10%, #f3f5f7 0%, #e9eef2 40%, #e6ecf1 60%, #e2e9ef 100%)",
    },
    cardWrap: {
        display: "flex",
        flexDirection: "column" as const,
        alignItems: "center",
        gap: 24,
        width: "min(560px, 92vw)",
        padding: 28,
        borderRadius: 24,
        background: "white",
        boxShadow: "0 10px 35px rgba(2, 6, 23, 0.12)",
    },
    logoWrap: {
        display: "grid",
        placeItems: "center",
        width: 160,
        height: 160,
    },
    form: {
        width: "100%",
        display: "grid",
        gridTemplateColumns: "1fr",
        gap: 10,
    },
    label: {
        fontSize: 12,
        letterSpacing: 0.6,
        textTransform: "uppercase" as const,
        color: "#475569",
    },
    input: {
        width: "100%",
        height: 48,
        padding: "0 14px",
        borderRadius: 12,
        outline: "none",
        border: "1px solid #e2e8f0",
        background: "#f8fafc",
        fontSize: 16,
    },
    cta: {
        marginTop: 12,
        height: 52,
        borderRadius: 14,
        border: "none",
        background: "#0f172a",
        color: "white",
        fontSize: 18,
        fontWeight: 700,
        letterSpacing: 0.2,
        cursor: "pointer",
        boxShadow: "0 12px 24px rgba(15,23,42,.15)",
    },
    githubBubble: {
        position: "fixed",
        right: 24,
        bottom: 24,
        width: 92,
        height: 92,
        borderRadius: "50%",
        background: "#0f172a",
        display: "grid",
        placeItems: "center",
        textDecoration: "none",
        boxShadow: "0 12px 28px rgba(2, 6, 23, 0.25)",
        zIndex: 10,
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
    main: {
        display: "grid",
        gap: 28,
        padding: "56px 6vw 96px",
        background: "#fff",
    },
    section: {
        width: "min(1000px, 100%)",
        margin: "0 auto",
        background: "#f8fafc",
        border: "1px solid #e2e8f0",
        borderRadius: 20,
        padding: 24,
    },
    h2: {
        margin: 0,
        fontSize: 24,
    },
    p: {
        lineHeight: 1.6,
    },
    list: {
        marginTop: 8,
    },
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
        background: "#0f172a",
        color: "#fff",
        display: "grid",
        placeItems: "center",
        fontWeight: 800,
    },
    memberName: { fontWeight: 700 },
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
    k: { fontWeight: 700, marginRight: 8 },
    footer: {
        width: "min(1000px, 100%)",
        margin: "0 auto",
        textAlign: "center" as const,
        color: "#64748b",
    },
};
