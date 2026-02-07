document.addEventListener("DOMContentLoaded", function () {
    const choreList = document.getElementById("chore-list");
    const confettiDone = new Set();
    let currentFilter = "all";
    let dayView = "all";
    let allUsers = []; // cache for dropdowns

    const DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"];
    function getTodayName() {
        return DAYS[(new Date().getDay() + 6) % 7];
    }

    // ==================== Tab switching ====================
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
            btn.classList.add("active");
            document.getElementById("tab-" + btn.dataset.tab).classList.add("active");
            if (btn.dataset.tab === "grocery") loadGrocery();
        });
    });

    // ==================== Cheer sound guard ====================
    window.allowCheer = false;
    const audio = document.getElementById('cheer-sound');
    window.cheerAudio = audio;

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

    // ==================== Filter bar ====================
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

    // ==================== Populate dropdowns ====================
    function refreshUserDropdowns() {
        fetch("/users")
            .then(res => res.json())
            .then(users => {
                allUsers = users;
                const dropdowns = [
                    document.getElementById("user-select"),
                    document.getElementById("rotation-user-select"),
                    document.getElementById("grocery-user-select"),
                    document.getElementById("grocery-send-select")
                ];
                dropdowns.forEach(sel => {
                    if (!sel) return;
                    const val = sel.value;
                    // keep the first placeholder option
                    while (sel.options.length > 1) sel.remove(1);
                    users.forEach(u => {
                        const opt = document.createElement("option");
                        opt.value = (sel.id === "rotation-user-select" || sel.id === "grocery-send-select")
                            ? u.username : u.id;
                        opt.textContent = u.username;
                        sel.appendChild(opt);
                    });
                    // restore selection
                    if (val) sel.value = val;
                });
            });
    }
    refreshUserDropdowns();

    // ==================== Create user ====================
    document.getElementById('create-user-form').addEventListener('submit', function (e) {
        e.preventDefault();
        const username = document.getElementById('username-input').value.trim();
        if (!username) return;
        fetch("/users", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username })
        })
        .then(res => res.json())
        .then(() => {
            document.getElementById('username-input').value = '';
            refreshUserDropdowns();
            loadChores();
        });
    });

    // ==================== Add chore ====================
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
                description, user_id: userId, day,
                rotation_type: rotation, rotation_order: rotationOrder
            })
        }).then(() => loadChores());
    });

    // ==================== Load & render chores ====================
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

        let userIndex = 0;
        users.forEach(user => {
            if (currentFilter !== "all" && currentFilter !== String(user.id)) return;

            const section = document.createElement("div");
            section.className = "user-section";
            section.setAttribute("data-user-index", userIndex % 5);
            section.setAttribute("data-user-id", user.id);
            userIndex++;

            // header
            const header = document.createElement("div");
            header.className = "user-header";
            header.innerHTML = `
                <div class="user-name">${user.name}</div>
                <button class="delete-user" data-user-id="${user.id}">Delete User</button>
            `;

            // progress bar
            const totalChores = user.chores.length;
            const doneChores = user.chores.filter(c => c.status === "Completed").length;
            const pct = totalChores > 0 ? Math.round((doneChores / totalChores) * 100) : 0;

            const progressWrapper = document.createElement("div");
            progressWrapper.className = "progress-wrapper";
            progressWrapper.innerHTML = `
                <div class="progress-track">
                    <div class="progress-fill" style="width:${pct}%"></div>
                </div>
                <div class="progress-label">${doneChores}/${totalChores} done (${pct}%)</div>
            `;

            // days header
            const daysHeader = document.createElement("div");
            daysHeader.className = "days-header";
            days.forEach(day => {
                const dayDiv = document.createElement("div");
                dayDiv.textContent = day;
                daysHeader.appendChild(dayDiv);
            });

            // chore row
            const userRow = document.createElement("div");
            userRow.className = "user-row";
            days.forEach(day => {
                const col = document.createElement("div");
                col.className = "day-col";
                col.setAttribute("data-day", day);
                col.setAttribute("data-user-id", user.id);

                user.chores.filter(chore => chore.day === day).forEach(chore => {
                    const choreCard = document.createElement("div");
                    choreCard.className = "chore-item";
                    if (chore.status === "Completed") choreCard.classList.add("completed");
                    if (chore.rotation === "rotating") choreCard.classList.add("rotating");
                    choreCard.setAttribute("data-id", chore.id);

                    const checkClass = chore.status === "Completed" ? "done" : "pending";
                    const checkContent = chore.status === "Completed" ? "&#10003;" : "";

                    choreCard.innerHTML = `
                        <div class="chore-title">${chore.description}</div>
                        <div class="chore-status">
                            <span class="check-icon ${checkClass}">${checkContent}</span>
                            ${chore.status}
                        </div>
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
                            <button class="primary-btn${chore.status === 'Completed' ? ' undo-btn' : ''}" onclick="toggleCompleted(${chore.id})">
                                ${chore.status === "Completed" ? "Undo" : "Done!"}
                            </button>
                        </div>
                    `;
                    col.appendChild(choreCard);
                });
                userRow.appendChild(col);
            });

            section.appendChild(header);
            section.appendChild(progressWrapper);
            section.appendChild(daysHeader);
            section.appendChild(userRow);
            choreList.appendChild(section);
        });

        // Initialize drag-and-drop after rendering
        initDragAndDrop();
    }

    // ==================== Drag-and-Drop ====================
    function initDragAndDrop() {
        document.querySelectorAll(".day-col").forEach(col => {
            new Sortable(col, {
                group: "chores",        // shared group allows cross-column + cross-user dragging
                animation: 200,
                ghostClass: "sortable-ghost",
                chosenClass: "sortable-chosen",
                dragClass: "sortable-drag",
                handle: ".chore-item",
                draggable: ".chore-item",
                onEnd: function (evt) {
                    const choreId = evt.item.getAttribute("data-id");
                    const newDay = evt.to.getAttribute("data-day");
                    const newUserId = evt.to.getAttribute("data-user-id");

                    if (!choreId || !newDay || !newUserId) return;

                    fetch(`/chores/${choreId}/move`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ user_id: parseInt(newUserId), day: newDay })
                    })
                    .then(res => {
                        if (!res.ok) throw new Error("Move failed");
                        return res.json();
                    })
                    .then(() => {
                        // Reload to get fresh state (progress bars, etc.)
                        loadChores();
                    })
                    .catch(() => {
                        // Revert on failure
                        loadChores();
                    });
                }
            });
        });
    }

    // ==================== Grocery List ====================
    function loadGrocery() {
        fetch("/grocery")
            .then(res => res.json())
            .then(items => {
                const list = document.getElementById("grocery-list");
                list.innerHTML = "";
                if (items.length === 0) {
                    list.innerHTML = '<li class="grocery-empty">No items yet. Add something!</li>';
                    return;
                }
                items.forEach(item => {
                    const li = document.createElement("li");
                    li.className = "grocery-item";
                    li.innerHTML = `
                        <div>
                            <span class="grocery-item-name">${item.item_name}</span>
                            <span class="grocery-item-by">by ${item.added_by}</span>
                        </div>
                        <button class="grocery-item-delete" onclick="deleteGroceryItem(${item.id})">Remove</button>
                    `;
                    list.appendChild(li);
                });
            });
    }

    // Add grocery item
    document.getElementById("grocery-add-btn").addEventListener("click", () => {
        const input = document.getElementById("grocery-input");
        const userSel = document.getElementById("grocery-user-select");
        const itemName = input.value.trim();
        const addedBy = userSel.options[userSel.selectedIndex]?.text || "";

        if (!itemName || !userSel.value) return;

        fetch("/grocery", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ item_name: itemName, added_by: addedBy })
        }).then(res => {
            if (res.ok) {
                input.value = "";
                loadGrocery();
            }
        });
    });

    // Enter key for grocery input
    document.getElementById("grocery-input").addEventListener("keydown", e => {
        if (e.key === "Enter") {
            e.preventDefault();
            document.getElementById("grocery-add-btn").click();
        }
    });

    // Send grocery list
    document.getElementById("grocery-send-btn").addEventListener("click", () => {
        const sel = document.getElementById("grocery-send-select");
        const recipient = sel.value;
        if (!recipient) return;

        fetch("/grocery/send", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ recipient_username: recipient })
        })
        .then(res => res.json())
        .then(data => {
            alert(data.message || data.error);
            loadGrocery();
        });
    });

    // Clear grocery list
    document.getElementById("grocery-clear-btn").addEventListener("click", () => {
        if (!confirm("Clear the entire grocery list?")) return;
        fetch("/grocery/clear", { method: "DELETE" })
            .then(() => loadGrocery());
    });

    // ==================== Delete user handler (delegated) ====================
    document.addEventListener("click", (e) => {
        if (e.target.classList.contains("delete-user")) {
            const userId = e.target.getAttribute("data-user-id");
            if (!userId) return;
            if (!confirm("Delete this user and all their chores?")) return;
            fetch(`/users/${userId}`, { method: "DELETE" })
                .then(() => {
                    refreshUserDropdowns();
                    loadChores();
                });
        }
    });

    // ==================== Initial load ====================
    loadChores();

    document.getElementById('reset-week-btn').addEventListener('click', () => {
        if (!confirm("Archive this week and rotate chores?")) return;
        fetch('/chores/reset', { method: 'POST' })
            .then(res => res.ok && loadChores());
    });

    // Expose loadChores globally for toggleCompleted callback
    window.loadChores = loadChores;
});

