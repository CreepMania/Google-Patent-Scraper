#! /usr/bin/env python3
# coding: utf-8

if __name__ == "__main__":
    import gui
    from PyQt5 import QtWidgets
    import sys

    Qapp = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = gui.ScraperWindow(MainWindow, Qapp)
    ui.show()

    sys.exit(Qapp.exec_())
