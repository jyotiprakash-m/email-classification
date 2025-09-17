-- Sample data for PostgreSQL schema

-- Insert sample users
INSERT INTO public."user" (username, email, password_hash, first_name, last_name, phone, employee_id, designation, department, user_role, approval_level, is_active) VALUES
('rajesh.kumar', 'rajesh.kumar@jharkhand.gov.in', '$2y$10$hashedpassword1', 'Rajesh', 'Kumar', '+91-9876543210', 'EMP001', 'Project Manager', 'Public Works', 'Applicant', NULL, TRUE),
('priya.singh', 'priya.singh@jharkhand.gov.in', '$2y$10$hashedpassword2', 'Priya', 'Singh', '+91-9876543211', 'EMP002', 'Education Officer', 'Education', 'Applicant', NULL, TRUE),
('amit.sharma', 'amit.sharma@jharkhand.gov.in', '$2y$10$hashedpassword3', 'Amit', 'Sharma', '+91-9876543212', 'EMP003', 'Medical Officer', 'Health', 'Applicant', NULL, TRUE),
('suresh.patel', 'suresh.patel@jharkhand.gov.in', '$2y$10$hashedpassword4', 'Dr. Suresh', 'Patel', '+91-9876543213', 'EMP004', 'Department Head', 'Public Works', 'Approver', 1, TRUE),
('sunita.devi', 'sunita.devi@jharkhand.gov.in', '$2y$10$hashedpassword5', 'Sunita', 'Devi', '+91-9876543214', 'EMP005', 'Finance Officer', 'Finance', 'Approver', 1, TRUE),
('ramesh.gupta', 'ramesh.gupta@jharkhand.gov.in', '$2y$10$hashedpassword6', 'Ramesh', 'Gupta', '+91-9876543215', 'EMP006', 'Medical Director', 'Health', 'Approver', 1, TRUE),
('admin.user', 'admin@jharkhand.gov.in', '$2y$10$hashedpassword7', 'Admin', 'User', '+91-9876543216', 'ADMIN001', 'System Administrator', 'IT', 'Admin', NULL, TRUE),
('vendor.abc', 'vendor@abcconstruction.com', '$2y$10$hashedpassword8', 'ABC Construction', 'Ltd', '+91-9876543217', 'VEN001', 'Vendor Representative', 'Construction', 'Vendor', NULL, TRUE),
('delivery.agent', 'delivery@logistics.com', '$2y$10$hashedpassword9', 'Ravi', 'Delivery', '+91-9876543218', 'DEL001', 'Delivery Agent', 'Logistics', 'Delivery_Agent', NULL, TRUE);

-- Insert sample applications
INSERT INTO public.applications (application_number, applicant_user_id, application_type, description, estimated_cost, priority_level) VALUES
('APP-2025-001', 1, 'Infrastructure', 'Road construction project for rural connectivity', 500000.00, 'High'),
('APP-2025-002', 2, 'Equipment Purchase', 'Computer equipment for government schools', 150000.00, 'Medium'),
('APP-2025-003', 3, 'Medical Supplies', 'Medical equipment procurement for district hospital', 300000.00, 'Critical'),
('APP-2025-004', 1, 'Maintenance', 'Bridge maintenance and repair work', 200000.00, 'High'),
('APP-2025-005', 2, 'Stationery', 'Office supplies for education department', 25000.00, 'Low');

-- Insert sample approvals
INSERT INTO public.approvals (application_id, approver_user_id, approval_level, approval_status, approval_date, comments) VALUES
(1, 4, 1, 'Approved', '2025-09-10 10:30:00', 'Project approved with budget allocation. Road construction is essential for rural connectivity.'),
(2, 5, 1, 'Approved', '2025-09-12 14:15:00', 'Budget verified and approved. Computer equipment meets technical specifications.'),
(3, 6, 1, 'Pending', NULL, 'Under review for medical equipment compliance and budget verification.'),
(4, 4, 1, 'Approved', '2025-09-13 09:20:00', 'Bridge maintenance approved. Safety inspection required before work begins.'),
(5, 5, 1, 'Approved', '2025-09-14 11:45:00', 'Office supplies approved within budget limits.');

