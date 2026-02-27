import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import './HR.css';

/**
 * LeaveManagement - Admin panel for managing leave types, viewing/reviewing leave requests,
 * and managing employee leave balances.
 */
const LeaveManagement = ({ onSuccess }) => {
  const [activeSection, setActiveSection] = useState('requests');
  const [leaveTypes, setLeaveTypes] = useState([]);
  const [leaveRequests, setLeaveRequests] = useState([]);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Leave type form
  const [showTypeForm, setShowTypeForm] = useState(false);
  const [typeForm, setTypeForm] = useState({
    name: '', code: '', max_days_per_year: 12, is_carry_forward: false, description: '',
  });

  // Initialize balance form
  const [showBalanceForm, setShowBalanceForm] = useState(false);
  const [balanceForm, setBalanceForm] = useState({ employee_id: '', year: new Date().getFullYear() });

  useEffect(() => {
    fetchData();
  }, [statusFilter]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [typesRes, requestsRes] = await Promise.all([
        api.getLeaveTypes(),
        api.getLeaveRequests(null, statusFilter || null),
      ]);
      setLeaveTypes(Array.isArray(typesRes) ? typesRes : []);
      setLeaveRequests(Array.isArray(requestsRes) ? requestsRes : []);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to load leave data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateLeaveType = async (e) => {
    e.preventDefault();
    try {
      await api.createLeaveType(typeForm);
      setSuccess('Leave type created successfully');
      setShowTypeForm(false);
      setTypeForm({ name: '', code: '', max_days_per_year: 12, is_carry_forward: false, description: '' });
      fetchData();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleReview = async (requestId, decision) => {
    const comment = decision === 'rejected' ? prompt('Reason for rejection (optional):') : '';
    try {
      await api.reviewLeaveRequest(requestId, {
        status: decision,
        review_comment: comment || null,
      });
      setSuccess(`Leave request ${decision}`);
      fetchData();
      if (onSuccess) onSuccess();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleInitializeBalances = async (e) => {
    e.preventDefault();
    try {
      const res = await api.initializeLeaveBalances(balanceForm.employee_id, balanceForm.year);
      setSuccess(res.detail || 'Leave balances initialized');
      setShowBalanceForm(false);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved': return '#28a745';
      case 'rejected': return '#dc3545';
      case 'cancelled': return '#6c757d';
      default: return '#ffc107';
    }
  };

  if (loading) return <div className="loading">Loading leave management...</div>;

  return (
    <div className="leave-management">
      <div className="section-tabs">
        <button className={`tab-pill ${activeSection === 'requests' ? 'active' : ''}`}
          onClick={() => setActiveSection('requests')}>
          Leave Requests {leaveRequests.filter(r => r.status === 'pending').length > 0 &&
            <span className="badge">{leaveRequests.filter(r => r.status === 'pending').length}</span>}
        </button>
        <button className={`tab-pill ${activeSection === 'types' ? 'active' : ''}`}
          onClick={() => setActiveSection('types')}>
          Leave Types
        </button>
        <button className={`tab-pill ${activeSection === 'balances' ? 'active' : ''}`}
          onClick={() => setActiveSection('balances')}>
          Manage Balances
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      {/* ─── Leave Requests ─── */}
      {activeSection === 'requests' && (
        <div className="leave-requests-section">
          <div className="section-header">
            <h3>Leave Requests</h3>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}
              className="filter-select">
              <option value="">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
          <table>
            <thead>
              <tr>
                <th>Employee</th>
                <th>Leave Type</th>
                <th>From</th>
                <th>To</th>
                <th>Days</th>
                <th>Reason</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {leaveRequests.length > 0 ? leaveRequests.map(req => (
                <tr key={req.id}>
                  <td>{req.employee_name || `Emp #${req.employee_id}`}</td>
                  <td>{req.leave_type_name || `Type #${req.leave_type_id}`}</td>
                  <td>{req.start_date}</td>
                  <td>{req.end_date}</td>
                  <td>{req.num_days}</td>
                  <td className="reason-cell">{req.reason || '—'}</td>
                  <td>
                    <span className="status" style={{
                      background: `${getStatusColor(req.status)}22`,
                      color: getStatusColor(req.status),
                      border: `1px solid ${getStatusColor(req.status)}`,
                    }}>{req.status}</span>
                  </td>
                  <td>
                    {req.status === 'pending' && (
                      <div className="action-group">
                        <button className="btn-small btn-approve"
                          onClick={() => handleReview(req.id, 'approved')}>Approve</button>
                        <button className="btn-small btn-reject"
                          onClick={() => handleReview(req.id, 'rejected')}>Reject</button>
                      </div>
                    )}
                    {req.status !== 'pending' && (
                      <span className="text-muted">—</span>
                    )}
                  </td>
                </tr>
              )) : (
                <tr><td colSpan="8" className="text-center">No leave requests found</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* ─── Leave Types ─── */}
      {activeSection === 'types' && (
        <div className="leave-types-section">
          <div className="section-header">
            <h3>Leave Types</h3>
            <button className="btn-primary" onClick={() => setShowTypeForm(!showTypeForm)}>
              {showTypeForm ? 'Cancel' : '+ Add Leave Type'}
            </button>
          </div>

          {showTypeForm && (
            <form className="inline-form" onSubmit={handleCreateLeaveType}>
              <div className="form-row">
                <div className="form-group">
                  <label>Name</label>
                  <input type="text" value={typeForm.name} required
                    onChange={e => setTypeForm({ ...typeForm, name: e.target.value })}
                    placeholder="e.g., Casual Leave" />
                </div>
                <div className="form-group">
                  <label>Code</label>
                  <input type="text" value={typeForm.code} required maxLength={10}
                    onChange={e => setTypeForm({ ...typeForm, code: e.target.value.toUpperCase() })}
                    placeholder="e.g., CL" />
                </div>
                <div className="form-group">
                  <label>Max Days/Year</label>
                  <input type="number" value={typeForm.max_days_per_year} min={1}
                    onChange={e => setTypeForm({ ...typeForm, max_days_per_year: parseInt(e.target.value) })} />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Description</label>
                  <input type="text" value={typeForm.description}
                    onChange={e => setTypeForm({ ...typeForm, description: e.target.value })}
                    placeholder="Optional description" />
                </div>
                <div className="form-group checkbox-group">
                  <label>
                    <input type="checkbox" checked={typeForm.is_carry_forward}
                      onChange={e => setTypeForm({ ...typeForm, is_carry_forward: e.target.checked })} />
                    Carry Forward
                  </label>
                </div>
              </div>
              <button type="submit" className="btn-primary">Create Leave Type</button>
            </form>
          )}

          <div className="leave-types-grid">
            {leaveTypes.map(lt => (
              <div key={lt.id} className="card leave-type-card">
                <div className="lt-header">
                  <span className="lt-code">{lt.code}</span>
                  <span className={`lt-badge ${lt.is_carry_forward ? 'carry' : ''}`}>
                    {lt.is_carry_forward ? 'Carry Forward' : 'Non-Carry'}
                  </span>
                </div>
                <h4>{lt.name}</h4>
                <p className="lt-days">{lt.max_days_per_year} days/year</p>
                {lt.description && <p className="lt-desc">{lt.description}</p>}
              </div>
            ))}
            {leaveTypes.length === 0 && (
              <p className="text-center">No leave types configured. Add one to get started.</p>
            )}
          </div>
        </div>
      )}

      {/* ─── Manage Balances ─── */}
      {activeSection === 'balances' && (
        <div className="leave-balances-section">
          <div className="section-header">
            <h3>Initialize Leave Balances</h3>
          </div>
          <p className="section-desc">
            Initialize leave balances for an employee for a specific year. This creates entries for all active leave types.
          </p>
          <form className="inline-form" onSubmit={handleInitializeBalances}>
            <div className="form-row">
              <div className="form-group">
                <label>Employee ID</label>
                <input type="number" value={balanceForm.employee_id} required
                  onChange={e => setBalanceForm({ ...balanceForm, employee_id: e.target.value })}
                  placeholder="Employee ID" />
              </div>
              <div className="form-group">
                <label>Year</label>
                <input type="number" value={balanceForm.year}
                  onChange={e => setBalanceForm({ ...balanceForm, year: parseInt(e.target.value) })} />
              </div>
            </div>
            <button type="submit" className="btn-primary">Initialize Balances</button>
          </form>
        </div>
      )}
    </div>
  );
};

export default LeaveManagement;
