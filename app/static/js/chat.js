let currentPropertyContext = null;
const websiteInfo = {
    name: "RealEstimate",
    description: "RealEstimate is a comprehensive real estate platform that connects property buyers and sellers in India. The platform offers property listings, AI-powered assistance, and direct communication between buyers and sellers.",
    features: {
        buyers: [
            "Search and browse property listings",
            "AI-powered property recommendations",
            "Direct chat with property sellers",
            "Property value estimation",
            "Save favorite properties",
            "Set property preferences"
        ],
        sellers: [
            "List properties for sale",
            "Manage property listings",
            "Chat with interested buyers",
            "Track property inquiries",
            "Property analytics"
        ]
    },
    about: "RealEstimate helps streamline the property buying and selling process by providing modern tools and AI assistance to make informed real estate decisions."
};
let currentChatId = null;
let lastMessageTimestamp = null;
let chatPollingInterval = null;
let selectedFiles = [];

document.addEventListener('DOMContentLoaded', function() {
    const chatWidget = document.getElementById('chatWidget');
    const chatIcon = document.getElementById('chatIcon');
    if (chatWidget && chatIcon) {
        chatWidget.style.display = 'none';
        chatIcon.style.display = 'flex';
    }
    const messages = document.getElementById('chatMessages');
    if (messages) {
        messages.innerHTML = `
            <div class="chat-message bot-message">
                Hi! I'm RealEstimate's AI assistant.
                What can I help you with?
            </div>
        `;
    }
    const chatButton = document.getElementById('chatButton');
    if (chatButton) {  // Check if element exists before adding listener
        chatButton.addEventListener('click', function() {
            // your chat button logic
        });
    }
});

function toggleChat() {
    const chatWidget = document.getElementById('chatWidget');
    const chatIcon = document.getElementById('chatIcon');
    
    if (chatWidget.style.display === 'none') {
        chatWidget.style.display = 'flex';
        chatIcon.style.display = 'none';
    } else {
        chatWidget.style.display = 'none';
        chatIcon.style.display = 'flex';
    }
}

function startChat(sellerUsername, propertyId) {
    const chatWidget = document.getElementById('chatWidget');
    chatWidget.style.display = 'flex';
    
    fetch('/chat/start_seller_chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            seller_username: sellerUsername,
            property_id: propertyId 
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.context) {
            currentPropertyContext = data.context;
            const messages = document.getElementById('chatMessages');
            const botMessageDiv = document.createElement('div');
            botMessageDiv.className = 'chat-message bot-message';
            botMessageDiv.textContent = data.response;
            messages.appendChild(botMessageDiv);
            messages.scrollTop = messages.scrollHeight;
        }
    })
    .catch(error => console.error('Error:', error));
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    if (!message) return;
    
    input.value = '';
    
    const messages = document.getElementById('chatMessages');
    const userMessageDiv = document.createElement('div');
    userMessageDiv.className = 'chat-message user-message';
    userMessageDiv.textContent = message;
    messages.appendChild(userMessageDiv);
    messages.scrollTop = messages.scrollHeight;
    
    try {
        const response = await fetch('/chat/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: message,
                pageContent: currentPropertyContext,
                websiteInfo: websiteInfo
            })
        });
        
        const data = await response.json();
        if (data.response) {
            const botMessageDiv = document.createElement('div');
            botMessageDiv.className = 'chat-message bot-message';
            botMessageDiv.textContent = data.response;
            messages.appendChild(botMessageDiv);
            messages.scrollTop = messages.scrollHeight;
        }
    } catch (error) {
        console.error('Error:', error);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'chat-message bot-message';
        errorDiv.textContent = "I apologize, but I encountered an error. Please try asking your question again.";
        messages.appendChild(errorDiv);
        messages.scrollTop = messages.scrollHeight;
    }
}

// File upload handling
document.getElementById('fileInput').addEventListener('change', handleFileSelect);

function handleFileSelect(event) {
    const files = event.target.files;
    const previewDiv = document.getElementById('attachmentPreview');
    previewDiv.innerHTML = '';
    selectedFiles = [];

    for (let file of files) {
        if (file.size > 10 * 1024 * 1024) { // 10MB limit
            alert('File size cannot exceed 10MB');
            continue;
        }
        
        selectedFiles.push(file);
        const filePreview = document.createElement('div');
        filePreview.className = 'attachment-preview';
        filePreview.innerHTML = `
            <i class="fas fa-file"></i>
            <span>${file.name}</span>
            <button type="button" onclick="removeFile('${file.name}')">&times;</button>
        `;
        previewDiv.appendChild(filePreview);
    }
}

function removeFile(fileName) {
    selectedFiles = selectedFiles.filter(file => file.name !== fileName);
    updateAttachmentPreview();
}

function updateAttachmentPreview() {
    const previewDiv = document.getElementById('attachmentPreview');
    previewDiv.innerHTML = '';
    selectedFiles.forEach(file => {
        const filePreview = document.createElement('div');
        filePreview.className = 'attachment-preview';
        filePreview.innerHTML = `
            <i class="fas fa-file"></i>
            <span>${file.name}</span>
            <button type="button" onclick="removeFile('${file.name}')">&times;</button>
        `;
        previewDiv.appendChild(filePreview);
    });
}

// Real-time updates
function startRealtimeUpdates() {
    if (chatPollingInterval) {
        clearInterval(chatPollingInterval);
    }
    
    chatPollingInterval = setInterval(async () => {
        if (currentChatId) {
            const response = await fetch(`/chat/updates/${currentChatId}?last_timestamp=${lastMessageTimestamp}`);
            const data = await response.json();
            
            if (data.messages && data.messages.length > 0) {
                appendNewMessages(data.messages);
                lastMessageTimestamp = data.messages[data.messages.length - 1].timestamp;
            }
        }
    }, 3000);
}

function appendNewMessages(messages) {
    const messagesDiv = document.getElementById('chatMessages');
    messages.forEach(msg => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${msg.sender_id === currentUserId ? 'sent' : 'received'}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = msg.message;
        
        if (msg.attachments && msg.attachments.length > 0) {
            const attachmentsDiv = document.createElement('div');
            attachmentsDiv.className = 'attachments';
            msg.attachments.forEach(att => {
                const link = document.createElement('a');
                link.href = `/chat/download/${att.id}`;
                link.className = 'attachment-link';
                link.innerHTML = `<i class="fas fa-file"></i> ${att.filename}`;
                attachmentsDiv.appendChild(link);
            });
            contentDiv.appendChild(attachmentsDiv);
        }
        
        const timeSpan = document.createElement('small');
        timeSpan.className = 'message-time';
        timeSpan.textContent = new Date(msg.timestamp).toLocaleTimeString();
        
        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(timeSpan);
        messagesDiv.appendChild(messageDiv);
    });
    
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (chatPollingInterval) {
        clearInterval(chatPollingInterval);
    }
}); 