import os
from csv import writer
from re import split, compile
from urllib import request

import pandas as pd
from bs4 import BeautifulSoup

from WebRender import render


class Scraper(object):
    """
    Parent class used to scrape our links
    """
    index = 0  # index of the current patent
    patent_list = []  # our list of patent
    MAX_LEN = 0  # the number of links to scrape, used to initialize our progress bar

    def __init__(self, sys_app, main_window):
        self.app = sys_app
        self.ui_window = main_window

        try:
            self.csv_file = ReadFile(self.ui_window.get_filepath()).dataframe()
            try:
                self.links = self.csv_file['result link'].tolist()
                self.MAX_LEN = len(self.links)

            except KeyError as e:
                print('Column not found : ' + str(e))
                self.ui_window.incompatible_data()

            self.ui_window.set_max_progress_bar(self.MAX_LEN)

        except FileNotFoundError as e:
            print('No file found : ' + str(e))
            self.ui_window.file_not_found_err()

        except IsADirectoryError as e:
            print('Entered path leads to a folder: ' + str(e))
            self.ui_window.is_directory_err()

    def chunkify(self):
        return [self.links[i::4] for i in range(4)]

    def _get_next_soup(self):
        """
        Reads our link, calls our render method to generate the HTML code, prints text in the UI
        :return: -BeautifulSoup object in order to call our methods to scrape the desired data
                 -None if we scraped the last link already
        """
        if self.index == self.MAX_LEN:
            return None

        self.ui_window.add_text(
            '[' + (str(self.index + 1) if self.index + 1 >= 10 else '0' + str(self.index + 1)) + '/'
            + (str(self.MAX_LEN) if self.MAX_LEN >= 10 else '0' + str(self.MAX_LEN))
            + '], link: \t' + self.links[self.index]
        )

        html_page = render(self.links[self.index], self.app)
        soup = BeautifulSoup(html_page, 'html.parser')
        self.index += 1

        return soup

    def show(self):
        """shows our ui"""
        self.ui_window.show()

    def __get_all_data(self):
        """
        Gets a Pandas DataFrame of all the patents in 'patent_list'
        :return: DataFrame Object containing all the patents' data
        """
        data = pd.DataFrame()

        for patent in self.patent_list:
            data = data.append(patent.get_dataframe())

        return data

    def _write_csv_file(self):
        """
        Writes all the data returned by __get_all_data into a csv file
        """
        dataframe = self.__get_all_data()
        df = pd.DataFrame(data=dataframe)
        df.to_csv('dataFrame.csv', encoding='utf-8', index=False)

    def scrape(self):
        """
        Main function used to scrape the data
        While our soup is not None we scrape data and create a Patent containing this data
        Writes our text into a TXT file, the short information in a csv file
        """
        soup = self._get_next_soup()

        while soup is not None:
            data = {}
            temp = self.csv_file.to_dict()
            """Initialize data dictionary with or patent value"""
            for key, value in temp.items():
                value = str(value.get(self.index - 1))
                data[key] = value

            print('Patent ID: ' + data['id'])

            data['pdf link'] = self.__get_pdf_link(soup)
            data['abstract'] = self.__get_abstract(soup)
            data['claims'] = self.__get_claims(soup)
            data['description'] = self.__get_description(soup)
            """Creates our Patent object with all our data"""
            patent = Patent(data)
            patent.given_citations.get_given_citations(soup)
            patent.received_citations.get_received_citations(soup)
            self.patent_list.append(patent)  # adding the patent to the list

            self.ui_window.iterate_progress_bar()  # makes our progress bar move
            soup = self._get_next_soup()  # reads the next link to scrape again

        for patent in self.patent_list:
            patent.write_txt_files('/home/guillaume/PycharmProjects/Scraper_OOP/TXT/', True)
            patent.write_txt_files('/home/guillaume/PycharmProjects/Scraper_OOP/TXT/', False)
            patent.write_citations('/home/guillaume/PycharmProjects/Scraper_OOP/')

        self._write_csv_file()
        self.ui_window.job_done()

    def __download_pdf(self, url):
        """
        Creates our download folder if not already existing
        Download the pdf file
        :param url: link to a url from our initial csv file
        """
        self.ui_window.add_text('Downloading pdf ...')
        path = '/home/guillaume/PycharmProjects/Scraper_OOP/PDF/'
        os.makedirs(os.path.dirname(path), exist_ok=True)  # creates our destination folder
        request.urlretrieve(url, path + split('/', url)[-1])  # downloads our pdf

    def __get_pdf_link(self, soup):
        """
        Uses beautiful soup to scrape our pdf link
        :param soup: BeautifulSoup object, returned from our _get_next_soup method
        :return: link to the pdf file
        """
        pdf_link = []

        for x in soup.find_all(href=compile('https://patentimages.'), class_='style-scope patent-result'):
            pdf_link.append(x['href'])
            url = pdf_link[-1]
            # self.__download_pdf(url)
            return url

    @staticmethod
    def __get_abstract(soup):
        """
        Uses BeautifulSoup to scrape our abstract
        :param soup: BeautifulSoup object, returned from our _get_next_soup method
        :return: -String containing our abstract if found
                 -Empty string if nothing found
        """
        found_abstract = False  # boolean is true if an 'abstract' class has been detected
        translated = False  # boolean is true if the text has been translated by Google
        out_abstract = ''  # buffer string to concatenate our scraped strings

        for x in soup.find_all(class_='abstract style-scope patent-text'):
            for y in x.find_all(class_='notranslate style-scope patent-text'):
                for txt in y.find_all(text=True):

                    parent_class = txt.parent['class']

                    if parent_class[0] != 'google-src-text':
                        out_abstract += txt
                        found_abstract = True
                        translated = True

            if translated is False:  # if our text has not been translated we can concatenate
                out_abstract += x.get_text()
                found_abstract = True
        if found_abstract is False:
            print('No abstract found')
            return ""
        else:
            return out_abstract

    @staticmethod
    def __get_description(soup):
        """
        Uses BeautifulSoup to scrape our description
        :param soup: BeautifulSoup object, returned from our _get_next_soup method
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

                    if parent_class[0] != 'google-src-text':
                        out_description += txt
                        found_description = True
                        translated = True

            if translated is False:
                out_description += x.get_text()
                found_description = True

        if found_description is False:
            print('No description found')

            return ""
        else:
            return out_description

    @staticmethod
    def __get_claims(soup):
        """
        Uses BeautifulSoup to scrape our claims
        :param soup: BeautifulSoup object, returned from our _get_next_soup method
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

                    if parent_class[0] != 'google-src-text':
                        out_claims += txt
                        found_claims = True
                        translated = True

            if translated is False:
                out_claims += x.get_text()
                found_claims = True

        if found_claims is False:
            print('No claims found')
            return ""
        else:
            return out_claims


