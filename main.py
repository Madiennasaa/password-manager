import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QDialog, QAbstractItemView, QHeaderView, QProgressDialog,
    QFrame
)
from PyQt5.QtCore import Qt, QThreadPool, pyqtSlot, QSize
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QPixmap, QPainter

from worker import Worker
from util import decrypt_password, derive_fernet_key
from modul.query import (
    insert_new_entry, get_all_entries, delete_entry, update_entry,
    check_if_user_exists, register_master_user, authenticate_user
)

threadpool = QThreadPool.globalInstance()

# Professional Modern Design - Clean & Corporate
GLOBAL_STYLE = """
    QMainWindow, QDialog {
        background-color: #f5f7fa;
    }
    
    QLabel {
        color: #2c3e50;
        font-size: 13px;
    }
    
    QLineEdit {
        background-color: #ffffff;
        border: 2px solid #e1e8ed;
        border-radius: 6px;
        padding: 10px 14px;
        color: #2c3e50;
        font-size: 14px;
        selection-background-color: #3498db;
    }
    
    QLineEdit:focus {
        border: 2px solid #3498db;
        background-color: #ffffff;
    }
    
    QLineEdit:hover {
        border: 2px solid #bdc3c7;
    }
    
    QPushButton {
        background-color: #3498db;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 10px 20px;
        font-size: 13px;
        font-weight: 600;
        min-height: 36px;
    }
    
    QPushButton:hover {
        background-color: #2980b9;
    }
    
    QPushButton:pressed {
        background-color: #21618c;
    }
    
    QPushButton:disabled {
        background-color: #bdc3c7;
        color: #7f8c8d;
    }
    
    QPushButton#secondaryButton {
        background-color: #ecf0f1;
        color: #2c3e50;
        border: 1px solid #bdc3c7;
    }
    
    QPushButton#secondaryButton:hover {
        background-color: #d5dbdb;
    }
    
    QPushButton#secondaryButton:pressed {
        background-color: #bdc3c7;
    }
    
    QPushButton#dangerButton {
        background-color: #e74c3c;
        color: white;
    }
    
    QPushButton#dangerButton:hover {
        background-color: #c0392b;
    }
    
    QTableWidget {
        background-color: white;
        border: 1px solid #e1e8ed;
        border-radius: 8px;
        gridline-color: #ecf0f1;
        color: #2c3e50;
        font-size: 13px;
    }
    
    QTableWidget::item {
        padding: 12px;
        border-bottom: 1px solid #ecf0f1;
    }
    
    QTableWidget::item:selected {
        background-color: #ebf5fb;
        color: #2c3e50;
    }
    
    QTableWidget::item:hover {
        background-color: #f8f9fa;
    }
    
    QHeaderView::section {
        background-color: #34495e;
        color: white;
        padding: 12px;
        border: none;
        font-weight: 600;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    QHeaderView::section:first {
        border-top-left-radius: 7px;
    }
    
    QHeaderView::section:last {
        border-top-right-radius: 7px;
    }
    
    QFrame#card {
        background-color: white;
        border-radius: 8px;
        border: 1px solid #e1e8ed;
    }
"""


