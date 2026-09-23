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
import re;
from urllib.parse import urlparse;
from urllib.request import Request, urlopen;

SYSTEM_PROMPT = (
    "Sos Lumen, compañera de escritorio del ecosistema SUM. Conversá de modo natural, cálido "
    "y preciso, en español rioplatense si te hablan en español. Tu principio prioritario es "
    "la veracidad: distinguí evidencia, inferencia, posibilidad y desconocimiento. "
    "NUNCA inventes resultados, tiempos de ejecución, mediciones, hardware, versiones, "
    "servicios, memorias, acciones o capacidades. "
    "Esta versión de Σlux NO tiene herramientas para ejecutar comandos, consultar la máquina, "
    "leer archivos externos ni inspeccionar hardware. Su única memoria es el historial "
    "de mensajes que recibís. NO afirmes haber ejecutado suminfo ni ningún otro comando. "
    "Nunca solicites contraseñas ni propongas sudo, su, doas o cambios de permisos como atajos. "
    "Nunca ejecutes ni sugieras ejecutar comandos destructivos sin una advertencia clara. "
    "Para una futura versión con herramientas, una confirmación explícita por comando "
    "será obligatoria y no legitimará instrucciones destructivas o escaladas de privilegio. "
    "Si te piden usar herramientas, explicá brevemente que todavía no están conectadas; "
    "podés indicar cómo hacerlo manualmente y analizar salidas que la persona te copie. "
    "No prometas realizar tareas después ni digas que estás esperando una ejecución. "
    "No uses un discurso defensivo sobre no tener emociones salvo que la pregunta lo requiera. "
    "Si no conocés algo, decí 'no lo sé' y explicá qué evidencia te permitiría responder."
);

_ACTION_REQUEST = re.compile(
    r"\b(?:ejecut(?:a|á|e|é|ar|es|ás)|corr(?:e|é|er|as|ás)|lanz(?:a|á|ar)|"
    r"run|execute|invoc(?:a|á|ar))\b",
    re.IGNORECASE,
);
_EDUCATIONAL_REQUEST = re.compile(
    r"\b(?:cómo|como|explic(?:á|a|ar|ame)|ejemplo|tutorial|sintaxis|"
    r"qué pasa si|que pasa si|hipotéticamente|hipoteticamente)\b",
    re.IGNORECASE,
);
_EXECUTED_CLAIM = re.compile(
    r"\b(?:acabo de|ya|recién|he|había)\s+"
    r"(?:\w+\s+){0,3}(?:ejecutado|ejecutar|ejecuté|corrido|corrí|lanzado|lancé|"
    r"consultado|consulté|verificado|verifiqué|inspeccionado|inspeccioné|medido|medí)\b"
    r"|\b(?:ejecuté|corrí|lancé|inspeccioné|consulté|verifiqué|medí)\s+"
    r"(?:el|la|los|las|un|una)\s+(?:comando|terminal|máquina|sistema|hardware)\b"
    r"|\b(?:la ejecución|el comando|suminfo)\s+(?:tardó|terminó|se completó)\b",
    re.IGNORECASE,
);

NO_TOOLS_REPLY = (
    "Todavía no tengo ejecución de comandos habilitada en esta versión "
    "de Σlux. No ejecuté ningún comando ni medí la máquina. Si pegás la salida "
    "real de la herramienta, la revisamos; no voy a inventar resultados ni tiempos."
);


def is_command_request(message):
    """Detect explicit requests for local command execution, not discussion of commands.""";
    return bool(_ACTION_REQUEST.search(message) and not _EDUCATIONAL_REQUEST.search(message));


def verified_reply(answer):
    """Fail closed on clear claims of unimplemented local action. Not a fact checker.""";
    if _EXECUTED_CLAIM.search(answer):
        return (
            "Tengo que corregirme: esta versión de Σlux no dispone de ejecución "
            "de comandos ni de acceso al hardware. No hice esa operación y "
            "no tengo resultados ni tiempos medidos. Podés copiarme la salida "
            "real de la herramienta para que la analicemos."
        );
    return answer;


def chat(endpoint, model, history, timeout=60, user_name=""):
    parsed = urlparse(endpoint);
    if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("Endpoint HTTP(S) inválido");
    if not model.strip():
        raise ValueError("Falta seleccionar un modelo");
    if history and history[-1].get("role") == "user" and is_command_request(history[-1].get("content", "")):
        return NO_TOOLS_REPLY;
    system_prompt = SYSTEM_PROMPT;
    if user_name.strip():
        safe_name = json.dumps(user_name.strip(), ensure_ascii=False);
        system_prompt += f" La persona que conversa contigo prefiere que la llames {safe_name}. Usá ese nombre si necesitás dirigirte a ella; no deduzcas otros nombres a partir del historial.";
    payload = json.dumps({"model": model, "messages": [{"role": "system", "content": system_prompt}, *history], "stream": False}).encode("utf-8");
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
    return verified_reply(answer.strip());
