# -*- coding: utf-8 -*-

import sys
from multiprocessing import cpu_count
from multiprocessing.dummy import Pool as ThreadPool
from os import path
from time import time

import pandas as pd
from PyQt5 import QtWidgets

import gui
from Scraper import Scraper


class ScraperApplication(QtWidgets.QMainWindow, gui.Ui_MainWindow):

    def __init__(self, parent=None):
        """Connects our buttons to the functions"""
        super(ScraperApplication, self).__init__(parent)
        self.setupUi(self)
        self.actionOpen_File.triggered.connect(self.open_file)
        self.SelectFile.clicked.connect(self.open_file)
        self.SelectDirectory.clicked.connect(self.open_directory)
        self.startButton.clicked.connect(self.start_scraping)
        self.radio_concatenate_all.toggled.connect(self.check_concatenate_all)
        self.radio_threads_no.toggled.connect(self.radio_check_nbthreads)
        self.radio_scrape_all.toggled.connect(self.check_scrape_items)
        self.nb_scraped = 1
        self.nb_pdf = 1
        self.MAX_LEN = 0

    def open_file(self):
        """Creates a window to select a file in the explorer"""
        options = QtWidgets.QFileDialog.Options()
        #options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(None, "Open CSV File", "",
                                                            "CSV Files (*.csv)", options=options)
        if fileName:
            self.filePath.setText(fileName)

    def open_directory(self):
        """Creates a window to select a folder in the explorer"""
        directory = QtWidgets.QFileDialog.getExistingDirectory(parent=None,
                                                               caption='Open backup directory',
                                                               options=QtWidgets.QFileDialog.ShowDirsOnly)
        if directory:
            self.directoryPath.setText(directory)

    def check_scrape_items(self):
        """Selects all the checkboxes if the All options is checked and disables them"""
        checked = self.radio_scrape_all.isChecked()

        self.check_scrape_classifications.setChecked(checked)
        self.check_scrape_cited.setChecked(checked)
        self.check_scrape_citations.setChecked(checked)
        self.check_scrape_similar.setChecked(checked)
        self.check_scrape_legal.setChecked(checked)
        self.check_PDF.setChecked(checked)

        self.check_scrape_classifications.setEnabled(not checked)
        self.check_scrape_cited.setEnabled(not checked)
        self.check_scrape_citations.setEnabled(not checked)
        self.check_scrape_similar.setEnabled(not checked)
        self.check_scrape_legal.setEnabled(not checked)
        self.check_PDF.setEnabled(not checked)

    def check_concatenate_all(self):
        """Selects all the checkboxes if the All options is checked and disables them"""
        check = self.radio_concatenate_all.isChecked()

        self.checkBox_abstract.setChecked(check)
        self.checkBox_title.setChecked(check)
        self.checkBox_description.setChecked(check)
        self.checkBox_claims.setChecked(check)

        self.checkBox_abstract.setEnabled(not check)
        self.checkBox_title.setEnabled(not check)
        self.checkBox_description.setEnabled(not check)
        self.checkBox_claims.setEnabled(not check)

    def option_check(self):
        """Manages the scraping options"""
        if self.radio_scrape_all.isChecked():

            self.check_PDF.isChecked(True)
            self.check_PDF.isEnabled(False)

            self.check_scrape_citations.isChecked(True)
            self.check_scrape_citations.isEnabled(False)

            self.check_scrape_classifications.isChecked(True)
            self.check_scrape_classifications.isEnabled(False)

            self.check_scrape_cited.isChecked(True)
            self.check_scrape_cited.isEnabled(False)

            self.check_scrape_similar.isChecked(True)
            self.check_scrape_similar.isEnabled(False)

            self.check_scrape_legal.isChecked(True)
            self.check_scrape_legal.isEnabled(False)
        else:
            self.check_scrape_legal.isEnabled(False)
            self.check_scrape_similar.isEnabled(False)
            self.check_scrape_cited.isEnabled(False)
            self.check_scrape_classifications.isEnabled(False)
            self.check_scrape_citations.isEnabled(False)
            self.check_PDF.isEnabled(False)

    def radio_check_nbthreads(self):
        """Manages the threads option"""
        if self.radio_threads_no.isChecked():
            self.txt_nb_cores.setEnabled(False)
        else:
            self.txt_nb_cores.setEnabled(True)

    def get_nb_threads(self):
        """Returns a number of threads
        if auto, return 2x number of cores or 8 if this number is superior to 8
        This is to limit the performance impact
        if specified, return the specified number"""

        if self.radio_threads_no.isChecked():
            return 1
        elif self.txt_nb_cores.text() == 'auto':
            nb_threads = cpu_count() * 2
            nb_threads = 8 if nb_threads > 8 else int(nb_threads)

            return nb_threads
        else:
            return int(self.txt_nb_cores.text())

    def option_concatenate_txt(self):
        """Returns a dictionary for the concatenation options
        If true, we concatenate"""
        return \
            {
                'TITLE': self.checkBox_title.isChecked(),  # this function returns a boolean
                'ABSTRACT': self.checkBox_abstract.isChecked(),
                'DESCRIPTION': self.checkBox_description.isChecked(),
                'CLAIMS': self.checkBox_claims.isChecked()
            }

    def get_all_options(self):
        """Return a dictionary with all our options"""
        options = {}
        options.update({'save_directory': self.directoryPath.text()})
        options.update({'scrape_abstract': self.checkBox_abstract.isChecked(),
                        'scrape_title': self.checkBox_title.isChecked(),
                        'scrape_description': self.checkBox_description.isChecked(),
                        'scrape_claims': self.checkBox_claims.isChecked(),
                        'scrape_citations': self.check_scrape_citations.isChecked(),
                        'scrape_cited': self.check_scrape_cited.isChecked(),
                        'scrape_similar': self.check_scrape_similar.isChecked(),
                        'scrape_legal': self.check_scrape_legal.isChecked(),
                        'scrape_classifications': self.check_scrape_classifications.isChecked()})
        options.update({'separate_files': self.check_separate_yes.isChecked()})
        options.update({'language': self.radio_english.isChecked()})
        options.update({'concatenate': self.option_concatenate_txt()})
        options.update({'download_pdf': self.check_PDF.isChecked()})
        options.update({'csv_delimiter': self.txt_char.text()})

        return options

    def add_increment(self, text):
        """Increases the progress on our progress bar"""
        self.progressBar.setValue(self.progressBar.value() + 1)
        self.nb_scraped += 1
        self.label_status.setText(text)
        self.label_status.setMinimumWidth(len(self.label_status.text()) * 10)

    def start_scraping(self):
        """Start the process of scraping
        First it reads the csv file
        Second, it reads all the options the user selected
        Third it instances a Scraper object and gets the number of threads
        Then it starts the scraping process by calling the 'scrape' method on a ThreadPool
        Finally it saves and displays a message
        :exception: FileNotFound: if the input csv is not found
                       Exception: if the nb_threads or csv_delimiter text inputs are empty
              NotADirectoryError: if the save path doesnt lead to a directory
               IsADirectoryError: if the input csv is in fact a directory
                        KeyError: if the inpu csv file is not compatible
        """

        start_time = time()  # monitors the time it takes to scrape our links
        filepath = self.filePath.text()
        self.nb_scraped = 1
        try:
            if not self.directoryPath.text():
                raise FileNotFoundError
            if not self.txt_char.text():
                raise Exception
            if not path.isdir(self.directoryPath.text()):
                raise NotADirectoryError

            file = ReadFile(filepath).data_frame

            options = self.get_all_options()

            scraper = Scraper(file, self.directoryPath.text(), self, options)
            self.MAX_LEN = len(scraper.links)

            self.progressBar.setMaximum(self.MAX_LEN)
            thread_count = self.get_nb_threads()

            self.progressBar.setValue(0)
            pool = ThreadPool(thread_count)

            self.label_status.setText('Scraping... ({}/{})'.format(self.nb_scraped, self.MAX_LEN))
            self.label_status.setMinimumWidth(len(self.label_status.text()) * 10)

            self.progressBar.setValue(len(scraper.links))
            self.progressBar.setValue(0)

            try:
                pool.map(scraper.scrape, scraper.links)
                pool.close()
                pool.join()
                for link in scraper.failed_url:
                    scraper.scrape(link)

                for tries in range(20):
                    try:
                        scraper.save()

                    except Exception as msg:
                        scraper.logger.exception(msg)
                        print('Saving of files failed :\n {} \n\n Trying again...'.format(msg))
                        scraper.save()
                    else:
                        break
                else:
                    print("Cannot save files. \n " + str(msg))

                pdf_list = []
                for patent in scraper.patent_list:
                    if patent.pdf_link is not None:
                        pdf_list.append(patent.pdf_link)

                if self.get_all_options().get('download_pdf'):
                    if thread_count == 1:
                        pool = ThreadPool(1)
                    else:
                        pool = ThreadPool(thread_count * 10)

                    self.nb_pdf = 1
                    self.label_status.setText('Downloading PDF... ({}/{})'.format(self.nb_pdf, len(pdf_list)))
                    self.label_status.setMinimumWidth(len(self.label_status.text()) * 10)
                    self.progressBar.setValue(0)

                    pool.map(scraper.download_pdf, pdf_list)
                    pool.close()

                scraper.logger.info('DONE')
                self.label_status.setText('Done.')
                self.label_status.setMinimumWidth(len(self.label_status.text()) * 10)

                done = round(time() - start_time)
                print("Process finished in {} seconds".format(done))
                self.job_done(done)

            except (ConnectionError, Exception) as msg:
                pool.close()
                print(msg)
                print("Scraper process terminated, please try again")
                self.err_render(msg)

        except IsADirectoryError as e:
            print(e)
            self.is_directory_err()

        except NotADirectoryError as e:
            print(e)
            self.not_directory_err()

        except FileNotFoundError as e:
            print(e)
            if not self.filePath.text() or not self.directoryPath.text():
                self._empty_path_err()
            else:
                self.file_not_found_err()

        except KeyError as e:
            print(e)
            self.incompatible_data()

        except Exception as e:
            print(e)
            if not self.txt_char.text():
                self.empty_csv_delimiter()
            elif not self.txt_nb_cores.text():
                self.empty_nb_cores()

    def _empty_path_err(self):
        """Creates an error window if the Path is empty"""
        msg = QtWidgets.QMessageBox(parent=self)
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setWindowTitle('Empty Path Error')
        msg.setText('Please enter a path')
        msg.exec_()

    def not_directory_err(self):
        msg = QtWidgets.QMessageBox(parent=self)
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setWindowTitle('Incorrect Backup Path')
        msg.setText('Backup path leads to a file')
        msg.exec_()

    def file_not_found_err(self):
        """Creates an error window if the file has not been found"""
        msg = QtWidgets.QMessageBox(parent=self)
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setWindowTitle('Error')
        msg.setText('File Not Found !')
        msg.exec_()

    def job_done(self, time):
        """When the scraper method is done, creates an info window"""
        msg = QtWidgets.QMessageBox(parent=self)
        msg.setWindowTitle('Done')
        msg.setText('Job done in {} seconds'.format(time))
        msg.exec_()

    def is_directory_err(self):
        """Creates an error window if the entered path is not a file"""
        msg = QtWidgets.QMessageBox(parent=self)
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setWindowTitle('Error')
        msg.setText('The path entered does not lead to a file !')
        msg.exec_()

    def incompatible_data(self):
        """Creates an error window if the input csv file is not compatible"""
        msg = QtWidgets.QMessageBox(parent=self)
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setWindowTitle('Incompatible Data')
        msg.setText('The csv file entered is not compatible ! \n \nMake sure to have all the needed columns in your '
                    'file and the first row empty !')
        msg.exec_()

    def empty_csv_delimiter(self):
        """Creates an error window if the csv delimiter input in empty"""
        msg = QtWidgets.QMessageBox(parent=self)
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setWindowTitle('Empty CSV Delimiter')
        msg.setText('CSV Delimiter input cannot be empty')
        msg.exec_()

    def empty_nb_cores(self):
        """Creates an error window if the csv delimiter input in empty"""
        msg = QtWidgets.QMessageBox(parent=self)
        msg.setIcon(QtWidgets.QMessageBox.Critical)
        msg.setWindowTitle('Empty Thread Number')
        msg.setText('Please specify a number of threads or leave auto')
        msg.exec_()

    def err_render(self, info):
        """Creates an error window if an error occurs during the scraping process"""
        msg = QtWidgets.QMessageBox(parent=self)
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setWindowTitle('Error in Scraping process')
        msg.setText('The following error has occured :\n\n' + str(info)
                    + '\n\n Please try again.')
        msg.exec_()


class ReadFile:
    """
    Object representing our original csv file, stored into a Pandas DataFrame
    """

    def __init__(self, file_name):
        self.f = open(file_name, encoding='utf-8', newline='')
        self.data_frame = pd.read_csv(self.f, skiprows=[0], encoding='utf-8', na_filter=False)
        self.f.close()

    def dataframe(self):
        return self.data_frame


def main():
    app = QtWidgets.QApplication(sys.argv)
    form = ScraperApplication()
    form.show()
    app.exec_()


if __name__ == '__main__':
    sys.exit(main())
