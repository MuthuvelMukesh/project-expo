# Frontend Implementation Guide - Finance & HR Modules

## Overview

This guide documents the complete frontend implementation for the Finance and HR modules in CampusIQ, including new React components, pages, styling, and API integration.

## Table of Contents

1. [New Components](#new-components)
2. [Page Files](#page-files)
3. [API Service Extensions](#api-service-extensions)
4. [Routing Structure](#routing-structure)
5. [Usage Examples](#usage-examples)
6. [Styling System](#styling-system)
7. [Data Flow](#data-flow)

---

## New Components

### Finance Module Components

#### **FinanceDashboard.jsx** (`frontend/src/components/Finance/FinanceDashboard.jsx`)
- **Purpose**: Main dashboard for viewing financial data
- **Props**:
  - `isAdmin` (boolean): Shows admin view if true, student view if false
- **Features**:
  - Outstanding balance display
  - Quick action buttons
  - Outstanding fees table
  - Recent payments history
  - Auto-refresh data on mount
- **States**:
  - Dashboard data with balance, fees, payments
  - Loading and error states
- **Example**:
  ```jsx
  <FinanceDashboard isAdmin={true} />
  ```

#### **FeeStructureForm.jsx** (`frontend/src/components/Finance/FeeStructureForm.jsx`)
- **Purpose**: Admin form to create fee structures
- **Props**:
  - `onSuccess` (function, optional): Callback when fee structure created
- **Features**:
  - Semester and fee type selection
  - Amount input with validation
  - Date range selection (valid_from, valid_to)
  - Success/error notifications
- **Form Fields**:
  - Semester (1-8)
  - Fee Type (tuition, library, sports, welfare, transportation, medical)
  - Amount (₹)
  - Valid From (date)
  - Valid To (date, optional)
- **Example**:
  ```jsx
  <FeeStructureForm onSuccess={() => refreshDashboard()} />
  ```

#### **PaymentForm.jsx** (`frontend/src/components/Finance/PaymentForm.jsx`)
- **Purpose**: Record student fee payments
- **Props**:
  - `invoiceId` (number): Invoice ID for payment
  - `amount` (number): Payment amount in rupees
  - `onSuccess` (function, optional): Callback after payment recorded
- **Features**:
  - Payment method selection
  - Reference number input
  - Amount confirmation
  - Payment status tracking
- **Payment Methods**: 
  - bank_transfer
  - credit_card, debit_card, upi
  - cheque, cash, online_portal
- **Example**:
  ```jsx
  <PaymentForm invoiceId={5} amount={1000} onSuccess={handlePaymentSuccess} />
  ```

#### **InvoiceList.jsx** (`frontend/src/components/Finance/InvoiceList.jsx`)
- **Purpose**: Display and manage invoices with filtering
- **Props**:
  - `studentId` (number, optional): Filter by student
  - `isAdmin` (boolean): Shows admin controls if true
- **Features**:
  - Invoice filtering (all, pending, paid, overdue)
  - Status badges with color coding
  - Invoice generation button (admin only)
  - Invoice details view
  - Payment action buttons
- **Status Values**: draft, issued, pending, paid, overdue, cancelled
- **Example**:
  ```jsx
  <InvoiceList studentId={42} isAdmin={false} />
  ```

### HR Module Components

#### **HRDashboard.jsx** (`frontend/src/components/HR/HRDashboard.jsx`)
- **Purpose**: Main HR overview dashboard
- **Features**:
  - Total employee count
  - Current month payroll summary
  - Pending payroll processing table
  - Recent salary slips list
  - Quick action buttons
- **Metrics Displayed**:
  - Total Employees
  - Total Gross Salary
  - Total Deductions
  - Net Payroll
- **Example**:
  ```jsx
  <HRDashboard isAdmin={true} />
  ```

#### **EmployeeForm.jsx** (`frontend/src/components/HR/EmployeeForm.jsx`)
- **Purpose**: Create/edit employee records with HR details
- **Props**:
  - `onSuccess` (function, optional): Callback on successful save
  - `editingEmployee` (object, optional): Employee data for editing
- **Features**:
  - Basic employee information (type, DOJ, DOB)
  - Contact information (phone, address)
  - Banking details (account, bank, IFSC)
  - Create or update employee
- **Employee Types**: faculty, staff, admin, non_teaching
- **Banks**: HDFC, ICICI, SBI, Axis, BoI, PNB, Other
- **Example**:
  ```jsx
  <EmployeeForm onSuccess={handleEmployeeAdded} />
  // Or for editing
  <EmployeeForm editingEmployee={employeeData} onSuccess={handleEmployeeUpdated} />
  ```

#### **SalaryStructureForm.jsx** (`frontend/src/components/HR/SalaryStructureForm.jsx`)
- **Purpose**: Define salary components for an employee
- **Props**:
  - `employeeId` (number): Employee ID for salary structure
  - `onSuccess` (function, optional): Callback on success
- **Features**:
  - Earnings section (base, DA, HRA, other allowances)
  - Deductions section (PF, insurance, tax rate)
  - Real-time salary calculation preview
  - Effective date range selection
- **Calculation Preview**:
  - Gross = Base + DA + HRA + Other Allowances
  - Deductions = PF + Insurance + (Gross × Tax%)
  - Net = Gross - Deductions
- **Example**:
  ```jsx
  <SalaryStructureForm employeeId={3} onSuccess={handleSalaryStructureCreated} />
  ```

#### **PayrollProcessing.jsx** (`frontend/src/components/HR/PayrollProcessing.jsx`)
- **Purpose**: Process monthly payroll for multiple employees
- **Props**:
  - `onSuccess` (function, optional): Callback after payroll processed
- **Features**:
  - Month and year selection
  - Employee multi-select with select all
  - Batch payroll processing
  - Processing status feedback
  - Success/error notifications
- **Process Flow**:
  1. Select month and year
  2. Select employees to process
  3. Submit to calculate and record payroll
  4. Automatic salary calculation per employee
- **Example**:
  ```jsx
  <PayrollProcessing onSuccess={handlePayrollProcessed} />
  ```

---

## Page Files

### **FinanceManagement.jsx** (`frontend/src/pages/FinanceManagement.jsx`)
- **Route**: `/finance`
- **Access**: Students and Admin
- **Tabs**:
  - Dashboard: Financial overview
  - Invoices: View and manage invoices
  - Fee Structures: Create fee rules (admin only)
  - Payments: Record payments (admin only)
- **Features**:
  - Tab-based navigation
  - Component composition
  - Refresh capability
  - Role-based tab visibility

### **HRManagement.jsx** (`frontend/src/pages/HRManagement.jsx`)
- **Route**: `/hr`
- **Access**: Admin only (with access denied page for others)
- **Tabs**:
  - Dashboard: HR overview
  - Employees: Add/edit employee records
  - Salary Structure: Define salary components
  - Process Payroll: Run monthly payroll
- **Features**:
  - Tab-based navigation
  - Employee management workflows
  - Payroll processing interface

---

## API Service Extensions

### Finance API Methods

```javascript
// Fee Management
await api.createFeeStructure(data)  // POST /api/finance/fee-structures
await api.listFeeStructures()       // GET /api/finance/fee-structures

// Student Balance & Fees
await api.getStudentBalance(studentId)  // GET /api/finance/student-balance/{id}

// Invoice Management
await api.createInvoice(studentId)      // POST /api/finance/invoices/generate/{id}
await api.getInvoices(studentId)        // GET /api/finance/invoices?student_id={id}

// Payment Management
await api.recordPayment(paymentData)    // POST /api/finance/payments
await api.getPayments(invoiceId)        // GET /api/finance/payments?invoice_id={id}
await api.verifyPayment(paymentId)      // PUT /api/finance/payments/{id}/verify

// Reports
await api.getFinanceReports(type)       // GET /api/finance/reports/{type}
// Types: 'outstanding', 'collection', 'revenue'
```

### HR API Methods

```javascript
// Employee Management
await api.createEmployee(data)          // POST /api/hr/employees
await api.listEmployees()               // GET /api/hr/employees
await api.getEmployeeDetails(empId)     // GET /api/hr/employees/{id}
await api.updateEmployee(empId, data)   // PUT /api/hr/employees/{id}

// Salary Structure
await api.createSalaryStructure(data)   // POST /api/hr/salary-structures
await api.getSalaryStructure(empId)     // GET /api/hr/salary-structures/{id}
await api.updateSalaryStructure(id, data) // PUT /api/hr/salary-structures/{id}

// Payroll Processing
await api.processSalary(data)            // POST /api/hr/salary-records/process
// data: { employee_id, month, year }

// Salary Records
await api.getSalaryRecords(empId)        // GET /api/hr/salary-records?employee_id={id}
await api.getSalarySlip(recordId)        // GET /api/hr/salary-records/{id}/slip
await api.markSalaryPaid(recordId)       // POST /api/hr/salary-records/{id}/pay

// Reports
await api.getPayrollReport(type, month, year) // GET /api/hr/reports/{type}
// Types: 'summary', 'slip'

// Attendance
await api.recordEmployeeAttendance(data) // POST /api/hr/attendance
await api.getEmployeeAttendance(empId, month, year) // GET /api/hr/attendance/{id}
```

---

## Routing Structure

### New Routes Added

```
/finance        - Finance Management Page (student, admin)
/hr             - HR & Payroll Page (admin only)
```

### Updated Navigation

**Student Sidebar**:
- Dashboard
- Timetable
- My Profile
- Attendance
- **Fees & Payments** ← NEW
- AI Copilot

**Admin Sidebar**:
- Admin Panel
- Users
- Courses
- Departments
- **Finance** ← NEW
- **HR & Payroll** ← NEW
- AI Copilot

---

## Usage Examples

### Student Viewing Fees

```jsx
import FinanceManagement from './pages/FinanceManagement';

// In App.jsx routes
<Route path="/finance" element={
  <ProtectedRoute allowedRoles={['student', 'admin']}>
    <FinanceManagement />
  </ProtectedRoute>
} />

// Student sees their fees and payments
// Only Dashboard and Invoices tabs available
```

### Admin Managing Payroll

```jsx
// Admin navigates to /hr
// Sees all tabs: Dashboard, Employees, Salary Structure, Process Payroll

// Create new employee
<EmployeeForm onSuccess={() => refreshDashboard()} />

// Define salary structure
<SalaryStructureForm employeeId={5} onSuccess={refreshDashboard} />

// Process monthly payroll
<PayrollProcessing onSuccess={refreshDashboard} />
```

### Viewing Financial Reports

```jsx
import { api } from './services/api';

// Get outstanding dues report
const report = await api.getFinanceReports('outstanding');
// Returns: { outstanding_dues: [...] }

// Get collection summary
const collection = await api.getFinanceReports('collection');
// Returns: { total_outstanding, recent_payments }

// Get revenue report
const revenue = await api.getFinanceReports('revenue');
// Returns: { total_collected, breakdown_by_type }
```

---

## Styling System

### CSS Files

1. **Finance.css** (`frontend/src/components/Finance/Finance.css`)
   - Dashboard grid layout
   - Form styling with responsive grid
   - Table styling with hover effects
   - Status badge colors
   - Button variations
   - Message notifications

2. **HR.css** (`frontend/src/components/HR/HR.css`)
   - Similar structure to Finance.css
   - Salary calculation preview box styles
   - Employee selection list styling
   - Payroll metrics display

3. **ManagementPages.css** (`frontend/src/pages/ManagementPages.css`)
   - Page header styling
   - Tab navigation and tab content
   - Access denied page
   - Print styles for reports
   - Responsive design breakpoints

### CSS Variables Used

```css
--primary-color: #007bff
--secondary-color: #6c757d
--text-primary: #333
--text-secondary: #666
--bg-secondary: #f8f9fa
--bg-section: #f9f9f9
--border-color: #ddd
--row-hover-bg: #f9f9f9
--table-header-bg: #f0f0f0
--bg-disabled: #e9ecef
--bg-highlight: #f0f0f0
```

### Responsive Breakpoints

- **Mobile** (< 768px):
  - Single column forms
  - Stacked filter buttons
  - Reduced font sizes
  - Full-width components

- **Desktop** (>= 768px):
  - Multi-column grids
  - Inline filters
  - Normal font sizes

---

## Data Flow

### Finance Data Flow

```
Student/Admin navigates to /finance
    ↓
FinanceManagement page loads
    ↓
Active tab determines which component renders:
  - Dashboard → FinanceDashboard fetches balance & fees
  - Invoices → InvoiceList fetches invoices with filter
  - Fees (admin) → FeeStructureForm POSTs new structure
  - Payments (admin) → PaymentForm POSTs payment
    ↓
API calls made via api.js service
    ↓
Backend /api/finance/* endpoints
    ↓
Response displayed in component with loading/error handling
    ↓
Optional callback (onSuccess) triggers parent refresh
```

### HR Data Flow

```
Admin navigates to /hr
    ↓
HRManagement page loads
    ↓
Active tab determines workflow:
  - Dashboard → HRDashboard fetches payroll data
  - Employees → EmployeeForm creates/edits employee
  - Salary → SalaryStructureForm defines components
  - Payroll → PayrollProcessing batch processes salary
    ↓
API calls made via api.js
    ↓
Backend /api/hr/* endpoints
    ↓
Multiple operations may be chained:
  - Add employee → Define salary → Process payroll
    ↓
Dashboard refreshes to show updated data
```

---

## File Structure

```
frontend/src/
├── components/
│   ├── Finance/
│   │   ├── FinanceDashboard.jsx
│   │   ├── FeeStructureForm.jsx
│   │   ├── PaymentForm.jsx
│   │   ├── InvoiceList.jsx
│   │   ├── Finance.css
│   │   └── index.js
│   ├── HR/
│   │   ├── HRDashboard.jsx
│   │   ├── EmployeeForm.jsx
│   │   ├── SalaryStructureForm.jsx
│   │   ├── PayrollProcessing.jsx
│   │   ├── HR.css
│   │   └── index.js
│   ├── Sidebar.jsx (UPDATED)
│   └── ...
├── pages/
│   ├── FinanceManagement.jsx
│   ├── HRManagement.jsx
│   ├── ManagementPages.css
│   └── ...
├── services/
│   ├── api.js (UPDATED)
│   └── ...
├── App.jsx (UPDATED)
└── ...
```

---

## Testing Components Locally

### 1. Start development server:
```bash
cd frontend
npm run dev
```

### 2. Login with admin account:
- Email: admin@example.com
- Password: admin123

### 3. Access Finance (/finance):
- View students' fees
- Create fee structures
- Process invoices and payments
- View financial reports

### 4. Access HR (/hr):
- Add employees
- Define salary structures
- Process monthly payroll
- View payroll reports

---

## Common Issues & Solutions

### Issue: API calls returning 401 Unauthorized
- **Cause**: Token expired or not attached
- **Solution**: Check localStorage for `campusiq_token`, re-login if expired

### Issue: Forms not submitting
- **Cause**: Required fields empty or validation failed
- **Solution**: Check console for validation errors, fill all required fields

### Issue: Dashboard not loading data
- **Cause**: API endpoint not responding
- **Solution**: Verify backend is running, check network tab in DevTools

### Issue: Sidebar not showing new links
- **Cause**: Browser cache or old component
- **Solution**: Hard refresh (Ctrl+F5), clear localStorage if needed

---

## Next Steps

1. **Frontend Testing**: Run E2E tests for all financial and HR workflows
2. **Performance**: Optimize large data tables with pagination
3. **Advanced Features**: Add export/print functionality for reports
4. **Mobile**: Improve mobile UX for small screens
5. **Notifications**: Add real-time updates for payment processing

---

## Support & Documentation

- API Documentation: See [FEATURES_IMPLEMENTATION.md](../FEATURES_IMPLEMENTATION.md)
- Backend Setup: See [ERP_QUICK_START.md](../ERP_QUICK_START.md)
- Testing Guide: See backend [FEATURES_IMPLEMENTATION.md](../FEATURES_IMPLEMENTATION.md#testing)

---

**Last Updated**: February 25, 2026
**Version**: 1.0
