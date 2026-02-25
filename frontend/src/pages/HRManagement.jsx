import React, { useState } from 'react';
import HRDashboard from '../components/HR/HRDashboard';
import EmployeeForm from '../components/HR/EmployeeForm';
import SalaryStructureForm from '../components/HR/SalaryStructureForm';
import PayrollProcessing from '../components/HR/PayrollProcessing';
import { useAuth } from '../context/AuthContext';
import '../pages/ManagementPages.css';

/**
 * HRManagement - Main HR page with dashboard and payroll management
 */
const HRManagement = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [activeTab, setActiveTab] = useState('dashboard');
  const [refreshKey, setRefreshKey] = useState(0);

  if (!isAdmin) {
    return (
      <div className="access-denied">
        <h2>Access Denied</h2>
        <p>Only HR administrators can access this page.</p>
      </div>
    );
  }

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
  };

  return (
    <div className="hr-management-page">
      <div className="page-header">
        <h1>HR & Payroll Management</h1>
        <p className="subtitle">Manage employees, salary structures, and payroll processing</p>
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
          className={`tab-btn ${activeTab === 'employees' ? 'active' : ''}`}
          onClick={() => setActiveTab('employees')}
        >
          Employees
        </button>
        <button 
          className={`tab-btn ${activeTab === 'salary' ? 'active' : ''}`}
          onClick={() => setActiveTab('salary')}
        >
          Salary Structure
        </button>
        <button 
          className={`tab-btn ${activeTab === 'payroll' ? 'active' : ''}`}
          onClick={() => setActiveTab('payroll')}
        >
          Process Payroll
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <HRDashboard key={refreshKey} isAdmin={isAdmin} />
        )}

        {/* Employees Tab */}
        {activeTab === 'employees' && (
          <div className="card">
            <EmployeeForm onSuccess={handleRefresh} />
          </div>
        )}

        {/* Salary Structure Tab */}
        {activeTab === 'salary' && (
          <div className="card">
            <SalaryStructureForm 
              employeeId={null}
              onSuccess={handleRefresh}
            />
          </div>
        )}

        {/* Payroll Processing Tab */}
        {activeTab === 'payroll' && (
          <div className="card">
            <PayrollProcessing onSuccess={handleRefresh} />
          </div>
        )}
      </div>
    </div>
  );
};

export default HRManagement;
