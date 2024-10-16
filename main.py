from PySide6.QtWidgets import (QApplication, QPushButton, QMainWindow, QLabel, 
QVBoxLayout, QHBoxLayout, QWidget, QDialog, QLineEdit)
from PySide6.QtCore import Slot, Qt
from PySide6 import QtGui, QtWidgets, QtCore
import psutil
import datetime
import sys

#Creating the main window
class HeimdallWindow(QMainWindow):
    def __init__(self):
       super().__init__()

       #Setting title and dimensions of the displayed window
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

#Work in Progress, table of habits

#Creating the table
class HabitTable(QtCore.QAbstractTableModel):
    def __init__(self, data):
        super(HabitTable, self).__init__()
        self._data = data
        self.headers = ['Habit name', 'Completed?', 'Streak', 'Started']

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            cell_value = self._data[index.row()][index.column()]
            
            #Converting date values in cells to d-m-Y format
            if isinstance(cell_value, datetime):
                return cell_value.strftime ("%d-%m-%Y")
            
            return cell_value    
        
        #Changing the text color of cells with value 0
        if role == Qt.ItemDataRole.ForegroundRole:
            cell_value = self._data[index.row()][index.column()]
            if (isinstance(cell_value, int)) and cell_value == 0:
                return QtGui.QColor('red')

        return cell_value

    def rowCount(self, index):
        return len(self._data)
    
    def columnCount(self, index):
        return len(self._data[0])
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return super().headerData(section, orientation, role)

#Temporary data structure for habits list
habits_data = [
          ["Reading", True, 9, datetime(2021,11,1)],
          ["Watching",True, 0, datetime(2017,10,1)],
          ["Programming",False, 8, datetime(2017,10,1)],
        ]

#Creating the window with the table
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.table = QtWidgets.QTableView()
        self.model = HabitTable(habits_data)
        self.table.setModel(self.model)
        self.setCentralWidget(self.table)

#Creating the popup with the prompt for name of new habit.
class add_habit_dialog(QDialog):
    def __init__(self, parent=None):
        super(add_habit_dialog, self).__init__(parent)
        self.edit = QLineEdit("Enter new habit name")
        self.button = QPushButton("Add to the table")
        heimdall_layout = QVBoxLayout()
        heimdall_layout.addWidget(self.edit)
        heimdall_layout.addWidget(self.button)
        self.setLayout(heimdall_layout)
        self.button.clicked.connect(self.table_add_habit)

    #Function to add new habit, with current date as a starting date
    def table_add_habit(self):
        completition = False
        habit_name = self.edit.text()
        #TODO STREAK HISTORY
        streak = 0
        start_date = datetime.now().date()
        habits_data.append([habit_name, completition, streak, start_date])
        
    


#Executing the interface
if __name__ == "__main__":        

    app = QApplication([])
    window = HeimdallWindow()
    window.show()
    app.exec()

    #Executing the habit table WiP
    app_second=QtWidgets.QApplication(sys.argv)
    window=MainWindow()
    window.show()
    habit_dialog = add_habit_dialog()
    habit_dialog.show()
    app_second.exec()
    



    