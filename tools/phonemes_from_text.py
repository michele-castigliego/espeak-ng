#!/usr/bin/env python3
"""Example wrapper for ``espeak_TextToPhonemes`` using ``ctypes``.

The eSpeak NG library must be initialised and a voice selected before
``espeak_TextToPhonemes`` can be called.  This script performs the
initialisation with ``espeak_Initialize`` and selects the ``"en"`` voice
via ``espeak_SetVoiceByName`` when it is imported.
"""
from ctypes import CDLL, POINTER, c_char_p, c_int, pointer
from ctypes.util import find_library
import sys

libname = find_library("espeak-ng") or "libespeak-ng.so"
espeak = CDLL(libname)

# Set the function prototypes
espeak.espeak_Initialize.argtypes = [c_int, c_int, c_char_p, c_int]
espeak.espeak_Initialize.restype = c_int
espeak.espeak_SetVoiceByName.argtypes = [c_char_p]
espeak.espeak_SetVoiceByName.restype = c_int
espeak.espeak_TextToPhonemes.argtypes = [POINTER(c_char_p), c_int, c_int]
espeak.espeak_TextToPhonemes.restype = c_char_p

# Initialize the library and select a voice
AUDIO_OUTPUT_RETRIEVAL = 1
espeak.espeak_Initialize(AUDIO_OUTPUT_RETRIEVAL, 0, None, 0)
espeak.espeak_SetVoiceByName(b"it")
espeakCHARS_UTF8 = 1
espeakPHONEMES_SHOW = 0x01


def text_to_phonemes(text: str) -> str:
    """Return the phonemes for *text* using espeak-ng."""
    text_ptr = c_char_p(text.encode("utf-8"))
    result_ptr = espeak.espeak_TextToPhonemes(
        pointer(text_ptr),
        espeakCHARS_UTF8,  # textmode
        espeakPHONEMES_SHOW,  # phonememode
    )
    return result_ptr.decode("utf-8")


if __name__ == "__main__":
    input_text = sys.argv[1] if len(sys.argv) > 1 else "Ciao mondo bello"
    print(text_to_phonemes(input_text))
