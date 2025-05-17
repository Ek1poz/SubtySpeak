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

def start_translation(stop_event, callback=None):

    # Игнорування попередження від soundcard
    warnings.filterwarnings("ignore", category=SoundcardRuntimeWarning)


#----------------------------------------------------------------------------------------

    from_code = "en"
    to_code = "uk"

    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()

    package_to_install = next(
        filter(
            lambda x: x.from_code == from_code and x.to_code == to_code, available_packages
        )
    )

    argostranslate.package.install_from_path(package_to_install.download())



#----------------------------------------------------------------------------------------
    q = queue.Queue()

    def int_or_str(text):
        try:
            return int(text)
        except ValueError:
            return text


#ПРи запуску скрипта, можливо знадобиться для додатку ¯\_(ツ)_/¯
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
    "-m", "--model", type=str, help="language model; e.g. en-us, fr, nl; default is en-us")
    args, remaining = parser.parse_known_args()
#---------------------------------------------------------------------------------------------------------



# Визначення loopback-пристрою (звук з динаміків)
    default_speaker_name = sc.default_speaker().name
    loopback = next((m for m in sc.all_microphones(include_loopback=True)
                    if m.isloopback and default_speaker_name in m.name), None)

    if not loopback:
        raise RuntimeError("Loopback-пристрій не знайдено")


#Налаштування параметрів аудіо
    samplerate = 16000
    channels = 1
    blocksize = 8000    #Встановлюється розмір одного блока (чанка) аудіоданих, який буде читатися за один раз. Це 8000 семплів. При частоті 16 кГц це відповідає 0.5 секунди звуку (8000 / 16000 = 0.5). Дані будуть оброблятися та передаватися блоками такого розміру.


# Завантаження моделі Vosk
    if args.model is None:
        model = Model(lang="en-us") #ru #en-us
    else:
        model = Model(lang=args.model)

    rec = KaldiRecognizer(model, samplerate) #!!!!



    def loopback_stream():
        print("Слухаю системний звук...)")
        with loopback.recorder(samplerate=samplerate, channels=channels, blocksize=blocksize) as mic:
            while not stop_event.is_set():
                data = mic.record(numframes=blocksize)
                data_bytes = (data * 32767).astype(np.int16).tobytes()
                q.put(data_bytes)

# Запуск потоку захоплення звуку
    threading.Thread(target=loopback_stream, daemon=True).start()


#Головний поток
    try:
        while not stop_event.is_set():
            try:
                data = q.get(timeout=1)
            except queue.Empty:
                continue

            if stop_event.is_set():
                break

            if rec.AcceptWaveform(data):
                # Готова фраза
                result_json = json.loads(rec.Result())
                recognized_text = result_json.get("text", "").strip()
                if recognized_text:
                    translated_text = argostranslate.translate.translate(recognized_text, from_code, to_code)

                    # Вивід у консоль — два рядки
                    print(f"\nEN: {recognized_text}")
                    print(f"UK: {translated_text}\n")

                    if callback: # for subtitles
                        callback(translated_text)

                    #Запис у файл — два рядки з порожнім рядком після
                    with open("output/en_output.txt", "a", encoding="utf-8") as f:
                        f.write(f" {recognized_text}\n")
                        f.flush()

                    with open("output/uk_output.txt", "a", encoding="utf-8") as f:
                        f.write(f" {translated_text}\n")
                        f.flush()




            else:
                partial_text = json.loads(rec.PartialResult())["partial"]
                partial_translate = argostranslate.translate.translate(partial_text, from_code, to_code)
                sys.stdout.write('\r' + partial_translate + ' ' * 20)
                sys.stdout.flush()

                if callback:
                    callback(partial_translate)

                #print(rec.PartialResult())
                #print(argostranslate.translate.translate(json.loads(rec.PartialResult())["partial"], from_code, to_code))
    except KeyboardInterrupt:
        print("✅ Готово! Усе збережено в output.txt")
        sys.exit(0)



