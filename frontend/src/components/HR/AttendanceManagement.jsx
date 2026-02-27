import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import './HR.css';

/**
 * AttendanceManagement - Record and view employee attendance with summary stats.
 */
const AttendanceManagement = ({ onSuccess }) => {
  const [employees, setEmployees] = useState([]);
  const [selectedEmployee, setSelectedEmployee] = useState('');
  const [attendanceRecords, setAttendanceRecords] = useState([]);
  const [summary, setSummary] = useState(null);
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Record form
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    employee_id: '',
    date: new Date().toISOString().split('T')[0],
    check_in: '09:00',
    check_out: '17:00',
    status: 'present',
  });

  useEffect(() => {
    fetchEmployees();
  }, []);

  useEffect(() => {
    if (selectedEmployee) {
      fetchAttendance();
      fetchSummary();
    }
  }, [selectedEmployee, month, year]);

  const fetchEmployees = async () => {
    try {
      const res = await api.getEmployeeDirectory();
      setEmployees(Array.isArray(res) ? res : []);
    } catch (err) {
      setError(err.message);
    }
  };

  const fetchAttendance = async () => {
    try {
      setLoading(true);
      const res = await api.getEmployeeAttendance(selectedEmployee, month, year);
      setAttendanceRecords(Array.isArray(res) ? res : []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchSummary = async () => {
    try {
      const res = await api.getAttendanceSummary(selectedEmployee, month, year);
      setSummary(res);
    } catch {
      setSummary(null);
    }
  };

  const handleRecordAttendance = async (e) => {
    e.preventDefault();
    try {
      // Calculate hours from check_in / check_out
      let hours = null;
      if (form.check_in && form.check_out) {
        const [inH, inM] = form.check_in.split(':').map(Number);
        const [outH, outM] = form.check_out.split(':').map(Number);
        hours = Math.max(0, (outH + outM / 60) - (inH + inM / 60));
      }

      await api.recordEmployeeAttendance({
        ...form,
        employee_id: parseInt(form.employee_id),
        hours_worked: hours ? parseFloat(hours.toFixed(2)) : null,
      });

      setSuccess('Attendance recorded successfully');
      setShowForm(false);
      if (form.employee_id == selectedEmployee) {
        fetchAttendance();
        fetchSummary();
      }
      if (onSuccess) onSuccess();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
      setTimeout(() => setError(null), 5000);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'present': return '✅';
      case 'absent': return '❌';
      case 'halfday': return '🕐';
      case 'leave': return '🏖️';
      default: return '—';
    }
  };

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
  ];

  return (
    <div className="attendance-management">
      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      {/* Controls */}
      <div className="attendance-controls">
        <div className="control-row">
          <div className="form-group">
            <label>Employee</label>
            <select value={selectedEmployee} onChange={e => setSelectedEmployee(e.target.value)}>
              <option value="">Select Employee</option>
              {employees.map(emp => (
                <option key={emp.id} value={emp.id}>
                  {emp.full_name} ({emp.employee_type})
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Month</label>
            <select value={month} onChange={e => setMonth(parseInt(e.target.value))}>
              {monthNames.map((name, idx) => (
                <option key={idx} value={idx + 1}>{name}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Year</label>
            <input type="number" value={year} min={2020} max={2030}
              onChange={e => setYear(parseInt(e.target.value))} />
          </div>
          <button className="btn-primary" onClick={() => setShowForm(!showForm)}
            style={{ alignSelf: 'flex-end' }}>
            {showForm ? 'Cancel' : '+ Record Attendance'}
          </button>
        </div>
      </div>

      {/* Record Form */}
      {showForm && (
        <form className="inline-form card" onSubmit={handleRecordAttendance}>
          <h4>Record Attendance</h4>
          <div className="form-row">
            <div className="form-group">
              <label>Employee</label>
              <select value={form.employee_id} required
                onChange={e => setForm({ ...form, employee_id: e.target.value })}>
                <option value="">Select</option>
                {employees.map(emp => (
                  <option key={emp.id} value={emp.id}>{emp.full_name}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Date</label>
              <input type="date" value={form.date} required
                onChange={e => setForm({ ...form, date: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Status</label>
              <select value={form.status}
                onChange={e => setForm({ ...form, status: e.target.value })}>
                <option value="present">Present</option>
                <option value="absent">Absent</option>
                <option value="halfday">Half Day</option>
                <option value="leave">Leave</option>
              </select>
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Check In</label>
              <input type="time" value={form.check_in}
                onChange={e => setForm({ ...form, check_in: e.target.value })} />
            </div>
            <div className="form-group">
              <label>Check Out</label>
              <input type="time" value={form.check_out}
                onChange={e => setForm({ ...form, check_out: e.target.value })} />
            </div>
          </div>
          <button type="submit" className="btn-primary">Save Attendance</button>
        </form>
      )}

      {/* Summary Cards */}
      {summary && (
        <div className="dashboard-grid attendance-summary-grid">
          <div className="card summary-card">
            <h4>Total Working Days</h4>
            <div className="metric">
              <span className="metric-value">{summary.total_days}</span>
            </div>
          </div>
          <div className="card summary-card" style={{ borderLeftColor: '#28a745' }}>
            <h4>Present</h4>
            <div className="metric">
              <span className="metric-value" style={{ color: '#28a745' }}>{summary.present}</span>
            </div>
          </div>
          <div className="card summary-card" style={{ borderLeftColor: '#dc3545' }}>
            <h4>Absent</h4>
            <div className="metric">
              <span className="metric-value" style={{ color: '#dc3545' }}>{summary.absent}</span>
            </div>
          </div>
          <div className="card summary-card" style={{ borderLeftColor: '#ffc107' }}>
            <h4>Half Day</h4>
            <div className="metric">
              <span className="metric-value" style={{ color: '#856404' }}>{summary.halfday}</span>
            </div>
          </div>
          <div className="card summary-card" style={{ borderLeftColor: '#17a2b8' }}>
            <h4>On Leave</h4>
            <div className="metric">
              <span className="metric-value" style={{ color: '#17a2b8' }}>{summary.leave}</span>
            </div>
          </div>
          <div className="card summary-card" style={{ borderLeftColor: '#6f42c1' }}>
            <h4>Total Hours</h4>
            <div className="metric">
              <span className="metric-value" style={{ color: '#6f42c1' }}>{summary.total_hours.toFixed(1)}</span>
            </div>
          </div>
        </div>
      )}

      {/* Attendance Records Table */}
      {selectedEmployee ? (
        <div className="card">
          <h3>Attendance Records — {monthNames[month - 1]} {year}</h3>
          {loading ? (
            <div className="loading">Loading...</div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Status</th>
                  <th>Check In</th>
                  <th>Check Out</th>
                  <th>Hours</th>
                </tr>
              </thead>
              <tbody>
                {attendanceRecords.length > 0 ? attendanceRecords.map(rec => (
                  <tr key={rec.id}>
                    <td>{rec.date}</td>
                    <td>
                      {getStatusIcon(rec.status)}{' '}
                      <span className={`status ${rec.status}`}>{rec.status}</span>
                    </td>
                    <td>{rec.check_in || '—'}</td>
                    <td>{rec.check_out || '—'}</td>
                    <td>{rec.hours_worked ? rec.hours_worked.toFixed(1) + 'h' : '—'}</td>
                  </tr>
                )) : (
                  <tr><td colSpan="5" className="text-center">No attendance records for this period</td></tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      ) : (
        <div className="card text-center" style={{ padding: '40px' }}>
          <p>Select an employee to view attendance records</p>
        </div>
      )}
    </div>
  );
};

export default AttendanceManagement;
