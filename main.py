import sys, psutil, ctypes
from PySide6 import QtCore,QtGui, QtWidgets
from PySide6.QtWidgets import (QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QMessageBox, QWidget, QDialog, QLineEdit)
from PySide6.QtCore import Slot, Signal, Qt, QThread
from datetime import date
from icoextract import IconExtractor
from PIL import Image
from time import sleep
from os import getcwd
from io import BytesIO

current_dir = getcwd()

#TODO 
# % based window size based rather than pixel
#change the window size and position to current monitor
#create an update class to reuse the code
#custom window for error messages
#Fix the line self.program_name.setText("Detecting now, please start the app you want to add.") not updating displayed message
#Fix the now_running function starting twice
#Ignore program button to the programs tab
#make a function to reuse adding tick / cross to boolean
#make a function to reuse geometry (?)
#only an icon in the boolean field, or a yes/no besides
#reimplement the background thread, so the program won't freeze for a second

#Main window class.
class HeimdallWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        #Sets window title, dimensions of the window and position where it appears
        self.setWindowTitle("Heimdall")
        
        #Gets the primary screen
        screen = QtWidgets.QApplication.screens()[0]

        #Calculates the position to show the window
        position_x = int(screen.size().width() * 0.45)
        position_y = int(screen.size().width() * 0.20)

        #Calculates the size of the window
        width_percent = int(screen.size().width() * 0.18)
        height_percent = int(screen.size().height() * 0.30)
        
        #Sets the position and size of the window
        self.setGeometry(position_x, position_y, width_percent, height_percent)

        self.tab_widget = QtWidgets.QTabWidget()
        
        #Creates three empty tabs
        self.settings = QWidget()
        self.sites_tab = QWidget()
        self.programs_tab = QWidget()
        self.habits_tab = QWidget()
        
        #Adds tabs to the tab widget
        self.tab_widget.addTab(self.habits_tab, "Habits Table")
        self.tab_widget.addTab(self.programs_tab, "Blocked programs")
        self.tab_widget.addTab(self.sites_tab, "Blocked websites") 
        self.tab_widget.addTab(self.settings, "Settings") 
        
        #Sets up the table tabs content
        self.setup_programs_tab()
        self.setup_habits_tab()

        #Sets the central widget to the tab widget
        self.setCentralWidget(self.tab_widget)

    #Inserts BlockedPrograms functionality to the programs_tab
    def setup_programs_tab(self):
        programs_tab_layout = QVBoxLayout()

        #Create the table widget
        self.programs_model = BlockedPrograms(programs_data)       
        self.programs_table_widget = QtWidgets.QTableView()
        self.programs_table_widget.setModel(self.programs_model)
        self.programs_table_widget.resizeColumnsToContents()
        self.programs_table_widget.resizeRowsToContents()
        programs_tab_layout.addWidget(self.programs_table_widget)
    
        #Adds the BlockedPrograms into the main layout
        programs_tab_layout.addWidget(self.programs_table_widget)
        self.programs_tab.setLayout(programs_tab_layout)

        #Adds the "Add Detect program" button below the table
        button_layout = QHBoxLayout()
        self.detect_button = QPushButton("Detect program")
        self.detect_button.clicked.connect(self.show_detect_window)
        button_layout.addWidget(self.detect_button)

        self.program_list_button = QPushButton("List of running programs")
        self.program_list_button.clicked.connect(self.show_program_list)
        button_layout.addWidget(self.program_list_button)

        #Create a widget for the button layout
        self.button_widget = QWidget()
        self.button_widget.setLayout(button_layout)

        #Adds both table_widget and bottom_widget to the main layout
        programs_tab_layout.addWidget(self.programs_table_widget)
        programs_tab_layout.addWidget(self.button_widget)

        #Sets layout of the tab, that includes all items
        self.programs_tab.setLayout(programs_tab_layout)

        self.programs_table_widget.selectionModel().selectionChanged.connect(self.bool_value_change)

    #Inserts HabitsTable functionality to the programs_tab
    def setup_habits_tab(self):
        habits_tab_layout = QVBoxLayout()
        
        #Create the table widget
        self.habits_model = HabitsTable(habits_data)
        self.habits_table_widget = QtWidgets.QTableView()
        self.habits_table_widget.setModel(self.habits_model)
        self.habits_table_widget.resizeColumnsToContents()
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
        
        #Sets layout of the tab, that includes all items
        self.habits_tab.setLayout(habits_tab_layout)

    #Changes the value of the cells in the "Completed?" column, after clicking
    def bool_value_change (self, selected: QtCore.QItemSelection):
        for index in selected.indexes():
            column = index.column()
            value = index.data()
            row = index.row()

            #Checks if the selected cell is in the "Completed?" column of the habits table
            if column == 1 and type(value) == bool:             
                new_value = not value
                #Updates the cell with the new value, and updates the interface to display changes
                habits_data[row][1] = new_value
                self.habits_model.update_row(row)  

            #Checks if the selected cell is in the "Blocked?" column of the programs table
            elif column == 2 and type(value) == bool:
                new_value = not value
                programs_data[row][2] = new_value
                self.programs_model.update_row(row)

                #Adds the programs toggled as "blocked" to the list of blocked programs
                if new_value == True and programs_data[row][1] not in currently_blocked:
                    currently_blocked.append(programs_data[row][1])
                else:
                    currently_blocked.remove(programs_data[row][1])

    #Functions to display windows used in adding values to the tables
    def show_add_habit(self):
        self.window = AddHabitDialog(self)
        self.window.show()
    def show_detect_window(self):
        self.window = DetectProgramWindow(self)
        self.window.show()
    def show_program_list(self):
        self.window = ProgramsListWindow(self)
        self.window.show()

