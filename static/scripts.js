document.addEventListener("DOMContentLoaded", function () {
    const choreList = document.getElementById("chore-list");
    const confettiDone = new Set();
    let currentFilter = "all";
    let dayView = "all";

    const DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"];
    function getTodayName() {
        return DAYS[(new Date().getDay() + 6) % 7];
    }

    // -------------------- Cheer sound guard --------------------
    window.allowCheer = false;
    const audio = document.getElementById('cheer-sound');
    window.cheerAudio = audio;

    // track when screen wakes
    let lastResume = 0;
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') lastResume = Date.now();
        if (document.visibilityState !== 'visible' && window.cheerAudio) {
            window.cheerAudio.pause();
            window.cheerAudio.currentTime = 0;
            window.cheerAudio.muted = true;
        }
    });

    if (audio) {
        audio.muted = true;
        audio.pause();
        audio.currentTime = 0;

        // block rogue plays on resume if not armed
        audio.addEventListener('play', () => {
            const justResumed = (Date.now() - lastResume) < 3000;
            if (!window.allowCheer && justResumed) {
                audio.pause();
                audio.currentTime = 0;
                audio.muted = true;
            }
        });
    }

    window.safePlayCheer = function () {
        if (document.visibilityState !== 'visible') return;
        if (!window.cheerAudio) return;

        window.cheerAudio.muted = false;
        window.cheerAudio.volume = 1;
        window.cheerAudio.currentTime = 0;

        window.cheerAudio.play()
            .then(() => { setTimeout(() => { window.allowCheer = false; }, 0); })
            .catch(()=>{});
    };
    // ------------------------------------------------------------

    function renderFilterBar(users) {
        let bar = document.getElementById("user-filter-bar");
        if (!bar) {
            bar = document.createElement("div");
            bar.id = "user-filter-bar";
            bar.className = "filter-bar";
            choreList.parentNode.insertBefore(bar, choreList);
        }
        bar.innerHTML = "";

        const userRow = document.createElement("div");
        userRow.className = "filter-row user-filter-row";
        const dayRow = document.createElement("div");
        dayRow.className = "filter-row day-filter-row";
        bar.append(userRow, dayRow);

        const addBtn = (label, value) => {
            const btn = document.createElement("button");
            btn.textContent = label;
            btn.className = "filter-btn" + (currentFilter === value ? " active" : "");
            btn.onclick = () => { currentFilter = value; loadChores(); };
            userRow.appendChild(btn);
        };

        addBtn("All", "all");
        users.forEach(u => addBtn(u.name, String(u.id)));

        const allDaysBtn = document.createElement("button");
        allDaysBtn.textContent = "All Days";
        allDaysBtn.className = "filter-btn" + (dayView === "all" ? " active" : "");
        allDaysBtn.onclick = () => { dayView = "all"; loadChores(); };
        dayRow.appendChild(allDaysBtn);

        const todayBtn = document.createElement("button");
        todayBtn.textContent = `Today (${getTodayName()})`;
        todayBtn.className = "filter-btn" + (dayView === "today" ? " active" : "");
        todayBtn.onclick = () => { dayView = "today"; loadChores(); };
        dayRow.appendChild(todayBtn);
    }

    // Populate the user dropdown
    fetch("/users")
    .then(res => res.json())
    .then(users => {
        const mainSel  = document.getElementById("user-select");
        const rotSel   = document.getElementById("rotation-user-select");

        users.forEach(u => {
            const opt1 = document.createElement("option");
            opt1.value = u.id;
            opt1.textContent = u.username;
            mainSel.appendChild(opt1);

            const opt2 = document.createElement("option");
            opt2.value = u.username;
            opt2.textContent = u.username;
            rotSel.appendChild(opt2);
        });
    });

    // Handle creating a new user
    document.getElementById('create-user-form').addEventListener('submit', function (e) {
        e.preventDefault();
        const username = document.getElementById('username-input').value;

        fetch("/users", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: username })
        })
        .then(res => res.json())
        .then(user => {
            const userSelect = document.getElementById('user-select');
            const option = document.createElement("option");
            option.value = user.id;
            option.textContent = user.username;
            userSelect.appendChild(option);
        });
    });

    // Handle adding a new chore
    document.getElementById('add-chore-form').addEventListener('submit', function (e) {
        e.preventDefault();

        const description = document.getElementById('chore-input').value;
        const userId = document.getElementById('user-select').value;
        const day = document.getElementById('day-select').value;
        const rotation = document.getElementById('rotation-select').value;

        let rotationOrder = [];
        if (rotation === "rotating") {
            const pinnedUser = document.getElementById("rotation-pinned-user")?.dataset.name;
            const extraUsers = [...document.querySelectorAll("#rotation-list .rotation-user")]
                .map(div => div.dataset.name);
        
            if (pinnedUser) {
                rotationOrder = [pinnedUser, ...extraUsers];
            }
        }
        fetch("/chores", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                description: description,
                user_id: userId,
                day: day,
                rotation_type: rotation,
                rotation_order: rotationOrder
            })
        }).then(() => loadChores());
    });

    // (rotation logic unchanged …)

    // Fetch all chores and render
    function loadChores() {
        fetch("/chores")
            .then(res => res.json())
            .then(chores => {
                const grouped = groupChoresByUser(chores);
                const usersWithChores = Object.entries(grouped).map(([userId, userChores]) => ({
                    id: userId,
                    name: userChores[0]?.username || "Unknown",
                    chores: userChores.map(chore => ({
                        id: chore.id,
                        description: chore.description,
                        day: chore.day,
                        status: chore.completed ? "Completed" : "Incomplete",
                        rotation: chore.rotation_type,
                        rotation_order: chore.rotation_order
                    }))
                }));
                renderUserChores(usersWithChores);
                renderFilterBar(usersWithChores);
            });
    }

    function groupChoresByUser(chores) {
        return chores.reduce((acc, chore) => {
            if (!acc[chore.user_id]) acc[chore.user_id] = [];
            acc[chore.user_id].push(chore);
            return acc;
        }, {});
    }

    function renderUserChores(users) {
        choreList.innerHTML = "";
        const days = (dayView === "today") ? [getTodayName()] : DAYS;
        document.body.classList.toggle("today-mode", dayView === "today");

        users.forEach(user => {
            if (currentFilter !== "all" && currentFilter !== String(user.id)) return;
            const section = document.createElement("div");
            section.className = "user-section";

            const header = document.createElement("div");
            header.className = "user-header";
            header.innerHTML = `
                <div class="user-name">${user.name}</div>
                <button class="delete-user" data-user-id="${user.id}">Delete User</button>
            `;

            const daysHeader = document.createElement("div");
            daysHeader.className = "days-header";
            days.forEach(day => {
                const dayDiv = document.createElement("div");
                dayDiv.textContent = day;
                daysHeader.appendChild(dayDiv);
            });

            const userRow = document.createElement("div");
            userRow.className = "user-row";
            days.forEach(day => {
                const col = document.createElement("div");
                col.className = "day-col";
                user.chores.filter(chore => chore.day === day).forEach(chore => {
                    const choreCard = document.createElement("div");
                    choreCard.className = "chore-item";
                    if (chore.status === "Completed") {
                        choreCard.classList.add("completed");
                    }
                    if (chore.rotation === "rotating") {
                        choreCard.classList.add("rotating");
                    }
                    choreCard.setAttribute("data-id", chore.id);
                    choreCard.innerHTML = `
                        <div class="chore-title">${chore.description}</div>
                        <div class="chore-status">Status: ${chore.status}</div>
                        <div class="chore-rotation">Rotation: ${chore.rotation}</div>
                        ${chore.rotation === "rotating" && chore.rotation_order?.length ? `
                            <div class="rotation-display">
                                Rotation Order:<br>
                                ${chore.rotation_order.map(name => `<div>${name}</div>`).join("")}
                            </div>` : ""
                        }
                        <div class="chore-buttons">
                            <div class="top-row">
                                <button class="delete-btn" onclick="deleteChore(${chore.id})">Delete</button>
                                <button class="edit-btn" onclick="editChore(${chore.id})">Edit</button>
                            </div>
                            <button class="primary-btn" onclick="toggleCompleted(${chore.id})">
                                ${chore.status === "Completed" ? "Undo" : "Done!"}
                            </button>
                        </div>
                    `;
                    col.appendChild(choreCard);
                });
                userRow.appendChild(col);
            });

            section.appendChild(header);
            section.appendChild(daysHeader);
            section.appendChild(userRow);
            choreList.appendChild(section);
        });
    }

    loadChores();
    document.getElementById('reset-week-btn').addEventListener('click', () => {
        fetch('/chores/reset', { method: 'POST' })
        .then(res => res.ok && loadChores());
    });
});

