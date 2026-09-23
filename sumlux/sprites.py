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

"""Interpretación del atlas 8×9 de Lumen Pet Delicate (192×208 px)."""

from dataclasses import dataclass;
import json;
from importlib.resources import files;
import zipfile;

COLUMNS = 8;
ROWS = 9;
CELL_WIDTH = 192;
CELL_HEIGHT = 208;
STATES = {"idle": (0, 6), "right": (1, 8), "left": (2, 8), "wave": (3, 4), "jump": (4, 5), "rest": (5, 8), "wait": (6, 6), "walk": (7, 6), "think": (8, 6)};


@dataclass(frozen=True)
class Frame:
    state: str;
    index: int;
    x: int;
    y: int;
    width: int = CELL_WIDTH;
    height: int = CELL_HEIGHT;


def frame(state, index=0):
    row, count = STATES[state];
    if not 0 <= index < count:
        raise IndexError(f"Frame inválido: {state}[{index}]");
    return Frame(state, index, index * CELL_WIDTH, row * CELL_HEIGHT);


def atlas_path():
    return files("sumlux").joinpath("assets", "spritesheet.png");


def pet_metadata():
    return json.loads(files("sumlux").joinpath("assets", "pet.json").read_text(encoding="utf-8"));


def validate_pet_zip(path):
    with zipfile.ZipFile(path) as package:
        entries = set(package.namelist());
        if entries != {"pet.json", "spritesheet.webp"}:
            raise ValueError(f"Paquete OpenPets inesperado: {sorted(entries)}");
        metadata = json.loads(package.read("pet.json"));
        if metadata.get("id") != "lumen-pet-delicate" or metadata.get("spritesheetPath") != "spritesheet.webp":
            raise ValueError("El paquete no es Lumen Pet Delicate");
        return metadata;
