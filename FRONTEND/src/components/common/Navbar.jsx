import React, { useState, useRef, useEffect, useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/useAuthStore';
import { CartContext } from '../../context/CartContext';
import { useQuery } from '@tanstack/react-query';
import { getProducts } from '../../api/productsApi';

const Navbar = React.forwardRef(({ isMenuOpen, onToggleMenu }, ref) => {
    const { isAuthenticated, user, isAuthLoading } = useAuthStore();
    const { itemCount } = useContext(CartContext);
    const navigate = useNavigate();

    const [isSearching, setIsSearching] = useState(false);
    const [query, setQuery] = useState('');
    const searchInputRef = useRef(null);

    const { data: searchResults, isLoading: isSearchLoading } = useQuery({
      queryKey: ['search', query],
      queryFn: () => getProducts({ q: query, limit: 5 }),
      enabled: query.length > 2,
      staleTime: 1000 * 60 * 5,
    });

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
                  <label className="search-label">SEARCH</label>
                  <div className="search-underline"></div>
                </div>
              )}
              
              {isSearching && query.length > 2 && (
                <div className="search-results-dropdown">
                  {isSearchLoading && <div className="search-result-item">Searching...</div>}
                  {searchResults && searchResults.length > 0 && searchResults.map(product => (
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
                  {searchResults && searchResults.length === 0 && !isSearchLoading && (
                    <div className="search-result-item">No results found.</div>
                  )}
                </div>
              )}
            </div>
            
            <a>LANGUAGE</a>
            
            {!isAuthLoading && (
              isAuthenticated ? (
                <>
                  {user?.role === 'admin' && (
                    <Link to="/admin">ADMIN</Link>
                  )}
                  <Link to="/account">ACCOUNT</Link>
                </>
              ) : (
                <Link to="/login">LOGIN</Link>
              )
            )}
            
            <Link to="/cart">BAG ({itemCount})</Link>
          </div>
        </nav>
      </header>
    );
});

export default Navbar;