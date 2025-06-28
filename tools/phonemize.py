#!/usr/bin/env python3
"""Example wrapper for ``espeak_TextToPhonemes`` using ``ctypes``.

The eSpeak NG library must be initialised and a voice selected before
``espeak_TextToPhonemes`` can be called.  This script performs the
initialisation with ``espeak_Initialize`` and exposes a small command
line interface to query phonemes.

Usage::

    python tools/phonemes_from_text.py [--ipa {1,2,3}] [-v VOICE] [--path PATH] TEXT
"""
from ctypes import CDLL, POINTER, CFUNCTYPE, c_char_p, c_int, c_uint, c_short, c_void_p, c_size_t, pointer
from ctypes.util import find_library
import argparse
import os

libname = find_library("espeak-ng") or "libespeak-ng.so"
espeak = CDLL(libname)
#espeak = CDLL("/usr/local/lib/libespeak-ng.so")

# Set the function prototypes
espeak.espeak_Initialize.argtypes = [c_int, c_int, c_char_p, c_int]
espeak.espeak_Initialize.restype = c_int
espeak.espeak_SetVoiceByName.argtypes = [c_char_p]
espeak.espeak_SetVoiceByName.restype = c_int
espeak.espeak_TextToPhonemes.argtypes = [POINTER(c_char_p), c_int, c_int]
espeak.espeak_TextToPhonemes.restype = c_char_p
espeak.espeak_Synth.argtypes = [c_void_p, c_size_t, c_uint, c_int, c_uint, c_uint, POINTER(c_uint), c_void_p]
espeak.espeak_Synth.restype = c_int

# Callback type definitions
PhonemeCallback = CFUNCTYPE(c_int, c_char_p)
SynthCallback = CFUNCTYPE(c_int, POINTER(c_short), c_int, c_void_p)

# Global callbacks. Keeping references prevents garbage collection while
# the callbacks are registered in the library.
def _phoneme_callback(p: bytes) -> int:
    return 0


def _synth_callback(wav, num, events) -> int:
    return 0

PHONEME_CB = PhonemeCallback(_phoneme_callback)
SYNTH_CB = SynthCallback(_synth_callback)

espeak.espeak_SetPhonemeCallback.argtypes = [PhonemeCallback]
espeak.espeak_SetPhonemeCallback.restype = None
espeak.espeak_SetSynthCallback.argtypes = [SynthCallback]
espeak.espeak_SetSynthCallback.restype = None

# Initialize the library and select a voice
AUDIO_OUTPUT_RETRIEVAL = 1
espeakCHARS_UTF8 = 1
espeakPHONEMES_SHOW = 0x01
espeakPHONEMES_IPA = 0x02
espeakPHONEMES_TIE = 0x80


def text_to_phonemes(text: str, phonememode: int) -> str:
    """Return the phonemes for *text* using espeak-ng."""
    text_ptr = c_char_p(text.encode("utf-8"))
    result_ptr = espeak.espeak_TextToPhonemes(
        pointer(text_ptr),
        espeakCHARS_UTF8,  # textmode
        phonememode,  # phonememode
    )
    return result_ptr.decode("utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert text to eSpeak NG phonemes")
    parser.add_argument("text")
    parser.add_argument(
        "--ipa",
        type=int,
        choices=range(1, 4),
        default=None,
        help="IPA output mode (1-3)",
    )
    parser.add_argument(
        "-v",
        "--voice",
        default="it",
        help="Language voice to use",
    )
    default_path = os.environ.get("ESPEAK_DATA_PATH")
    if default_path is None:
        default_path = os.path.join(os.path.dirname(__file__), "..", "espeak-ng-data")
    parser.add_argument(
        "--path",
        default=default_path,
        help="Path to eSpeak NG data directory",
    )
    args = parser.parse_args()

    espeak.espeak_Initialize(AUDIO_OUTPUT_RETRIEVAL, 0, args.path.encode(), 0)
    espeak.espeak_SetPhonemeCallback(PHONEME_CB)
    espeak.espeak_SetSynthCallback(SYNTH_CB)
    if espeak.espeak_SetVoiceByName(args.voice.encode()) != 0:
        parser.error(f"voice '{args.voice}' not found in {args.path}")

    if args.ipa is None:
        phonememode = espeakPHONEMES_SHOW
    elif args.ipa == 1:
        phonememode = espeakPHONEMES_IPA | (ord("_") << 8)
    elif args.ipa == 2:
        phonememode = espeakPHONEMES_IPA | espeakPHONEMES_TIE | (0x0361 << 8)
    else:
        phonememode = espeakPHONEMES_IPA | espeakPHONEMES_TIE | (0x200D << 8)

    print(text_to_phonemes(args.text, phonememode))
