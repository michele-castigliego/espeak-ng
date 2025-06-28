from ctypes import *
from ctypes.util import find_library
import os
import argparse
import threading

# Costanti espeak
AUDIO_OUTPUT_RETRIEVAL = 1
espeakCHARS_UTF8 = 1
espeakEVENT_PHONEME = 4
espeakPHONEMES_IPA = 0x02
espeakPHONEMES_TIE = 0x80

# Carica libreria
libname = find_library("espeak-ng") or "libespeak-ng.so"
espeak = CDLL(libname)

# Struttura evento
class EspeakEvent(Structure):
    _fields_ = [
        ("type", c_int),
        ("unique_identifier", c_uint),
        ("text_position", c_uint),
        ("length", c_uint),
        ("audio_position", c_int),
        ("sample", c_int),
        ("user_data", c_void_p),
        ("id_name", c_char_p),
        ("value", c_int)
    ]

# Funzioni necessarie
espeak.espeak_Initialize.argtypes = [c_int, c_int, c_char_p, c_int]
espeak.espeak_Initialize.restype = c_int
espeak.espeak_SetVoiceByName.argtypes = [c_char_p]
espeak.espeak_SetVoiceByName.restype = c_int
espeak.espeak_Synth.argtypes = [c_void_p, c_size_t, c_uint, c_int, c_uint, c_uint, POINTER(c_uint), c_void_p]
espeak.espeak_Synth.restype = c_int
espeak.espeak_SetPhonemeCallback.argtypes = [CFUNCTYPE(c_int, POINTER(EspeakEvent))]
espeak.espeak_SetPhonemeCallback.restype = None
espeak.espeak_Synchronize.restype = c_int

# Buffer fonemi
phonemes = []
phoneme_lock = threading.Lock()

# Callback
@CFUNCTYPE(c_int, POINTER(EspeakEvent))
def phoneme_callback(events):
    idx = 0
    while True:
        event = events[idx]
        if event.type == 0:  # espeakEVENT_LIST_TERMINATED
            break
        if event.type == espeakEVENT_PHONEME:
            phoneme = event.id_name.decode('utf-8')
            with phoneme_lock:
                phonemes.append(phoneme)
        idx += 1
    return 0

def init_espeak(datapath, voice):
    espeak.espeak_Initialize(AUDIO_OUTPUT_RETRIEVAL, 0, datapath.encode('utf-8'), 0)
    espeak.espeak_SetPhonemeCallback(phoneme_callback)
    res = espeak.espeak_SetVoiceByName(voice.encode('utf-8'))
    if res != 0:
        raise RuntimeError(f"Voice '{voice}' not found in {datapath}")

def synth_text(text):
    utt_id = c_uint(0)
    espeak.espeak_Synth(text.encode('utf-8'), len(text), 0, 0, 0, espeakPHONEMES_IPA | espeakPHONEMES_TIE, pointer(utt_id), None)
    espeak.espeak_Synchronize()
    with phoneme_lock:
        return phonemes.copy()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phonemize using full eSpeak pipeline")
    parser.add_argument("text", help="Text to convert")
    parser.add_argument("-v", "--voice", default="it", help="Voice/language to use")
    default_path = os.environ.get("ESPEAK_DATA_PATH")
    if default_path is None:
        default_path = os.path.join(os.path.dirname(__file__), "..", "espeak-ng-data")
    parser.add_argument("--path", default=default_path, help="Path to espeak-ng-data")
    args = parser.parse_args()

    init_espeak(args.path, args.voice)
    phoneme_list = synth_text(args.text)
    print(" ".join(phoneme_list))

