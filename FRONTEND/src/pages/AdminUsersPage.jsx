import React, { useState, useEffect, useContext } from 'react';
import { getUsersAPI, updateUserRoleAPI } from '../api/adminApi';
import { NotificationContext } from '../context/NotificationContext';
import Spinner from '../components/common/Spinner';

const AdminUsersPage = () => {
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
      setError(err.detail || 'No se pudieron cargar los usuarios.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleRoleChange = async (userId, newRole) => {
    // Actualiza la UI inmediatamente para una respuesta visual rápida
    const originalUsers = users;
    const newUsers = users.map(u => (u.id === userId ? { ...u, role: newRole } : u));
    setUsers(newUsers);

    try {
      // Llama a la API para persistir el cambio
      await updateUserRoleAPI(userId, newRole);
      notify('Rol actualizado con éxito.', 'success');
      // El estado ya está actualizado, no es necesario hacer nada más
    } catch (err) {
      // Si la API falla, revierte el cambio en la UI y notifica el error
      setUsers(originalUsers);
      notify(`Error: ${err.detail || 'No se pudo actualizar el rol.'}`, 'error');
    }
  };

  if (loading) return <Spinner message="Cargando usuarios..." />;

  return (
    <div>
      <div className="admin-header">
        <h1>Gestión de Usuarios</h1>
      </div>

      {error && <h2 className="error-message" style={{marginBottom: '1rem'}}>{error}</h2>}

      <table className="admin-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Nombre</th>
            <th>Email</th>
            <th>Rol</th>
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
                      <option value="user">User</option>
                      <option value="admin">Admin</option>
                  </select>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="4" style={{textAlign: 'center'}}>No hay usuarios para mostrar.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

export default AdminUsersPage;