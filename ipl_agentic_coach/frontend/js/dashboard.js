const API_BASE =
    window.__API_BASE__ ||
    document.querySelector('meta[name="api-base"]')?.content ||
    localStorage.getItem("apiBase") ||
    window.location.origin;

const DEFAULT_USERNAME = "Sridhar";

function getCurrentUsername() {
    const input = document.getElementById("username_input");
    const value = input?.value?.trim();
    if (value) return value;
    return localStorage.getItem("ipl_username") || DEFAULT_USERNAME;
}

function initializeUsername() {
    const input = document.getElementById("username_input");
    if (!input) return;

    const stored = localStorage.getItem("ipl_username") || DEFAULT_USERNAME;
    input.value = stored;

    const persistAndReload = () => {
        const username = input.value.trim() || DEFAULT_USERNAME;
        input.value = username;
        localStorage.setItem("ipl_username", username);
        loadDecisionHistory();
    };

    input.addEventListener("change", persistAndReload);
    input.addEventListener("blur", persistAndReload);
}

/* ══════════════════════════════════════════
   Field Positions — Data, Init, Interactivity
   ══════════════════════════════════════════ */
const FIELD_POSITIONS = [
    { name: "Slip",           x: 63, y: 58, abbr: "SL",  tip: "Behind batsman on off side — catches thick edges" },
    { name: "Gully",          x: 69, y: 47, abbr: "GU",  tip: "Square off side — catches slashed or cut shots" },
    { name: "Point",          x: 77, y: 52, abbr: "PT",  tip: "Square off side — restricts cuts and late drives" },
    { name: "Cover",          x: 73, y: 36, abbr: "CV",  tip: "Off side — stops drives through the covers" },
    { name: "Mid-off",        x: 57, y: 21, abbr: "MO",  tip: "Straight off side — restricts straight drives" },
    { name: "Mid-on",         x: 43, y: 21, abbr: "MN",  tip: "Straight leg side — restricts on-drives" },
    { name: "Midwicket",      x: 27, y: 45, abbr: "MW",  tip: "Square leg side — covers pulls & flicks" },
    { name: "Square Leg",     x: 23, y: 56, abbr: "SQ",  tip: "Fine leg side — close catching position" },
    { name: "Fine Leg",       x: 33, y: 74, abbr: "FL",  tip: "Behind on leg side — covers glances & sweeps" },
    { name: "Long On",        x: 41, y: 87, abbr: "LN",  tip: "Deep leg-side boundary — saving lofted on-drives" },
    { name: "Long Off",       x: 60, y: 87, abbr: "LO",  tip: "Deep off-side boundary — saving lofted off-drives" },
    { name: "Deep Midwicket", x: 16, y: 63, abbr: "DM",  tip: "Deep leg side — covers big pulls to the boundary" },
    { name: "Deep Cover",     x: 81, y: 32, abbr: "DC",  tip: "Deep off side — saves slashed drives to boundary" },
    { name: "Third Man",      x: 69, y: 74, abbr: "TM",  tip: "Fine off side behind wicket — covers deflections" },
];

const selectedPositions = new Set();

function initFieldPositions() {
    const oval = document.getElementById("cricket-field-oval");
    const chips = document.getElementById("position-chips");
    if (!oval || !chips) return;

    FIELD_POSITIONS.forEach(pos => {
        // ── Dot on visual field ──
        const dot = document.createElement("div");
        dot.className = "field-pos-dot";
        dot.id = `dot-${pos.name.replace(/\s+/g, "-")}`;
        dot.style.left = pos.x + "%";
        dot.style.top  = pos.y + "%";
        dot.innerHTML  = `${pos.abbr}<span class="pos-tooltip"><strong>${pos.name}</strong><br>${pos.tip}</span>`;
        dot.addEventListener("click", () => togglePosition(pos.name));
        oval.appendChild(dot);

        // ── Chip ──
        const chip = document.createElement("div");
        chip.className = "pos-chip";
        chip.id = `chip-${pos.name.replace(/\s+/g, "-")}`;
        chip.title = pos.tip;
        chip.innerHTML = `<i class="fa-solid fa-check chip-check"></i>${pos.name}`;
        chip.addEventListener("click", () => togglePosition(pos.name));
        chips.appendChild(chip);
    });
}

