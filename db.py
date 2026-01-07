import mysql.connector

DB_CONFIG = {
    'user': 'root',
    'password': '',
    'host': 'localhost',
    'database': 'password_manager'
}

def connect_db():
    try:
        db_conn = mysql.connector.connect(**DB_CONFIG)
        create_tables(db_conn)
        return db_conn
    except mysql.connector.Error as err:
        if err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            raise Exception(f"Database '{DB_CONFIG['database']}' tidak ditemukan. Silakan buat secara manual. (MySQL Error: {err.errno})") 
        else:
            raise Exception(f"Gagal terhubung ke MySQL: {err}\nPastikan MySQL berjalan.") 

def create_tables(db_conn):
    cursor = db_conn.cursor()
    try:
        create_user_table = """
        CREATE TABLE IF NOT EXISTS master_user (
            id INT PRIMARY KEY,
            master_password_hash VARCHAR(255) NOT NULL
        )
        """
        cursor.execute(create_user_table)

        create_passwords_table = """
        CREATE TABLE IF NOT EXISTS passwords (
            id INT AUTO_INCREMENT PRIMARY KEY,
            service VARCHAR(255) NOT NULL,
            username VARCHAR(255) NOT NULL,
            encrypted_password BLOB NOT NULL
        )
        """
        cursor.execute(create_passwords_table)
        
        db_conn.commit()
        
    except mysql.connector.Error as err:
        raise Exception(f"Gagal membuat tabel: {err}") 
    finally:
        cursor.close()