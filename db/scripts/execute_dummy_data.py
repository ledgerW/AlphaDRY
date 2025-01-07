import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)

from database import get_session
from sqlalchemy import text

def execute_sql_file():
    # Read the SQL file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file_path = os.path.join(script_dir, 'add_dummy_token_data.sql')
    
    with open(sql_file_path, 'r') as file:
        sql = file.read()
    
    # Execute the SQL using our database session
    with get_session() as session:
        session.execute(text(sql))
        session.commit()

if __name__ == "__main__":
    execute_sql_file()
