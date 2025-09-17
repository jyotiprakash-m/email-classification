-- Jharkhand Procurement Database Schema (PostgreSQL)
-- Database: jharkhand_db_simulation

-- Create database (run separately)
-- CREATE DATABASE jharkhand_db_simulation;
-- \c jharkhand_db_simulation

-- ENUM types
CREATE TYPE user_role_enum AS ENUM ('Admin', 'Applicant', 'Approver', 'Vendor', 'Delivery_Agent');
CREATE TYPE priority_level_enum AS ENUM ('Low', 'Medium', 'High', 'Critical');
CREATE TYPE status_enum AS ENUM ('Submitted', 'Under Review', 'Approved', 'Rejected');
CREATE TYPE approval_status_enum AS ENUM ('Pending', 'Approved', 'Rejected', 'Returned');
CREATE TYPE order_type_enum AS ENUM ('Work Order', 'Purchase Order');
CREATE TYPE order_status_enum AS ENUM ('Draft', 'Issued', 'In Progress', 'Completed', 'Cancelled');
CREATE TYPE delivery_status_enum AS ENUM ('Pending', 'In Transit', 'Delivered', 'Failed', 'Returned');
CREATE TYPE reference_type_enum AS ENUM ('Application', 'Approval', 'Order', 'Delivery');
CREATE TYPE audit_action_enum AS ENUM ('INSERT', 'UPDATE', 'DELETE');

-- USER MANAGEMENT
CREATE TABLE public."user" (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    employee_id VARCHAR(50) UNIQUE,
    designation VARCHAR(100),
    department VARCHAR(100),
    office_address TEXT,
    user_role user_role_enum NOT NULL,
    approval_level INT,
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- APPLICATION MANAGEMENT
CREATE TABLE public.applications (
    application_id SERIAL PRIMARY KEY,
    application_number VARCHAR(50) UNIQUE NOT NULL,
    applicant_user_id INT NOT NULL REFERENCES "user"(user_id) ON DELETE RESTRICT,
    application_type VARCHAR(100),
    description TEXT,
    estimated_cost NUMERIC(15,2),
    priority_level priority_level_enum DEFAULT 'Medium',
    application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status status_enum DEFAULT 'Submitted',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- APPROVAL WORKFLOW
CREATE TABLE public.approvals (
    approval_id SERIAL PRIMARY KEY,
    application_id INT NOT NULL REFERENCES applications(application_id) ON DELETE CASCADE,
    approver_user_id INT NOT NULL REFERENCES "user"(user_id) ON DELETE RESTRICT,
    approval_level INT NOT NULL,
    approval_status approval_status_enum DEFAULT 'Pending',
    approval_date TIMESTAMP,
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ORDER MANAGEMENT
CREATE TABLE public.orders (
    order_id SERIAL PRIMARY KEY,
    application_id INT NOT NULL REFERENCES applications(application_id) ON DELETE CASCADE,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    order_type order_type_enum NOT NULL,
    vendor_name VARCHAR(255),
    vendor_contact VARCHAR(255),
    vendor_address TEXT,
    order_amount NUMERIC(15,2) NOT NULL,
    order_date DATE NOT NULL,
    expected_completion_date DATE,
    terms_and_conditions TEXT,
    status order_status_enum DEFAULT 'Draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE public.order_items (
    item_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    item_name VARCHAR(255) NOT NULL,
    item_description TEXT,
    quantity INT NOT NULL,
    unit_price NUMERIC(10,2) NOT NULL,
    total_price NUMERIC(15,2) NOT NULL,
    specifications TEXT
);

-- DELIVERY MANAGEMENT
CREATE TABLE public.deliveries (
    delivery_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    delivery_number VARCHAR(50) UNIQUE NOT NULL,
    delivery_agent_user_id INT REFERENCES "user"(user_id) ON DELETE SET NULL,
    delivery_date DATE,
    delivery_address TEXT NOT NULL,
    delivery_contact VARCHAR(255),
    tracking_number VARCHAR(100),
    delivery_status delivery_status_enum DEFAULT 'Pending',
    delivery_notes TEXT,
    received_by_user_id INT REFERENCES "user"(user_id) ON DELETE SET NULL,
    received_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- DOCUMENT MANAGEMENT
CREATE TABLE public.documents (
    document_id SERIAL PRIMARY KEY,
    reference_type reference_type_enum NOT NULL,
    reference_id INT NOT NULL,
    document_name VARCHAR(255) NOT NULL,
    document_path VARCHAR(500) NOT NULL,
    file_size INT,
    uploaded_by_user_id INT NOT NULL REFERENCES "user"(user_id) ON DELETE RESTRICT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AUDIT AND LOGGING
CREATE TABLE public.audit_log (
    log_id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id INT NOT NULL,
    action audit_action_enum NOT NULL,
    old_values JSONB,
    new_values JSONB,
    changed_by_user_id INT REFERENCES "user"(user_id) ON DELETE SET NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- INDEXES
CREATE INDEX idx_user_email ON public."user"(email);
CREATE INDEX idx_user_employee_id ON public."user"(employee_id);
CREATE INDEX idx_user_role ON public."user"(user_role);
CREATE INDEX idx_user_department ON public."user"(department);
CREATE INDEX idx_application_status ON public.applications(status);
CREATE INDEX idx_application_date ON public.applications(application_date);
CREATE INDEX idx_application_applicant ON public.applications(applicant_user_id);
CREATE INDEX idx_approval_status ON public.approvals(approval_status);
CREATE INDEX idx_approval_application ON public.approvals(application_id);
CREATE INDEX idx_approval_user ON public.approvals(approver_user_id);
CREATE INDEX idx_order_status ON public.orders(status);
CREATE INDEX idx_order_date ON public.orders(order_date);
CREATE INDEX idx_order_application ON public.orders(application_id);
CREATE INDEX idx_delivery_status ON public.deliveries(delivery_status);
CREATE INDEX idx_delivery_date ON public.deliveries(delivery_date);
CREATE INDEX idx_delivery_order ON public.deliveries(order_id);
CREATE INDEX idx_document_reference ON public.documents(reference_type, reference_id);
CREATE INDEX idx_document_uploaded_by ON public.documents(uploaded_by_user_id);

-- Note: Sample data and views can be converted similarly if needed.
