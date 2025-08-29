"""
Setup script for Recruitment System Database
"""
import mysql.connector
from mysql.connector import Error

def setup_recruitment_database():
    try:
        # Database connection
        connection = mysql.connector.connect(
            host='localhost',
            database='lumorange_db',
            user='root',
            password='gmkr'
        )

        if connection.is_connected():
            cursor = connection.cursor()
            print("Connected to MySQL database")

            # Read SQL file and execute statements
            with open('recruitment_database_setup.sql', 'r') as file:
                sql_script = file.read()

            # Split by semicolon and execute each statement
            statements = sql_script.split(';')
            
            for statement in statements:
                statement = statement.strip()
                if statement:
                    try:
                        cursor.execute(statement)
                        print(f"✅ Executed: {statement[:50]}...")
                    except Error as e:
                        if "already exists" in str(e):
                            print(f"⚠️ Already exists: {statement[:50]}...")
                        else:
                            print(f"❌ Error: {e}")
                            continue

            connection.commit()
            print("\n🎉 Recruitment database setup completed successfully!")
            
            # Verify tables were created
            cursor.execute("SHOW TABLES LIKE '%candidates%' OR SHOW TABLES LIKE '%job_positions%' OR SHOW TABLES LIKE '%interviews%'")
            tables = cursor.fetchall()
            print(f"\n📋 Created {len(tables)} recruitment tables:")
            for table in tables:
                print(f"   • {table[0]}")

    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("\nMySQL connection is closed")

if __name__ == "__main__":
    setup_recruitment_database()