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

"""Cliente compatible con /v1/chat/completions (por defecto Ollama local)."""

import json;
import os;
from urllib.parse import urlparse;
from urllib.request import Request, urlopen;

SYSTEM_PROMPT = "Eres Lumen, compañera de escritorio del ecosistema SUM. Responde con claridad, calidez, rigor técnico y honestidad. No afirmes recordar nada fuera de los mensajes que recibes. Si una función no está implementada, dilo.";


def chat(endpoint, model, history, timeout=60):
    parsed = urlparse(endpoint);
    if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("Endpoint HTTP(S) inválido");
    if not model.strip():
        raise ValueError("Falta seleccionar un modelo");
    payload = json.dumps({"model": model, "messages": [{"role": "system", "content": SYSTEM_PROMPT}, *history], "stream": False}).encode("utf-8");
    headers = {"Content-Type": "application/json"};
    api_key = os.environ.get("SUMLUX_API_KEY", "");
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}";
    request = Request(endpoint, payload, headers, method="POST");
    with urlopen(request, timeout=timeout) as response:
        result = json.load(response);
    answer = result["choices"][0]["message"]["content"];
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("El modelo devolvió una respuesta vacía");
    return answer.strip();
