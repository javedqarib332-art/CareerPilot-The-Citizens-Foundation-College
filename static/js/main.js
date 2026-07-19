// TCF Discovery Agent — Frontend flow logic
console.log("TCF Discovery Agent JS — v3 loaded (radar chart + PDF export + resume, English only)");

let QUESTIONS = null;
let studentName = "";
let flatQuestions = [];
let currentIndex = 0;
let currentSkillIndex = 0;
let lastResult = null;

const answers = { riasec: [], big_five: [], skills: [] };
const STORAGE_KEY = "tcf_discovery_progress_v1";

const screens = {
  welcome: document.getElementById("screen-welcome"),
  questions: document.getElementById("screen-questions"),
  skills: document.getElementById("screen-skills"),
  loading: document.getElementById("screen-loading"),
  report: document.getElementById("screen-report"),
};

function showScreen(name) {
  Object.values(screens).forEach(s => s.classList.remove("active"));
  screens[name].classList.add("active");
}

const RIASEC_SCALE_LABELS = ["Strongly dislike", "Dislike", "Neutral", "Enjoy", "Strongly enjoy"];
const AGREE_SCALE_LABELS = ["Strongly disagree", "Disagree", "Neutral", "Agree", "Strongly agree"];

// ---------------------------------------------------------------------------
// PROGRESS SAVE / RESUME (localStorage)
// ---------------------------------------------------------------------------

function saveProgress() {
  const state = {
    studentName, currentIndex, currentSkillIndex, answers,
    stage: screens.skills.classList.contains("active") ? "skills" : "questions",
    savedAt: Date.now(),
  };
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch (e) { /* ignore quota errors */ }
}

function clearProgress() {
  try { localStorage.removeItem(STORAGE_KEY); } catch (e) { /* ignore */ }
}

function checkForSavedProgress() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const state = JSON.parse(raw);
    if (Date.now() - (state.savedAt || 0) > 7 * 24 * 60 * 60 * 1000) { clearProgress(); return; }

    document.getElementById("resume-banner").style.display = "block";

    document.getElementById("btn-resume").onclick = async () => {
      studentName = state.studentName;
      answers.riasec = state.answers.riasec;
      answers.big_five = state.answers.big_five;
      answers.skills = state.answers.skills;
      currentIndex = state.currentIndex;
      currentSkillIndex = state.currentSkillIndex;
      if (!QUESTIONS) await loadQuestions();
      if (state.stage === "skills") {
        showScreen("skills");
        renderSkill();
      } else {
        showScreen("questions");
        renderQuestion();
      }
    };
    document.getElementById("btn-restart").onclick = () => {
      clearProgress();
      document.getElementById("resume-banner").style.display = "none";
    };
  } catch (e) {
    console.error("Resume-progress check failed:", e);
  }
}

// ---------------------------------------------------------------------------
// QUESTION FLOW
// ---------------------------------------------------------------------------

async function loadQuestions() {
  const res = await fetch("/api/questions");
  QUESTIONS = await res.json();
  flatQuestions = [
    ...QUESTIONS.riasec.map(q => ({ type: "riasec", ...q })),
    ...QUESTIONS.big_five.map(q => ({ type: "big_five", ...q })),
  ];
}

document.getElementById("btn-start").addEventListener("click", async () => {
  studentName = document.getElementById("student-name").value.trim() || "Student";
  if (!QUESTIONS) await loadQuestions();
  currentIndex = 0;
  showScreen("questions");
  renderQuestion();
});

function renderQuestion() {
  const q = flatQuestions[currentIndex];
  document.getElementById("q-text").textContent = q.question;
  const section = q.type === "riasec" ? "Section 1 of 3 — Interests" : "Section 2 of 3 — Personality";
  document.getElementById("q-meta").textContent = section;
  const pct = (currentIndex / flatQuestions.length) * 66;
  document.getElementById("progress-fill").style.width = pct + "%";

  const labels = q.type === "riasec" ? RIASEC_SCALE_LABELS : AGREE_SCALE_LABELS;
  document.querySelectorAll("#q-scale button").forEach((btn, i) => {
    btn.querySelector("small").textContent = labels[i];
    btn.classList.remove("selected");
  });
}

document.getElementById("q-scale").addEventListener("click", (e) => {
  const btn = e.target.closest("button");
  if (!btn) return;
  const val = parseInt(btn.dataset.val, 10);
  const q = flatQuestions[currentIndex];

  btn.classList.add("selected");

  if (q.type === "riasec") {
    answers.riasec.push([q.category, currentIndex, val]);
  } else {
    answers.big_five.push([q.trait, currentIndex, val]);
  }

  saveProgress();

  setTimeout(() => {
    currentIndex++;
    if (currentIndex < flatQuestions.length) {
      renderQuestion();
    } else {
      currentSkillIndex = 0;
      showScreen("skills");
      renderSkill();
    }
  }, 180);
});