function togglePosition(name) {
    if (selectedPositions.has(name)) {
        selectedPositions.delete(name);
    } else {
        selectedPositions.add(name);
    }
    updateFieldUI();
    updateTacticsSummary();
}

function updateFieldUI() {
    const count  = selectedPositions.size;
    const badge  = document.getElementById("field-count");
    const display = document.getElementById("selected-display");

    badge.textContent = `${count} selected`;
    badge.classList.toggle("has-selection", count > 0);

    FIELD_POSITIONS.forEach(pos => {
        const key    = pos.name.replace(/\s+/g, "-");
        const active = selectedPositions.has(pos.name);
        const dot    = document.getElementById(`dot-${key}`);
        const chip   = document.getElementById(`chip-${key}`);
        if (dot)  dot.classList.toggle("active", active);
        if (chip) chip.classList.toggle("selected", active);
    });

    if (count === 0) {
        display.innerHTML = `<span style="color:var(--text-muted);font-style:italic">No positions selected — click on the field diagram or chips above</span>`;
    } else {
        display.innerHTML = [...selectedPositions].map(p =>
            `<span class="selected-pos-tag"><i class="fa-solid fa-map-pin"></i> ${p}</span>`
        ).join("");
    }
}

function clearFieldSelections() {
    selectedPositions.clear();
    updateFieldUI();
    updateTacticsSummary();
}

function updateTacticsSummary() {
    const summary  = document.getElementById("tactics-summary");
    if (!summary) return;
    const bowler   = document.getElementById("bowler_input")?.value;
    const strategy = document.getElementById("strategy_input")?.value.trim();
    const count    = selectedPositions.size;

    if (!bowler && count === 0 && !strategy) {
        summary.classList.remove("visible");
        return;
    }

    const parts = [];
    if (bowler)  parts.push(`<span class="ts-val">${bowler}</span> bowling`);
    if (count > 0) {
        const preview = [...selectedPositions].slice(0, 3).join(", ");
        parts.push(`${count} fielder${count > 1 ? "s" : ""} placed (<span class="ts-val">${preview}${count > 3 ? "…" : ""}</span>)`);
    }
    if (strategy) parts.push(`strategy: "<span class="ts-val">${strategy.slice(0, 55)}${strategy.length > 55 ? "…" : ""}</span>"`);

    summary.innerHTML = `<i class="fa-solid fa-eye" style="color:#FBBC05"></i><span class="ts-label">Live Preview:</span> ${parts.join(" · ")}`;
    summary.classList.add("visible");
}

/* ══════════════════════════════════════════
   Realistic Live Ground Animation
   ══════════════════════════════════════════ */
function easeInOutQuad(value) {
    return value < 0.5 ? 2 * value * value : 1 - Math.pow(-2 * value + 2, 2) / 2;
}

function easeOutCubic(value) {
    return 1 - Math.pow(1 - value, 3);
}

function lerp(start, end, progress) {
    return start + (end - start) * progress;
}