class BaseAuthDialog(QDialog):
    def __init__(self, parent, title, button_text, action_callback):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.action_callback = action_callback
        self.setWindowModality(Qt.ApplicationModal)
        self.setFixedWidth(420)
        self.setStyleSheet(GLOBAL_STYLE)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Logo area
        icon_label = QLabel("🔐")
        icon_label.setStyleSheet("""
            font-size: 48px;
            background-color: #3498db;
            border-radius: 12px;
            padding: 20px;
        """)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFixedHeight(100)
        layout.addWidget(icon_label)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: 600;
            color: #2c3e50;
            margin-top: 10px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Subtitle
        subtitle = QLabel("Enter your master password to continue")
        subtitle.setStyleSheet("""
            font-size: 13px;
            color: #7f8c8d;
            margin-bottom: 10px;
        """)
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        # Password field
        pwd_label = QLabel("Master Password")
        pwd_label.setStyleSheet("font-weight: 600; font-size: 13px; color: #34495e;")
        
        self.pwd_entry = QLineEdit()
        self.pwd_entry.setEchoMode(QLineEdit.Password)
        self.pwd_entry.setPlaceholderText("Enter your master password")
        self.pwd_entry.setMinimumHeight(42)

        layout.addWidget(pwd_label)
        layout.addWidget(self.pwd_entry)

        # Button
        self.action_button = QPushButton(button_text)
        self.action_button.clicked.connect(self.process_action)
        self.action_button.setMinimumHeight(44)
        self.action_button.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.action_button)

        # Info text
        info_label = QLabel("Your password is encrypted and secure")
        info_label.setStyleSheet("""
            font-size: 11px;
            color: #95a5a6;
            margin-top: 5px;
        """)
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)

        self.pwd_entry.returnPressed.connect(self.process_action)

    def process_action(self):
        password = self.pwd_entry.text()
        if not password:
            QMessageBox.warning(self, "Warning", "Password cannot be empty.")
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
                QMessageBox.critical(self, "Authentication Failed", "Invalid password. Please try again.")
                self.action_button.setEnabled(True)
                self.pwd_entry.setEnabled(True)
        else:
            QMessageBox.critical(self, "Error", f"Authentication error:\n{result}")
            self.action_button.setEnabled(True)
            self.pwd_entry.setEnabled(True)

    def closeEvent(self, event):
        sys.exit()


class RegisterDialog(BaseAuthDialog):
    def __init__(self, parent):
        super().__init__(parent, "Create Account", "Register", self._register_user_logic)

    def _register_user_logic(self, password):
        if len(password) < 8:
            return False
        if register_master_user(password):
            return derive_fernet_key(password)
        return False


class LoginDialog(BaseAuthDialog):
    def __init__(self, parent):
        super().__init__(parent, "Welcome Back", "Sign In", self._login_user_logic)

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
        self.setWindowTitle("Edit Entry" if is_edit else "New Entry")
        self.setFixedWidth(480)
        self.setStyleSheet(GLOBAL_STYLE)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Header
        title_label = QLabel("Edit Entry" if is_edit else "Add New Entry")
        title_label.setStyleSheet("""
            font-size: 20px;
            font-weight: 600;
            color: #2c3e50;
        """)
        layout.addWidget(title_label)

        subtitle = QLabel("Update entry details" if is_edit else "Create a new password entry")
        subtitle.setStyleSheet("""
            font-size: 13px;
            color: #7f8c8d;
            margin-bottom: 10px;
        """)
        layout.addWidget(subtitle)

        # Form
        service_label = QLabel("Service Name")
        service_label.setStyleSheet("font-weight: 600; font-size: 13px; color: #34495e;")
        self.service_entry = QLineEdit(entry_data.get("service", "") if entry_data else "")
        self.service_entry.setPlaceholderText("e.g., Gmail, Facebook")
        self.service_entry.setMinimumHeight(40)
        layout.addWidget(service_label)
        layout.addWidget(self.service_entry)

        username_label = QLabel("Username/Email")
        username_label.setStyleSheet("font-weight: 600; font-size: 13px; color: #34495e;")
        self.username_entry = QLineEdit(entry_data.get("username", "") if entry_data else "")
        self.username_entry.setPlaceholderText("e.g., user@email.com")
        self.username_entry.setMinimumHeight(40)
        layout.addWidget(username_label)
        layout.addWidget(self.username_entry)

        password_label = QLabel("Password")
        password_label.setStyleSheet("font-weight: 600; font-size: 13px; color: #34495e;")
        self.password_entry = QLineEdit()
        self.password_entry.setEchoMode(QLineEdit.Password)
        self.password_entry.setPlaceholderText("Enter password for this service")
        self.password_entry.setMinimumHeight(40)

        if is_edit:
            encrypted_pwd = entry_data.get("encrypted_password")
            if encrypted_pwd:
                try:
                    decrypted_pwd = decrypt_password(encrypted_pwd, self.master_key)
                    self.password_entry.setText(decrypted_pwd)
                except Exception as e:
                    QMessageBox.critical(self, "Decryption Error", str(e))

        layout.addWidget(password_label)
        layout.addWidget(self.password_entry)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("secondaryButton")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.setMinimumHeight(40)
        
        self.save_button = QPushButton("Save Entry")
        self.save_button.clicked.connect(self.save_entry)
        self.save_button.setMinimumHeight(40)
        self.save_button.setCursor(Qt.PointingHandCursor)

        btn_layout.addWidget(self.cancel_button)
        btn_layout.addWidget(self.save_button)
        layout.addLayout(btn_layout)

    def save_entry(self):
        service = self.service_entry.text().strip()
        username = self.username_entry.text().strip()
        password = self.password_entry.text()

        if not (service and username and password):
            QMessageBox.warning(self, "Warning", "All fields are required.")
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
            QMessageBox.information(self, "Success", "Entry saved successfully!")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", str(result))


