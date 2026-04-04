"""
Tab Management Utilities
=========================
Handles dynamic insertion and removal of industry-specific tabs.
Uses a metadata-based registry (tab tags) instead of fragile emoji-matching.
"""
import logging
from tkinter import ttk


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


def reload_industry_tabs(notebook, app_state, get_industry_type_fn, add_industry_tabs_fn,
                       username, role, switch_tab_callback):
    """Reload industry-specific tabs without restart.

    Uses a metadata-based registry to track dynamic tabs instead of
    fragile emoji-matching. Only removes tabs tagged as 'dynamic'.

    Args:
        notebook: The ttk.Notebook widget
        app_state: AppState instance
        get_industry_type_fn: Callable that returns current industry ID from DB
        add_industry_tabs_fn: Callable(notebook, industry_id, username) that adds vertical tabs
        username: Current username
        role: Current user role
        switch_tab_callback: Callback for tab switching
    """
    if not notebook or not notebook.winfo_exists():
        logging.warning("Cannot reload tabs - notebook not available")
        return False

    try:
        industry_id = get_industry_type_fn()
        logging.info(f"Reloading tabs for industry: {industry_id}")

        # 1. Identify dynamic tabs to remove using metadata registry
        tabs_to_remove = []
        for i in range(notebook.index("end") + 1):
            try:
                tab_tags = notebook.tab(i, "tags")
                if tab_tags and "dynamic" in tab_tags:
                    tabs_to_remove.append(i)
            except Exception:
                continue

        # 2. Remove in reverse order to avoid index shifting
        for i in sorted(tabs_to_remove, reverse=True):
            notebook.forget(i)

        # 3. Re-add Dashboard (only if it was removed or doesn't exist)
        dashboard_found = False
        for i in range(notebook.index("end") + 1):
            try:
                tab_text = notebook.tab(i, "text").strip()
                if "Dashboard" in tab_text:
                    dashboard_found = True
                    break
            except Exception:
                continue

        if not dashboard_found:
            from dashboard_ui import create_dashboard_tab
            dash_frame = create_dashboard_tab(
                notebook, username, role,
                switch_tab_callback=switch_tab_callback
            )
            notebook.insert(0, dash_frame, text=" 🏠 Dashboard ")
            _tag_last_tab(notebook, "dynamic")

        # 4. Re-add Industry Vertical tabs
        add_industry_tabs_fn(notebook, industry_id, username)

        logging.info("✅ Tab reload complete")
        return True
    except Exception as e:
        logging.error(f"❌ Error reloading tabs: {e}")
        return False


def tag_dashboard_tab(notebook):
    """Tag the dashboard tab as dynamic for safe removal during reload."""
    _tag_last_tab(notebook, "dynamic")
