import sys
import string
import time
import threading
from PyQt5.QtWidgets import (
    QApplication, QWidget, QListWidget, QListWidgetItem, QLabel, QPushButton, QComboBox, QVBoxLayout,
    QTextEdit, QCheckBox
)
from PyQt5.QtGui import QFont, QIcon, QCloseEvent
from PyQt5.QtCore import Qt
                # діалогове вікно з субтитрами
class DialogWindow(QWidget):  # вікно з текстом
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dialog history")
        self.setGeometry(200, 200, 600, 303)
        self.setFixedWidth(600)
        self.setStyleSheet("background-color: #1C1A1B;")

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("background-color: #D8C99B; color: black;")

        font = QFont()
        font.setPointSize(12)
        self.text_edit.setFont(font)

        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        self.setLayout(layout)

    def add_text(self, text):
        self.text_edit.append(text)

               #  вікно зі збереженнями
class RecordingsWindow(QWidget):  # вікно для записів
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Записи")
        self.setGeometry(300, 300, 300, 200)
        self.setStyleSheet("background-color: #333333; color: white;")

        self.recordings_list = QListWidget()
        self.recordings_list.setStyleSheet("background-color: #444444; color: white; border: 1px solid #555555;")

        self.open_selected_button = QPushButton("Відкрити обране")
        self.open_selected_button.setStyleSheet("""
            QPushButton {
                background-color: #555555;
                color: white;
                border: 1px solid #666666;
                border-radius: 5px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #666666;
            }
        """)
        self.open_selected_button.clicked.connect(self.open_selected_recording)

        layout = QVBoxLayout()
        layout.addWidget(self.recordings_list)
        layout.addWidget(self.open_selected_button)
        self.setLayout(layout)

    def add_recording(self, record_name):
        item = QListWidgetItem(record_name)
        self.recordings_list.addItem(item)

    def open_selected_recording(self):
        selected_item = self.recordings_list.currentItem()
        if selected_item:
            record_name = selected_item.text()
            # Тут буде логіка для відкриття/відтворення обраного запису
            print(f"Відкрити запис: {record_name}")
        else:
            print("Не обрано жодного запису.")
