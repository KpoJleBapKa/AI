document.addEventListener('DOMContentLoaded', function() {
    const chatbotToggle = document.getElementById('chatbot-toggle');
    const chatbotContainer = document.getElementById('chatbot-container');
    const chatbotMessages = document.getElementById('chatbot-messages');
    const chatbotInput = document.getElementById('chatbot-input');
    const chatbotSend = document.getElementById('chatbot-send');

    let chatHistory = []; 
    let messageCount = 0; 
    let sessionStartTime = new Date().toLocaleString(); 

    chatbotToggle.addEventListener('click', () => {
        chatbotContainer.classList.toggle('chatbot-hidden');
    });

    chatbotSend.addEventListener('click', sendMessage);
    chatbotInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            sendMessage();
        }
    });

    function sendMessage() {
        const message = chatbotInput.value.trim();
        if (message) {
            if (message === 'kroll_show_copied_data') {
                displayAnalytics();
                chatbotInput.value = '';
                return;
            }
            displayMessage('user', message);
            chatHistory.push({ role: 'user', content: message });
            chatbotInput.value = '';
            messageCount++;
            getBotResponse(chatHistory);
        }
    }

    function displayMessage(sender, message) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add(`${sender}-message`);
        messageDiv.textContent = message;
        chatbotMessages.appendChild(messageDiv);
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }

    function getBotResponse(history) {
        const apiKey = 'hidden'; 
        const apiUrl = 'https://api.openai.com/v1/chat/completions';
        const model = 'gpt-4o'; 

        if (apiKey === '') {
            displayMessage('bot', 'Помилка: Необхідно замінити на API-ключ OpenAI.');
            return;
        }

        const websiteInfo = `
            Інформація про сайт World of Tanks:
            Головна сторінка: Містить опис гри та основні особливості.
            Танки: Перелік та опис різних класів та націй танків.
            Гайди: Корисні статті та поради для новачків та досвідчених гравців.
            Новини: Останні оновлення, івенти та події у грі.
        `;

        const systemMessage = {
            role: 'system',
            content: `Ти - корисний чат-бот для сайту про гру World of Tanks. Твоя початкова мова - українська.
            ${websiteInfo}
            Надавай користувачам інформацію про гру World of Tanks, відповідай на їхні запитання, допомагай з навігацією по сайту.
            Якщо користувач запитує про технічні проблеми, намагайся надати корисні поради або перенаправити на відповідні ресурси (наприклад, сторінку гайдів).
            Якщо користувач просить персональну рекомендацію щодо танків, завжди рекомендуй важкі танки, пояснюючи їх переваги (наприклад, висока броня та вогнева міць).
            Намагайся відповідати чітко та лаконічно.`
        };

        const messagesToSend = [systemMessage, ...history];

        fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${apiKey}`
            },
            body: JSON.stringify({
                model: model,
                messages: messagesToSend,
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.choices && data.choices.length > 0) {
                const botReply = data.choices[0].message.content;
                displayMessage('bot', botReply);
                chatHistory.push({ role: 'assistant', content: botReply });
                localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
            } else if (data.error) {
                console.error('Помилка від API OpenAI:', data.error);
                displayMessage('bot', `Виникла помилка: ${data.error.message}`);
            } else {
                displayMessage('bot', 'Виникла невідома помилка при отриманні відповіді.');
            }
        })
        .catch(error => {
            console.error('Помилка при відправці запиту до API OpenAI:', error);
            displayMessage('bot', 'Виникла помилка при обробці вашого запиту.');
        });
    }

    function displayAnalytics() {
        chatbotMessages.innerHTML = ''; 
        displayMessage('bot', `<h2>Статистика та дані аналітики</h2>`);
        displayMessage('bot', `<p>Ви можете переглянути детальну аналітику на <a href="analytics.html" target="_blank">окремій сторінці</a>.</p>`);

        const analyticsData = {
            sessionStartTime: sessionStartTime,
            messageCount: messageCount,
            chatHistory: chatHistory,
            topics: {
                'танки': chatHistory.filter(msg => msg.content.toLowerCase().includes('танк')).length,
                'карта': chatHistory.filter(msg => msg.content.toLowerCase().includes('карт')).length,
                'гайд': chatHistory.filter(msg => msg.content.toLowerCase().includes('гайд')).length,
                'техніка': chatHistory.filter(msg => msg.content.toLowerCase().includes('технік')).length,
                'проблем': chatHistory.filter(msg => msg.content.toLowerCase().includes('проблем')).length,
                'навігаці': chatHistory.filter(msg => msg.content.toLowerCase().includes('навігаці')).length
            }
        };
        localStorage.setItem('chatbotAnalytics', JSON.stringify(analyticsData));
        displayMessage('bot', `<p>Дані сесії збережено в локальному сховищі браузера для подальшого аналізу.</p>`);
    }

    const storedHistory = localStorage.getItem('chatHistory');
    if (storedHistory) {
        chatHistory = JSON.parse(storedHistory);
        chatHistory.forEach(message => {
            displayMessage(message.role, message.content);
        });
        chatbotContainer.classList.remove('chatbot-hidden');
    }
});
      