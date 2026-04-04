"""
Mintaka Sphere - Tab Management Utilities
=========================================
Handles dynamic insertion of industry-specific tabs.
"""
import logging
from tkinter import ttk

def add_industry_tabs(notebook, industry_id, username):
    """Adds industry-specific tabs to the notebook based on current mode.

    All dynamically added tabs are tagged with 'dynamic' so that
    reload_industry_tabs() can safely identify and remove them.

    Duplicate guard: skips adding a tab if one with the same text already exists.
    """

    def _tab_exists(text: str) -> bool:
        """Check if a tab with the given text already exists."""
        for i in range(notebook.index("end") + 1):
            try:
                if notebook.tab(i, "text").strip() == text.strip():
                    return True
            except Exception:
                continue
        return False

    if industry_id == "pharma":
        if _tab_exists("💊 Pharma"):
            logging.info("⏭️ Pharma tab already exists, skipping")
            return
        try:
            from pharmacy_ui import create_pharma_tab
            pharma_frame = create_pharma_tab(notebook, current_user=username)
            notebook.add(pharma_frame, text=" 💊 Pharma ")
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
            notebook.add(lease_frame, text=" 📋 Lease/Rental ")
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
            notebook.add(electronics_frame, text=" 📱 Electronics ")
            _tag_last_tab(notebook, "dynamic")
            logging.info("✅ Added Electronics tab")
        except Exception as e:
            logging.warning(f"Electronics tab not available: {e}")

    else:
        logging.info(f"Retail mode: No additional vertical tabs for '{industry_id}'")


def _tag_last_tab(notebook, tag: str):
    """Add a metadata tag to the last-added tab in the notebook."""
    try:
        last_idx = notebook.index("end")
        if last_idx > 0:
            current_tags = list(notebook.tab(last_idx - 1, "tags") or [])
            if tag not in current_tags:
                notebook.tab(last_idx - 1, tags=current_tags + [tag])
    except Exception:
        pass
