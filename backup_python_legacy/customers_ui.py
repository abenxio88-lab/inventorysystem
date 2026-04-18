"""
Customer Management Module
===========================
Manage customer information and history.
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QDialog,
    QLineEdit, QTextEdit, QLabel, QPushButton
)
from PySide6.QtCore import Qt
import logging

from services import svc
from ui_theme import (
    make_card, styled_label, make_button,
    FONT_HEADING, FONT_BOLD, FONT_REGULAR,
    COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_TEXT_MUTED
)

logger = logging.getLogger(__name__)


def create_customers_tab(parent, current_user=None):
    """Create the Customers management tab."""
    frame = QFrame()
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(15, 15, 15, 15)

    # Header
    header_frame = QFrame()
    header_layout = QHBoxLayout(header_frame)
    header_layout.setContentsMargins(0, 0, 0, 0)

    styled_label(header_frame, "👥 Customer Management", font=FONT_HEADING)
    layout.addWidget(header_frame)

    # Toolbar
    toolbar = QFrame()
    toolbar_layout = QHBoxLayout(toolbar)
    toolbar_layout.setContentsMargins(0, 10, 0, 10)

    search_edit = QLineEdit()
    search_edit.setPlaceholderText("Search customers by name, phone, or email...")
    search_edit.setMinimumWidth(300)
    toolbar_layout.addWidget(search_edit)

    make_button(toolbar_layout, "➕ Add Customer", command=lambda: open_customer_dialog(frame, current_user), kind="primary")
    make_button(toolbar_layout, "🔄 Refresh", command=lambda: refresh_from_db(), kind="secondary")

    layout.addWidget(toolbar)

    # Customer table
    columns = ("name", "phone", "email", "address", "actions")
    tree = QTableWidget()
    tree.setColumnCount(len(columns))
    tree.setHorizontalHeaderLabels(["Name", "Phone", "Email", "Address", "Actions"])
    tree.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
    tree.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
    tree.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
    tree.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
    tree.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
    tree.setSelectionBehavior(QAbstractItemView.SelectRows)
    tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
    tree.verticalHeader().setVisible(False)

    layout.addWidget(tree)

    def refresh_from_db():
        tree.setRowCount(0)
        try:
            customers = svc.customer.get_all_customers()
            for row_idx, customer in enumerate(customers):
                tree.insertRow(row_idx)
                tree.setItem(row_idx, 0, QTableWidgetItem(customer.get('name', 'N/A')))
                tree.setItem(row_idx, 1, QTableWidgetItem(customer.get('phone', 'N/A')))
                tree.setItem(row_idx, 2, QTableWidgetItem(customer.get('email', 'N/A')))
                tree.setItem(row_idx, 3, QTableWidgetItem(customer.get('address', 'N/A')))
                
                # Action buttons
                actions_frame = QFrame()
                actions_layout = QHBoxLayout(actions_frame)
                actions_layout.setContentsMargins(5, 2, 5, 2)
                
                customer_data = customer
                
                edit_btn = QPushButton("Edit")
                edit_btn.setStyleSheet("color: #3B82F6;")
                edit_btn.clicked.connect(lambda checked, c=customer_data: open_customer_dialog(frame, current_user, mode="edit", data=c))
                actions_layout.addWidget(edit_btn)
                
                delete_btn = QPushButton("Delete")
                delete_btn.setStyleSheet("color: #EF4444;")
                delete_btn.clicked.connect(lambda checked, c=customer_data: delete_customer(c))
                actions_layout.addWidget(delete_btn)
                
                tree.setCellWidget(row_idx, 4, actions_frame)
        except Exception as e:
            logger.error(f"Failed to load customers: {e}")
            QMessageBox.critical(frame, "Error", f"Failed to load customers: {e}")

    def delete_customer(customer):
        reply = QMessageBox.question(
            frame, "Confirm Delete",
            f"Are you sure you want to delete customer '{customer.get('name')}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                svc.customer.delete_customer(customer.get('id'))
                QMessageBox.information(frame, "Success", "Customer deleted successfully")
                refresh_from_db()
            except Exception as e:
                logger.error(f"Failed to delete customer: {e}")
                QMessageBox.critical(frame, "Error", f"Failed to delete customer: {e}")

    def open_customer_dialog(parent_window, user, mode="add", data=None):
        """Dialog to add or edit customer."""
        dlg = QDialog(parent_window)
        dlg.setWindowTitle("Edit Customer" if mode == "edit" else "Add Customer")
        dlg.resize(600, 500)
        dlg.setModal(True)

        main_layout = QVBoxLayout(dlg)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Form card
        form_card = make_card(dlg, padding=20)
        form_layout = QVBoxLayout(form_card)
        main_layout.addWidget(form_card)

        # Name
        name_label = styled_label(form_card, "Customer Name *:", font=FONT_BOLD)
        form_layout.addWidget(name_label)
        name_edit = QLineEdit()
        name_edit.setMinimumHeight(35)
        form_layout.addWidget(name_edit)

        # Phone
        phone_label = styled_label(form_card, "Phone:", font=FONT_BOLD)
        form_layout.addWidget(phone_label)
        phone_edit = QLineEdit()
        phone_edit.setMinimumHeight(35)
        form_layout.addWidget(phone_edit)

        # Email
        email_label = styled_label(form_card, "Email:", font=FONT_BOLD)
        form_layout.addWidget(email_label)
        email_edit = QLineEdit()
        email_edit.setMinimumHeight(35)
        form_layout.addWidget(email_edit)

        # Address
        address_label = styled_label(form_card, "Address:", font=FONT_BOLD)
        form_layout.addWidget(address_label)
        address_edit = QTextEdit()
        address_edit.setMaximumHeight(80)
        form_layout.addWidget(address_edit)

        # Notes
        notes_label = styled_label(form_card, "Notes:", font=FONT_BOLD)
        form_layout.addWidget(notes_label)
        notes_edit = QTextEdit()
        notes_edit.setMaximumHeight(80)
        form_layout.addWidget(notes_edit)

        # If editing, populate fields
        if mode == "edit" and data:
            name_edit.setText(data.get('name', ''))
            phone_edit.setText(data.get('phone', ''))
            email_edit.setText(data.get('email', ''))
            address_edit.setText(data.get('address', ''))
            notes_edit.setText(data.get('notes', ''))

        # Buttons
        btn_frame = QFrame()
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(0, 15, 0, 0)
        main_layout.addWidget(btn_frame)

        def save_customer():
            name = name_edit.text().strip()
            if not name:
                QMessageBox.critical(dlg, "Error", "Customer name is required")
                return

            customer_data = {
                'name': name,
                'phone': phone_edit.text().strip(),
                'email': email_edit.text().strip(),
                'address': address_edit.toPlainText().strip(),
                'notes': notes_edit.toPlainText().strip(),
            }

            try:
                if mode == "edit":
                    svc.customer.update_customer(data.get('id'), customer_data)
                    QMessageBox.information(dlg, "Success", "Customer updated successfully")
                else:
                    svc.customer.create_customer(customer_data)
                    QMessageBox.information(dlg, "Success", "Customer added successfully")
                
                dlg.accept()
                refresh_from_db()
            except Exception as e:
                logger.error(f"Failed to save customer: {e}")
                QMessageBox.critical(dlg, "Error", f"Failed to save customer: {e}")

        save_btn = make_button(btn_frame, "Save", command=save_customer, kind="success")
        btn_layout.addWidget(save_btn)
        
        cancel_btn = make_button(btn_frame, "Cancel", command=dlg.reject, kind="secondary")
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        
        dlg.setLayout(main_layout)
        dlg.exec()

    # Search functionality
    search_edit.textChanged.connect(lambda text: filter_customers(text))

    def filter_customers(search_text):
        tree.setRowCount(0)
        try:
            customers = svc.customer.get_all_customers()
            if search_text:
                customers = [
                    c for c in customers
                    if search_text.lower() in c.get('name', '').lower()
                    or search_text.lower() in c.get('phone', '').lower()
                    or search_text.lower() in c.get('email', '').lower()
                ]
            
            for row_idx, customer in enumerate(customers):
                tree.insertRow(row_idx)
                tree.setItem(row_idx, 0, QTableWidgetItem(customer.get('name', 'N/A')))
                tree.setItem(row_idx, 1, QTableWidgetItem(customer.get('phone', 'N/A')))
                tree.setItem(row_idx, 2, QTableWidgetItem(customer.get('email', 'N/A')))
                tree.setItem(row_idx, 3, QTableWidgetItem(customer.get('address', 'N/A')))
                
                actions_frame = QFrame()
                actions_layout = QHBoxLayout(actions_frame)
                actions_layout.setContentsMargins(5, 2, 5, 2)
                
                customer_data = customer
                
                edit_btn = QPushButton("Edit")
                edit_btn.setStyleSheet("color: #3B82F6;")
                edit_btn.clicked.connect(lambda checked, c=customer_data: open_customer_dialog(frame, current_user, mode="edit", data=c))
                actions_layout.addWidget(edit_btn)
                
                delete_btn = QPushButton("Delete")
                delete_btn.setStyleSheet("color: #EF4444;")
                delete_btn.clicked.connect(lambda checked, c=customer_data: delete_customer(c))
                actions_layout.addWidget(delete_btn)
                
                tree.setCellWidget(row_idx, 4, actions_frame)
        except Exception as e:
            logger.error(f"Failed to filter customers: {e}")

    # Initial load
    refresh_from_db()

    return frame
