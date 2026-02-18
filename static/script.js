document.addEventListener('DOMContentLoaded', () => {
    // Connect to current host
    const socket = io();

    // DOM Elements
    const chatContainer = document.querySelector('.chat-container');
    const chatHistory = document.getElementById('chat-history');
    const textInput = document.getElementById('user-input'); // Updated ID from HTML
    const sendBtn = document.getElementById('send-btn');
    const micBtn = document.getElementById('mic-btn');
    const attachBtn = document.getElementById('attach-btn');
    const imageInput = document.getElementById('image-input');
    const imagePreviewContainer = document.getElementById('image-preview-container');
    const imagePreview = document.getElementById('image-preview');
    const removeImageBtn = document.getElementById('remove-image');

    const voiceIndicator = document.getElementById('voice-indicator');
    const voiceStatus = document.getElementById('status-text'); // Restored status text
    const welcomeScreen = document.getElementById('welcome-screen');
    const menuBtn = document.getElementById('menu-btn');
    const sidebar = document.getElementById('sidebar');
    const speakerBtn = document.getElementById('speaker-btn');

    let currentImageBase64 = null;
    let recognition = null;
    let isTTSEnabled = false; // Default off

    // --- Web Speech API Setup ---
    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'hi-IN'; // Default to Hindi/India as per user preference

        recognition.onstart = function () {
            console.log('Voice recognition started');
            if (voiceIndicator) {
                voiceIndicator.classList.remove('hidden');
                if (voiceStatus) voiceStatus.innerText = "Listening...";
            }
        };

        recognition.onresult = function (event) {
            const transcript = event.results[0][0].transcript;
            console.log('Result:', transcript);
            textInput.value = transcript;
            sendMessage('voice');
        };

        recognition.onerror = function (event) {
            console.error('Speech recognition error', event.error);
            if (voiceIndicator) voiceIndicator.classList.add('hidden');
        };

        recognition.onend = function () {
            console.log('Voice recognition ended');
            // Don't auto-hide immediately, allow status update to handle it
        };
    } else {
        console.log("Web Speech API not supported");
    }

    // --- Sidebar Toggle ---
    if (menuBtn && sidebar) {
        menuBtn.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }

    // --- Speaker Toggle ---
    if (speakerBtn) {
        speakerBtn.addEventListener('click', () => {
            isTTSEnabled = !isTTSEnabled;
            const icon = speakerBtn.querySelector('span');
            if (isTTSEnabled) {
                icon.innerText = 'volume_up';
                speakerBtn.classList.add('active'); // Optional: Add active class for styling
            } else {
                icon.innerText = 'volume_off';
                speakerBtn.classList.remove('active');
            }
        });
    }

    // --- Suggestion Cards ---
    const suggestionCards = document.querySelectorAll('.suggestion-card');
    suggestionCards.forEach(card => {
        card.addEventListener('click', () => {
            const text = card.querySelector('p').innerText;
            textInput.value = text;
            sendMessage('text');
        });
    });

    // --- Socket Events ---
    socket.on('connect', () => {
        console.log("Connected to Assistant Server");
        loadHistory();
    });

    function loadHistory() {
        console.log("Loading history...");
        fetch('/api/history')
            .then(res => res.json())
            .then(data => {
                if (data.length > 0) {
                    // Clear previous
                    if (chatHistory) chatHistory.innerHTML = '';
                    // Determine user
                    const welcomeScreen = document.getElementById('welcome-screen');
                    if (welcomeScreen) welcomeScreen.style.display = 'none';

                    data.forEach(msg => {
                        appendMessage(msg.role === 'user' ? 'user' : 'bot', msg.text, msg.image);
                    });
                }
            })
            .catch(e => console.error("History load failed", e));
    }

    socket.on('status_update', (data) => {
        console.log("Status:", data);

        // Handle Voice Indicator
        if (voiceIndicator) {
            // Only show overlay for active listening/processing
            if (data.status === 'LISTENING' || data.status === 'PROCESSING') {
                voiceIndicator.classList.remove('hidden');
                if (voiceStatus) {
                    if (data.status === 'LISTENING') voiceStatus.innerText = "Listening...";
                    else if (data.status === 'PROCESSING') voiceStatus.innerText = "Thinking...";
                }
            } else {
                // Hide immediately for SPEAKING or IDLE
                voiceIndicator.classList.add('hidden');
            }
        }

        // Handle Text Output (Bot Answer)
        if (data.text) {
            // If status is SPEAKING, it means we have a final answer
            if (data.status === 'SPEAKING') {
                appendMessage('bot', data.text);
            }
        }
    });

    socket.on('user_speech', (data) => {
        if (data.text) {
            appendMessage('user', data.text);
        }
    });

    // --- Image Handling ---
    if (attachBtn && imageInput) {
        attachBtn.addEventListener('click', () => {
            imageInput.click();
        });

        imageInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    currentImageBase64 = e.target.result; // Data URL
                    imagePreview.src = currentImageBase64;
                    imagePreviewContainer.style.display = 'flex';
                };
                reader.readAsDataURL(file);
            }
        });
    }

    if (removeImageBtn) {
        removeImageBtn.addEventListener('click', () => {
            currentImageBase64 = null;
            imageInput.value = '';
            imagePreviewContainer.style.display = 'none';
        });
    }

    // --- Sending Messages ---
    function sendMessage(source = 'text') {
        if (!textInput) return;

        const text = textInput.value.trim();

        if (text === '' && !currentImageBase64) return;

        // Hide welcome screen
        if (welcomeScreen) welcomeScreen.style.display = 'none';

        // Add User Message to UI
        appendMessage('user', text, currentImageBase64);

        // Send to Backend
        socket.emit('text_input', {
            text: text,
            image: currentImageBase64,
            source: source, // 'text' or 'voice'
            tts_enabled: isTTSEnabled
        });

        // Clear Input
        textInput.value = '';
        currentImageBase64 = null;
        if (imageInput) imageInput.value = '';
        if (imagePreviewContainer) imagePreviewContainer.style.display = 'none';
    }

    if (sendBtn) {
        sendBtn.addEventListener('click', () => sendMessage('text'));
    }

    if (textInput) {
        textInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage('text');
            }
        });
    }



    // --- UI Helpers ---
    function appendMessage(sender, text, imageSrc = null) {
        // Double check welcome screen hiding
        if (welcomeScreen && welcomeScreen.style.display !== 'none') {
            welcomeScreen.style.display = 'none';
        }

        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;

        // Avatar setup
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        if (sender === 'bot') {
            // CSS handles bot image
        } else {
            avatarDiv.innerHTML = '<span class="material-icons-outlined">person</span>';
            avatarDiv.style.background = '#8E24AA';
            avatarDiv.style.color = '#fff';
            // avatarDiv.style.display = 'none'; // Keep hidden for user if desired
        }

        const contentDiv = document.createElement('div');
        contentDiv.className = 'content';

        // Image for User
        if (imageSrc) {
            const img = document.createElement('img');
            img.src = imageSrc;
            img.style.maxWidth = '200px';
            img.style.borderRadius = '8px';
            img.style.marginBottom = '8px';
            img.style.display = 'block';
            contentDiv.appendChild(img);
        }

        // Text Content
        if (sender === 'bot') {
            const textSpan = document.createElement('div');
            // Render Markdown
            textSpan.innerHTML = marked.parse(text);
            contentDiv.appendChild(textSpan);
        } else {
            const textSpan = document.createElement('div');
            textSpan.innerText = text;
            contentDiv.appendChild(textSpan);
        }

        if (sender === 'bot') {
            msgDiv.appendChild(avatarDiv);
            msgDiv.appendChild(contentDiv);
        } else {
            msgDiv.appendChild(contentDiv);
        }

        if (chatHistory) {
            chatHistory.appendChild(msgDiv);
            // Scroll container
            const container = document.querySelector('.chat-container');
            if (container) container.scrollTop = container.scrollHeight;
        }
    }
});