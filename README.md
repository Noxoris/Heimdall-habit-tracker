### Heimdall - habit tracker

Heimdall is a habit tracker software with a feature to block sites and software chosen by the user, before all habits for the day are marked as completed. Most of the code is written in Python, the GUI uses PySide6 framework and the browser addon to block sites will be written in JavaScript. When completed, it will be deployed to an .exe file to simplify usage for the end user.

Currently work in progress, the main features missing are: 
- Customizing the interface
- Days cycle logic
- Fully working two methods to add programs to block
- Habit streak and history logic
- Saving data inserted
- Settings tab

### Planned

- Blocking of software and websites
- Custom date formats
- Custom hour of starting next day
- Dark and light mode
- Easy to use interface
- History of habits completion
- Import and export data option accessible from the GUI
- Two methods for selecting programs to block

### Installation

This section will change after the final release!

Currently, to run Heimdall you need to have installed Python 3 and following libraries: icoextract, Pillow and PySide6.

Download Python 3: https://www.python.org/downloads/

Install icoextract using: pip install icoextract
If you don't know how look here: https://python.land/virtual-environments/installing-packages-with-pip

Install Pillow using: pip install pillow

Install PySide6 using: pip install PySide6

After installing all requirements, download main.py and run it using python. 
Instruction: https://www.wikihow.com/Open-a-Python-File

Note: the icons alongside True/False values in the tables will be missing, because of lack of required files. It will be fixed in the future commits.

### Usage

As a work in progress, it is not made to be used by regular user yet.

Usage is rather straightforward, the program is divided into four tabs:

#### Habits tab

Here you can manage tracked habits. The button below the table allows to add new habit. The date of start will be of today, and completion status set to False. Currently there is no option to remove habits. 

Clicking on a completion status cell of the table, will change it's value. From True to False, and from False to True.

### Programs tab

The tab includes the programs to block, with their icon, name and status of the blocking.

Clicking on a blocking status will change it in the same way as with the completion status in Habits tab.

Below the table, there are two buttons. 

Detect button allows to read what app the user starts after clicking, and allows to add it to the table.

List of programs displays the list of currently running processes, allowing to add selected programs to the list.

### Sites tab

Currently not implemented.

### Settings tab

Currently not implemented.
### Credits

Thank you to:
https://commons.wikimedia.org/ for free to use icons, that were used in this project.
https://doc.qt.io/qtforpython-6/ for documentation on PyQt6/PySide6 without which the work would be much harder.
https://www.pythonguis.com/ for great tutorials on using PyQt6/PySide6.

### License (will change!)

You may copy, redistribute, modify and use the program, as long as you credit the author (https://github.com/Noxoris). You may not use it for commercial purposes, unless given the permission by the author.
