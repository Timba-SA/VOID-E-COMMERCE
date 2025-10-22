import React, { useState, useEffect, useRef } from 'react';

/**
 * Componente de imagen con lazy loading optimizado
 * Carga la imagen solo cuando está cerca del viewport
 */
const LazyProductImage = ({ src, alt, className = '', threshold = 0.1 }) => {
    const [imageSrc, setImageSrc] = useState(null);
    const [imageRef, setImageRef] = useState();
    const imgRef = useRef();

    useEffect(() => {
        let observer;
        
        if (imgRef.current) {
            observer = new IntersectionObserver(
                (entries) => {
                    entries.forEach((entry) => {
                        if (entry.isIntersecting) {
                            // La imagen está en el viewport, cargarla
                            setImageSrc(src);
                            // Desconectar el observer ya que la imagen se cargó
                            observer.unobserve(imgRef.current);
                        }
                    });
                },
                {
                    threshold: threshold,
                    rootMargin: '50px', // Empezar a cargar 50px antes de entrar al viewport
                }
            );

            observer.observe(imgRef.current);
        }

        return () => {
            if (observer && imgRef.current) {
                observer.unobserve(imgRef.current);
            }
        };
    }, [src, threshold]);

    return (
        <div ref={imgRef} className={`relative ${className}`}>
            {!imageSrc ? (
                // Placeholder mientras carga
                <div className="w-full h-full bg-gray-200 animate-pulse flex items-center justify-center">
                    <svg 
                        className="w-12 h-12 text-gray-400" 
                        fill="none" 
                        stroke="currentColor" 
                        viewBox="0 0 24 24"
                    >
                        <path 
                            strokeLinecap="round" 
                            strokeLinejoin="round" 
                            strokeWidth={2} 
                            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" 
                        />
                    </svg>
                </div>
            ) : (
                <img
                    src={imageSrc}
                    alt={alt}
                    className={className}
                    loading="lazy"
                    onError={(e) => {
                        // Si falla la carga, mostrar imagen por defecto
                        e.target.src = 'https://via.placeholder.com/400x500?text=Sin+Imagen';
                    }}
                />
            )}
        </div>
    );
};

export default LazyProductImage;
