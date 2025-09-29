// En FRONTEND/src/pages/ForgotPasswordPage.jsx
import React, { useState, useContext } from 'react';
import { Link } from 'react-router-dom';
import { NotificationContext } from '../context/NotificationContext';
import { forgotPasswordAPI } from '../api/authApi';

const ForgotPasswordPage = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const { notify } = useContext(NotificationContext);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // The backend will always return a generic success message for security
      const data = await forgotPasswordAPI(email);
      notify(data.message, 'success');
      setEmail('');
    } catch (err) {
      // Even if the API fails, we show the generic message
      notify('If your email is in our database, you will receive a link to reset your password.', 'success');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="login-page-container" style={{ maxWidth: '500px', margin: '0 auto' }}>
      <h1 className="form-title">RECOVER PASSWORD</h1>
      <p style={{ textAlign: 'center', marginBottom: '2.5rem', color: '#888', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
        Enter your e-mail and we will send you a link to create a new one.
      </p>
      <form onSubmit={handleSubmit} className="login-form">
        <div className="input-group">
          <label htmlFor="email">E-MAIL</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={loading}
          />
        </div>
        <button type="submit" className="form-button" disabled={loading} style={{ marginTop: '1.5rem' }}>
          {loading ? 'SENDING...' : 'SEND LINK'}
        </button>
      </form>
      <div style={{ marginTop: '4rem', paddingTop: '2rem', borderTop: '1px solid #e0e0e0', width: '100%' }}>
        <p className="signup-text">ALREADY REMEMBERED?</p>
        <Link to="/login" className="form-button outline">BACK TO LOG IN</Link>
      </div>
    </main>
  );
};

export default ForgotPasswordPage;