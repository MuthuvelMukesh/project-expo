import React, { useState } from 'react';
import api from '../../services/api';
import './HR.css';

/**
 * EmployeeForm - Create/edit employee records with HR details
 */
const EmployeeForm = ({ onSuccess, editingEmployee = null }) => {
  const [formData, setFormData] = useState(editingEmployee || {
    user_id: '',
    employee_type: 'faculty',
    date_of_joining: new Date().toISOString().split('T')[0],
    date_of_birth: '',
    phone: '',
    address: '',
    bank_account: '',
    bank_name: '',
    ifsc_code: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const employeeTypes = ['faculty', 'staff', 'admin', 'non_teaching'];
  const banks = ['HDFC', 'ICICI', 'SBI', 'Axis', 'BoI', 'PNB', 'Other'];

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (editingEmployee?.id) {
        await api.put(`/api/hr/employees/${editingEmployee.id}`, formData);
      } else {
        await api.post('/api/hr/employees', formData);
      }
      
      setSuccess(true);
      if (onSuccess) onSuccess();
      
      setTimeout(() => {
        setSuccess(false);
        if (!editingEmployee?.id) {
          setFormData({
            user_id: '',
            employee_type: 'faculty',
            date_of_joining: new Date().toISOString().split('T')[0],
            date_of_birth: '',
            phone: '',
            address: '',
            bank_account: '',
            bank_name: '',
            ifsc_code: '',
          });
        }
      }, 2000);
    } catch (err) {
      setError(err.message || 'Failed to save employee');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="employee-form">
      <h3>{editingEmployee ? 'Edit Employee' : 'Add New Employee'}</h3>
      
      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">Employee saved successfully!</div>}

      <form onSubmit={handleSubmit}>
        <div className="form-section">
          <h4>Basic Information</h4>
          
          <div className="form-group">
            <label>User ID</label>
            <input 
              type="number" 
              name="user_id" 
              value={formData.user_id}
              onChange={handleChange}
              placeholder="User ID"
              disabled={editingEmployee?.id}
              required
            />
          </div>

          <div className="form-group">
            <label>Employee Type</label>
            <select 
              name="employee_type" 
              value={formData.employee_type}
              onChange={handleChange}
              required
            >
              {employeeTypes.map(type => (
                <option key={type} value={type}>
                  {type.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                </option>
              ))}
            </select>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Date of Joining</label>
              <input 
                type="date" 
                name="date_of_joining" 
                value={formData.date_of_joining}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label>Date of Birth</label>
              <input 
                type="date" 
                name="date_of_birth" 
                value={formData.date_of_birth}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="form-group">
            <label>Phone</label>
            <input 
              type="tel" 
              name="phone" 
              value={formData.phone}
              onChange={handleChange}
              placeholder="+91 XXXXX XXXXX"
            />
          </div>

          <div className="form-group">
            <label>Address</label>
            <textarea 
              name="address" 
              value={formData.address}
              onChange={handleChange}
              placeholder="Full address"
              rows="3"
            />
          </div>
        </div>

        <div className="form-section">
          <h4>Banking Information</h4>
          
          <div className="form-group">
            <label>Bank Name</label>
            <select 
              name="bank_name" 
              value={formData.bank_name}
              onChange={handleChange}
            >
              <option value="">Select Bank</option>
              {banks.map(bank => (
                <option key={bank} value={bank}>{bank}</option>
              ))}
            </select>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Bank Account Number</label>
              <input 
                type="text" 
                name="bank_account" 
                value={formData.bank_account}
                onChange={handleChange}
                placeholder="Account number"
              />
            </div>

            <div className="form-group">
              <label>IFSC Code</label>
              <input 
                type="text" 
                name="ifsc_code" 
                value={formData.ifsc_code}
                onChange={handleChange}
                placeholder="IFSC code"
              />
            </div>
          </div>
        </div>

        <button 
          type="submit" 
          className="btn-primary"
          disabled={loading}
        >
          {loading ? 'Saving...' : editingEmployee ? 'Update Employee' : 'Add Employee'}
        </button>
      </form>
    </div>
  );
};

export default EmployeeForm;
