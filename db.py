import os
import sys
import mysql.connector
from dotenv import load_dotenv

# Fungsi untuk menentukan path file yang benar saat menjadi EXE
def get_resource_path(relative_path):
    """ Mendapatkan path absolut ke resource, berfungsi untuk dev dan PyInstaller """
    try:
        # PyInstaller membuat folder sementara di _MEIPASS saat dijalankan sebagai EXE
        base_path = sys._MEIPASS
    except Exception:
        # Jika dijalankan sebagai script .py biasa
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Memuat file .env menggunakan path yang sudah disesuaikan agar terbaca di EXE
env_path = get_resource_path(".env")
load_dotenv(env_path)

# Konfigurasi Database diperbarui dengan menambahkan Port
DB_CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),  # <--- Menambahkan Port untuk koneksi Aiven
    'database': os.getenv('DB_NAME')
}

def connect_db():
    try:
        # Melakukan koneksi menggunakan konfigurasi yang menyertakan port
        db_conn = mysql.connector.connect(**DB_CONFIG)
        create_tables(db_conn)
        return db_conn
    except mysql.connector.Error as err:
        if err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            raise Exception(f"Database '{DB_CONFIG['database']}' tidak ditemukan. Silakan buat secara manual. (MySQL Error: {err.errno})") 
        else:
            raise Exception(f"Gagal terhubung ke MySQL: {err}\nPastikan MySQL berjalan dan Port/Host sudah benar.") 

def create_tables(db_conn):
    cursor = db_conn.cursor()
    try:
        # Membuat tabel user jika belum ada
        create_user_table = """
        CREATE TABLE IF NOT EXISTS master_user (
            id INT PRIMARY KEY,
            master_password_hash VARCHAR(255) NOT NULL
        )
        """
        cursor.execute(create_user_table)

        # Membuat tabel password jika belum ada
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