class Citations:
    """
    class to contain our Patent's citations into a dictionary
    """
    def __init__(self, patent_id):
        self.text = {'SOURCE': 'TARGET'}
        self.patent_id = patent_id

    def get_given_citations(self, soup):
        """
        Uses BeautifulSoup to scrape our cited patents
        :param soup: BeautifulSoup object, returned from our _get_next_soup method
        :return: -String containing our abstract if found
                 -None if nothing found
        """
        try:
            out_givencitations = []  # buffer array that contains the given citations
            """
            all of them are contained under a title named patentCitations
            here we use a sibling of sibling because the first one is the '\n',
            while the next one is the one we are interested in
            """
            cit = soup.find('h3', id='patentCitations').next_sibling.next_sibling

            if len(cit) != 0:
                # looking for the specific rows that store the ID of the patent

                for x in cit.find_all(attrs={'data-result': compile('patent/')}):
                    out_givencitations.append(x.get_text())

                # storing the result into the dictionary
                self.text.update({self.patent_id: out_givencitations})

        except AttributeError:  # if there is no citations it will raise an AttributeError exception
            print('No cited patents found')
            return None

    def get_received_citations(self, soup):
        """
        Uses BeautifulSoup to scrape our cited patents
        :param soup: BeautifulSoup object, returned from our _get_next_soup method
        :return: -String containing our abstract if found
                 -None if nothing found
        """
        try:
            out_receivedcitations = []  # buffer array that contains the received citations

            """
            all of them are contained under a title named citedBy
            here we use a sibling of sibling because the first sibling is the '\n',
            while the next one is the one we are interested in
            """
            cit = soup.find('h3', id='citedBy').next_sibling.next_sibling
            if len(cit) != 0:
                for x in cit.find_all(attrs={'data-result': compile('patent/')}):
                    out_receivedcitations.append(x.get_text())

                self.text.update({self.patent_id: out_receivedcitations})

        except AttributeError:
            print('No citations found')
            return None

    def items(self):
        return self.text.items()


