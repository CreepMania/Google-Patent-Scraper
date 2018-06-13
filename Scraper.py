# -*- coding: utf-8 -*-

import contextlib
import logging
import os
import re
from csv import writer
from datetime import datetime
from logging.handlers import RotatingFileHandler
from re import split, compile

import certifi
import pandas as pd
import selenium.webdriver as webdriver
import urllib3
from bs4 import BeautifulSoup


class Scraper:
    """
    Parent class used to scrape our links contained in a list
    It stores a list of Patent objects as well as all the html pages
    """

    # creates a logging file
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')

    file_handler = RotatingFileHandler(datetime.now().strftime('scraper_%H_%M_%S_%d_%m_%Y-debug.log'), mode='w')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    def __init__(self, csv_file, save_directory, interface, options):
        self.csv_file = csv_file
        self.links = self.csv_file['result link'].tolist()  # creates a list from our links
        self.html_pages = {}  # {url: html_page}
        self.path = save_directory  # path chosen by the user
        self.interface = interface
        self.options = options  # dictionary containing our options for scraping
        self.index = 1  # index of the current patent
        self.patent_list = []  # our list of patent
        self.failed_url = []

    def __get_all_data(self):
        """
        Iterates over all our patents and extract a DataFrame containing all their data
        :return: DataFrame Object containing all the patents' data
        """
        data = pd.DataFrame()

        for patent in self.patent_list:
            data = data.append(patent.get_dataframe())

        return data

    def _write_csv_file(self):
        """
        Writes all the data returned by __get_all_data function into a csv file
        """
        dataframe = self.__get_all_data()
        df = pd.DataFrame(data=dataframe)

        # reodering our columns
        df = df[
            ["id", "title", "assignee", "inventor/author", "priority date", "filing/creation date", "publication date",
             "grant date", "link", "patent office", "type", "status", "nb_received_citations", "nb_given_citations",
             "abstract", "description", "claims"]]

        # uses the delimiter given by the user or a comma by default
        separator = self.options.get('csv_delimiter')
        os.makedirs(os.path.dirname(self.path + "/CSV/"), exist_ok=True)
        df.to_csv(self.path + '/CSV/' + 'dataFrame.csv', encoding='utf-8', index=False, sep=separator)

    def scrape(self, url):

        """
        Main function used to scrape the data
        :param url: url to the patent

        First it renders the page by calling the render function which stores the html into the dictionary 'html_pages'
        Then, using the 'options' dictionary, it scrapes only the wanted data
        Finally it creates a Patent object, feeding it the scraped data
        It then appends this patent to the list 'patent_list'
        And increases the progress on the progress bar

        options =
        {
            'save_directory': TEXT,
            'scrape_abstract': BOOLEAN,
            'scrape_title': BOOLEAN,
            'scrape_description': BOOLEAN,
            'scrape_claims': BOOLEAN,
            'scrape_citations': BOOLEAN,
            'scrape_cited': BOOLEAN,
            'scrape_similar': BOOLEAN,
            'scrape_legal': BOOLEAN,
            'scrape_classifications': BOOLEAN,
            'separate_files': BOOLEAN,
            'language': BOOLEAN,
            'concatenate': DICTIONARY, as follows: {
                'TITLE': BOOLEAN,
                'ABSTRACT': BOOLEAN,
                'DESCRIPTION': BOOLEAN,
                'CLAIMS': BOOLEAN
            },
            'download_pdf': BOOLEAN,
            'csv_delimiter': CHAR
        }
        """

        print('link: \t' + url)

        self.render(url)  # renders our html page using the url

        try:
            soup = BeautifulSoup(self.html_pages.get(url), 'html.parser')  # creates a Soup object with our html page
            data = {}  # dictionary contaning all of our data
            temp = self.csv_file.to_dict()

            """Initialize data dictionary with our patent value
            This looks into the csv file for all the data that doesnt need to be scraped
            It also standardizes the patent id
            """
            try:
                for key, value in temp.items():
                    value = str(value.get(self.links.index(url)))
                    if key == 'id':
                        data[key] = value.replace('-', '')
                    else:
                        data[key] = value

            except Exception as msg:
                self.logger.exception(str(msg))
                print(msg)

            try:
                current_ID = data['id']
            except:
                current_ID = data['Id']

            print('Patent ID: ' + current_ID)

            # boolean, defines the language when need to scrape
            english = self.options.get('language')
            self.logger.info(url + " English option=" + str(english))

            """ below is all the optional stuff """

            # PDF download
            self.logger.info('Patent ID: ' + current_ID + " PDF Download=" + str(self.options.get('download_pdf')))

            if self.options.get('download_pdf'):
                data['pdf link'] = self.__get_pdf_link(soup, current_ID)

            # ABSTRACT
            self.logger.info(
                'Patent ID: ' + current_ID + " Scrape abstract=" + str(self.options.get('scrape_abstract')))

            if self.options.get('scrape_abstract'):
                data['abstract'] = self.__get_abstract(soup, english, current_ID)

                # adds a Y/N column in the final csv file depending on if there is an abstract or not
                # we have the same column for the description and claims as well
                if not data['abstract']:
                    data['ABSTRACT'] = 'N'
                else:
                    data['ABSTRACT'] = 'Y'

            # DESCRIPTION
            self.logger.info(
                'Patent ID: ' + current_ID + " Scrape description=" + str(self.options.get('scrape_description')))

            if self.options.get('scrape_description'):
                data['description'] = self.__get_description(soup, english, current_ID)

                if not data['description']:
                    data['DESCRIPTION'] = 'N'
                else:
                    data['DESCRIPTION'] = 'Y'

            # CLAIMS
            self.logger.info('Patent ID: ' + current_ID + " Scrape claims=" + str(self.options.get('scrape_claims')))

            if self.options.get('scrape_claims'):
                data['claims'] = self.__get_claims(soup, english, current_ID)

                if not data['claims']:
                    data['CLAIMS'] = 'N'
                else:
                    data['CLAIMS'] = 'Y'

            # CLASSIFICATIONS
            self.logger.info(
                'Patent ID: ' + current_ID + ", Scrape classifications=" + str(
                    self.options.get('scrape_classifications')))

            if self.options.get('scrape_classifications'):
                data['classifications'] = self.__get_classifications(soup, current_ID)

            # LEGAL EVENTS
            self.logger.info(
                'Patent ID: ' + current_ID + ", Scrape legal events=" + str(self.options.get('scrape_legal')))

            if self.options.get('scrape_legal'):
                data['legal_events'] = self.__get_legal_events(soup, current_ID)

            # TITLE
            self.logger.info('Patent ID: ' + current_ID + ", Scrape title=" + str(self.options.get('scrape_title')))

            if not self.options.get('scrape_title'):
                data['title'] = ''

            # TYPE OF PATENT
            data['type'] = self.__get_type(soup)

            # STATUS OF PATENT
            data['status'] = self.__get_status(soup, current_ID)

            # INVENTOR
            data['inventor/author'] = self.__get_inventor(soup, current_ID)

            # ASSIGNEE
            data['assignee'] = self.__get_assignee(soup, current_ID)

            """Creates our Patent object with all our data"""
            patent = Patent(data, self.logger)

            # CITATIONS
            # always calls the scraping for the citations, just to get the number of citations per patent
            option = self.options.get('scrape_citations')
            self.logger.info('Patent ID: ' + current_ID + ', Scraper citations= ' + str(option))
            patent.citations.get_given_citations(soup, option)
            patent.nb_given_citations = patent.citations.nb_given
            self.logger.info(
                'Patent ID: ' + current_ID + ', number of citations found: ' + str(patent.nb_given_citations))

            option = self.options.get('scrape_cited')
            self.logger.info('Patent ID: ' + current_ID + ', Scrape cited= ' + str(option))
            patent.citations.get_received_citations(soup, option)
            patent.nb_received_citations = patent.citations.nb_received
            self.logger.info('Patent ID: ' + current_ID + ', number of cited patents found: '
                             + str(patent.nb_received_citations))

            # SIMILAR DOCUMENTS
            self.logger.info('Patent ID: ' + current_ID +
                             ' Scrape similar documents=' + str(self.options.get('scrape_similar')))

            if self.options.get('scrape_similar'):
                patent.citations.get_similar_documents(soup)

            self.patent_list.append(patent)  # adding the patent to the list
            text = 'Scraping... ({}/{})'.format(self.interface.nb_scraped, self.interface.MAX_LEN)
            self.interface.add_increment(text)

        except TypeError as msg:
            print("Exception: " + str(msg))

        except Exception as msg:
            self.failed_url.append(url)
            self.logger.error(
                'URL "{}", ID {} ERROR: {}'.format(url, current_ID, str(msg)))
            print('The url "{}" failed to scrape, trying again... \n ERROR: {}'.format(url, msg))
            self.scrape(url)

    def render(self, url):
        """
        Renders a patent page from Google Patent using a headless Chrome
        When the page has fully rendered, adds the html page to a dictionary with the url as the key: {url: html}

        DEPENDENCIES:
        For this to work, the user needs to have a recent version of Chrome installed
        as well as the compatible chromedriver available at: http://chromedriver.chromium.org/downloads
        This chromedriver needs to be located in PATH

        :param url: url to the patent
        """
        content = None
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.set_headless(headless=True)

        try:
            with contextlib.closing(webdriver.Chrome(chrome_options=chrome_options)) as driver:
                while content is None:
                    driver.get(url)
                    content = driver.page_source

            # content returned if there is no response from the server
            if content == '<html xmlns="http://www.w3.org/1999/xhtml"><head></head><body></body></html>':
                driver.quit()
                raise ConnectionError('Page is empty. Please check your internet connection')

            driver.quit()

            self.html_pages.update({url: content})

        except Exception as e:
            self.logger.exception(str(e) + "\n URL :" + url)
            print('Error while rendering page : \n' + str(e))
            print('Trying again...')
            self.render(url)

    def save(self):
        """
        Calls every method used to save data: txt files and csv files
        """
        try:
            self.interface.label_status.setText('Saving files...')

            for patent in self.patent_list:
                concatenated = self.options.get('concatenate')
                separated = self.options.get('separate_files')
                patent.write_txt_files(self.path + '/TXT/', concatenated, separated)
                patent.write_citations(self.path)

            self._write_csv_file()
        except Exception as msg:
            print(msg)

    def download_pdf(self, url):
        """
        Creates our download folder if not already existing
        Downloads the pdf file
        :param url: link to a url from our initial csv file
        """
        try:
            self.logger.info('Downloading PDF: ' + url)

            dirpath = self.path + '/PDF/'
            os.makedirs(os.path.dirname(dirpath), exist_ok=True)  # creates our destination folder

            connection_pool = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
            resp = connection_pool.request('GET', url)

            with open(dirpath + split('/', url)[-1], 'wb') as f:
                f.write(resp.data)
                f.close()
            resp.release_conn()

            self.interface.nb_pdf += 1
            text = 'Downloading PDF... ({}/{})'.format(self.interface.nb_pdf, self.interface.MAX_LEN)
            print('Downloading :' + url)
            self.interface.add_increment(text)

        except Exception as msg:
            self.logger.exception('Cannot download PDF: ' + url + str(msg))
            print('Cannot download PDF: ' + url)
            print(msg)
            print('Trying again...')
            self.download_pdf(url)

    def __get_pdf_link(self, soup, id):
        """
        Uses beautiful soup to scrape our pdf link
        :param soup: BeautifulSoup object, returned from our _get_next_soup method
        :return: link to the pdf file
        """
        try:
            pdf_link = []

            for x in soup.find_all(href=compile('https://patentimages.'), class_='style-scope patent-result'):
                pdf_link.append(x['href'])
                url = pdf_link[-1]

            if url is not None:
                self.logger.info("Patent ID: " + id + ", PDF link: " + url)
                return url

        except Exception as msg:
            self.logger.info("Patent ID: " + id + ", no PDF link found \n" + str(msg))
            print('No PDF link found')
            print(msg)

    def __get_abstract(self, soup, english, id):
        """
        Uses BeautifulSoup to scrape our abstract
        :param soup: BeautifulSoup object, returned from our _get_next_soup method
               english: Boolean, the user can choose between translated or original text
                        True is translated text
                        False is original text
        :return: -String containing our abstract if found
                 -Empty string if nothing found
        """

        found_abstract = False  # boolean is true if an 'abstract' class has been detected
        translated = False  # boolean is true if the text has been translated by Google
        out_abstract = ''  # buffer string to concatenate our scraped strings

        for x in soup.find_all(class_='abstract style-scope patent-text'):  # first class which starts the abstract
            for y in x.find_all(class_='notranslate style-scope patent-text'):  # container of all text
                for txt in y.find_all(text=True):  # extracts only the text

                    parent_class = txt.parent['class']

                    # if the class is different than 'google-src-text'
                    # it means that the text has been translated by Google
                    # which we want only if the user decided to get the english text
                    if parent_class[0] != 'google-src-text' and english is True:
                        out_abstract += txt
                        found_abstract = True
                        translated = True

                    elif english is False:
                        for original in y.find_all(class_='google-src-text style-scope patent-text'):
                            out_abstract += original.get_text()
                        found_abstract = True
                        translated = True

            if translated is False:  # if our text has not been translated we can concatenate
                out_abstract += x.get_text()
                found_abstract = True

        if found_abstract is False:
            self.logger.info("Patent ID: " + id + ', no Abstract found')
            print('No abstract found')
            return ""
        else:
            self.logger.info("Patent ID: " + id + ', Abstract found')
            return out_abstract

    def __get_description(self, soup, english, id):
        """
       Uses BeautifulSoup to scrape our abstract
        :param  soup: BeautifulSoup object, returned from our _get_next_soup method
                english: Boolean, the user can choose between translated or original text
                        True is translated text
                        False is original text
        :return: -String containing our abstract if found
                 -Empty string if nothing found
        """

        translated = False
        found_description = False
        out_description = ''

        for x in soup.find_all(class_='description style-scope patent-text'):
            for y in x.find_all(class_='notranslate style-scope patent-text'):
                for txt in y.find_all(text=True):

                    parent_class = txt.parent['class']

                    if parent_class[0] != 'google-src-text' and english is True:
                        out_description += txt
                        found_description = True
                        translated = True

                    elif english is False:
                        for original in y.find_all(class_='google-src-text style-scope patent-text'):
                            out_description += original.get_text()
                        found_description = True
                        translated = True

            if translated is False:
                out_description += x.get_text()
                found_description = True

        if found_description is False:
            self.logger.info('Patent ID: ' + id + ', no Description found')
            print('No description found')
            return ""
        else:
            self.logger.info('Patent ID: ' + id + ', Description found')
            return out_description

    def __get_claims(self, soup, english, id):
        """
        Uses BeautifulSoup to scrape our abstract
        :param soup: BeautifulSoup object, returned from our _get_next_soup method
               english: Boolean, the user can choose between translated or original text
                        True is translated text
                        False is original text
        :return: -String containing our abstract if found
                 -Empty string if nothing found
        """

        translated = False
        found_claims = False
        out_claims = ''

        for x in soup.find_all(class_='claims style-scope patent-text'):
            for y in x.find_all(class_='notranslate style-scope patent-text'):
                for txt in y.find_all(text=True):

                    parent_class = txt.parent['class']

                    if parent_class[0] != 'google-src-text' and english is True:
                        out_claims += txt
                        found_claims = True
                        translated = True

                    elif english is False:
                        for original in y.find_all(class_='google-src-text style-scope patent-text'):
                            out_claims += original.get_text()
                        found_claims = True
                        translated = True

            if translated is False:
                out_claims += x.get_text()
                found_claims = True

        if found_claims is False:
            self.logger.info('Patent ID: ' + id + ', no Claims found')
            print('No claims found')
            return ""
        else:
            self.logger.info('Patent ID:' + id + ', Claims found')
            return out_claims

    def __get_type(self, soup):
        """Scrapes the type of patent
        :return String
        :exception  TypeError if nothing is found (extremely rare)"""
        try:
            return soup.find(class_='tagline style-scope patent-result').text

        except TypeError as msg:
            self.logger.exception(str(msg))
            print(msg)
            return ''

    def __get_status(self, soup, id):
        """Scrapes the status of patent
        :return String """
        try:
            status = soup.find_all(class_='appstatus style-scope family-viewer', id='')[-1].text.replace('\n', '')

            """Sometimes there are multiple statuses, we only want the last one, if empty, the first one"""
            if status:
                self.logger.info('Patent ID: ' + id + ', Status found')
                return status
            else:
                self.logger.info('Patent ID: ' + id + ', Status found')
                return status[0]
        except:
            self.logger.info('Patent ID: ' + id + ', no Status found')
            print('No status found')
            return ''

    def __get_classifications(self, soup, id):
        """Scrapes the classifications of patent
        :return:    -String
                    -Empty String if nothing is found
        :exception: AttributeError: if the field is not found in the page"""

        out_classifications = ''

        try:
            for x in soup.find_all(class_='style-scope classification-viewer'):
                txt = x.get_text()
                out_classifications += re.sub('\n+', '\n', txt)  # gets rid of the unecessary \n in the text

            self.logger.info('Patent ID: ' + id + ', Classifications found')
            return out_classifications
        except AttributeError:
            self.logger.info('Patent ID: ' + id + ', no Classifications found')
            print('No classification found')
            return ''

    def __get_legal_events(self, soup, id):
        """Scrapes the legal events of patent
        :return:    -String
                    -Empty String if nothing is found
        :exception: AttributeError: if the field is not found in the page"""

        out_legal_events = ''

        try:
            events = soup.find('h3', id='legalEvents').next_sibling.next_sibling

            if len(events) != 0:

                for x in events.find_all(class_='tr style-scope patent-result'):
                    out_legal_events += x.get_text()

            self.logger.info('Patent ID: ' + id + ', Legal Events found')
            return out_legal_events

        except AttributeError:
            self.logger.info('Patent ID: ' + id + ', no Legal Events found')
            print('No legal events found')
            return ''

    def __get_inventor(self, soup, id):
        try:
            inventor = []

            for x in soup.find_all(attrs={'data-inventor': compile(r".*")}, class_='style-scope patent-result'):
                inventor.append(x['data-inventor'])
                self.logger.info('Patent ID: ' + id + ', Inventor found')
                return inventor[-1]

        except Exception as msg:
            self.logger.info('Patent ID: ' + id + ', no Inventor found')
            print("No inventor found")
            return ''

    def __get_assignee(self, soup, id):
        try:
            inventor = []

            for x in soup.find_all(attrs={'data-assignee': compile(r".*")}, class_='style-scope patent-result'):
                inventor.append(x['data-assignee'])
                self.logger.info('Patent ID: ' + id + ', Assignee found')
                return inventor[-1]

        except Exception as msg:
            self.logger.info('Patent ID: ' + id + ', no Assignee found')
            print("No assignee found")
            return ''


