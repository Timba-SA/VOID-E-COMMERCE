import React, { useState, useContext } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../stores/useAuthStore';
import { loginUser } from '../api/authApi';
import { mergeCartAPI } from '../api/cartApi';
import { NotificationContext } from '../context/NotificationContext';

const LoginPage = () => {
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  
  const { login } = useAuthStore(); 
  
  const { notify } = useContext(NotificationContext);
  const navigate = useNavigate();
  const location = useLocation();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const data = await loginUser(email, password);
      await login(data.access_token);
      
      const guestSessionId = localStorage.getItem('guestSessionId');
      if (guestSessionId) {
        await mergeCartAPI(guestSessionId);
        localStorage.removeItem('guestSessionId');
      }

      notify(t('login_success_notification', 'Inicio de sesión exitoso'), 'success');
      
      const from = location.state?.from || '/';
      navigate(from, { replace: true });

    } catch (err) {
      const errorMessage = err.detail || t('login_error_notification', 'Error al iniciar sesión.');
      setError(errorMessage);
      notify(errorMessage, 'error');
    }
  };

  return (
    <main className="login-page-container">
      <div className="login-form-section">
        <h1 className="form-title animate-fadeInUp">{t('login_title')}</h1>
        <form onSubmit={handleSubmit} className="login-form">
          <div className="input-group animate-fadeInUp animation-delay-100">
            <label htmlFor="email">{t('login_email_label')}</label>
            <input 
              type="email" 
              id="email" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required 
            />
          </div>
          <div className="input-group animate-fadeInUp animation-delay-200">
            <label htmlFor="password">{t('login_password_label')}</label>
            <input 
              type="password" 
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <Link to="/forgot-password" className="forgot-password-link animate-fadeInUp animation-delay-300">{t('login_forgot_password')}</Link>
          {error && <p className="error-message">{error}</p>}
          <button type="submit" className="form-button animate-fadeInUp animation-delay-400">{t('login_button')}</button>
        </form>
      </div>

      <div className="signup-section animate-fadeInUp animation-delay-500">
        <h2 className="form-subtitle">{t('login_not_registered')}</h2>
        <p className="signup-text">{t('login_create_account')}</p>
        <Link to="/register" className="form-button animate-fadeInUp animation-delay-600">{t('login_signup_button')}</Link>
      </div>
    </main>
  );
};

export default LoginPage;