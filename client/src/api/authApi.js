// En FRONTEND/src/api/authApi.js

import axiosClient from '../hooks/axiosClient';

export const loginUser = async (email, password) => {
  const params = new URLSearchParams();
  params.append('username', email);
  params.append('password', password);

  try {
    const response = await axiosClient.post('/auth/login', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error during login:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};

export const registerUser = async (userData) => {
  try {
    const response = await axiosClient.post('/auth/register', userData);
    return response.data;
  } catch (error) {
    console.error('Error during registration:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};

export const forgotPasswordAPI = async (email) => {
  try {
    const response = await axiosClient.post('/auth/forgot-password', { email });
    return response.data;
  } catch (error) {
    console.error('Error en forgot password:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};

// --- ¡ACÁ ESTÁ EL ARREGLO POSTA! ---
export const resetPasswordAPI = async (token, newPassword) => {
  try {
    // La URL ahora incluye el token al final, como espera el backend.
    // Y en el cuerpo de la petición, mandamos solo la nueva contraseña.
    const response = await axiosClient.post(
      `/auth/reset-password/${token}`, 
      { new_password: newPassword }
    );
    return response.data;
  } catch (error) {
    console.error('Error en reset password:', error.response?.data?.detail || error.message);
    throw error.response?.data || error;
  }
};