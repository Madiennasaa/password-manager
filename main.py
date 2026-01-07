import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QDialog, QAbstractItemView, QHeaderView, QProgressDialog
)
from PyQt5.QtCore import Qt, QThreadPool, pyqtSlot

from worker import Worker
from util import decrypt_password, derive_fernet_key
from modul.query import (
    insert_new_entry, get_all_entries, delete_entry, update_entry,
    check_if_user_exists, register_master_user, authenticate_user
)

threadpool = QThreadPool.globalInstance()


class BaseAuthDialog(QDialog):
    def __init__(self, parent, title, button_text, action_callback):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.action_callback = action_callback
        self.setWindowModality(Qt.ApplicationModal)

        layout = QVBoxLayout(self)
        form_layout = QHBoxLayout()

        self.pwd_entry = QLineEdit()
        self.pwd_entry.setEchoMode(QLineEdit.Password)
        self.pwd_entry.setPlaceholderText("Masukkan Kata Sandi Master")

        form_layout.addWidget(QLabel("Kata Sandi Master:"))
        form_layout.addWidget(self.pwd_entry)

        self.action_button = QPushButton(button_text)
        self.action_button.clicked.connect(self.process_action)

        layout.addLayout(form_layout)
        layout.addWidget(self.action_button)

        self.pwd_entry.returnPressed.connect(self.process_action)

    def process_action(self):
        password = self.pwd_entry.text()
        if not password:
            QMessageBox.warning(self, "Peringatan", "Kata Sandi tidak boleh kosong.")
            return

        self.action_button.setEnabled(False)
        self.pwd_entry.setEnabled(False)

        worker = Worker(self._run_auth_action, password)
        worker.signals.finished.connect(self.handle_auth_result)
        threadpool.start(worker)

    def _run_auth_action(self, password):
        return self.action_callback(password)

    @pyqtSlot(bool, object)
    def handle_auth_result(self, success, result):
        if success:
            if result is not False:
                app_instance = QApplication.instance()
                app_instance.fernet_key = result
                self.accept()
            else:
                QMessageBox.critical(self, "Gagal", "Otentikasi Gagal.")
                self.action_button.setEnabled(True)
                self.pwd_entry.setEnabled(True)
        else:
            QMessageBox.critical(self, "Kesalahan", f"Kesalahan Otentikasi: {result}")
            self.action_button.setEnabled(True)
            self.pwd_entry.setEnabled(True)

    def closeEvent(self, event):
        sys.exit()


class RegisterDialog(BaseAuthDialog):
    def __init__(self, parent):
        super().__init__(parent, "Daftar Kata Sandi Master", "Daftar", self._register_user_logic)

    def _register_user_logic(self, password):
        if len(password) < 8:
            return False
        if register_master_user(password):
            return derive_fernet_key(password)
        return False


class LoginDialog(BaseAuthDialog):
    def __init__(self, parent):
        super().__init__(parent, "Login", "Masuk", self._login_user_logic)

    def _login_user_logic(self, password):
        if authenticate_user(password):
            return derive_fernet_key(password)
        return False


class EntryDialog(QDialog):
    def __init__(self, parent, master_key, entry_data=None):
        super().__init__(parent)
        self.master_key = master_key
        self.entry_id = entry_data.get("id") if entry_data else None

        is_edit = self.entry_id is not None
        self.setWindowTitle("Edit Entri" if is_edit else "Tambah Entri Baru")

        layout = QVBoxLayout(self)

        self.service_entry = QLineEdit(entry_data.get("service", "") if entry_data else "")
        self.username_entry = QLineEdit(entry_data.get("username", "") if entry_data else "")
        self.password_entry = QLineEdit()
        self.password_entry.setEchoMode(QLineEdit.Password)

        if is_edit:
            encrypted_pwd = entry_data.get("encrypted_password")
            if encrypted_pwd:
                try:
                    decrypted_pwd = decrypt_password(encrypted_pwd, self.master_key)
                    self.password_entry.setText(decrypted_pwd)
                except Exception as e:
                    QMessageBox.critical(self, "Kesalahan Kripto", str(e))

        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.addWidget(QLabel("Layanan:"))
        form_layout.addWidget(self.service_entry)
        form_layout.addWidget(QLabel("Username/Email:"))
        form_layout.addWidget(self.username_entry)
        form_layout.addWidget(QLabel("Kata Sandi:"))
        form_layout.addWidget(self.password_entry)
        layout.addWidget(form_widget)

        btn_layout = QHBoxLayout()
        self.save_button = QPushButton("Simpan")
        self.save_button.clicked.connect(self.save_entry)
        self.cancel_button = QPushButton("Batal")
        self.cancel_button.clicked.connect(self.reject)

        btn_layout.addStretch(1)
        btn_layout.addWidget(self.save_button)
        btn_layout.addWidget(self.cancel_button)
        layout.addLayout(btn_layout)

    def save_entry(self):
        service = self.service_entry.text().strip()
        username = self.username_entry.text().strip()
        password = self.password_entry.text()

        if not (service and username and password):
            QMessageBox.warning(self, "Peringatan", "Semua kolom harus diisi.")
            return

        self.save_button.setEnabled(False)

        if self.entry_id is None:
            worker = Worker(insert_new_entry, service, username, password, self.master_key)
        else:
            worker = Worker(update_entry, self.entry_id, service, username, password, self.master_key)

        worker.signals.finished.connect(self.handle_save_result)
        threadpool.start(worker)

    @pyqtSlot(bool, object)
    def handle_save_result(self, success, result):
        self.save_button.setEnabled(True)
        if success:
            QMessageBox.information(self, "Sukses", "Data berhasil disimpan.")
            self.accept()
        else:
            QMessageBox.critical(self, "Kesalahan", str(result))


