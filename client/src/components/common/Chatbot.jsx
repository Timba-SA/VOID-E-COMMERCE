import React, { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { useTranslation } from 'react-i18next';
import { postQueryAPI, smartSearchAPI } from '../../api/chatbotApi';

const Chatbot = () => {
    const { t } = useTranslation();
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [sessionId, setSessionId] = useState('');
    const [showSuggestions, setShowSuggestions] = useState(false);
    const messagesEndRef = useRef(null);

    // Sugerencias rápidas dinámicas
    const quickSuggestions = [
        t('chatbot_suggestion_1'),
        t('chatbot_suggestion_2'),
        t('chatbot_suggestion_3'),
        t('chatbot_suggestion_4'),
        t('chatbot_suggestion_5')
    ];

    useEffect(() => {
        let currentSessionId = localStorage.getItem('chatSessionId');
        if (!currentSessionId) {
            currentSessionId = uuidv4();
            localStorage.setItem('chatSessionId', currentSessionId);
        }
        setSessionId(currentSessionId);
    }, []);
    
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const toggleChat = () => {
        if (!isOpen && messages.length === 0) {
            const welcomeMessage = t('chatbot_welcome');
            setMessages([{ sender: 'bot', text: welcomeMessage }]);
            setShowSuggestions(true);
        }
        setIsOpen(!isOpen);
    };

    const handleSuggestionClick = async (suggestion) => {
        setShowSuggestions(false);
        await sendMessage(suggestion);
    };

    const sendMessage = async (messageText) => {
        const userMessage = messageText.trim();
        if (!userMessage || isLoading) return;

        setMessages(prev => [...prev, { sender: 'user', text: userMessage }]);
        setInputValue('');
        setIsLoading(true);
        setShowSuggestions(false);

        try {
            // Intentar búsqueda inteligente primero para consultas de productos
            const productKeywords = ['busco', 'quiero', 'necesito', 'tenes', 'tienen', 'mostrame', 'ver', 'remera', 'campera', 'pantalon', 'buzo'];
            const isProductQuery = productKeywords.some(keyword => userMessage.toLowerCase().includes(keyword));
            
            let smartSearchResults = [];
            if (isProductQuery) {
                smartSearchResults = await smartSearchAPI(userMessage, 4);
            }

            // Obtener respuesta del chatbot
            const response = await postQueryAPI(userMessage, sessionId);
            let botMessage = response?.respuesta || "Disculpá, no estoy pudiendo procesar la respuesta.";

            // Si hay resultados de búsqueda inteligente, agregarlos
            if (smartSearchResults.length > 0) {
                botMessage += "\n\n🔍 Encontré estos productos que podrían interesarte:";
                smartSearchResults.forEach(product => {
                    botMessage += `\n• ${product.nombre} - $${product.precio}`;
                    if (product.categoria) {
                        botMessage += ` (${product.categoria.nombre})`;
                    }
                });
                botMessage += "\n\n¿Te gustaría ver alguno en detalle?";
            }

            setMessages(prev => [...prev, { sender: 'bot', text: botMessage }]);

        } catch (error) {
            console.error("Error en la llamada del chatbot:", error);
            setMessages(prev => [...prev, { 
                sender: 'bot', 
                text: 'Disculpá, estoy teniendo problemas para conectarme. ¿Podés intentar de nuevo en un momento?' 
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSendMessage = async (e) => {
        e.preventDefault();
        await sendMessage(inputValue);
    };

    const formatMessage = (text) => {
        // Formatear emojis y saltos de línea
        return text.split('\n').map((line, index) => (
            <span key={index}>
                {line}
                {index < text.split('\n').length - 1 && <br />}
            </span>
        ));
    };

    return (
        <div className="chatbot-container">
            <button 
                onClick={toggleChat} 
                className="chatbot-toggle-button" 
                style={{ opacity: isOpen ? 0 : 1, pointerEvents: isOpen ? 'none' : 'auto' }}
            >
                <img src="/CHATBOT.png" alt="Abrir Chat" className="chatbot-logo-img" />
            </button>

            <div className={`chatbot-window ${isOpen ? 'open' : ''}`}>
                <div className="chatbot-header">
                    <div className="header-content">
                        <h3>{t('chatbot_title')}</h3>
                        <span className="header-subtitle">{t('chatbot_subtitle')}</span>
                    </div>
                    <button onClick={toggleChat} className="chatbot-close-btn">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                    </button>
                </div>

                <div className="chatbot-messages">
                    {messages.map((msg, index) => (
                        <div key={index} className={`message-bubble ${msg.sender}`}>
                            {formatMessage(msg.text)}
                        </div>
                    ))}

                    {showSuggestions && (
                        <div className="suggestions-container">
                            <p className="suggestions-title">{t('chatbot_suggestions_title')}</p>
                            <div className="suggestions-grid">
                                {quickSuggestions.map((suggestion, index) => (
                                    <button
                                        key={index}
                                        className="suggestion-button"
                                        onClick={() => handleSuggestionClick(suggestion)}
                                        disabled={isLoading}
                                    >
                                        {suggestion}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {isLoading && (
                        <div className="message-bubble bot typing-indicator">
                            <span></span><span></span><span></span>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                <form onSubmit={handleSendMessage} className="chatbot-input-form">
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder={t('chatbot_placeholder')}
                        disabled={isLoading}
                        className="chatbot-input"
                    />
                    <button 
                        type="submit" 
                        disabled={isLoading || !inputValue.trim()} 
                        className="chatbot-send-btn"
                    >
                        {isLoading ? '...' : '▶'}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default Chatbot;