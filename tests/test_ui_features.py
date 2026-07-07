import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["RAF_DEV"] = "1"

# Dynamically resolve project root (parent of tests/)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from PyQt5.QtWidgets import QApplication
from src.ui.main_window import MainWindow


def test_ui_features():
    app = QApplication.instance() or QApplication(sys.argv)

    window = MainWindow()
    window.show()

    # Mock check_network_status to prevent overriding test states
    window.check_network_status = lambda: None

    print("Testing action buttons and search box...")
    assert window.settings_btn is not None
    assert window.about_btn is not None
    assert window.search_input is not None

    # Test search filtering works
    window.search_input.setText("Ankara")
    filtered_books = window.get_filtered_books()
    for b in filtered_books:
        assert (
            "ankara" in b["title"].lower()
            or "ankara" in b["publisher"].lower()
            or "ankara" in b.get("description", "").lower()
        )

    print("Testing offline mode logic...")
    # Trigger offline mode
    window.is_offline = True
    window.refresh_grid()

    # Ensure offline badge is visible
    window.refresh_all_statuses()
    assert (
        window.offline_badge.isVisible()
    ), "Offline badge should be visible in offline mode"

    # Get an uninstalled card and verify button is disabled
    for card in window.card_widgets.values():
        if not card.is_installed and not card.downloading:
            assert (
                not card.primary_btn.isEnabled()
            ), f"Primary button for uninstalled card {card.book_id} should be disabled in offline mode"

    # Trigger online mode
    window.is_offline = False
    window.refresh_all_statuses()
    assert (
        not window.offline_badge.isVisible()
    ), "Offline badge should be hidden in online mode"

    # Verify primary button is enabled again
    for card in window.card_widgets.values():
        if not card.is_installed and not card.downloading:
            assert (
                card.primary_btn.isEnabled()
            ), f"Primary button for uninstalled card {card.book_id} should be enabled in online mode"

    print("UI features test passed successfully!")


if __name__ == "__main__":
    test_ui_features()
