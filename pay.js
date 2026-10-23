// ПОПОЛНЕНИЕ БАЛАНСА ЧЕРЕЗ СБП И TELEGRAM
document.getElementById('topupBtn').addEventListener('click', async () => {
    const amount = parseInt(document.getElementById('topupAmountInput').value) || 0;
    if (amount <= 0) {
        showToast("Введите корректную сумму");
        return;
    }
    if (!currentUser || currentUser.username === "Гость") {
        showToast("Войдите в личный аккаунт для пополнения");
        return;
    }

    // Отправляем уведомление вам в Telegram о запросе на пополнение
    const message = `💳 <b>Запрос на пополнение баланса!</b>\n` +
                    `👤 Аккаунт: <code>${currentUser.username}</code>\n` +
                    `📞 Контакт: ${currentUser.contact || 'не указан'}\n` +
                    `💰 Сумма к зачислению: <b>${amount} ₽</b>\n\n` +
                    `<i>Проверьте поступление по СБП на номер +79161383846 и начислите баланс пользователю.</i>`;

    await sendToTelegram(message);

    showToast("✅ Запрос отправлен! Ожидайте зачисления после перевода по СБП.");
    
    // Закрываем модальное окно профиля
    const profileModal = document.getElementById('profileModal');
    if (profileModal) profileModal.classList.remove('show');
});
