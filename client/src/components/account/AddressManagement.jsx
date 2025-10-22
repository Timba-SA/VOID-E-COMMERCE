// En FRONTEND/src/components/account/AddressManagement.jsx
import React, { useState, useEffect, useContext } from 'react';
import { getAddressesAPI, addAddressAPI, updateAddressAPI, deleteAddressAPI } from '../../api/userApi';
import Spinner from '../common/Spinner';
import { NotificationContext } from '../../context/NotificationContext';
import { useTranslation } from 'react-i18next';
import { countryPrefixes } from '../../utils/countryPrefixes';

const AddressManagement = () => {
  const { t } = useTranslation();
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading] = useState(true);
  const { notify } = useContext(NotificationContext);

  const [isFormVisible, setIsFormVisible] = useState(false);
  const [editingAddressId, setEditingAddressId] = useState(null);
  const [formData, setFormData] = useState({
    firstName: '', 
    lastName: '', 
    streetAddress: '', 
    city: '', 
    postalCode: '', 
    country: 'Argentina', 
    state: '', 
    prefix: '+54',
    phone: ''
  });

  const fetchAddresses = async () => {
    try {
      const data = await getAddressesAPI();
      console.log('📍 Direcciones recibidas del servidor:', data);
      setAddresses(data);
    } catch (error) {
      console.error('❌ Error al cargar direcciones:', error);
      notify(t('address_load_error', 'No se pudieron cargar las direcciones.'), 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAddresses();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleAddNew = () => {
    setEditingAddressId(null);
    setFormData({
      firstName: '', 
      lastName: '', 
      streetAddress: '', 
      city: '', 
      postalCode: '', 
      country: 'Argentina', 
      state: '', 
      prefix: '+54',
      phone: ''
    });
    setIsFormVisible(true);
  };

  const handleEdit = (address) => {
    setEditingAddressId(address.address_id);
    setFormData({
      firstName: address.firstName || '',
      lastName: address.lastName || '',
      streetAddress: address.streetAddress || '',
      city: address.city || '',
      postalCode: address.postalCode || '',
      country: address.country || 'Argentina',
      state: address.state || '',
      prefix: address.prefix || '+54',
      phone: address.phone || ''
    });
    setIsFormVisible(true);
  };

  const handleDelete = async (addressId) => {
    console.log('🗑️ Intentando eliminar dirección con ID:', addressId);
    
    if (!window.confirm(t('address_delete_confirm', '¿Estás seguro de eliminar esta dirección?'))) {
      console.log('❌ Usuario canceló la eliminación');
      return;
    }

    setLoading(true);
    try {
      await deleteAddressAPI(addressId);
      notify(t('address_deleted_success', 'Dirección eliminada exitosamente'), 'success');
      console.log('🔄 Recargando lista después de eliminar...');
      await fetchAddresses();
    } catch (error) {
      console.error('❌ Error al eliminar dirección:', error);
      notify(error.detail || t('address_delete_error', 'Error al eliminar la dirección'), 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      if (editingAddressId) {
        // Actualizar dirección existente
        console.log('📝 Actualizando dirección:', editingAddressId, formData);
        await updateAddressAPI(editingAddressId, formData);
        notify(t('address_updated_success', 'Dirección actualizada exitosamente'), 'success');
      } else {
        // Crear nueva dirección
        console.log('➕ Creando nueva dirección:', formData);
        const result = await addAddressAPI(formData);
        console.log('✅ Dirección creada:', result);
        notify(t('address_added_success', 'Dirección agregada exitosamente'), 'success');
      }
      
      setIsFormVisible(false);
      setEditingAddressId(null);
      
      // Recargar las direcciones
      console.log('🔄 Recargando lista de direcciones...');
      await fetchAddresses();
    } catch (error) {
      console.error('❌ Error al guardar dirección:', error);
      notify(error.detail || t('address_save_error', 'Error al guardar la dirección'), 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    setIsFormVisible(false);
    setEditingAddressId(null);
    setFormData({
      firstName: '', 
      lastName: '', 
      streetAddress: '', 
      city: '', 
      postalCode: '', 
      country: 'Argentina', 
      state: '', 
      prefix: '',
      phone: ''
    });
  };

  if (loading && addresses.length === 0) return <Spinner />;

  return (
    <div>
      {!isFormVisible && (
        <button onClick={handleAddNew} className="add-product-btn" style={{ marginBottom: '2rem' }}>
          {t('add_new_address', 'AGREGAR NUEVA DIRECCIÓN')}
        </button>
      )}

      {isFormVisible && (
        <form onSubmit={handleSubmit} className="admin-form" style={{ marginBottom: '3rem' }}>
          <h3 style={{ marginBottom: '1.5rem' }}>
            {editingAddressId 
              ? t('edit_address_title', 'Editar Dirección') 
              : t('new_address_title', 'Nueva Dirección')
            }
          </h3>
          
          <div className="form-grid">
            <div className="input-group">
              <label htmlFor="firstName">{t('address_first_name', 'NOMBRE')}</label>
              <input 
                type="text" 
                id="firstName" 
                name="firstName" 
                value={formData.firstName} 
                onChange={handleChange} 
                required 
              />
            </div>

            <div className="input-group">
              <label htmlFor="lastName">{t('address_last_name', 'APELLIDO')}</label>
              <input 
                type="text" 
                id="lastName" 
                name="lastName" 
                value={formData.lastName} 
                onChange={handleChange} 
                required 
              />
            </div>

            <div className="input-group" style={{ gridColumn: '1 / -1' }}>
              <label htmlFor="streetAddress">{t('address_street', 'DIRECCIÓN')}</label>
              <input 
                type="text" 
                id="streetAddress" 
                name="streetAddress" 
                value={formData.streetAddress} 
                onChange={handleChange} 
                required 
              />
            </div>

            <div className="input-group">
              <label htmlFor="city">{t('address_city', 'CIUDAD')}</label>
              <input 
                type="text" 
                id="city" 
                name="city" 
                value={formData.city} 
                onChange={handleChange} 
                required 
              />
            </div>

            <div className="input-group">
              <label htmlFor="state">{t('address_state', 'PROVINCIA/ESTADO')}</label>
              <input 
                type="text" 
                id="state" 
                name="state" 
                value={formData.state} 
                onChange={handleChange} 
                required 
              />
            </div>

            <div className="input-group">
              <label htmlFor="postalCode">{t('address_postal_code', 'CÓDIGO POSTAL')}</label>
              <input 
                type="text" 
                id="postalCode" 
                name="postalCode" 
                value={formData.postalCode} 
                onChange={handleChange} 
                required 
              />
            </div>

            <div className="input-group">
              <label htmlFor="country">{t('address_country', 'PAÍS')}</label>
              <input 
                type="text" 
                id="country" 
                name="country" 
                value={formData.country} 
                onChange={handleChange} 
                required 
              />
            </div>

            {/* Campo de teléfono con prefijo y número separados */}
            <div className="input-group">
              <label htmlFor="phone">{t('address_phone', 'TELÉFONO')}</label>
              <div className="phone-input-wrapper">
                <select
                  id="prefix"
                  name="prefix"
                  value={formData.prefix}
                  onChange={handleChange}
                  required
                  className="phone-prefix-select"
                >
                  {countryPrefixes.map(country => (
                    <option key={country.code} value={country.code}>
                      {country.code} {country.iso}
                    </option>
                  ))}
                </select>
                <input 
                  type="tel" 
                  id="phone" 
                  name="phone" 
                  value={formData.phone} 
                  onChange={handleChange}
                  placeholder="2611111111"
                  required
                  className="phone-number-input"
                />
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
            <button type="submit" className="form-button" disabled={loading}>
              {loading 
                ? t('saving', 'GUARDANDO...') 
                : editingAddressId 
                  ? t('update_address', 'ACTUALIZAR DIRECCIÓN')
                  : t('save_address', 'GUARDAR DIRECCIÓN')
              }
            </button>
            <button type="button" onClick={handleCancel} className="form-button outline">
              {t('cancel', 'CANCELAR')}
            </button>
          </div>
        </form>
      )}
      
      <div className="address-list">
        {addresses.length > 0 ? addresses.map((addr, index) => {
          console.log(`📋 Dirección ${index}:`, addr);
          console.log(`🆔 address_id:`, addr.address_id);
          
          return (
            <div key={addr.address_id || index} className="address-card">
              <div className="address-card-content">
                <p><strong>{addr.firstName} {addr.lastName}</strong></p>
                <p>{addr.streetAddress}</p>
                <p>{addr.city}, {addr.state} {addr.postalCode}</p>
                <p>{addr.country}</p>
                <p>{t('phone', 'Teléfono')}: {addr.prefix ? `${addr.prefix} ` : ''}{addr.phone}</p>
              </div>
              <div className="address-card-actions">
                <button 
                  onClick={() => {
                    console.log('🖱️ Click en Editar, addr completo:', addr);
                    handleEdit(addr);
                  }} 
                  className="action-btn edit"
                  disabled={loading}
                >
                  {t('edit', 'Editar')}
                </button>
                <button 
                  onClick={() => {
                    console.log('🖱️ Click en Eliminar, address_id:', addr.address_id);
                    handleDelete(addr.address_id);
                  }} 
                  className="action-btn delete"
                  disabled={loading || !addr.address_id}
                >
                  {t('delete', 'Eliminar')}
                </button>
              </div>
            </div>
          );
        }) : !isFormVisible && <p>{t('no_addresses', 'No tienes direcciones guardadas.')}</p>}
      </div>
    </div>
  );
};

export default AddressManagement;