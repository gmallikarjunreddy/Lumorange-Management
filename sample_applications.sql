-- Add sample job applications
INSERT INTO job_applications (candidate_id, job_position_id, applied_date, status, cover_letter, salary_expectation, priority, created_at) VALUES
(1, 1, '2025-08-25', 'Applied', 'I am excited to apply for this software developer position. I have strong experience in Python and web development.', 75000.00, 'High', NOW()),
(2, 1, '2025-08-26', 'Under Review', 'Looking forward to contributing to your development team with my full-stack experience.', 80000.00, 'Medium', NOW()),
(3, 2, '2025-08-27', 'Interview Scheduled', 'I am passionate about marketing and have successfully run several campaigns in my previous roles.', 60000.00, 'High', NOW()),
(4, 1, '2025-08-28', 'Applied', 'Software development has been my passion for over 5 years. I would love to join your innovative team.', 70000.00, 'Low', NOW()),
(5, 3, '2025-08-28', 'Interview Completed', 'With 8 years of HR experience, I am confident I can lead your human resources initiatives effectively.', 90000.00, 'High', NOW());