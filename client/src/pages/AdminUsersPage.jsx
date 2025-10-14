import React, { useState, useEffect, useContext } from 'react';
import { useTranslation } from 'react-i18next';
import { getUsersAPI, updateUserRoleAPI } from '../api/adminApi';
import { NotificationContext } from '../context/NotificationContext';
import Spinner from '../components/common/Spinner';

const AdminUsersPage = () => {
  const { t } = useTranslation();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { notify } = useContext(NotificationContext);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const data = await getUsersAPI();
      setUsers(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.detail || t('admin_users_load_error'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleRoleChange = async (userId, newRole) => {
    const originalUsers = users;
    const newUsers = users.map(u => (u.id === userId ? { ...u, role: newRole } : u));
    setUsers(newUsers);

    try {
      await updateUserRoleAPI(userId, newRole);
      notify(t('admin_users_update_success'), 'success');
    } catch (err) {
      setUsers(originalUsers);
      const errorMsg = err.detail || t('admin_users_update_error');
      notify(`Error: ${errorMsg}`, 'error');
    }
  };

  if (loading) return <Spinner message={t('admin_users_loading')} />;

  return (
    <div>
      <div className="admin-header">
        <h1>{t('admin_users_title')}</h1>
      </div>

      {error && <h2 className="error-message" style={{marginBottom: '1rem'}}>{error}</h2>}

      <div className="table-responsive-wrapper">
        <table className="admin-table">
          <thead>
            <tr>
              <th>{t('admin_users_table_id')}</th>
              <th>{t('admin_users_table_name')}</th>
              <th>{t('admin_users_table_email')}</th>
              <th>{t('admin_users_table_role')}</th>
            </tr>
          </thead>
          <tbody>
            {users.length > 0 ? (
              users.map(user => (
                <tr key={user._id}>
                  <td title={user._id}>{user._id ? user._id.slice(-6) : 'N/A'}...</td>
                  <td>{user.name} {user.last_name}</td>
                  <td>{user.email}</td>
                  <td>
                    <select value={user.role} onChange={(e) => handleRoleChange(user._id, e.target.value)} className="role-select">
                        <option value="user">{t('admin_users_role_user')}</option>
                        <option value="admin">{t('admin_users_role_admin')}</option>
                    </select>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="4" style={{textAlign: 'center'}}>{t('admin_users_none')}</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AdminUsersPage;