# kernel_of_project.py
# (Оновлена логіка надсилання даних: по одному слову для субтитрів)

import argparse
import queue
import sys
import numpy as np
import soundcard as sc
import threading
from vosk import Model, KaldiRecognizer
import json
import argostranslate.package
import argostranslate.translate
import warnings
from soundcard.mediafoundation import SoundcardRuntimeWarning
import os
from deepmultilingualpunctuation import PunctuationModel
model_p = PunctuationModel()
import time


# Функція для перенесення тексту на новий рядок
def wrap_text(text, width=80):
    """Розбиває текст на рядки заданої ширини."""
    import textwrap
    return textwrap.fill(text, width=width)


# Змінюємо сигнатуру функції start_translation
# callback тепер прийматиме кортеж:
# ('subtitle_word', new_word_text) для поступового виводу слів в субтитрах
# ('subtitle_clear_all',) для повного очищення субтитрів після речення
# ('dialog_entry', original_text, translated_text) для вікна діалогів
def start_translation(stop_event, from_lang="en", to_lang="uk", callback=None):
    warnings.filterwarnings("ignore", category=SoundcardRuntimeWarning)

    from_code = from_lang
    to_code = to_lang

    def install_language_package(src_code, dest_code):
        print(f"Перевіряємо та встановлюємо пакет для {src_code} -> {dest_code}...")
        try:
            installed_packages = argostranslate.package.get_installed_packages()
            package_found = False
            for p in installed_packages:
                if p.from_code == src_code and p.to_code == dest_code:
                    package_found = True
                    print(f"Пакет {src_code} -> {dest_code} вже встановлено.")
                    break

            if not package_found:
                argostranslate.package.update_package_index()
                available_packages = argostranslate.package.get_available_packages()
                package_to_install = next(
                    filter(lambda x: x.from_code == src_code and x.to_code == dest_code, available_packages), None
                )

                if package_to_install:
                    print(f"Завантажуємо та встановлюємо пакет {src_code} -> {dest_code}...")
                    argostranslate.package.install_from_path(package_to_install.download())
                    print(f"Пакет {src_code} -> {dest_code} успішно встановлено.")
                else:
                    print(
                        f"❌ Пакет для {src_code} -> {dest_code} не знайдено серед доступних. Будь ласка, перевірте коди мов.")
                    raise ValueError(f"Пакет перекладу для {src_code} -> {dest_code} не знайдено.")
        except Exception as e:
            print(f"Помилка при встановленні пакета {src_code} -> {dest_code}: {e}")
            raise

    install_language_package(from_code, to_code)

    q = queue.Queue()

    default_speaker_name = sc.default_speaker().name
    loopback = next((m for m in sc.all_microphones(include_loopback=True)
                     if m.isloopback and default_speaker_name in m.name), None)
    print("🔍 Мікрофони:")
    for mic in sc.all_microphones(include_loopback=True):
        print(f"  - {mic.name} (loopback: {mic.isloopback})")

    if not loopback:
        raise RuntimeError("❌ Loopback-пристрій не знайдено. Перевір, чи є аудіо вихід з динаміків.")

    samplerate = 16000
    channels = 1
    blocksize = 8000

    vosk_model_lang = from_code
    if from_code == "en":
        vosk_model_lang = "en-us"
    elif from_code == "uk":
        vosk_model_lang = "uk"
    elif from_code == "pl":
        vosk_model_lang = "pl"
    elif from_code == "es":
        vosk_model_lang = "es"
    elif from_code == "zh":
        vosk_model_lang = "zh"
    else:
        print(
            f"Попередження: Для мови '{from_code}' немає прямого зіставлення з моделлю Vosk. Використовуємо '{from_code}' як є.")

    try:
        model = Model(lang=vosk_model_lang)
    except Exception as e:
        print(f"Помилка завантаження моделі Vosk для мови '{vosk_model_lang}': {e}")
        print("Будь ласка, переконайтеся, що ви встановили відповідну модель Vosk.")
        print("Наприклад, для англійської: pip install vosk; для української: https://alphacephei.com/vosk/models")
        sys.exit(1)

    rec = KaldiRecognizer(model, samplerate)
    os.makedirs("output", exist_ok=True)

    def loopback_stream():
        print("🎧 Слухаю системний звук...")
        with loopback.recorder(samplerate=samplerate, channels=channels, blocksize=blocksize) as mic:
            while not stop_event.is_set():
                data = mic.record(numframes=blocksize)
                data_bytes = (data * 32767).astype(np.int16).tobytes()
                q.put(data_bytes)

    threading.Thread(target=loopback_stream, daemon=True).start()

    last_partial_words = []  # Щоб відслідковувати, які слова вже були надіслані

    try:
        while not stop_event.is_set():
            try:
                data = q.get(timeout=1)
            except queue.Empty:
                continue

            if rec.AcceptWaveform(data):
                result_json = json.loads(rec.Result())
                recognized_text = result_json.get("text", "").strip()
                if recognized_text:
                    punctuated = model_p.restore_punctuation(recognized_text)
                    translated_text = argostranslate.translate.translate(punctuated, from_code, to_code)

                    print(f"\n🎙 {from_code.upper()}:\n{wrap_text(punctuated)}")
                    print(f"🌐 {to_code.upper()}:\n{wrap_text(translated_text)}\n")

                    if callback:
                        # 1. Надсилаємо команду на повне очищення субтитрів (щоб розпочати новий рядок)
                        callback("subtitle_clear_all", None, None)
                        # 2. Надсилаємо повний оригінальний текст для історії діалогів
                        callback("dialog_entry", punctuated, translated_text)

                    last_partial_words = []  # Скидаємо буфер слів після повного речення

            else:
                partial_text = json.loads(rec.PartialResult())["partial"]

                if partial_text.strip():
                    current_words = partial_text.strip().split()

                    # Знаходимо нові слова, яких ще не було в last_partial_words
                    new_words_to_send = []
                    for i in range(len(current_words)):
                        if i >= len(last_partial_words) or current_words[i] != last_partial_words[i]:
                            new_words_to_send.append(current_words[i])

                    # Надсилаємо кожне нове слово окремо для субтитрів
                    if callback:
                        for word in new_words_to_send:
                            callback("subtitle_word", word, None)
                            # time.sleep(0.01) # Можливо, невелика затримка для плавного виведення
                            # Важливо: цю затримку краще контролювати в qt.py через QTimer,
                            # щоб не блокувати потік розпізнавання.

                    last_partial_words = current_words  # Оновлюємо список останніх слів

    except KeyboardInterrupt:
        print("\n✅ Завершено! Текст збережено в папці output.")
    except Exception as e:
        print(f"\n❌ Виникла помилка в процесі перекладу: {e}")
        stop_event.set()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Real-time speech translation.")
    parser.add_argument("--from_lang", type=str, default="en", help="Source language code (e.g., 'en', 'uk', 'es')")
    parser.add_argument("--to_lang", type=str, default="uk", help="Target language code (e.g., 'uk', 'en', 'es')")
    args = parser.parse_args()

    stop_translation_event = threading.Event()
    start_translation(stop_translation_event, from_lang=args.from_lang, to_lang=args.to_lang)