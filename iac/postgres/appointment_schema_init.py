"""Initialize appointment management database schema."""
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def init_appointment_schema():
    """Initialize the appointment management schema in PostgreSQL."""
    # Read database credentials from environment
    db_host = os.getenv('POSTGRES_HOST', 'localhost')
    db_port = os.getenv('POSTGRES_PORT', '5432')
    db_user = os.getenv('POSTGRES_USER', 'postgres')
    db_pass = os.getenv('POSTGRES_PASSWORD', 'postgres')
    db_name = os.getenv('POSTGRES_DB', 'rag_db')

    # Get the absolute path to the directory containing this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file_path = os.path.join(script_dir, 'appointment_schema.sql')

    # Connect to PostgreSQL
    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_pass,
        database=db_name
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    try:
        print("Initializing appointment management schema...")
        
        # Read and execute the schema SQL file
        with open(sql_file_path, 'r') as f:
            schema_sql = f.read()
            cursor.execute(schema_sql)
        
        # Insert initial specializations
        specializations = [
            ('General Medicine', 'Primary healthcare and general consultations'),
            ('Pediatrics', 'Medical care for children and adolescents'),
            ('Cardiology', 'Heart and cardiovascular system'),
            ('Orthopedics', 'Musculoskeletal system'),
            ('Dermatology', 'Skin conditions and treatments')
        ]
        
        cursor.executemany("""
            INSERT INTO appointments.specializations (name, description)
            VALUES (%s, %s)
            ON CONFLICT (name) DO NOTHING
        """, specializations)
        
        print("Appointment management schema initialized successfully!")
        
    except Exception as e:
        print(f"Error initializing schema: {str(e)}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    init_appointment_schema()