class PasswordManagerApp(QMainWindow):
    def __init__(self, fernet_key):
        super().__init__()
        self.setWindowTitle("Manajer Kata Sandi Aman (PyQt5)")
        self.master_key = fernet_key
        self.is_loading = False
        self.current_sort_key = "service"

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.setup_ui()
        self.start_load_passwords_thread()

    def setup_ui(self):
        search_widget = QWidget()
        search_layout = QHBoxLayout(search_widget)

        self.search_entry = QLineEdit()
        self.search_entry.returnPressed.connect(self.start_load_passwords_thread)

        self.search_button = QPushButton("Cari")
        self.search_button.clicked.connect(self.start_load_passwords_thread)

        self.reset_button = QPushButton("Reset Filter")
        self.reset_button.clicked.connect(self.reset_search)

        search_layout.addWidget(QLabel("Cari:"))
        search_layout.addWidget(self.search_entry)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.reset_button)
        self.main_layout.addWidget(search_widget)

        btn_widget = QWidget()
        btn_layout = QHBoxLayout(btn_widget)

        self.add_btn = QPushButton("Tambah Baru")
        self.add_btn.clicked.connect(self.add_new_entry)

        self.reload_btn = QPushButton("Muat Ulang")
        self.reload_btn.clicked.connect(self.start_load_passwords_thread)

        self.edit_btn = QPushButton("Edit Terpilih")
        self.edit_btn.clicked.connect(self.edit_selected_entry)

        self.decrypt_btn = QPushButton("Lihat PW")
        self.decrypt_btn.clicked.connect(self.view_password)

        self.delete_btn = QPushButton("Hapus Terpilih")
        self.delete_btn.clicked.connect(self.delete_selected_entry)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.reload_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.decrypt_btn)
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.delete_btn)

        self.main_layout.addWidget(btn_widget)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Layanan", "Username", "Kata Sandi"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.main_layout.addWidget(self.table)

        self.progress_bar = QProgressDialog("Memuat data...", None, 0, 0, self)
        self.progress_bar.setWindowModality(Qt.WindowModal)
        self.progress_bar.hide()

    def start_load_passwords_thread(self):
        if self.is_loading:
            return

        self.is_loading = True
        self.progress_bar.show()
        self.setCursor(Qt.WaitCursor)

        keyword = self.search_entry.text()
        worker = Worker(get_all_entries, self.current_sort_key, keyword)
        worker.signals.finished.connect(self._update_table_from_results)
        threadpool.start(worker)

    @pyqtSlot(bool, object)
    def _update_table_from_results(self, success, results):
        self.is_loading = False
        self.progress_bar.hide()
        self.setCursor(Qt.ArrowCursor)

        if success:
            self._populate_table(results)
        else:
            QMessageBox.critical(self, "Kesalahan", str(results))

    def _populate_table(self, results):
        self.table.setRowCount(len(results))
        for row, data in enumerate(results):
            self.table.setItem(row, 0, QTableWidgetItem(str(data["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(data["service"]))
            self.table.setItem(row, 2, QTableWidgetItem(data["username"]))

            pwd_item = QTableWidgetItem("********")
            pwd_item.setData(Qt.UserRole, data["encrypted_password"])
            self.table.setItem(row, 3, pwd_item)

    def reset_search(self):
        self.search_entry.clear()
        self.start_load_passwords_thread()

    def add_new_entry(self):
        dialog = EntryDialog(self, self.master_key)
        if dialog.exec_() == QDialog.Accepted:
            self.start_load_passwords_thread()

    def edit_selected_entry(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.warning(self, "Peringatan", "Pilih satu baris.")
            return

        r = rows[0].row()
        entry_data = {
            "id": int(self.table.item(r, 0).text()),
            "service": self.table.item(r, 1).text(),
            "username": self.table.item(r, 2).text(),
            "encrypted_password": self.table.item(r, 3).data(Qt.UserRole)
        }

        dialog = EntryDialog(self, self.master_key, entry_data)
        if dialog.exec_() == QDialog.Accepted:
            self.start_load_passwords_thread()

    def delete_selected_entry(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return

        r = rows[0].row()
        entry_id = int(self.table.item(r, 0).text())

        worker = Worker(delete_entry, entry_id)
        worker.signals.finished.connect(self.handle_delete_result)
        threadpool.start(worker)

    @pyqtSlot(bool, object)
    def handle_delete_result(self, success, result):
        if success:
            self.start_load_passwords_thread()

    def view_password(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Peringatan", "Pilih satu baris untuk melihat sandi.")
            return

        row_index = selected_rows[0].row()
        item_pwd = self.table.item(row_index, 3)
        encrypted_pwd = item_pwd.data(Qt.UserRole)
        service = self.table.item(row_index, 1).text()

        if encrypted_pwd:
            try:
                decrypted_pwd = decrypt_password(encrypted_pwd, self.master_key)
                
                QMessageBox.information(self, f"Kata Sandi untuk {service}",
                    f"Kata Sandi: \n\n-- {decrypted_pwd} --", QMessageBox.Ok)
            
            except Exception as e:
                QMessageBox.critical(self, "Kesalahan Dekripsi", f"Gagal mendekripsi kata sandi. (Coba buat entri baru): {e}")
        else:
             QMessageBox.warning(self, "Kesalahan", "Data sandi terenkripsi tidak ditemukan.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.fernet_key = None

    if not check_if_user_exists():
        if RegisterDialog(None).exec_() != QDialog.Accepted:
            sys.exit()
    else:
        if LoginDialog(None).exec_() != QDialog.Accepted:
            sys.exit()

    if app.fernet_key:
        window = PasswordManagerApp(app.fernet_key)
        window.show()
        sys.exit(app.exec_())
