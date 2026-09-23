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

"""Preferencias locales; nunca almacena tokens de API."""

from dataclasses import dataclass;
import os;
from pathlib import Path;
import tomllib;
from .paths import config_path;


@dataclass
class Config:
    model_enabled: bool = False;
    endpoint: str = "http://127.0.0.1:11434/v1/chat/completions";
    model: str = "llama3.2";
    voice_enabled: bool = False;
    voice_language: str = "es";
    roaming: bool = False;
    scale: float = 1.0;


def load(path=None):
    location = Path(path) if path is not None else config_path();
    if not location.is_file():
        return Config();
    data = tomllib.loads(location.read_text(encoding="utf-8"));
    return Config(**{name: value for name, value in data.items() if name in Config.__dataclass_fields__});


def save(config, path=None):
    location = Path(path) if path is not None else config_path();
    location.parent.mkdir(parents=True, exist_ok=True, mode=0o700);
    payload = "\n".join((f"model_enabled = {str(config.model_enabled).lower()}", f'endpoint = "{_escape(config.endpoint)}"', f'model = "{_escape(config.model)}"', f"voice_enabled = {str(config.voice_enabled).lower()}", f'voice_language = "{_escape(config.voice_language)}"', f"roaming = {str(config.roaming).lower()}", f"scale = {float(config.scale):.2f}", ""));
    temp = location.with_suffix(".tmp");
    descriptor = os.open(temp, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600);
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(payload);
    os.replace(temp, location);
    location.chmod(0o600);


def _escape(value):
    return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n");
