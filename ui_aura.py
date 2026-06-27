"""
AuraUI - Cinematic ultra-minimal AI assistant interface.
A living AI consciousness experience.
"""

import sys
import math
import time
import os
import json
from pathlib import Path
from typing import Callable, Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QScrollArea, QGraphicsBlurEffect,
    QSizePolicy, QFrame
)
from PyQt6.QtCore import (
    Qt, QTimer, QRectF, pyqtSignal, QPointF
)
from PyQt6.QtGui import (
    QPainter, QColor, QBrush, QRadialGradient, QPen, QFont,
    QLinearGradient, QPainterPath, QCursor, QEnterEvent,
    QBlurFoundation
)


# ============================================================================
# CONSTANTS
# ============================================================================

COLORS = {
    "bg_deep": QColor("#030810"),
    "bg_center": QColor("#0a1628"),
    "bg_ambient": QColor("#061020"),
    "orb_core": QColor("#00e5ff"),
    "orb_glow": QColor("#0088aa"),
    "orb_inner": QColor("#00ccff"),
    "waveform": QColor("#00ffff"),
    "waveform_soft": QColor("#008888"),
    "particle": QColor("#00ccff"),
    "glass_bg": QColor("#0a1520"),
    "glass_border": QColor("#1a3040"),
    "text_user": QColor("#ffffff"),
    "text_jarvis": QColor("#00ddff"),
    "text_dim": QColor("#556677"),
    "text_timestamp": QColor("#334455"),
    "muted_red": QColor("#ff4444"),
    "upload_glow": QColor("#00aaff"),
}

STATE_PARAMS = {
    "INITIALISING": {"breath_speed": 0.4, "glow_intensity": 0.5, "wave_amplitude": 0.1, "particle_speed": 0.3, "bloom": 0.3},
    "IDLE": {"breath_speed": 0.35, "glow_intensity": 0.45, "wave_amplitude": 0.08, "particle_speed": 0.25, "bloom": 0.35},
    "LISTENING": {"breath_speed": 0.7, "glow_intensity": 0.75, "wave_amplitude": 0.4, "particle_speed": 0.5, "bloom": 0.5},
    "THINKING": {"breath_speed": 0.5, "glow_intensity": 0.6, "wave_amplitude": 0.25, "particle_speed": 0.35, "bloom": 0.45},
    "PROCESSING": {"breath_speed": 0.6, "glow_intensity": 0.7, "wave_amplitude": 0.45, "particle_speed": 0.45, "bloom": 0.5},
    "SPEAKING": {"breath_speed": 1.0, "glow_intensity": 0.95, "wave_amplitude": 0.8, "particle_speed": 0.8, "bloom": 0.7},
    "MUTED": {"breath_speed": 0.2, "glow_intensity": 0.2, "wave_amplitude": 0.03, "particle_speed": 0.15, "bloom": 0.15},
}

CONFIG_PATH = Path(__file__).parent / "config" / "api_keys.json"


# ============================================================================
# PARTICLE SYSTEM
# ============================================================================

class Particle:
    def __init__(self, center_x: float, center_y: float, orbit_radius: float):
        self.center_x = center_x
        self.center_y = center_y
        self.orbit_radius = orbit_radius
        self.angle = (hash(time.time() + id(self)) % 1000) / 1000.0 * 2 * math.pi
        self.speed = 0.2 + (hash(time.time() * 7 + id(self)) % 100) / 100.0 * 0.3
        self.life = 0.6 + (hash(time.time() * 13 + id(self)) % 100) / 250.0
        self.decay = 0.001 + (hash(time.time() * 3 + id(self)) % 50) / 5000.0
        self.size = 1.0 + (hash(time.time() * 11 + id(self)) % 20) / 15.0
        self.orbit_tilt = (hash(time.time() * 17 + id(self)) % 100) / 100.0 * 0.3 - 0.15
        self.update_position()

    def update_position(self):
        self.x = self.center_x + math.cos(self.angle) * self.orbit_radius
        self.y = self.center_y + math.sin(self.angle) * self.orbit_radius * (1 + self.orbit_tilt)

    def update(self, speed_mult: float = 1.0, center_x: float = None, center_y: float = None):
        if center_x is not None:
            self.center_x = center_x
        if center_y is not None:
            self.center_y = center_y
        self.angle += self.speed * speed_mult * 0.015
        self.life -= self.decay
        self.update_position()
        return self.life > 0


