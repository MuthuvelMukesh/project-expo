import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import './HR.css';

/**
 * EmployeeDirectory - Searchable, filterable employee list with details and actions.
 */
const EmployeeDirectory = ({ onEditEmployee, onSuccess }) => {
  const [employees, setEmployees] = useState([]);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [leaveBalances, setLeaveBalances] = useState([]);

  useEffect(() => {
    fetchEmployees();
  }, [typeFilter]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => fetchEmployees(), 300);
    return () => clearTimeout(timer);
  }, [search]);

  const fetchEmployees = async () => {
    try {
      setLoading(true);
      const res = await api.getEmployeeDirectory(search || null, typeFilter || null);
      setEmployees(Array.isArray(res) ? res : []);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectEmployee = async (emp) => {
    setSelectedEmployee(selectedEmployee?.id === emp.id ? null : emp);
    if (selectedEmployee?.id !== emp.id) {
      try {
        const balances = await api.getLeaveBalances(emp.id);
        setLeaveBalances(Array.isArray(balances) ? balances : []);
      } catch {
        setLeaveBalances([]);
      }
    }
  };

  const handleDelete = async (empId) => {
    if (!window.confirm('Are you sure you want to delete this employee record? This action cannot be undone.')) return;
    try {
      await api.deleteEmployee(empId);
      setSuccess('Employee deleted');
      setSelectedEmployee(null);
      fetchEmployees();
      if (onSuccess) onSuccess();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
    }
  };

  const getTypeBadgeColor = (type) => {
    switch (type) {
      case 'faculty': return '#007bff';
      case 'staff': return '#28a745';
      case 'admin': return '#dc3545';
      case 'non_teaching': return '#6f42c1';
      default: return '#6c757d';
    }
  };

  return (
    <div className="employee-directory">
      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      {/* Search & Filters */}
      <div className="directory-controls">
        <div className="search-box">
          <input
            type="text"
            placeholder="🔍 Search by name..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="search-input"
          />
        </div>
        <div className="filter-group">
          <select value={typeFilter} onChange={e => setTypeFilter(e.target.value)}
            className="filter-select">
            <option value="">All Types</option>
            <option value="faculty">Faculty</option>
            <option value="staff">Staff</option>
            <option value="admin">Admin</option>
            <option value="non_teaching">Non-Teaching</option>
          </select>
        </div>
        <div className="directory-count">
          <strong>{employees.length}</strong> employee{employees.length !== 1 ? 's' : ''} found
        </div>
      </div>

      {loading ? (
        <div className="loading">Loading employees...</div>
      ) : (
        <div className="directory-list">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Type</th>
                <th>Phone</th>
                <th>Joined</th>
                <th>Location</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {employees.length > 0 ? employees.map(emp => (
                <React.Fragment key={emp.id}>
                  <tr className={`employee-row ${selectedEmployee?.id === emp.id ? 'selected' : ''}`}
                    onClick={() => handleSelectEmployee(emp)}>
                    <td className="emp-name">{emp.full_name}</td>
                    <td>{emp.email}</td>
                    <td>
                      <span className="type-badge" style={{
                        background: `${getTypeBadgeColor(emp.employee_type)}18`,
                        color: getTypeBadgeColor(emp.employee_type),
                        border: `1px solid ${getTypeBadgeColor(emp.employee_type)}`,
                      }}>
                        {emp.employee_type}
                      </span>
                    </td>
                    <td>{emp.phone || '—'}</td>
                    <td>{emp.date_of_joining || '—'}</td>
                    <td>{[emp.city, emp.state].filter(Boolean).join(', ') || '—'}</td>
                    <td>
                      <button className="btn-small" onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(emp.id);
                      }} style={{ background: '#dc3545' }}>Delete</button>
                    </td>
                  </tr>
                  {/* Expanded Detail */}
                  {selectedEmployee?.id === emp.id && (
                    <tr className="detail-row">
                      <td colSpan="7">
                        <div className="employee-detail-panel">
                          <div className="detail-grid">
                            <div className="detail-item">
                              <span className="detail-label">Employee ID</span>
                              <span className="detail-value">#{emp.id}</span>
                            </div>
                            <div className="detail-item">
                              <span className="detail-label">User ID</span>
                              <span className="detail-value">#{emp.user_id}</span>
                            </div>
                            <div className="detail-item">
                              <span className="detail-label">Full Name</span>
                              <span className="detail-value">{emp.full_name}</span>
                            </div>
                            <div className="detail-item">
                              <span className="detail-label">Phone</span>
                              <span className="detail-value">{emp.phone || 'Not provided'}</span>
                            </div>
                          </div>
                          {leaveBalances.length > 0 && (
                            <div className="leave-balance-inline">
                              <h5>Leave Balances ({new Date().getFullYear()})</h5>
                              <div className="balance-chips">
                                {leaveBalances.map(bal => (
                                  <div key={bal.id} className="balance-chip">
                                    <span className="bal-code">{bal.leave_type_code || bal.leave_type_name}</span>
                                    <span className="bal-nums">
                                      {bal.remaining_days}/{bal.total_days}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              )) : (
                <tr><td colSpan="7" className="text-center">No employees found</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default EmployeeDirectory;
