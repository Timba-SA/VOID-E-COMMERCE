import React, { useState, useContext } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '../stores/useAuthStore';
import { loginUser } from '../api/authApi';
import { mergeCartAPI } from '../api/cartApi'; // Import merge function
import { NotificationContext } from '../context/NotificationContext';

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  
  const { login } = useAuthStore(); 
  
  const { notify } = useContext(NotificationContext);
  const navigate = useNavigate();
  const location = useLocation(); // Get location

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const data = await loginUser(email, password);
      await login(data.access_token);
      
      // --- CART MERGE LOGIC ---
      const guestSessionId = localStorage.getItem('guestSessionId');
      if (guestSessionId) {
        await mergeCartAPI(guestSessionId);
        localStorage.removeItem('guestSessionId');
      }
      // -------------------------

      notify('Inicio de sesión exitoso', 'success');
      
      // --- REDIRECT LOGIC ---
      const from = location.state?.from || '/';
      navigate(from, { replace: true });
      // ----------------------

    } catch (err) {
      const errorMessage = err.detail || 'Error al iniciar sesión. Revisa tus credenciales.';
      setError(errorMessage);
      notify(errorMessage, 'error');
    }
  };

  return (
    <main className="login-page-container">
      <div className="login-form-section">
        <h1 className="form-title">LOG IN</h1>
        <form onSubmit={handleSubmit} className="login-form">
          <div className="input-group">
            <label htmlFor="email">E-MAIL</label>
            <input 
              type="email" 
              id="email" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required 
            />
          </div>
          <div className="input-group">
            <label htmlFor="password">PASSWORD</label>
            <input 
              type="password" 
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <Link to="/forgot-password" className="forgot-password-link">FORGOT PASSWORD?</Link>
          {error && <p className="error-message">{error}</p>}
          <button type="submit" className="form-button">LOG IN</button>
        </form>
      </div>

      <div className="signup-section">
        <h2 className="form-subtitle">ARE YOU NOT REGISTERED YET?</h2>
        <p className="signup-text">CREATE AN ACCOUNT</p>
        <Link to="/register" className="form-button">SIGN UP</Link>
      </div>
    </main>
  );
};

export default LoginPage;