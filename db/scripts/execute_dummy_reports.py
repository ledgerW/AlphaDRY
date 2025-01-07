#!/usr/bin/env python3
import os
import sys

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from database import get_session
from sqlalchemy import text

def execute_sql_file(file_path):
    """Execute a SQL file with proper error handling"""
    try:
        # Read the SQL file
        with open(file_path, 'r') as f:
            sql = f.read()
        
        # Split the SQL into individual statements
        statements = sql.split(';')
        
        # Execute each statement in a transaction
        with get_session() as session:
            for stmt in statements:
                # Skip empty statements
                if stmt.strip():
                    session.execute(text(stmt))
            session.commit()
            print(f"Successfully executed {file_path}")
            
    except Exception as e:
        print(f"Error executing {file_path}: {str(e)}")
        raise

if __name__ == "__main__":
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the SQL file
    sql_file = os.path.join(script_dir, "add_dummy_token_reports.sql")
    
    print(f"Executing SQL file: {sql_file}")
    execute_sql_file(sql_file)
    print("Done!")
