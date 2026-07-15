// TCF Discovery Agent — Frontend flow logic

let QUESTIONS = null;
let studentName = "";
let flatQuestions = [];   // combined riasec + big_five queue
let currentIndex = 0;
let currentSkillIndex = 0;

const answers = { riasec: [], big_five: [], skills: [] };

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
  const pct = (currentIndex / flatQuestions.length) * 66; // reserve last third for skills
  document.getElementById("progress-fill").style.width = pct + "%";
}

document.getElementById("q-scale").addEventListener("click", (e) => {
  const btn = e.target.closest("button");
  if (!btn) return;
  const val = parseInt(btn.dataset.val, 10);
  const q = flatQuestions[currentIndex];

  if (q.type === "riasec") {
    answers.riasec.push([q.category, currentIndex, val]);
  } else {
    answers.big_five.push([q.trait, currentIndex, val]);
  }

  currentIndex++;
  if (currentIndex < flatQuestions.length) {
    renderQuestion();
  } else {
    currentSkillIndex = 0;
    showScreen("skills");
    renderSkill();
  }
});

let selectedSkillVal = null;

function renderSkill() {
  selectedSkillVal = null;
  const skill = QUESTIONS.skills[currentSkillIndex];
  document.getElementById("skill-text").textContent = `Rate your ${humanizeSkill(skill)} (1 = weak, 5 = strong)`;
  document.getElementById("skill-reason").value = "";
  document.querySelectorAll("#skill-scale button").forEach(b => b.style.background = "");
  const pct = 66 + ((currentSkillIndex / QUESTIONS.skills.length) * 34);
  document.getElementById("progress-fill-skills").style.width = pct + "%";
}

function humanizeSkill(skill) {
  return skill.replace(/([A-Z])/g, " $1").trim();
}

document.getElementById("skill-scale").addEventListener("click", (e) => {
  const btn = e.target.closest("button");
  if (!btn) return;
  selectedSkillVal = parseInt(btn.dataset.val, 10);
  document.querySelectorAll("#skill-scale button").forEach(b => b.style.background = "");
  btn.style.background = "#C9A15A";
});

document.getElementById("btn-skill-next").addEventListener("click", async () => {
  if (selectedSkillVal === null) {
    alert("Please select a rating first.");
    return;
  }
  const skill = QUESTIONS.skills[currentSkillIndex];
  const reason = document.getElementById("skill-reason").value.trim() || "No reason given";
  answers.skills.push([skill, selectedSkillVal, reason]);

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

  renderReport(data.result);
}

function renderReport(result) {
  const grid = document.getElementById("fields-grid");
  grid.innerHTML = "";

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