class HabitsTable(QtCore.QAbstractTableModel):

    #Variables needed to control what rows were changed
    #rows_modified_signal emits a list of rows that have been modified
    data_changed = Signal()
    rows_modified_signal = Signal(list)

    def __init__(self, data):
        super(HabitsTable, self).__init__()
        self._data = data
        self.headers = ['Name', 'Completed?', 'Streak', 'Started']

        #Stores the indices of rows that have been modified
        self.modified_rows_set = set()

    def data(self, index, role):
        cell_value = None

        #Displays data in cells 
        if role == Qt.ItemDataRole.DisplayRole:
            cell_value = self._data[index.row()][index.column()]

            #Formats date in the table to %d-%m-%Y         
            if isinstance(cell_value, date):
                return cell_value.strftime("%d-%m-%Y")
            
            return cell_value
        
        if role == Qt.ItemDataRole.ForegroundRole:
            cell_value = self._data[index.row()][index.column()]

            #Sets the text color of bool items depending on the value  
            if isinstance(cell_value, bool):
                if cell_value:
                    return QtGui.QColor('green')
                return QtGui.QColor('red')
            return None
           
        if role == QtCore.Qt.ItemDataRole.DecorationRole:
            cell_value = self._data[index.row()][index.column()]

            #Adds a tick or cross alongside the bool value, depending on the value  
            if isinstance(cell_value, bool):
                if cell_value:
                    return QtGui.QIcon(rf"{current_dir}/data/icons/tick.svg")
                return QtGui.QIcon(rf"{current_dir}/data/icons/cross.svg")
            return None

        return cell_value

    def rowCount(self, index):
        return len(self._data)
    
    def columnCount(self, index):
        #Try except block ensures the correct display even when the list is empty
        try:
            return len(self._data[0])
        except:
            return 0
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return super().headerData(section, orientation, role)   

    #Functions to update display after the table was modified
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

#Creates a dialog to add new habit and appends it into the table.
class AddHabitDialog(QDialog):
    def __init__(self, parent=None):
        super(AddHabitDialog, self).__init__(parent)

        #Creates the editable field and a button
        self.edit = QLineEdit("Enter new habit name")
        self.button = QPushButton("Add to the table")

        #Adds the field and button to the layout of the window
        habits_layout = QVBoxLayout()
        habits_layout.addWidget(self.edit)
        habits_layout.addWidget(self.button)

        self.button.clicked.connect(self.table_add_habit)

        #Sets layout of dialog
        self.setLayout(habits_layout)
        
    #Inserts new habit to the table, with custom text and today's date
    def table_add_habit(self):
        habit_name = self.edit.text()
        start_date = date.today()
        habits_data.append([habit_name, False, 0, start_date])

        #Updates display after appending new values
        self.parent().habits_model.update_row(len(habits_data) - 1)

