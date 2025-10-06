// En client/src/components/common/Navbar.jsx
import React, { useState, useRef, useEffect, useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/useAuthStore';
import { CartContext } from '../../context/CartContext';
import { useQuery } from '@tanstack/react-query';
import { getProducts } from '../../api/productsApi';
import { useTranslation } from 'react-i18next';
import { Heart } from 'lucide-react'; // Importamos el ícono

const Navbar = React.forwardRef(({ isMenuOpen, onToggleMenu }, ref) => {
    const { isAuthenticated, user, isAuthLoading } = useAuthStore();
    const { itemCount } = useContext(CartContext);
    const navigate = useNavigate();
    const { t, i18n } = useTranslation();

    const [isSearching, setIsSearching] = useState(false);
    const [query, setQuery] = useState('');
    const [isLangOpen, setIsLangOpen] = useState(false);
    const searchInputRef = useRef(null);
    const langDropdownRef = useRef(null);

    const {
      data: searchResults,
      isLoading: isSearchLoading
    } = useQuery({
      queryKey: ['searchProducts', query],
      queryFn: () => getProducts({ q: query, limit: 5 }),
      enabled: query.length > 1,
      staleTime: 1000 * 60 * 5,
    });

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (langDropdownRef.current && !langDropdownRef.current.contains(event.target)) {
                setIsLangOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    useEffect(() => {
        if (isSearching) {
            searchInputRef.current?.focus();
        }
    }, [isSearching]);

    const handleSearchSubmit = (e) => {
        e.preventDefault();
        if (query.trim()) {
            navigate(`/search?q=${encodeURIComponent(query.trim())}`);
            setQuery('');
            setIsSearching(false);
        }
    };
    
    const handleResultClick = () => {
        setQuery('');
        setIsSearching(false);
    };

    const changeLanguage = (lang) => {
        i18n.changeLanguage(lang);
        setIsLangOpen(false);
    };

    return (
      <header className="main-header">
        <nav className="main-nav">
          <div className="nav-left">
            <button
              className={`hamburger-menu ${isMenuOpen ? 'open' : ''}`}
              aria-label="Abrir menú"
              aria-expanded={isMenuOpen}
              onClick={onToggleMenu}
            >
              <span></span>
              <span></span>
              <span></span>
            </button>
          </div>

          <div className="nav-center">
            <Link to="/" className="logo" ref={ref}>VOID</Link>
          </div>

          <div className="nav-right">
            <div className="search-container">
              {isSearching ? (
                <form onSubmit={handleSearchSubmit}>
                  <input
                    ref={searchInputRef}
                    type="text"
                    className="search-input-active"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onBlur={() => { if (!query.trim()) { setIsSearching(false); } }}
                    placeholder=""
                  />
                  <div className="search-underline"></div>
                </form>
              ) : (
                <div onClick={() => setIsSearching(true)} style={{ cursor: 'text' }}>
                  <label className="search-label">{t('nav_search')}</label>
                  <div className="search-underline"></div>
                </div>
              )}
              
              {isSearching && query.length > 1 && (
                <div className="search-results-dropdown">
                  {isSearchLoading && <div className="search-result-item">Buscando...</div>}
                  {!isSearchLoading && searchResults && searchResults.length === 0 && (
                    <div className="search-result-item">No se encontraron resultados.</div>
                  )}
                  {searchResults && searchResults.map(product => (
                    <Link 
                      key={product.id} 
                      to={`/product/${product.id}`} 
                      className="search-result-item"
                      onClick={handleResultClick}
                    >
                      <img src={product.urls_imagenes?.[0] || '/img/placeholder.jpg'} alt={product.nombre} />
                      <span>{product.nombre}</span>
                    </Link>
                  ))}
                </div>
              )}
            </div>
            
            <div className="language-selector" ref={langDropdownRef}>
              <a style={{cursor: 'pointer'}} onClick={() => setIsLangOpen(!isLangOpen)}>{t('nav_language')}</a>
              {isLangOpen && (
                <ul className="language-dropdown">
                  <li onClick={() => changeLanguage('es')}>Español</li>
                  <li onClick={() => changeLanguage('en')}>English</li>
                </ul>
              )}
            </div>
            
            {!isAuthLoading && (
              isAuthenticated ? (
                <>
                  {user?.role === 'admin' && (
                    <Link to="/admin">{t('nav_admin')}</Link>
                  )}
                  <Link to="/account">{t('nav_account')}</Link>
                </>
              ) : (
                <Link to="/login">{t('nav_login')}</Link>
              )
            )}
            
            {!isAuthLoading && isAuthenticated && (
              <Link to="/wishlist" title="Wishlist" style={{ display: 'flex', alignItems: 'center' }}>
                <Heart size={20} />
              </Link>
            )}
            
            <Link to="/cart">{t('nav_bag')} ({itemCount})</Link>
          </div>
        </nav>
      </header>
    );
});

export default Navbar;