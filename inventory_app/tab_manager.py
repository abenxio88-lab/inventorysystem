"""
Tab Management System
=====================
Config-driven tab management.
Each industry defines exactly which tabs it needs.
NO hardcoding, NO if/elif branches.

Usage:
    from tab_manager import build_tabs_for_industry
    build_tabs_for_industry("electronics", notebook, username)
"""

import logging
from tkinter import ttk

logger = logging.getLogger(__name__)


def build_tabs_for_industry(industry_id: str, notebook, username: str, role: str = "staff",
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
                    frame = _create_placeholder_tab(notebook, tab_name, config.color)
                    notebook.add(frame, text=f" {tab_name} ")
                    created_tabs.append(tab_name)
                    continue

                # Create the tab
                import inspect
                sig = inspect.signature(create_func)
                params = list(sig.parameters.keys())

                # Determine how to call the function based on its signature
                if "current_user" in params:
                    frame = create_func(notebook, current_user=username)
                elif "username" in params and "role" in params:
                    frame = create_func(notebook, username=username, role=role)
                elif "username" in params:
                    frame = create_func(notebook, username=username)
                else:
                    # Standard: just parent
                    frame = create_func(notebook)

                # Add to notebook
                notebook.add(frame, text=f" {tab_name} ")
                created_tabs.append(tab_name)

            except Exception as e:
                logger.warning(f"Tab '{tab_name}' failed: {e}, creating placeholder")
                try:
                    # FALLBACK: Create placeholder tab
                    frame = _create_placeholder_tab(notebook, tab_name, config.color)
                    notebook.add(frame, text=f" {tab_name} ")
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


def _create_placeholder_tab(notebook, tab_name: str, color: str = "#3B82F6"):
    """
    Create a placeholder tab when the real function doesn't exist.
    This prevents empty notebooks during industry switching.
    """
    import tkinter as tk
    from tkinter import ttk
    
    frame = ttk.Frame(notebook, padding=30)
    
    # Message card
    card = ttk.LabelFrame(frame, text=f"{tab_name} - Coming Soon", padding=20)
    card.pack(fill="both", expand=True, padx=20, pady=20)
    
    ttk.Label(
        card, 
        text=f"This tab is under development.",
        font=("Segoe UI", 14)
    ).pack(pady=(20, 10))
    
    ttk.Label(
        card, 
        text=f"Industry: {tab_name} features will be available soon.",
        font=("Segoe UI", 10)
    ).pack(pady=5)
    
    return frame


def reload_tabs_for_new_industry(industry_id: str, notebook, username: str, 
                                role: str = "staff", switch_tab_callback=None) -> bool:
    """
    Remove all current tabs and rebuild for a new industry.
    Called when user switches industries.
    
    Args:
        industry_id: New industry ID
        notebook: ttk.Notebook widget
        username: Current username
        role: Current user role
        switch_tab_callback: Callback for tab switching
        
    Returns:
        bool: Success status
    """
    try:
        logger.info(f"Switching to industry: {industry_id}")
        
        # 1. Remove ALL existing tabs
        tab_count = notebook.index("end") + 1
        for i in range(tab_count):
            notebook.forget(0)
        
        logger.debug(f"Cleared {tab_count} tabs")
        
        # 2. Build new tabs for the industry
        success = build_tabs_for_industry(
            industry_id, notebook, username, role, switch_tab_callback
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
