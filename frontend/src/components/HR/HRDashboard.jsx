import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import './HR.css';

/**
 * HRDashboard - Main HR and payroll management dashboard
 * Shows employee count, payroll status, salary reports
 */
const HRDashboard = ({ isAdmin }) => {
  const [dashboard, setDashboard] = useState({
    totalEmployees: 0,
    thisMonthPayroll: {},
    pendingPayrolls: [],
    recentSalarySlips: [],
    loading: true,
    error: null,
  });

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setDashboard(prev => ({ ...prev, loading: true }));
      
      const now = new Date();
      const month = now.getMonth() + 1;
      const year = now.getFullYear();

      const payrollRes = await api.get(`/api/hr/reports/payroll-summary?month=${month}&year=${year}`);
      
      setDashboard({
        totalEmployees: payrollRes.data.total_employees || 0,
        thisMonthPayroll: payrollRes.data || {},
        pendingPayrolls: payrollRes.data.pending_records || [],
        recentSalarySlips: payrollRes.data.recent_slips || [],
        loading: false,
        error: null,
      });
    } catch (error) {
      setDashboard(prev => ({
        ...prev,
        loading: false,
        error: error.response?.data?.detail || 'Failed to load HR dashboard',
      }));
    }
  };

  if (dashboard.loading) {
    return <div className="hr-dashboard loading">Loading HR data...</div>;
  }

  return (
    <div className="hr-dashboard">
      <h2>HR & Payroll Management</h2>
      
      {dashboard.error && <div className="error-message">{dashboard.error}</div>}

      <div className="dashboard-grid">
        {/* Employee Summary */}
        <div className="card summary-card">
          <h3>Employee Summary</h3>
          <div className="metric">
            <span className="metric-value">{dashboard.totalEmployees}</span>
            <span className="metric-label">Total Employees</span>
          </div>
        </div>

        {/* Current Month Payroll */}
        <div className="card payroll-card">
          <h3>This Month's Payroll</h3>
          <div className="payroll-stats">
            <div className="stat">
              <span className="label">Total Gross</span>
              <span className="value">₹{(dashboard.thisMonthPayroll.total_gross || 0).toFixed(2)}</span>
            </div>
            <div className="stat">
              <span className="label">Total Deductions</span>
              <span className="value">₹{(dashboard.thisMonthPayroll.total_deductions || 0).toFixed(2)}</span>
            </div>
            <div className="stat">
              <span className="label">Net Payroll</span>
              <span className="value">₹{(dashboard.thisMonthPayroll.total_net || 0).toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="card actions-card">
          <h3>Quick Actions</h3>
          <div className="action-buttons">
            <button className="btn-primary">Add Employee</button>
            <button className="btn-primary">Process Payroll</button>
            <button className="btn-secondary">View Reports</button>
          </div>
        </div>
      </div>

      {/* Pending Payroll Records */}
      <div className="card pending-table">
        <h3>Pending Payroll Processing</h3>
        <table>
          <thead>
            <tr>
              <th>Employee ID</th>
              <th>Month</th>
              <th>Year</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {dashboard.pendingPayrolls.length > 0 ? (
              dashboard.pendingPayrolls.map((record, idx) => (
                <tr key={idx}>
                  <td>{record.employee_id}</td>
                  <td>{record.month}</td>
                  <td>{record.year}</td>
                  <td><span className={`status ${record.status}`}>{record.status}</span></td>
                  <td><button className="btn-small">Process</button></td>
                </tr>
              ))
            ) : (
              <tr><td colSpan="5" className="text-center">All payrolls processed</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Recent Salary Slips */}
      <div className="card slips-table">
        <h3>Recent Salary Slips</h3>
        <table>
          <thead>
            <tr>
              <th>Employee</th>
              <th>Month</th>
              <th>Gross Salary</th>
              <th>Deductions</th>
              <th>Net Salary</th>
              <th>View</th>
            </tr>
          </thead>
          <tbody>
            {dashboard.recentSalarySlips.length > 0 ? (
              dashboard.recentSalarySlips.map((slip, idx) => (
                <tr key={idx}>
                  <td>{slip.employee_name}</td>
                  <td>{slip.month}/{slip.year}</td>
                  <td>₹{slip.gross_salary.toFixed(2)}</td>
                  <td>₹{slip.deductions.toFixed(2)}</td>
                  <td className="highlight">₹{slip.net_salary.toFixed(2)}</td>
                  <td><button className="btn-small">View Slip</button></td>
                </tr>
              ))
            ) : (
              <tr><td colSpan="6" className="text-center">No salary slips available</td></tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="dashboard-actions">
        <button className="btn-secondary" onClick={fetchDashboardData}>Refresh</button>
      </div>
    </div>
  );
};

export default HRDashboard;
