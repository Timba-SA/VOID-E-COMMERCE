import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

const Footer = () => {
  const { t } = useTranslation();

  return (
    <footer className="main-footer">
      <div className="footer-content">
        
        <div className="footer-column">
          <h4>{t('footer_social')}</h4>
          <ul>
            <li><a href="https://instagram.com" target="_blank" rel="noopener noreferrer">Instagram</a></li>
            <li><a href="https://tiktok.com" target="_blank" rel="noopener noreferrer">TikTok</a></li>
            <li><a href="https://facebook.com" target="_blank" rel="noopener noreferrer">Facebook</a></li>
            <li><a href="https://spotify.com" target="_blank" rel="noopener noreferrer">Spotify</a></li>
          </ul>
        </div>

        <div className="footer-column">
          <h4>{t('footer_info')}</h4>
          <ul>
            <li><Link to="/about">{t('footer_about')}</Link></li>
            <li><Link to="/contact">{t('footer_contact')}</Link></li>
          </ul>
        </div>

        <div className="footer-column subscribe-column">
          <h4>{t('footer_join')}</h4>
          <p>{t('footer_subscribe_text')}</p>
          <form className="subscribe-form">
            <input type="email" placeholder="Tu email" />
            <button type="submit">→</button>
          </form>
        </div>

      </div>
      <div className="footer-bottom">
        <p>{t('footer_copyright')}</p>
      </div>
    </footer>
  );
};

export default Footer;