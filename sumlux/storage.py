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

"""Memoria conversacional local explícita, sin memoria de otras apps."""

import os;
from pathlib import Path;
import sqlite3;
from .paths import db_path;


class ConversationStore:
    def __init__(self, path=None):
        self.path = Path(path) if path is not None else db_path();
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700);
        self.path.parent.chmod(0o700);
        descriptor = os.open(self.path, os.O_CREAT | os.O_WRONLY, 0o600);
        os.close(descriptor);
        self.path.chmod(0o600);
        self.db = sqlite3.connect(self.path);
        self.db.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, role TEXT NOT NULL CHECK(role IN ('user','assistant')), content TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT (datetime('now')))");
        self.db.commit();

    def append(self, role, content):
        if role not in ("user", "assistant") or not isinstance(content, str) or not content.strip():
            raise ValueError("Mensaje o rol inválido");
        self.db.execute("INSERT INTO messages (role, content) VALUES (?, ?)", (role, content));
        self.db.commit();

    def recent(self, limit=24):
        rows = self.db.execute("SELECT role, content FROM (SELECT id, role, content FROM messages ORDER BY id DESC LIMIT ?) ORDER BY id ASC", (max(0, int(limit)),)).fetchall();
        return [{"role": row[0], "content": row[1]} for row in rows];

    def all_messages(self):
        return self.db.execute("SELECT id, created_at, role, content FROM messages ORDER BY id ASC").fetchall();

    def clear(self):
        self.db.execute("DELETE FROM messages");
        self.db.commit();

    def close(self):
        self.db.close();
