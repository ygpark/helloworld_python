import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout

class MyApp(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('My First Application')
        self.move(300, 300)
        self.resize(400, 200)
        self.show()

        label1 = QLabel('First Label', self)
        font1 = label1.font()
        font1.setPointSize(20)
        label1.setFont(font1)

        layout = QVBoxLayout()
        layout.addWidget(label1)

        self.setLayout(layout)


if __name__ == '__main__':
   app = QApplication(sys.argv)
   ex = MyApp()
   sys.exit(app.exec_())