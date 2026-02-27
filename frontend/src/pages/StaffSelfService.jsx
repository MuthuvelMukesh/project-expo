import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import '../components/HR/HR.css';

/**
 * StaffSelfService - Self-service portal for employees (non-admin) to view
 * their profile, salary slips, attendance, leave balances, and apply for leave.
 */
const StaffSelfService = () => {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [salaryRecords, setSalaryRecords] = useState([]);
  const [leaveRequests, setLeaveRequests] = useState([]);
  const [leaveTypes, setLeaveTypes] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Leave request form
  const [showLeaveForm, setShowLeaveForm] = useState(false);
  const [leaveForm, setLeaveForm] = useState({
    leave_type_id: '',
    start_date: '',
    end_date: '',
    reason: '',
  });

  useEffect(() => {
    fetchProfile();
    fetchLeaveTypes();
    fetchMyLeaveRequests();
  }, []);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const res = await api.getMyEmployeeProfile();
      setProfile(res);

      // Also fetch salary records if employee exists
      if (res?.employee?.id) {
        const salRes = await api.getSalaryRecords(res.employee.id);
        setSalaryRecords(Array.isArray(salRes) ? salRes : []);
      }
    } catch (err) {
      setError(err.message || 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const fetchLeaveTypes = async () => {
    try {
      const res = await api.getLeaveTypes();
      setLeaveTypes(Array.isArray(res) ? res : []);
    } catch { /* ignore */ }
  };

  const fetchMyLeaveRequests = async () => {
    try {
      const res = await api.getLeaveRequests();
      setLeaveRequests(Array.isArray(res) ? res : []);
    } catch { /* ignore */ }
  };

  const handleApplyLeave = async (e) => {
    e.preventDefault();
    try {
      await api.createLeaveRequest(leaveForm);
      setSuccess('Leave request submitted successfully!');
      setShowLeaveForm(false);
      setLeaveForm({ leave_type_id: '', start_date: '', end_date: '', reason: '' });
      fetchMyLeaveRequests();
      fetchProfile();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
      setTimeout(() => setError(null), 5000);
    }
  };

  const handleCancelLeave = async (requestId) => {
    if (!window.confirm('Cancel this leave request?')) return;
    try {
      await api.cancelLeaveRequest(requestId);
      setSuccess('Leave request cancelled');
      fetchMyLeaveRequests();
      fetchProfile();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved': case 'paid': return '#28a745';
      case 'rejected': case 'failed': return '#dc3545';
      case 'cancelled': return '#6c757d';
      case 'processed': return '#17a2b8';
      default: return '#ffc107';
    }
  };

  if (loading) {
    return (
      <div className="staff-self-service">
        <div className="loading">Loading your profile...</div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="staff-self-service">
        <div className="card text-center" style={{ padding: '40px' }}>
          <h2>No Employee Record Found</h2>
          <p>Your user account is not linked to an employee record. Please contact HR administration.</p>
        </div>
      </div>
    );
  }

  const emp = profile.employee;
  const salary = profile.latest_salary;
  const attendance = profile.attendance_this_month;
  const balances = profile.leave_balances || [];

  return (
    <div className="staff-self-service">
      <div className="page-header">
        <h1>My Portal</h1>
        <p className="subtitle">Welcome, {emp.full_name}</p>
      </div>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      {/* Tab Navigation */}
      <div className="tab-navigation">
        {['overview', 'salary', 'leave', 'attendance'].map(tab => (
          <button key={tab}
            className={`tab-btn ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}>
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      <div className="tab-content">
        {/* ─── Overview ─── */}
        {activeTab === 'overview' && (
          <div className="overview-section">
            <div className="dashboard-grid">
              {/* Profile Card */}
              <div className="card" style={{ borderLeftColor: '#007bff' }}>
                <h3>My Profile</h3>
                <div className="profile-info">
                  <div className="info-row"><span>Name:</span><strong>{emp.full_name}</strong></div>
                  <div className="info-row"><span>Email:</span><strong>{emp.email}</strong></div>
                  <div className="info-row"><span>Type:</span><strong>{emp.employee_type}</strong></div>
                  <div className="info-row"><span>Phone:</span><strong>{emp.phone || '—'}</strong></div>
                  <div className="info-row"><span>Joined:</span><strong>{emp.date_of_joining || '—'}</strong></div>
                </div>
              </div>

              {/* Salary Card */}
              <div className="card" style={{ borderLeftColor: '#28a745' }}>
                <h3>Latest Salary</h3>
                {salary?.month ? (
                  <div className="profile-info">
                    <div className="info-row"><span>Period:</span><strong>{salary.month}/{salary.year}</strong></div>
                    <div className="info-row">
                      <span>Net Salary:</span>
                      <strong style={{ color: '#28a745', fontSize: '18px' }}>₹{salary.net_salary?.toFixed(2)}</strong>
                    </div>
                    <div className="info-row">
                      <span>Status:</span>
                      <span className="status" style={{
                        background: `${getStatusColor(salary.status)}22`,
                        color: getStatusColor(salary.status),
                      }}>{salary.status}</span>
                    </div>
                  </div>
                ) : (
                  <p className="text-center">No salary records yet</p>
                )}
              </div>

              {/* Attendance Card */}
              <div className="card" style={{ borderLeftColor: '#17a2b8' }}>
                <h3>This Month's Attendance</h3>
                <div className="profile-info">
                  <div className="info-row"><span>Days Recorded:</span><strong>{attendance?.total_days || 0}</strong></div>
                  <div className="info-row"><span>Present:</span><strong style={{ color: '#28a745' }}>{attendance?.present || 0}</strong></div>
                  <div className="info-row"><span>Absent:</span><strong style={{ color: '#dc3545' }}>{attendance?.absent || 0}</strong></div>
                </div>
              </div>
            </div>

            {/* Leave Balances */}
            {balances.length > 0 && (
              <div className="card" style={{ marginTop: '20px' }}>
                <h3>Leave Balances ({new Date().getFullYear()})</h3>
                <div className="leave-balance-cards">
                  {balances.map((bal, idx) => (
                    <div key={idx} className="balance-card-item">
                      <div className="bal-header">{bal.leave_type} ({bal.code})</div>
                      <div className="bal-bar">
                        <div className="bal-fill"
                          style={{ width: `${(bal.remaining / bal.total) * 100}%` }} />
                      </div>
                      <div className="bal-numbers">
                        <span>{bal.remaining} remaining</span>
                        <span>of {bal.total}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ─── Salary History ─── */}
        {activeTab === 'salary' && (
          <div className="card">
            <h3>Salary History</h3>
            <table>
              <thead>
                <tr>
                  <th>Month/Year</th>
                  <th>Gross Salary</th>
                  <th>Deductions</th>
                  <th>Net Salary</th>
                  <th>Status</th>
                  <th>Payment Date</th>
                </tr>
              </thead>
              <tbody>
                {salaryRecords.length > 0 ? salaryRecords.map(rec => (
                  <tr key={rec.id}>
                    <td>{rec.month}/{rec.year}</td>
                    <td>₹{rec.gross_salary?.toFixed(2)}</td>
                    <td>₹{rec.deductions?.toFixed(2)}</td>
                    <td className="highlight">₹{rec.net_salary?.toFixed(2)}</td>
                    <td>
                      <span className="status" style={{
                        background: `${getStatusColor(rec.status)}22`,
                        color: getStatusColor(rec.status),
                      }}>{rec.status}</span>
                    </td>
                    <td>{rec.payment_date || '—'}</td>
                  </tr>
                )) : (
                  <tr><td colSpan="6" className="text-center">No salary records</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* ─── Leave ─── */}
        {activeTab === 'leave' && (
          <div className="leave-section">
            <div className="section-header" style={{ marginBottom: '15px' }}>
              <h3>My Leave Requests</h3>
              <button className="btn-primary" onClick={() => setShowLeaveForm(!showLeaveForm)}>
                {showLeaveForm ? 'Cancel' : '+ Apply for Leave'}
              </button>
            </div>

            {showLeaveForm && (
              <form className="card inline-form" onSubmit={handleApplyLeave} style={{ marginBottom: '20px' }}>
                <h4>New Leave Request</h4>
                <div className="form-row">
                  <div className="form-group">
                    <label>Leave Type</label>
                    <select value={leaveForm.leave_type_id} required
                      onChange={e => setLeaveForm({ ...leaveForm, leave_type_id: parseInt(e.target.value) })}>
                      <option value="">Select Type</option>
                      {leaveTypes.map(lt => (
                        <option key={lt.id} value={lt.id}>{lt.name} ({lt.code})</option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>From</label>
                    <input type="date" value={leaveForm.start_date} required
                      onChange={e => setLeaveForm({ ...leaveForm, start_date: e.target.value })} />
                  </div>
                  <div className="form-group">
                    <label>To</label>
                    <input type="date" value={leaveForm.end_date} required
                      onChange={e => setLeaveForm({ ...leaveForm, end_date: e.target.value })} />
                  </div>
                </div>
                <div className="form-group">
                  <label>Reason</label>
                  <textarea value={leaveForm.reason}
                    onChange={e => setLeaveForm({ ...leaveForm, reason: e.target.value })}
                    placeholder="Reason for leave (optional)" rows={2} />
                </div>
                <button type="submit" className="btn-primary">Submit Request</button>
              </form>
            )}

            {/* Leave Balances */}
            {balances.length > 0 && (
              <div className="leave-balance-cards" style={{ marginBottom: '20px' }}>
                {balances.map((bal, idx) => (
                  <div key={idx} className="balance-card-item">
                    <div className="bal-header">{bal.leave_type} ({bal.code})</div>
                    <div className="bal-numbers">
                      <span className="highlight" style={{ fontSize: '24px' }}>{bal.remaining}</span>
                      <span> / {bal.total} days remaining</span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Leave Request History */}
            <div className="card">
              <table>
                <thead>
                  <tr>
                    <th>Leave Type</th>
                    <th>From</th>
                    <th>To</th>
                    <th>Days</th>
                    <th>Status</th>
                    <th>Comment</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {leaveRequests.length > 0 ? leaveRequests.map(req => (
                    <tr key={req.id}>
                      <td>{req.leave_type_name || `Type #${req.leave_type_id}`}</td>
                      <td>{req.start_date}</td>
                      <td>{req.end_date}</td>
                      <td>{req.num_days}</td>
                      <td>
                        <span className="status" style={{
                          background: `${getStatusColor(req.status)}22`,
                          color: getStatusColor(req.status),
                          border: `1px solid ${getStatusColor(req.status)}`,
                        }}>{req.status}</span>
                      </td>
                      <td>{req.review_comment || '—'}</td>
                      <td>
                        {(req.status === 'pending' || req.status === 'approved') && (
                          <button className="btn-small" style={{ background: '#dc3545' }}
                            onClick={() => handleCancelLeave(req.id)}>Cancel</button>
                        )}
                      </td>
                    </tr>
                  )) : (
                    <tr><td colSpan="7" className="text-center">No leave requests</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ─── Attendance ─── */}
        {activeTab === 'attendance' && (
          <div className="card">
            <h3>My Attendance</h3>
            <p className="text-center" style={{ padding: '20px' }}>
              Attendance records are managed by HR. Contact administration for attendance queries.
            </p>
            {attendance && (
              <div className="dashboard-grid">
                <div className="card summary-card" style={{ borderLeftColor: '#28a745' }}>
                  <h4>Present This Month</h4>
                  <div className="metric">
                    <span className="metric-value" style={{ color: '#28a745' }}>{attendance.present}</span>
                  </div>
                </div>
                <div className="card summary-card" style={{ borderLeftColor: '#dc3545' }}>
                  <h4>Absent This Month</h4>
                  <div className="metric">
                    <span className="metric-value" style={{ color: '#dc3545' }}>{attendance.absent}</span>
                  </div>
                </div>
                <div className="card summary-card">
                  <h4>Total Recorded Days</h4>
                  <div className="metric">
                    <span className="metric-value">{attendance.total_days}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default StaffSelfService;
