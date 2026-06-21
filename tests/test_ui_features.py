import os
import sys
import time

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["RAF_DEV"] = "1"

# Dynamically resolve project root (parent of tests/)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.qt_compat import QApplication
from src.ui.main_window import MainWindow

def test_ui_features():
    app = QApplication.instance() or QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    # Mock check_network_status to prevent overriding test states
    window.check_network_status = lambda: None
    
    print("Testing category filtering...")
    # Verify categories exist
    categories = ["all", "primary", "middle", "high", "general"]
    for cat in categories:
        assert cat in window.cat_buttons, f"Button for category {cat} missing"
        
    # Test filtering
    all_count = len(window.get_filtered_books())
    print(f"All books count: {all_count}")
    
    # Filter by high
    window.cat_buttons["high"].click()
    lise_books = window.get_filtered_books()
    print(f"High books count: {len(lise_books)}")
    assert len(lise_books) > 0, "No high books found"
    assert len(lise_books) < all_count, "Filtering by high did not change count"
    for b in lise_books:
        assert b.get("category") == "high", f"Book {b['id']} has wrong category: {b.get('category')}"
        
    # Filter by primary
    window.cat_buttons["primary"].click()
    ilkokul_books = window.get_filtered_books()
    print(f"Primary books count: {len(ilkokul_books)}")
    assert len(ilkokul_books) > 0, "No primary books found"
    for b in ilkokul_books:
        assert b.get("category") == "primary", f"Book {b['id']} has wrong category"
        
    print("Testing offline mode logic...")
    # Trigger offline mode
    window.is_offline = True
    window.refresh_grid()
    
    # Ensure offline badge is visible
    window.refresh_all_statuses()
    assert window.offline_badge.isVisible(), "Offline badge should be visible in offline mode"
    
    # Get an uninstalled card and verify button is disabled
    for card in window.card_widgets.values():
        if not card.is_installed and not card.downloading:
            assert not card.primary_btn.isEnabled(), f"Primary button for uninstalled card {card.book_id} should be disabled in offline mode"
            
    # Trigger online mode
    window.is_offline = False
    window.refresh_all_statuses()
    assert not window.offline_badge.isVisible(), "Offline badge should be hidden in online mode"
    
    # Verify primary button is enabled again
    for card in window.card_widgets.values():
        if not card.is_installed and not card.downloading:
            assert card.primary_btn.isEnabled(), f"Primary button for uninstalled card {card.book_id} should be enabled in online mode"
            
    print("UI features test passed successfully!")

if __name__ == "__main__":
    test_ui_features()
