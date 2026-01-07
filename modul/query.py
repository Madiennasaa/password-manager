import mysql.connector
from db import connect_db
from util import encrypt_password, decrypt_password, hash_master_password, verify_master_password


def check_if_user_exists():
    db_conn = None
    try:
        db_conn = connect_db()
        cursor = db_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM master_user")
        count = cursor.fetchone()[0]
        return count > 0
    except mysql.connector.Error as err:
        raise Exception(f"Gagal mengecek user: {err}")
    finally:
        if db_conn and db_conn.is_connected():
            cursor.close()
            db_conn.close()


def register_master_user(password):
    db_conn = None
    try:
        db_conn = connect_db()
        cursor = db_conn.cursor()
        hashed_password = hash_master_password(password)
        sql = "INSERT INTO master_user (id, master_password_hash) VALUES (%s, %s)"
        cursor.execute(sql, (1, hashed_password))
        db_conn.commit()
        return True
    except mysql.connector.Error as err:
        raise Exception(f"Gagal mendaftar user: {err}")
    finally:
        if db_conn and db_conn.is_connected():
            cursor.close()
            db_conn.close()


def authenticate_user(password):
    db_conn = None
    try:
        db_conn = connect_db()
        cursor = db_conn.cursor()
        cursor.execute("SELECT master_password_hash FROM master_user WHERE id = 1")
        result = cursor.fetchone()

        if result:
            password_hash = result[0]
            return verify_master_password(password_hash, password)
        return False
    except mysql.connector.Error as err:
        raise Exception(f"Gagal autentikasi: {err}")
    finally:
        if db_conn and db_conn.is_connected():
            cursor.close()
            db_conn.close()


def insert_new_entry(service, username, password, master_key):
    if not (service and username and password):
        raise Exception("Semua kolom harus diisi.")

    db_conn = None
    try:
        db_conn = connect_db()
        cursor = db_conn.cursor()
        encrypted_pwd = encrypt_password(password, master_key)
        sql = "INSERT INTO passwords (service, username, encrypted_password) VALUES (%s, %s, %s)"
        cursor.execute(sql, (service, username, encrypted_pwd))
        db_conn.commit()
        return True
    except mysql.connector.Error as err:
        raise Exception(f"Gagal memasukkan entri: {err}")
    except Exception as e:
        raise Exception(f"Gagal memproses sandi: {e}")
    finally:
        if db_conn and db_conn.is_connected():
            cursor.close()
            db_conn.close()


def get_all_entries(sort_by="service", search_keyword=""):
    entries = []
    db_conn = None

    if sort_by not in ["service", "username", "id"]:
        sort_by = "service"

    try:
        db_conn = connect_db()
        cursor = db_conn.cursor(dictionary=True)

        sql = "SELECT id, service, username, encrypted_password FROM passwords"
        params = []

        if search_keyword:
            sql += " WHERE service LIKE %s OR username LIKE %s"
            search_param = f"%{search_keyword}%"
            params.extend([search_param, search_param])

        sql += f" ORDER BY {sort_by}"
        cursor.execute(sql, tuple(params))
        entries = cursor.fetchall()
        return entries
    except mysql.connector.Error as err:
        raise Exception(f"Gagal mengambil entri: {err}")
    finally:
        if db_conn and db_conn.is_connected():
            cursor.close()
            db_conn.close()


def delete_entry(entry_id):
    if not entry_id:
        return False

    db_conn = None
    try:
        db_conn = connect_db()
        cursor = db_conn.cursor()
        sql = "DELETE FROM passwords WHERE id = %s"
        cursor.execute(sql, (entry_id,))
        db_conn.commit()
        return cursor.rowcount > 0
    except mysql.connector.Error as err:
        raise Exception(f"Gagal menghapus entri: {err}")
    except Exception as e:
        raise Exception(f"Terjadi kesalahan: {e}")
    finally:
        if db_conn and db_conn.is_connected():
            cursor.close()
            db_conn.close()


def update_entry(entry_id, service, username, password, master_key):
    if not (entry_id and service and username and password):
        raise Exception("Semua kolom harus diisi.")

    db_conn = None
    try:
        db_conn = connect_db()
        cursor = db_conn.cursor()
        encrypted_pwd = encrypt_password(password, master_key)
        sql = "UPDATE passwords SET service = %s, username = %s, encrypted_password = %s WHERE id = %s"
        cursor.execute(sql, (service, username, encrypted_pwd, entry_id))
        db_conn.commit()
        return True
    except mysql.connector.Error as err:
        raise Exception(f"Gagal memperbarui entri: {err}")
    except Exception as e:
        raise Exception(f"Gagal memproses sandi baru: {e}")
    finally:
        if db_conn and db_conn.is_connected():
            cursor.close()
            db_conn.close()