#Table of blocked programs.
class BlockedPrograms(QtCore.QAbstractTableModel):

    #Variables needed to control what rows were changed
    #rows_modified_signal emits a list of rows that have been modified
    data_changed = Signal()
    rows_modified_signal = Signal(list)

    def __init__(self, data):
       super().__init__()
       self._data = data
       self.headers = ['Icon', 'Name', 'Blocked?']

       #Stores the indices of rows that have been modified 
       self.modified_rows_set = set()

    def data(self, index, role):
        cell_value = None

        #Displays data in cells
        if role == Qt.ItemDataRole.DisplayRole:
            cell_value = self._data[index.row()][index.column()]   
            return cell_value

        #Sets the text color of items in the list which values are False
        if role == Qt.ItemDataRole.ForegroundRole:
            cell_value = self._data[index.row()][index.column()]

            #Sets the text color of bool items depending on the value  
            if isinstance(cell_value, bool):
                if cell_value:
                    return QtGui.QColor('green')
                return QtGui.QColor('red')
            return None
        
         
        if role == QtCore.Qt.ItemDataRole.DecorationRole:
            cell_value = self._data[index.row()][index.column()]

            #Makes sure the pixmap are displayed correctly
            if isinstance(cell_value, QtWidgets.QLabel):
                return cell_value.pixmap()

            #Adds a tick or cross alongside the bool value, depending on the value  
            if isinstance(cell_value, bool):
                if cell_value:
                    return QtGui.QIcon(rf"{current_dir}/data/icons/tick.svg")
                return QtGui.QIcon(rf"{current_dir}/data/icons/cross.svg")
            return None
        
        return cell_value

    def rowCount(self, index):
        return len(self._data)
    
    def columnCount(self, index):
        #Try except block ensures the correct display even when the list is empty
        try:
            return len(self._data[0])
        except:
            return 0
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return super().headerData(section, orientation, role)   
    
    #Functions to update display after the table was modified
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

#Adds programs to the list based on detecting newly started program.
class DetectProgramWindow(QWidget):
    def __init__(self, parent = None):
        super().__init__()

        self.parent = parent
        self.setWindowTitle("Heimdall - detecting programs")


        #Gets the primary screen
        screen = QtWidgets.QApplication.screens()[0]

        #Calculates the position to show the window
        position_x = int(screen.size().width() * 0.64)
        position_y = int(screen.size().width() * 0.20)

        #Calculates the size of the window
        width_percent = int(screen.size().width() * 0.10)
        height_percent = int(screen.size().height() * 0.20)

        #Sets the position and size of the window
        self.setGeometry(position_x, position_y, width_percent, height_percent)
        
        #Sets layout and adds text that shows what program was detected
        window_layout = QVBoxLayout()
        self.program_name = QLabel("No program detected", alignment=Qt.AlignCenter)

        #Adds the text to the window layout
        window_layout.addWidget(self.program_name)
        self.setLayout(window_layout)
       
        #Creates a button to trigger detection of programs and adds them to the table
        self.detect_button = QPushButton("Detect program")
        self.detect_button.clicked.connect(self.detect_processes)
        self.append_button = QPushButton("Add to the table")
        self.append_button.clicked.connect(self.append_progam)
    
        #Creates a layout and adds buttons to it
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.detect_button)
        button_layout.addWidget(self.append_button)
        window_layout.addLayout(button_layout)

        #Sets layout of the buttons
        self.setLayout(button_layout)

    program_to_add = None     

    @Slot()
    def detect_processes(self):

        #Detecting all processes in the background and creating a set with only their names and file name
        old_processes:set = set()
        for process in psutil.process_iter(['name', 'exe']):
            old_processes.add((process.info['name'], process.info['exe']))
        
        counter:int = 0
        #List of background processes that can disrupt the process of detecting 
        excluded_processes:list = ['smartscreen.exe', 'backgroundTaskHost.exe', 'svchost.exe', 
                                   'dllhost.exe', 'docker.exe', 'conhost.exe', 'com.docker.cli.exe']
        
        #Scans for the first started process that is not on the excluded list
        while counter < 1:
            self.program_name.setText("Detecting now, please start the app you want to add.")
            new_processes = set()
            for process in psutil.process_iter(['name', 'exe']):
                new_processes.add((process.info['name'], process.info['exe']))

            #Compares the sets of processes to find which are new
            added: set = new_processes ^ old_processes
            sleep(0.3)
            #Changes the text displayed to the name of the first program found
            for program_name, program_path in added:
                if program_name not in excluded_processes:
                    self.program_name.setText(f"Detected program: {program_name}")
                    counter += 1
                    self.program_to_add = program_name

                    #Extracts the icon of the detected program
                    extractor = IconExtractor(program_path)
                    icon = extractor.get_icon(num=0)
                    icon_to_png = Image.open(icon)

                    #Converts the icon to png
                    icon_to_png = icon_to_png.resize((40,40))
                    icon_to_png.save(rf"{current_dir}/data/icons/programs/{program_name}.png", format='PNG')

                    #Sets the icon as the image extracted from the process 
                    self.label = QLabel()
                    pixmap = QtGui.QPixmap(rf"{current_dir}/data/icons/programs/{program_name}.png")
                    self.label.setPixmap(pixmap)

    #Adds the program to the programs table
    def append_progam(self):
        if self.program_to_add not in programs_data:  
            programs_data.append([self.label, self.program_to_add, False])
            self.parent.programs_model.update_row(len(programs_data) - 1)
        else:
            ctypes.windll.user32.MessageBoxW(0, f"The {self.program_to_add} is already added. ", "Adding program", 0x40000)

