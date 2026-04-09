"""
Mintaka Sphere - Tab Management Utilities
=========================================
Handles dynamic insertion of industry-specific tabs.
"""
import logging
from PySide6 import QtWidgets, QtCore, QtGui

def add_industry_tabs(notebook, industry_id, username):
    """Adds industry-specific tabs to the notebook based on current mode.

    All dynamically added tabs are tagged with 'dynamic' so that
    reload_industry_tabs() can safely identify and remove them.

    Duplicate guard: skips adding a tab if one with the same text already exists.
    """

    def _tab_exists(text: str) -> bool:
        """Check if a tab with the given text already exists."""
        for i in range(notebook.count()):
            if notebook.tabText(i).strip() == text.strip():
                return True
        return False

    if industry_id == "pharma":
        if _tab_exists("💊 Pharma"):
            logging.info("⏭️ Pharma tab already exists, skipping")
            return
        try:
            from pharmacy_ui import create_pharma_tab
            pharma_frame = create_pharma_tab(notebook, current_user=username)
            notebook.addTab(pharma_frame, " 💊 Pharma ")
            _tag_last_tab(notebook, "dynamic")
            logging.info("✅ Added Pharma tab")
        except Exception as e:
            logging.warning(f"Pharma tab not available: {e}")

    elif industry_id == "lease_rental":
        if _tab_exists("📋 Lease/Rental"):
            logging.info("⏭️ Lease/Rental tab already exists, skipping")
            return
        try:
            from lease_ui import create_lease_management_tab
            lease_frame = create_lease_management_tab(notebook, current_user=username)
            notebook.addTab(lease_frame, " 📋 Lease/Rental ")
            _tag_last_tab(notebook, "dynamic")
            logging.info("✅ Added Lease/Rental tab")
        except Exception as e:
            logging.warning(f"Lease/Rental tab not available: {e}")

    elif industry_id == "electronics":
        if _tab_exists("📱 Electronics"):
            logging.info("⏭️ Electronics tab already exists, skipping")
            return
        try:
            from electronics_ui import create_electronics_tab
            electronics_frame = create_electronics_tab(notebook, current_user=username)
            notebook.addTab(electronics_frame, " 📱 Electronics ")
            _tag_last_tab(notebook, "dynamic")
            logging.info("✅ Added Electronics tab")
        except Exception as e:
            logging.warning(f"Electronics tab not available: {e}")

    else:
        logging.info(f"Retail mode: No additional vertical tabs for '{industry_id}'")


def _tag_last_tab(notebook, tag: str):
    """Add a metadata tag to the last-added tab in the notebook using objectName."""
    try:
        last_idx = notebook.count() - 1
        if last_idx >= 0:
            widget = notebook.widget(last_idx)
            existing = widget.objectName() or ""
            if tag not in existing:
                new_name = f"{existing},{tag}" if existing else tag
                widget.setObjectName(new_name)
    except Exception:
        pass
