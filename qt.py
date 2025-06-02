import sys
from kernel_of_project import start_translation # Make sure kernel_of_project.py is in the same directory or accessible via PYTHONPATH
import threading
from PyQt5.QtWidgets import (
    QApplication, QWidget, QListWidget, QListWidgetItem, QLabel, QPushButton, QComboBox, QVBoxLayout,
    QTextEdit, QMessageBox, QInputDialog
)
from PyQt5.QtGui import QFont, QCloseEvent, QFontMetrics
from PyQt5.QtCore import Qt, pyqtSignal, QObject
import os

# Dictionary to map GUI language names to their codes (ArgoTranslate)
LANGUAGE_CODES = {
    'English': 'en',
    'Українськa': 'uk',
    'Polska': 'pl',
    "Español": "es",
    "Português": "pt",
    '中国人': 'zh'
}


class DialogWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dialog history")
        self.setGeometry(200, 200, 600, 450)
        self.setFixedWidth(600)
        self.setStyleSheet("background-color: #1C1A1B;")

        # --- New: QLabel for displaying current original text word-by-word ---
        self.current_original_label = QLabel("", self)
        self.current_original_label.setStyleSheet("color: #D8C99B; background-color: #1C1A1B; padding: 5px;")
        font_current_original = QFont()
        font_current_original.setPointSize(12)
        font_current_original.setItalic(True) # Optional: make it italic to distinguish
        self.current_original_label.setFont(font_current_original)
        self.current_original_label.setWordWrap(True) # Allow text to wrap

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("background-color: #D8C99B; color: black;")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        font_text_edit = QFont()
        font_text_edit.setPointSize(12)
        self.text_edit.setFont(font_text_edit)

        layout = QVBoxLayout()
        layout.addWidget(self.current_original_label) # Add the new label to the layout
        layout.addWidget(self.text_edit)
        self.setLayout(layout)

        self._load_text_from_file()

    def update_current_original_display(self, text):
        """Updates the QLabel displaying the current original sentence word-by-word."""
        self.current_original_label.setText(text)

    def add_text(self, text):
        """Appends complete dialog entries to the main QTextEdit."""
        self.text_edit.append(text)
        self.text_edit.verticalScrollBar().setValue(self.text_edit.verticalScrollBar().maximum())

    def _save_text_to_file(self):
        os.makedirs("output", exist_ok=True)
        try:
            with open("output/dialog_history.txt", "w", encoding="utf-8") as f:
                f.write(self.text_edit.toPlainText())
            print("History of dialogues saved in output/dialog_history.txt")
        except Exception as e:
            print(f"Error while saving history: {e}")

    def _load_text_from_file(self):
        try:
            if os.path.exists("output/dialog_history.txt"):
                with open("output/dialog_history.txt", "r", encoding="utf-8") as f:
                    self.text_edit.setText(f.read())
                print("History of dialogues downloaded from output/dialog_history.txt")
        except Exception as e:
            print(f"Error while downloading history: {e}")

    def closeEvent(self, event: QCloseEvent):
        self._save_text_to_file()
        super().closeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if hasattr(self, '_old_pos') and self._old_pos is not None:
            delta = event.globalPos() - self._old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self._old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._old_pos = None


class RecordingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Записи")
        self.setGeometry(300, 300, 300, 200)
        self.setStyleSheet("background-color: #1C1A1B; color: white;")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.recordings_list = QListWidget()
        self.recordings_list.setStyleSheet("background-color: #D8C99B; color: black; border: 1px solid #555555;")
        self.recordings_list.itemDoubleClicked.connect(self.open_selected_recording)

        self.open_selected_button = QPushButton("Open")
        self.open_selected_button.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: white;
                border: 1px solid #444444;
                border-radius: 5px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        """)
        self.open_selected_button.clicked.connect(self.open_selected_recording)

        layout = QVBoxLayout()
        layout.addWidget(self.recordings_list)
        layout.addWidget(self.open_selected_button)
        self.setLayout(layout)

        self._load_recordings()

    def add_recording(self, record_name):
        item = QListWidgetItem(record_name)
        self.recordings_list.addItem(item)
        self._save_recordings()

    def open_selected_recording(self):
        selected_item = self.recordings_list.currentItem()
        if selected_item:
            record_name = selected_item.text()
            file_path = os.path.join("output", record_name)
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    msg_box = QMessageBox()
                    msg_box.setWindowTitle(f"Вміст: {record_name}")
                    msg_box.setText(content)
                    msg_box.setStyleSheet("""
                        QMessageBox {
                            background-color: #1C1A1B;
                            color: white;
                        }
                        QLabel {
                            color: white;
                        }
                        QPushButton {
                            background-color: #333333;
                            color: white;
                            border: 2px solid #444444;
                            border-radius: 5px;
                            padding: 5px 10px;
                        }
                        QPushButton:hover {
                            background-color: #555555;
                        }
                    """)
                    msg_box.exec_()
                except Exception as e:
                    QMessageBox.critical(self, "Error opening file", f"Failed to open file: {e}")
            else:
                QMessageBox.warning(self, "File not found", f"File '{record_name}' does not exist in the folder 'output'.")
        else:
            QMessageBox.information(self, "Nothing selected", "No record selected to open.")

    def _save_recordings(self):
        os.makedirs("output", exist_ok=True)
        try:
            with open("output/recordings_list.txt", "w", encoding="utf-8") as f:
                for i in range(self.recordings_list.count()):
                    f.write(self.recordings_list.item(i).text() + "\n")
            print("The list of entries is saved in output/recordings_list.txt")
        except Exception as e:
            print(f"Error saving list of records: {e}")

    def _load_recordings(self):
        try:
            if os.path.exists("output/recordings_list.txt"):
                with open("output/recordings_list.txt", "r", encoding="utf-8") as f:
                    for line in f:
                        self.recordings_list.addItem(line.strip())
                print("Record list loaded from output/recordings_list.txt")
        except Exception as e:
            print(f"Error loading list of records: {e}")

    def closeEvent(self, event: QCloseEvent):
        self._save_recordings()
        super().closeEvent(event)


class SubtitleHandler(QObject):
    # Signal passes: (data_type, text_data, translated_text_or_None)
    # data_type can be: 'subtitle_word', 'subtitle_clear_all', 'dialog_original_word', 'dialog_full_entry'
    data_signal = pyqtSignal(str, str, object)


class SpellweaverApp(QWidget):
    def process_incoming_data(self, data_type, text_data, translated_text):
        """
        Processes incoming data from kernel_of_project.
        data_type: 'subtitle_word', 'subtitle_clear_all', 'dialog_original_word', 'dialog_full_entry'
        text_data: word for subtitles or original text for dialog_original_word, full original for dialog_full_entry
        translated_text: translated text (if data_type == 'dialog_full_entry'), otherwise None
        """
        # Buffer to build the current original sentence for the dialog history temporary display
        if not hasattr(self, '_current_original_dialog_buffer'):
            self._current_original_dialog_buffer = ""

        if data_type == "subtitle_word":
            if self.subtitle_window and self.subtitle_label and self.subtitle_window.isVisible():
                current_text = self.subtitle_label.text()
                new_text = current_text

                # Add a space if the current text is not empty
                if current_text:
                    new_text += " " + text_data
                else:
                    new_text = text_data

                # Check if the new text fits in the line
                font_metrics = QFontMetrics(self.subtitle_label.font())
                if font_metrics.width(new_text) <= self.subtitle_label.width():
                    self.subtitle_label.setText(new_text)
                else:
                    # If it doesn't fit, clear and start a new line
                    self.subtitle_label.setText(text_data)

        elif data_type == "subtitle_clear_all":
            self.clear_subtitle_text()

        elif data_type == "dialog_original_word":
            # Append word to the buffer for gradual display in the dialog history's temporary label
            if self._current_original_dialog_buffer:
                self._current_original_dialog_buffer += " " + text_data
            else:
                # Start with language code for the first word
                self._current_original_dialog_buffer = f"{self.current_from_code.upper()}: {text_data}"
            self.dialog_window.update_current_original_display(self._current_original_dialog_buffer)

        elif data_type == "dialog_full_entry":
            # This signal carries the complete original and translated sentences.
            full_original_text = text_data
            full_translated_text = translated_text

            dialog_entry = ""
            if full_translated_text:
                dialog_entry = f"{self.current_from_code.upper()}: {full_original_text}\n{self.current_to_code.upper()}: {full_translated_text}\n"
                self.current_session_original_text += f"{full_original_text}\n"
                self.current_session_translated_text += f"{full_translated_text}\n"
            else:
                # Fallback if translation didn't arrive, still store original
                dialog_entry = f"{self.current_from_code.upper()}: {full_original_text}\n"
                self.current_session_original_text += f"{full_original_text}\n"

            if dialog_entry:
                self.add_dialog_text(dialog_entry)

            # Clear the temporary buffer and label after adding the full entry to the main history
            self._current_original_dialog_buffer = ""
            self.dialog_window.update_current_original_display("")

    def clear_subtitle_text(self):
        """Clears the text in the subtitles."""
        if self.subtitle_label:
            self.subtitle_label.setText("")

    def run_worker_script(self):
        if not self.translating:
            selected_from_lang_name = self.language_dropdown.currentText()
            selected_to_lang_name = self.language2_dropdown.currentText()

            self.current_from_code = LANGUAGE_CODES.get(selected_from_lang_name)
            self.current_to_code = LANGUAGE_CODES.get(selected_to_lang_name)

            if not self.current_from_code or not self.current_to_code:
                QMessageBox.warning(self, "Language selection error", "Please select a valid language for translation..")
                return

            print(f"Selected translation from '{self.current_from_code}' to '{self.current_to_code}'")

            self.current_session_original_text = ""  # Clear for new session
            self.current_session_translated_text = "" # Clear for new session
            self.clear_subtitle_text()
            self.dialog_window.text_edit.clear() # Clear main dialog history
            self.dialog_window.update_current_original_display("") # Clear temporary original text display

            self.stop_event.clear()
            # Callback now expects data_type, text_data, translated_text_or_None.
            # kernel_of_project must emit the new types for dialog history:
            # "dialog_original_word" (word, None) and "dialog_full_entry" (full_original, full_translated)
            callback_func = lambda dtype, txt, tr_txt: self.subtitle_handler.data_signal.emit(dtype, txt, tr_txt)

            self.translation_thread = threading.Thread(
                target=start_translation,
                args=(self.stop_event, self.current_from_code, self.current_to_code, callback_func)
            )
            self.translation_thread.daemon = True
            self.translation_thread.start()
            self.STARTbutton.setText("■")
            self.translating = True
        else:
            self.stop_event.set()
            if self.translation_thread and self.translation_thread.is_alive():
                self.translation_thread.join(timeout=2)
            self.STARTbutton.setText("▶")
            self.translating = False
            self.save_session_translation()
            self.clear_subtitle_text()
            self.dialog_window.update_current_original_display("") # Clear temporary original text display on stop

    def __init__(self):
        super().__init__()
        self.translation_thread = None
        self.stop_event = threading.Event()
        self.translating = False
        self.current_session_original_text = "" # New buffer for original text
        self.current_session_translated_text = "" # Existing buffer for translated text
        self.current_from_code = ""
        self.current_to_code = ""

        self.subtitle_display_duration = 3000  # 3 seconds for full sentence subtitles (in ms)

        self.dialog_window = DialogWindow()
        self.recordings_window = RecordingsWindow()
        self.dialog_window_visible = False
        self.recordings_window_visible = False

        self.subtitle_window = None
        self.subtitle_label = None

        self.init_ui()

        self.subtitle_handler = SubtitleHandler()
        # Connect the signal to the process_incoming_data function
        self.subtitle_handler.data_signal.connect(self.process_incoming_data)

    def save_session_translation(self):
        if not self.current_session_original_text.strip() and not self.current_session_translated_text.strip():
            print("There is no text to save.")
            QMessageBox.information(self, "Saving", "There is no translated text to save.")
            return

        file_name, ok = QInputDialog.getText(self, "Save the translation",
                                             "Enter a name for the recording (without the .txt extension):")
        if not ok or not file_name:
            QMessageBox.warning(self, "Saving canceled", "File name not entered. Translation not saved.")
            return

        os.makedirs("output", exist_ok=True)

        try:
            # Save original text
            original_file_name = f"{file_name}_{self.current_from_code}.txt"
            original_file_path = os.path.join("output", original_file_name)
            with open(original_file_path, "w", encoding="utf-8") as f:
                f.write(f"Original text ({self.current_from_code.upper()}):\n\n")
                f.write(self.current_session_original_text)
            print(f"Session original text saved in '{original_file_path}'")
            self.recordings_window.add_recording(original_file_name)

            # Save translated text
            translated_file_name = f"{file_name}_{self.current_to_code}.txt"
            translated_file_path = os.path.join("output", translated_file_name)
            with open(translated_file_path, "w", encoding="utf-8") as f:
                f.write(f"Translated text ({self.current_to_code.upper()}):\n\n")
                f.write(self.current_session_translated_text)
            print(f"Session translated text saved in '{translated_file_path}'")
            self.recordings_window.add_recording(translated_file_name)

            QMessageBox.information(self, "Saved", f"Translation saved in '{original_file_name}' and '{translated_file_name}'.")
        except Exception as e:
            QMessageBox.critical(self, "Save error", f"Failed to save translation: {e}")

    def closeEvent(self, event: QCloseEvent):
        if self.translating:
            reply = QMessageBox.question(self, 'Confirmation',
                                         "The translation is still in progress. Do you want to stop and save the current session?",
                                         QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self.stop_event.set()
                if self.translation_thread and self.translation_thread.is_alive():
                    self.translation_thread.join(timeout=2)
                self.save_session_translation()
                event.accept()
            elif reply == QMessageBox.No:
                self.stop_event.set()
                if self.translation_thread and self.translation_thread.is_alive():
                    self.translation_thread.join(timeout=2)
                event.accept()
            else:
                event.ignore()
                return

        if self.dialog_window:
            self.dialog_window.close()
        if self.recordings_window:
            self.recordings_window.close()
        if self.subtitle_window:
            self.subtitle_window.close()

        super().closeEvent(event)

    def init_ui(self):
        self.setWindowTitle("Spellweaver")
        self.setFixedSize(520, 651)
        self.setStyleSheet("background-color: #212124;")

        self.STARTbutton = QPushButton("▶", self)
        self.STARTbutton.setGeometry(10, 560, 500, 80)
        self.STARTbutton.setFont(QFont("comicsans", 30))
        self.STARTbutton.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: white;
                border: 2px solid #444444;
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QPushButton:pressed {
                background-color: #777777;
            }
        """)
        self.STARTbutton.clicked.connect(self.run_worker_script)

        self.label = QLabel("Language choice", self)
        self.label.setFont(QFont("comicsans", 12, QFont.Bold))
        self.label.setStyleSheet("color: white;")
        self.label.setGeometry(200, 10, 150, 30)

        languages = sorted(list(LANGUAGE_CODES.keys()))

        self.language_dropdown = QComboBox(self)
        self.language_dropdown.addItems(languages)
        self.language_dropdown.setFont(QFont("comicsans", 12, QFont.Bold))
        self.language_dropdown.setEditable(False)
        self.language_dropdown.setGeometry(20, 50, 200, 30)
        self.language_dropdown.setStyleSheet("""
            QComboBox {
                background-color: #333333;
                color: white;
                border: 2px solid #444444;
                border-radius: 5px;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #333333;
            }
            QComboBox QAbstractItemView {
                background-color: #333333;
                color: white;
                selection-background-color: #555555;
                selection-color: white;
                border: 1px solid #444444;
            }
        """)
        self.language_dropdown.setCurrentText('English')

        self.language2_dropdown = QComboBox(self)
        self.language2_dropdown.addItems(languages)
        self.language2_dropdown.setFont(QFont("comicsans", 12, QFont.Bold))
        self.language2_dropdown.setEditable(False)
        self.language2_dropdown.setGeometry(290, 50, 200, 30)
        self.language2_dropdown.setStyleSheet("""
            QComboBox {
                background-color: #333333;
                color: white;
                border: 2px solid #444444;
                border-radius: 5px;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #333333;
            }
            QComboBox QAbstractItemView {
                background-color: #333333;
                color: white;
                selection-background-color: #555555;
                selection-color: white;
                border: 1px solid #444444;
            }
        """)
        self.language2_dropdown.setCurrentText('Українськa')

        self.toggle_subtitles_btn = QPushButton("Subtitles", self)
        self.toggle_subtitles_btn.setGeometry(10, 400, 250, 40)
        self.toggle_subtitles_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: white;
                border: 2px solid #444444;
                border-radius: 10px;
                padding: 10px 20px;
                font: bold 14px "comicsans";
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QPushButton:pressed {
                background-color: #777777;
            }
        """)
        self.toggle_subtitles_btn.clicked.connect(self.toggle_subtitle_window)

        self.toggle_window_text_btn = QPushButton("Dialog History", self)
        self.toggle_window_text_btn.setGeometry(10, 450, 250, 40)
        self.toggle_window_text_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: white;
                border: 2px solid #444444;
                border-radius: 10px;
                padding: 10px 20px;
                font: bold 14px "comicsans";
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QPushButton:pressed {
                background-color: #777777;
            }
        """)
        self.toggle_window_text_btn.clicked.connect(self.toggle_dialog_window)

        self.record_btn = QPushButton("Recordings", self)
        self.record_btn.setGeometry(10, 500, 500, 40)
        self.record_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: white;
                border: 2px solid #444444;
                border-radius: 10px;
                padding: 10px 20px;
                font: bold 14px "comicsans";
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QPushButton:pressed {
                background-color: #777777;
            }
        """)
        self.record_btn.clicked.connect(self.toggle_recordings_window)

    def toggle_recordings_window(self):
        if self.recordings_window_visible:
            self.recordings_window.hide()
            self.recordings_window_visible = False
        else:
            self.recordings_window.show()
            self.recordings_window_visible = True

    def toggle_dialog_window(self):
        if self.dialog_window_visible:
            self.dialog_window.hide()
            self.dialog_window_visible = False
        else:
            self.dialog_window.show()
            self.dialog_window_visible = True

    def add_dialog_text(self, text):
        self.dialog_window.add_text(text)

    def toggle_subtitle_window(self):
        if self.subtitle_window and self.subtitle_window.isVisible():
            self.subtitle_window.hide()
            self.clear_subtitle_text()  # Clear text when window is hidden
            return

        if self.subtitle_window is None:
            self.subtitle_window = QWidget()
            self.subtitle_window.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            self.subtitle_window.setAttribute(Qt.WA_TranslucentBackground)
            self.subtitle_window.setStyleSheet("background-color: rgba(0, 0, 0, 153);")

            screen_width = QApplication.primaryScreen().geometry().width()
            self.subtitle_window.setFixedSize(int(screen_width * 0.75), 120)  # Make subtitles wider

            screen = QApplication.primaryScreen().geometry()
            x = (screen.width() - self.subtitle_window.width()) // 2
            y = screen.height() - 160
            self.subtitle_window.move(x, y)

            self.subtitle_label = QLabel("", self.subtitle_window)
            self.subtitle_label.setFont(QFont("comicsans", 24))  # Increased font for better readability
            self.subtitle_label.setStyleSheet("color: white;")
            self.subtitle_label.setAlignment(Qt.AlignCenter)
            self.subtitle_label.setGeometry(0, 0, self.subtitle_window.width(), self.subtitle_window.height())

        self.subtitle_window.show()
        self.clear_subtitle_text()  # Clear subtitle text on show for a clean start


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SpellweaverApp()
    window.show()
    sys.exit(app.exec_())