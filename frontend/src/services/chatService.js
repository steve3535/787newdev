// src/services/chatService.js

const API_ENDPOINT = 'https://7t51dho1ba.execute-api.eu-central-1.amazonaws.com/DEV';

export const sendChatMessage = async (query) => {
    try {
        const response = await fetch(`${API_ENDPOINT}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query }),
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();
        return data.response;
    } catch (error) {
        console.error('Chat API Error:', error);
        throw error;
    }
};