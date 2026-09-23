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

"""Pruebas sin sesión gráfica ni servidor de modelo."""

import io;
import hashlib;
import struct;
import json;
from pathlib import Path;
import tempfile;
import unittest;
from unittest.mock import patch;
import zipfile;
from sumlux.backend import chat;
from sumlux.config import Config, load, save;
from sumlux.sprites import STATES, atlas_path, frame, pet_metadata, validate_pet_zip;
from sumlux.storage import ConversationStore;
from sumlux.voice import play, speak, voice_ready, speech_text;


class AssetTests(unittest.TestCase):
    def test_metadata_and_states(self):
        zip_path = Path(__file__).parents[1] / "sumlux" / "assets" / "Lumen-OpenPets.zip";
        data = validate_pet_zip(zip_path);
        self.assertEqual(data["id"], "lumen");
        self.assertEqual(len(STATES), 9);
        self.assertEqual((frame("think", 5).x, frame("think", 5).y), (960, 1664));
        self.assertTrue(atlas_path().is_file());

    def test_green_avatar_is_selected(self):
        self.assertEqual(pet_metadata()["id"], "lumen");
        image = atlas_path();
        self.assertEqual(image.name, "spritesheet.png");
        self.assertEqual(image.read_bytes()[0:8], b"\x89PNG\r\n\x1a\n");
        self.assertEqual(struct.unpack(">II", image.read_bytes()[16:24]), (1536, 1872));
        zip_path = image.parent / "Lumen-OpenPets.zip";
        with zipfile.ZipFile(zip_path) as package:
            self.assertEqual(json.loads(package.read("pet.json"))["id"], "lumen");
            self.assertEqual(package.read("spritesheet.webp")[:4], b"RIFF");
        self.assertEqual(sorted(p.name for p in image.parent.glob("*.zip")), ["Lumen-OpenPets.zip"]);

    def test_out_of_range(self):
        with self.assertRaises(IndexError):
            frame("wave", 5);


