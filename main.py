import sys, psutil
from PySide6 import QtCore,QtGui, QtWidgets
from PySide6.QtWidgets import (QPushButton, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QDialog, QLineEdit)
from PySide6.QtCore import Slot, Signal, Qt
from datetime import date
#from windows_tools.installed_software import get_installed_software

class HabitsTable(QtCore.QAbstractTableModel):

    #Variables needed to control what rows were changed
    #rows_modified_signal emits a list of rows that have been modified
    data_changed = Signal()
    rows_modified_signal = Signal(list)

    def __init__(self, data):
        super(HabitsTable, self).__init__()
        self._data = data
        self.headers = ['Habit name', 'Completed?', 'Streak', 'Started']

        #Stores the indices of rows that have been modified
        self.modified_rows_set = set()

    def data(self, index, role):
        cell_value = None

        #Formats date in the table to %d-%m-%Y
        if role == Qt.ItemDataRole.DisplayRole:
            cell_value = self._data[index.row()][index.column()]
                     
            if isinstance(cell_value, date):
                return cell_value.strftime("%d-%m-%Y")
            
            return cell_value

        #Sets the text color of items in the list which equal 0
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

    #Function to update display after the table was modified
    def update_row(self, row_index):
        self.beginResetModel()
        self._data[row_index] = self._data[row_index]
        self.endResetModel()
        self.modified_rows_set.clear()
        self.emit_data_changed()

    def emit_data_changed(self):
        self.data_changed.emit()
        self.rows_modified_signal.emit(list(self.modified_rows_set))
        self.modified_rows_set.clear()

class BlockedPrograms(QMainWindow):
    def __init__(self):
       super().__init__()

       #Creating text to display what program has been detected 
       self.program_detected = QLabel("No program detected", alignment=Qt.AlignCenter)
        
       #Setting layout
       programs_layout = QVBoxLayout()
       programs_layout.addWidget(self.program_detected)
       button_layout = QHBoxLayout()
       
       #Adding main widget
       heimdall_widget = QWidget()
       heimdall_widget.setLayout(programs_layout)
       self.setCentralWidget(heimdall_widget)

       #Creating a button to trigger detection of programs
       self.detect_button = QPushButton("Detect program")
       self.detect_button.clicked.connect(self.detect_processes)

       #Adding button to the layout
       button_layout.addWidget(self.detect_button)
       programs_layout.addLayout(button_layout)

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

habits_data = [
    ["Reading", False, 9, date(2021,11,1)],
    ["Watching",False, 0, date(2017,10,1)],
    ["Programming",False, 8, date(2017,10,1)],
]

class HeimdallWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        #Sets window title, dimensions of the window and position where it appears
        self.setWindowTitle("Heimdall")
        self.setGeometry(400, 400, 450, 450)
        self.tab_widget = QtWidgets.QTabWidget()
        
        #Creates three empty tabs
        self.empty_tab1 = QWidget()
        self.empty_tab2 = QWidget()
        self.programs_tab = QWidget()
        self.habits_tab = QWidget()
        
        #Adds tabs to the tab widget
        self.tab_widget.addTab(self.empty_tab1, "Empty Tab 1")
        self.tab_widget.addTab(self.empty_tab2, "Empty Tab 2") 
        self.tab_widget.addTab(self.programs_tab, "Blocked programs")
        self.tab_widget.addTab(self.habits_tab, "Habit Table")

        self.setup_programs_tab()
            
        #Sets up the table tab content
        self.setup_habits_tab()

        #Sets the central widget to the tab widget
        self.setCentralWidget(self.tab_widget)

    #Inserts BlockedPrograms functionality to the programs_tab
    def setup_programs_tab(self):

        self.programs_window = BlockedPrograms()       
        programs_tab_layout = QVBoxLayout()

        #Adds the BlockedPrograms into the main layout
        programs_tab_layout.addWidget(self.programs_window)    
        self.programs_tab.setLayout(programs_tab_layout)

    #Inserts HabitsTable functionality to the programs_tab
    def setup_habits_tab(self):
        habits_tab_layout = QVBoxLayout()
        
        #Create the table widget
        self.model = HabitsTable(habits_data)
        self.habits_table_widget = QtWidgets.QTableView()
        self.habits_table_widget.setModel(self.model)
        habits_tab_layout.addWidget(self.habits_table_widget)

        self.habits_table_widget.selectionModel().selectionChanged.connect(self.bool_value_change)

        #Adds the "Add Habit" button below the table
        bottom_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Habit")
        self.add_button.clicked.connect(self.show_add_habit)
        bottom_layout.addWidget(self.add_button)
        
        #Create a widget for the bottom layout
        self.bottom_widget = QWidget()
        self.bottom_widget.setLayout(bottom_layout)

        #Adds both table_widget and bottom_widget to the main layout
        habits_tab_layout.addWidget(self.habits_table_widget)
        habits_tab_layout.addWidget(self.bottom_widget)
        
        self.habits_tab.setLayout(habits_tab_layout)

    #Changes the value of the cells in the "Completed?" column, after clicking
    def bool_value_change (self, selected: QtCore.QItemSelection):
        for index in selected.indexes():
           column = index.column()
           value = index.data()
           row = index.row()

           #Checks if the selected cell is in the "Completed?" column
           if column == 1:             
            new_value = not value
            #Updates the cell with the new value, and updates the interface to display changes
            habits_data[row][1] = new_value
            self.model.update_row(row)   
            return new_value          

    def show_add_habit(self):
        habit_dialog = add_habit_dialog(self)
        habit_dialog.show()

#Creates a dialog to add new habit and inserts it into the table
class add_habit_dialog(QDialog):
    def __init__(self, parent=None):
        super(add_habit_dialog, self).__init__(parent)
        self.edit = QLineEdit("Enter new habit name")
        self.button = QPushButton("Add to the table")
        programs_layout = QVBoxLayout()
        programs_layout.addWidget(self.edit)
        programs_layout.addWidget(self.button)
        self.button.clicked.connect(self.table_add_habit)
        self.setLayout(programs_layout)
        
    #Inserts new habit to the table, with custom text and today's date
    def table_add_habit(self):
        habit_name = self.edit.text()
        start_date = date.now()
        habits_data.append([habit_name, False, 0, start_date])
        self.parent().model.update_row(len(habits_data) - 1)

#Initializes the program        
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = HeimdallWindow()
    window.show()
    sys.exit(app.exec())