class PasswordManagerApp(QMainWindow):
    def __init__(self, fernet_key):
        super().__init__()
        self.setWindowTitle("SecureVault Pro - Password Manager")
        self.master_key = fernet_key
        self.is_loading = False
        self.current_sort_key = "service"
        self.setMinimumSize(1000, 650)
        self.setStyleSheet(GLOBAL_STYLE)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(30, 30, 30, 30)

        self.setup_ui()
        self.start_load_passwords_thread()

    def setup_ui(self):
        # Header
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 15)
        
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(2)
        
        app_title = QLabel("SecureVault Pro")
        app_title.setStyleSheet("""
            font-size: 28px;
            font-weight: 600;
            color: #2c3e50;
        """)
        
        tagline = QLabel("Professional Password Management")
        tagline.setStyleSheet("""
            font-size: 14px;
            color: #7f8c8d;
        """)
        
        title_layout.addWidget(app_title)
        title_layout.addWidget(tagline)
        
        stats_label = QLabel("🔒 AES-256 Encrypted")
        stats_label.setStyleSheet("""
            background-color: #ecf0f1;
            color: #34495e;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 12px;
            border: 1px solid #bdc3c7;
        """)
        stats_label.setFixedHeight(36)
        
        header_layout.addWidget(title_container)
        header_layout.addStretch()
        header_layout.addWidget(stats_label)
        
        self.main_layout.addWidget(header_widget)

        # Search card
        search_card = QFrame()
        search_card.setObjectName("card")
        search_card.setStyleSheet("""
            QFrame#card {
                background-color: white;
                border-radius: 8px;
                padding: 16px;
                border: 1px solid #e1e8ed;
            }
        """)
        search_layout = QHBoxLayout(search_card)
        search_layout.setSpacing(10)
        
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Search services, usernames, or keywords...")
        self.search_entry.returnPressed.connect(self.start_load_passwords_thread)
        self.search_entry.setMinimumHeight(40)

        self.search_button = QPushButton("Search")
        self.search_button.setMaximumWidth(100)
        self.search_button.clicked.connect(self.start_load_passwords_thread)
        self.search_button.setCursor(Qt.PointingHandCursor)
        
        self.reset_button = QPushButton("Reset")
        self.reset_button.setObjectName("secondaryButton")
        self.reset_button.setMaximumWidth(80)
        self.reset_button.clicked.connect(self.reset_search)
        self.reset_button.setCursor(Qt.PointingHandCursor)

        search_layout.addWidget(self.search_entry)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.reset_button)
        self.main_layout.addWidget(search_card)

        # Action buttons
        btn_widget = QWidget()
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setSpacing(10)

        self.add_btn = QPushButton("+ Add New")
        self.add_btn.clicked.connect(self.add_new_entry)
        self.add_btn.setCursor(Qt.PointingHandCursor)

        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setObjectName("secondaryButton")
        self.edit_btn.clicked.connect(self.edit_selected_entry)
        self.edit_btn.setCursor(Qt.PointingHandCursor)

        self.decrypt_btn = QPushButton("View Password")
        self.decrypt_btn.setObjectName("secondaryButton")
        self.decrypt_btn.clicked.connect(self.view_password)
        self.decrypt_btn.setCursor(Qt.PointingHandCursor)

        self.reload_btn = QPushButton("Refresh")
        self.reload_btn.setObjectName("secondaryButton")
        self.reload_btn.clicked.connect(self.start_load_passwords_thread)
        self.reload_btn.setCursor(Qt.PointingHandCursor)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setObjectName("dangerButton")
        self.delete_btn.clicked.connect(self.delete_selected_entry)
        self.delete_btn.setCursor(Qt.PointingHandCursor)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.decrypt_btn)
        btn_layout.addWidget(self.reload_btn)
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.delete_btn)

        self.main_layout.addWidget(btn_widget)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "SERVICE", "USERNAME", "PASSWORD"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        self.main_layout.addWidget(self.table)

        # Footer
        footer_label = QLabel("All data is encrypted end-to-end using AES-256 encryption")
        footer_label.setStyleSheet("""
            font-size: 11px;
            color: #95a5a6;
            padding: 10px;
        """)
        footer_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(footer_label)

        self.progress_bar = QProgressDialog("Loading data...", None, 0, 0, self)
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
            QMessageBox.critical(self, "Error", str(results))

    def _populate_table(self, results):
        self.table.setRowCount(len(results))
        for row, data in enumerate(results):
            id_item = QTableWidgetItem(str(data["id"]))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, id_item)
            
            self.table.setItem(row, 1, QTableWidgetItem(data["service"]))
            self.table.setItem(row, 2, QTableWidgetItem(data["username"]))

            pwd_item = QTableWidgetItem("••••••••")
            pwd_item.setTextAlignment(Qt.AlignCenter)
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
            QMessageBox.warning(self, "Warning", "Please select an entry to edit.")
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
            QMessageBox.warning(self, "Warning", "Please select an entry to delete.")
            return

        r = rows[0].row()
        entry_id = int(self.table.item(r, 0).text())
        service = self.table.item(r, 1).text()

        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("Confirm Delete")
        msg_box.setText(f"Are you sure you want to delete '{service}'?")
        msg_box.setInformativeText("This action cannot be undone.")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)

        if msg_box.exec_() == QMessageBox.Yes:
            worker = Worker(delete_entry, entry_id)
            worker.signals.finished.connect(self.handle_delete_result)
            threadpool.start(worker)

    @pyqtSlot(bool, object)
    def handle_delete_result(self, success, result):
        if success:
            QMessageBox.information(self, "Success", "Entry deleted successfully.")
            self.start_load_passwords_thread()

    def view_password(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "Please select an entry to view password.")
            return

        row_index = selected_rows[0].row()
        item_pwd = self.table.item(row_index, 3)
        encrypted_pwd = item_pwd.data(Qt.UserRole)
        service = self.table.item(row_index, 1).text()

        if encrypted_pwd:
            try:
                decrypted_pwd = decrypt_password(encrypted_pwd, self.master_key)
                
                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Information)
                msg_box.setWindowTitle(f"Password - {service}")
                msg_box.setText(f"Password for: {service}")
                msg_box.setInformativeText(f"\n{decrypted_pwd}\n")
                msg_box.setStandardButtons(QMessageBox.Ok)
                msg_box.setTextInteractionFlags(Qt.TextSelectableByMouse)
                msg_box.exec_()
            
            except Exception as e:
                QMessageBox.critical(self, "Decryption Error", 
                    f"Failed to decrypt password.\n\nDetails: {e}")
        else:
            QMessageBox.warning(self, "Error", "Encrypted password data not found.")


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