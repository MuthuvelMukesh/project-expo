import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import './Finance.css';

/**
 * PaymentForm - Record student fee payments
 * Accepts payment method, amount, and reference number
 */
const PaymentForm = ({ invoiceId, amount, onSuccess }) => {
  const [formData, setFormData] = useState({
    invoice_id: invoiceId,
    amount: amount || 0,
    payment_method: 'bank_transfer',
    reference_number: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const paymentMethods = [
    'bank_transfer',
    'credit_card',
    'debit_card',
    'upi',
    'cheque',
    'cash',
    'online_portal',
  ];

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'amount' ? Number(value) : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/api/finance/payments', formData);
      
      setSuccess(true);
      if (onSuccess) onSuccess(response.data);
      
      setTimeout(() => {
        setSuccess(false);
        setFormData({
          invoice_id: invoiceId,
          amount: amount || 0,
          payment_method: 'bank_transfer',
          reference_number: '',
        });
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to record payment');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="payment-form">
      <h3>Record Payment</h3>
      
      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">Payment recorded successfully!</div>}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Invoice ID</label>
          <input 
            type="number" 
            value={formData.invoice_id}
            disabled
          />
        </div>

        <div className="form-group">
          <label>Amount (₹)</label>
          <input 
            type="number" 
            name="amount" 
            value={formData.amount}
            onChange={handleChange}
            placeholder="Enter payment amount"
            min="0"
            step="0.01"
            required
          />
        </div>

        <div className="form-group">
          <label>Payment Method</label>
          <select 
            name="payment_method" 
            value={formData.payment_method}
            onChange={handleChange}
            required
          >
            {paymentMethods.map(method => (
              <option key={method} value={method}>
                {method.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Reference Number</label>
          <input 
            type="text" 
            name="reference_number" 
            value={formData.reference_number}
            onChange={handleChange}
            placeholder="Bank trasn ID, card txn, UTR, etc."
            required
          />
        </div>

        <button 
          type="submit" 
          className="btn-primary"
          disabled={loading}
        >
          {loading ? 'Processing...' : 'Record Payment'}
        </button>
      </form>
    </div>
  );
};

export default PaymentForm;