# ============================================================================
# ORB CANVAS - The Soul of the Interface
# ============================================================================

class OrbCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMinimumSize(500, 500)

        self._state = "INITIALISING"
        self._phase = 0.0
        self._audio_level = 0.0
        self._target_audio_level = 0.0
        self._particles = []
        self._center = (0, 0)

        self._breath_scale = 1.0
        self._glow_intensity = 0.5
        self._wave_amplitude = 0.1
        self._bloom = 0.3

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(16)

        self._init_particles()

    def _init_particles(self):
        self._particles = []
        for _ in range(24):
            orbit = 60 + (hash(time.time() + _ * 7) % 80)
            self._particles.append(Particle(0, 0, orbit))

    def set_state(self, state: str):
        self._state = state

    def update_audio_level(self, level: float):
        self._target_audio_level = max(0.0, min(1.0, level))

    def _animate(self):
        self._phase += 0.016

        # Smooth audio level
        self._audio_level += (self._target_audio_level - self._audio_level) * 0.12

        params = STATE_PARAMS.get(self._state, STATE_PARAMS["IDLE"])
        breath_speed = params["breath_speed"]
        particle_speed = params["particle_speed"]

        # Breathing animation - slow and organic
        breath_cycle = math.sin(self._phase * breath_speed)
        self._breath_scale = 0.94 + breath_cycle * 0.06

        # Smooth parameter transitions
        self._glow_intensity += (params["glow_intensity"] - self._glow_intensity) * 0.04
        self._wave_amplitude += (params["wave_amplitude"] - self._wave_amplitude) * 0.06
        self._bloom += (params["bloom"] - self._bloom) * 0.04

        # Update center
        self._center = (self.width() / 2, self.height() / 2)
        cx, cy = self._center

        # Update particles
        dead_particles = []
        for p in self._particles:
            alive = p.update(particle_speed, cx, cy)
            if not alive:
                dead_particles.append(p)

        for p in dead_particles:
            self._particles.remove(p)
            self._particles.append(Particle(cx, cy, 60 + (hash(time.time() + len(self._particles)) % 80)))

        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.LosslessImageRendering)

        cx, cy = self._center

        # Draw cinematic background
        self._draw_cinematic_background(p)

        # Draw ambient light bloom
        self._draw_ambient_bloom(p, cx, cy)

        # Draw outer atmosphere
        self._draw_atmosphere(p, cx, cy)

        # Draw waveform rings
        self._draw_waveform_rings(p, cx, cy)

        # Draw particles
        self._draw_particles(p, cx, cy)

        # Draw core with bloom
        self._draw_core(p, cx, cy)

    def _draw_cinematic_background(self, p: QPainter):
        rect = self.rect()
        w, h = rect.width(), rect.height()

        # Deep base layer
        base_gradient = QRadialGradient(w/2, h/2, max(w, h) * 0.8)
        base_gradient.setColorAt(0, COLORS["bg_center"])
        base_gradient.setColorAt(0.5, COLORS["bg_ambient"])
        base_gradient.setColorAt(1, COLORS["bg_deep"])
        p.fillRect(rect, QBrush(base_gradient))

        # Subtle radial light from center
        center_gradient = QRadialGradient(w/2, h/2, max(w, h) * 0.5)
        center_gradient.setColorAt(0, QColor(0, 40, 60, 40))
        center_gradient.setColorAt(1, QColor(0, 0, 0, 0))
        p.fillRect(rect, QBrush(center_gradient))

    def _draw_ambient_bloom(self, p: QPainter, cx: float, cy: float):
        # Soft ambient glow emanating from center
        bloom_radius = min(self.width(), self.height()) * 0.4 * self._breath_scale

        for i in range(5, 0, -1):
            alpha = self._bloom * 0.08 * (1 - i / 6)
            radius = bloom_radius * (1 + i * 0.4)

            gradient = QRadialGradient(cx, cy, radius)
            if self._state == "MUTED":
                gradient.setColorAt(0, QColor(255, 50, 50, int(255 * alpha)))
                gradient.setColorAt(1, QColor(100, 0, 0, 0))
            else:
                gradient.setColorAt(0, QColor(0, 150, 200, int(255 * alpha)))
                gradient.setColorAt(1, QColor(0, 50, 100, 0))

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(gradient))
            p.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))

    def _draw_atmosphere(self, p: QPainter, cx: float, cy: float):
        # Soft rotating atmosphere rings
        base_radius = min(self.width(), self.height()) * 0.32 * self._breath_scale

        for ring in range(2):
            ring_phase = self._phase * 0.3 + ring * math.pi
            ring_alpha = 0.15 * self._glow_intensity * (1 - ring * 0.3)

            path = QPainterPath()
            num_points = 180

            for i in range(num_points):
                angle = (i / num_points) * 2 * math.pi
                wave = math.sin(angle * 6 + ring_phase) * 8 * self._wave_amplitude
                wave += math.sin(angle * 3 - ring_phase * 0.7) * 4 * self._wave_amplitude
                radius = base_radius * (1 + ring * 0.15) + wave

                x = cx + math.cos(angle) * radius
                y = cy + math.sin(angle) * radius

                if i == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)

            path.closeSubpath()

            color = QColor(COLORS["waveform_soft"].red(), COLORS["waveform_soft"].green(),
                          COLORS["waveform_soft"].blue(), int(255 * ring_alpha))
            pen = QPen(color, 1.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawPath(path)

    def _draw_waveform_rings(self, p: QPainter, cx: float, cy: float):
        # Main waveform ring
        base_radius = min(self.width(), self.height()) * 0.28 * self._breath_scale

        # Wave amplitude based on state + audio
        wave_amp = self._wave_amplitude * (1 + self._audio_level * 0.6)

        # Primary waveform
        path = QPainterPath()
        num_points = 200

        for i in range(num_points):
            angle = (i / num_points) * 2 * math.pi

            # Multi-layered wave for organic feel
            wave1 = math.sin(angle * 8 + self._phase * 2.5) * wave_amp * 25
            wave2 = math.sin(angle * 4 - self._phase * 1.8) * wave_amp * 12
            wave3 = math.sin(angle * 12 + self._phase * 3.2) * wave_amp * 6
            total_wave = wave1 + wave2 + wave3

            radius = base_radius + total_wave
            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius

            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)

        path.closeSubpath()

        # Soft gradient stroke
        alpha = int(180 * self._glow_intensity)
        color = QColor(COLORS["waveform"].red(), COLORS["waveform"].green(),
                      COLORS["waveform"].blue(), alpha)
        pen = QPen(color, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.drawPath(path)

        # Inner glow ring
        inner_path = QPainterPath()
        inner_radius = base_radius * 0.85

        for i in range(num_points):
            angle = (i / num_points) * 2 * math.pi
            wave = math.sin(angle * 6 + self._phase * 2) * wave_amp * 15
            radius = inner_radius + wave
            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius

            if i == 0:
                inner_path.moveTo(x, y)
            else:
                inner_path.lineTo(x, y)

        inner_path.closeSubpath()

        inner_alpha = int(80 * self._glow_intensity)
        inner_color = QColor(COLORS["waveform"].red(), COLORS["waveform"].green(),
                            COLORS["waveform"].blue(), inner_alpha)
        inner_pen = QPen(inner_color, 1.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(inner_pen)
        p.drawPath(inner_path)

    def _draw_particles(self, p: QPainter, cx: float, cy: float):
        for particle in self._particles:
            alpha = int(180 * particle.life * self._glow_intensity * 0.7)
            size = particle.size * (1 + self._audio_level * 0.3)

            color = QColor(COLORS["particle"].red(), COLORS["particle"].green(),
                          COLORS["particle"].blue(), alpha)

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(color))
            p.drawEllipse(QRectF(
                particle.x - size,
                particle.y - size,
                size * 2,
                size * 2
            ))

    def _draw_core(self, p: QPainter, cx: float, cy: float):
        base_radius = min(self.width(), self.height()) * 0.1 * self._breath_scale

        if self._state == "MUTED":
            core_color = COLORS["muted_red"]
        else:
            core_color = COLORS["orb_core"]

        # Outer glow
        glow_radius = base_radius * 2.5
        for i in range(6, 0, -1):
            alpha = self._glow_intensity * 0.12 * (1 - i / 7)
            r = base_radius * (1 + i * 0.5)

            gradient = QRadialGradient(cx, cy, r)
            gradient.setColorAt(0, QColor(core_color.red(), core_color.green(), core_color.blue(), int(255 * alpha)))
            gradient.setColorAt(1, QColor(0, 0, 0, 0))

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(gradient))
            p.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

        # Core gradient
        core_gradient = QRadialGradient(cx, cy, base_radius)
        core_gradient.setColorAt(0, QColor(255, 255, 255, 230))
        core_gradient.setColorAt(0.3, QColor(core_color.red(), core_color.green(), core_color.blue(), 200))
        core_gradient.setColorAt(0.7, QColor(core_color.red() * 0.7, core_color.green() * 0.7, core_color.blue() * 0.7, 120))
        core_gradient.setColorAt(1, QColor(core_color.red() * 0.3, core_color.green() * 0.3, core_color.blue() * 0.3, 0))

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(core_gradient))
        p.drawEllipse(QRectF(cx - base_radius, cy - base_radius, base_radius * 2, base_radius * 2))

        # Inner bright spot
        inner_radius = base_radius * 0.4
        inner_gradient = QRadialGradient(cx, cy, inner_radius)
        inner_gradient.setColorAt(0, QColor(255, 255, 255, 255))
        inner_gradient.setColorAt(0.5, QColor(200, 240, 255, 150))
        inner_gradient.setColorAt(1, QColor(0, 150, 200, 0))

        p.setBrush(QBrush(inner_gradient))
        p.drawEllipse(QRectF(cx - inner_radius, cy - inner_radius, inner_radius * 2, inner_radius * 2))