class SpellweaverApp(QWidget):  # головне вікно
    def __init__(self):
        super().__init__()
        self.dialog_window = DialogWindow()
        self.recordings_window = RecordingsWindow()
        self.dialog_window_visible = False
        self.recordings_window_visible = False
        self.init_ui()


        self.subtitle_window = None
        self.subtitle_label = None
        self.subtitle_thread_started = False
        self.record_btn = None
    # це закриття всіх вікон якщо якривається головне вікно
    # (якщо видалити то всі решта вікон будуть працювати і після закриття програми , навіть не знаю як краще)
    def closeEvent(self, event: QCloseEvent):
     """Обробник події закриття головного вікна."""
     if self.dialog_window:
        self.dialog_window.close()
     if self.recordings_window:
        self.recordings_window.close()
     if self.subtitle_window:
        self.subtitle_window.close()
     event.accept()

             # ===ВИГЛЯД САМОГО ВІКНА===
    def init_ui(self):
        self.setWindowTitle("Spellweaver")
        self.setFixedSize(520, 651)
        self.setStyleSheet("background-color: #0C1821;")
        #          ====ЛЕМЕНТИ ВІКНА====

        # Кнопка запуску перекладу
        self.STARTbutton = QPushButton("0", self)
        self.STARTbutton.move(220, 550)
        self.STARTbutton.setStyleSheet("""
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
        #self.STARTbutton.clicked.connect(speech_translator.run_translator)
        # лейбли(з цими надписами нічого робити не треба)
        self.label = QLabel("Language choice", self)
        self.label.setFont(QFont("comicsans", 12, QFont.Bold))
        self.label.setStyleSheet("color: white;")
        self.label.move(180, 10)

        self.labelcheck1 = QLabel("Start recording", self)
        self.labelcheck1.setFont(QFont("comicsans", 10, QFont.Bold))
        self.labelcheck1.setStyleSheet("color: white;")
        self.labelcheck1.move(320, 400)

        self.labelcheck2 = QLabel("Hide on demo", self)
        self.labelcheck2.setFont(QFont("comicsans", 10, QFont.Bold))
        self.labelcheck2.setStyleSheet("color: white;")
        self.labelcheck2.move(320, 450)

          # чекбокси
        self.checkbox1 = QCheckBox(self)
        self.checkbox1.setChecked(False)
        self.checkbox1.setObjectName("hide on demo")
        self.checkbox1.move(290, 400)
        self.checkbox1.setStyleSheet("""
                    QCheckBox::indicator:checked {
                        background-color: gray;
                        border: none;
                    }
                    QCheckBox:focus {
                        outline: none;
                        border-radius: 5px;
                    }
                """)

        self.checkbox2 = QCheckBox(self)
        self.checkbox2.setChecked(False)
        self.checkbox2.setObjectName("hide on demo")
        self.checkbox2.move(290, 450)
        self.checkbox2.setStyleSheet("""
                    QCheckBox::indicator:checked {
                        background-color: gray;
                        border: none;
                    }
                    QCheckBox:focus {
                        outline: none;
                        border-radius: 5px;
                    }
                """)
        # Кнопка субтитрів
        self.toggle_subtitles_btn = QPushButton("Subtitles", self)
        self.toggle_subtitles_btn.move(10, 400)
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

        # Кнопка створення окремого вікна з текстом
        self.toggle_window_text_btn = QPushButton("Windowed text", self)
        self.toggle_window_text_btn.move(10, 450)
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
                        background-color: #BFB6BB;
                    }
                    QPushButton:pressed {
                        background-color: #BFB6BB;
                    }

                """)
        self.toggle_window_text_btn.clicked.connect(self.toggle_dialog_window)
        # кнопка виклику вікна з записами
        self.record_btn = QPushButton("recoedings", self)
        self.record_btn.move(10, 250)
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
                                background-color: #BFB6BB;
                            }
                            QPushButton:pressed {
                                background-color: #BFB6BB;
                            }

                        """)
        self.record_btn.clicked.connect(self.toggle_recordings_window)

        # дропдаун бокси з виборами мов
        languages = ['English', 'Українськa', 'Polska', 'Espanol', '中国人']

        self.language_dropdown = QComboBox(self) # це бокс з вибором мови з якої перекладають
        self.language_dropdown.addItems(languages)
        self.language_dropdown.setFont(QFont("comicsans", 12, QFont.Bold))
        self.language_dropdown.setEditable(False)
        self.language_dropdown.move(100, 40)
        self.language_dropdown.view().setStyleSheet("""
                    QAbstractItemView {
                        background-color: #333333;
                        color: white;
                        selection-background-color: #555555;
                        selection-color: white;
                        border: 2px solid #444444;
                        border-radius: 5px;
                    }
                """)
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
                """)

        self.language2_dropdown = QComboBox(self) # це бокс в якому має бути вибір на яку мову перекладають
        self.language2_dropdown.addItems(languages)
        self.language2_dropdown.setFont(QFont("comicsans", 12, QFont.Bold))
        self.language2_dropdown.setEditable(False)
        self.language2_dropdown.move(300, 40)
        self.language2_dropdown.view().setStyleSheet("""
                            QAbstractItemView {
                                background-color: #333333;
                                color: white;
                                selection-background-color: #555555;
                                selection-color: white;
                                border: 2px solid #444444;
                                border-radius: 5px;
                            }
                        """)
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
                        """)
     # це відповідає за сам показ вікна записів при натисканні кнопки
    def toggle_recordings_window(self):
        if self.recordings_window_visible:
            self.recordings_window.hide()
            self.recordings_window_visible = False
        else:
            self.recordings_window.show()
            self.recordings_window_visible = True

    # це відповідає за сам показ вікна з текстом при натисканні кнопки
    def toggle_dialog_window(self):
        if self.dialog_window_visible:
            self.dialog_window.hide()
            self.dialog_window_visible = False
        else:
            self.dialog_window.show()
            self.dialog_window_visible = True
            self.test_dialog_text() # Викликаємо додавання тексту тут
     # це все по суті тест того як має працювати отримання тексту
    def generate_random_text(self, length=10):
        """Генерує простий тестовий рядок"""
        return "тест " * (length // 5)

    def test_dialog_text(self):
        """Функція для простого тестування додавання тексту"""
        self.add_dialog_text("Перший тестовий рядок.")
        self.add_dialog_text("Другий тестовий рядок.")
        self.add_dialog_text("Третій тестовий рядок.")

    def add_dialog_text(self, text):
        """Метод для додавання тексту до вікна діалогу"""
        self.dialog_window.add_text(text)

    # Методи для субтитрів (ЗАМІНИ ЦІ КОМЕНТАРІ СВОЇМ КОДОМ)
    def toggle_subtitle_window(self):
        if self.subtitle_window and self.subtitle_window.isVisible():
            self.subtitle_window.hide()
            return

        if self.subtitle_window is None:
            self.subtitle_window = QWidget()
            self.subtitle_window.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            self.subtitle_window.setAttribute(Qt.WA_TranslucentBackground)
            self.subtitle_window.setStyleSheet("background-color: rgba(0, 0, 0, 153);")
            self.subtitle_window.setFixedSize(600, 60)

            screen = QApplication.primaryScreen().geometry()
            x = (screen.width() - 600) // 2
            y = screen.height() - 160
            self.subtitle_window.move(x, y)

            self.subtitle_label = QLabel("", self.subtitle_window)
            self.subtitle_label.setFont(QFont("comicsans", 20))
            self.subtitle_label.setStyleSheet("color: white;")
            self.subtitle_label.setGeometry(10, 10, 580, 40)

        self.subtitle_window.show()

        if not self.subtitle_thread_started:
            threading.Thread(target=self.subtitle_loop, daemon=True).start()
            self.subtitle_thread_started = True

    def subtitle_loop(self):
        while True:
            time.sleep(3)
            if self.subtitle_label:
                self.subtitle_label.setText("Це нові субтитри...")
            time.sleep(3)
            if self.subtitle_label:
                self.subtitle_label.setText("І ще один приклад...")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SpellweaverApp()
    window.show()
    sys.exit(app.exec_())