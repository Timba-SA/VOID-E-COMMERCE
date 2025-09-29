import React, { useState, useContext } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { registerUser, loginUser } from '../api/authApi'; // Import both
import { useAuthStore } from '../stores/useAuthStore'; // Import store
import { mergeCartAPI } from '../api/cartApi'; // Import merge
import { NotificationContext } from '../context/NotificationContext';

const RegisterPage = () => {
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
  const location = useLocation(); // Get location
  const { login } = useAuthStore(); // Get login action

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
      notify('Debes aceptar la declaración de privacidad para continuar.', 'error');
      return;
    }

    try {
      const apiPayload = {
        email: formData.email,
        password: formData.password,
        name: formData.name,
        last_name: formData.lastName, // El backend espera last_name
        phone: {
          prefix: formData.phonePrefix,
          number: formData.phoneNumber,
        },
      };

      // 1. Register the user
      await registerUser(apiPayload);

      // 2. Automatically log them in
      const loginData = await loginUser(formData.email, formData.password);
      await login(loginData.access_token);

      // 3. Merge the cart
      const guestSessionId = localStorage.getItem('guestSessionId');
      if (guestSessionId) {
        await mergeCartAPI(guestSessionId);
        localStorage.removeItem('guestSessionId');
      }

      notify('¡Cuenta creada con éxito!', 'success');
      
      // 4. Redirect
      const from = location.state?.from || '/';
      navigate(from, { replace: true });

    } catch (err) {
      const errorMessage = err.detail || 'Ocurrió un error al registrar la cuenta.';
      notify(errorMessage, 'error');
      console.error('Error en el registro:', err);
    }
  };

  return (
    <main className="register-page-container">
      <h1 className="form-title">REGISTER</h1>
      <form onSubmit={handleSubmit} className="register-form">
        {/* Los campos del formulario no cambian, solo la lógica de envío */}
        <div className="input-group">
          <label htmlFor="email">E-MAIL</label>
          <input type="email" id="email" name="email" value={formData.email} onChange={handleChange} required />
        </div>
        <div className="input-group">
          <label htmlFor="password">PASSWORD</label>
          <input type="password" id="password" name="password" value={formData.password} onChange={handleChange} required />
        </div>
        <div className="input-group">
          <label htmlFor="name">NAME</label>
          <input type="text" id="name" name="name" value={formData.name} onChange={handleChange} required />
        </div>
        <div className="input-group">
          <label htmlFor="lastName">LAST NAME</label>
          <input type="text" id="lastName" name="lastName" value={formData.lastName} onChange={handleChange} required />
        </div>

        <div className="phone-input-group">
          <div className="input-group prefix">
            <label htmlFor="phonePrefix">PREFIX</label>
            <input type="text" id="phonePrefix" name="phonePrefix" value={formData.phonePrefix} onChange={handleChange} />
          </div>
          <div className="input-group phone-number">
            <label htmlFor="phoneNumber">PHONE</label>
            <input type="tel" id="phoneNumber" name="phoneNumber" value={formData.phoneNumber} onChange={handleChange} />
          </div>
        </div>

        <div className="checkbox-group">
          <label className="checkbox-container-register">
            <input type="checkbox" name="acceptPrivacy" checked={formData.acceptPrivacy} onChange={handleChange} />
            <span className="checkmark-register"></span>
            I ACCEPT THE <Link to="/privacy" className="privacy-link">PRIVACY STATEMENT</Link>
          </label>
        </div>

        {/* Los mensajes de error/éxito ahora se manejan por el sistema de notificaciones global */}

        <button type="submit" className="form-button outline">CREATE AN ACCOUNT</button>
      </form>
    </main>
  );
};

export default RegisterPage;