function initLiveGroundAnimation() {
    const ground = document.querySelector(".ground-oval");
    const ball = document.querySelector(".live-ball");
    const trail = document.querySelector(".ball-trail");

    if (!ground || !ball || !trail) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const fielderConfig = [
        { selector: ".f1", x: 16, y: 44 },
        { selector: ".f2", x: 26, y: 24 },
        { selector: ".f3", x: 43, y: 14 },
        { selector: ".f4", x: 72, y: 20 },
        { selector: ".f5", x: 86, y: 44 },
        { selector: ".f6", x: 74, y: 78 },
        { selector: ".f7", x: 24, y: 80 },
    ];

    const fielders = fielderConfig
        .map((config, index) => {
            const element = ground.querySelector(config.selector);
            return element ? { ...config, element, index } : null;
        })
        .filter(Boolean);

    if (!fielders.length) return;

    const shotTargets = [
        { x: 74, y: 34 },
        { x: 69, y: 22 },
        { x: 81, y: 44 },
        { x: 31, y: 30 },
        { x: 21, y: 56 },
        { x: 58, y: 16 },
    ];

    let lastX = 49;
    let lastY = 70;
    let currentCycle = -1;
    let target = shotTargets[0];
    const cycleDurationMs = 4200;
    const startTime = performance.now();

    function animateFrame(now) {
        const elapsedMs = now - startTime;
        const cycle = Math.floor(elapsedMs / cycleDurationMs);

        if (cycle !== currentCycle) {
            currentCycle = cycle;
            target = shotTargets[Math.floor(Math.random() * shotTargets.length)];
        }

        const phase = (elapsedMs % cycleDurationMs) / cycleDurationMs;

        let ballX;
        let ballY;

        if (phase < 0.45) {
            const progress = easeInOutQuad(phase / 0.45);
            ballX = lerp(49, 51.8, progress);
            ballY = lerp(70, 46.5, progress) + Math.sin(progress * Math.PI * 1.9) * 0.8;
        } else {
            const progress = easeOutCubic((phase - 0.45) / 0.55);
            ballX = lerp(51.8, target.x, progress);
            ballY = lerp(46.5, target.y, progress) - Math.sin(progress * Math.PI) * 2.2;
        }

        const deltaX = ballX - lastX;
        const deltaY = ballY - lastY;
        const velocity = Math.hypot(deltaX, deltaY);
        const angle = Math.atan2(deltaY, deltaX) * (180 / Math.PI);

        ball.style.left = `${ballX}%`;
        ball.style.top = `${ballY}%`;

        const trailScale = Math.max(0.24, Math.min(1.26, velocity * 8.5));
        const trailOpacity = Math.max(0.2, Math.min(0.85, velocity * 4.7));
        trail.style.left = `${ballX}%`;
        trail.style.top = `${ballY}%`;
        trail.style.opacity = `${trailOpacity}`;
        trail.style.transform = `rotate(${angle + 180}deg) scaleX(${trailScale})`;

        const groundWidth = ground.clientWidth;
        const groundHeight = ground.clientHeight;
        const ballPxX = (ballX / 100) * groundWidth;
        const ballPxY = (ballY / 100) * groundHeight;

        let nearestIndex = -1;
        let nearestDistance = Number.POSITIVE_INFINITY;
        fielders.forEach((fielder, index) => {
            const fx = (fielder.x / 100) * groundWidth;
            const fy = (fielder.y / 100) * groundHeight;
            const distance = Math.hypot(ballPxX - fx, ballPxY - fy);
            if (distance < nearestDistance) {
                nearestDistance = distance;
                nearestIndex = index;
            }
        });

        fielders.forEach((fielder, index) => {
            const fx = (fielder.x / 100) * groundWidth;
            const fy = (fielder.y / 100) * groundHeight;
            const toBallX = ballPxX - fx;
            const toBallY = ballPxY - fy;
            const distance = Math.max(1, Math.hypot(toBallX, toBallY));

            const reactionRadius = 160;
            const isPrimaryResponder = index === nearestIndex;
            const reactionStrength = isPrimaryResponder ? Math.max(0, 1 - nearestDistance / reactionRadius) : 0;

            const reactX = (toBallX / distance) * reactionStrength * 8;
            const reactY = (toBallY / distance) * reactionStrength * 8;
            const idleBob = Math.sin(elapsedMs / 540 + index * 0.8) * 1.6;
            const scale = 1 + reactionStrength * 0.12;
            fielder.element.style.transform = `translate(${reactX.toFixed(2)}px, ${(reactY + idleBob).toFixed(2)}px) scale(${scale.toFixed(3)})`;
            fielder.element.style.opacity = `${Math.min(1, 0.86 + reactionStrength * 0.18)}`;
        });

        lastX = ballX;
        lastY = ballY;
        requestAnimationFrame(animateFrame);
    }

    requestAnimationFrame(animateFrame);
}

