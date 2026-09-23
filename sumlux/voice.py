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

"""Voz cancelable de Σlux: Markdown -> phonem -> pronounce -> WAV -> ffplay.

Respeta es-uy y el volumen base de pronounce. Las negritas se enfatizan
únicamente tras sintetizar, sin sobrescribir ~/.config/phonem/pronounce.json.
""";

from array import array;
import os;
from pathlib import Path;
import re;
import shutil;
import signal;
import subprocess;
import sys;
import tempfile;
from threading import Event, Lock, Thread, Timer;
import wave;
from .speech import speech_plain, speech_segments;

_MANAGER_LOCK = Lock();
_ACTIVE = None;


class SpeechCancelled(Exception):
    """Interrupción solicitada desde la interfaz.""";


def speech_text(text, user_name="", spoken_name=""):
    """Adapta solamente la pronunciación del nombre, no el historial visible.""";
    name = user_name.strip();
    reading = spoken_name.strip();
    if not name or not reading or name == reading:
        return text;
    return re.sub(r"(?<!\w)" + re.escape(name) + r"(?!\w)", lambda _match: reading, text, flags=re.IGNORECASE);


def executable(name):
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
    if engine == "phonem":
        return all(executable(name) for name in ("phonem", "pronounce", "ffplay"));
    if engine == "espeak":
        return bool(executable("espeak-ng") or executable("espeak"));
    return False;


def _terminate(process):
    """Interrumpe el grupo Linux, también si el motor inició algún proceso hijo.""";
    if process is None or process.poll() is not None:
        return;
    try:
        os.killpg(process.pid, signal.SIGTERM);
    except ProcessLookupError:
        return;
    except OSError:
        process.terminate();
    def force_kill():
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL);
            except ProcessLookupError:
                pass;
            except OSError:
                process.kill();
    timer = Timer(0.75, force_kill);
    timer.daemon = True;
    timer.start();


class SpeechSession:
    def __init__(self):
        self.cancelled = Event();
        self.lock = Lock();
        self.process = None;

    def stop(self):
        with self.lock:
            already_stopped = self.cancelled.is_set();
            self.cancelled.set();
            process = self.process;
        _terminate(process);
        return not already_stopped;

    def run(self, command, input_data=None, stdout=subprocess.DEVNULL):
        with self.lock:
            if self.cancelled.is_set():
                raise SpeechCancelled();
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE if input_data is not None else subprocess.DEVNULL,
                stdout=stdout,
                stderr=subprocess.PIPE,
                start_new_session=True,
            );
            self.process = process;
        try:
            output, errors = process.communicate(input=input_data, timeout=180);
            if self.cancelled.is_set():
                raise SpeechCancelled();
            if process.returncode:
                details = (errors or b"").decode("utf-8", "replace").strip();
                raise RuntimeError(f"{Path(command[0]).name}: {details or 'exit code ' + str(process.returncode)}");
            return output;
        except subprocess.TimeoutExpired as error:
            _terminate(process);
            raise RuntimeError(f"Se agotó el tiempo de espera de {Path(command[0]).name}") from error;
        finally:
            with self.lock:
                if self.process is process:
                    self.process = None;


def _boost_pcm16(data, gain):
    """Ganancia con saturación suave en PCM16; admite audio Piper estándar.""";
    samples = array("h");
    samples.frombytes(data);
    if sys.byteorder != "little":
        samples.byteswap();
    for index, sample in enumerate(samples):
        samples[index] = max(-32768, min(32767, round(sample * gain)));
    if sys.byteorder != "little":
        samples.byteswap();
    return samples.tobytes();