class Patent:
    """Object representing a Patent from Google"""
    def __init__(self, data):
        self.patent_id = data['id']
        self.link = data['result link']
        self.assignee = data['assignee']
        self.title = data['title']
        self.inventor = data['inventor/author']
        self.priority_date = data['priority date']
        self.publication_date = data['publication date']
        self.creation_date = data['filing/creation date'],
        self.grant_date = data['grant date']
        self.pdf_link = data['pdf link']
        self.abstract = data['abstract']
        self.description = data['description']
        self.claims = data['claims']
        self.given_citations = Citations(self.patent_id)
        self.received_citations = Citations(self.patent_id)

    def claims(self):
        return self.claims

    def description(self):
        return self.description

    def abstract(self):
        return self.abstract

    def all_text(self):
        """
        Creates a dictionary containing our abstract, description and claims with a key identifying them
        """
        return {
            'ABSTRACT': self.abstract,
            'DESCRIPTION': self.description,
            'CLAIMS': self.claims
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
                'pdf link': self.pdf_link
            }
        )

    def write_txt_files(self, path, concatenated):
        """
        Writes our text contained into a Patent into txt files
        :param path: Output path
        :param concatenated: True= All our text into a single file,
                             False= Distinct files for abstract, description and claims
        """
        text = self.all_text()

        if concatenated is True:
            for name, content in text.items():
                if content:
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(str(path) + str(self.patent_id) + '.txt', 'a') as txt_file:
                        txt_file.write(name + '\n' + content + '\n')
                    txt_file.close()
        else:
            for name, content in text.items():
                if content:
                    os.makedirs(os.path.dirname(path + name + '/'), exist_ok=True)
                    with open(str(path) + '/' + str(name) + '/' + str(name) + '_' + str(self.patent_id) + '.txt',
                              'a') as txt_file:
                        txt_file.write(name + '\n' + content + '\n')
                        txt_file.close()

    def write_given_citations(self, path):
        """
        Writes our given citations from a Patent object into a csv file
        :param path: Output path
        """

        exists = os.path.isfile(path + 'given_citations.csv')
        with open(path + 'given_citations.csv', 'a') as citation_file:

            write = writer(citation_file)
            iter_citations = self.given_citations.items()

            if not exists:
                write.writerow(['SOURCE', 'TARGET'])

            for citing, value in iter_citations:
                if citing != 'SOURCE':
                    for cited in value:     # gets rid of the - in the patent name from our original csv file
                        write.writerow([citing.replace('-', ''),
                                        cited.replace('-', '')])  # the citing patent is the scraped patent
        citation_file.close()

    def write_received_citations(self, path):
        """
        Writes our received citations from a Patent object into a csv file
        :param path: Output path
        """
        exists = os.path.isfile(path + 'received_citations.csv')
        with open(path + 'received_citations.csv', 'a') as citation_file:

            write = writer(citation_file)
            iter_citations = self.received_citations.items()

            if not exists:
                write.writerow(['SOURCE', 'TARGET'])

            for cited, value in iter_citations:
                if cited != 'SOURCE':
                    for citing in value:
                        write.writerow(
                            [citing.replace('-', ''), cited.replace('-', '')])  # the cited patent is the scraped patent
        citation_file.close()

    def write_citations(self, path):
        self.write_given_citations(path)
        self.write_received_citations(path)


class ReadFile:
    """
    Object representing our original csv file, stored into a Pandas DataFrame
    """
    def __init__(self, file_name):
        self.f = open(file_name)
        self.data_frame = pd.read_csv(self.f, skiprows=[0], encoding='utf-8')
        self.f.close()

    def dataframe(self):
        return self.data_frame
