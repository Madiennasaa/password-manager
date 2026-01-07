# 🛡️ Manajer Kata Sandi Aman (PyQt5 & MySQL)

Aplikasi desktop Manajer Kata Sandi yang dirancang untuk menyimpan kredensial akun secara lokal di database MySQL dengan keamanan tingkat tinggi.

## ✨ Fitur Utama

* **Autentikasi Aman (Argon2):** Kata Sandi Master pengguna di-*hash* menggunakan **Argon2**, salah satu fungsi *Key Derivation* dan *Hashing* sandi terkuat yang direkomendasikan saat ini.
* **Enkripsi Data (Fernet):** Semua kata sandi sensitif dienkripsi menggunakan standar kriptografi **Fernet (AES 128-bit CBC)** sebelum disimpan sebagai *BLOB* di database MySQL.
* **Kunci Deterministik (SHA256):** Kunci enkripsi Fernet diturunkan secara konsisten dari Kata Sandi Master menggunakan **SHA256**. Ini memastikan Anda dapat mendekripsi data Anda dengan benar setiap kali Anda masuk.
* **UI Responsif (PyQt5 & Threading):** Semua operasi I/O yang memakan waktu (koneksi DB, *hashing*, enkripsi) dijalankan pada *Worker Thread* (`QRunnable`) untuk menjaga antarmuka pengguna tetap lancar.
* **Operasi CRUD Lengkap:** Mendukung penambahan, melihat, pembaruan, dan penghapusan entri kata sandi.
* **Fungsi Pencarian:** Filter cepat berdasarkan Layanan (*Service*) atau *Username*.

## 🛠️ Teknologi dan Dependensi

* **Python** (3.x)
* **PyQt5** (GUI Framework)
* **MySQL** (Database Backend)
* **`cryptography`** (Pustaka untuk Fernet)
* **`argon2-cffi`** (Pustaka untuk *Hashing* Master Password)
* **`mysql-connector-python`** (Konektor Database)

## ⚙️ Instalasi dan Setup

Ikuti langkah-langkah berikut untuk menginstal dan menjalankan aplikasi.

### 1. Setup Database MySQL

Aplikasi ini memerlukan server MySQL yang berjalan dan terhubung ke database bernama `password_manager`.

1. Pastikan Server MySQL Anda berjalan.
2. Buka klien MySQL Anda (Terminal, Workbench, atau Navicat).
3. Buat database yang diperlukan:
```sql
CREATE DATABASE IF NOT EXISTS password_manager;

```


4. Verifikasi kredensial di `db.py` (secara *default* menggunakan `user='root', password=''`).

### 2. Instalasi Dependensi Python

Navigasi ke direktori proyek dan instal semua kebutuhan melalui `pip`.

```bash
# Pastikan Anda telah membuat virtual environment (opsional, tapi disarankan)
pip install pyqt5 cryptography argon2-cffi mysql-connector-python

```

### 3. Menjalankan Aplikasi

Jalankan *file* utama:

```bash
python main.py

```

## 🚀 Panduan Penggunaan

1. **Pendaftaran Awal:** Saat dijalankan pertama kali, aplikasi akan mendeteksi tidak adanya `Master User` dan meminta Anda mendaftarkan Kata Sandi Master.
2. **Login:** Gunakan Kata Sandi Master yang telah Anda daftarkan untuk masuk. Kunci enkripsi akan diturunkan dari sandi ini.
3. **Mengelola Entri:**
* Klik **Tambah Baru** untuk memasukkan kredensial baru.
* Pilih baris dan klik **Lihat PW** untuk mendekripsi dan menampilkan kata sandi yang tersimpan.



## ❗️ Penting: Kesalahan Dekripsi Entri Lama

Jika Anda mencoba mendekripsi entri yang dibuat **sebelum** perbaikan *key derivation* pada `util.py` (yaitu, sebelum *commit* yang memperbaiki masalah kunci non-deterministik), Anda akan mendapatkan kesalahan dekripsi.

* Ini adalah perilaku yang diharapkan, karena kunci enkripsi lama tidak dapat direplikasi.
* **Solusi:** Hapus entri yang lama dan masukkan kembali data tersebut. Semua entri yang dibuat dengan kode versi terbaru ini akan dijamin dapat diakses kembali.

---

## 🤝 Kontribusi

Jika Anda menemukan *bug* atau memiliki saran perbaikan, jangan ragu untuk membuka *Issue* atau mengirimkan *Pull Request*.