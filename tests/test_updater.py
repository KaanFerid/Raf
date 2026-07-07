import os
import sys
import time

# Set headless mode for Qt
os.environ["QT_QPA_PLATFORM"] = "offscreen"
# Force dev mode
os.environ["RAF_DEV"] = "1"

# Dynamically resolve project root (parent of tests/)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from PyQt5.QtWidgets import QApplication, QMessageBox
from src.core.config import load_config, save_config


def test_updater_flow():
    print("Resetting mock config...")
    config = load_config()
    config["last_update_check"] = 0
    config["auto_update_policy"] = "auto"
    save_config(config)

    print("Initializing QApplication...")
    app = QApplication.instance() or QApplication(sys.argv)

    print("Creating MainWindow...")
    from src.ui.main_window import MainWindow

    window = MainWindow()

    # Track actions
    dialog_questions = []
    dialog_informations = []

    # Monkeypatch QMessageBox.question
    def mock_question(parent, title, text, buttons, default_button):
        print(f"[Mock QMessageBox.question] Title: {title}, Text: {text}")
        dialog_questions.append((title, text))
        return QMessageBox.Yes

    QMessageBox.question = mock_question

    # Monkeypatch QMessageBox.information
    def mock_information(parent, title, text):
        print(f"[Mock QMessageBox.information] Title: {title}, Text: {text}")
        dialog_informations.append((title, text))
        # Quit the app when update completes
        app.quit()
        return QMessageBox.Ok

    QMessageBox.information = mock_information

    # Monkeypatch QMessageBox.warning
    def mock_warning(parent, title, text):
        print(f"[Mock QMessageBox.warning] Title: {title}, Text: {text}")
        app.quit()
        return QMessageBox.Ok

    QMessageBox.warning = mock_warning

    # The update checker runs automatically on MainWindow init
    print("Waiting for update checker to trigger...")

    # Spin the event loop to let the updater thread run
    start_time = time.time()
    while not dialog_questions and time.time() - start_time < 10:
        app.processEvents()
        time.sleep(0.1)

    if not dialog_questions:
        print(
            "FAILED: Update checker did not detect the mock update within 10 seconds."
        )
        sys.exit(1)

    print("Update detected successfully. Mock installer will run now...")

    # Wait for the installer to finish and pop up the completion dialog
    start_time = time.time()
    while not dialog_informations and time.time() - start_time < 30:
        app.processEvents()
        time.sleep(0.1)

    if not dialog_informations:
        print("FAILED: Update installation did not complete within 30 seconds.")
        sys.exit(1)

    print("SUCCESS: Self-updater flow verified successfully!")
    sys.exit(0)


if __name__ == "__main__":
    test_updater_flow()
