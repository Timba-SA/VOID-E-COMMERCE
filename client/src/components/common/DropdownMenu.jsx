import React, { useState, useEffect, useContext } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { getCategories } from '../../api/categoriesApi';
import { getCategoryName } from '../../utils/categoryHelper';
import { useAuthStore } from '../../stores/useAuthStore';
import { CartContext } from '../../context/CartContext';
import { useTranslation } from 'react-i18next';

// Categorías de hombre por su nombre en español (nombre original en DB)
const MENSWEAR_CATEGORIES = ['hoodies', 'camperas', 'remeras', 'pantalones'];

const DropdownMenu = ({ isOpen, onClose, logoPosition, onOpenSearch }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const currentSubCategory = location.pathname.split('/')[2] || '';
  
  const { t, i18n } = useTranslation();
  const { isAuthenticated, user, isAuthLoading } = useAuthStore();
  const { itemCount } = useContext(CartContext);

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

        // Separar por nombre en español (el campo 'nombre' de la DB)
        const menswear = allCategories.filter(c => MENSWEAR_CATEGORIES.includes(c.nombre.toLowerCase()));
        const womenswear = allCategories.filter(c => !MENSWEAR_CATEGORIES.includes(c.nombre.toLowerCase()));

        setCategories({
          womenswear: womenswear.map(c => ({
            name: getCategoryName(c, i18n.language),
            path: `/catalog/${c.nombre.toLowerCase()}`,
            id: c.id
          })),
          menswear: menswear.map(c => ({
            name: getCategoryName(c, i18n.language),
            path: `/catalog/${c.nombre.toLowerCase()}`,
            id: c.id
          }))
        });

      } catch (error) {
        console.error("Falló la carga de categorías:", error);
      }
    };

    if (isOpen) {
        fetchAndOrganizeCategories();
    }
  }, [isOpen, t, i18n.language]); // Agregar i18n.language para recargar al cambiar idioma

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
  
  const handleSearchClick = () => {
    onClose();
    onOpenSearch();
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
        {isOpen && logoPosition && <div style={phantomLogoStyle}>VOID</div>}

        <div className="dropdown-header">
          <button className={`close-btn ${isOpen ? 'open' : ''}`} aria-label="Cerrar menú" onClick={onClose}>
            <span/><span/><span/>
          </button>
          <Link to="/" className="dropdown-logo" onClick={onClose} style={{ visibility: 'hidden' }}>VOID</Link>
        </div>

        <div className="dropdown-content">
          <div className="menu-categories">
            <nav className="dropdown-nav-left">
              <ul>
                <li>
                  <div onClick={() => handleMainCategoryClick('womenswear')} className={`category-link ${activeCategory === 'womenswear' ? 'active-category' : ''}`}>
                    {t('menu_womenswear')}
                  </div>
                </li>
                <li>
                  <div onClick={() => handleMainCategoryClick('menswear')} className={`category-link ${activeCategory === 'menswear' ? 'active-category' : ''}`}>
                    {t('menu_menswear')}
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
                          {t(`menu_view_all_${activeCategory}`)}
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

          <nav className="dropdown-nav-secondary">
            <ul>
              <li><button onClick={handleSearchClick} className="category-link">{t('nav_search')}</button></li>
              <li><a href="#" onClick={(e) => e.preventDefault()} className="category-link">{t('nav_language')}</a></li>
              {!isAuthLoading && (
                isAuthenticated ? (
                  <>
                    {user?.role === 'admin' && (
                      <li><Link to="/admin" onClick={onClose} className="category-link">{t('nav_admin')}</Link></li>
                    )}
                    <li><Link to="/account" onClick={onClose} className="category-link">{t('nav_account')}</Link></li>
                  </>
                ) : (
                  <li><Link to="/login" onClick={onClose} className="category-link">{t('nav_login')}</Link></li>
                )
              )}
              <li><Link to="/cart" onClick={onClose} className="category-link">{t('nav_bag')} ({itemCount})</Link></li>
            </ul>
          </nav>

          <div className="dropdown-footer">
            <div className="footer-images">
              {/* ¡ACÁ ESTÁ EL ARREGLO! LE SAQUÉ EL /img/ */}
              <div className="footer-image left"><img src="/dropdownIzquierda.jpg" alt="Carretera" /></div>
              <div className="footer-image right"><img src="/dropdownDerecha.jpg" alt="Autopista" /></div>
            </div>
            <h3 className="footer-text">{t('menu_footer_text')}</h3>
          </div>
        </div>
      </aside>
    </>
  );
};

export default DropdownMenu;