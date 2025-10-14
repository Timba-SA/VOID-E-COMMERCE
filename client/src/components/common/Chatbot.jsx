import React, { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { postQueryAPI, getRecommendationsAPI, smartSearchAPI } from '../../api/chatbotApi';

const Chatbot = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [sessionId, setSessionId] = useState('');
    const [recommendations, setRecommendations] = useState([]);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const messagesEndRef = useRef(null);

    // Sugerencias rápidas dinámicas
    const quickSuggestions = [
        "¿Qué remeras tienen?",
        "Camperas en stock",
        "Talles disponibles",
        "Productos en oferta",
        "Colores disponibles"
    ];

    useEffect(() => {
        let currentSessionId = localStorage.getItem('chatSessionId');
        if (!currentSessionId) {
            currentSessionId = uuidv4();
            localStorage.setItem('chatSessionId', currentSessionId);
        }
        setSessionId(currentSessionId);
        
        // Cargar recomendaciones cuando se inicializa
        if (currentSessionId) {
            loadRecommendations(currentSessionId);
        }
    }, []);
    
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const loadRecommendations = async (sessionId) => {
        try {
            const recs = await getRecommendationsAPI(sessionId, 3);
            setRecommendations(recs);
        } catch (error) {
            console.error('Error cargando recomendaciones:', error);
        }
    };

    const toggleChat = () => {
        if (!isOpen && messages.length === 0) {
            const welcomeMessage = '¡Hola! Soy Kara, tu asistente personal de VOID 👋\n\n¿Qué tipo de ropa estás buscando hoy?';
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

            // Recargar recomendaciones después de cada conversación
            loadRecommendations(sessionId);

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
                        <h3>KARA • VOID ASSISTANT</h3>
                        <span className="status-indicator">🟢 Online</span>
                    </div>
                    <button onClick={toggleChat} className="chatbot-close-btn">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
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
                            <p className="suggestions-title">Sugerencias rápidas:</p>
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

                    {recommendations.length > 0 && messages.length <= 1 && (
                        <div className="recommendations-container">
                            <p className="recommendations-title">💡 Productos recomendados para vos:</p>
                            <div className="recommendations-list">
                                {recommendations.slice(0, 3).map((product, index) => (
                                    <div key={index} className="recommendation-item">
                                        <span className="product-name">{product.nombre}</span>
                                        <span className="product-price">${product.precio}</span>
                                    </div>
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
                        placeholder="Escribí tu consulta..."
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