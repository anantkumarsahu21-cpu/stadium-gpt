// StadiumGPT - AI Assistant Script
document.addEventListener('DOMContentLoaded', () => {
    initAssistantInput();
    initSpeechRecognition();
});

// Send message triggers
function initAssistantInput() {
    const input = document.getElementById('chat-query-input');
    if (input) {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendAssistantMessage();
            }
        });
    }
}

function sendAssistantMessage() {
    const input = document.getElementById('chat-query-input');
    if (!input) return;
    
    const message = input.value.trim();
    if (!message) return;
    
    // Clear input
    input.value = '';
    
    // Render user message bubble
    appendChatBubble(message, 'user');
    
    // Call backend API
    fetch(window.API_ASSISTANT_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: message })
    })
    .then(response => {
        if (!response.ok) throw new Error("Assistant response failure");
        return response.json();
    })
    .then(data => {
        if (data.reply) {
            appendChatBubble(data.reply, 'bot');
            
            // Vocalize response if checked
            const voiceOutputChecked = document.getElementById('assistant-voice-output');
            if (voiceOutputChecked && voiceOutputChecked.checked) {
                vocalizeText(data.reply);
            }
        }
    })
    .catch(err => {
        console.error(err);
        appendChatBubble("I apologize, but I am having trouble connecting to my cognitive operations center. Please check your network and try again.", 'bot');
    });
}

// Preset Queries submitter
window.submitPresetQuery = function(text) {
    const input = document.getElementById('chat-query-input');
    if (input) {
        input.value = text;
        sendAssistantMessage();
    }
}

// Append Chat bubbles to console
function appendChatBubble(text, sender) {
    const chatBox = document.getElementById('chat-messages-box');
    if (!chatBox) return;
    
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${sender}`;
    bubble.innerText = text;
    
    chatBox.appendChild(bubble);
    
    // Scroll lock to bottom
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Speech Recognition module (Web Speech API)
function initSpeechRecognition() {
    const micBtn = document.getElementById('btn-voice-input');
    const input = document.getElementById('chat-query-input');
    
    if (!micBtn || !input) return;

    // Check compatibility
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        micBtn.title = "Voice Input Not Supported in Browser";
        micBtn.style.opacity = '0.4';
        micBtn.style.cursor = 'not-allowed';
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    micBtn.addEventListener('click', () => {
        // Toggle visual active state
        micBtn.classList.toggle('btn-primary');
        micBtn.classList.toggle('btn-outline-secondary');
        
        try {
            recognition.start();
            input.placeholder = "Listening...";
        } catch (e) {
            recognition.stop();
        }
    });

    recognition.onresult = (event) => {
        const resultText = event.results[0][0].transcript;
        input.value = resultText;
        input.placeholder = "Type your query...";
        sendAssistantMessage();
    };

    recognition.onspeechend = () => {
        recognition.stop();
        resetMicBtn(micBtn);
    };

    recognition.onerror = (event) => {
        console.error("Speech Recognition Error: ", event.error);
        input.placeholder = "Type your query...";
        resetMicBtn(micBtn);
    };
}

function resetMicBtn(btn) {
    btn.classList.remove('btn-primary');
    btn.classList.add('btn-outline-secondary');
}

// Speech Synthesis (Text-to-Speech vocalizer)
function vocalizeText(text) {
    if ('speechSynthesis' in window) {
        // Cancel active readings
        window.speechSynthesis.cancel();
        
        const cleanText = text.replace(/[^\w\s\d,.\-']/g, ''); // strip markdown formatting symbols
        
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        
        // Match language if possible (defaults to en-US)
        utterance.lang = 'en-US';
        
        window.speechSynthesis.speak(utterance);
    }
}