class ConfigTests(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as root:
            dest = Path(root) / "prefs.toml";
            cfg = Config(model_enabled=True, endpoint='http://127.0.0.1:11434/v1/chat/completions', model='llama3.2', voice_enabled=True, voice_language='es-uy', voice_engine='phonem', roaming=True, scale=1.5, user_name="Sebastián", spoken_name="", name_onboarding_complete=True);
            save(cfg, dest);
            self.assertEqual(load(dest), cfg);
            self.assertEqual(dest.stat().st_mode & 0o777, 0o600);


    def test_old_config_defaults_for_upgrade(self):
        with tempfile.TemporaryDirectory() as root:
            dest = Path(root) / "old.toml";
            dest.write_text('voice_engine = "phonem"\nvoice_language = "es-uy"\n', encoding="utf-8");
            cfg = load(dest);
            self.assertEqual(cfg.user_name, "");
            self.assertEqual(cfg.spoken_name, "");
            self.assertFalse(cfg.name_onboarding_complete);


class StorageTests(unittest.TestCase):
    def test_order_and_persistence(self):
        with tempfile.TemporaryDirectory() as root:
            location = Path(root) / "db" / "test.sqlite3";
            storage = ConversationStore(location);
            storage.append("user", "Hola");
            storage.append("assistant", "Bonjour !");
            self.assertEqual(storage.recent(1), [{"role": "assistant", "content": "Bonjour !"}]);
            storage.close();
            storage = ConversationStore(location);
            self.assertEqual(len(storage.recent()), 2);
            self.assertEqual(location.stat().st_mode & 0o777, 0o600);
            storage.clear();
            self.assertEqual(storage.recent(), []);
            storage.close();


class BackendTests(unittest.TestCase):
    def test_mocked_chat(self):
        class Reply:
            def __enter__(self):
                return self;
            def __exit__(self, *unused):
                return False;
            def read(self, size=-1):
                return json.dumps({"choices": [{"message": {"content": "Salut!"}}]}).encode();
        def fake_urlopen(request, timeout):
            self.assertEqual(timeout, 60);
            self.assertEqual(json.loads(request.data)["messages"][-1]["content"], "Hola");
            return Reply();
        with patch("sumlux.backend.urlopen", fake_urlopen):
            self.assertEqual(chat("http://127.0.0.1:11434/v1/chat/completions", "llama3.2", [{"role": "user", "content": "Hola"}]), "Salut!");

    def test_name_only_when_configured(self):
        from unittest.mock import Mock;
        observed = [];
        def fake_urlopen(request, timeout):
            observed.append(json.loads(request.data));
            stream = Mock();
            stream.__enter__ = Mock(return_value=stream);
            stream.__exit__ = Mock(return_value=None);
            stream.read.return_value = json.dumps({"choices": [{"message": {"content": "Hola, Seba"}}]}).encode();
            return stream;
        with patch("sumlux.backend.urlopen", fake_urlopen):
            self.assertEqual(chat("http://127.0.0.1:11434/v1/chat/completions", "llama3.2", [], user_name="Seba"), "Hola, Seba");
        self.assertIn("Seba", observed[0]["messages"][0]["content"]);
        self.assertNotIn("William", observed[0]["messages"][0]["content"]);

    def test_rejects_embedded_credentials(self):
        with self.assertRaises(ValueError):
            chat("http://user:secret@127.0.0.1/v1/chat/completions", "llama3.2", []);



class VoiceTests(unittest.TestCase):
    def test_phonem_profile_is_default(self):
        self.assertEqual(Config().voice_engine, "phonem");
        self.assertEqual(Config().voice_language, "es-uy");

    def test_voice_only_name_pronunciation(self):
        self.assertEqual(speech_text("Hola, William. ¿Williamson?", "William", "Uiliam"), "Hola, Uiliam. ¿Williamson?");
        self.assertEqual(speech_text("Hola, Sebastián.", "Sebastián", ""), "Hola, Sebastián.");
        self.assertEqual(speech_text("hola, WILLIAM", "William", "Uiliam"), "hola, Uiliam");
        self.assertEqual(speech_text("Hola, William", "", "Uiliam"), "Hola, William");

    def test_synthesis_reuses_phonem_profile_and_wav(self):
        import wave;
        from sumlux.voice import SpeechSession;
        calls = [];
        def fake_run(_session, args, input_data=None, stdout=None):
            calls.append((args, input_data));
            if args[0] == "/mock/phonem":
                return b"la kasa roxa";
            if args[0] == "/mock/pronounce":
                with wave.open(args[-1], "wb") as wav:
                    wav.setnchannels(1);
                    wav.setsampwidth(2);
                    wav.setframerate(22050);
                    wav.writeframes(b"\x00\x00" * 32);
            return None;
        with patch("sumlux.voice.executable", side_effect=lambda name: "/mock/" + name), patch.object(SpeechSession, "run", fake_run):
            self.assertTrue(play("La casa roja", "es-uy"));
        self.assertEqual(calls[0][0], ["/mock/phonem", "-t", "La casa roja", "-l", "es-uy"]);
        self.assertEqual(calls[1][0][:3], ["/mock/pronounce", "-l", "es-uy"]);
        self.assertEqual(calls[1][1], b"la kasa roxa");
        self.assertEqual(calls[2][0][:5], ["/mock/ffplay", "-nodisp", "-autoexit", "-loglevel", "error"]);
        self.assertEqual(calls[1][0][-1], calls[2][0][-1]);

    def test_missing_phonem_does_not_fallback_to_espeak(self):
        with patch("sumlux.voice.executable", side_effect=lambda name: None if name == "pronounce" else "/mock/" + name):
            self.assertFalse(voice_ready("phonem"));
            self.assertFalse(speak("hola", "es-uy", "phonem"));

    def test_espeak_explicit_engine_collapses_project_profile(self):
        from sumlux.voice import SpeechSession;
        calls = [];
        def fake_run(_session, args, input_data=None, stdout=None):
            calls.append(args);
            return None;
        with patch("sumlux.voice.executable", side_effect=lambda name: "/mock/" + name if name == "espeak-ng" else None), patch.object(SpeechSession, "run", fake_run):
            self.assertTrue(play("hola", "es-uy", "espeak"));
        self.assertEqual(calls[0], ["/mock/espeak-ng", "-v", "es", "--", "hola"]);

    def test_missing_audio_does_not_run_commands(self):
        with patch("sumlux.voice.executable", return_value=None), patch("sumlux.voice.subprocess.Popen") as run:
            with self.assertRaises(RuntimeError):
                play("hola", "es-uy", "phonem");
            run.assert_not_called();

class SpeechFormattingTests(unittest.TestCase):
    def test_list_bold_and_escaped_markdown(self):
        from sumlux.speech import speech_plain, speech_segments;
        source = "**Ecosistema SUM**\n\n* **Versión**: 1.2.5\n* \\*\\*Idiomas\\*\\*: español\n";
        result = speech_plain(source);
        self.assertIn("Ecosistema SUM", result);
        self.assertIn("Versión", result);
        self.assertIn("Idiomas", result);
        self.assertNotIn("*", result);
        self.assertNotIn("\\", result);
        self.assertTrue(any(bold for text, bold in speech_segments(source) if "Versión" in text));

    def test_gain_uses_pcm16_without_changing_voice_profile(self):
        import struct;
        from sumlux.voice import _boost_pcm16;
        self.assertEqual(struct.unpack("<2h", _boost_pcm16(struct.pack("<2h", 100, -100), 1.12)), (112, -112));

    def test_skip_code_speak_link_caption(self):
        from sumlux.speech import speech_plain;
        source = "Mirá [el reporte](https://example.org).\n```bash\nrm -rf ~/datos\n```";
        result = speech_plain(source);
        self.assertIn("el reporte", result);
        self.assertNotIn("https://", result);
        self.assertNotIn("rm -rf", result);


class TrustTests(unittest.TestCase):
    def test_command_request_never_calls_model_or_host(self):
        from sumlux.backend import NO_TOOLS_REPLY;
        with patch("sumlux.backend.urlopen") as mocked:
            result = chat("http://127.0.0.1:11434/v1/chat/completions", "llama3.2", [{"role": "user", "content": "Podrías ejecutar suminfo para ver la máquina?"}]);
        self.assertEqual(result, NO_TOOLS_REPLY);
        mocked.assert_not_called();
        from sumlux.backend import is_command_request;
        self.assertTrue(is_command_request("ejecutá ls"));
        self.assertTrue(is_command_request("corré uname -a"));
        self.assertFalse(is_command_request("¿Cómo ejecutar ls en Linux?"));

    def test_fake_execution_result_blocked(self):
        from sumlux.backend import verified_reply;
        for message in ("Acabo de ejecutar SUMINFO; tardó 10 segundos", "El comando terminó correctamente", "Ya he verificado el hardware"):
            self.assertIn("No hice esa operación", verified_reply(message));

    def test_no_command_process_interface(self):
        import sumlux.backend as backend;
        self.assertFalse(hasattr(backend, "execute"));
        self.assertFalse(hasattr(backend, "run_command"));


class CancellationTests(unittest.TestCase):
    def test_cancel_running_subprocess(self):
        import sys;
        import time;
        from sumlux.voice import SpeechCancelled, SpeechSession;
        from threading import Thread;
        session = SpeechSession();
        outcomes = [];
        def run():
            try:
                session.run([sys.executable, "-c", "import time;time.sleep(30)"]);
            except SpeechCancelled:
                outcomes.append("cancelled");
        worker = Thread(target=run, daemon=True);
        worker.start();
        for _ in range(100):
            with session.lock:
                active = session.process;
            if active is not None:
                break;
            time.sleep(0.01);
        self.assertIsNotNone(active);
        session.stop();
        worker.join(4);
        self.assertFalse(worker.is_alive());
        self.assertEqual(outcomes, ["cancelled"]);


if __name__ == "__main__":
    unittest.main();
