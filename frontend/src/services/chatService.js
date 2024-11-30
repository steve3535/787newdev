// src/services/chatService.js

const OLLAMA_ENDPOINT = 'http://172.31.40.51:11434';

export const sendChatMessage = async (query) => {
    try {
        const response = await fetch(`${OLLAMA_ENDPOINT}/api/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                model: "llama3.1",
                prompt: query,
                stream: false,
                options: {
                    temperature: 0.7,
                    top_k: 40,
                    top_p: 0.9,
                }
            }),
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();
        return data.response;
    } catch (error) {
        console.error('Ollama API Error:', error);
        throw error;
    }
};

// Optional: Add a function to check model availability
export const checkModelAvailability = async () => {
    try {
        const response = await fetch(`${OLLAMA_ENDPOINT}/api/tags`);
        if (!response.ok) {
            throw new Error('Failed to fetch models');
        }
        return await response.json();
    } catch (error) {
        console.error('Error checking model availability:', error);
        throw error;
    }
};