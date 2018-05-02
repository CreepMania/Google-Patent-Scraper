# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mainwindow.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtWidgets
from contextlib2 import suppress

import Scraper


# from multiprocessing.dummy import Pool as ThreadPool
# import threading


class ScraperWindow(object):
    """Initializes our UI"""

    def __init__(self, main_window, app):
        self.app = app
        self.scraper_instance = None
        self.MainWindow = main_window
        self.MainWindow.setObjectName("Scraper")
        self.MainWindow.resize(700, 500)
        self.MainWindow.setMinimumSize(QtCore.QSize(700, 500))

        qt_rectangle = self.MainWindow.frameGeometry()
        center_point = QtWidgets.QDesktopWidget().availableGeometry().center()
        qt_rectangle.moveCenter(center_point)
        self.MainWindow.move(qt_rectangle.topLeft())

        self.centralWidget = QtWidgets.QWidget(self.MainWindow)
        self.centralWidget.setObjectName("centralWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralWidget)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(self.centralWidget)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.filePath = QtWidgets.QLineEdit(self.centralWidget)
        self.filePath.setObjectName("filePath")
        self.filePath.setText('/home/guillaume/PycharmProjects/Scrapper1.0/test.csv')
        self.horizontalLayout.addWidget(self.filePath)

        self.pushButton = QtWidgets.QPushButton(self.centralWidget)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout.addWidget(self.pushButton)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.progressBar = QtWidgets.QProgressBar(self.centralWidget)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")

        self.verticalLayout.addWidget(self.progressBar)
        self.textBrowser = QtWidgets.QTextBrowser(self.centralWidget)
        self.textBrowser.setObjectName("textBrowser")
        self.verticalLayout.addWidget(self.textBrowser)
        self.MainWindow.setCentralWidget(self.centralWidget)
        self.statusBar = QtWidgets.QStatusBar(self.MainWindow)
        self.statusBar.setObjectName("statusBar")
        self.MainWindow.setStatusBar(self.statusBar)

        self.menuBar = QtWidgets.QMenuBar(self.MainWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 700, 23))
        self.menuBar.setObjectName("menuBar")

        self.menuFile = QtWidgets.QMenu(self.menuBar)
        self.menuFile.setObjectName("menuFile")
        self.MainWindow.setMenuBar(self.menuBar)

        self.actionOpen_File = QtWidgets.QAction("&Open File")
        self.actionOpen_File.setObjectName("actionOpen_File")
        self.actionOpen_File.setShortcut("Ctrl+O")
        self.actionOpen_File.setStatusTip("Open a file")
        self.actionOpen_File.triggered.connect(self.open_file)

        self.pushButton.clicked.connect(self._call_scraping)

        self.menuFile.addAction(self.actionOpen_File)
        self.menuBar.addAction(self.menuFile.menuAction())

        self._retranslate_ui()
        QtCore.QMetaObject.connectSlotsByName(self.MainWindow)

    def _retranslate_ui(self):
        _translate = QtCore.QCoreApplication.translate
        self.MainWindow.setWindowTitle(_translate("MainWindow", "Scraper"))
        self.label.setText(_translate("MainWindow", "File Name:"))
        self.pushButton.setText(_translate("MainWindow", "Start"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.actionOpen_File.setText(_translate("MainWindow", "Open File"))

    def open_file(self):
        """Opens the 'Open File' Menu and sets the 'filePath' of the UI"""
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(None, "Open CSV File", "",
                                                             "CSV Files (*.csv)", options=options)
        if file_name:
            self.filePath.setText(file_name)

    def add_text(self, text):
        """adds text to our output"""
        self.textBrowser.append(text)

    def _call_scraping(self):
        self.textBrowser.clear()
        self.progressBar.setValue(0)
        with suppress(FileNotFoundError, IsADirectoryError, KeyError, EmptyPath):
            self.scraper_instance = Scraper.Scraper(self.app, self)
            self.scraper_instance.scrape()

    @staticmethod
    def _empty_path_err():
        """Creates an error window if the Path is empty"""
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setWindowTitle('Error')
        msg.setText('Empty File Path !')
        msg.exec_()
        raise EmptyPath

    @staticmethod
    def file_not_found_err():
        """Creates an error window if the file has not been found"""
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setWindowTitle('Error')
        msg.setText('File Not Found !')
        msg.exec_()
        raise FileNotFoundError

    def job_done(self):
        """When the scraper method is done, creates an info window"""
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle('Done')
        msg.setText('Job Done !')
        msg.exec_()
        self.add_text('Done.')

    @staticmethod
    def is_directory_err():
        """Creates an error window if the entered path is not a file"""
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setWindowTitle('Error')
        msg.setText('The path entered does not lead to a file !')
        msg.exec_()
        raise IsADirectoryError

    @staticmethod
    def incompatible_data():
        """Creates an error window if the input csv file is not compatible"""
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setWindowTitle('Incompatible Data')
        msg.setText('The csv file entered is not compatible ! \n \nMake sure to have all the needed columns in your '
                    'file and the first row empty !')
        msg.exec_()
        raise KeyError

    def set_max_progress_bar(self, value):
        """Initialize the progress bar"""
        self.progressBar.setMaximum(value)

    def iterate_progress_bar(self):
        """Adds 1 to the value of our progress bar"""
        self.progressBar.setValue(self.progressBar.value() + 1)

    def get_filepath(self):
        """
        Returns our file path, if empty raises the error
        :return:
        """
        if not self.filePath.text():
            self._empty_path_err()
        else:
            return self.filePath.text()

    def show(self):
        self.MainWindow.show()


class EmptyPath(Exception):
    """Exception in case the Path has not been initialized"""
    pass
