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

"""Convierte Markdown de conversación a texto y marcas de énfasis para TTS.

Se preserva el original para pantalla y SQLite. No analiza ni ejecuta el contenido.
""";

from html import unescape;
import re;

_FENCES = re.compile(r"^\s{0,3}(```|~~~)");
_STRONG = re.compile(r"(?<!\\)(\*\*|__)(?!\s)(.+?)(?<!\\)\1");
_TABLE_SEPARATOR = re.compile(r"^\s*\|?\s*:?-{3,}:?(\s*\|\s*:?-{3,}:?)*\s*\|?\s*$");
_HORIZONTAL_RULE = re.compile(r"^\s{0,3}(?:\*\s*){3,}$|^\s{0,3}(?:-\s*){3,}$|^\s{0,3}(?:_\s*){3,}$");
_LINK = re.compile(r"!?\[([^\]]*)\]\((?:<[^>]*>|(?:\\.|[^)])+)(?:\s+['\"][^'\"]*['\"])?\)");


def _plain_inline(text):
    """Limpia sintaxis visual sin quitar puntuación que ayuda a pronunciar.""";
    text = _LINK.sub(lambda match: match.group(1) if not match.group(0).startswith("!") else "", text);
    text = re.sub(r"!\[([^\]]*)\]", "", text);
    text = re.sub(r"\[([^\]]+)\]\[[^\]]*\]", r"\1", text);
    text = re.sub(r"(?<!\w)https?://\S+", "enlace", text);
    text = re.sub(r"</?[^<>\n]+>", "", text);
    text = re.sub(r"(?<!\\)`+([^`\n]+)`+", r"\1", text);
    text = re.sub(r"(?<!\\)~~(.*?)~~", r"\1", text);
    text = re.sub(r"(?<!\\)(\*|_)(?=\S)(.*?)(?<=\S)\1", r"\2", text);
    text = re.sub(r"\\([\\`*_{}\[\]()#+.!<>~|])", r"\1", text);
    text = unescape(text);
    return re.sub(r"[ \t]+", " ", text).strip();


def _append(parts, text, emphasized):
    text = _plain_inline(text);
    if not text:
        return;
    if parts and parts[-1][1] == emphasized:
        parts[-1] = (parts[-1][0] + text, emphasized);
    else:
        parts.append((text, emphasized));


def _clean_line(line):
    line = re.sub(r"^\s{0,3}#{1,6}\s+", "", line);
    line = re.sub(r"^\s{0,3}>\s?", "", line);
    line = re.sub(r"^\s*[-+*]\s+", "", line);
    line = re.sub(r"^\s*\d+[.)]\s+", "", line);
    line = re.sub(r"^\s*\[[ xX]\]\s+", "", line);
    if "|" in line and line.count("|") >= 2:
        line = re.sub(r"\s*\|\s*", ": ", line.strip(" |"));
    return line;


def speech_segments(markdown):
    """Devuelve (texto, negrita) manteniendo el orden y sin marcas Markdown.

    Los bloques cercados de código se omiten en voz, pues recitar código fuente
    no es la misma tarea que leer una respuesta en lenguaje natural.
    """;
    parts = [];
    fenced = False;
    delimiter = "";
    saw_code = False;
    for raw in markdown.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        boundary = _FENCES.match(raw);
        if boundary:
            marker = boundary.group(1)[:3];
            if not fenced:
                fenced = True;
                delimiter = marker;
                saw_code = True;
            elif marker == delimiter:
                fenced = False;
            continue;
        if fenced or _TABLE_SEPARATOR.match(raw) or _HORIZONTAL_RULE.match(raw):
            continue;
        line = _clean_line(raw);
        # Algunos modelos devuelven Markdown escapado: \*\*negrita\*\*.
        line = re.sub(r"\\([*_])", r"\1", line);
        line = re.sub(r":(?=\s|$)", ",", line);
        if not line.strip():
            if parts and not parts[-1][0].endswith((". ", "! ", "? ")):
                parts[-1] = (parts[-1][0].rstrip() + ". ", parts[-1][1]);
            continue;
        if parts and not parts[-1][0].endswith((" ", "\n")):
            previous = parts[-1][0].rstrip();
            parts[-1] = (previous + (" " if previous.endswith((".", ":", "!", "?", ";")) else ". "), parts[-1][1]);
        position = 0;
        for match in _STRONG.finditer(line):
            _append(parts, line[position:match.start()], False);
            _append(parts, match.group(2), True);
            position = match.end();
        _append(parts, line[position:], False);
    cleaned = [];
    for value, emph in parts:
        value = re.sub(r"\s+", " ", value).strip();
        if value:
            cleaned.append((value, emph));
    # A code-only answer must never be silently spoken as raw Markdown/code.
    if not cleaned and saw_code:
        return [("La respuesta contiene un bloque de código.", False)];
    return cleaned;


def speech_plain(markdown):
    """Texto TTS plano, útil para eSpeak y pruebas de accesibilidad.""";
    parts = speech_segments(markdown);
    result = " ".join(text for text, _emphasized in parts).strip();
    return re.sub(r"\s+([,.;!?])", r"\1", result);