class Citations:
    """
    class to contain our Patent's citations into a dictionary
    """

    def __init__(self, patent_id, logger):
        self.given = {'SOURCE': 'TARGET'}
        self.received = {'SOURCE': 'TARGET'}
        self.similar_documents = {'SOURCE': 'TARGET'}
        self.patent_id = patent_id
        self.nb_given = 0
        self.nb_received = 0
        self.logger = logger

    def get_given_citations(self, soup, option):
        """
        Uses BeautifulSoup to scrape our cited patents
        :param soup: BeautifulSoup object, returned from our _get_next_soup method
        :return: -String containing our abstract if found
                 -None if nothing found
        """
        try:
            out_givencitations = {}  # buffer array that contains the given citations
            """
            all of them are contained under a title named patentCitations
            here we use a sibling of sibling because the first one is the '\n'
            """

            ids = []
            priority_dates = []
            publication_dates = []
            assignees = []
            titles = []
            all = []

            cit = soup.find('h3', id='patentCitations').next_sibling.next_sibling

            if len(cit) != 0:
                # looking for the specific rows that store the ID of the patent

                for y in cit.find_all(class_="td style-scope patent-result"):
                    all.append(re.sub('\n+', '', y.get_text()))

                for x in cit.find_all(attrs={'data-result': compile('patent/')}):
                    ids.append(x.get_text())
                    self.nb_given += 1

                for i in range(0, len(all), 4):
                    priority_dates.append(str(all[i]))

                for i in range(1, len(all), 4):
                    publication_dates.append(str(all[i]))

                for i in range(2, len(all), 4):
                    assignees.append(str(all[i]))

                for i in range(3, len(all), 4):
                    titles.append(str(all[i]))

                out_givencitations.update({'ids': ids,
                                           'priority_dates': priority_dates,
                                           'publication_dates': publication_dates,
                                           'assignees': assignees,
                                           'titles': titles})

                if option:
                    self.given.update({self.patent_id: out_givencitations})

        except AttributeError:  # if there is no citations 'find_all' will raise an AttributeError exception
            self.logger.info('Patent ID: ' + self.patent_id + ', no Cited Patents found')
            print('No cited patents found')
            return None

    def get_received_citations(self, soup, option):
        """
        Uses BeautifulSoup to scrape our cited patents
        :param soup: BeautifulSoup object, returned from our _get_next_soup method
        :return: -String containing our abstract if found
                 -None if nothing found
        """
        try:
            out_receivedcitations = {}  # buffer array that contains the received citations

            """
            all of them are contained under a title named citedBy
            here we use a sibling of sibling because the first sibling is the '\n'
            """

            ids = []
            priority_dates = []
            publication_dates = []
            assignees = []
            titles = []
            all = []

            cit = soup.find('h3', id='citedBy').next_sibling.next_sibling

            if len(cit) != 0:

                for y in cit.find_all(class_="td style-scope patent-result"):
                    all.append(re.sub('\n+', '', y.get_text()))

                for x in cit.find_all(attrs={'data-result': compile('patent/')}):
                    ids.append(x.get_text())
                    self.nb_received += 1

                for i in range(0, len(all), 4):
                    priority_dates.append(str(all[i]))

                for i in range(1, len(all), 4):
                    publication_dates.append(str(all[i]))

                for i in range(2, len(all), 4):
                    assignees.append(str(all[i]))

                for i in range(3, len(all), 4):
                    titles.append(str(all[i]))

                out_receivedcitations.update({'ids': ids,
                                              'priority_dates': priority_dates,
                                              'publication_dates': publication_dates,
                                              'assignees': assignees,
                                              'titles': titles})

                if option:
                    self.received.update({self.patent_id: out_receivedcitations})

        except AttributeError:
            self.logger.info('Patent ID: ' + self.patent_id + ', no Citing Patents found')
            print('No citations found')
            return None

    def get_similar_documents(self, soup):
        try:
            out_similar_documents = {}  # buffer dict that contains the similar documents
            ids = []
            dates = []
            titles = []
            all = []

            """
            all of them are contained under a title named similarDocuments
            here we use a sibling of sibling because the first one is the '\n',
            while the next one is the one we are interested in
            """
            cit = soup.find('h3', id='similarDocuments').next_sibling.next_sibling

            if len(cit) != 0:
                # looking for the specific rows that store the ID of the patent

                for y in cit.find_all(class_="td style-scope patent-result"):
                    all.append(re.sub('\n+', '', y.get_text()))

                for i in range(0, len(all), 3):
                    ids.append(str(all[i]))

                for i in range(1, len(all), 3):
                    dates.append(str(all[i]))

                for i in range(2, len(all), 3):
                    titles.append(str(all[i]))

                out_similar_documents.update({'ids': ids, 'dates': dates, 'titles': titles})

                # storing the result into the dictionary
                self.logger.info('Patent ID: ' + self.patent_id + ', Similar documents found')
                self.similar_documents.update({self.patent_id: out_similar_documents})

        except AttributeError:
            self.logger.info('Patent ID: ' + self.patent_id + ', no Similar documents found')
            print('No similar documents found')
            return None

    def given_items(self):
        return self.given.items()

    def received_items(self):
        return self.received.items()