-- Insert sample orders
INSERT INTO public.orders (application_id, order_number, order_type, vendor_name, vendor_contact, order_amount, order_date, expected_completion_date, status) VALUES
(1, 'WO-2025-001', 'Work Order', 'ABC Construction Ltd', 'contact@abcconstruction.com', 500000.00, '2025-09-11', '2025-12-11', 'Issued'),
(2, 'PO-2025-001', 'Purchase Order', 'Tech Solutions Pvt Ltd', 'sales@techsolutions.com', 150000.00, '2025-09-13', '2025-10-13', 'Issued'),
(4, 'WO-2025-002', 'Work Order', 'Bridge Engineers Co', 'info@bridgeengineers.com', 200000.00, '2025-09-14', '2025-11-14', 'Draft'),
(5, 'PO-2025-002', 'Purchase Order', 'Office Supplies Hub', 'orders@officesupplies.com', 25000.00, '2025-09-15', '2025-09-25', 'Issued');

-- Insert sample order items
INSERT INTO public.order_items (order_id, item_name, item_description, quantity, unit_price, total_price, specifications) VALUES
(2, 'Desktop Computer', 'All-in-one desktop computer for schools', 50, 25000.00, 1250000.00, 'Intel i5, 8GB RAM, 256GB SSD, 21.5 inch display'),
(2, 'Printer', 'Laser printer for school office', 10, 15000.00, 150000.00, 'Monochrome laser printer, network enabled'),
(4, 'A4 Paper', 'White A4 printing paper', 100, 200.00, 20000.00, '70 GSM, 500 sheets per ream'),
(4, 'Pens', 'Blue ballpoint pens', 500, 10.00, 5000.00, 'Blue ink, smooth writing');

-- Insert sample deliveries
INSERT INTO public.deliveries (order_id, delivery_number, delivery_agent_user_id, delivery_address, delivery_contact, delivery_status, delivery_notes) VALUES
(1, 'DEL-2025-001', 9, 'Construction Site, Village Ramgarh, Ranchi District, Jharkhand - 835103', 'Site Engineer: +91-9876543220', 'Pending', 'Materials to be delivered to construction site. Road access confirmed.'),
(2, 'DEL-2025-002', 9, 'Government Higher Secondary School, Dhanbad, Jharkhand - 826001', 'Principal: +91-9876543221', 'In Transit', 'Computer equipment packed and dispatched. Expected delivery in 2 days.'),
(4, 'DEL-2025-003', 9, 'District Education Office, Hazaribagh, Jharkhand - 825301', 'Office Manager: +91-9876543222', 'Delivered', 'Office supplies delivered successfully. Received by office staff.');

-- Insert sample audit log entries
INSERT INTO public.audit_log (table_name, record_id, action, old_values, new_values, changed_by_user_id, changed_at) VALUES
('applications', 1, 'INSERT', NULL, 
	'{"application_number": "APP-2025-001", "applicant_user_id": 1, "application_type": "Infrastructure", "description": "Road construction project for rural connectivity", "estimated_cost": 500000.00, "priority_level": "High", "status": "Submitted"}', 
	1, '2025-09-09 09:00:00'),
('applications', 1, 'UPDATE', 
	'{"status": "Submitted"}', 
	'{"status": "Under Review"}', 
	7, '2025-09-09 10:30:00'),
('applications', 1, 'UPDATE', 
	'{"status": "Under Review"}', 
	'{"status": "Approved"}', 
	4, '2025-09-10 10:30:00'),
('approvals', 1, 'INSERT', NULL,
	'{"application_id": 1, "approver_user_id": 4, "approval_level": 1, "approval_status": "Pending"}',
	7, '2025-09-09 11:00:00'),
