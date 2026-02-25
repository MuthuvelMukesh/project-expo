import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import './Finance.css';

/**
 * FinanceDashboard - Main finance overview for admins and students
 * Shows balance, outstanding fees, payment history, and quick actions
 */
const FinanceDashboard = ({ isAdmin }) => {
  const [dashboard, setDashboard] = useState({
    totalBalance: 0,
    outstandingFees: [],
    recentPayments: [],
    loading: true,
    error: null,
  });

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setDashboard(prev => ({ ...prev, loading: true }));
      
      if (isAdmin) {
        const outstandingRes = await api.get('/api/finance/reports/outstanding');
        const collectionRes = await api.get('/api/finance/reports/collection');
        
        setDashboard({
          totalBalance: collectionRes.data.total_outstanding || 0,
          outstandingFees: outstandingRes.data.outstanding_dues || [],
          recentPayments: collectionRes.data.recent_payments || [],
          loading: false,
          error: null,
        });
      } else {
        const balanceRes = await api.get(`/api/finance/student-balance/${getCurrentStudentId()}`);
        setDashboard({
          totalBalance: balanceRes.data.outstanding_balance || 0,
          outstandingFees: balanceRes.data.outstanding_fees || [],
          recentPayments: balanceRes.data.paid_fees || [],
          loading: false,
          error: null,
        });
      }
    } catch (error) {
      setDashboard(prev => ({
        ...prev,
        loading: false,
        error: error.response?.data?.detail || 'Failed to load dashboard',
      }));
    }
  };

  if (dashboard.loading) {
    return <div className="finance-dashboard loading">Loading financial data...</div>;
  }

  return (
    <div className="finance-dashboard">
      <h2>Financial Management</h2>
      
      {dashboard.error && <div className="error-message">{dashboard.error}</div>}

      <div className="dashboard-grid">
        {/* Balance Summary */}
        <div className="card balance-card">
          <h3>Outstanding Balance</h3>
          <div className="balance-amount">
            ₹{dashboard.totalBalance.toFixed(2)}
          </div>
          <p className="balance-label">
            {dashboard.outstandingFees.length} unpaid fees
          </p>
        </div>

        {/* Quick Actions */}
        <div className="card actions-card">
          <h3>Quick Actions</h3>
          <div className="action-buttons">
            {isAdmin ? (
              <>
                <button className="btn-primary">Generate Invoices</button>
                <button className="btn-primary">View Reports</button>
                <button className="btn-secondary">Fee Waivers</button>
              </>
            ) : (
              <>
                <button className="btn-primary">View Invoices</button>
                <button className="btn-primary">Pay Fees</button>
                <button className="btn-secondary">Receipt History</button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Outstanding Fees Table */}
      <div className="card fees-table">
        <h3>Outstanding Fees</h3>
        <table>
          <thead>
            <tr>
              <th>Student ID</th>
              <th>Fee Type</th>
              <th>Amount</th>
              <th>Due Date</th>
              <th>Days Overdue</th>
            </tr>
          </thead>
          <tbody>
            {dashboard.outstandingFees.length > 0 ? (
              dashboard.outstandingFees.map((fee, idx) => (
                <tr key={idx}>
                  <td>{fee.student_id}</td>
                  <td>{fee.fee_type}</td>
                  <td>₹{fee.amount.toFixed(2)}</td>
                  <td>{new Date(fee.due_date).toLocaleDateString()}</td>
                  <td className={fee.days_overdue > 0 ? 'overdue' : ''}>
                    {fee.days_overdue > 0 ? `${fee.days_overdue} days` : 'On time'}
                  </td>
                </tr>
              ))
            ) : (
              <tr><td colSpan="5" className="text-center">No outstanding fees</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Recent Payments */}
      <div className="card payments-table">
        <h3>Recent Payments</h3>
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Amount</th>
              <th>Method</th>
              <th>Reference</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {dashboard.recentPayments.length > 0 ? (
              dashboard.recentPayments.map((payment, idx) => (
                <tr key={idx}>
                  <td>{new Date(payment.payment_date).toLocaleDateString()}</td>
                  <td>₹{payment.amount.toFixed(2)}</td>
                  <td>{payment.payment_method}</td>
                  <td>{payment.reference_number}</td>
                  <td><span className={`status ${payment.status}`}>{payment.status}</span></td>
                </tr>
              ))
            ) : (
              <tr><td colSpan="5" className="text-center">No recent payments</td></tr>
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

// Helper function - get current student ID from context/session
const getCurrentStudentId = () => {
  // This would typically come from AuthContext or session
  return localStorage.getItem('currentStudentId') || 1;
};

export default FinanceDashboard;
