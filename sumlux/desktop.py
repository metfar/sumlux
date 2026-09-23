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

"""Avatar transparente independiente de OpenPets, destinado a Linux X11."""

import argparse;
import os;
import random;
import sys;
from PySide6.QtCore import QRect, Qt, QTimer;
from PySide6.QtGui import QPainter, QPixmap, QRegion;
from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QFormLayout, QCheckBox, QDoubleSpinBox, QLineEdit, QComboBox, QInputDialog, QMenu, QPushButton, QMessageBox, QWidget;
from . import __version__;
from .config import load, save;
from .sprites import CELL_WIDTH, CELL_HEIGHT, STATES, atlas_path, frame, pet_metadata;
from .storage import ConversationStore;


class Preferences(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent);
        self.setWindowTitle("Σlux · Preferencias");
        self.setMinimumWidth(470);
        self.model_on = QCheckBox("Habilitar conversación con modelo (sin conexión por defecto)");
        self.model_on.setChecked(config.model_enabled);
        self.endpoint = QLineEdit(config.endpoint);
        self.model = QLineEdit(config.model);
        self.user_name = QLineEdit(config.user_name);
        self.user_name.setPlaceholderText("Seba, Sebastián, o como prefieras");
        self.spoken_name = QLineEdit(config.spoken_name);
        self.spoken_name.setPlaceholderText("Opcional; p. ej., Uiliam para William");
        self.voice = QCheckBox("Leer las respuestas en voz alta");
        self.voice.setChecked(config.voice_enabled);
        self.engine = QComboBox();
        self.engine.addItem("phonem + pronounce (Piper, voz configurada)", "phonem");
        self.engine.addItem("eSpeak-NG / Speech Dispatcher (alternativa)", "espeak");
        self.engine.setCurrentIndex(max(0, self.engine.findData(config.voice_engine)));
        self.language = QLineEdit(config.voice_language);
        self.language.setPlaceholderText("es-uy");
        self.roaming = QCheckBox("Pasear por el escritorio");
        self.roaming.setChecked(config.roaming);
        self.scale = QDoubleSpinBox();
        self.scale.setRange(0.60, 3.00);
        self.scale.setSingleStep(0.10);
        self.scale.setValue(config.scale);
        layout = QFormLayout(self);
        layout.addRow("Cómo querés que te llame:", self.user_name);
        layout.addRow("Cómo pronunciar ese nombre:", self.spoken_name);
        layout.addRow(self.model_on);
        layout.addRow("Endpoint HTTP(S):", self.endpoint);
        layout.addRow("Modelo:", self.model);
        layout.addRow(self.voice);
        layout.addRow("Motor de voz:", self.engine);
        layout.addRow("Perfil phonem (-l):", self.language);
        preview = QPushButton("Probar voz");
        preview.clicked.connect(lambda: parent.preview_voice(self.language.text().strip() or "es-uy", self.engine.currentData(), self.user_name.text().strip(), self.spoken_name.text().strip()));
        layout.addRow(preview);
        layout.addRow(self.roaming);
        layout.addRow("Escala del avatar:", self.scale);
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel);
        buttons.accepted.connect(self.accept);
        buttons.rejected.connect(self.reject);
        layout.addRow(buttons);

    def apply_to(self, config):
        config.user_name = self.user_name.text().strip();
        config.spoken_name = self.spoken_name.text().strip();
        config.name_onboarding_complete = True;
        config.model_enabled = self.model_on.isChecked();
        config.endpoint = self.endpoint.text().strip();
        config.model = self.model.text().strip();
        config.voice_enabled = self.voice.isChecked();
        config.voice_language = self.language.text().strip() or "es-uy";
        config.voice_engine = self.engine.currentData();
        config.roaming = self.roaming.isChecked();
        config.scale = self.scale.value();


