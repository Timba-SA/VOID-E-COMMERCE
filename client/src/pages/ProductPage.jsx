// client/src/pages/ProductPage.jsx

import React, { useState, useEffect, useContext, useMemo, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { CartContext } from '../context/CartContext';
import { NotificationContext } from '../context/NotificationContext';
import { getProductById } from '../api/productsApi';
import Spinner from '../components/common/Spinner';

import { useAuthStore } from '../stores/useAuthStore';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getWishlistAPI, addToWishlistAPI, removeFromWishlistAPI } from '../api/wishListApi';
import { Heart } from 'lucide-react';

// ¡Importamos GSAP y ScrollTrigger!
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

// ¡Registramos el plugin!
gsap.registerPlugin(ScrollTrigger);

const transformCloudinaryUrl = (url, width) => {
  if (!url || !url.includes('cloudinary')) return url;
  const parts = url.split('/upload/');
  return `${parts[0]}/upload/f_auto,q_auto:best,w_${width}/${parts[1]}`;
};

const getSafeImageUrls = (urls) => {
    if (Array.isArray(urls) && urls.length > 0) {
        return urls;
    }
    return ['/img/placeholder.jpg'];
};


const ProductPage = ({ onOpenCartModal, onSetAddedItem }) => {
    const { t } = useTranslation();
    const { productId } = useParams();
    const { addItemToCart } = useContext(CartContext);
    const { notify } = useContext(NotificationContext);
    const { isAuthenticated } = useAuthStore();
    const queryClient = useQueryClient();

    const [product, setProduct] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    
    const [selectedColor, setSelectedColor] = useState(null);
    const [selectedSize, setSelectedSize] = useState(null);
    
    // ¡NUEVO! Creamos una referencia al contenedor de las imágenes
    const imageContainerRef = useRef(null);
    
    const { data: wishlist } = useQuery({
      queryKey: ['wishlist'],
      queryFn: getWishlistAPI,
      enabled: isAuthenticated,
    });

    const isWishlisted = useMemo(() => 
      wishlist?.some(item => item.id === parseInt(productId)),
      [wishlist, productId]
    );

    const addToWishlistMutation = useMutation({
      mutationFn: addToWishlistAPI,
      onSuccess: () => queryClient.invalidateQueries({ queryKey: ['wishlist'] }),
    });

    const removeFromWishlistMutation = useMutation({
      mutationFn: removeFromWishlistAPI,
      onSuccess: () => queryClient.invalidateQueries({ queryKey: ['wishlist'] }),
    });

    const handleWishlistToggle = () => {
      if (!isAuthenticated) return;
      const id = parseInt(productId);
      isWishlisted ? removeFromWishlistMutation.mutate(id) : addToWishlistMutation.mutate(id);
    };

    useEffect(() => {
        const fetchProductData = async () => {
            setLoading(true);
            setError(null);
            try {
                const data = await getProductById(productId);
                if (!data) throw new Error(t('product_not_found'));
                setProduct(data);

                if (data.variantes && data.variantes.length > 0) {
                    const firstAvailableVariant = data.variantes.find(v => v.cantidad_en_stock > 0);
                    if (firstAvailableVariant) {
                        const firstColor = firstAvailableVariant.color;
                        setSelectedColor(firstColor);
                        const firstSizeForColor = data.variantes.find(v => v.color === firstColor && v.cantidad_en_stock > 0);
                        setSelectedSize(firstSizeForColor ? firstSizeForColor.tamanio : null);
                    } else {
                        const firstVariantEver = data.variantes[0];
                        if(firstVariantEver) {
                            setSelectedColor(firstVariantEver.color);
                            setSelectedSize(null);
                        }
                    }
                }
            } catch (err) {
                const errorMessage = err?.response?.data?.detail || err.message || t('product_not_found');
                setError(errorMessage);
                notify(errorMessage, 'error');
            } finally {
                setLoading(false);
            }
        };
        fetchProductData();
    }, [productId, notify, t]);

    // ¡AQUÍ ESTÁ LA MAGIA DEL PARALLAX!
    useEffect(() => {
        if (!loading && product && imageContainerRef.current) {
            // Seleccionamos todas las imágenes dentro del contenedor
            const images = gsap.utils.toArray('.product-image-parallax');

            // Creamos una animación para cada imagen
            images.forEach(img => {
                gsap.to(img, {
                    yPercent: -10, // Mueve la imagen hacia arriba un 10% de su altura
                    ease: "none",
                    scrollTrigger: {
                        trigger: img,
                        start: "top bottom", // La animación empieza cuando la parte de arriba de la imagen toca la parte de abajo de la pantalla
                        end: "bottom top", // y termina cuando la parte de abajo de la imagen toca la de arriba de la pantalla
                        scrub: true // Esto hace que la animación se vincule directamente al scroll
                    }
                });
            });
        }
    }, [loading, product]); // Se ejecuta cuando el producto termina de cargar

    const availableColors = useMemo(() => {
        if (!product?.variantes) return [];
        return [...new Set(product.variantes.map(v => v.color))];
    }, [product]);

    const availableSizesForSelectedColor = useMemo(() => {
        if (!product?.variantes || !selectedColor) return [];
        const sizeOrder = ['XS', 'S', 'M', 'L', 'XL', 'XXL'];
        return product.variantes
            .filter(v => v.color === selectedColor)
            .sort((a, b) => {
                const indexA = sizeOrder.indexOf(a.tamanio.toUpperCase());
                const indexB = sizeOrder.indexOf(b.tamanio.toUpperCase());
                if (indexA === -1) return 1; if (indexB === -1) return -1;
                return indexA - indexB;
            });
    }, [product, selectedColor]);

    const isSelectionOutOfStock = useMemo(() => {
        if (!selectedColor) return false;
        if (!product.variantes.some(v => v.color === selectedColor && v.cantidad_en_stock > 0)) return true;
        if (selectedSize) {
            const variant = product.variantes.find(v => v.color === selectedColor && v.tamanio === selectedSize);
            return !variant || variant.cantidad_en_stock <= 0;
        }
        return false;
    }, [product, selectedColor, selectedSize]);

    const handleColorSelect = (color) => {
        setSelectedColor(color);
        const firstAvailableSize = product.variantes.find(v => v.color === color && v.cantidad_en_stock > 0);
        setSelectedSize(firstAvailableSize ? firstAvailableSize.tamanio : null);
    };

    const handleAddToCart = () => {
        const selectedVariant = product.variantes.find(v => v.tamanio === selectedSize && v.color === selectedColor);
        if (!selectedVariant || selectedVariant.cantidad_en_stock <= 0) {
            notify(t('product_out_of_stock_notification'), "error");
            return;
        }
        if (!selectedSize || !selectedColor) {
            notify(t('product_select_option_notification'), "error");
            return;
        }
        const itemToAdd = {
            variante_id: selectedVariant.id, quantity: 1, price: product.precio,
            name: product.nombre, image_url: product.urls_imagenes[0] || null,
            size: selectedVariant.tamanio, color: selectedVariant.color,
        };
        addItemToCart(itemToAdd);
        onSetAddedItem(itemToAdd);
        onOpenCartModal();
    };
    
    const getColorTranslationKey = (dbColor) => {
        const colorMapping = { 'negro': 'black', 'blanco': 'white', 'gris': 'grey', 'marrón': 'brown', 'beige': 'beige', 'azul': 'blue' };
        return colorMapping[dbColor.toLowerCase()] || dbColor.toLowerCase();
    };

    if (loading) return <Spinner message={t('product_loading')} />;
    if (error) return <div className="error-container" style={{ textAlign: 'center', padding: '5rem' }}><h1>{t('product_error')}: {error}</h1></div>;
    if (!product) return <div style={{ textAlign: 'center', padding: '5rem' }}><h1>{t('product_not_found')}</h1></div>;
    
    const formatPrice = (price) => {
        if (typeof price !== 'number') return '$--';
        return new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(price);
    };

    const imageUrls = getSafeImageUrls(product.urls_imagenes);

    return (
        <main>
            <div className="product-details-container-full">
                <div className="product-images-column" ref={imageContainerRef} style={{ overflow: 'hidden' }}>
                  {imageUrls.map((url, index) => (
                    <div key={index} className="product-image-wrapper">
                        <img 
                            src={transformCloudinaryUrl(url, 900)} 
                            alt={`${product.nombre} - vista ${index + 1}`} 
                            className="product-image-parallax"
                        />
                    </div>
                  ))}
                </div>
                
                <div className="product-info-panel-full">
                    <h1 className="product-name">{product.nombre}</h1>
                    <p className="product-price">{formatPrice(product.precio)}</p>
                    
                    <div className="product-selector">
                        <p className="selector-label">{t('product_color_label')} <span>{selectedColor ? t(`color_${getColorTranslationKey(selectedColor)}`, selectedColor) : 'N/A'}</span></p>
                        <div className="selector-buttons">
                            {availableColors.map(color => (
                                <button key={color} className={`size-button ${selectedColor === color ? 'active' : ''}`} onClick={() => handleColorSelect(color)}>
                                    {t(`color_${getColorTranslationKey(color)}`, color)}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="product-selector">
                        <p className="selector-label">{t('product_size_label')} <span>{selectedSize || 'N/A'}</span></p>
                        <div className="selector-buttons">
                            {availableSizesForSelectedColor.map(variant => (
                                <button key={variant.id} className={`size-button ${selectedSize === variant.tamanio ? 'active' : ''}`} onClick={() => setSelectedSize(variant.tamanio)} disabled={variant.cantidad_en_stock <= 0}>
                                    {variant.tamanio}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="product-description-full">
                        <p>{product.descripcion || t('product_no_description')}</p>
                    </div>
                    
                    <div className="product-actions">
                        <button onClick={handleAddToCart} disabled={isSelectionOutOfStock || !selectedSize} className="add-to-cart-button">
                            {isSelectionOutOfStock ? t('product_out_of_stock_button') : t('product_add_to_bag_button')}
                        </button>
                        {isAuthenticated && (
                            <button onClick={handleWishlistToggle} className="wishlist-button-detail" title={isWishlisted ? 'Quitar de Wishlist' : 'Añadir a Wishlist'}>
                                <Heart size={24} className={isWishlisted ? 'wishlisted' : ''} />
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </main>
    );
};

export default ProductPage;