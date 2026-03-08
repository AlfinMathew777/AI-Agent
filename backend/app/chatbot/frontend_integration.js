/**
 * Hotel Chatbot Frontend Integration
 * Provides easy integration with React/Vue/vanilla JS frontends
 */

class HotelChatbot {
    /**
     * Initialize chatbot client
     * @param {string} apiUrl - Base URL of chatbot API (default: http://localhost:8000)
     */
    constructor(apiUrl = 'http://localhost:8000') {
        this.apiUrl = apiUrl;
        this.sessionId = null;
        this.propertyId = null;
        this.isInitialized = false;
    }

    /**
     * Initialize chat session with property context
     * @param {string} propertyId - Property ID (e.g., 'hotel_tas_luxury')
     * @returns {Promise<string>} Welcome message
     */
    async initialize(propertyId) {
        this.propertyId = propertyId;

        try {
            const response = await fetch(`${this.apiUrl}/chat/init`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ property_id: propertyId })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Initialization failed');
            }

            const data = await response.json();
            this.sessionId = data.session_id || data.data?.session_id;
            this.isInitialized = true;

            return data.response;
        } catch (error) {
            console.error('[Chatbot] Initialization error:', error);
            throw error;
        }
    }

    /**
     * Send message to chatbot
     * @param {string} message - User message
     * @returns {Promise<Object>} Response object with {response, action, data}
     */
    async sendMessage(message) {
        if (!this.isInitialized || !this.sessionId) {
            throw new Error('Chat not initialized. Call initialize() first.');
        }

        try {
            const response = await fetch(`${this.apiUrl}/chat/message`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    message: message
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Message processing failed');
            }

            return await response.json();
        } catch (error) {
            console.error('[Chatbot] Send message error:', error);
            throw error;
        }
    }

    /**
     * Get session information
     * @returns {Promise<Object>} Session data with context and history
     */
    async getSessionInfo() {
        if (!this.sessionId) {
            throw new Error('No active session');
        }

        try {
            const response = await fetch(`${this.apiUrl}/chat/session/${this.sessionId}`);

            if (!response.ok) {
                throw new Error('Failed to fetch session info');
            }

            return await response.json();
        } catch (error) {
            console.error('[Chatbot] Get session error:', error);
            throw error;
        }
    }

    /**
     * Reset current session
     * @returns {Promise<void>}
     */
    async reset() {
        if (!this.sessionId) {
            return;
        }

        try {
            await fetch(`${this.apiUrl}/chat/reset?session_id=${this.sessionId}`, {
                method: 'POST'
            });

            this.sessionId = null;
            this.isInitialized = false;
        } catch (error) {
            console.error('[Chatbot] Reset error:', error);
        }
    }

    /**
     * Extract property ID from subdomain
     * Assumes format: propertyname.domain.com -> propertyname
     * @returns {string} Property subdomain
     */
    static getPropertyFromSubdomain() {
        const host = window.location.host;
        const parts = host.split('.');

        // e.g., grandtasman.achotels.com -> grandtasman
        // or localhost -> 'hotel_tas_luxury' (default for dev)
        if (parts.length >= 3) {
            return parts[0];
        }

        // Default for localhost development
        return 'hotel_tas_luxury';
    }

    /**
     * Map subdomain to property ID
     * Customize this for your property naming scheme
     * @param {string} subdomain - Subdomain extracted from URL
     * @returns {string} Full property ID
     */
    static mapSubdomainToPropertyId(subdomain) {
        const mapping = {
            'grandtasman': 'hotel_tas_luxury',
            'tasman-budget': 'hotel_tas_budget',
            'tasman-standard': 'hotel_tas_standard',
            // Add your property mappings here
        };

        return mapping[subdomain] || subdomain;
    }
}

// ============================================================================
// USAGE EXAMPLES
// ============================================================================

/**
 * Example 1: Vanilla JavaScript Integration
 */
async function vanillaJsExample() {
    // Auto-detect property from subdomain
    const subdomain = HotelChatbot.getPropertyFromSubdomain();
    const propertyId = HotelChatbot.mapSubdomainToPropertyId(subdomain);

    // Initialize chatbot
    const bot = new HotelChatbot('http://localhost:8000');
    const welcome = await bot.initialize(propertyId);

    console.log('Bot:', welcome);

    // Send message
    const reply = await bot.sendMessage('What time is check-in?');
    console.log('Bot:', reply.response);
    console.log('Action:', reply.action);

    // Book a room flow
    const avail = await bot.sendMessage('Do you have rooms available next weekend?');
    console.log('Bot:', avail.response);

    if (avail.action === 'show_availability') {
        const booking = await bot.sendMessage('Yes, book it');
        console.log('Bot:', booking.response);

        if (booking.action === 'booking_confirmed') {
            console.log('Confirmation:', booking.data.confirmation);
        }
    }
}

/**
 * Example 2: React Integration
 */
