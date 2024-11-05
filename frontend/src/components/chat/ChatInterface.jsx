import React, { useState } from 'react';
import { Send } from 'lucide-react';
import { sendChatMessage } from '../../services/chatService';  // Add this import


const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    try {
      setIsLoading(true);
      // Add user message to chat
      const newUserMessage = {
        type: 'user',
        content: inputMessage
      };
      setMessages(prev => [...prev, newUserMessage]);

      // Call the chat service
      const aiResponse = await sendChatMessage(inputMessage);

      // Add AI response to chat
      const newAIMessage = {
        type: 'ai',
        content: aiResponse
      };
      setMessages(prev => [...prev, newAIMessage]);

      // Clear input
      setInputMessage('');
    } catch (error) {
      console.error('Error sending message:', error);
      // Add error message to chat
      const errorMessage = {
        type: 'error',
        content: 'Sorry, there was an error processing your request. Please try again.'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-4 bg-white rounded-lg shadow">
      <div className="mb-4">
        <h2 className="text-lg font-semibold mb-2">Data Analysis Chat</h2>
        
        {/* Messages Container */}
        <div className="h-96 overflow-y-auto border rounded-lg p-4 mb-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`mb-4 ${
                message.type === 'user' 
                  ? 'text-right' 
                  : 'text-left'
              }`}
            >
              <div
                className={`inline-block p-3 rounded-lg ${
                  message.type === 'user'
                    ? 'bg-blue-500 text-white'
                    : message.type === 'error'
                    ? 'bg-red-100 text-red-700'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                {message.content}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="text-center text-gray-500">
              Processing your request...
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="flex gap-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Ask about your lottery data..."
            className="flex-1 p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={isLoading}
            className="p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-300"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
