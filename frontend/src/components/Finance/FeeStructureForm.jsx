import React, { useState } from 'react';
import api from '../../services/api';
import './Finance.css';

/**
 * FeeStructureForm - Admin form to create/edit fee structures
 * Defines what fees students must pay for each semester
 */
const FeeStructureForm = ({ onSuccess }) => {
  const [formData, setFormData] = useState({
    semester: 1,
    fee_type: 'tuition',
    amount: 0,
    valid_from: new Date().toISOString().split('T')[0],
    valid_to: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const feeTypes = ['tuition', 'library', 'sports', 'welfare', 'transportation', 'medical'];
  const semesters = Array.from({ length: 8 }, (_, i) => i + 1);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'amount' || name === 'semester' ? Number(value) : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const payload = {
        ...formData,
        valid_to: formData.valid_to || null,
      };

      await api.post('/api/finance/fee-structures', payload);
      
      setSuccess(true);
      setFormData({
        semester: 1,
        fee_type: 'tuition',
        amount: 0,
        valid_from: new Date().toISOString().split('T')[0],
        valid_to: '',
      });

      if (onSuccess) onSuccess();
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create fee structure');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fee-structure-form">
      <h3>Create Fee Structure</h3>
      
      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">Fee structure created successfully!</div>}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Semester</label>
          <select 
            name="semester" 
            value={formData.semester}
            onChange={handleChange}
            required
          >
            {semesters.map(s => (
              <option key={s} value={s}>Semester {s}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Fee Type</label>
          <select 
            name="fee_type" 
            value={formData.fee_type}
            onChange={handleChange}
            required
          >
            {feeTypes.map(type => (
              <option key={type} value={type}>
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Amount (₹)</label>
          <input 
            type="number" 
            name="amount" 
            value={formData.amount}
            onChange={handleChange}
            placeholder="Enter amount"
            min="0"
            step="0.01"
            required
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Valid From</label>
            <input 
              type="date" 
              name="valid_from" 
              value={formData.valid_from}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label>Valid To (Optional)</label>
            <input 
              type="date" 
              name="valid_to" 
              value={formData.valid_to}
              onChange={handleChange}
            />
          </div>
        </div>

        <button 
          type="submit" 
          className="btn-primary"
          disabled={loading}
        >
          {loading ? 'Creating...' : 'Create Fee Structure'}
        </button>
      </form>
    </div>
  );
};

export default FeeStructureForm;
