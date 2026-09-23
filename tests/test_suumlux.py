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
import json;
from pathlib import Path;
import tempfile;
import unittest;
from unittest.mock import patch;
import zipfile;
from sumlux.backend import chat;
from sumlux.config import Config, load, save;
from sumlux.sprites import STATES, atlas_path, frame, validate_pet_zip;
from sumlux.storage import ConversationStore;


class AssetTests(unittest.TestCase):
    def test_metadata_and_states(self):
        zip_path = Path(__file__).parents[1] / "sumlux" / "assets" / "Lumen-Pet-delicate-OpenPets.zip";
        data = validate_pet_zip(zip_path);
        self.assertEqual(data["id"], "lumen-pet-delicate");
        self.assertEqual(len(STATES), 9);
        self.assertEqual((frame("think", 5).x, frame("think", 5).y), (960, 1664));
        self.assertTrue(atlas_path().is_file());

    def test_out_of_range(self):
        with self.assertRaises(IndexError):
            frame("wave", 5);


class ConfigTests(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as root:
            dest = Path(root) / "prefs.toml";
            cfg = Config(model_enabled=True, endpoint='http://127.0.0.1:11434/v1/chat/completions', model='llama3.2', voice_enabled=True, voice_language='es', roaming=True, scale=1.5);
            save(cfg, dest);
            self.assertEqual(load(dest), cfg);
            self.assertEqual(dest.stat().st_mode & 0o777, 0o600);


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

    def test_rejects_embedded_credentials(self):
        with self.assertRaises(ValueError):
            chat("http://user:secret@127.0.0.1/v1/chat/completions", "llama3.2", []);


if __name__ == "__main__":
    unittest.main();