#Adds programs to the list based on list of all running programs.
class ProgramsListWindow(QWidget):
    
    def __init__(self, parent = None):
        super().__init__()
        self.parent = parent
        self.current_processes = CurrentProcesses()  
        self.setWindowTitle("Heimdall - current programs")
        
        #Gets the primary screen
        screen = QtWidgets.QApplication.screens()[0]

        #Calculates the position to show the window
        position_x = int(screen.size().width() * 0.65)
        position_y = int(screen.size().width() * 0.20)

        #Calculates the size of the window
        width_percent = int(screen.size().width() * 0.14)
        height_percent = int(screen.size().height() * 0.30)
        
        #Sets the position and size of the window
        self.setGeometry(position_x, position_y, width_percent, height_percent)

        #Creates the main layout and sets it
        processes_layout = QVBoxLayout()
        self.setLayout(processes_layout)
        
        #Creates a processes table and sets it's model
        self.processes_model = CurrentProcesses()
        self.processes_widget = QtWidgets.QTableView()
        self.processes_widget.setModel(self.processes_model)
        processes_layout.addWidget(self.processes_widget)

        self.processes_widget.resizeColumnsToContents()
        self.processes_widget.resizeRowsToContents()

        #Creates a layout and a button
        bottom_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_clicked)

        #Adds the button to the layout
        bottom_layout.addWidget(self.refresh_button)
        processes_layout.addLayout(bottom_layout)

        #Sets the button layout
        self.setLayout(bottom_layout)

    #Triggers refresh after clicking
    def refresh_clicked(self):
        self.processes_model.beginResetModel
        self.processes_model.refresh_list()
        self.processes_model.endResetModel

