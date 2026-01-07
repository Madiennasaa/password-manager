Hai! Selamat datang di repositori Manajer Kata Sandi pribadi saya. Ini adalah aplikasi desktop sederhana tapi aman yang saya buat menggunakan Python untuk menyimpan semua kredensial akun saya.

Dibanding menyimpan di sticky notes atau spreadsheet, aplikasi ini menggunakan kriptografi yang serius untuk memastikan data saya bener-bener aman dari mata-mata nakal.

🌟 Kenapa Aplikasi Ini Keren?
Pintu Gerbang Super Aman: Aplikasi dikunci dengan Kata Sandi Master. Sandi ini di-hash pakai Argon2 — ini seperti bouncer super kuat yang menjaga club data Anda.

Data Enkripsi Total: Semua password yang Anda simpan di MySQL akan diubah menjadi kode rahasia yang tidak bisa dibaca pakai Fernet (kriptografi serius, lho!).

Gak Bakal Lupa Kunci: Meskipun Anda tutup aplikasinya, kunci enkripsi yang diturunkan dari Sandi Master Anda akan selalu sama. Jadi, Anda tidak akan mengalami lagi drama "sandi tersimpan tapi tidak bisa dibuka" (kecuali Anda lupa Sandi Master Anda sendiri, ya!).

Anti-Ngadat: Semua tugas berat (seperti hashing dan komunikasi DB) dikerjakan di balik layar (menggunakan Worker Thread), jadi aplikasinya tetap lancar jaya dan gak bikin freeze.

Fitur Dasar Lengkap: Cari, Tambah, Edit, Hapus—semua ada.

💻 Resep Setup (Cara Menjalankan)
Ini yang Anda butuhkan sebelum bisa menjalankan aplikasinya.

1. Bahan-Bahan Dasar
Python 3.x

Server MySQL (Pastikan sudah running di PC Anda!)

2. Dapur SQL (Setup Database)
Aplikasi ini mencari database bernama password_manager. Anda bisa membuatnya cepat di MySQL client Anda (seperti HeidiSQL, DBeaver, dll.):

SQL

CREATE DATABASE password_manager;
3. Meracik Python
Instal semua library yang diperlukan:

Bash

# Pastikan Anda berada di folder proyek ini
pip install pyqt5 cryptography argon2-cffi mysql-connector-python
4. Panaskan Mesin!
Waktunya jalankan aplikasinya:

Bash

python main.py
👣 Petunjuk Penggunaan Singkat
Daftar Pertama: Jika ini pertama kali, Anda akan diminta membuat Kata Sandi Master. JANGAN SAMPAI LUPA!

Login Santai: Setiap kali buka, masukkan Sandi Master Anda.

Tambah Data: Klik Tambah Baru, masukkan Layanan (misalnya, Netflix), Username, dan Password asli. Lalu, klik Simpan.

Intip Rahasia: Pilih baris data, lalu klik Lihat PW untuk mendekripsi dan menampilkan sandi aslinya. Hanya Sandi Master yang benar yang bisa melakukannya.

Cari Cepat: Ketik nama layanan atau username di kolom pencarian, lalu tekan Cari.