('approvals', 1, 'UPDATE',
	'{"approval_status": "Pending"}',
	'{"approval_status": "Approved", "approval_date": "2025-09-10 10:30:00", "comments": "Project approved with budget allocation. Road construction is essential for rural connectivity."}',
	4, '2025-09-10 10:30:00'),
('orders', 1, 'INSERT', NULL,
	'{"application_id": 1, "order_number": "WO-2025-001", "order_type": "Work Order", "vendor_name": "ABC Construction Ltd", "order_amount": 500000.00, "status": "Draft"}',
	7, '2025-09-10 15:20:00'),
('orders', 1, 'UPDATE',
	'{"status": "Draft"}',
	'{"status": "Issued", "order_date": "2025-09-11"}',
	7, '2025-09-11 09:15:00'),
('applications', 2, 'INSERT', NULL,
	'{"application_number": "APP-2025-002", "applicant_user_id": 2, "application_type": "Equipment Purchase", "description": "Computer equipment for government schools", "estimated_cost": 150000.00, "priority_level": "Medium", "status": "Submitted"}',
	2, '2025-09-11 14:30:00'),
('applications', 2, 'UPDATE',
	'{"status": "Submitted"}',
	'{"status": "Approved"}',
	5, '2025-09-12 14:15:00'),
('orders', 2, 'INSERT', NULL,
	'{"application_id": 2, "order_number": "PO-2025-001", "order_type": "Purchase Order", "vendor_name": "Tech Solutions Pvt Ltd", "order_amount": 150000.00, "status": "Issued"}',
	7, '2025-09-12 16:45:00'),
('deliveries', 1, 'INSERT', NULL,
	'{"order_id": 1, "delivery_number": "DEL-2025-001", "delivery_agent_user_id": 9, "delivery_status": "Pending"}',
	7, '2025-09-11 10:00:00'),
('deliveries', 2, 'INSERT', NULL,
	'{"order_id": 2, "delivery_number": "DEL-2025-002", "delivery_agent_user_id": 9, "delivery_status": "Pending"}',
	9, '2025-09-13 08:30:00'),
('deliveries', 2, 'UPDATE',
	'{"delivery_status": "Pending"}',
	'{"delivery_status": "In Transit", "tracking_number": "TRK123456789"}',
	9, '2025-09-13 14:20:00'),
('deliveries', 3, 'UPDATE',
	'{"delivery_status": "In Transit"}',
	'{"delivery_status": "Delivered", "received_by_user_id": 2, "received_date": "2025-09-15 11:30:00"}',
	9, '2025-09-15 11:30:00'),
('user', 8, 'INSERT', NULL,
	'{"username": "vendor.abc", "email": "vendor@abcconstruction.com", "first_name": "ABC Construction", "last_name": "Ltd", "user_role": "Vendor", "is_active": true}',
	7, '2025-09-08 16:20:00'),
('user', 3, 'UPDATE',
	'{"last_login": null}',
	'{"last_login": "2025-09-12 09:15:00"}',
	3, '2025-09-12 09:15:00'),
('applications', 4, 'INSERT', NULL,
	'{"application_number": "APP-2025-004", "applicant_user_id": 1, "application_type": "Maintenance", "description": "Bridge maintenance and repair work", "estimated_cost": 200000.00, "priority_level": "High", "status": "Submitted"}',
	1, '2025-09-13 10:45:00'),
('applications', 4, 'UPDATE',
	'{"status": "Submitted"}',
	'{"status": "Approved"}',
	4, '2025-09-13 09:20:00'),
('orders', 4, 'INSERT', NULL,
	'{"application_id": 5, "order_number": "PO-2025-002", "order_type": "Purchase Order", "vendor_name": "Office Supplies Hub", "order_amount": 25000.00, "status": "Draft"}',
	7, '2025-09-14 13:10:00'),
('user', 1, 'UPDATE',
	'{"phone": "+91-9876543210"}',
	'{"phone": "+91-9876543299"}',
	1, '2025-09-14 16:30:00');