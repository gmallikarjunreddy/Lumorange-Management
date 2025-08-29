"""
Add sample data to recruitment system for testing
"""
import mysql.connector
from datetime import datetime, date, timedelta
import random

def add_sample_recruitment_data():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='lumorange_db',
            user='root',
            password='gmkr'
        )
        cursor = connection.cursor()
        
        print("Adding sample recruitment data...")
        
        # Sample Job Positions
        job_positions = [
            ("Senior Software Developer", 1, "Develop and maintain web applications using Python/Django and React", "Python, Django, React, JavaScript, SQL", "Senior", "Full Time", 80000, 120000, "Hyderabad", "Open", "2025-08-01", "2025-09-30"),
            ("Frontend Developer", 1, "Create responsive user interfaces using React and modern CSS", "React, JavaScript, HTML, CSS, TypeScript", "Mid Level", "Full Time", 60000, 90000, "Hyderabad", "Open", "2025-08-10", "2025-09-10"),
            ("HR Manager", 2, "Manage recruitment, employee relations, and HR policies", "HR Management, Recruitment, Employee Relations", "Senior", "Full Time", 70000, 100000, "Hyderabad", "Open", "2025-08-05", "2025-09-05"),
            ("Marketing Executive", 3, "Digital marketing campaigns and brand management", "Digital Marketing, SEO, Social Media, Content Creation", "Mid Level", "Full Time", 50000, 75000, "Hyderabad", "Open", "2025-08-15", "2025-10-15"),
            ("Data Analyst", 1, "Analyze business data and create insights and reports", "Python, SQL, Tableau, Excel, Statistics", "Junior", "Full Time", 45000, 65000, "Hyderabad", "Open", "2025-08-12", "2025-09-12")
        ]
        
        for job in job_positions:
            cursor.execute("""
                INSERT IGNORE INTO job_positions (position_title, department_id, job_description, required_skills, 
                                                experience_level, employment_type, salary_min, salary_max, location, 
                                                status, posted_date, closing_date) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, job)
        
        # Sample Candidates
        candidates = [
            ("CAND001", "Priya", "Sharma", "priya.sharma@email.com", "+91-9876543210", "Software Developer", "TechCorp", 75000, 95000, "30 days", 4.5, 3.0, "B.Tech Computer Science", "Python, Django, React, JavaScript, SQL, Git"),
            ("CAND002", "Ravi", "Kumar", "ravi.kumar@email.com", "+91-9876543211", "Frontend Developer", "WebSolutions", 55000, 80000, "15 days", 3.0, 2.5, "B.Tech IT", "React, JavaScript, HTML, CSS, Angular, TypeScript"),
            ("CAND003", "Anjali", "Patel", "anjali.patel@email.com", "+91-9876543212", "HR Specialist", "HRTech", 60000, 85000, "45 days", 5.0, 4.0, "MBA HR", "HR Management, Recruitment, Employee Relations, Training"),
            ("CAND004", "Suresh", "Reddy", "suresh.reddy@email.com", "+91-9876543213", "Marketing Manager", "AdAgency", 65000, 90000, "30 days", 6.0, 5.0, "MBA Marketing", "Digital Marketing, SEO, PPC, Social Media, Analytics"),
            ("CAND005", "Meera", "Singh", "meera.singh@email.com", "+91-9876543214", "Data Analyst", "DataCorp", 50000, 70000, "Immediate", 2.5, 2.0, "M.Tech Data Science", "Python, SQL, Tableau, R, Statistics, Machine Learning"),
            ("CAND006", "Vikash", "Gupta", "vikash.gupta@email.com", "+91-9876543215", "Full Stack Developer", "StartupXYZ", 70000, 100000, "60 days", 3.5, 3.0, "B.Tech CSE", "Python, React, Node.js, MongoDB, AWS"),
            ("CAND007", "Pooja", "Nair", "pooja.nair@email.com", "+91-9876543216", "UX Designer", "DesignStudio", 55000, 75000, "30 days", 4.0, 3.5, "M.Des User Experience", "UI/UX Design, Figma, Adobe XD, Prototyping"),
            ("CAND008", "Amit", "Joshi", "amit.joshi@email.com", "+91-9876543217", "DevOps Engineer", "CloudTech", 80000, 110000, "45 days", 5.5, 4.5, "B.Tech CSE", "AWS, Docker, Kubernetes, Jenkins, Python, Linux")
        ]
        
        for candidate in candidates:
            cursor.execute("""
                INSERT IGNORE INTO candidates (candidate_id, first_name, last_name, email, phone, current_position, 
                                             current_company, current_salary, expected_salary, notice_period, 
                                             total_experience, relevant_experience, highest_qualification, skills) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, candidate)
        
        # Sample Job Applications
        applications = [
            (1, 1, "2025-08-20", "Applied", "Company Website", "I am excited to apply for the Senior Software Developer position..."),
            (2, 2, "2025-08-22", "Under Review", "LinkedIn", "As a frontend developer with 3 years of experience..."),
            (3, 3, "2025-08-18", "Interview Scheduled", "Referral", "I am interested in the HR Manager role..."),
            (4, 4, "2025-08-25", "Applied", "Job Portal", "I would like to apply for the Marketing Executive position..."),
            (5, 5, "2025-08-21", "Shortlisted", "Company Website", "I am applying for the Data Analyst role..."),
            (6, 1, "2025-08-23", "Under Review", "LinkedIn", "I am a full stack developer interested in your senior role..."),
            (7, 2, "2025-08-24", "Applied", "Company Website", "I am a UX designer but interested in frontend development..."),
            (8, 1, "2025-08-19", "Interview Scheduled", "Referral", "DevOps engineer looking to transition to full stack development...")
        ]
        
        for app in applications:
            cursor.execute("""
                INSERT IGNORE INTO job_applications (candidate_id, job_position_id, application_date, status, 
                                                   application_source, cover_letter) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, app)
        
        # Sample Interviews
        interviews = [
            ("INT001", 3, 1, 1, "2025-09-02", "10:00:00", 60, "Video Call", "Scheduled"),
            ("INT002", 8, 2, 1, "2025-09-03", "14:00:00", 90, "Video Call", "Scheduled"),
            ("INT003", 1, 1, 1, "2025-08-28", "11:00:00", 60, "Video Call", "Completed", "Strong technical skills, good communication", 8.5, 7.5, 8.0, 8.0, "Hire"),
        ]
        
        for interview in interviews:
            if len(interview) == 9:  # Scheduled interview
                cursor.execute("""
                    INSERT IGNORE INTO interviews (interview_code, application_id, interview_type_id, interview_round, 
                                                 scheduled_date, scheduled_time, duration_minutes, interview_mode, status) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, interview)
            else:  # Completed interview
                cursor.execute("""
                    INSERT IGNORE INTO interviews (interview_code, application_id, interview_type_id, interview_round, 
                                                 scheduled_date, scheduled_time, duration_minutes, interview_mode, status,
                                                 interviewer_notes, technical_score, communication_score, cultural_fit_score,
                                                 overall_score, recommendation) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, interview)
        
        connection.commit()
        print("✅ Sample recruitment data added successfully!")
        
        # Show counts
        cursor.execute("SELECT COUNT(*) FROM job_positions")
        print(f"📊 Job Positions: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM candidates")
        print(f"👥 Candidates: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM job_applications")
        print(f"📝 Applications: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM interviews")
        print(f"🎯 Interviews: {cursor.fetchone()[0]}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

if __name__ == "__main__":
    add_sample_recruitment_data()