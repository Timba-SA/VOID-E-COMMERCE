// En FRONTEND/src/components/products/QuickViewModal.jsx

import React from 'react';
import QuickViewContent from './QuickViewContent.jsx';

const QuickViewModal = ({ product, onClose }) => {
    if (!product) return null;

    return (
        <div className="quick-view-overlay" onClick={onClose}>
            {/* El cambio está en este 'div' */}
            <div 
              className="quick-view-modal-content" 
              onClick={(e) => e.stopPropagation()} 
              style={{ maxWidth: '800px', width: '90%' }} // <-- ¡AQUÍ!
            >
                <button onClick={onClose} className="product-modal-close-btn">
                    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M1 1L17 17M17 1L1 17" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                    </svg>
                </button>
                <QuickViewContent product={product} onClose={onClose} />
            </div>
        </div>
    );
};

export default QuickViewModal;