let selectedSkillVal = null;

function humanizeSkill(skill) {
  return skill.replace(/([A-Z])/g, " $1").trim();
}

function renderSkill() {
  selectedSkillVal = null;
  const skill = QUESTIONS.skills[currentSkillIndex];
  document.getElementById("skill-text").textContent = `Rate your ${humanizeSkill(skill)} (1 = weak, 5 = strong)`;
  document.getElementById("skill-reason").value = "";
  document.querySelectorAll("#skill-scale button").forEach(b => b.classList.remove("selected"));
  const pct = 66 + ((currentSkillIndex / QUESTIONS.skills.length) * 34);
  document.getElementById("progress-fill-skills").style.width = pct + "%";
}

document.getElementById("skill-scale").addEventListener("click", (e) => {
  const btn = e.target.closest("button");
  if (!btn) return;
  selectedSkillVal = parseInt(btn.dataset.val, 10);
  document.querySelectorAll("#skill-scale button").forEach(b => b.classList.remove("selected"));
  btn.classList.add("selected");
});

document.getElementById("btn-skill-next").addEventListener("click", async () => {
  if (selectedSkillVal === null) {
    alert("Please select a rating first.");
    return;
  }
  const skill = QUESTIONS.skills[currentSkillIndex];
  const reason = document.getElementById("skill-reason").value.trim() || "No reason given";
  answers.skills.push([skill, selectedSkillVal, reason]);
  saveProgress();

  currentSkillIndex++;
  if (currentSkillIndex < QUESTIONS.skills.length) {
    renderSkill();
  } else {
    await submitAssessment();
  }
});

async function submitAssessment() {
  showScreen("loading");
  const payload = { student_name: studentName, ...answers };

  const res = await fetch("/api/submit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();

  if (!data.ok) {
    alert("Something went wrong: " + data.error);
    return;
  }

  clearProgress();
  renderReport(data.result);
}

// ---------------------------------------------------------------------------
// RADAR CHART
// ---------------------------------------------------------------------------

function renderRadarChart(riasecScores) {
  const categories = ["R", "I", "A", "S", "E", "C"];
  const labels = { R: "Realistic", I: "Investigative", A: "Artistic", S: "Social", E: "Enterprising", C: "Conventional" };
  const size = 420, center = size / 2, maxScore = 30, radius = 100;
  const labelDist = 155;
  const angleStep = (Math.PI * 2) / categories.length;

  const points = categories.map((cat, i) => {
    const angle = i * angleStep - Math.PI / 2;
    const value = riasecScores[cat] || 0;
    const r = (value / maxScore) * radius;
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle),
      labelX: center + labelDist * Math.cos(angle),
      labelY: center + labelDist * Math.sin(angle),
      label: labels[cat],
      value,
    };
  });

  const polygonPoints = points.map(p => `${p.x},${p.y}`).join(" ");

  let gridRings = "";
  [0.25, 0.5, 0.75, 1].forEach(frac => {
    const ringPoints = categories.map((_, i) => {
      const angle = i * angleStep - Math.PI / 2;
      const r = frac * radius;
      return `${center + r * Math.cos(angle)},${center + r * Math.sin(angle)}`;
    }).join(" ");
    gridRings += `<polygon points="${ringPoints}" fill="none" stroke="#E3DFD5" stroke-width="1"/>`;
  });

  let axisLines = "";
  categories.forEach((_, i) => {
    const angle = i * angleStep - Math.PI / 2;
    const x = center + radius * Math.cos(angle);
    const y = center + radius * Math.sin(angle);
    axisLines += `<line x1="${center}" y1="${center}" x2="${x}" y2="${y}" stroke="#E3DFD5" stroke-width="1"/>`;
  });

  const labelTexts = points.map(p => `
    <text x="${p.labelX}" y="${p.labelY - 6}" text-anchor="middle" dominant-baseline="middle" font-size="13" font-weight="600" font-family="Inter, sans-serif" fill="#16233F">${p.label}</text>
    <text x="${p.labelX}" y="${p.labelY + 10}" text-anchor="middle" dominant-baseline="middle" font-size="11" font-family="Inter, sans-serif" fill="#6B7280">${p.value}/30</text>
  `).join("");

  return `
    <svg viewBox="0 0 ${size} ${size}" width="100%" style="max-width:440px; display:block; margin: 0 auto;">
      ${gridRings}
      ${axisLines}
      <polygon points="${polygonPoints}" fill="#C9A15A" fill-opacity="0.35" stroke="#C9A15A" stroke-width="2"/>
      ${points.map(p => `<circle cx="${p.x}" cy="${p.y}" r="3.5" fill="#16233F"/>`).join("")}
      ${labelTexts}
    </svg>
    <p style="text-align:center; font-size:12px; color:#6B7280; margin-top:8px;">Each point shows how strongly your answers leaned toward that category (out of 30).</p>
  `;
}

