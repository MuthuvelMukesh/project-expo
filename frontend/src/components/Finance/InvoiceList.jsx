import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import './Finance.css';

/**
 * InvoiceList - Display and manage student invoices
 * Admin can view all invoices, students can view their own
 */
const InvoiceList = ({ studentId = null, isAdmin = false }) => {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all'); // all, pending, paid, overdue

  useEffect(() => {
    fetchInvoices();
  }, [filter]);

  const fetchInvoices = async () => {
    try {
      setLoading(true);
      setError(null);

      let url = '/api/finance/invoices';
      if (studentId && !isAdmin) {
        url = `/api/finance/invoices/student/${studentId}`;
      }

      const response = await api.get(url);
      
      let filtered = Array.isArray(response) ? response : [];
      
      if (filter !== 'all') {
        filtered = filtered.filter(inv => {
          if (filter === 'pending') return inv.status === 'draft' || inv.status === 'issued';
          if (filter === 'paid') return inv.status === 'paid';
          if (filter === 'overdue') return new Date(inv.due_date) < new Date() && inv.status !== 'paid';
          return true;
        });
      }

      setInvoices(filtered);
    } catch (err) {
      setError(err.message || 'Failed to load invoices');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateInvoices = async () => {
    if (!isAdmin) return;
    
    try {
      await api.post('/api/finance/invoices/generate', {});
      fetchInvoices();
    } catch (err) {
      alert(err.message || 'Failed to generate invoices');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'paid': return 'success';
      case 'draft': return 'info';
      case 'issued': return 'warning';
      case 'overdue': return 'danger';
      default: return 'secondary';
    }
  };

  if (loading) {
    return <div className="invoice-list loading">Loading invoices...</div>;
  }

  return (
    <div className="invoice-list">
      <h3>Invoices</h3>
      
      {error && <div className="error-message">{error}</div>}

      <div className="controls">
        <div className="filter-buttons">
          <button 
            className={`btn-filter ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All
          </button>
          <button 
            className={`btn-filter ${filter === 'pending' ? 'active' : ''}`}
            onClick={() => setFilter('pending')}
          >
            Pending
          </button>
          <button 
            className={`btn-filter ${filter === 'paid' ? 'active' : ''}`}
            onClick={() => setFilter('paid')}
          >
            Paid
          </button>
          <button 
            className={`btn-filter ${filter === 'overdue' ? 'active' : ''}`}
            onClick={() => setFilter('overdue')}
          >
            Overdue
          </button>
        </div>

        {isAdmin && (
          <button className="btn-primary" onClick={handleGenerateInvoices}>
            Generate Invoices
          </button>
        )}
      </div>

      <table className="invoice-table">
        <thead>
          <tr>
            <th>Invoice #</th>
            <th>Student</th>
            <th>Amount</th>
            <th>Issued Date</th>
            <th>Due Date</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {invoices.length > 0 ? (
            invoices.map(invoice => (
              <tr key={invoice.id}>
                <td className="invoice-number">{invoice.invoice_number}</td>
                <td>{invoice.student_id}</td>
                <td className="amount">₹{invoice.amount_due.toFixed(2)}</td>
                <td>{new Date(invoice.issued_date).toLocaleDateString()}</td>
                <td>{new Date(invoice.due_date).toLocaleDateString()}</td>
                <td>
                  <span className={`badge status-${getStatusColor(invoice.status)}`}>
                    {invoice.status}
                  </span>
                </td>
                <td>
                  <button className="btn-small">View</button>
                  {!['paid', 'cancelled'].includes(invoice.status) && (
                    <button className="btn-small btn-info">Pay</button>
                  )}
                </td>
              </tr>
            ))
          ) : (
            <tr><td colSpan="7" className="text-center">No invoices found</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

export default InvoiceList;
