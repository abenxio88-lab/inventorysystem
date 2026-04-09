"""
Tab Management System
=====================
Config-driven tab management.
Each industry defines exactly which tabs it needs.
NO hardcoding, NO if/elif branches.

Usage:
    from tab_manager import build_tabs_for_industry
    build_tabs_for_industry("electronics", tab_widget, username)
"""

import logging

from PySide6 import QtWidgets, QtCore, QtGui

logger = logging.getLogger(__name__)


def build_tabs_for_industry(industry_id: str, tab_widget: QtWidgets.QTabWidget, username: str, role: str = "staff",
                           switch_tab_callback=None) -> bool:
    """
    Build ALL tabs for a specific industry based on config.
    Falls back to placeholder if tab function doesn't exist.
    """
    try:
        from config import get_industry_config, get_tab_function

        # 1. Get industry config
        config = get_industry_config(industry_id)

        # 2. Get visible tabs for this industry
        visible_tabs = config.get_visible_tabs()

        logger.info(f"Building tabs for {config.industry_name}: {visible_tabs}")

        # 3. Create each tab (fallback to placeholder if function missing)
        created_tabs = []
        failed_tabs = []

        for tab_name in visible_tabs:
            try:
                # Get tab creation function from registry
                create_func = get_tab_function(tab_name)

                if create_func is None:
                    # FALLBACK: Create placeholder tab
                    logger.debug(f"Tab function not found for: {tab_name}, creating placeholder")
                    frame = _create_placeholder_tab(tab_widget, tab_name, config.color)
                    tab_widget.addTab(frame, f" {tab_name} ")
                    created_tabs.append(tab_name)
                    continue

                # Create the tab
                import inspect
                sig = inspect.signature(create_func)
                params = list(sig.parameters.keys())

                # Determine how to call the function based on its signature
                if "current_user" in params:
                    frame = create_func(tab_widget, current_user=username)
                elif "username" in params and "role" in params:
                    frame = create_func(tab_widget, username=username, role=role)
                elif "username" in params:
                    frame = create_func(tab_widget, username=username)
                else:
                    # Standard: just parent
                    frame = create_func(tab_widget)

                # Add to tab widget
                tab_widget.addTab(frame, f" {tab_name} ")
                created_tabs.append(tab_name)

            except Exception as e:
                logger.warning(f"Tab '{tab_name}' failed: {e}, creating placeholder")
                try:
                    # FALLBACK: Create placeholder tab
                    frame = _create_placeholder_tab(tab_widget, tab_name, config.color)
                    tab_widget.addTab(frame, f" {tab_name} ")
                    created_tabs.append(tab_name)
                except Exception as e2:
                    logger.error(f"Failed to create placeholder for '{tab_name}': {e2}")
                    failed_tabs.append(tab_name)
                continue

        # Report results
        logger.info(f"✅ Created {len(created_tabs)}/{len(visible_tabs)} tabs")
        if failed_tabs:
            logger.warning(f"❌ Failed tabs: {failed_tabs}")

        # Success if we got at least 1 tab
        return len(created_tabs) > 0

    except Exception as e:
        logger.error(f"❌ Failed to build tabs: {e}")
        return False


def _create_placeholder_tab(tab_widget: QtWidgets.QTabWidget, tab_name: str, color: str = "#3B82F6"):
    """
    Create a placeholder tab when the real function doesn't exist.
    This prevents empty notebooks during industry switching.
    """
    frame = QtWidgets.QWidget(tab_widget)
    layout = QtWidgets.QVBoxLayout(frame)
    layout.setContentsMargins(30, 30, 30, 30)

    # Message card
    card = QtWidgets.QGroupBox(f"{tab_name} - Coming Soon", frame)
    card_layout = QtWidgets.QVBoxLayout(card)
    card_layout.setContentsMargins(20, 20, 20, 20)

    card_layout.addWidget(QtWidgets.QLabel(
        f"<p style='font-size: 14pt; font-family: Segoe UI;'>This tab is under development.</p>"
    ))

    card_layout.addWidget(QtWidgets.QLabel(
        f"<p style='font-size: 10pt; font-family: Segoe UI;'>Industry: {tab_name} features will be available soon.</p>"
    ))

    card_layout.addStretch()
    layout.addWidget(card)
    layout.addStretch()

    return frame


def reload_tabs_for_new_industry(industry_id: str, tab_widget: QtWidgets.QTabWidget, username: str,
                                role: str = "staff", switch_tab_callback=None) -> bool:
    """
    Remove all current tabs and rebuild for a new industry.
    Called when user switches industries.

    Args:
        industry_id: New industry ID
        tab_widget: QTabWidget widget
        username: Current username
        role: Current user role
        switch_tab_callback: Callback for tab switching

    Returns:
        bool: Success status
    """
    try:
        logger.info(f"Switching to industry: {industry_id}")

        # 1. Remove ALL existing tabs
        tab_count = tab_widget.count()
        for i in range(tab_count - 1, -1, -1):
            tab_widget.removeTab(i)

        logger.debug(f"Cleared {tab_count} tabs")

        # 2. Build new tabs for the industry
        success = build_tabs_for_industry(
            industry_id, tab_widget, username, role, switch_tab_callback
        )

        if success:
            logger.info(f"✅ Industry switch complete: {industry_id}")
        else:
            logger.error(f"❌ Failed to switch industry: {industry_id}")

        return success

    except Exception as e:
        logger.error(f"❌ Error during industry switch: {e}")
        return False


def get_industry_tab_count(industry_id: str) -> int:
    """
    Get number of tabs an industry should have.
    Useful for validation and testing.

    Args:
        industry_id: Industry identifier

    Returns:
        int: Expected tab count
    """
    try:
        from config import get_industry_config
        config = get_industry_config(industry_id)
        return len(config.get_visible_tabs())
    except Exception:
        return 0
