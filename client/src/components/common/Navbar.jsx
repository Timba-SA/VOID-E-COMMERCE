import React, { useState, useRef, useEffect, useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/useAuthStore';
import { CartContext } from '../../context/CartContext';
import { useQuery } from '@tanstack/react-query';
import { getProducts } from '../../api/productsApi';
import { useTranslation } from 'react-i18next';

const Navbar = React.forwardRef(({ isMenuOpen, onToggleMenu }, ref) => {
    const { isAuthenticated, user, isAuthLoading } = useAuthStore();
    const { itemCount } = useContext(CartContext);
    const navigate = useNavigate();
    const { t, i18n } = useTranslation();

    const [isSearching, setIsSearching] = useState(false);
    const [query, setQuery] = useState('');
    const [isLangOpen, setIsLangOpen] = useState(false);
    const searchInputRef = useRef(null);
    const langDropdownRef = useRef(null); // <-- Ref para el menú de idioma

    // --- EFECTO PARA CERRAR EL MENÚ AL HACER CLICK AFUERA ---
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (langDropdownRef.current && !langDropdownRef.current.contains(event.target)) {
                setIsLangOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
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
              
              {isSearching && query.length > 2 && (
                <div className="search-results-dropdown">
                  {/* ...código de resultados de búsqueda... */}
                </div>
              )}
            </div>
            
            {/* --- ACÁ ESTÁ EL CAMBIO DE LÓGICA --- */}
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
            
            <Link to="/cart">{t('nav_bag')} ({itemCount})</Link>
          </div>
        </nav>
      </header>
    );
});

export default Navbar;