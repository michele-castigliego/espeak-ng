#!/usr/bin/env python3
"""Example wrapper for espeak_TextToPhonemes using ctypes."""
from ctypes import CDLL, POINTER, c_char_p, c_int, pointer
from ctypes.util import find_library
import sys

libname = find_library("espeak-ng") or "libespeak-ng.so"
espeak = CDLL(libname)

# Set the function prototype
espeak.espeak_TextToPhonemes.argtypes = [POINTER(c_char_p), c_int, c_int]
espeak.espeak_TextToPhonemes.restype = c_char_p

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
    input_text = sys.argv[1] if len(sys.argv) > 1 else "Hello world"
    print(text_to_phonemes(input_text))