/* ══════════════════════════════════════════
   Animated Cricket Field Background Canvas
   ══════════════════════════════════════════ */
(function initCanvas() {
    const canvas = document.getElementById("bg-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    function resize() {
        canvas.width  = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener("resize", resize);

    // Draw concentric cricket-oval rings
    function drawField() {
        const cx = canvas.width  * 0.72;
        const cy = canvas.height * 0.38;
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Outer oval
        ctx.beginPath();
        ctx.ellipse(cx, cy, 380, 260, 0, 0, Math.PI * 2);
        ctx.strokeStyle = "rgba(255,215,0,0.06)";
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Inner circle (30-yard)
        ctx.beginPath();
        ctx.ellipse(cx, cy, 200, 140, 0, 0, Math.PI * 2);
        ctx.strokeStyle = "rgba(66,133,244,0.06)";
        ctx.lineWidth = 1;
        ctx.stroke();

        // Pitch rectangle
        ctx.beginPath();
        ctx.rect(cx - 14, cy - 70, 28, 140);
        ctx.strokeStyle = "rgba(255,255,255,0.05)";
        ctx.stroke();

        // Crease lines
        [-50, 50].forEach(y => {
            ctx.beginPath();
            ctx.moveTo(cx - 20, cy + y);
            ctx.lineTo(cx + 20, cy + y);
            ctx.strokeStyle = "rgba(255,255,255,0.07)";
            ctx.stroke();
        });
    }

    // Floating particles
    const particles = Array.from({ length: 40 }, () => ({
        x: Math.random() * window.innerWidth,
        y: Math.random() * window.innerHeight,
        r: Math.random() * 2 + 0.5,
        dx: (Math.random() - 0.5) * 0.4,
        dy: -Math.random() * 0.5 - 0.2,
        color: ["#FFD700","#4285F4","#EA4335","#34A853","#FBBC05"][Math.floor(Math.random()*5)],
        alpha: Math.random() * 0.4 + 0.1,
    }));

    function animateParticles() {
        drawField();
        particles.forEach(p => {
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fillStyle = p.color + Math.round(p.alpha * 255).toString(16).padStart(2, "0");
            ctx.fill();
            p.x += p.dx;
            p.y += p.dy;
            if (p.y < -10) { p.y = canvas.height + 10; p.x = Math.random() * canvas.width; }
            if (p.x < -10 || p.x > canvas.width + 10) p.dx *= -1;
        });
        requestAnimationFrame(animateParticles);
    }
    animateParticles();
})();

/* ══════════════════════════════════════════
   Leaderboard
   ══════════════════════════════════════════ */
function getRankBadge(index) {
    if (index === 0) return "🥇";
    if (index === 1) return "🥈";
    if (index === 2) return "🥉";
    return `#${index + 1}`;
}

function getRankClass(index) {
    if (index === 0) return "gold";
    if (index === 1) return "silver";
    if (index === 2) return "bronze";
    return "";
}

function renderLeaderboard(entries) {
    const leaderboard = document.getElementById("leaderboard");
    if (!entries?.length) {
        leaderboard.innerHTML = `<p style="color:var(--text-muted);text-align:center;padding:20px">No leaderboard data yet.</p>`;
        return;
    }

    leaderboard.innerHTML = entries.map((entry, index) => `
        <div class="leaderboard-item ${getRankClass(index)}">
            <div class="rank-badge ${index > 2 ? 'rank-num' : ''}">${getRankBadge(index)}</div>
            <div class="lb-info">
                <h4>${entry.username}</h4>
                <p>Fan Coach</p>
            </div>
            <div class="lb-score">${entry.points.toLocaleString()} <span>pts</span></div>
        </div>
    `).join("");
}

/* ══════════════════════════════════════════
    Decision Output
    ══════════════════════════════════════════ */
function renderFeedback(evaluation) {
    const feedback = document.getElementById("decision-result");
    if (!feedback) return;
    const impact   = evaluation.simulation_impact || {};
    const score    = Math.round(evaluation.score * 100);
    const histScore = Math.round(evaluation.historical_score * 100);
    const wicketChance = Math.round((impact.wicket_chance || 0) * 100);
    const runsSaved    = impact.runs_saved || 0;
    const pointsEarned = Math.max(1, score);
    const appreciation = getAppreciationBand(score);

    feedback.innerHTML = `
        <div class="feedback-item success">
            <div class="fi-icon"><i class="fa-solid fa-circle-check"></i></div>
            <div>
                <h3>AI Tactical Analysis Complete</h3>
                <p>${evaluation.feedback}</p>
            </div>
        </div>
        <div class="appreciation-banner ${appreciation.tone}" id="appreciation-banner">
            <i class="fa-solid fa-sparkles"></i>
            <span>${appreciation.text}</span>
        </div>
        <div class="feedback-item info">
            <div class="fi-icon"><i class="fa-solid fa-chart-bar"></i></div>
            <div>
                <h3>Score Breakdown</h3>
                <p>
                    Final Score: <strong><span id="animated-score">0</span> / 100</strong><br/>
                    Historical Fit: <strong>${histScore}%</strong><br/>
                    Wicket Chance: <strong>${wicketChance}%</strong><br/>
                    Runs Saved: <strong>${runsSaved}</strong><br/>
                    Points Earned: <strong class="points-earned" id="points-earned">+${pointsEarned}</strong>
                </p>
            </div>
        </div>
        <div class="score-burst" id="score-burst">+${pointsEarned} pts</div>
    `;

    animateScoreValue(score);
    triggerAppreciationAnimation();
}

function getAppreciationBand(score) {
    if (score >= 90) return { tone: "elite", text: "Legendary move! Captain-level excellence!" };
    if (score >= 75) return { tone: "great", text: "Brilliant tactical call. Huge impact!" };
    if (score >= 60) return { tone: "good", text: "Strong decision. Keep that pressure on." };
    if (score >= 40) return { tone: "okay", text: "Good attempt. Fine-tune field and bowler combo." };
    return { tone: "learn", text: "Learning moment. Try a tighter field setup next ball." };
}

function animateScoreValue(targetScore) {
    const scoreEl = document.getElementById("animated-score");
    if (!scoreEl) return;

    const duration = 900;
    const startTime = performance.now();

    function step(now) {
        const elapsed = now - startTime;
        const progress = Math.min(1, elapsed / duration);
        const eased = 1 - Math.pow(1 - progress, 3);
        scoreEl.textContent = String(Math.round(targetScore * eased));

        if (progress < 1) requestAnimationFrame(step);
    }

    requestAnimationFrame(step);
}

function triggerAppreciationAnimation() {
    const burst = document.getElementById("score-burst");
    const points = document.getElementById("points-earned");
    const banner = document.getElementById("appreciation-banner");

    if (burst) {
        burst.classList.remove("show");
        void burst.offsetWidth;
        burst.classList.add("show");
    }

    if (points) {
        points.classList.remove("pulse");
        void points.offsetWidth;
        points.classList.add("pulse");
    }

    if (banner) {
        banner.classList.remove("show");
        void banner.offsetWidth;
        banner.classList.add("show");
    }
}

function renderHistory(historyItems) {
    const container = document.getElementById("history-list");
    if (!container) return;

    if (!historyItems?.length) {
        container.innerHTML = `<p class="history-empty">No tactical decisions yet. Submit one to see history here.</p>`;
        return;
    }

    container.innerHTML = historyItems.map(item => {
        const score = Math.round((item.score || 0) * 100);
        const points = Math.max(1, score);
        const ts = item.timestamp ? new Date(item.timestamp).toLocaleString() : "-";
        return `
            <div class="history-item">
                <div class="history-top">
                    <span class="history-ball">Ball ${item.ball_number}</span>
                    <span class="history-score">${score}/100</span>
                    <span class="history-points">+${points} pts</span>
                </div>
                <div class="history-body">
                    <p><strong>Field:</strong> ${item.field_placement || "-"}</p>
                    <p><strong>Bowler:</strong> ${item.bowling_change || "-"}</p>
                    <p><strong>Strategy:</strong> ${item.tactical_strategy || "-"}</p>
                    <p><strong>AI Feedback:</strong> ${item.feedback || "-"}</p>
                </div>
                <div class="history-time">${ts}</div>
            </div>
        `;
    }).join("");
}

async function loadDecisionHistory() {
    try {
        const username = getCurrentUsername();
        const response = await fetch(`${API_BASE}/decisions/history/${encodeURIComponent(username)}?limit=25`);
        if (!response.ok) {
            renderHistory([]);
            return;
        }
        const data = await response.json();
        renderHistory(data);
    } catch (_) {
        renderHistory([]);
    }
}

/* ══════════════════════════════════════════
   API Calls
   ══════════════════════════════════════════ */
async function loadLeaderboard() {
    try {
        const response = await fetch(`${API_BASE}/users/leaderboard/top?limit=10`);
        if (!response.ok) return;
        const data = await response.json();
        renderLeaderboard(data);
    } catch (_) {}
}

async function submitDecision() {
    const field    = [...selectedPositions].join(", ");
    const bowler   = document.getElementById("bowler_input").value.trim();
    const strategy = document.getElementById("strategy_input").value.trim();
    const username = getCurrentUsername();

    if (selectedPositions.size === 0) {
        alert("Please select at least one field placement position.");
        return;
    }
    if (!bowler) {
        alert("Please choose a bowler.");
        return;
    }
    if (!strategy) {
        alert("Please describe your tactical strategy.");
        return;
    }
    if (!username) {
        alert("Please enter a username.");
        return;
    }

    const submitBtn = document.querySelector(".submit-btn");
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Evaluating with AI Agents...`;

    try {
        const payload = {
            username,
            field_input:    field,
            bowler_input:   bowler,
            strategy_input: strategy,
            ball_number:    19,
        };

        const response = await fetch(`${API_BASE}/decisions/submit`, {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify(payload),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Failed to submit decision");
        }

        const result = await response.json();
        renderFeedback(result.evaluation);
        renderLeaderboard(result.leaderboard);
        loadDecisionHistory();

        submitBtn.innerHTML = `<i class="fa-solid fa-circle-check"></i> Decision Submitted Successfully`;
    } catch (error) {
        alert(error.message || "Unable to submit decision right now.");
        submitBtn.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> Submission Failed`;
    } finally {
        setTimeout(() => {
            submitBtn.disabled = false;
            submitBtn.innerHTML = `<i class="fa-solid fa-paper-plane"></i> Submit Tactical Decision`;
        }, 2500);
    }
}

/* Navbar scroll highlight */
window.addEventListener("scroll", () => {
    const pills = document.querySelectorAll(".nav-pill");
    const sections = ["decision", "field-ground", "leaderboard-section", "history-section"];
    let current = "";
    sections.forEach(id => {
        const el = document.getElementById(id);
        if (el && window.scrollY >= el.offsetTop - 120) current = id;
    });
    pills.forEach(p => {
        p.classList.toggle("active", p.getAttribute("href") === `#${current}`);
    });
});

window.addEventListener("load", () => {
    initializeUsername();
    initFieldPositions();
    initLiveGroundAnimation();
    loadLeaderboard();
    loadDecisionHistory();
});