import sys
from kernel_of_project import start_translation
import time
import threading
from PyQt5.QtWidgets import (
    QApplication, QWidget, QListWidget, QListWidgetItem, QLabel, QPushButton, QComboBox, QVBoxLayout,
    QTextEdit, QCheckBox, QMessageBox, QInputDialog
)
from PyQt5.QtGui import QFont, QCloseEvent, QFontMetrics  # Додано QFontMetrics
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer
import os

# Словник для зіставлення назв мов у GUI до їх кодів (ArgoTranslate)
LANGUAGE_CODES = {
    'English': 'en',
    'Українськa': 'uk',
    'Polska': 'pl',
    'Espanol': 'es',
    '中国人': 'zh'
}


class DialogWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dialog history")
        self.setGeometry(200, 200, 600, 303)
        self.setFixedWidth(600)
        self.setStyleSheet("background-color: #1C1A1B;")

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("background-color: #D8C99B; color: black;")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        font = QFont()
        font.setPointSize(12)
        self.text_edit.setFont(font)

        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        self.setLayout(layout)

        self._load_text_from_file()

    def add_text(self, text):
        self.text_edit.append(text)
        self.text_edit.verticalScrollBar().setValue(self.text_edit.verticalScrollBar().maximum())

    def _save_text_to_file(self):
        os.makedirs("output", exist_ok=True)
        try:
            with open("output/dialog_history.txt", "w", encoding="utf-8") as f:
                f.write(self.text_edit.toPlainText())
            print("Історія діалогів збережена у output/dialog_history.txt")
        except Exception as e:
            print(f"Помилка при збереженні історії діалогів: {e}")

    def _load_text_from_file(self):
        try:
            if os.path.exists("output/dialog_history.txt"):
                with open("output/dialog_history.txt", "r", encoding="utf-8") as f:
                    self.text_edit.setText(f.read())
                print("Історія діалогів завантажена з output/dialog_history.txt")
        except Exception as e:
            print(f"Помилка при завантаженні історії діалогів: {e}")

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

        self.open_selected_button = QPushButton("Відкрити обране")
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
                    QMessageBox.critical(self, "Помилка відкриття файлу", f"Не вдалося відкрити файл: {e}")
            else:
                QMessageBox.warning(self, "Файл не знайдено", f"Файл '{record_name}' не існує в папці 'output'.")
        else:
            QMessageBox.information(self, "Нічого не вибрано", "Не обрано жодного запису для відкриття.")

    def _save_recordings(self):
        os.makedirs("output", exist_ok=True)
        try:
            with open("output/recordings_list.txt", "w", encoding="utf-8") as f:
                for i in range(self.recordings_list.count()):
                    f.write(self.recordings_list.item(i).text() + "\n")
            print("Список записів збережено у output/recordings_list.txt")
        except Exception as e:
            print(f"Помилка при збереженні списку записів: {e}")

    def _load_recordings(self):
        try:
            if os.path.exists("output/recordings_list.txt"):
                with open("output/recordings_list.txt", "r", encoding="utf-8") as f:
                    for line in f:
                        self.recordings_list.addItem(line.strip())
                print("Список записів завантажено з output/recordings_list.txt")
        except Exception as e:
            print(f"Помилка при завантаженні списку записів: {e}")

    def closeEvent(self, event: QCloseEvent):
        self._save_recordings()
        super().closeEvent(event)


class SubtitleHandler(QObject):
    # Сигнал тепер передає три аргументи: (type, text_data, translated_text_or_None)
    data_signal = pyqtSignal(str, str, object)  # object для translated_text_or_None


