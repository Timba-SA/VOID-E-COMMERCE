// En FRONTEND/src/components/common/SearchModal.jsx
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { searchProducts } from '@/services/api'; // Crearemos esta función en el siguiente paso

const SearchModal = ({ isOpen, onClose }) => {
    const [query, setQuery] = useState('');
    const navigate = useNavigate();
    const inputRef = useRef(null);

    // Para que el input tenga el foco apenas se abre el modal
    useEffect(() => {
        if (isOpen) {
            setTimeout(() => inputRef.current?.focus(), 100);
        }
    }, [isOpen]);

    const handleSearch = (e) => {
        e.preventDefault();
        if (query.trim()) {
            navigate(`/search?q=${encodeURIComponent(query.trim())}`);
            onClose();
        }
    };

    return (
        <div className={`search-modal-overlay ${isOpen ? 'open' : ''}`} onClick={onClose}>
            <div className="search-modal-content" onClick={(e) => e.stopPropagation()}>
                <button onClick={onClose} className="search-modal-close-btn">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                </button>
                <form onSubmit={handleSearch} className="search-form">
                    <input
                        ref={inputRef}
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="TYPE HERE..."
                        className="search-input"
                    />
                </form>
            </div>
        </div>
    );
};

export default SearchModal;