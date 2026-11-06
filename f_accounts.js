// --- СИСТЕМА АККАУНТОВ И АДМИНКИ (f_accounts.js) ---

let allUsers = JSON.parse(localStorage.getItem('fn_all_users')) || {};
let adminRequests = JSON.parse(localStorage.getItem('fn_admin_requests')) || [];
let currentUser = localStorage.getItem('fn_current_user') || null;

function getActiveUser() {
    if (!currentUser || !allUsers[currentUser]) {
        return { username: 'Гость', balance: 0, inventory: [] };
    }
    return allUsers[currentUser];
}

function saveActiveUser(userObj) {
    if (!currentUser) return;
    allUsers[currentUser] = userObj;
    localStorage.setItem('fn_all_users', JSON.stringify(allUsers));
    if (typeof updateUI === 'function') {
        updateUI();
    }
}

// Авторизация / Вход (исправлено считывание полей)
function handleLogin() {
    let loginInput = document.getElementById('auth-login');
    let passInput = document.getElementById('auth-pass');
    
    if (!loginInput || !passInput) return;

    let login = loginInput.value.trim();
    let pass = passInput.value.trim();

    if (!login) {
        alert('Введите ник (логин)!');
        return;
    }

    // Проверка администратора
    if (login === 'serjant' && pass === '12345678') {
        currentUser = 'serjant';
    } else {
        currentUser = login;
    }

    if (!allUsers[currentUser]) {
        allUsers[currentUser] = {
            username: currentUser,
            balance: 0,
            inventory: []
        };
    }

    localStorage.setItem('fn_current_user', currentUser);
    localStorage.setItem('fn_all_users', JSON.stringify(allUsers));

    closeAuthModal();
    if (typeof updateUI === 'function') {
        updateUI();
    }
}

function openAuthModal() {
    let modal = document.getElementById('auth-modal');
    if (modal) modal.style.display = 'flex';
}

function closeAuthModal() {
    let modal = document.getElementById('auth-modal');
    if (modal) modal.style.display = 'none';
}

// Отправка заявки администратору (serjant)
function sendTopUpRequestToAdmin() {
    let amountInput = document.getElementById('topup-amount');
    if (!amountInput) return;

    let amount = parseInt(amountInput.value) || 0;
    if (amount <= 0) {
        alert('Введите корректную сумму!');
        return;
    }

    let user = getActiveUser();
    if (user.username === 'Гость') {
        alert('Сначала войдите в аккаунт!');
        openAuthModal();
        return;
    }

    adminRequests.push({
        id: Date.now(),
        username: user.username,
        amount: amount,
        time: new Date().toLocaleTimeString()
    });
    
    localStorage.setItem('fn_admin_requests', JSON.stringify(adminRequests));
    closeTopUpModal();
    alert(`✅ Заявка на пополнение на ${amount} ₽ отправлена администратору (@serjantyabloko)! Ожидайте подтверждения.`);
}

// Управление заявками в админке
function openAdminModal() {
    renderAdminRequests();
    let modal = document.getElementById('admin-modal');
    if (modal) modal.style.display = 'flex';
}

function closeAdminModal() {
    let modal = document.getElementById('admin-modal');
    if (modal) modal.style.display = 'none';
}

function renderAdminRequests() {
    let container = document.getElementById('admin-requests-list');
    if (!container) return;

    container.innerHTML = '';

    if (adminRequests.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: var(--text-muted); padding: 20px;">Нет новых заявок на пополнение.</p>';
        return;
    }

    adminRequests.forEach((req, idx) => {
        container.innerHTML += `
            <div class="admin-notif-card">
                <div>
                    <strong>Игрок:</strong> ${req.username}<br>
                    <strong>Сумма:</strong> <span style="color:var(--accent-color);">${req.amount} ₽</span><br>
                    <small style="color:var(--text-muted);">${req.time}</small>
                </div>
                <div style="display: flex; gap: 8px;">
                    <button class="btn-action" style="background: #27ae60; padding: 8px 12px;" onclick="resolveAdminRequest(${idx}, true)">Принять</button>
                    <button class="btn-action" style="background: #c0392b; padding: 8px 12px;" onclick="resolveAdminRequest(${idx}, false)">Удалить</button>
                </div>
            </div>
        `;
    });
}

function resolveAdminRequest(index, isApproved) {
    let req = adminRequests[index];
    if (isApproved) {
        if (allUsers[req.username]) {
            allUsers[req.username].balance += req.amount;
            localStorage.setItem('fn_all_users', JSON.stringify(allUsers));
            alert(`Заявка игрока ${req.username} на ${req.amount} ₽ одобрена! Баланс зачислен.`);
        } else {
            alert('Игрок не найден в базе данных!');
        }
    }
    adminRequests.splice(index, 1);
    localStorage.setItem('fn_admin_requests', JSON.stringify(adminRequests));
    renderAdminRequests();
    if (typeof updateUI === 'function') {
        updateUI();
    }
}

// Автопроверка при старте
window.addEventListener('DOMContentLoaded', () => {
    if (!currentUser || !allUsers[currentUser]) {
        openAuthModal();
    }
});