def _join_wavs(chunks, destination, gain, session):
    """Concatena WAV de Piper con énfasis moderado; no modifica perfil phonem.""";
    expected = None;
    with wave.open(str(destination), "wb") as output:
        for file, emphasized in chunks:
            if session.cancelled.is_set():
                raise SpeechCancelled();
            with wave.open(str(file), "rb") as source:
                params = source.getparams();
                format_signature = (params.nchannels, params.sampwidth, params.framerate, params.comptype);
                if expected is None:
                    expected = format_signature;
                    output.setparams(params);
                elif expected != format_signature:
                    raise RuntimeError("Los fragmentos sintetizados tienen formatos WAV incompatibles");
                data = source.readframes(source.getnframes());
                if emphasized and gain > 1.0:
                    if params.sampwidth != 2:
                        raise RuntimeError("El énfasis requiere WAV PCM de 16 bits; desactivá el énfasis si tu modelo usa otro formato");
                    data = _boost_pcm16(data, gain);
                output.writeframes(data);


def _play(markdown, language, engine, gain, session):
    if not voice_ready(engine):
        raise RuntimeError(f"Motor de voz '{engine}' no disponible. Revisá phonem, pronounce y ffplay.");
    segments = speech_segments(markdown);
    if not segments:
        return False;
    if engine == "phonem":
        if gain <= 1.0 or not any(emph for _, emph in segments):
            segments = [(speech_plain(markdown), False)];
        with tempfile.TemporaryDirectory(prefix="sumlux-voice-") as directory:
            directory = Path(directory);
            chunks = [];
            for number, (text, emphasized) in enumerate(segments):
                ipa = session.run([executable("phonem"), "-t", text, "-l", language], stdout=subprocess.PIPE);
                if not ipa or not ipa.strip():
                    raise RuntimeError("phonem no generó una transcripción IPA");
                path = directory / f"part-{number:03}.wav";
                session.run([executable("pronounce"), "-l", language, "--wav", str(path)], input_data=ipa);
                chunks.append((path, emphasized));
            wav = directory / "lumen.wav";
            if len(chunks) == 1:
                wav = chunks[0][0];
                if chunks[0][1] and gain > 1.0:
                    _join_wavs(chunks, directory / "emphasized.wav", gain, session);
                    wav = directory / "emphasized.wav";
            else:
                _join_wavs(chunks, wav, gain, session);
            session.run([executable("ffplay"), "-nodisp", "-autoexit", "-loglevel", "error", str(wav)]);
        return True;
    legacy_language = {"es-uy": "es", "en-ca": "en", "fr-fr": "fr"}.get(language.lower(), language);
    tool = executable("espeak-ng") or executable("espeak");
    if tool:
        session.run([tool, "-v", legacy_language, "--", speech_plain(markdown)]);
    else:
        raise RuntimeError("eSpeak-NG o eSpeak no disponible; Speech Dispatcher no se utiliza porque no admite cancelación fiable de una sola voz");
    return True;


def play(text, language="es-uy", engine="phonem", emphasis_gain=1.12):
    """Versión sincrónica; el chat utiliza speak(), cuya sesión es cancelable.""";
    if not text.strip():
        return False;
    return _play(text, language, engine, emphasis_gain, SpeechSession());


def stop():
    """Detiene síntesis o audio inmediatamente; no toca phonem ni otros procesos.""";
    with _MANAGER_LOCK:
        active = _ACTIVE;
    if active is None:
        return False;
    active.stop();
    return True;


def speak(text, language="es-uy", engine="phonem", emphasis_gain=1.12):
    """Nueva respuesta cancela audio previo; no bloquea el hilo Qt.""";
    global _ACTIVE;
    if not text.strip() or not voice_ready(engine):
        return False;
    session = SpeechSession();
    with _MANAGER_LOCK:
        old = _ACTIVE;
        _ACTIVE = session;
    if old is not None:
        old.stop();
    def worker():
        global _ACTIVE;
        try:
            _play(text, language, engine, emphasis_gain, session);
        except SpeechCancelled:
            pass;
        except (OSError, RuntimeError, subprocess.SubprocessError, wave.Error) as error:
            if not session.cancelled.is_set():
                print(f"sumlux: error de voz: {error}", file=sys.stderr);
        finally:
            with _MANAGER_LOCK:
                if _ACTIVE is session:
                    _ACTIVE = None;
    Thread(target=worker, daemon=True, name="sumlux-voice").start();
    return True;
