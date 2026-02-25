import React, { useState } from 'react';
import FinanceDashboard from '../components/Finance/FinanceDashboard';
import FeeStructureForm from '../components/Finance/FeeStructureForm';
import PaymentForm from '../components/Finance/PaymentForm';
import InvoiceList from '../components/Finance/InvoiceList';
import { useAuth } from '../context/AuthContext';
import '../pages/ManagementPages.css';

/**
 * FinanceManagement - Main Finance page with dashboard and management forms
 */
const FinanceManagement = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [activeTab, setActiveTab] = useState('dashboard');
  const [refreshKey, setRefreshKey] = useState(0);

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
  };

  return (
    <div className="finance-management-page">
      <div className="page-header">
        <h1>Financial Management</h1>
        <p className="subtitle">
          {isAdmin ? 'Manage fees, invoices, and payments for all students' : 'View your fees and payment history'}
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="tab-navigation">
        <button 
          className={`tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          Dashboard
        </button>
        <button 
          className={`tab-btn ${activeTab === 'invoices' ? 'active' : ''}`}
          onClick={() => setActiveTab('invoices')}
        >
          Invoices
        </button>
        {isAdmin && (
          <button 
            className={`tab-btn ${activeTab === 'fees' ? 'active' : ''}`}
            onClick={() => setActiveTab('fees')}
          >
            Fee Structures
          </button>
        )}
        {isAdmin && (
          <button 
            className={`tab-btn ${activeTab === 'payments' ? 'active' : ''}`}
            onClick={() => setActiveTab('payments')}
          >
            Payments
          </button>
        )}
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <FinanceDashboard key={refreshKey} isAdmin={isAdmin} />
        )}

        {/* Invoices Tab */}
        {activeTab === 'invoices' && (
          <InvoiceList 
            key={refreshKey}
            studentId={!isAdmin ? user?.student_id : null}
            isAdmin={isAdmin}
          />
        )}

        {/* Fee Structures Tab (Admin Only) */}
        {activeTab === 'fees' && isAdmin && (
          <div className="card">
            <FeeStructureForm onSuccess={handleRefresh} />
          </div>
        )}

        {/* Payments Tab (Admin Only) */}
        {activeTab === 'payments' && isAdmin && (
          <div className="card">
            <PaymentForm 
              invoiceId={null}
              amount={0}
              onSuccess={handleRefresh}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default FinanceManagement;
