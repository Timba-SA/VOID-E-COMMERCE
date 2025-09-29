// En FRONTEND/src/components/account/AddressManagement.jsx
import React, { useState, useEffect, useContext } from 'react';
import { getAddressesAPI, addAddressAPI } from '../../api/userApi';
import Spinner from '../common/Spinner';
import { NotificationContext } from '../../context/NotificationContext';

const AddressManagement = () => {
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading] = useState(true);
  const { notify } = useContext(NotificationContext);

  const [isFormVisible, setIsFormVisible] = useState(false);
  const [newAddress, setNewAddress] = useState({
    firstName: '', lastName: '', streetAddress: '', city: '', postalCode: '', country: 'Argentina', state: '', phone: ''
  });

  const fetchAddresses = async () => {
    try {
      const data = await getAddressesAPI();
      setAddresses(data);
    } catch (error) {
      notify('Could not load addresses.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAddresses();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setNewAddress(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await addAddressAPI(newAddress);
      notify('Address added successfully!', 'success');
      setIsFormVisible(false);
      fetchAddresses(); // Recargamos la lista
    } catch (error) {
      notify(error.detail || 'Failed to add address.', 'error');
      setLoading(false);
    }
  };

  if (loading && addresses.length === 0) return <Spinner />;

  return (
    <div>
      {!isFormVisible && (
        <button onClick={() => setIsFormVisible(true)} className="add-product-btn" style={{ marginBottom: '2rem' }}>
          ADD NEW ADDRESS
        </button>
      )}

      {isFormVisible && (
        <form onSubmit={handleSubmit} className="admin-form" style={{ marginBottom: '3rem' }}>
          <div className="form-grid">
            {Object.keys(newAddress).map(key => (
              <div className="input-group" key={key}>
                <label htmlFor={key}>{key.replace(/([A-Z])/g, ' $1').toUpperCase()}</label>
                <input type="text" id={key} name={key} value={newAddress[key]} onChange={handleChange} required />
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
            <button type="submit" className="form-button" disabled={loading}>{loading ? 'SAVING...' : 'SAVE ADDRESS'}</button>
            <button type="button" onClick={() => setIsFormVisible(false)} className="form-button outline">CANCEL</button>
          </div>
        </form>
      )}
      
      <div className="address-list">
        {addresses.length > 0 ? addresses.map((addr, index) => (
          <div key={addr.address_id || index} className="address-card">
            <p><strong>{addr.firstName} {addr.lastName}</strong></p>
            <p>{addr.streetAddress}</p>
            <p>{addr.city}, {addr.state} {addr.postalCode}</p>
            <p>{addr.country}</p>
            <p>Phone: {addr.phone}</p>
          </div>
        )) : !isFormVisible && <p>You have no saved addresses.</p>}
      </div>
    </div>
  );
};

export default AddressManagement;