// En FRONTEND/src/components/account/ProfileManagement.jsx
import React from 'react';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../../stores/useAuthStore';

const ProfileManagement = () => {
  const { t } = useTranslation();
  const { user } = useAuthStore();

  return (
    <div>
      <div className="form-grid" style={{ gridTemplateColumns: '1fr' }}>
        <div className="input-group">
          <label>{t('profile_first_name', 'NOMBRE')}</label>
          <input type="text" value={user?.name || ''} readOnly />
        </div>
        <div className="input-group">
          <label>{t('profile_last_name', 'APELLIDO')}</label>
          <input type="text" value={user?.last_name || ''} readOnly />
        </div>
        <div className="input-group">
          <label>{t('profile_email', 'E-MAIL')}</label>
          <input type="email" value={user?.email || ''} readOnly />
        </div>
      </div>
      <p style={{ color: '#888', fontSize: '0.8rem', marginTop: '2rem' }}>
        {t('profile_contact_support', 'Para actualizar tus datos, por favor contacta con atención al cliente.')}
      </p>
    </div>
  );
};

export default ProfileManagement;