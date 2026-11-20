// Address of our FastAPI backend
const API = "/api";

const MEDALS = { 1: "🥇", 2: "🥈", 3: "🥉" };

// Picture and short text for each subject card
const SUBJECT_INFO = {
    "Mathematics": { image: "img/mathematics.svg", text: "Algebra, geometry, number theory and logic problems." },
    "Physics": { image: "img/physics.svg", text: "Mechanics, electricity, optics and experimental tasks." },
    "Informatics": { image: "img/informatics.svg", text: "Algorithms, data structures and programming problems." },
};


// ---------- Helpers ----------

function showStatus(id, text, type) {
    const status = document.getElementById(id);
    status.textContent = text;
    status.className = "status " + (type || "");
}

// Turns an error response from FastAPI into a readable message
function errorMessage(data) {
    // Our own errors: {"detail": "some text"}
    if (typeof data.detail === "string") {
        return data.detail;
    }
    // Pydantic validation errors (422): {"detail": [{ "msg": "..." }]}
    if (Array.isArray(data.detail)) {
        return data.detail.map(err => err.msg).join(", ");
    }
    return "Something went wrong";
}

// GET request that returns JSON
async function getJSON(path) {
    const response = await fetch(API + path);
    return response.json();
}


// ---------- Hero: numbers and current olympiad ----------

async function loadStats() {
    try {
        const olympiads = await getJSON("/olympiads");
        const schools = await getJSON("/schools");
        const students = await getJSON("/students");
        const subjects = await getJSON("/subjects");

        document.getElementById("stat-olympiads").textContent = olympiads.length;
        document.getElementById("stat-schools").textContent = schools.length;
        document.getElementById("stat-students").textContent = students.length;
        document.getElementById("stat-subjects").textContent = subjects.length;

        showCurrentOlympiad(olympiads);
    } catch (error) {
        document.getElementById("hero-status").textContent = "Server is not available";
    }
}

function showCurrentOlympiad(olympiads) {
    const status = document.getElementById("hero-status");
    if (olympiads.length === 0) {
        status.textContent = "No olympiads yet";
        return;
    }

    // the newest olympiad (largest year)
    let latest = olympiads[0];
    for (const olympiad of olympiads) {
        if (olympiad.year > latest.year) {
            latest = olympiad;
        }
    }

    document.getElementById("hero-date").textContent = "Republic of Tajikistan, " + latest.year;
    document.getElementById("hero-title").textContent = "APEX OLYMPIAD " + latest.year;

    if (latest.status === "registration") {
        status.textContent = "● Registration is open";
    } else if (latest.status === "ongoing") {
        status.textContent = "● " + latest.current_round_name + " round in progress";
        // highlight the current round card
        const card = document.querySelector('.round-card[data-round="' + latest.current_round + '"]');
        if (card) {
            card.classList.add("active");
        }
    } else {
        status.textContent = "● Completed. See the winners below";
    }
}


// ---------- Subjects ----------

async function loadSubjects() {
    const list = document.getElementById("subjects-list");
    try {
        const subjects = await getJSON("/subjects");

        list.innerHTML = "";
        for (const subject of subjects) {
            const info = SUBJECT_INFO[subject.name] || { image: "img/subject.svg", text: "Olympiad subject." };

            const card = document.createElement("div");
            card.className = "category";
            card.innerHTML = `
                <div class="category-img">
                    <img src="${info.image}" alt="${subject.name}">
                    <h3>${subject.name}</h3>
                </div>
                <p class="category-info">${info.text}</p>
                <a href="#rules" class="learn-more">Learn more →</a>
            `;
            list.appendChild(card);
        }
    } catch (error) {
        list.innerHTML = "<p>Could not load subjects.</p>";
    }
}


// ---------- Dropdowns ----------

async function loadOlympiads() {
    const select = document.getElementById("olympiad-select");
    try {
        const olympiads = await getJSON("/olympiads");

        select.innerHTML = "";
        for (const olympiad of olympiads) {
            const option = document.createElement("option");
            option.value = olympiad.id;
            option.textContent = olympiad.year + " - " + olympiad.title + " (" + olympiad.status + ")";
            select.appendChild(option);
        }
    } catch (error) {
        select.innerHTML = "<option>Could not load olympiads</option>";
    }
}

async function loadStudents() {
    const select = document.getElementById("student-select");
    try {
        const students = await getJSON("/students");

        select.innerHTML = "";
        for (const student of students) {
            const option = document.createElement("option");
            option.value = student.id;
            option.textContent = student.first_name + " " + student.last_name + " (grade " + student.grade + ")";
            select.appendChild(option);
        }
    } catch (error) {
        select.innerHTML = "<option>Could not load students</option>";
    }
}

