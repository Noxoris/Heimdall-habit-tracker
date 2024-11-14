import sys, psutil, ctypes
from PySide6 import QtCore,QtGui, QtWidgets
from PySide6.QtWidgets import (QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QMessageBox, QWidget, QDialog, QLineEdit)
from PySide6.QtCore import Slot, Signal, Qt, QThread
from datetime import date, datetime
from icoextract import IconExtractor
from PIL import Image
from time import sleep
from os import getcwd, remove
from io import BytesIO
import json


current_dir = getcwd()

#TODO 
#add exporting last_cycle to prevent starting at each running of the program
#change the window size and position to current monitor
#create an update class to reuse the code
#custom window for error messages
#Fix the line self.program_name.setText("Detecting now, please start the app you want to add.") not updating displayed message
#Fix lastcycle not exporting
#Ignore program button to the programs tab
#make a function to reuse geometry (?)
#only an icon in the boolean field, or a yes/no besides
  
class ExportImport():
    
    #Removes the json file 
    def delete_file(file_name):
        try:
            remove(f"{file_name}.json")

        except FileNotFoundError:
            pass
    
    #If it exists, loads data from json file
    def get_data(file_name):
        try:
            return ExportImport.import_json(file_name)
        
        except FileNotFoundError:
            return []

    def export_json(name, table):

        formatted_table = []
        for row in table:
            formatted_row = []
            for item in row:

                #Checks for date, and converts it into an isoformat, that the json supports
                if isinstance(item, date):
                    formatted_item = item.isoformat() 
                
                #Checks for int, and leaves it's normal value
                elif isinstance(item, int):
                    formatted_item = item

                #Otherwise converts the item into string, to ensure compability with json
                else:
                    formatted_item = str(item)

            #Adds items to rows, and rows to the table
                formatted_row.append(formatted_item)
            formatted_table.append(formatted_row)
        
        #Creates a dictionary with the name from the function call
        data_dict = {name: formatted_table}

        #Adds it into the json object
        json_object = json.dumps(data_dict, indent=4) 

        #Exports the json object into a json file
        with open(f"{name}.json", "w") as export_json:
            export_json.write(json_object)

    def import_json(name):
        with open(f"{name}.json", "r") as import_json:
            json_object = json.load(import_json)

        new_list = json_object.get(name, [])
        
        converted_list = []

        for row in new_list:
            converted_row = []
            for i, item in enumerate(row):

                #Checks if the item was date or datetime object before exporting
                if isinstance(item, str) and item.startswith("20"):

                    #Tries to create a date object from the string in isoformat
                    try:
                        converted_item = date.fromisoformat(item)

                    #If it throws ValueError, then the string must be in datetime format, so it creates the datetime object instead
                    except ValueError:
                        converted_item = datetime.fromisoformat(item)

                #Checks if the value is a string that was QLabel object before exporting
                elif isinstance(item, str) and item.startswith("<PySide6.QtWidgets.QLabel"):
                    
                    #Gets the program name from the next item
                    program_name = row[i+1]

                    #Creates a QLabel from the icon exported earlier and adds it as the item to return
                    label = QLabel()
                    pixmap = QtGui.QPixmap(rf"{current_dir}/data/icons/programs/{program_name}.png")
                    label.setPixmap(pixmap)
                    converted_item = label

                else:
                    converted_item = item

            #Adds items to rows, and rows to list
                converted_row.append(converted_item)
            converted_list.append(converted_row)
        return converted_list

#Imports saved data
habits_data = ExportImport.get_data("habits")
currently_blocked = ExportImport.get_data("blocked")

#Imports an empty list, because generating icons from images doesn't work before starting QApplication
programs_data = []

#Imports last day cycle datetime
last_cycle_table = ExportImport.get_data("lastcycle")

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
                    currently_blocked.append([programs_data[row][1]])

                    #Updates the json file
                    ExportImport.export_json("blocked", currently_blocked)
                else:
                    currently_blocked.remove(programs_data[row][1])

                    #Updates the json file
                    ExportImport.export_json("blocked", currently_blocked)

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
            color = BoolTextAndIcon.bool_color(cell_value)
            return color
           
        if role == QtCore.Qt.ItemDataRole.DecorationRole:
            cell_value = self._data[index.row()][index.column()]

            #Adds a tick or cross alongside the bool value, depending on the value  
            self.icon_setter = BoolTextAndIcon.set_icon(cell_value)
            return self.icon_setter

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

        #Updates the json file
        ExportImport.export_json("habits", habits_data)
        #Updates display after appending new values
        self.parent().habits_model.update_row(len(habits_data) - 1)

