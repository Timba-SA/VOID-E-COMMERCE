import React, { useState, useContext } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Trans, useTranslation } from 'react-i18next'; // Importar Trans y useTranslation
import { registerUser, loginUser } from '../api/authApi';
import { useAuthStore } from '../stores/useAuthStore';
import { mergeCartAPI } from '../api/cartApi';
import { NotificationContext } from '../context/NotificationContext';
import { countryPrefixes } from '../utils/countryPrefixes';

const RegisterPage = () => {
  const { t } = useTranslation(); // Inicializar
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    lastName: '',
    phonePrefix: '+54',
    phoneNumber: '',
    acceptPrivacy: false,
  });
  
  const { notify } = useContext(NotificationContext);
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuthStore();

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prevState => ({
      ...prevState,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.acceptPrivacy) {
      notify(t('register_error_privacy'), 'error'); // Opcional
      return;
    }

    try {
      const apiPayload = {
        email: formData.email,
        password: formData.password,
        name: formData.name,
        last_name: formData.lastName,
        phone: {
          prefix: formData.phonePrefix,
          number: formData.phoneNumber,
        },
      };

      await registerUser(apiPayload);
      const loginData = await loginUser(formData.email, formData.password);
      await login(loginData.access_token);
      
      const guestSessionId = localStorage.getItem('guestSessionId');
      if (guestSessionId) {
        await mergeCartAPI(guestSessionId);
        localStorage.removeItem('guestSessionId');
      }

      notify(t('register_success_notification'), 'success'); // Opcional
      
      const from = location.state?.from || '/';
      navigate(from, { replace: true });

    } catch (err) {
      const errorMessage = err.detail || t('register_error_generic');
      notify(errorMessage, 'error');
      console.error('Error en el registro:', err);
    }
  };

  return (
    <main className="register-page-container">
      <h1 className="form-title">{t('register_title')}</h1>
      <form onSubmit={handleSubmit} className="register-form">
        <div className="input-group">
          <label htmlFor="email">{t('login_email_label')}</label>
          <input type="email" id="email" name="email" value={formData.email} onChange={handleChange} required />
        </div>
        <div className="input-group">
          <label htmlFor="password">{t('login_password_label')}</label>
          <input type="password" id="password" name="password" value={formData.password} onChange={handleChange} required />
        </div>
        <div className="input-group">
          <label htmlFor="name">{t('register_name_label')}</label>
          <input type="text" id="name" name="name" value={formData.name} onChange={handleChange} required />
        </div>
        <div className="input-group">
          <label htmlFor="lastName">{t('register_lastname_label')}</label>
          <input type="text" id="lastName" name="lastName" value={formData.lastName} onChange={handleChange} required />
        </div>
        <div className="phone-input-group">
          <div className="input-group prefix">
            <label htmlFor="phonePrefix">{t('register_prefix_label')}</label>
            <select 
              id="phonePrefix" 
              name="phonePrefix" 
              value={formData.phonePrefix} 
              onChange={handleChange}
            >
              {countryPrefixes.map(country => (
                <option key={country.code} value={country.code}>
                  {country.code} {country.iso}
                </option>
              ))}
            </select>
          </div>
          <div className="input-group phone-number">
            <label htmlFor="phoneNumber">{t('register_phone_label')}</label>
            <input type="tel" id="phoneNumber" name="phoneNumber" value={formData.phoneNumber} onChange={handleChange} placeholder="2616657396" />
          </div>
        </div>
        <div className="checkbox-group">
          <label className="checkbox-container-register">
            <input type="checkbox" name="acceptPrivacy" checked={formData.acceptPrivacy} onChange={handleChange} />
            <span className="checkmark-register"></span>
            <Trans i18nKey="register_accept_privacy">
              I ACCEPT THE <Link to="/privacy" className="privacy-link">PRIVACY STATEMENT</Link>
            </Trans>
          </label>
        </div>
        <button type="submit" className="form-button outline">{t('register_create_account_button')}</button>
      </form>
    </main>
  );
};

export default RegisterPage;