// ---- global helpers ----
function deleteChore(id) {
    fetch(`/chores/${id}`, { method: 'DELETE' })
        .then(() => document.querySelector(`[data-id='${id}']`)?.remove());
}

function editChore(id) {
    const newDesc = prompt("New description:");
    if (newDesc) {
        fetch(`/chores/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ description: newDesc })
        }).then(() => location.reload());
    }
}

function toggleCompleted(id) {
    fetch(`/chores/${id}`)
        .then(res => res.json())
        .then(chore => {
            fetch(`/chores/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ completed: !chore.completed })
            }).then(() => {
                const card = document.querySelector(`[data-id='${id}']`);
                if (card) {
                    const statusElement = card.querySelector(".chore-status");
                    const buttonElement = card.querySelector(".primary-btn, .undo-btn");

                    if (!chore.completed) {
                        card.classList.add("completed","pop-big");
                        statusElement.innerText = "Status: Completed";
                        if (buttonElement) {
                            buttonElement.innerText = "Undo";
                            buttonElement.classList.add("undo-btn");
                        }
                    } else {
                        card.classList.remove("completed");
                        card.classList.add("pop-small");
                        statusElement.innerText = "Status: Incomplete";
                        if (buttonElement) {
                            buttonElement.innerText = "Done!";
                            buttonElement.classList.remove("undo-btn");
                        }
                    }

                    setTimeout(() => {
                        card.classList.remove("pop-big","pop-small");
                    }, 200);

                    const userSection = card.closest(".user-section");
                    const stillIncomplete =
                        userSection.querySelectorAll(".chore-item:not(.completed)").length;

                    if (stillIncomplete === 0) {
                        confetti({ spread: 70, particleCount: 120, origin: { y: 0.3 } });
                        window.allowCheer = true;
                        window.safePlayCheer();
                    }
                }
                loadChores();
            });
        });
}
