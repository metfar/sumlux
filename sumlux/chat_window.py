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

"""Interfaz opcional de conversación; usa memoria sqlite local."""

from PySide6.QtCore import Qt, QThread, Signal;
from PySide6.QtGui import QTextDocumentFragment;
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QTextBrowser, QVBoxLayout;
from .backend import chat;
from .voice import speak, speech_text, stop;


class ChatWorker(QThread):
    result = Signal(str, str);

    def __init__(self, endpoint, model, messages, user_name="", parent=None):
        super().__init__(parent);
        self.endpoint = endpoint;
        self.model = model;
        self.messages = messages;
        self.user_name = user_name;

    def run(self):
        try:
            result = chat(self.endpoint, self.model, self.messages, user_name=self.user_name);
            self.result.emit(result, "");
        except Exception as error:
            self.result.emit("", str(error));


class ChatWindow(QDialog):
    def __init__(self, config, store, avatar):
        super().__init__(avatar);
        self.config = config;
        self.store = store;
        self.avatar = avatar;
        self._workers = [];
        self.setWindowTitle("Σlux · Conversar con Lumen");
        self.setMinimumSize(580, 480);
        self.setWindowFlag(Qt.WindowType.Window, True);
        layout = QVBoxLayout(self);
        self.status = QLabel();
        layout.addWidget(self.status);
        self.history = QTextBrowser();
        layout.addWidget(self.history);
        row = QHBoxLayout();
        self.line = QLineEdit();
        self.line.setPlaceholderText("Escribile a Lumen…");
        self.line.returnPressed.connect(self.send);
        row.addWidget(self.line);
        self.send_button = QPushButton("Enviar");
        self.send_button.clicked.connect(self.send);
        self.send_button.setAutoDefault(True);
        self.send_button.setDefault(True);
        row.addWidget(self.send_button);
        self.stop_button = QPushButton("■ Detener voz");
        self.stop_button.setAutoDefault(False);
        self.stop_button.clicked.connect(self.stop_voice);
        row.addWidget(self.stop_button);
        layout.addLayout(row);
        bottom = QHBoxLayout();
        preferences = QPushButton("Modelo y voz…");
        preferences.clicked.connect(self.avatar.open_preferences);
        preferences.setAutoDefault(False);
        bottom.addWidget(preferences);
        delete = QPushButton("Borrar historial…");
        delete.clicked.connect(self.clear_history);
        delete.setAutoDefault(False);
        bottom.addWidget(delete);
        layout.addLayout(bottom);
        self.refresh_connection_status();
        self.show_history();
        self.line.setFocus();

    def refresh_connection_status(self):
        if self.config.model_enabled:
            self.status.setText(f"Modelo configurado: {self.config.model} (no verificado)");
        else:
            self.status.setText("Modelo desconectado. Activá ‘Modelo y voz…’ para conversar.");

    def show_history(self):
        self.history.clear();
        for role, content in ((row[2], row[3]) for row in self.store.all_messages()):
            self.add_line("Vos" if role == "user" else "Lumen", content);

    def add_line(self, title, value):
        """Markdown de modelo en pantalla, sin tocar SQLite ni texto enviado a TTS.""";
        from html import escape;
        cursor = self.history.textCursor();
        cursor.movePosition(cursor.MoveOperation.End);
        cursor.insertHtml(f"<p><b>{escape(title)}:</b></p>");
        cursor.insertFragment(QTextDocumentFragment.fromMarkdown(value));
        cursor.insertHtml("<p></p>");
        self.history.setTextCursor(cursor);
        self.history.ensureCursorVisible();

    def stop_voice(self):
        stop();


    def send(self):
        stop();
        content = self.line.text().strip();
        if not content:
            return;
        if not self.config.model_enabled:
            QMessageBox.information(self, "Modelo desconectado", "Abrí ‘Modelo y voz…’ y activá el modelo que quieras usar. Por defecto se propone Ollama local.");
            return;
        self.store.append("user", content);
        self.add_line("Vos", content);
        self.line.clear();
        self.line.setEnabled(False);
        self.send_button.setEnabled(False);
        self.status.setText("Lumen está pensando…");
        worker = ChatWorker(self.config.endpoint, self.config.model, self.store.recent(), self.config.user_name, self);
        self._workers.append(worker);
        worker.result.connect(self._reply);
        worker.finished.connect(lambda: self._workers.remove(worker));
        worker.start();

    def _reply(self, answer, error):
        if error:
            self.status.setText("Error de conexión; el mensaje enviado permanece en memoria local.");
            QMessageBox.warning(self, "Modelo no disponible", error);
        else:
            self.store.append("assistant", answer);
            self.add_line("Lumen", answer);
            self.status.setText(f"Modelo: {self.config.model}");
            self.avatar._animate("wave");
            if self.config.voice_enabled and not speak(speech_text(answer, self.config.user_name, self.config.spoken_name), self.config.voice_language, self.config.voice_engine):
                self.status.setText("Motor de voz no disponible: revisá phonem, pronounce y ffplay, o cambiá motor en Preferencias.");
        self.line.setEnabled(True);
        self.send_button.setEnabled(True);
        self.line.setFocus();

    def clear_history(self):
        answer = QMessageBox.question(self, "Borrar memoria", "¿Eliminar todo el historial local de conversaciones de Σlux? Esta acción no se puede deshacer.");
        if answer == QMessageBox.StandardButton.Yes:
            self.store.clear();
            self.history.clear();

    def shutdown(self):
        stop();
        for worker in self._workers[:]:
            if worker.isRunning():
                worker.wait(65000);
