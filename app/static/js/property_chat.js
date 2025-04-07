document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chatMessages');
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.querySelector('.btn-send');
    const fileInput = document.getElementById('fileInput');
    const attachButton = document.getElementById('attachButton');
    const messageForm = document.getElementById('messageForm');

    // Load initial messages
    loadMessages();

    // Single event listener for form submission
    messageForm.addEventListener('submit', function(e) {
        e.preventDefault();
        sendMessage();
    });

    // File input listener
    fileInput.addEventListener('change', function(e) {
        const files = e.target.files;
        if (files.length > 0) {
            sendFiles(files);
        }
    });

    // Auto-scroll to bottom when new messages are added
    const observer = new MutationObserver(function(mutations) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });

    observer.observe(chatMessages, { childList: true });

    let lastMessageTimestamp = null;

    // Functions
    function loadMessages() {
        fetch(`/chat/messages/${chatId}`)
            .then(response => response.json())
            .then(data => {
                if (data.messages.length > 0) {
                    chatMessages.innerHTML = '';
                    data.messages.forEach(message => {
                        console.log('Message data:', message); // Debug log
                        appendMessage({
                            content: message.content,
                            is_sender: message.is_sender,
                            timestamp: message.timestamp,
                            file_url: message.file_url,
                            file_name: message.file_name,
                            file_type: message.file_type
                        });
                    });
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }
            })
            .catch(error => console.error('Error loading messages:', error));
    }

    function sendMessage() {
        const content = messageInput.value.trim();
        if (!content) return;

        messageInput.disabled = true;
        sendButton.disabled = true;

        fetch('/chat/send-message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                chat_id: chatId,
                content: content
            })
        })
        .then(response => response.json())
        .then(message => {
            appendMessage({
                content: message.content,
                is_sender: true,
                timestamp: message.created_at,
                file_url: message.file_url,
                file_name: message.file_name,
                file_type: message.file_type
            });
            messageInput.value = '';
            chatMessages.scrollTop = chatMessages.scrollHeight;
        })
        .catch(error => console.error('Error sending message:', error))
        .finally(() => {
            messageInput.disabled = false;
            sendButton.disabled = false;
            messageInput.focus();
        });
    }

    function appendMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${message.is_sender ? 'sender' : 'receiver'}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Don't set content if it's a file message
        if (!message.file_url) {
            contentDiv.textContent = message.content;
        }
        
        // Handle file attachments
        if (message.file_url) {
            console.log('File URL found:', message.file_url); // Debug log
            const attachmentDiv = document.createElement('div');
            attachmentDiv.className = 'file-attachment';
            
            const fileIcon = document.createElement('i');
            fileIcon.className = 'fas fa-file';
            
            const fileName = document.createElement('span');
            fileName.className = 'file-name';
            fileName.textContent = message.file_name || 'File';
            
            const downloadBtn = document.createElement('a');
            downloadBtn.href = message.file_url;
            downloadBtn.className = 'download-btn';
            downloadBtn.innerHTML = '<i class="fas fa-download"></i>';
            downloadBtn.setAttribute('download', '');
            
            attachmentDiv.appendChild(fileIcon);
            attachmentDiv.appendChild(fileName);
            attachmentDiv.appendChild(downloadBtn);
            contentDiv.appendChild(attachmentDiv);
        }
        
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        const messageDate = new Date(message.timestamp);
        timeDiv.textContent = messageDate.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(timeDiv);
        chatMessages.appendChild(messageDiv);
    }

    // Functions for sending files
    function sendFiles(files) {
        Array.from(files).forEach(file => {
            if (file.size > maxFileSize) {
                alert(`File ${file.name} is too large. Maximum size is 5MB.`);
                return;
            }

            const formData = new FormData();
            formData.append('file', file);
            formData.append('chat_id', chatId);

            fetch('/chat/send-file', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(message => {
                // Ensure file_url is absolute
                if (message.file_url && !message.file_url.startsWith('http')) {
                    message.file_url = window.location.origin + message.file_url;
                }
                appendMessage(message);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            })
            .catch(error => console.error('Error sending file:', error));
        });
        
        fileInput.value = '';
    }

    // Poll for new messages every 15 seconds instead of 5
    setInterval(loadMessages, 15000);
}); 