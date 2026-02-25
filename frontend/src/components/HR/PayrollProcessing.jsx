import React, { useState } from 'react';
import api from '../../services/api';
import './HR.css';

/**
 * PayrollProcessing - Process monthly payroll for employees
 * Calculates salary and records payroll state
 */
const PayrollProcessing = ({ onSuccess }) => {
  const [formData, setFormData] = useState({
    month: new Date().getMonth() + 1,
    year: new Date().getFullYear(),
    selectedEmployees: [],
  });

  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  React.useEffect(() => {
    fetchEmployees();
  }, []);

  const fetchEmployees = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/hr/employees');
      setEmployees(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load employees');
    } finally {
      setLoading(false);
    }
  };

  const handleEmployeeToggle = (employeeId) => {
    setFormData(prev => ({
      ...prev,
      selectedEmployees: prev.selectedEmployees.includes(employeeId)
        ? prev.selectedEmployees.filter(id => id !== employeeId)
        : [...prev.selectedEmployees, employeeId],
    }));
  };

  const handleSelectAll = () => {
    if (formData.selectedEmployees.length === employees.length) {
      setFormData(prev => ({ ...prev, selectedEmployees: [] }));
    } else {
      setFormData(prev => ({
        ...prev,
        selectedEmployees: employees.map(e => e.id),
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.selectedEmployees.length === 0) {
      setError('Please select atleast one employee');
      return;
    }

    setProcessing(true);
    setError(null);

    try {
      // Process payroll for each selected employee
      for (const employeeId of formData.selectedEmployees) {
        await api.post('/api/hr/salary-records/process', {
          employee_id: employeeId,
          month: formData.month,
          year: formData.year,
        });
      }

      setSuccess(true);
      if (onSuccess) onSuccess();

      setTimeout(() => {
        setSuccess(false);
        setFormData(prev => ({
          ...prev,
          selectedEmployees: [],
        }));
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to process payroll');
    } finally {
      setProcessing(false);
    }
  };

  const months = Array.from({ length: 12 }, (_, i) => ({ value: i + 1, label: new Date(2024, i).toLocaleString('default', { month: 'long' }) }));
  const years = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i);

  return (
    <div className="payroll-processing">
      <h3>Process Monthly Payroll</h3>
      
      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">Payroll processed successfully for {formData.selectedEmployees.length} employee(s)!</div>}

      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <div className="form-group">
            <label>Month</label>
            <select 
              name="month" 
              value={formData.month}
              onChange={(e) => setFormData(prev => ({ ...prev, month: Number(e.target.value) }))}
            >
              {months.map(m => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Year</label>
            <select 
              name="year" 
              value={formData.year}
              onChange={(e) => setFormData(prev => ({ ...prev, year: Number(e.target.value) }))}
            >
              {years.map(y => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="employee-selection">
          <div className="selection-header">
            <input 
              type="checkbox"
              checked={formData.selectedEmployees.length === employees.length && employees.length > 0}
              onChange={handleSelectAll}
              id="select-all"
            />
            <label htmlFor="select-all" onClick={handleSelectAll}>
              Select All ({formData.selectedEmployees.length} of {employees.length})
            </label>
          </div>

          <div className="employee-list">
            {loading ? (
              <p>Loading employees...</p>
            ) : employees.length > 0 ? (
              employees.map(emp => (
                <div key={emp.id} className="employee-item">
                  <input 
                    type="checkbox"
                    checked={formData.selectedEmployees.includes(emp.id)}
                    onChange={() => handleEmployeeToggle(emp.id)}
                    id={`emp-${emp.id}`}
                  />
                  <label htmlFor={`emp-${emp.id}`}>
                    {emp.name || `Employee #${emp.id}`}
                    <span className="type">{emp.employee_type}</span>
                  </label>
                </div>
              ))
            ) : (
              <p>No employees found</p>
            )}
          </div>
        </div>

        <button 
          type="submit" 
          className="btn-primary"
          disabled={processing || formData.selectedEmployees.length === 0}
        >
          {processing ? 'Processing...' : `Process Payroll for ${formData.selectedEmployees.length} Employee(s)`}
        </button>
      </form>
    </div>
  );
};

export default PayrollProcessing;
