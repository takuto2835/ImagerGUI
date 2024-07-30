import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QProgressBar, QFileDialog, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal, Qt

class ImageWriterThread(QThread):
    progress_update = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, image_path, device):
        super().__init__()
        self.image_path = image_path
        self.device = device

    def run(self):
        try:
            total_size = os.path.getsize(self.image_path)
            with open(self.image_path, 'rb') as src, open(self.device, 'wb') as dst:
                written = 0
                while True:
                    chunk = src.read(4 * 1024 * 1024)  # 4MB chunks
                    if not chunk:
                        break
                    dst.write(chunk)
                    written += len(chunk)
                    progress = (written / total_size) * 100
                    self.progress_update.emit(f"{progress:.2f}% ({written} / {total_size} bytes)")
            self.finished.emit(True, "Image written successfully!")
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")

class ImageWriterGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.image_label = QLabel("No Image Selected")
        layout.addWidget(self.image_label)

        select_button = QPushButton("Select Image")
        select_button.clicked.connect(self.select_image)
        layout.addWidget(select_button)

        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel("Device Path:"))
        self.device_entry = QLineEdit()        
        self.device_entry.setText("/dev/sda")  # デフォルト値を設定
        device_layout.addWidget(self.device_entry)
        layout.addLayout(device_layout)

        self.write_button = QPushButton("Write Image")
        self.write_button.clicked.connect(self.write_image)
        layout.addWidget(self.write_button)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("")
        layout.addWidget(self.progress_label)

        self.setLayout(layout)
        self.setWindowTitle("Image Writer")
        self.show()

    def select_image(self):
        self.image_path, _ = QFileDialog.getOpenFileName(self, "Select Image File")
        if self.image_path:
            self.image_label.setText(f"Selected Image: {self.image_path}")

    def write_image(self):
        if not hasattr(self, 'image_path') or not self.image_path:
            QMessageBox.warning(self, "Error", "No image selected!")
            return
        
        device = self.device_entry.text()
        if not device:
            QMessageBox.warning(self, "Error", "Device path is required!")
            return

        confirm = QMessageBox.question(self, "Confirm", f"Are you sure you want to write to {device}?", 
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.write_button.setEnabled(False)
            self.progress_bar.setValue(0)
            self.writer_thread = ImageWriterThread(self.image_path, device)
            self.writer_thread.progress_update.connect(self.update_progress)
            self.writer_thread.finished.connect(self.writing_finished)
            self.writer_thread.start()

    def update_progress(self, progress_text):
        progress = float(progress_text.split('%')[0])
        self.progress_bar.setValue(int(progress))
        self.progress_label.setText(progress_text)

    def writing_finished(self, success, message):
        self.write_button.setEnabled(True)
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageWriterGUI()
    sys.exit(app.exec_())