class SpellweaverApp(QWidget):
    def process_incoming_data(self, data_type, text_data, translated_text):
        """
        Обробляє вхідні дані від kernel_of_project.
        data_type: 'subtitle_word', 'subtitle_clear_all', 'dialog_entry'
        text_data: слово для субтитрів або оригінальний текст для діалогу
        translated_text: перекладений текст (якщо data_type == 'dialog_entry'), інакше None
        """
        if data_type == "subtitle_word":
            if self.subtitle_window and self.subtitle_label and self.subtitle_window.isVisible():
                current_text = self.subtitle_label.text()
                new_text = current_text

                # Додаємо пробіл, якщо поточний текст не порожній
                if current_text:
                    new_text += " " + text_data
                else:
                    new_text = text_data

                # Перевіряємо, чи новий текст поміщається в рядок
                font_metrics = QFontMetrics(self.subtitle_label.font())
                if font_metrics.width(new_text) <= self.subtitle_label.width():
                    self.subtitle_label.setText(new_text)
                else:
                    # Якщо не поміщається, очищаємо і починаємо новий рядок
                    self.subtitle_label.setText(text_data)
                    # Можливо, тут потрібно скинути буфер в qt.py, якщо він є.
                    # Але оскільки ми беремо слова з kernel_of_project, qt.py просто відображає.
                    # Логіка "скидання" буфера для нового рядка субтитрів повинна бути в kernel_of_project.
                    # Однак, якщо в kernel_of_project приходить повне речення, він надсилає clear_all,
                    # що також призведе до очищення і нового рядка.

        elif data_type == "subtitle_clear_all":
            self.clear_subtitle_text()
            # Додатково: якщо ви хочете, щоб повне речення на мить з'являлося
            # після всіх слів і перед очищенням, можна зробити так:
            # self.subtitle_label.setText(text_data) # text_data тут буде повним реченням з AcceptWaveform
            # QTimer.singleShot(self.subtitle_display_duration, self.clear_subtitle_text)

        elif data_type == "dialog_entry":
            # Форматуємо і додаємо до історії діалогів
            dialog_entry = ""
            if translated_text:
                dialog_entry = f"{self.current_to_code.upper()}: {translated_text}\n{self.current_from_code.upper()}: {text_data}\n"
                self.current_session_translated_text += dialog_entry + "\n"
            else:
                dialog_entry = f"{self.current_from_code.upper()}: {text_data}\n"  # На випадок, якщо переклад не надійшов

            if dialog_entry:
                self.add_dialog_text(dialog_entry)

    def clear_subtitle_text(self):
        """Очищає текст в субтитрах."""
        if self.subtitle_label:
            self.subtitle_label.setText("")

    def run_worker_script(self):
        if not self.translating:
            selected_from_lang_name = self.language_dropdown.currentText()
            selected_to_lang_name = self.language2_dropdown.currentText()

            self.current_from_code = LANGUAGE_CODES.get(selected_from_lang_name)
            self.current_to_code = LANGUAGE_CODES.get(selected_to_lang_name)

            if not self.current_from_code or not self.current_to_code:
                QMessageBox.warning(self, "Помилка вибору мови", "Будь ласка, виберіть дійсну мову для перекладу.")
                return

            # Перевіряємо, чи "from_lang" є англійською для коректного виводу субтитрів.
            if self.current_from_code != 'en':
                reply = QMessageBox.question(self, 'Попередження',
                                             f"Обрана мова джерела ('{selected_from_lang_name}') не є англійською. "
                                             "Субтитри на екрані призначені для відображення АНГЛІЙСЬКОГО тексту. "
                                             "Продовжити?",
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    return

            print(f"Вибрано переклад з '{self.current_from_code}' на '{self.current_to_code}'")

            self.current_session_translated_text = ""
            self.clear_subtitle_text()
            self.dialog_window.text_edit.clear()

            self.stop_event.clear()
            # Callback тепер передає 3 аргументи: (type, text_data, translated_text_or_None)
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

    def __init__(self):
        super().__init__()
        self.translation_thread = None
        self.stop_event = threading.Event()
        self.translating = False
        self.current_session_translated_text = ""
        self.current_from_code = ""
        self.current_to_code = ""

        self.subtitle_display_duration = 3000  # 3 секунди для відображення повного речення субтитрів (в мс)

        self.dialog_window = DialogWindow()
        self.recordings_window = RecordingsWindow()
        self.dialog_window_visible = False
        self.recordings_window_visible = False

        self.subtitle_window = None
        self.subtitle_label = None

        self.init_ui()

        self.subtitle_handler = SubtitleHandler()
        # Підключаємо сигнал до функції process_incoming_data
        self.subtitle_handler.data_signal.connect(self.process_incoming_data)

    def save_session_translation(self):
        if not self.current_session_translated_text.strip():
            print("Немає тексту для збереження.")
            QMessageBox.information(self, "Збереження", "Немає перекладеного тексту для збереження.")
            return

        file_name, ok = QInputDialog.getText(self, "Зберегти переклад",
                                             "Введіть назву для запису (без розширення .txt):")
        if not ok or not file_name:
            QMessageBox.warning(self, "Збереження скасовано", "Назву файлу не введено. Переклад не збережено.")
            return

        full_file_name = f"{file_name}.txt"
        file_path = os.path.join("output", full_file_name)

        try:
            os.makedirs("output", exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                # Зберігаємо буфер, який вже містить формат "UK:\nEN:"
                f.write(f"Історія перекладу з {self.current_from_code.upper()} на {self.current_to_code.upper()}:\n\n")
                f.write(self.current_session_translated_text)
            print(f"Переклад сесії збережено у '{file_path}'")
            self.recordings_window.add_recording(full_file_name)
            QMessageBox.information(self, "Збережено", f"Переклад збережено у '{full_file_name}'.")
        except Exception as e:
            QMessageBox.critical(self, "Помилка збереження", f"Не вдалося зберегти переклад: {e}")

    def closeEvent(self, event: QCloseEvent):
        if self.translating:
            reply = QMessageBox.question(self, 'Підтвердження',
                                         "Переклад ще триває. Ви хочете зупинити і зберегти поточну сесію?",
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

        self.checkbox1 = QCheckBox("Start recording", self)
        self.checkbox1.setFont(QFont("comicsans", 10, QFont.Bold))
        self.checkbox1.setStyleSheet("color: white;")
        self.checkbox1.setGeometry(320, 400, 150, 20)
        self.checkbox1.setChecked(False)

        self.checkbox2 = QCheckBox("Hide on demo", self)
        self.checkbox2.setFont(QFont("comicsans", 10, QFont.Bold))
        self.checkbox2.setStyleSheet("color: white;")
        self.checkbox2.setGeometry(320, 450, 150, 20)
        self.checkbox2.setChecked(False)

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
            self.clear_subtitle_text()  # Очищаємо текст, коли вікно ховається
            return

        if self.subtitle_window is None:
            self.subtitle_window = QWidget()
            self.subtitle_window.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            self.subtitle_window.setAttribute(Qt.WA_TranslucentBackground)
            self.subtitle_window.setStyleSheet("background-color: rgba(0, 0, 0, 153);")

            screen_width = QApplication.primaryScreen().geometry().width()
            self.subtitle_window.setFixedSize(int(screen_width * 0.75), 120)  # Зробити субтитри ширшими

            screen = QApplication.primaryScreen().geometry()
            x = (screen.width() - self.subtitle_window.width()) // 2
            y = screen.height() - 160
            self.subtitle_window.move(x, y)

            self.subtitle_label = QLabel("", self.subtitle_window)
            self.subtitle_label.setFont(QFont("comicsans", 24))  # Збільшив шрифт для кращої читабельності
            self.subtitle_label.setStyleSheet("color: white;")
            self.subtitle_label.setAlignment(Qt.AlignCenter)
            self.subtitle_label.setGeometry(0, 0, self.subtitle_window.width(), self.subtitle_window.height())

        self.subtitle_window.show()
        self.clear_subtitle_text()  # Очищаємо текст субтитрів при показі для чистого старту


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SpellweaverApp()
    window.show()
    sys.exit(app.exec_())
