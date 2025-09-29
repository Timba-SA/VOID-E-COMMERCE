// En FRONTEND/src/pages/ContactPage.jsx
import React from 'react';

const ContactPage = () => {
  return (
    <main className="login-page-container" style={{ maxWidth: '600px', margin: '0 auto' }}>
      <h1 className="form-title">CONTACT</h1>
      <p style={{ textAlign: 'center', marginBottom: '3rem', color: '#888', letterSpacing: '0.05em', lineHeight: '1.7' }}>
        Have a question about a product, your order, or just want to say hello? Use the form below or write to us directly. We'd love to hear from you.
      </p>

      <form className="login-form">
        <div className="input-group">
          <label htmlFor="name">NAME</label>
          <input type="text" id="name" required />
        </div>
        <div className="input-group">
          <label htmlFor="email">E-MAIL</label>
          <input type="email" id="email" required />
        </div>
        <div className="input-group">
          <label htmlFor="message">MESSAGE</label>
          <textarea id="message" rows="5" required></textarea>
        </div>
        <button type="submit" className="form-button" style={{ marginTop: '1.5rem' }}>
          SEND MESSAGE
        </button>
      </form>

      <div className="contact-info-footer" style={{ marginTop: '4rem', paddingTop: '2rem', borderTop: '1px solid #e0e0e0', width: '100%', textAlign: 'center', color: '#888' }}>
          <p><strong>E-MAIL:</strong> voidindumentaria.mza@gmail.com</p>
          <p><strong>HOURS:</strong> Monday to Friday, 9am - 6pm</p>
      </div>
    </main>
  );
};

export default ContactPage;