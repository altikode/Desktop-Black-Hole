import sys
import os
import math
import random
from PyQt5.QtWidgets import QApplication, QWidget, QMenu, QAction
from PyQt5.QtGui import QPainter, QColor, QRadialGradient, QPen
from PyQt5.QtCore import Qt, QTimer, QPointF
from send2trash import send2trash

class BlackHole(QWidget):
    def __init__(self):
        super().__init__()

        # Masaüstü katmanı ayarları (pencerelerin arkasında kalır)
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAcceptDrops(True)

        # Küçültülmüş boyut (200px'den 125px'e düşürüldü)
        self.base_size = 125
        self.resize(self.base_size, self.base_size)

        self.angle = 0.0
        self.pulse = 0.0
        self.is_hovered = False
        self.eating_animation = 0
        self.eaten_count = 0

        # Parçacık mesafeleri de yeni küçük boyuta göre uyarlandı
        self.particles = []
        for _ in range(28):
            self.particles.append({
                'dist': random.uniform(22, 52),
                'angle': random.uniform(0, math.pi * 2),
                'speed': random.uniform(0.03, 0.08),
                'size': random.uniform(1.2, 2.6),
                'color': random.choice([
                    QColor(180, 70, 255, 200),
                    QColor(70, 190, 255, 220),
                    QColor(255, 120, 200, 180)
                ])
            })

        self.drag_position = None

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_physics)
        self.timer.start(16)

    def get_work_area(self):
        screen = QApplication.primaryScreen()
        return screen.availableGeometry()

    def update_physics(self):
        self.angle += 0.04
        self.pulse += 0.05

        for p in self.particles:
            p['angle'] += p['speed']
            if self.eating_animation > 0:
                p['dist'] -= 1.6
                if p['dist'] < 6:
                    p['dist'] = random.uniform(40, 58)

        if self.eating_animation > 0:
            self.eating_animation -= 1

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center_x = self.width() / 2
        center_y = self.height() / 2
        center = QPointF(center_x, center_y)

        # Fare yakalama zemini
        painter.setBrush(QColor(0, 0, 0, 1))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())

        scale_mod = 1.18 if self.is_hovered else (1.3 if self.eating_animation > 0 else 1.0)
        pulse_val = math.sin(self.pulse) * 1.8
        
        # Küçültülmüş yarıçap oranları
        core_radius = (20 * scale_mod) + pulse_val
        accretion_radius = (48 * scale_mod)

        # 1. Dış Parıltı / Aura
        outer_grad = QRadialGradient(center, accretion_radius + 10)
        if self.eating_animation > 0:
            outer_grad.setColorAt(0.0, QColor(255, 40, 40, 180))
            outer_grad.setColorAt(0.7, QColor(255, 120, 0, 70))
        elif self.is_hovered:
            outer_grad.setColorAt(0.0, QColor(0, 255, 200, 180))
            outer_grad.setColorAt(0.7, QColor(0, 150, 255, 70))
        else:
            outer_grad.setColorAt(0.0, QColor(140, 40, 255, 130))
            outer_grad.setColorAt(0.7, QColor(0, 180, 255, 50))
        outer_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(outer_grad)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, accretion_radius + 10, accretion_radius + 10)

        # 2. Dönen Gaz Diski
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(math.degrees(self.angle))
        
        disk_pen = QPen(QColor(160, 90, 255, 160), 2.0)
        painter.setPen(disk_pen)
        painter.drawEllipse(QPointF(0, 0), accretion_radius * 0.9, accretion_radius * 0.35)
        
        disk_pen.setColor(QColor(0, 230, 255, 200))
        disk_pen.setWidthF(1.2)
        painter.setPen(disk_pen)
        painter.drawEllipse(QPointF(0, 0), accretion_radius * 0.7, accretion_radius * 0.25)
        painter.restore()

        # 3. Yörünge Parçacıkları
        for p in self.particles:
            px = center_x + math.cos(p['angle']) * (p['dist'] * scale_mod)
            py = center_y + math.sin(p['angle']) * (p['dist'] * scale_mod) * 0.6
            painter.setBrush(p['color'])
            painter.drawEllipse(QPointF(px, py), p['size'], p['size'])

        # 4. Foton Çemberi
        glow_pen = QPen(QColor(255, 255, 255, 240), 1.8)
        painter.setPen(glow_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(center, core_radius + 1.5, core_radius + 1.5)

        # 5. Simsiyah Olay Ufku
        core_grad = QRadialGradient(center, core_radius)
        core_grad.setColorAt(0.0, QColor(0, 0, 0, 255))
        core_grad.setColorAt(0.9, QColor(5, 5, 12, 255))
        core_grad.setColorAt(1.0, QColor(40, 20, 60, 255))
        painter.setBrush(core_grad)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, core_radius, core_radius)

    # --- Mouse Tekerleği ile Boyutlandırma ---
    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        step = 15
        new_size = self.width() + (step if delta > 0 else -step)
        # Minimum 80px, maksimum 300px sınırı
        new_size = max(80, min(300, new_size))
        
        self.resize(new_size, new_size)
        event.accept()

    # --- Sürükle ve Bırak Olayları ---
    def dragEnterEvent(self, event):
        event.accept()
        self.is_hovered = True
        self.update()

    def dragMoveEvent(self, event):
        event.accept()

    def dragLeaveEvent(self, event):
        self.is_hovered = False
        self.update()
        event.accept()

    def dropEvent(self, event):
        self.is_hovered = False
        mime = event.mimeData()
        
        if mime.hasUrls():
            self.eating_animation = 30
            for url in mime.urls():
                clean_path = os.path.normpath(url.toLocalFile())
                if os.path.exists(clean_path):
                    try:
                        send2trash(clean_path)
                        self.eaten_count += 1
                    except Exception as e:
                        print(f"Hata: {e}")
            event.accept()
        else:
            event.ignore()
        self.update()

    # --- Taşıma ve Görev Çubuğu Kilidi ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position is not None:
            new_pos = event.globalPos() - self.drag_position
            
            work_area = self.get_work_area()
            min_x = work_area.left()
            max_x = work_area.right() - self.width() + 1
            min_y = work_area.top()
            max_y = work_area.bottom() - self.height() + 1

            clamped_x = max(min_x, min(new_pos.x(), max_x))
            clamped_y = max(min_y, min(new_pos.y(), max_y))

            self.move(clamped_x, clamped_y)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_position = None
        event.accept()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        info = QAction(f"Yutulan Nesne: {self.eaten_count}", self)
        info.setEnabled(False)
        menu.addAction(info)
        menu.addSeparator()

        exit_btn = QAction("Çıkış Yap", self)
        exit_btn.triggered.connect(QApplication.instance().quit)
        menu.addAction(exit_btn)
        menu.exec_(event.globalPos())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    hole = BlackHole()
    hole.show()
    sys.exit(app.exec_())