class LumenDesktop(QWidget):
    def __init__(self, config, store):
        super().__init__();
        self.config = config;
        self.store = store;
        self.chat_window = None;
        self.atlas = QPixmap(str(atlas_path()));
        if self.atlas.isNull() or self.atlas.width() != CELL_WIDTH * 8 or self.atlas.height() != CELL_HEIGHT * 9:
            raise RuntimeError("Atlas del avatar público incorrecto: esperaba 1536×1872");
        self.setWindowTitle(pet_metadata()["displayName"]);
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint);
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground);
        self.setMouseTracking(True);
        self.setToolTip("Lumen: doble clic para conversar · botón derecho para opciones");
        self._state = "idle";
        self._index = 0;
        self._frames_left = 0;
        self._drag_start = None;
        self._walking_direction = 1;
        self._scaled = QPixmap();
        self._set_frame();
        screen = QApplication.primaryScreen().availableGeometry();
        self.move(screen.left() + (screen.width() - self.width()) // 2, screen.bottom() - self.height() - 24);
        self.timer = QTimer(self);
        self.timer.setInterval(155);
        self.timer.timeout.connect(self._tick);
        self.timer.start();

    def _set_frame(self):
        spec = frame(self._state, self._index);
        source = self.atlas.copy(QRect(spec.x, spec.y, spec.width, spec.height));
        self._scaled = source.scaled(round(spec.width * self.config.scale), round(spec.height * self.config.scale), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation);
        self.resize(self._scaled.size());
        self.setMask(QRegion(self._scaled.mask()));
        self.update();

    def paintEvent(self, _event):
        painter = QPainter(self);
        painter.drawPixmap(0, 0, self._scaled);
        painter.end();

    def _animate(self, state):
        self._state = state;
        self._index = 0;
        self._frames_left = STATES[state][1];
        self._set_frame();

    def _tick(self):
        if self._frames_left > 0:
            self._frames_left -= 1;
            self._index = (self._index + 1) % STATES[self._state][1];
            if self._frames_left == 0:
                self._state = "idle";
                self._index = 0;
        else:
            if self.config.roaming and random.randrange(100) < 3:
                self._walking_direction = random.choice((-1, 1));
                self._animate("right" if self._walking_direction > 0 else "left");
            elif random.randrange(100) < 2:
                self._animate(random.choice(("wave", "wait", "think")));
            else:
                self._index = (self._index + 1) % STATES["idle"][1];
        if self._state in ("right", "left") and self.config.roaming and self._drag_start is None:
            available = self.screen().availableGeometry();
            new_x = max(available.left(), min(self.x() + 7 * self._walking_direction, available.right() - self.width()));
            self.move(new_x, self.y());
        self._set_frame();

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.globalPosition().toPoint() - self.pos();
            event.accept();
        else:
            super().mousePressEvent(event);

    def mouseMoveEvent(self, event):
        if self._drag_start is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_start);
            event.accept();
        else:
            super().mouseMoveEvent(event);

    def mouseReleaseEvent(self, event):
        self._drag_start = None;
        super().mouseReleaseEvent(event);

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_chat();
        super().mouseDoubleClickEvent(event);

    def contextMenuEvent(self, event):
        menu = QMenu(self);
        talk = menu.addAction("Conversar con Lumen…");
        wave = menu.addAction("Saludar");
        jump = menu.addAction("Saltar");
        walk = menu.addAction("Pasear" if not self.config.roaming else "Dejar de pasear");
        silence = menu.addAction("■ Detener voz");
        menu.addSeparator();
        silence = menu.addAction("Detener voz");
        options = menu.addAction("Preferencias…");
        menu.addSeparator();
        quit_action = menu.addAction("Salir de Σlux");
        choice = menu.exec(event.globalPos());
        if choice == talk:
            self.open_chat();
        elif choice == wave:
            self._animate("wave");
        elif choice == jump:
            self._animate("jump");
        elif choice == walk:
            self.config.roaming = not self.config.roaming;
            save(self.config);
        elif choice == silence:
            from .voice import stop;
            stop();
        elif choice == silence:
            from .voice import stop;
            stop();
        elif choice == options:
            self.open_preferences();
        elif choice == quit_action:
            QApplication.instance().quit();

    def preview_voice(self, language, engine, user_name="", spoken_name=""):
        from .voice import speak;
        from .voice import speech_text;
        greeting = f"Hola, {user_name}." if user_name else "Hola.";
        sample = speech_text(f"{greeting} Soy Lumen. Ahora puedo hablar con nuestra voz configurada.", user_name, spoken_name);
        if not speak(sample, language, engine):
            QMessageBox.warning(self, "Voz no disponible", "No encontré phonem, pronounce y ffplay (o el motor elegido). Revisá que estén instalados y ejecutables.");

    def ask_user_name(self):
        """One-time GUI onboarding, including upgrades from configs without name fields.""";
        if self.config.name_onboarding_complete:
            return;
        name, accepted = QInputDialog.getText(
            self,
            "Σlux · Conocernos",
            "¡Hola! ¿Cómo querés que te llame?\nPodés cambiarlo luego en Preferencias.",
            QLineEdit.EchoMode.Normal,
            self.config.user_name,
        );
        if accepted:
            self.config.user_name = name.strip();
        self.config.name_onboarding_complete = True;
        save(self.config);

    def open_chat(self):
        from .chat_window import ChatWindow;
        if self.chat_window is None:
            self.chat_window = ChatWindow(self.config, self.store, self);
        self.chat_window.show();
        self.chat_window.raise_();
        self.chat_window.activateWindow();
        self.chat_window.line.setFocus();

    def open_preferences(self):
        dialog = Preferences(self.config, self);
        if dialog.exec() == QDialog.DialogCode.Accepted:
            dialog.apply_to(self.config);
            save(self.config);
            self._set_frame();
            if self.chat_window is not None:
                self.chat_window.refresh_connection_status();


def main():
    parser = argparse.ArgumentParser(description="Σlux · Lumen Linux desktop companion");
    parser.add_argument("--version", action="version", version=f"sumlux {__version__}");
    args = parser.parse_args();
    _ = args;
    from .paths import config_path;
    os.umask(0o077);
    config = load();
    if not config_path().exists():
        save(config);
    app = QApplication(sys.argv[:1]);
    app.setApplicationName("Σlux");
    store = ConversationStore();
    avatar = LumenDesktop(config, store);
    def shutdown():
        from .voice import stop;
        stop();
        if avatar.chat_window is not None:
            avatar.chat_window.shutdown();
        store.close();
    app.aboutToQuit.connect(shutdown);
    avatar.show();
    QTimer.singleShot(0, avatar.ask_user_name);
    return app.exec();


if __name__ == "__main__":
    sys.exit(main());