class Patent:
    """Object representing a Patent from Google"""

    def __init__(self, data, logger):
        try:
            self.patent_id = data['id']
        except:
            self.patent_id = data['Id']
        self.link = data['result link']
        self.assignee = data['assignee']
        self.title = data['title']
        self.inventor = data['inventor/author']
        self.logger = logger

        try:
            self.classifications = data['classifications']
        except KeyError:
            self.classifications = ''

        try:
            self.legal_events = data['legal_events']
        except KeyError:
            self.legal_events = ''

        self.priority_date = data['priority date']
        self.publication_date = data['publication date']
        self.creation_date = data['filing/creation date'],
        self.grant_date = data['grant date']

        try:
            self.pdf_link = data['pdf link']
        except KeyError:
            self.pdf_link = ''

        try:
            self.abstract = data['abstract']
            self.found_abstract = data['ABSTRACT']
        except KeyError:
            self.abstract = ''
            self.found_abstract = 'N'

        try:
            self.description = data['description']
            self.found_description = data['DESCRIPTION']
        except KeyError:
            self.description = ''
            self.found_description = 'N'

        try:
            self.claims = data['claims']
            self.found_claims = data['CLAIMS']
        except KeyError:
            self.claims = ''
            self.found_claims = 'N'

        self.type = data['type']
        self.status = data['status']
        self.citations = Citations(self.patent_id, self.logger)
        self.nb_received_citations = 0
        self.nb_given_citations = 0

    def claims(self):
        return self.claims

    def description(self):
        return self.description

    def abstract(self):
        return self.abstract

    def all_text(self):
        """
        Creates a dictionary containing our abstract, description, claims, classifications, legal events, title
        with a key identifying them
        """
        return {
            'TITLE': self.title,
            'ABSTRACT': self.abstract,
            'DESCRIPTION': self.description,
            'CLAIMS': self.claims,
            'CLASSIFICATIONS': self.classifications,
            'LEGAL_EVENTS': self.legal_events
        }

    def get_dataframe(self):
        """
        Gets every 'short' info about a patent and returns a Pandas DataFrame Object
        """
        return pd.DataFrame(
            {
                'id': self.patent_id,
                'title': self.title,
                'assignee': self.assignee,
                'inventor/author': self.inventor,
                'priority date': self.priority_date,
                'filing/creation date': self.creation_date,
                'publication date': self.publication_date,
                'grant date': self.grant_date,
                'link': self.link,
                'pdf link': self.pdf_link,
                'type': self.type,
                'status': self.status,
                'patent office': self.patent_id[:2],
                'nb_received_citations': self.nb_received_citations,
                'nb_given_citations': self.nb_given_citations,
                'abstract': self.found_abstract,
                'description': self.found_description,
                'claims': self.found_claims
            }
        )

    def write_txt_files(self, filepath, concatenated, separated):
        """
        Writes our text contained into a Patent into txt files
        :param  filepath: Output path
        :param  concatenated: dictionary : {'ABSTRACT': boolean, 'DESCRIPTION': boolean, 'CLAIMS': boolean,
                                            'TITLE': boolean}
                                            Puts all TRUE keys into a single file for each patent
                separated:  True: folders for abstract, description and claims
                            False: a single text file with all content in it
        """
        text = self.all_text()

        for name, content in text.items():

            if content:
                if concatenated.get(name) is True:
                    # creates a folder if it doesnt exist
                    os.makedirs(os.path.dirname(str(filepath) + 'CONCATENATED_ITEMS/'), exist_ok=True)

                    with open(str(filepath) + 'CONCATENATED_ITEMS' + '/' + str(self.patent_id) + '.txt',
                              'at', encoding='utf-8') as txt_file:
                        txt_file.write('\n' + name + '\n' + content + '\n')
                        txt_file.close()

                if separated is True and name is not 'TITLE':
                    # creates a folder if it doesnt exist
                    os.makedirs(os.path.dirname(filepath + str(name) + '/'), exist_ok=True)

                    with open(filepath + str(name) + '/' + str(self.patent_id) + '.txt',
                              'wt', encoding='utf-8') as txt_file:
                        txt_file.write(str('\n' + name + '\n' + content + '\n'))
                        txt_file.close()

                elif name is not 'TITLE':
                    # creates a folder if it doesnt exist
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)

                    with open(filepath + str(self.patent_id) + '.txt', 'at', encoding='utf-8') as txt_file:
                        txt_file.write(str('\n' + name + '\n' + content + '\n'))
                        txt_file.close()

    def write_given_citations(self, dirpath):
        """
        Writes our given citations from a Patent object into a csv file
        :param dirpath: Output path
        """

        if len(self.citations.given.keys()) != 1:
            os.makedirs(os.path.dirname(dirpath), exist_ok=True)

            exists = os.path.isfile(dirpath + '/' + 'given_citations.csv')

            with open(dirpath + '/' + 'given_citations.csv', 'at', encoding='utf-8', newline='') as citation_file:
                write = writer(citation_file)
                iter_citations = self.citations.given_items()

                if not exists:
                    write.writerow(['SOURCE', 'TARGET', 'priority date', 'publication date', 'assignee', 'title'])

                for citing, value in iter_citations:
                    if citing != 'SOURCE':
                        index = 0
                        for cited in value.get('ids'):
                            patent_id = str(citing).replace('-', '')
                            priority_date = value.get('priority_dates')[index]
                            publication_date = value.get('publication_dates')[index]
                            assignee = value.get('assignees')[index]
                            title = value.get('titles')[index]

                            index += 1
                            write.writerow([patent_id,
                                            cited.replace('-', ''),
                                            priority_date,
                                            publication_date,
                                            assignee,
                                            title])

            citation_file.close()

    def write_received_citations(self, dirpath):
        """
        Writes our received citations from a Patent object into a csv file
        :param dirpath: Output path
        """

        if len(self.citations.received.keys()) != 1:
            os.makedirs(os.path.dirname(dirpath), exist_ok=True)

            exists = os.path.isfile(dirpath + '/' + 'received_citations.csv')

            with open(dirpath + '/' + 'received_citations.csv', 'at', encoding='utf-8', newline='') as citation_file:
                write = writer(citation_file)
                iter_citations = self.citations.received_items()

                if not exists:
                    write.writerow(['SOURCE', 'priority date', 'publication date', 'assignee', 'title', 'TARGET'])

                for cited, value in iter_citations:
                    if cited != 'SOURCE':

                        index = 0
                        for citing in value.get('ids'):
                            patent_id = cited.replace('-', '')
                            priority_date = value.get('priority_dates')[index]
                            publication_date = value.get('publication_dates')[index]
                            assignee = value.get('assignees')[index]
                            title = value.get('titles')[index]

                            index += 1
                            write.writerow([citing.replace('-', ''),
                                            priority_date,
                                            publication_date,
                                            assignee,
                                            title,
                                            patent_id
                                            ])

            citation_file.close()

    def write_similar_documents(self, dirpath):
        """
        Writes our received citations from a Patent object into a csv file
        :param dirpath: Output path
        """

        if len(self.citations.similar_documents.keys()) != 1:
            os.makedirs(os.path.dirname(dirpath), exist_ok=True)

            exists = os.path.isfile(dirpath + '/' + 'similar_documents.csv')

            with open(dirpath + '/' + 'similar_documents.csv', 'at', encoding='utf-8',
                      newline='') as similar_documents_file:
                write = writer(similar_documents_file)

                if not exists:
                    write.writerow(['SOURCE', 'TARGET', 'TITLE', 'DATE', 'LINK'])

                for citing, cited in self.citations.similar_documents.items():
                    if citing != 'SOURCE':
                        index = 0
                        for value in cited.get('ids'):
                            pat_id = value
                            title = cited.get('titles')[index]
                            date = cited.get('dates')[index]
                            link = "https://patents.google.com/patent/" + value.replace('-', '') + "/en"

                            write.writerow([citing.replace('-', ''), pat_id, title, date, link])

                            index += 1

                similar_documents_file.close()

    def write_citations(self, dirpath):
        dirpath += '/CSV/'
        self.write_given_citations(dirpath)
        self.write_received_citations(dirpath)
        self.write_similar_documents(dirpath)
