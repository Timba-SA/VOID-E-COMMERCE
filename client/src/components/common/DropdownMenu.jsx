import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { getCategories } from '../../api/categoriesApi';

const MENSWEAR_CATEGORIES = ['hoodies', 'jackets', 'shirts', 'pants'];

const DropdownMenu = ({ isOpen, onClose, logoPosition }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const currentSubCategory = location.pathname.split('/')[2] || '';

  const [activeCategory, setActiveCategory] = useState('menswear');
  const [categories, setCategories] = useState({ womenswear: [], menswear: [] });

  useEffect(() => {
    const fetchAndOrganizeCategories = async () => {
      try {
        const allCategories = await getCategories();
        if (!Array.isArray(allCategories)) {
          console.error("Error: getCategories no devolvió un array.");
          return;
        }

        const menswear = allCategories.filter(c => MENSWEAR_CATEGORIES.includes(c.nombre.toLowerCase()));
        const womenswear = allCategories.filter(c => !MENSWEAR_CATEGORIES.includes(c.nombre.toLowerCase()));

        setCategories({
          womenswear: womenswear.map(c => ({ name: c.nombre.toUpperCase(), path: `/catalog/${c.nombre.toLowerCase()}` })),
          menswear: menswear.map(c => ({ name: c.nombre.toUpperCase(), path: `/catalog/${c.nombre.toLowerCase()}` }))
        });

      } catch (error) {
        console.error("Falló la carga de categorías:", error);
      }
    };

    if (isOpen) {
        fetchAndOrganizeCategories();
    }
  }, [isOpen]);

  const handleNavigateAndClose = (path) => {
    navigate(path);
    onClose();
  };

  const handleMainCategoryClick = (category) => {
    if (activeCategory === category) {
      handleNavigateAndClose(`/catalog/${category}`);
    } else {
      setActiveCategory(category);
    }
  };

  const phantomLogoStyle = logoPosition ? {
    position: 'fixed',
    top: `${logoPosition.top}px`,
    left: `${logoPosition.left}px`,
    width: `${logoPosition.width}px`,
    height: `${logoPosition.height}px`,
    color: 'var(--text-color)',
    fontFamily: 'var(--font-logo)',
    fontSize: '60px',
    fontWeight: '400',
    letterSpacing: '0.05em',
    lineHeight: '1',
    zIndex: 2003,
    pointerEvents: 'none',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center'
  } : {};

  return (
    <>
      <div className={`overlay ${isOpen ? 'active' : ''}`} onClick={onClose} />
      
      <aside className={`dropdown-menu ${isOpen ? 'open' : ''}`}>
        {isOpen && logoPosition && (
          <div style={phantomLogoStyle}>
            VOID
          </div>
        )}

        <div className="dropdown-header">
          <button
            className={`close-btn ${isOpen ? 'open' : ''}`}
            aria-label="Cerrar menú"
            onClick={onClose}
          >
            <span/>
            <span/>
            <span/>
          </button>
          <Link to="/" className="dropdown-logo" onClick={onClose} style={{ visibility: 'hidden' }}>
              VOID
          </Link>
        </div>

        <div className="dropdown-content">
          <div className="menu-categories">
            <nav className="dropdown-nav-left">
              <ul>
                <li>
                  <div 
                    onClick={() => handleMainCategoryClick('womenswear')} 
                    className={`category-link ${activeCategory === 'womenswear' ? 'active-category' : ''}`}
                  >
                    WOMENSWEAR
                  </div>
                </li>
                <li>
                  <div 
                    onClick={() => handleMainCategoryClick('menswear')} 
                    className={`category-link ${activeCategory === 'menswear' ? 'active-category' : ''}`}
                  >
                    MENSWEAR
                  </div>
                </li>
              </ul>
            </nav>
            <nav className="dropdown-nav-right">
              {categories[activeCategory] && categories[activeCategory].length > 0 && (
                <ul className="submenu active-submenu">
                  <li key={`all-${activeCategory}`}>
                      <Link
                          to={`/catalog/${activeCategory}`}
                          onClick={() => handleNavigateAndClose(`/catalog/${activeCategory}`)} 
                          className="view-all-link"
                      >
                          VIEW ALL {activeCategory.toUpperCase()}
                      </Link>
                  </li>
                  
                  {categories[activeCategory].map(subcategory => (
                    <li key={subcategory.name}>
                      <Link 
                        to={subcategory.path} 
                        onClick={onClose} 
                        className={currentSubCategory === subcategory.path.split('/')[2] ? 'active-link' : ''}
                      >
                        {subcategory.name}
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </nav>
          </div>
          <div className="dropdown-footer">
            <div className="footer-images">
              <div className="footer-image left"><img src="/img/dropdownIzquierda.jpg" alt="Carretera" /></div>
              <div className="footer-image right"><img src="/img/dropdownDerecha.jpg" alt="Autopista" /></div>
            </div>
            <h3 className="footer-text">FIND YOUR OWN ROAD</h3>
          </div>
        </div>
      </aside>
    </>
  );
};

export default DropdownMenu;