// ---------------------------------------------------------------------------
// REPORT RENDERING
// ---------------------------------------------------------------------------

function renderReport(result) {
  lastResult = result;
  const grid = document.getElementById("fields-grid");
  const radarContainer = document.getElementById("radar-container");
  grid.innerHTML = "";
  radarContainer.innerHTML = renderRadarChart(result.riasec_scores || {});

  if (result.valid_response === false) {
    document.getElementById("report-name").innerHTML = `A note for you, <em>${escapeHtml(studentName)}</em>`;
    document.getElementById("report-reason").textContent = result.reason || "We couldn't generate a confident suggestion from these answers.";
    showScreen("report");
    return;
  }

  document.getElementById("report-name").innerHTML = `Directions worth exploring, <em>${escapeHtml(studentName)}</em>`;
  result.suggested_fields.forEach(f => {
    const el = document.createElement("div");
    el.className = "field-pill";
    el.textContent = f;
    grid.appendChild(el);
  });
  document.getElementById("report-reason").textContent =
    result.student_report.split("Why:")[1]?.split("\n")[0]
      ? "Why: " + result.student_report.split("Why:")[1].split("\n")[0]
      : "";
  showScreen("report");
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// ---------------------------------------------------------------------------
// PDF EXPORT
// ---------------------------------------------------------------------------

document.getElementById("btn-download-pdf").addEventListener("click", () => {
  if (!lastResult) {
    alert("No result to export yet.");
    return;
  }
  if (!window.jspdf || !window.jspdf.jsPDF) {
    alert("PDF library didn't load. Please check your internet connection and try again.");
    console.error("window.jspdf is not available — the jsPDF script from cdnjs may not have loaded.");
    return;
  }

  try {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    const marginLeft = 20;
    let y = 24;

    doc.setFont("helvetica", "bold");
    doc.setFontSize(18);
    doc.text("TCF Discovery Agent — Results", marginLeft, y);
    y += 10;

    doc.setFontSize(11);
    doc.setFont("helvetica", "normal");
    doc.text(`Student: ${studentName}`, marginLeft, y);
    y += 6;
    doc.text(`Date: ${new Date().toLocaleDateString()}`, marginLeft, y);
    y += 12;

    if (lastResult.valid_response === false) {
      doc.setFont("helvetica", "bold");
      doc.text("A note for you:", marginLeft, y);
      y += 8;
      doc.setFont("helvetica", "normal");
      const lines = doc.splitTextToSize(lastResult.reason || "", 170);
      doc.text(lines, marginLeft, y);
    } else {
      doc.setFont("helvetica", "bold");
      doc.text("Suggested Field Directions:", marginLeft, y);
      y += 8;
      doc.setFont("helvetica", "normal");
      (lastResult.suggested_fields || []).forEach(f => {
        doc.text(`- ${f}`, marginLeft, y);
        y += 7;
      });
      y += 5;

      doc.setFont("helvetica", "bold");
      doc.text("RIASEC Scores (max 30 each):", marginLeft, y);
      y += 8;
      doc.setFont("helvetica", "normal");
      Object.entries(lastResult.riasec_scores || {}).forEach(([cat, val]) => {
        doc.text(`${cat}: ${val}`, marginLeft, y);
        y += 6;
      });
    }

    y += 10;
    doc.setFontSize(9);
    doc.setTextColor(120, 120, 120);
    const disclaimerLines = doc.splitTextToSize(
      "This isn't a final decision - it's a starting point for your counselling session. A TCF counsellor will go through this with you.",
      170
    );
    doc.text(disclaimerLines, marginLeft, y);

    doc.save(`TCF_Discovery_${studentName.replace(/\s+/g, "_")}.pdf`);
  } catch (err) {
    console.error("PDF generation failed:", err);
    alert("Something went wrong generating the PDF. Check the browser console for details.");
  }
});

// ---------------------------------------------------------------------------
// INIT
// ---------------------------------------------------------------------------

checkForSavedProgress();
