-- Orbital Robotics: employee directory seed data
-- For testing a future SQL source connector against a real Postgres table.

DROP TABLE IF EXISTS employees;

CREATE TABLE employees (
    employee_id   VARCHAR(10) PRIMARY KEY,
    full_name     VARCHAR(100) NOT NULL,
    department    VARCHAR(50) NOT NULL,
    role          VARCHAR(100) NOT NULL,
    manager_id    VARCHAR(10),
    hire_date     DATE NOT NULL
);

INSERT INTO employees (employee_id, full_name, department, role, manager_id, hire_date) VALUES
('EMP-001', 'Rahul Mehta',        'Engineering', 'Falcon Engineering Lead',      NULL,      '2021-04-12'),
('EMP-002', 'Ananya Rao',         'Engineering', 'Platform Team Lead',           NULL,      '2021-06-01'),
('EMP-003', 'Priya Nandakumar',   'HR',          'Head of HR',                   NULL,      '2020-01-15'),
('EMP-004', 'Kevin Osei',         'Procurement', 'Procurement Manager',          NULL,      '2022-02-20'),
('EMP-005', 'Sara Lindqvist',     'Engineering', 'Backend Engineer, Falcon',     'EMP-001', '2025-11-03'),
('EMP-006', 'Daniel Cho',         'Engineering', 'Backend Engineer, Falcon',     'EMP-001', '2026-01-12'),
('EMP-007', 'Meera Iyer',         'Engineering', 'Platform Engineer',            'EMP-002', '2023-07-19'),
('EMP-008', 'Tomas Novak',        'Engineering', 'Site Reliability Engineer',    'EMP-002', '2024-03-08');