#Sets displayed color and icon to boolean values in the tables.
class BoolTextAndIcon():

    def bool_color(value):
    #Sets the text color of bool items depending on the value  
        if isinstance(value, bool):
            if value:
                return QtGui.QColor('green')
            return QtGui.QColor('red')
        return None

    #Adds a tick or cross alongside the bool value, depending on the value  
    def set_icon(cell_value):
        if isinstance(cell_value, bool):
            if cell_value:
                return QtGui.QIcon(f"{current_dir}/data/icons/tick.svg")
            return QtGui.QIcon(f"{current_dir}/data/icons/cross.svg")
        return None

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
            color = BoolTextAndIcon.bool_color(cell_value)
            return color
         
        if role == QtCore.Qt.ItemDataRole.DecorationRole:
            cell_value = self._data[index.row()][index.column()]

            #Makes sure the pixmap are displayed correctly
            if isinstance(cell_value, QtWidgets.QLabel):
                return cell_value.pixmap()

            #Adds a tick or cross alongside the bool value, depending on the value  
            self.icon_setter = BoolTextAndIcon.set_icon(cell_value)
            return self.icon_setter
        
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

            #Updates the json file
            ExportImport.export_json("programs", programs_data)
            self.parent.programs_model.update_row(len(programs_data) - 1)
        else:
            ctypes.windll.user32.MessageBoxW(0, f"The {self.program_to_add} is already added. ", "Adding program", 0x40000)

#Adds programs to the list based on list of all running programs.
class ProgramsListWindow(QWidget):
    
    def __init__(self, parent = None):
        super().__init__()
        self.parent = parent
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
        self.initialized = False
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

class NewDay(QThread):
    stopped = Signal()
    
    def __init__(self):
        super().__init__()

    #Checks if the table is empty, meaning the data was not loaded from json
    if last_cycle_table == []:
        
    #Sets the last cycle to the 1 january 1970, so it will always be before current date.
        last_cycle = datetime.min
    
    #Otherwise gets the value from the loaded data
    else:
        last_cycle = last_cycle_table[0]
        last_cycle = last_cycle[0]

    #Sets the hour of new day
    new_day_hour = 0

    def NewDayCheck(self):
        
        #Gets current time and replaces hour with custom hour of the day
        now = datetime.now()
        target_time = now.replace(hour=self.new_day_hour, minute=0, second=0)

        #Checks if the time is greater than or equal to the set time of new day
        if now >= target_time:
            #Sets the last cycle to the current date
            current_date = now.date()
            last_cycle_date = self.last_cycle.date()

            #Tldr; checks if the new cycle should begin. Checks if the day had changed since the last cycle or the date is the same, but time is later than the last occurrence time
            if current_date > last_cycle_date or (current_date == last_cycle_date and now > self.last_cycle):
                self.NewDayCycle()
                self.update_last_cycle(now)

    #Updates the last cycle to the set hour of new day and current day. 
    def update_last_cycle(self, time):
        self.last_cycle = time.replace(hour=self.new_day_hour, minute=0, second=0)

        #Clears the table to make sure there is only one last_cycle date
        last_cycle_table = []
        last_cycle_table.append([self.last_cycle])

        #Exports the newest last cycle date to a json file
        ExportImport.export_json("lastcycle", last_cycle_table)

    def NewDayCycle(self):
        for habit_list in habits_data:

            #If the completion is True, then adds +1 to the streak counter, and sets the completion as False.
            if habit_list[1]:
                habit_list[2] += 1
                habit_list[1] = False             

            #Otherwise simply resets streak counter
            else:
                habit_list[2] = 0
            
            #Updates the exported habits
            ExportImport.export_json("habits",habits_data)

    #Runs the loop checking for the new day every 60 seconds
    def run(self):
        while True:
            self.NewDayCheck()
            sleep(60)

#Initializes the program        
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    #Imports the programs data, after the QApplication was initialized
    programs_data = ExportImport.get_data("programs")

    #Starts the killing processes thread with the main program
    killing_thread = ProcessKiler()
    killing_thread.finished.connect(app.exit)
    killing_thread.start()

    #Starts the day cycle thread with the main program
    new_day_thread = NewDay()
    new_day_thread.finished.connect(app.exit)
    new_day_thread.start()

    window = HeimdallWindow()
    window.show()
    sys.exit(app.exec())