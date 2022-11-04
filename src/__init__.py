import aqt
from aqt import mw 
from aqt.qt import * 
from aqt import AnkiQt, gui_hooks
from aqt.utils import showInfo, showWarning, tooltip 

from . import nodes

class ImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Dialog")
        self.resize(400, 300)
        self.setupUI()
        self.setupConnections()
        self.show()

    def setupUI(self):
        self.layout = QVBoxLayout(self)
        self.label = QLabel("Import Dialog")
        self.layout.addWidget(self.label)
        # add a text field to set the base deck 
        self.baseDeck = QLineEdit()
        self.baseDeck.setPlaceholderText("Base Deck")
        self.layout.addWidget(self.baseDeck)
        # add a button to open the file selector dialog
        self.button = QPushButton("Import")
        self.layout.addWidget(self.button)

    def setupConnections(self):
        self.button.clicked.connect(self.onButtonClicked)

    def onButtonClicked(self):
        # open a file selector dialog that selects tex files
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter("Tex files (*.tex)")
        lines = []
        filename = ""
        if dialog.exec_():
            # read the file 
            filename = dialog.selectedFiles()[0]
            with open(filename, "r") as f:
                lines = f.readlines()
            # close the dialog
            self.close()
        showInfo(filename)
        # get the filename's base url 
        base_url = filename[:filename.rfind('/')]
        fileNode = nodes.FileNode(lines)
        fileNode.act(self.baseDeck.text(), base_url=base_url)
        mw.reset()
        self.accept()

action = QAction("Import Tex", mw)
action.triggered.connect(lambda _, mw=mw: ImportDialog(mw))
mw.form.menuTools.addAction(action)

