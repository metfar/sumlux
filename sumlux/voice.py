#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#pylint:disable=W0301
#  
#  Copyright 2018- William Martinez Bas <metfar@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#
#import warnings;
#warnings.filterwarnings("ignore", category=UserWarning);

"""Motor de voz de Σlux; reutiliza phonem/pronounce y sus perfiles existentes.

phonem -t TEXT -l es-uy | pronounce -l es-uy --wav FILE; ffplay FILE
La síntesis se ejecuta fuera del hilo gráfico, sin shell=True.
""";

import os;
from pathlib import Path;
import shutil;
import subprocess;
import sys;
import tempfile;
from threading import Lock, Thread;

_PLAYBACK_LOCK = Lock();


def executable(name):
    """Find phonem commands even when .desktop omits ~/.local/bin from PATH.""";
    found = shutil.which(name);
    if found:
        return found;
    for directory in (os.environ.get("PHONEM_BIN_DIR", ""), str(Path.home() / ".local" / "bin")):
        if directory:
            candidate = Path(directory) / name;
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate);
    return None;


def voice_ready(engine="phonem"):
    """Do not fall back to an unexpected robotic voice.""";
    if engine == "phonem":
        return all(executable(name) for name in ("phonem", "pronounce", "ffplay"));
    if engine == "espeak":
        return bool(executable("espeak-ng") or executable("espeak") or executable("spd-say"));
    return False;


def _checked(command, **options):
    result = subprocess.run(command, check=False, timeout=180, **options);
    if result.returncode:
        detail = result.stderr.decode("utf-8", "replace") if isinstance(result.stderr, bytes) else (result.stderr or "");
        raise RuntimeError(f"{' '.join(command[:2])}: {detail.strip() or 'exit code ' + str(result.returncode)}");
    return result;


def play(text, language="es-uy", engine="phonem"):
    """Synchronous voice playback: call from a worker, not the Qt GUI thread.""";
    if not text.strip():
        return False;
    if not voice_ready(engine):
        raise RuntimeError(f"Motor de voz '{engine}' no disponible. Revisá phonem, pronounce y ffplay.");
    if engine == "phonem":
        ipa = _checked([executable("phonem"), "-t", text, "-l", language], stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout;
        if not ipa.strip():
            raise RuntimeError("phonem no generó una transcripción IPA");
        with tempfile.TemporaryDirectory(prefix="sumlux-voice-") as tmpdir:
            wav = str(Path(tmpdir) / "lumen.wav");
            _checked([executable("pronounce"), "-l", language, "--wav", wav], input=ipa, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE);
            _checked([executable("ffplay"), "-nodisp", "-autoexit", "-loglevel", "error", wav], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE);
        return True;
    # eSpeak/spd-say do not understand phonem project locale es-uy.
    legacy_language = {"es-uy": "es", "en-ca": "en", "fr-fr": "fr"}.get(language.lower(), language);
    tool = executable("espeak-ng") or executable("espeak");
    if tool:
        _checked([tool, "-v", legacy_language, "--", text], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE);
    else:
        _checked([executable("spd-say"), "-l", legacy_language, "--", text], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE);
    return True;


def speak(text, language="es-uy", engine="phonem"):
    """Queue local playback without freezing Σlux's animation or chat window.""";
    if not text.strip() or not voice_ready(engine):
        return False;
    def worker():
        with _PLAYBACK_LOCK:
            try:
                play(text, language, engine);
            except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
                print(f"sumlux: error de voz: {error}", file=sys.stderr);
    Thread(target=worker, daemon=True, name="sumlux-voice").start();
    return True;
