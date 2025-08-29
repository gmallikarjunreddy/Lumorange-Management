-- =====================================================
-- LUMORANGE RECRUITMENT & INTERVIEW MANAGEMENT SYSTEM
-- Database Schema for Candidate Tracking System
-- =====================================================

-- Job Positions Table
CREATE TABLE IF NOT EXISTS job_positions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    position_title VARCHAR(255) NOT NULL,
    department_id INT,
    job_description TEXT,
    required_skills TEXT,
    experience_level ENUM('Entry Level', 'Junior', 'Mid Level', 'Senior', 'Lead', 'Manager', 'Director') NOT NULL,
    employment_type ENUM('Full Time', 'Part Time', 'Contract', 'Intern') DEFAULT 'Full Time',
    salary_min DECIMAL(10,2),
    salary_max DECIMAL(10,2),
    location VARCHAR(255),
    status ENUM('Open', 'Closed', 'On Hold') DEFAULT 'Open',
    posted_date DATE NOT NULL,
    closing_date DATE,
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Candidates Table
CREATE TABLE IF NOT EXISTS candidates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    alternate_phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100) DEFAULT 'India',
    pincode VARCHAR(10),
    current_company VARCHAR(255),
    current_position VARCHAR(255),
    current_salary DECIMAL(10,2),
    expected_salary DECIMAL(10,2),
    notice_period VARCHAR(50),
    total_experience DECIMAL(3,1),
    relevant_experience DECIMAL(3,1),
    highest_qualification VARCHAR(255),
    skills TEXT,
    resume_filename VARCHAR(255),
    resume_path VARCHAR(500),
    linkedin_profile VARCHAR(500),
    github_profile VARCHAR(500),
    portfolio_url VARCHAR(500),
    source ENUM('Job Portal', 'Referral', 'Direct Application', 'LinkedIn', 'Campus Hiring', 'Walk-in', 'Other') DEFAULT 'Direct Application',
    status ENUM('New', 'Shortlisted', 'In Process', 'Interview Scheduled', 'Interviewed', 'Selected', 'Rejected', 'On Hold', 'Offer Extended', 'Offer Accepted', 'Offer Declined', 'Joined') DEFAULT 'New',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Job Applications Table (Many-to-Many between candidates and positions)
CREATE TABLE IF NOT EXISTS job_applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id INT NOT NULL,
    job_position_id INT NOT NULL,
    application_date DATE NOT NULL,
    status ENUM('Applied', 'Under Review', 'Shortlisted', 'Interview Scheduled', 'Interviewed', 'Selected', 'Rejected', 'Withdrawn', 'Offer Extended', 'Offer Accepted', 'Offer Declined') DEFAULT 'Applied',
    application_source ENUM('Job Portal', 'Company Website', 'Referral', 'LinkedIn', 'Email', 'Walk-in', 'Other') DEFAULT 'Company Website',
    cover_letter TEXT,
    screening_score DECIMAL(3,1),
    hr_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    FOREIGN KEY (job_position_id) REFERENCES job_positions(id) ON DELETE CASCADE,
    UNIQUE KEY unique_application (candidate_id, job_position_id)
);

-- Interview Types Master Table
CREATE TABLE IF NOT EXISTS interview_types (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type_name VARCHAR(100) NOT NULL,
    description TEXT,
    typical_duration INT DEFAULT 60, -- in minutes
    is_active BOOLEAN DEFAULT TRUE
);

-- Interviews Table
CREATE TABLE IF NOT EXISTS interviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    interview_code VARCHAR(20) UNIQUE NOT NULL,
    application_id INT NOT NULL,
    interview_type_id INT NOT NULL,
    interview_round INT DEFAULT 1,
    scheduled_date DATE NOT NULL,
    scheduled_time TIME NOT NULL,
    duration_minutes INT DEFAULT 60,
    interview_mode ENUM('In-Person', 'Video Call', 'Phone Call', 'Online Assessment') DEFAULT 'In-Person',
    meeting_link VARCHAR(500),
    meeting_room VARCHAR(100),
    status ENUM('Scheduled', 'In Progress', 'Completed', 'Cancelled', 'Rescheduled', 'No Show') DEFAULT 'Scheduled',
    interviewer_notes TEXT,
    technical_score DECIMAL(3,1),
    communication_score DECIMAL(3,1),
    cultural_fit_score DECIMAL(3,1),
    overall_score DECIMAL(3,1),
    recommendation ENUM('Strong Hire', 'Hire', 'Maybe', 'No Hire', 'Strong No Hire'),
    feedback TEXT,
    next_steps TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES job_applications(id) ON DELETE CASCADE,
    FOREIGN KEY (interview_type_id) REFERENCES interview_types(id)
);

