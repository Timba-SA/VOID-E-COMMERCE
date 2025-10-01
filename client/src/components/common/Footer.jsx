// En FRONTEND/src/components/common/Footer.jsx
import React from 'react';
import { Link } from 'react-router-dom';

const Footer = () => {
  return (
    <footer className="main-footer">
      <div className="footer-content">
        
        {/* --- ACÁ ESTÁ LA MAGIA, FIERA --- */}
        <div className="footer-column">
          <h4>SOCIAL MEDIA</h4>
          <ul>
            {/* OJO: Te puse links de ejemplo, metele las URLs posta de tus redes */}
            <li><a href="https://instagram.com" target="_blank" rel="noopener noreferrer">Instagram</a></li>
            <li><a href="https://tiktok.com" target="_blank" rel="noopener noreferrer">TikTok</a></li>
            <li><a href="https://facebook.com" target="_blank" rel="noopener noreferrer">Facebook</a></li>
            <li><a href="https://spotify.com" target="_blank" rel="noopener noreferrer">Spotify</a></li>
          </ul>
        </div>
        {/* --- FIN DE LA MAGIA --- */}

        <div className="footer-column">
          <h4>INFO</h4>
          <ul>
            <li><Link to="/about">About Us</Link></li>
            <li><Link to="/contact">Contact</Link></li>
            <li><a href="#">Shipping</a></li>
            <li><a href="#">Returns</a></li>
          </ul>
        </div>

        <div className="footer-column subscribe-column">
          <h4>JOIN THE VOID</h4>
          <p>Suscribite a nuestro newsletter y sé el primero en enterarte de todo.</p>
          <form className="subscribe-form">
            <input type="email" placeholder="Tu email" />
            <button type="submit">→</button>
          </form>
        </div>

      </div>
      <div className="footer-bottom">
        <p>© 2025 VOID. Todos los derechos reservados.</p>
        {/* Y de acá volaron los links de redes porque ya no van más */}
      </div>
    </footer>
  );
};

export default Footer;