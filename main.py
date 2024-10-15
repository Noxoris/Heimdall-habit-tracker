from PySide6.QtWidgets import QApplication, QPushButton, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget
from PySide6.QtCore import Slot, Qt
import psutil

class HeimdallWindow(QMainWindow):
    def __init__(self):
       super().__init__()

       self.setWindowTitle("Heimdall")
       self.setGeometry(400, 400, 450, 450)

       #Creating text to display what program has been detected 
       self.program_detected = QLabel("No program detected", alignment=Qt.AlignCenter)

       #Setting layout
       heimdall_layout = QVBoxLayout()
       heimdall_layout.addWidget(self.program_detected)
       button_layout = QHBoxLayout()
       
       #Adding main widget
       heimdall_widget = QWidget()
       heimdall_widget.setLayout(heimdall_layout)
       self.setCentralWidget(heimdall_widget)

       #Creating a button to trigger detection of programs
       self.detect_button = QPushButton("Detect program")
       self.detect_button.clicked.connect(self.detect_processes)

       #Adding button to the layout
       button_layout.addWidget(self.detect_button)
       heimdall_layout.addLayout(button_layout)
      

    @Slot()
    def detect_processes(self):

        #Detecting all processes in the background and creating a set with only their names
        old_processes = set()
        for process in psutil.process_iter(['name']):
            old_processes.add(process.info['name'])
        
        counter = 0
        excluded_processes:list = ['smartscreen.exe', 'svchost.exe', 'dllhost.exe', 'docker.exe', 'conhost.exe', 'com.docker.cli.exe']
        
        #Scans for the first started process that is not on the excluded list
        while counter < 1:
            new_processes = set()
            for process in psutil.process_iter(['name']):
                new_processes.add(process.info['name'])

            #Compares the sets of processes to find which are new
            added: set = new_processes - old_processes

            #Changes the text displayed to the name of the first program found
            for program in added:
                if program not in excluded_processes:
                    self.program_detected.setText(f"Detected program: {program}")
                    counter += 1

#Executing the interface
if __name__ == "__main__":        

    app = QApplication([])
    window = HeimdallWindow()
    window.show()
    app.exec()



    