async function loadSchools() {
    const select = document.getElementById("school-select");
    try {
        const schools = await getJSON("/schools");

        select.innerHTML = "";
        for (const school of schools) {
            const option = document.createElement("option");
            option.value = school.id;
            option.textContent = school.name + " (" + school.region + ")";
            select.appendChild(option);
        }
    } catch (error) {
        select.innerHTML = "<option>Could not load schools</option>";
    }
}


// ---------- Winners (results) ----------

async function showResults() {
    const olympiadId = document.getElementById("olympiad-select").value;
    const list = document.getElementById("results-list");

    list.innerHTML = "";
    showStatus("results-status", "Loading...");

    try {
        const response = await fetch(API + "/olympiads/" + olympiadId + "/results");
        const data = await response.json();

        // Error from the API, for example 409 "olympiad is not completed"
        if (!response.ok) {
            showStatus("results-status", errorMessage(data), "error");
            return;
        }

        if (data.results.length === 0) {
            showStatus("results-status", "No results yet.");
            return;
        }

        showStatus("results-status", data.results.length + " finalists in " + data.year, "success");

        for (const result of data.results) {
            const place = result.place || "none";
            const medal = MEDALS[result.place] || "📜";
            const badgeText = result.place ? "PLACE " + result.place : "CERTIFICATE";

            const card = document.createElement("div");
            card.className = "card card-" + place;
            card.innerHTML = `
                <span class="badge place-${place}">${badgeText}</span>
                <div class="medal">${medal}</div>
                <h3>${result.student_name}</h3>
                <p>${result.school} · ${result.region}</p>
                <p class="score">${result.subject} · <b>${result.final_score}</b> / 100</p>
            `;
            list.appendChild(card);
        }
    } catch (error) {
        showStatus("results-status", "Server is not available. Is FastAPI running?", "error");
    }
}


// ---------- Student history ----------

async function showHistory() {
    const studentId = document.getElementById("student-select").value;
    const list = document.getElementById("history-list");

    list.innerHTML = "";
    showStatus("history-status", "Loading...");

    try {
        const response = await fetch(API + "/students/" + studentId + "/history");
        const data = await response.json();

        if (!response.ok) {
            showStatus("history-status", errorMessage(data), "error");
            return;
        }

        if (data.history.length === 0) {
            showStatus("history-status", data.student + " has not taken part in any olympiad yet.");
            return;
        }

        showStatus("history-status", data.student + " · " + data.school, "success");

        for (const item of data.history) {
            // scores look like {"1": {"total": 61}, "2": {...}}
            const chips = Object.entries(item.scores)
                .map(([round, score]) => `<span class="chip">Round ${round}: <b>${score.total}</b></span>`)
                .join("");

            const card = document.createElement("div");
            card.className = "card";
            card.innerHTML = `
                <h3>${item.year} · ${item.subject}</h3>
                <p>Reached: <b>${item.reached_round}</b> (${item.status})</p>
                <div class="round-chips">${chips || "<span class='chip'>No scores yet</span>"}</div>
                <p>${item.award ? (MEDALS[item.place] || "📜") + " " + item.award : ""}</p>
            `;
            list.appendChild(card);
        }
    } catch (error) {
        showStatus("history-status", "Server is not available. Is FastAPI running?", "error");
    }
}


// ---------- Add a student (POST) ----------

async function addStudent(event) {
    event.preventDefault(); // stop the page from reloading

    const newStudent = {
        first_name: document.getElementById("first-name").value,
        last_name: document.getElementById("last-name").value,
        grade: Number(document.getElementById("grade").value),
        school_id: Number(document.getElementById("school-select").value),
    };

    showStatus("form-status", "Saving...");

    try {
        const response = await fetch(API + "/students", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(newStudent),
        });
        const data = await response.json();

        if (!response.ok) {
            // 404, 409 or 422 from the API
            showStatus("form-status", "Error " + response.status + ": " + errorMessage(data), "error");
            return;
        }

        showStatus("form-status",
            "✅ Student added: " + data.first_name + " " + data.last_name + " (id " + data.id + ")", "success");
        document.getElementById("student-form").reset();
        loadStudents(); // refresh the student list
        loadStats();    // refresh the numbers at the top
    } catch (error) {
        showStatus("form-status", "Server is not available. Is FastAPI running?", "error");
    }
}


// ---------- Connect buttons and start ----------

document.getElementById("results-btn").addEventListener("click", showResults);
document.getElementById("history-btn").addEventListener("click", showHistory);
document.getElementById("student-form").addEventListener("submit", addStudent);

loadStats();
loadSubjects();
loadOlympiads();
loadStudents();
loadSchools();
