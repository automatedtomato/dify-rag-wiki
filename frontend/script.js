// Get necessary DOM elements
const chatForm = document.getElementById('chat-form');
const messageInput = document.getElementById('message-input');
const chatWindow = document.getElementById('chat-window');

// API endpoint for our backend
const API_URL = 'http://localhost:8088/api/chat/';

// Generate a unique session ID for this chat session
const sessionId = `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;

// Listen for form submission
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault(); // Prevent default form submission behavior

    const userQuery = messageInput.value.trim();
    if (!userQuery) return; // Do nothing if input is empty

    // Display the user's message in the chat window
    appendMessage(userQuery, 'user-message');

    // Clear the input field
    messageInput.value = '';

    // Show a temporary loading message from the assistant
    const loadingMessageElement = appendMessage('', 'assistant-message loading');
    
    try {
        // Send the message to the backend API
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId,
                query: userQuery,
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        // Update the loading message with the actual response
        loadingMessageElement.textContent = data.content;
        loadingMessageElement.classList.remove('loading');

    } catch (error) {
        console.error('Error fetching chat response:', error);
        loadingMessageElement.textContent = 'Sorry, something went wrong. Please try again.';
        loadingMessageElement.classList.remove('loading');
    }
});

function appendMessage(text, className) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', className);
    messageElement.textContent = text;
    chatWindow.appendChild(messageElement);
    
    // Scroll to the bottom of the chat window
    chatWindow.scrollTop = chatWindow.scrollHeight;

    return messageElement;
}