import React, { useState } from 'react';
import api from '../../services/api';
import './HR.css';

/**
 * SalaryStructureForm - Define salary components for an employee
 * Includes base salary, allowances, deductions, and tax
 */
const SalaryStructureForm = ({ employeeId, onSuccess }) => {
  const [formData, setFormData] = useState({
    employee_id: employeeId,
    designation: '',
    base_salary: 0,
    da: 0,
    hra: 0,
    other_allowances: 0,
    pf_contribution: 0,
    insurance: 0,
    tax_rate: 0,
    effective_from: new Date().toISOString().split('T')[0],
    effective_to: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const designations = [
    'Professor',
    'Associate Professor',
    'Assistant Professor',
    'Lecturer',
    'Demonstrator',
    'Clerk',
    'Peon',
    'Security Guard',
    'Canteen Staff',
    'Other',
  ];

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: ['base_salary', 'da', 'hra', 'other_allowances', 'pf_contribution', 'insurance', 'tax_rate'].includes(name) 
        ? Number(value) 
        : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await api.post('/api/hr/salary-structures', formData);
      
      setSuccess(true);
      if (onSuccess) onSuccess();
      
      setTimeout(() => setSuccess(false), 2000);
    } catch (err) {
      setError(err.message || 'Failed to create salary structure');
    } finally {
      setLoading(false);
    }
  };

  // Calculate gross for preview
  const grossSalary = formData.base_salary + formData.da + formData.hra + formData.other_allowances;
  const totalDeductions = formData.pf_contribution + formData.insurance + (grossSalary * formData.tax_rate / 100);
  const netSalary = grossSalary - totalDeductions;

  return (
    <div className="salary-structure-form">
      <h3>Define Salary Structure</h3>
      
      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">Salary structure created successfully!</div>}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Designation</label>
          <select 
            name="designation" 
            value={formData.designation}
            onChange={handleChange}
            required
          >
            <option value="">Select Designation</option>
            {designations.map(des => (
              <option key={des} value={des}>{des}</option>
            ))}
          </select>
        </div>

        <div className="form-section">
          <h4>Earnings</h4>
          
          <div className="form-row">
            <div className="form-group">
              <label>Base Salary (₹)</label>
              <input 
                type="number" 
                name="base_salary" 
                value={formData.base_salary}
                onChange={handleChange}
                min="0"
                step="100"
                required
              />
            </div>

            <div className="form-group">
              <label>DA - Dearness Allowance (₹)</label>
              <input 
                type="number" 
                name="da" 
                value={formData.da}
                onChange={handleChange}
                min="0"
                step="100"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>HRA - House Rent Allowance (₹)</label>
              <input 
                type="number" 
                name="hra" 
                value={formData.hra}
                onChange={handleChange}
                min="0"
                step="100"
              />
            </div>

            <div className="form-group">
              <label>Other Allowances (₹)</label>
              <input 
                type="number" 
                name="other_allowances" 
                value={formData.other_allowances}
                onChange={handleChange}
                min="0"
                step="100"
              />
            </div>
          </div>
        </div>

        <div className="form-section">
          <h4>Deductions</h4>
          
          <div className="form-row">
            <div className="form-group">
              <label>PF Contribution (₹)</label>
              <input 
                type="number" 
                name="pf_contribution" 
                value={formData.pf_contribution}
                onChange={handleChange}
                min="0"
                step="100"
              />
            </div>

            <div className="form-group">
              <label>Insurance (₹)</label>
              <input 
                type="number" 
                name="insurance" 
                value={formData.insurance}
                onChange={handleChange}
                min="0"
                step="100"
              />
            </div>
          </div>

          <div className="form-group">
            <label>Tax Rate (%)</label>
            <input 
              type="number" 
              name="tax_rate" 
              value={formData.tax_rate}
              onChange={handleChange}
              min="0"
              max="100"
              step="0.5"
            />
          </div>
        </div>

        <div className="form-section">
          <h4>Calculation Preview</h4>
          <div className="calculation-box">
            <div className="calc-row">
              <span>Gross Salary:</span>
              <strong>₹{grossSalary.toFixed(2)}</strong>
            </div>
            <div className="calc-row">
              <span>Total Deductions:</span>
              <strong>₹{totalDeductions.toFixed(2)}</strong>
            </div>
            <div className="calc-row highlight">
              <span>Net Salary:</span>
              <strong>₹{netSalary.toFixed(2)}</strong>
            </div>
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Effective From</label>
            <input 
              type="date" 
              name="effective_from" 
              value={formData.effective_from}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label>Effective To (Optional)</label>
            <input 
              type="date" 
              name="effective_to" 
              value={formData.effective_to}
              onChange={handleChange}
            />
          </div>
        </div>

        <button 
          type="submit" 
          className="btn-primary"
          disabled={loading}
        >
          {loading ? 'Creating...' : 'Create Salary Structure'}
        </button>
      </form>
    </div>
  );
};

export default SalaryStructureForm;
