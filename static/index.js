// ZCare AI Assistant - Frontend Interaction Logic

document.addEventListener("DOMContentLoaded", () => {
    // State Variables
    let chatHistory = [];
    
    // DOM Elements
    const chatViewport = document.getElementById("chat-viewport");
    const conversationFeed = document.getElementById("conversation-feed");
    const activeMessagesContainer = document.getElementById("active-messages");
    const chatForm = document.getElementById("chat-input-form");
    const messageInput = document.getElementById("chat-message-input");
    const sendBtn = document.getElementById("send-btn");
    const typingIndicator = document.getElementById("typing-indicator");
    
    const infoBanner = document.getElementById("info-banner");
    const closeBannerBtn = document.getElementById("close-banner-btn");
    
    const newChatTrigger = document.getElementById("new-conversation-trigger");
    const quickActionCards = document.querySelectorAll(".action-card");
    
    const btnHelpful = document.getElementById("btn-helpful");
    const btnNotHelpful = document.getElementById("btn-not-helpful");
    const infoTooltipTrigger = document.getElementById("info-tooltip-trigger");
    
    const btnFeedback = document.getElementById("btn-feedback");
    const btnEmail = document.getElementById("btn-email");
    
    // Feedback Modal Elements
    const feedbackModal = document.getElementById("feedback-modal");
    const modalCloseBtn = document.getElementById("modal-close-btn");
    const modalCancelBtn = document.getElementById("modal-cancel-btn");
    const feedbackForm = document.getElementById("feedback-form");
    const feedbackText = document.getElementById("feedback-text");

    // Initialize welcome message timestamp
    const welcomeTimestamp = document.getElementById("welcome-timestamp");
    if (welcomeTimestamp) {
        welcomeTimestamp.textContent = getFormattedTime();
    }

    // --- Helper Functions ---
    
    // Get time in format HH:MM AM/PM
    function getFormattedTime() {
        const now = new Date();
        let hours = now.getHours();
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const ampm = hours >= 12 ? 'PM' : 'AM';
        hours = hours % 12;
        hours = hours ? hours : 12; // the hour '0' should be '12'
        const hoursStr = String(hours).padStart(2, '0');
        return `${hoursStr}:${minutes} ${ampm}`;
    }

    // Scroll to bottom of chat
    function scrollToBottom() {
        if (chatViewport) {
            setTimeout(() => {
                chatViewport.scrollTo({
                    top: chatViewport.scrollHeight,
                    behavior: 'smooth'
                });
            }, 50);
        }
    }

    // Parse lightweight markdown to beautiful HTML (with support for lists, paragraphs, bold, inline code)
    function parseMarkdown(text) {
        if (!text) return "";
        // Sanitize raw HTML tags to prevent XSS while allowing styling
        let html = text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");

        // Convert bold (**text**)
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Convert inline code or highlighted terms (`term`)
        html = html.replace(/`(.*?)`/g, '<code class="inline-code">$1</code>');

        // Split into lines to parse lists and paragraphs
        const lines = html.split('\n');
        let inUnorderedList = false;
        let inOrderedList = false;
        let parsedLines = [];

        for (let line of lines) {
            let trimmed = line.trim();
            
            // Unordered Lists
            if (trimmed.startsWith('* ') || trimmed.startsWith('- ') || trimmed.startsWith('• ')) {
                if (inOrderedList) {
                    parsedLines.push('</ol>');
                    inOrderedList = false;
                }
                if (!inUnorderedList) {
                    parsedLines.push('<ul>');
                    inUnorderedList = true;
                }
                const content = trimmed.replace(/^(\*\s*|-\s*|•\s*)/, '');
                parsedLines.push(`<li>${content}</li>`);
            } 
            // Ordered Lists (e.g. 1., 2.)
            else if (/^\d+\.\s+/.test(trimmed)) {
                if (inUnorderedList) {
                    parsedLines.push('</ul>');
                    inUnorderedList = false;
                }
                if (!inOrderedList) {
                    parsedLines.push('<ol>');
                    inOrderedList = true;
                }
                const content = trimmed.replace(/^\d+\.\s+/, '');
                parsedLines.push(`<li>${content}</li>`);
            } 
            // Plain text or empty lines
            else {
                if (inUnorderedList) {
                    parsedLines.push('</ul>');
                    inUnorderedList = false;
                }
                if (inOrderedList) {
                    parsedLines.push('</ol>');
                    inOrderedList = false;
                }
                if (trimmed !== '') {
                    parsedLines.push(`<p>${trimmed}</p>`);
                }
            }
        }

        if (inUnorderedList) {
            parsedLines.push('</ul>');
        }
        if (inOrderedList) {
            parsedLines.push('</ol>');
        }

        return parsedLines.join('');
    }

    // --- Message Appending ---

    function appendUserMessage(text) {
        if (!activeMessagesContainer) return;
        const time = getFormattedTime();
        const userHtml = `
            <div class="message-wrapper user-message-wrapper">
                <div class="avatar-container">
                    <div class="user-avatar">U</div>
                </div>
                <div class="message-content-container">
                    <div class="message-meta">
                        <span class="message-time">${time}</span>
                    </div>
                    <div class="message-bubble user-bubble">
                        <p>${parseMarkdown(text)}</p>
                    </div>
                </div>
            </div>
        `;
        activeMessagesContainer.insertAdjacentHTML('beforeend', userHtml);
        scrollToBottom();
    }

    function appendBotMessage(text) {
        if (!activeMessagesContainer) return;
        const time = getFormattedTime();
        const parsedHtml = parseMarkdown(text);
        const botHtml = `
            <div class="message-wrapper bot-message-wrapper">
                <div class="avatar-container">
                    <img src="/static/icon/assistant.png" alt="ZCare Bot" class="bot-avatar">
                </div>
                <div class="message-content-container">
                    <div class="message-meta">
                        <span class="bot-name">ZCare Assistant</span>
                        <span class="message-time">${time}</span>
                    </div>
                    <div class="message-bubble bot-bubble">
                        ${parsedHtml}
                    </div>
                </div>
            </div>
        `;
        activeMessagesContainer.insertAdjacentHTML('beforeend', botHtml);
        scrollToBottom();
    }

    // --- Backend API Interaction ---

    async function sendQueryToBackend(messageText) {
        // Show Typing Indicator
        if (typingIndicator) {
            typingIndicator.style.display = "flex";
        }
        scrollToBottom();

        // Disable input during request
        if (messageInput) messageInput.disabled = true;
        if (sendBtn) sendBtn.disabled = true;

        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    question: messageText,
                    chat_history: chatHistory
                })
            });

            if (!response.ok) {
                let errorMessage = `Server returned code ${response.status}`;
                try {
                    const errorData = await response.json();
                    if (errorData && errorData.detail) {
                        errorMessage = errorData.detail;
                    }
                } catch (e) {
                    // Response not JSON
                }
                throw new Error(errorMessage);
            }

            const data = await response.json();
            
            // Hide typing indicator
            if (typingIndicator) {
                typingIndicator.style.display = "none";
            }
            
            // Append bot response
            appendBotMessage(data.answer);
            
            // Update local chat history state
            chatHistory = data.chat_history;

        } catch (error) {
            console.error("Error calling chat API:", error);
            if (typingIndicator) {
                typingIndicator.style.display = "none";
            }
            appendBotMessage(`I'm sorry, I encountered an error: **${error.message}**. Please verify your network connection and server state.`);
        } finally {
            // Re-enable inputs
            if (messageInput) {
                messageInput.disabled = false;
                messageInput.focus();
            }
            if (sendBtn) {
                sendBtn.disabled = false;
            }
        }
    }

    // --- Event Handlers ---

    // Chat Submission Form
    if (chatForm && messageInput) {
        chatForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const messageText = messageInput.value.trim();
            if (!messageText) return;

            // Clear input field
            messageInput.value = "";

            // Append user bubble
            appendUserMessage(messageText);

            // Fetch reply from backend
            sendQueryToBackend(messageText);
        });
    }

    // Quick Actions Click Handler
    if (quickActionCards) {
        quickActionCards.forEach(card => {
            card.addEventListener("click", () => {
                const query = card.getAttribute("data-query");
                if (!query) return;
                
                const cardTitleElem = card.querySelector(".card-title");
                const titleText = cardTitleElem ? cardTitleElem.textContent : "Query";
                
                // Append user bubble and fetch answer
                appendUserMessage(titleText);
                sendQueryToBackend(query);
            });
        });
    }

    // Dismiss info agreement banner
    if (closeBannerBtn && infoBanner) {
        closeBannerBtn.addEventListener("click", () => {
            infoBanner.style.opacity = "0";
            infoBanner.style.transform = "translateY(-10px)";
            setTimeout(() => {
                infoBanner.style.display = "none";
            }, 300);
        });
    }

    // Clear and start new conversation
    if (newChatTrigger) {
        newChatTrigger.addEventListener("click", (e) => {
            e.preventDefault();
            
            // Reset state
            chatHistory = [];
            
            // Add absolute visual reset
            if (activeMessagesContainer) {
                activeMessagesContainer.innerHTML = "";
            }
            
            // Notify user elegantly in chat
            appendBotMessage("Conversation reset successfully. Let's start fresh! What hospital information can I assist you with today?");
            
            // Reset feedback thumbs
            if (btnHelpful) btnHelpful.classList.remove("active");
            if (btnNotHelpful) btnNotHelpful.classList.remove("active");
        });
    }

    // Thumbs Feedback buttons
    if (btnHelpful && feedbackModal && feedbackText) {
        btnHelpful.addEventListener("click", () => {
            btnHelpful.classList.add("active");
            if (btnNotHelpful) btnNotHelpful.classList.remove("active");
            showToast("Thank you! Opening feedback panel...");
            setTimeout(() => {
                feedbackModal.style.display = "flex";
                feedbackText.focus();
            }, 800);
        });
    }

    if (btnNotHelpful && feedbackModal && feedbackText) {
        btnNotHelpful.addEventListener("click", () => {
            btnNotHelpful.classList.add("active");
            if (btnHelpful) btnHelpful.classList.remove("active");
            showToast("Thank you! Opening feedback panel...");
            setTimeout(() => {
                feedbackModal.style.display = "flex";
                feedbackText.focus();
            }, 800);
        });
    }

    // Footer Info Tooltip Click
    if (infoTooltipTrigger) {
        infoTooltipTrigger.addEventListener("click", () => {
            showToast("ZCare AI Assistant v1.0 | Support: +91 8589088985");
        });
    }

    // Secondary action triggers
    if (btnFeedback && feedbackModal && feedbackText) {
        btnFeedback.addEventListener("click", () => {
            feedbackModal.style.display = "flex";
            feedbackText.focus();
        });
    }

    if (btnEmail) {
        btnEmail.addEventListener("click", () => {
            showToast("Opening email client... Contacting support@zautomate.in");
            window.location.href = "mailto:support@zautomate.in?subject=ZCare AI Assistant Inquiry";
        });
    }

    // Feedback Modal Event Handlers
    if (modalCloseBtn && feedbackModal && feedbackText) {
        modalCloseBtn.addEventListener("click", () => {
            feedbackModal.style.display = "none";
            feedbackText.value = "";
        });
    }

    if (modalCancelBtn && feedbackModal && feedbackText) {
        modalCancelBtn.addEventListener("click", () => {
            feedbackModal.style.display = "none";
            feedbackText.value = "";
        });
    }

    // Close modal by clicking outside the card
    if (feedbackModal && feedbackText) {
        feedbackModal.addEventListener("click", (e) => {
            if (e.target === feedbackModal) {
                feedbackModal.style.display = "none";
                feedbackText.value = "";
            }
        });
    }

    // Handle Feedback Form Submission
    if (feedbackForm && feedbackText && feedbackModal) {
        feedbackForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const feedbackValue = feedbackText.value.trim();
            if (!feedbackValue) return;

            // Reset and Close
            feedbackText.value = "";
            feedbackModal.style.display = "none";

            // Show elegant thank you toast
            showToast("Thank you! Your feedback has been submitted successfully.");
        });
    }

    // --- Elegant Toast Notification Helper ---
    function showToast(message) {
        // Remove existing toast if present
        const oldToast = document.querySelector(".custom-toast");
        if (oldToast) oldToast.remove();

        const toast = document.createElement("div");
        toast.className = "custom-toast";
        toast.textContent = message;
        
        // Add styling directly or via style.css additions
        Object.assign(toast.style, {
            position: "absolute",
            bottom: "20px",
            left: "50%",
            transform: "translateX(-50%) translateY(20px)",
            backgroundColor: "#0F172A",
            color: "#FFFFFF",
            padding: "8px 16px",
            borderRadius: "30px",
            fontSize: "12.5px",
            fontWeight: "500",
            boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.3)",
            opacity: "0",
            transition: "all 0.3s ease",
            zIndex: "9999",
            textAlign: "center",
            pointerEvents: "none"
        });

        const container = document.querySelector(".app-container") || document.body;
        container.appendChild(toast);
        
        // Trigger transition
        setTimeout(() => {
            toast.style.opacity = "0.95";
            toast.style.transform = "translateX(-50%) translateY(0)";
        }, 50);

        // Fade out and remove
        setTimeout(() => {
            toast.style.opacity = "0";
            toast.style.transform = "translateX(-50%) translateY(-10px)";
            setTimeout(() => toast.remove(), 300);
        }, 2800);
    }
});