# ============================================================================
# GLASSMORPHISM CONTAINER
# ============================================================================

class GlassWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()

        # Glass background with soft gradient
        glass_gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        glass_gradient.setColorAt(0, QColor(15, 30, 45, 180))
        glass_gradient.setColorAt(1, QColor(10, 20, 35, 160))

        # Draw glass panel
        path = QPainterPath()
        radius = 24
        path.addRoundedRect(QRectF(rect), radius, radius)
        p.fillPath(path, QBrush(glass_gradient))

        # Subtle border
        border_color = QColor(COLORS["glass_border"].red(), COLORS["glass_border"].green(),
                              COLORS["glass_border"].blue(), 60)
        pen = QPen(border_color, 1)
        p.setPen(pen)
        p.drawPath(path)


# ============================================================================
# MESSAGE WIDGET
# ============================================================================

class Message:
    def __init__(self, text: str, source: str, timestamp: float):
        self.text = text
        self.source = source
        self.timestamp = timestamp
        self.opacity = 0.0
        self.target_opacity = 1.0


class ConversationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._messages = []
        self._scroll_timer = QTimer(self)
        self._scroll_timer.timeout.connect(self._check_animation)
        self._scroll_timer.start(50)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def _check_animation(self):
        needs_update = False
        for msg in self._messages:
            if msg.opacity < msg.target_opacity:
                msg.opacity = min(msg.opacity + 0.08, msg.target_opacity)
                needs_update = True
        if needs_update:
            self.update()

    def add_message(self, text: str, source: str = "jarvis"):
        msg = Message(text, source, time.time())
        self._messages.append(msg)
        self.update()

    def clear(self):
        self._messages.clear()
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        rect = self.rect()
        center_x = rect.center().x()

        y = 30
        for msg in self._messages[-15:]:  # Last 15 messages
            if msg.opacity <= 0:
                continue

            opacity = msg.opacity

            # Source label
            if msg.source == "user":
                source_color = QColor(255, 255, 255, int(160 * opacity))
                msg_color = QColor(255, 255, 255, int(220 * opacity))
                source_text = "YOU"
                align = Qt.AlignmentFlag.AlignRight
                msg_x = center_x
            elif msg.source == "system":
                source_color = QColor(80, 100, 120, int(120 * opacity))
                msg_color = QColor(100, 120, 140, int(150 * opacity))
                source_text = ""
                align = Qt.AlignmentFlag.AlignCenter
                msg_x = center_x
            else:
                source_color = QColor(0, 200, 230, int(160 * opacity))
                msg_color = QColor(0, 220, 255, int(220 * opacity))
                source_text = "AURA"
                align = Qt.AlignmentFlag.AlignLeft
                msg_x = 0

            # Draw source label
            if source_text:
                font_label = QFont("Inter", 10, QFont.Weight.Medium)
                font_label.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 3)
                p.setFont(font_label)
                p.setPen(source_color)
                p.drawText(QRect(40, y, rect.width() - 80, 18), align, source_text)
                y += 22

            # Draw message text with word wrap
            font_msg = QFont("Inter", 13, QFont.Weight.Light)
            p.setFont(font_msg)
            p.setPen(msg_color)

            max_width = rect.width() - 120
            words = msg.text.split()
            lines = []
            current_line = ""

            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                if p.fontMetrics().horizontalAdvance(test_line) <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)

            for line in lines:
                msg_rect = QRect(msg_x, y, rect.width() - 80, 22)
                p.drawText(msg_rect, align, line)
                y += 24

            y += 35  # Extra spacing


