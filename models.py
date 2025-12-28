import psycopg2
import os
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash

def get_db():
    DATABASE_URL = os.getenv("DB_URL")
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        conn.autocommit = True 
        return conn
    except Exception as e:
        print(f"Koneksi Supabase Gagal: {e}")
        return None

class TravelModel:
    @staticmethod
    def get_all_packages():
        db = get_db()
        if not db: return []
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM paket_travel ORDER BY id DESC")
            result = cursor.fetchall()
        db.close()
        return result

    @staticmethod
    def add_package(nama, tujuan, harga):
        db = get_db()
        if not db: return
        with db.cursor() as cursor:
            cursor.execute("INSERT INTO paket_travel (nama_paket, tujuan, harga) VALUES (%s, %s, %s)", 
                           (nama, tujuan, harga))
        db.close()

    @staticmethod
    def delete_package(id):
        db = get_db()
        if not db: return
        with db.cursor() as cursor:
            cursor.execute("DELETE FROM paket_travel WHERE id=%s", (id,))
        db.close()

    @staticmethod
    def get_package_by_id(id):
        db = get_db()
        if not db: return None
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM paket_travel WHERE id=%s", (id,))
            result = cursor.fetchone()
        db.close()
        return result

    @staticmethod
    def update_package(id, nama, tujuan, harga):
        db = get_db()
        if not db: return
        with db.cursor() as cursor:
            cursor.execute("""
                UPDATE paket_travel 
                SET nama_paket=%s, tujuan=%s, harga=%s 
                WHERE id=%s
            """, (nama, tujuan, harga, id))
        db.close()

    @staticmethod
    def pesan_paket(username, id_paket, tgl_wisata, jumlah, catatan):
        db = get_db()
        if not db: return False
        cursor = db.cursor()
        cursor.execute('SELECT id_user FROM "user" WHERE username=%s', (username,))
        user = cursor.fetchone()
        if user:
            cursor.execute("""
                INSERT INTO pesanan (id_user, id_paket, tgl_wisata, jumlah_orang, catatan, status) 
                VALUES (%s, %s, %s, %s, %s, 'Pending')
            """, (user['id_user'], id_paket, tgl_wisata, jumlah, catatan))
            db.close()
            return True
        db.close()
        return False

    @staticmethod
    def get_pesanan_user(username):
        db = get_db()
        if not db: return []
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT pesanan.*, paket_travel.nama_paket, paket_travel.tujuan, paket_travel.harga 
                FROM pesanan 
                JOIN paket_travel ON pesanan.id_paket = paket_travel.id
                JOIN "user" ON pesanan.id_user = "user".id_user
                WHERE "user".username = %s
                ORDER BY pesanan.id DESC
            """, (username,))
            result = cursor.fetchall()
        db.close()
        return result

    @staticmethod
    def get_semua_pesanan_admin():
        db = get_db()
        if not db: return []
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT pesanan.*, paket_travel.nama_paket, "user".username 
                FROM pesanan 
                JOIN paket_travel ON pesanan.id_paket = paket_travel.id
                JOIN "user" ON pesanan.id_user = "user".id_user
                ORDER BY pesanan.id DESC
            """)
            result = cursor.fetchall()
        db.close()
        return result
        
    @staticmethod
    def update_status_admin(pesanan_id, status_baru):
        db = get_db()
        if not db: return False, "Koneksi gagal"
        cursor = db.cursor()
        cursor.execute("SELECT status FROM pesanan WHERE id=%s", (pesanan_id,))
        pesanan = cursor.fetchone()
        
        if pesanan:
            if pesanan['status'] == 'Dibatalkan':
                db.close()
                return False, "Gagal! Pesanan sudah dibatalkan oleh user."
            
            cursor.execute("UPDATE pesanan SET status=%s WHERE id=%s", (status_baru, pesanan_id))
            db.close()
            return True, f"Status pesanan berhasil diubah menjadi {status_baru}."
        
        db.close()
        return False, "Data pesanan tidak ditemukan."
        
    @staticmethod
    def update_status_pesanan(id, status):
        db = get_db()
        if not db: return
        with db.cursor() as cursor:
            cursor.execute("UPDATE pesanan SET status=%s WHERE id=%s", (status, id))
        db.close()

    @staticmethod
    def batal_pesanan_user(pesanan_id, username):
        db = get_db()
        if not db: return False, "Koneksi gagal"
        cursor = db.cursor()
        sql_check = """
            SELECT pesanan.id FROM pesanan 
            JOIN "user" ON pesanan.id_user = "user".id_user
            WHERE pesanan.id=%s AND "user".username=%s AND pesanan.status='Pending'
        """
        cursor.execute(sql_check, (pesanan_id, username))
        pesanan = cursor.fetchone()
        
        if pesanan:
            cursor.execute("UPDATE pesanan SET status='Dibatalkan' WHERE id=%s", (pesanan_id,))
            db.close()
            return True, "Pesanan berhasil dibatalkan."
        
        db.close()
        return False, "Pesanan tidak ditemukan atau sudah diproses."

class UserModel:
    @staticmethod
    def register_user(username, password, role):
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM "user" WHERE username=%s', (username,))
        if cursor.fetchone():
            db.close()
            return False, "Username sudah terdaftar!"
        
        hashed_password = generate_password_hash(password)
        cursor.execute('INSERT INTO "user" (username, password, role) VALUES (%s, %s, %s)', 
                        (username, hashed_password, role))
        db.close()
        return True, "Registrasi berhasil!"

    @staticmethod
    def authenticate(username, password):
        db = get_db()
        if not db: return None
        with db.cursor() as cursor:
            cursor.execute('SELECT * FROM "user" WHERE username=%s', (username,))
            user = cursor.fetchone()
            
            if user and check_password_hash(user['password'], password):
                db.close()
                return user
        db.close()
        return None
    
    @staticmethod
    def get_user_profile(username):
        db = get_db()
        if not db: return None
        cursor = db.cursor()
        cursor.execute('SELECT id_user, username, role FROM "user" WHERE username=%s', (username,))
        user = cursor.fetchone()
        db.close()
        return user

    @staticmethod
    def update_password(username, new_password):
        db = get_db()
        if not db: return False
        cursor = db.cursor()
        hashed_pw = generate_password_hash(new_password)
        cursor.execute('UPDATE "user" SET password=%s WHERE username=%s', (hashed_pw, username))
        db.close()
        return True