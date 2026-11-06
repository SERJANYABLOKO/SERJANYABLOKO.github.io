let user = JSON.parse(localStorage.getItem('fn_user')) || {
    username: 'Player_' + Math.floor(Math.random() * 1000),
    balance: 1000,
    inventory: []
};

const skinsDatabase = [
    { name: 'Аура', price: 150, img: 'https://fortnite-api.com/images/cosmetics/br/cid_436_athena_commune_f_aurora/icon.png' },
    { name: 'Супергерой', price: 400, img: 'https://fortnite-api.com/images/cosmetics/br/cid_703_athena_commune_m_superhero/icon.png' },
    { name: 'Редкость', price: 800, img: 'https://fortnite-api.com/images/cosmetics/br/cid_175_athena_commune_m_cyberpunk/icon.png' },
    { name: 'Дикий Налетчик', price: 1500, img: 'https://fortnite-api.com/images/cosmetics/br/cid_029_athena_commune_m_halloween/icon.png' },
    { name: 'Рыцарь Омега', price: 3000, img: 'https://fortnite-api.com/images/cosmetics/br/cid_138_athena_commune_m_carbide/icon.png' }
];

const targetUpgradeItem = { name: 'Элитный агент (Цель)', price: 2000, img: 'https://fortnite-api.com/images/cosmetics/br/cid_035_athena_commune_m_military/icon.png' };

function saveUser() {
    localStorage.setItem('fn_user', JSON.stringify(user));
    updateUI();
}

function updateUI() {
    document.getElementById('balance-display').innerText = user.balance;
    document.getElementById('username-display').innerText = user.username;
    document.getElementById('inv-count').innerText = user.inventory.length;
    
    const invGrid = document.getElementById('inventory-grid');
    invGrid.innerHTML = '';
    user.inventory.forEach((item, index) => {
        invGrid.innerHTML += `
            <div class="item-card">
                <img src="${item.img}" alt="${item.name}">
                <p>${item.name}</p>
                <p>${item.price} ₽</p>
                <button class="btn-primary" onclick="sellItem(${index})">Продать</button>
            </div>
        `;
    });

    updateUpgradeSelect();
}

function switchTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    
    document.getElementById('tab-' + tabName).classList.add('active');
    event.currentTarget.classList.add('active');
}

function openTopUpModal() { document.getElementById('topup-modal').style.display = 'flex'; }
function closeTopUpModal() { document.getElementById('topup-modal').style.display = 'none'; }
function simulateTopUp() {
    let amount = parseInt(document.getElementById('topup-amount').value) || 0;
    user.balance += amount;
    saveUser();
    closeTopUpModal();
    alert(`Баланс успешно пополнен на ${amount} ₽!`);
}

function openCase(price, type) {
    if (user.balance < price) {
        alert('Недостаточно средств!');
        return;
    }
    user.balance -= price;
    saveUser();

    const track = document.getElementById('roulette-track');
    track.innerHTML = '';
    document.getElementById('roulette-container').style.display = 'block';

    let itemsPool = [];
    for (let i = 0; i < 40; i++) {
        let randomSkin = skinsDatabase[Math.floor(Math.random() * skinsDatabase.length)];
        itemsPool.push(randomSkin);
    }
    
    let winningSkin = skinsDatabase[Math.floor(Math.random() * skinsDatabase.length)];
    itemsPool[30] = winningSkin;

    itemsPool.forEach(skin => {
        track.innerHTML += `
            <div class="roulette-item">
                <img src="${skin.img}" alt="${skin.name}">
                <span>${skin.price}₽</span>
            </div>
        `;
    });

    track.style.transition = 'none';
    track.style.left = '0px';

    setTimeout(() => {
        track.style.transition = 'left 4s cubic-bezier(0.1, 0.7, 0.1, 1)';
        let offset = -(30 * 120 - 380);
        track.style.left = offset + 'px';
    }, 50);

    setTimeout(() => {
        user.inventory.push(winningSkin);
        saveUser();
        document.getElementById('drop-result').innerHTML = `Вы выиграли: <b>${winningSkin.name}</b> (${winningSkin.price} ₽)!`;
    }, 4100);
}

function sellItem(index) {
    user.balance += user.inventory[index].price;
    user.inventory.splice(index, 1);
    saveUser();
}

function updateUpgradeSelect() {
    const select = document.getElementById('upgrade-item-select');
    select.innerHTML = '';
    user.inventory.forEach((item, index) => {
        select.innerHTML += `<option value="${index}">${item.name} (${item.price} ₽)</option>`;
    });
    
    document.getElementById('target-img').src = targetUpgradeItem.img;
    document.getElementById('target-name').innerText = targetUpgradeItem.name;
    document.getElementById('target-price').innerText = `Цена: ${targetUpgradeItem.price} ₽`;
    updateUpgradeChance();
}

function updateUpgradeChance() {
    const select = document.getElementById('upgrade-item-select');
    if (select.selectedIndex === -1) {
        document.getElementById('chance-display').innerText = 0;
        return;
    }
    let itemPrice = user.inventory[select.value].price;
    let chance = Math.min(Math.floor((itemPrice / targetUpgradeItem.price) * 100), 90);
    document.getElementById('chance-display').innerText = chance;
}

function runUpgrade() {
    const select = document.getElementById('upgrade-item-select');
    if (select.selectedIndex === -1) {
        alert('Выберите предмет для апгрейда!');
        return;
    }
    let itemIndex = select.value;
    let itemPrice = user.inventory[itemIndex].price;
    let chance = Math.min(Math.floor((itemPrice / targetUpgradeItem.price) * 100), 90);

    user.inventory.splice(itemIndex, 1);

    let roll = Math.random() * 100;
    if (roll <= chance) {
        user.inventory.push(targetUpgradeItem);
        alert('Успех! Апгрейд удался!');
    } else {
        alert('Неудача! Предмет сгорел.');
    }
    saveUser();
}

updateUI();
