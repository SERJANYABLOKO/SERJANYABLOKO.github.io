// --- СИСТЕМА АККАУНТОВ, АДМИНКИ И ВЫВОДА (f_accounts.js) ---

let allUsers = JSON.parse(localStorage.getItem('fn_all_users')) || {};
let adminRequests = JSON.parse(localStorage.getItem('fn_admin_requests')) || [];
let currentUser = localStorage.getItem('fn_current_user') || null;

// Установка пароля администратора по умолчанию, если он еще не задан
if (!localStorage.getItem('fn_admin_pass')) {
    localStorage.setItem('fn_admin_pass', '12345678');
}

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

// Строгая авторизация с проверкой логина и пароля
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
    if (login === 'serjant') {
        let correctAdminPass = localStorage.getItem('fn_admin_pass');
        if (pass !== correctAdminPass) {
            alert('❌ Неверный пароль администратора!');
            return; // Прерываем вход при неверном пароле
        }
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

// Запрос на пополнение счета
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
        type: 'topup',
        id: Date.now(),
        username: user.username,
        amount: amount,
        time: new Date().toLocaleTimeString()
    });
    
    localStorage.setItem('fn_admin_requests', JSON.stringify(adminRequests));
    closeTopUpModal();
    alert(`✅ Заявка на пополнение на ${amount} ₽ отправлена администратору (@serjantyabloko)! Ожидайте подтверждения.`);
}

// Запрос на вывод скина из инвентаря
function requestWithdrawal(itemIndex) {
    let user = getActiveUser();
    let item = user.inventory[itemIndex];
    if (!item) return;

    let targetTg = prompt(`Вывод скина: ${item.name} (${item.price} ₽)\nВведите ваш Telegram для выдачи:`, '@');
    if (!targetTg) return;

    // Списываем скин из инвентаря игрока
    user.inventory.splice(itemIndex, 1);
    saveActiveUser(user);

    // Добавляем заявку в панель админа
    adminRequests.push({
        type: 'withdraw',
        id: Date.now(),
        username: user.username,
        itemName: item.name,
        itemPrice: item.price,
        itemImg: item.img,
        targetTg: targetTg,
        time: new Date().toLocaleTimeString()
    });

    localStorage.setItem('fn_admin_requests', JSON.stringify(adminRequests));
    alert(`📤 Заявка на вывод скина "${item.name}" успешно создана! Администратор (@serjantyabloko) свяжется с вами.`);
}

// Управление панелью администратора
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
        container.innerHTML = '<p style="text-align: center; color: var(--text-muted); padding: 20px;">Нет новых заявок.</p>';
        return;
    }

    adminRequests.forEach((req, idx) => {
        if (req.type === 'topup') {
            container.innerHTML += `
                <div class="admin-notif-card">
                    <div>
                        <strong style="color: #00ff80;">[ПОПОЛНЕНИЕ]</strong><br>
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
        } else if (req.type === 'withdraw') {
            container.innerHTML += `
                <div class="admin-notif-card">
                    <div style="display:flex; align-items:center; gap:12px;">
                        <img src="${req.itemImg}" style="width:50px; height:50px; object-fit:contain;">
                        <div>
                            <strong style="color: #ff3366;">[ВЫВОД СКИНА]</strong><br>
                            <strong>Игрок:</strong> ${req.username} (ТГ: ${req.targetTg})<br>
                            <strong>Скин:</strong> ${req.itemName} (${req.itemPrice} ₽)<br>
                            <small style="color:var(--text-muted);">${req.time}</small>
                        </div>
                    </div>
                    <div>
                        <button class="btn-action" style="background: #27ae60; padding: 8px 12px;" onclick="resolveAdminRequest(${idx}, false)">Выдал (Закрыть)</button>
                    </div>
                </div>
            `;
        }
    });
}

function resolveAdminRequest(index, isApproved) {
    let req = adminRequests[index];
    if (req.type === 'topup' && isApproved) {
        if (allUsers[req.username]) {
            allUsers[req.username].balance += req.amount;
            localStorage.setItem('fn_all_users', JSON.stringify(allUsers));
            alert(`Заявка игрока ${req.username} на ${req.amount} ₽ одобрена! Баланс зачислен.`);
        }
    }
    adminRequests.splice(index, 1);
    localStorage.setItem('fn_admin_requests', JSON.stringify(adminRequests));
    renderAdminRequests();
    if (typeof updateUI === 'function') {
        updateUI();
    }
}

// Проверка сессии при загрузке
window.addEventListener('DOMContentLoaded', () => {
    if (!currentUser || !allUsers[currentUser]) {
        openAuthModal();
    }
});