#Funtionality for ProgramsListWindow
class CurrentProcesses(QtCore.QAbstractTableModel):

    def __init__(self):
        super(CurrentProcesses, self).__init__()
        currently_running = self.now_running()
        self._data = currently_running
        self.headers = ['Add?','Icon', 'Name']

    def now_running(self):
        running = set()
        running_list = []
    
        #Used to prevent displaying programs which if blocked could cause more "serious" issues ex. windows file explorer
        excluded_list=['explorer.exe']

        for process in psutil.process_iter(['name', 'exe']):
            running.add((process.info['name'], process.info['exe']))

        for program_name, program_path in running:
            #Extracts the icon of the detected program
            try:
                extractor = IconExtractor(program_path)
            except:
                continue
            icon = extractor.get_icon(num=0)
            icon_to_png = Image.open(icon)

            #Converts the icon to png
            icon_to_png = icon_to_png.resize((40,40))

            #Uses BytesIo to store the image in the buffer as the PNG
            icon_bytes = BytesIO()
            icon_to_png.save(icon_bytes, format='PNG')
            icon_bytes.seek(0)

            #Sets the icon as the image extracted from the process 
            self.label = QLabel()
            pixmap = QtGui.QPixmap()

            #Loads the image from the buffer
            pixmap.loadFromData(icon_bytes.getvalue())

            self.label.setPixmap(pixmap)
            if program_name not in excluded_list:
                running_list.append([False, self.label, program_name])

        #Sorts the list alphabetically ascending based on the name column        
        running_list.sort(key = lambda x: x[2])    
        return running_list
    
    def data(self, index, role):
        cell_value = None
        
        #Displays data in cells 
        if role == Qt.ItemDataRole.DisplayRole:
            cell_value = self._data[index.row()][index.column()]
            
            return cell_value
        
        if role == Qt.ItemDataRole.ForegroundRole:
            cell_value = self._data[index.row()][index.column()]

            return cell_value
        
        if role == QtCore.Qt.ItemDataRole.DecorationRole:
            cell_value = self._data[index.row()][index.column()]

            #Makes sure the pixmap are displayed correctly
            if isinstance(cell_value, QtWidgets.QLabel):
                return cell_value.pixmap()

    def refresh_list(self):
        self._data = self.now_running()
        
    def rowCount(self, index):
        return len(self._data)
    
    def columnCount(self, index):
        #Try except block ensures the correct display even when the list is empty
        try:
            return len(self._data[0])
        except:
            return 0
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return super().headerData(section, orientation, role)   

#Kills the blocked processes
class ProcessKiler(QThread):
    ended = Signal()

    def __init__(self):
        super().__init__()

    def kill_blocked(self):
        #Detecting all processes in the background and creating a set with only their names
        background_processes:set = set()
        for process in psutil.process_iter(['name']):
            background_processes.add(process.info['name'])
      
        #Scans for the first started process
        new_background_processes = set()
        for process in psutil.process_iter(['name']):
            new_background_processes.add(process.info['name'])

            for proc in psutil.process_iter(['name']):
                try:
                    #Kills the process if the program is blocked
                    if proc.info['name'] in currently_blocked:
                        proc.kill()
                       
                        #WiP custom window
                        #msg_window = MessageWindow("Error!", f"Sorry, the {proc.info['name']} is blocked. ")
                        #msg_window.show()

                        #Shows a windows error message
                        ctypes.windll.user32.MessageBoxW(0, f"Sorry, the {proc.info['name']} is blocked. ", "Blocked program", 0x40000)
                #If killing the process throws an error, the error is ignored
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

    #Runs the function as long as the program is working, with 2 seconds break between the cycles         
    def run(self):
        while True:
            self.kill_blocked()
            sleep(2)

#WiP custom alert
class MessageWindow(QtWidgets.QMainWindow):
    def __init__(self, error_header, error_text):
        super().__init__()
        self.setWindowTitle(error_header)
        self.setGeometry(450, 400, 350, 150)
        msg_box = QMessageBox(self)
        msg_box.setText = QLabel(error_text, alignment=Qt.AlignCenter)
        button = msg_box.exec()
        if button == QMessageBox.StandardButton.Ok:
            print("OK!")

#Testing values    
programs_data = [['TEST', 'AIMP.exe', False]]
habits_data = [
    ["Reading", False, 9, date(2021,11,1)],
    ["Watching",False, 0, date(2017,10,1)],
    ["Programming",False, 8, date(2017,10,1)],
]
currently_blocked = ['AIMP.exe']

#Initializes the program        
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    #Starts the killing processes thread with the main program
    killing_thread = ProcessKiler()
    killing_thread.finished.connect(app.exit)
    killing_thread.start()

    window = HeimdallWindow()
    window.show()
    sys.exit(app.exec())