# ============================================================================
# UPLOAD BUTTON
# ============================================================================

class UploadButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(52, 52)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._hovering = False
        self._glow_phase = 0.0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._pulse)
        self._timer.start(40)

    def _pulse(self):
        self._glow_phase += 0.08
        self.update()

    def enterEvent(self, event: QEnterEvent):
        self._hovering = True
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovering = False
        super().leaveEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = self.width() / 2
        cy = self.height() / 2
        radius = 22

        # Glow intensity
        glow_base = 0.25 + math.sin(self._glow_phase) * 0.08
        if self._hovering:
            glow_base = 0.55 + math.sin(self._glow_phase) * 0.15

        # Outer glow
        for i in range(4, 0, -1):
            alpha = glow_base * 0.15 * (1 - i / 5)
            r = radius + i * 6
            color = QColor(COLORS["upload_glow"].red(), COLORS["upload_glow"].green(),
                          COLORS["upload_glow"].blue(), int(255 * alpha))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(color))
            p.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

        # Glass circle background
        bg_gradient = QRadialGradient(cx, cy - 5, radius)
        bg_gradient.setColorAt(0, QColor(30, 50, 70, 220))
        bg_gradient.setColorAt(1, QColor(15, 25, 40, 200))

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(bg_gradient))
        p.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))

        # Border
        border_alpha = 100 + (60 if self._hovering else 0)
        border_color = QColor(COLORS["upload_glow"].red(), COLORS["upload_glow"].green(),
                              COLORS["upload_glow"].blue(), int(border_alpha * glow_base))
        pen = QPen(border_color, 1.2)
        p.setPen(pen)
        p.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))

        # Upload icon (+)
        icon_alpha = 180 + (40 if self._hovering else 0)
        icon_color = QColor(COLORS["upload_glow"].red(), COLORS["upload_glow"].green(),
                           COLORS["upload_glow"].blue(), int(icon_alpha * glow_base * 1.5))
        p.setPen(QPen(icon_color, 2))

        p.drawLine(int(cx - 7), int(cy), int(cx + 7), int(cy))
        p.drawLine(int(cx), int(cy - 9), int(cx), int(cy + 1))