// ==================== Global helpers ====================
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
        }).then(() => window.loadChores());
    }
}

function deleteGroceryItem(id) {
    fetch(`/grocery/${id}`, { method: 'DELETE' })
        .then(() => {
            // Reload grocery list
            const list = document.getElementById("grocery-list");
            fetch("/grocery").then(r => r.json()).then(items => {
                list.innerHTML = "";
                if (items.length === 0) {
                    list.innerHTML = '<li class="grocery-empty">No items yet. Add something!</li>';
                    return;
                }
                items.forEach(item => {
                    const li = document.createElement("li");
                    li.className = "grocery-item";
                    li.innerHTML = `
                        <div>
                            <span class="grocery-item-name">${item.item_name}</span>
                            <span class="grocery-item-by">by ${item.added_by}</span>
                        </div>
                        <button class="grocery-item-delete" onclick="deleteGroceryItem(${item.id})">Remove</button>
                    `;
                    list.appendChild(li);
                });
            });
        });
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
                    const buttonElement = card.querySelector(".primary-btn");
                    const checkIcon = card.querySelector(".check-icon");

                    if (!chore.completed) {
                        card.classList.add("completed","pop-big");
                        if (statusElement) statusElement.innerHTML = '<span class="check-icon done">&#10003;</span> Completed';
                        if (buttonElement) {
                            buttonElement.innerText = "Undo";
                            buttonElement.classList.add("undo-btn");
                        }
                    } else {
                        card.classList.remove("completed");
                        card.classList.add("pop-small");
                        if (statusElement) statusElement.innerHTML = '<span class="check-icon pending"></span> Incomplete';
                        if (buttonElement) {
                            buttonElement.innerText = "Done!";
                            buttonElement.classList.remove("undo-btn");
                        }
                    }

                    setTimeout(() => card.classList.remove("pop-big","pop-small"), 250);

                    const userSection = card.closest(".user-section");
                    const stillIncomplete = userSection.querySelectorAll(".chore-item:not(.completed)").length;

                    if (stillIncomplete === 0 && !chore.completed) {
                        confetti({ spread: 70, particleCount: 120, origin: { y: 0.3 } });
                        window.allowCheer = true;
                        window.safePlayCheer();
                    }
                }
                if (window.loadChores) window.loadChores();
            });
        });
}