// In your React component:
/*
import React, { useState, useEffect } from 'react';

function ChatbotComponent() {
    const [bot, setBot] = useState(null);
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');

    useEffect(() => {
        async function init() {
            const propertyId = HotelChatbot.mapSubdomainToPropertyId(
                HotelChatbot.getPropertyFromSubdomain()
            );
            
            const chatbot = new HotelChatbot('http://localhost:8000');
            const welcome = await chatbot.initialize(propertyId);
            
            setBot(chatbot);
            setMessages([{role: 'assistant', text: welcome}]);
        }
        
        init();
    }, []);

    async function handleSend() {
        if (!bot || !input.trim()) return;
        
        // Add user message
        setMessages(prev => [...prev, {role: 'user', text: input}]);
        
        // Get response
        const reply = await bot.sendMessage(input);
        setMessages(prev => [...prev, {role: 'assistant', text: reply.response}]);
        
        setInput('');
    }

    return (
        <div className="chatbot">
            <div className="messages">
                {messages.map((msg, i) => (
                    <div key={i} className={`message ${msg.role}`}>
                        {msg.text}
                    </div>
                ))}
            </div>
            <input 
                value={input} 
                onChange={e => setInput(e.target.value)}
                onKeyPress={e => e.key === 'Enter' && handleSend()}
            />
            <button onClick={handleSend}>Send</button>
        </div>
    );
}
*/

/**
 * Example 3: Vue Integration
 */
/*
<template>
  <div class="chatbot">
    <div class="messages">
      <div v-for="(msg, i) in messages" :key="i" :class="`message ${msg.role}`">
        {{ msg.text }}
      </div>
    </div>
    <input v-model="input" @keyup.enter="sendMessage" />
    <button @click="sendMessage">Send</button>
  </div>
</template>

<script>
export default {
  data() {
    return {
      bot: null,
      messages: [],
      input: ''
    }
  },
  async mounted() {
    const propertyId = HotelChatbot.mapSubdomainToPropertyId(
      HotelChatbot.getPropertyFromSubdomain()
    );
    
    this.bot = new HotelChatbot('http://localhost:8000');
    const welcome = await this.bot.initialize(propertyId);
    
    this.messages.push({role: 'assistant', text: welcome});
  },
  methods: {
    async sendMessage() {
      if (!this.bot || !this.input.trim()) return;
      
      this.messages.push({role: 'user', text: this.input});
      
      const reply = await this.bot.sendMessage(this.input);
      this.messages.push({role: 'assistant', text: reply.response});
      
      this.input = '';
    }
  }
}
</script>
*/

/**
 * Example 4: Chatbot Widget (Drop-in)
 */
class ChatbotWidget {
    constructor(apiUrl, propertyId) {
        this.bot = new HotelChatbot(apiUrl);
        this.propertyId = propertyId;
        this.messages = [];
        this.isOpen = false;
    }

    async init() {
        const welcome = await this.bot.initialize(this.propertyId);
        this.messages.push({ role: 'assistant', text: welcome });
        this.render();
    }

    render() {
        // Create widget HTML
        const widget = document.createElement('div');
        widget.id = 'chatbot-widget';
        widget.className = this.isOpen ? 'open' : 'closed';

        widget.innerHTML = `
            <div class="chatbot-toggle" onclick="chatbotWidget.toggle()">
                💬 Chat with us
            </div>
            <div class="chatbot-window">
                <div class="chatbot-header">
                    <h3>Hotel Concierge</h3>
                    <button onclick="chatbotWidget.toggle()">✕</button>
                </div>
                <div class="chatbot-messages" id="chatbot-messages">
                    ${this.messages.map(msg => `
                        <div class="message ${msg.role}">
                            ${msg.text}
                        </div>
                    `).join('')}
                </div>
                <div class="chatbot-input">
                    <input 
                        id="chatbot-input-field" 
                        placeholder="Type a message..."
                        onkeypress="if(event.key==='Enter') chatbotWidget.send()"
                    />
                    <button onclick="chatbotWidget.send()">Send</button>
                </div>
            </div>
        `;

        // Remove old widget if exists
        const old = document.getElementById('chatbot-widget');
        if (old) old.remove();

        document.body.appendChild(widget);
    }

    toggle() {
        this.isOpen = !this.isOpen;
        this.render();
    }

    async send() {
        const input = document.getElementById('chatbot-input-field');
        const message = input.value.trim();

        if (!message) return;

        this.messages.push({ role: 'user', text: message });
        this.render();

        const reply = await this.bot.sendMessage(message);
        this.messages.push({ role: 'assistant', text: reply.response });
        this.render();

        input.value = '';

        // Scroll to bottom
        const messagesDiv = document.getElementById('chatbot-messages');
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
}

// Auto-initialize widget on page load
// window.addEventListener('load', async () => {
//     const propertyId = HotelChatbot.mapSubdomainToPropertyId(
//         HotelChatbot.getPropertyFromSubdomain()
//     );
//     
//     window.chatbotWidget = new ChatbotWidget('http://localhost:8000', propertyId);
//     await window.chatbotWidget.init();
// });

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { HotelChatbot, ChatbotWidget };
}