-- Interview Participants Table (Interviewers)
CREATE TABLE IF NOT EXISTS interview_participants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    interview_id INT NOT NULL,
    employee_id VARCHAR(10) NOT NULL,
    role ENUM('Primary Interviewer', 'Secondary Interviewer', 'Observer', 'Technical Expert', 'HR Representative') DEFAULT 'Primary Interviewer',
    individual_feedback TEXT,
    individual_score DECIMAL(3,1),
    individual_recommendation ENUM('Strong Hire', 'Hire', 'Maybe', 'No Hire', 'Strong No Hire'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (interview_id) REFERENCES interviews(id) ON DELETE CASCADE
);

-- Job Offers Table
CREATE TABLE IF NOT EXISTS job_offers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    offer_code VARCHAR(20) UNIQUE NOT NULL,
    application_id INT NOT NULL,
    position_offered VARCHAR(255) NOT NULL,
    department_id INT,
    offered_salary DECIMAL(10,2) NOT NULL,
    joining_bonus DECIMAL(10,2) DEFAULT 0,
    annual_bonus DECIMAL(10,2) DEFAULT 0,
    benefits TEXT,
    joining_date DATE,
    offer_date DATE NOT NULL,
    expiry_date DATE NOT NULL,
    status ENUM('Draft', 'Sent', 'Accepted', 'Declined', 'Expired', 'Withdrawn') DEFAULT 'Draft',
    offer_letter_path VARCHAR(500),
    acceptance_date DATE,
    decline_reason TEXT,
    hr_notes TEXT,
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES job_applications(id) ON DELETE CASCADE
);

-- Recruitment Pipeline Tracking
CREATE TABLE IF NOT EXISTS recruitment_pipeline (
    id INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NOT NULL,
    stage ENUM('Applied', 'Resume Screening', 'Phone Screening', 'Technical Test', 'Technical Interview', 'HR Interview', 'Management Interview', 'Final Interview', 'Background Check', 'Offer', 'Joined', 'Rejected') NOT NULL,
    stage_date DATE NOT NULL,
    stage_status ENUM('In Progress', 'Completed', 'Failed', 'Skipped') DEFAULT 'In Progress',
    notes TEXT,
    duration_days INT,
    completed_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES job_applications(id) ON DELETE CASCADE
);

-- Insert Sample Interview Types
INSERT IGNORE INTO interview_types (type_name, description, typical_duration) VALUES
('Phone Screening', 'Initial phone screening with HR/Recruiter', 30),
('Technical Interview', 'Technical assessment with technical team', 90),
('HR Interview', 'HR round focusing on cultural fit and compensation', 60),
('Management Interview', 'Interview with hiring manager/department head', 75),
('Final Interview', 'Final round with senior leadership', 45),
('Panel Interview', 'Group interview with multiple interviewers', 120),
('Online Assessment', 'Online technical or aptitude test', 90),
('Coding Challenge', 'Live coding session', 120),
('System Design', 'System design and architecture discussion', 90),
('Behavioral Interview', 'Behavioral questions and cultural fit assessment', 60);

-- Create Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email);
CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);
CREATE INDEX IF NOT EXISTS idx_applications_status ON job_applications(status);
CREATE INDEX IF NOT EXISTS idx_applications_date ON job_applications(application_date);
CREATE INDEX IF NOT EXISTS idx_interviews_date ON interviews(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_interviews_status ON interviews(status);
CREATE INDEX IF NOT EXISTS idx_job_positions_status ON job_positions(status);
CREATE INDEX IF NOT EXISTS idx_offers_status ON job_offers(status);