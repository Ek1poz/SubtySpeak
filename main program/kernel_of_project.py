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

# Змінюємо сигнатуру функції, щоб вона приймала from_lang та to_lang
def start_translation(stop_event, from_lang="en", to_lang="uk", callback=None):
    # Ігнорування попереджень бібліотеки soundcard
    warnings.filterwarnings("ignore", category=SoundcardRuntimeWarning)

    # Коди мов для перекладу тепер беруться з аргументів функції
    from_code = from_lang
    to_code = to_lang

    # Функція для перевірки та встановлення пакету мов
    def install_language_package(src_code, dest_code):
        print(f"Перевіряємо та встановлюємо пакет для {src_code} -> {dest_code}...")
        try:
            # Перевіряємо, чи вже встановлено пакет
            # Замість ітерації по lang.translations, ми тепер просто перевіряємо
            # чи функція translate може працювати з цією парою мов
            # або чи пакет вже є в installed_languages.
            # Більш надійна перевірка наявності пакета:
            installed_packages = argostranslate.package.get_installed_packages()
            package_found = False
            for p in installed_packages:
                if p.from_code == src_code and p.to_code == dest_code:
                    package_found = True
                    print(f"Пакет {src_code} -> {dest_code} вже встановлено.")
                    break

            if not package_found:
                # Якщо не встановлено, оновлюємо індекс та шукаємо пакет
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
                    print(f"❌ Пакет для {src_code} -> {dest_code} не знайдено серед доступних. Будь ласка, перевірте коди мов.")
                    raise ValueError(f"Пакет перекладу для {src_code} -> {dest_code} не знайдено.")
        except Exception as e:
            print(f"Помилка при встановленні пакета {src_code} -> {dest_code}: {e}")
            raise # Перевикидаємо помилку, щоб вона була помітна

    # Встановлюємо пакет для обраних мов
    install_language_package(from_code, to_code)


    # Черга для передачі аудіо-даних між потоками
    q = queue.Queue()

    # Аналіз аргументів (для можливості вказати модель через команду) - залишаємо для Vosk
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-m", "--model", type=str, help="Vosk language model (наприклад: en-us, ru)")
    args, _ = parser.parse_known_args()

    # Отримання loopback-пристрою для запису системного звуку
    default_speaker_name = sc.default_speaker().name
    loopback = next((m for m in sc.all_microphones(include_loopback=True)
                     if m.isloopback and default_speaker_name in m.name), None)
    print("🔍 Мікрофони:")
    for mic in sc.all_microphones(include_loopback=True):
        print(f"  - {mic.name} (loopback: {mic.isloopback})")

    if not loopback:
        raise RuntimeError("❌ Loopback-пристрій не знайдено. Перевір, чи є аудіо вихід з динаміків.")

    # Налаштування аудіо
    samplerate = 16000
    channels = 1
    blocksize = 8000

    # Завантаження моделі Vosk
    # Важливо: Vosk моделі мають свої специфічні коди мов (наприклад, "en-us"),
    # які можуть відрізнятися від кодів ArgoTranslate ("en").
    # Вам потрібно буде зіставити їх або дозволити користувачеві вибирати окремо Vosk модель.
    vosk_model_lang = from_code
    if from_code == "en":
        vosk_model_lang = "en-us"
    elif from_code == "uk":
        vosk_model_lang = "uk"
    elif from_code == "pl":
        vosk_model_lang = "pl" # Якщо є польська модель Vosk
    elif from_code == "es":
        vosk_model_lang = "es" # Якщо є іспанська модель Vosk
    elif from_code == "zh":
        vosk_model_lang = "zh" # Якщо є китайська модель Vosk
    else:
        print(f"Попередження: Для мови '{from_code}' немає прямого зіставлення з моделлю Vosk. Використовуємо '{from_code}' як є.")

    try:
        model = Model(lang=vosk_model_lang)
    except Exception as e:
        print(f"Помилка завантаження моделі Vosk для мови '{vosk_model_lang}': {e}")
        print("Будь ласка, переконайтеся, що ви встановили відповідну модель Vosk.")
        print("Наприклад, для англійської: pip install vosk; для української: https://alphacephei.com/vosk/models")
        sys.exit(1)


    rec = KaldiRecognizer(model, samplerate)

    # Створення папки для збереження файлів, якщо її ще немає
    os.makedirs("output", exist_ok=True)

    # Потік для захоплення системного звуку
    def loopback_stream():
        print("🎧 Слухаю системний звук...")
        with loopback.recorder(samplerate=samplerate, channels=channels, blocksize=blocksize) as mic:
            while not stop_event.is_set():
                data = mic.record(numframes=blocksize)
                data_bytes = (data * 32767).astype(np.int16).tobytes()
                q.put(data_bytes)

    threading.Thread(target=loopback_stream, daemon=True).start()

    # Головний цикл розпізнавання та перекладу
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
                    translated_text = argostranslate.translate.translate(recognized_text, from_code, to_code)

                    print(f"\n{from_code.upper()}: {recognized_text}")
                    print(f"{to_code.upper()}: {translated_text}\n")

                    if callback:
                        callback(translated_text) # ВИКЛИК `callback` ТІЛЬКИ ДЛЯ ПОВНИХ РЕЗУЛЬТАТІВ

                    with open(f"output/{from_code}_output.txt", "a", encoding="utf-8") as f:
                        f.write(f"{recognized_text}\n")

                    with open(f"output/{to_code}_output.txt", "a", encoding="utf-8") as f:
                        f.write(f"{translated_text}\n")

            else:
                partial_text = json.loads(rec.PartialResult())["partial"]
                if partial_text:
                    partial_translate = argostranslate.translate.translate(partial_text, from_code, to_code)
                    sys.stdout.write('\r' + partial_translate + ' ' * 20)
                    sys.stdout.flush()

    except KeyboardInterrupt:
        print("\n✅ Завершено! Текст збережено в папці output.")
    except Exception as e:
        print(f"\n❌ Виникла помилка в процесі перекладу: {e}")
        stop_event.set()