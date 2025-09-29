// En FRONTEND/src/components/account/ProfileManagement.jsx
import React from 'react';
import { useAuthStore } from '../../stores/useAuthStore';

const ProfileManagement = () => {
  const { user } = useAuthStore();

  return (
    <div>
      <div className="form-grid" style={{ gridTemplateColumns: '1fr' }}>
        <div className="input-group">
          <label>FIRST NAME</label>
          <input type="text" value={user?.name || ''} readOnly />
        </div>
        <div className="input-group">
          <label>LAST NAME</label>
          <input type="text" value={user?.last_name || ''} readOnly />
        </div>
        <div className="input-group">
          <label>E-MAIL</label>
          <input type="email" value={user?.email || ''} readOnly />
        </div>
      </div>
      <p style={{ color: '#888', fontSize: '0.8rem', marginTop: '2rem' }}>
        To update your details, please contact customer support.
      </p>
    </div>
  );
};

export default ProfileManagement;