# ============================================================================
# SETUP OVERLAY
# ============================================================================

class SetupOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._build_ui()
        self.hide()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        title = QLabel("AURA")
        title.setFont(QFont("Inter", 42, QFont.Weight.Light))
        title.setStyleSheet("color: #00ddff; background: transparent; letter-spacing: 12px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("AI Assistant Setup")
        subtitle.setFont(QFont("Inter", 12, QFont.Weight.Light))
        subtitle.setStyleSheet("color: #446688; background: transparent;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        self._api_key_input = QLineEdit()
        self._api_key_input.setPlaceholderText("Enter Gemini API Key")
        self._api_key_input.setFixedWidth(360)
        self._api_key_input.setFont(QFont("Inter", 12))
        self._api_key_input.setStyleSheet("""
            QLineEdit {
                background: rgba(10, 22, 40, 200);
                border: 1px solid rgba(0, 100, 150, 100);
                border-radius: 12px;
                padding: 14px 18px;
                color: #00ddff;
                letter-spacing: 0.5px;
            }
            QLineEdit:focus {
                border: 1px solid #00aaff;
            }
            QLineEdit::placeholder {
                color: #335566;
            }
        """)
        layout.addWidget(self._api_key_input)

        save_btn = QPushButton("Continue")
        save_btn.setFixedSize(120, 44)
        save_btn.setFont(QFont("Inter", 12, QFont.Weight.Medium))
        save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        save_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0, 80, 120, 150);
                border: 1px solid rgba(0, 180, 220, 150);
                border-radius: 12px;
                color: #00ddff;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: rgba(0, 100, 150, 180);
                border: 1px solid #00ccff;
            }
        """)
        save_btn.clicked.connect(self._save_api_key)
        layout.addWidget(save_btn)

        self.setLayout(layout)

    def _save_api_key(self):
        api_key = self._api_key_input.text().strip()
        if api_key:
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            config = {}
            if CONFIG_PATH.exists():
                with open(CONFIG_PATH, 'r') as f:
                    config = json.load(f)

            config["gemini_api_key"] = api_key

            with open(CONFIG_PATH, 'w') as f:
                json.dump(config, f, indent=2)

            self.hide()

    def show_setup(self):
        self.show()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(3, 8, 16, 230))


# ============================================================================
# MAIN WINDOW
# ============================================================================

class AuraMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._muted = False
        self._state = "INITIALISING"
        self._current_file = None
        self._on_text_command = None

        self._build_ui()
        self._center_window()

    def _build_ui(self):
        self.setWindowTitle("Aura")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)

        central = QWidget()
        self.setCentralWidget(central)

        # Main vertical layout
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Orb canvas - takes upper 60%
        self._orb = OrbCanvas()
        self._orb.setMinimumHeight(380)
        self._orb.setMaximumHeight(500)
        main_layout.addWidget(self._orb, stretch=6)

        # Glassmorphism conversation panel - lower portion
        conversation_container = GlassWidget()
        conversation_layout = QVBoxLayout(conversation_container)
        conversation_layout.setContentsMargins(20, 15, 20, 15)

        self._conversation = ConversationWidget()
        conversation_layout.addWidget(self._conversation)

        main_layout.addWidget(conversation_container, stretch=4)

        # Upload button - bottom right, floating
        self._upload_btn = UploadButton()
        self._upload_btn.setParent(self)
        self._upload_btn.clicked.connect(self._on_upload_clicked)

        # Setup overlay
        self._setup_overlay = SetupOverlay(self)
        self._setup_overlay.resize(self.size())

        self.resize(QSize(580, 820))

    def _center_window(self):
        screen = QApplication.primaryScreen()
        if screen:
            rect = screen.availableGeometry()
            self.move(rect.center().x() - self.width() // 2, rect.center().y() - self.height() // 2)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_upload_btn'):
            self._upload_btn.move(self.width() - 76, self.height() - 86)
        if hasattr(self, '_setup_overlay'):
            self._setup_overlay.resize(event.size())

    def _on_upload_clicked(self):
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Select file")
        if path:
            self._current_file = path
            if self._on_text_command:
                self._on_text_command(f"File uploaded: {Path(path).name}")

    # Public API
    @property
    def muted(self) -> bool:
        return self._muted

    @muted.setter
    def muted(self, value: bool):
        self._muted = value
        if value:
            self._orb.set_state("MUTED")
        else:
            self._orb.set_state("IDLE")

    @property
    def current_file(self) -> Optional[str]:
        return self._current_file

    @current_file.setter
    def current_file(self, value: Optional[str]):
        self._current_file = value

    @property
    def on_text_command(self) -> Optional[Callable]:
        return self._on_text_command

    @on_text_command.setter
    def on_text_command(self, value: Callable):
        self._on_text_command = value

    def set_state(self, state: str):
        self._state = state
        self._orb.set_state(state)

    def write_log(self, text: str, source: str = "jarvis"):
        self._conversation.add_message(text, source)

    def start_speaking(self):
        self.set_state("SPEAKING")

    def stop_speaking(self):
        if self._muted:
            self.set_state("MUTED")
        else:
            self.set_state("LISTENING")

    def update_audio_level(self, level: float):
        self._orb.update_audio_level(level)

    def wait_for_api_key(self):
        if not CONFIG_PATH.exists() or not json.loads(CONFIG_PATH.read_text()).get("gemini_api_key"):
            self._setup_overlay.show_setup()


# ============================================================================
# AURA UI - PUBLIC WRAPPER
# ============================================================================

class AuraUI:
    """
    Cinematic ultra-minimal AI assistant interface.
    API compatible with JarvisUI.
    """

    def __init__(self, face_image_path: str = "face.png"):
        self._app = QApplication.instance()
        if self._app is None:
            self._app = QApplication(sys.argv)

        self._win = AuraMainWindow()
        self._win.show()

        _ = face_image_path  # Unused in Aura

    @property
    def muted(self) -> bool:
        return self._win.muted

    @muted.setter
    def muted(self, value: bool):
        self._win.muted = value

    @property
    def current_file(self) -> Optional[str]:
        return self._win.current_file

    @current_file.setter
    def current_file(self, value: Optional[str]):
        self._win.current_file = value

    @property
    def on_text_command(self) -> Optional[Callable]:
        return self._win.on_text_command

    @on_text_command.setter
    def on_text_command(self, value: Callable):
        self._win.on_text_command = value

    def set_state(self, state: str):
        self._win.set_state(state)

    def write_log(self, text: str, source: str = "jarvis"):
        self._win.write_log(text, source)

    def start_speaking(self):
        self._win.start_speaking()

    def stop_speaking(self):
        self._win.stop_speaking()

    def wait_for_api_key(self):
        self._win.wait_for_api_key()

    def update_audio_level(self, level: float):
        self._win.update_audio_level(level)

    @property
    def root(self):
        class RootShim:
            def __init__(self, app):
                self._app = app
            def mainloop(self):
                self._app.exec()
        return RootShim(self._app)


# ============================================================================
# STANDALONE TEST
# ============================================================================

if __name__ == "__main__":
    ui = AuraUI()

    ui.write_log("Hello, I'm Aura. How can I assist you today?", "jarvis")

    import time
    time.sleep(1)
    ui.set_state("LISTENING")
    ui.write_log("Open Spotify and play some music", "user")

    time.sleep(1)
    ui.set_state("THINKING")
    ui.write_log("Opening Spotify for you...", "jarvis")

    time.sleep(1)
    ui.set_state("SPEAKING")

    time.sleep(1)
    ui.set_state("IDLE")

    ui.root.mainloop()
