# Google-Patent-Scraper
This tool provides an interface which enables the user to select what to extract from the [Google Patents website](https://www.google.com/patents).

## Interface
![interface](https://i.imgur.com/Fkc1tOo.png)

### Data Extraction
It uses as input the CSV file given by Google Patents and can extract :
* **Text files** :
```
  Titles
  Abstracts
  Descriptions
  Claims
  Legal Events
  Classifications
```
* **CSV files** :
```
  Citations
  Similar documents
```
* **Figures**
* **PDF files**

### Langage
The user has the option to choose between English (if Google provides an English translation) or the original patent langage.
If no English translation is found, it defaults to the original langage.

### Concatenation
The user also has the option to concatenate text files and get one big text file instead of multiple small ones.
This works only for the Title, Abstract, Description and Claims.
It concatenates only the text of individual patents.

### Folders
The tool will create multiple folders :
* **CSV** :
This folder will contain every CSV File extracted : Given Citations, Received Citations, Non-patents Citations, Similar Documents and DataFrame.
The latter is the Google Patent CSV file with added data :
```
Patent Office
Type
Status
Number of Received Citations
Number of Given Citations
Number of Non-patent Citations
Abstract (Y/N)
Description (Y/N)
Claims (Y/N)
```

* **Figures** :
This folder will contain every figure linked to a patent. Those are extracted using the link in the input CSV File.

* **Text** :
This folder can contain multiple folders if the user chooses so :
```
Abstract
Claims
Classifications
Descriptions
Legal Events
Concatenated items
```
Each one of these subfolders will contain a unique text file for every Patent named using the patent ID (example : USXXXXXXX)

* **PDF** :
As the name subtly implies, this folder will contain all the PDF files.

* **log** :
This folder will contain the log files generated after every execution of the program.

## Dependencies
### Python
```
Developed using Python 3.6
```
### Packages
```
selenium
pandas
PyQt5
beautifulsoup4
```
In order to use this tool, you also need the latest Chrome as well as the latest [chromedriver executable](https://chromedriver.storage.googleapis.com/index.html) .
If you don't know which version is the latest, check the [LATEST_RELEASE](https://chromedriver.storage.googleapis.com/LATEST_RELEASE) file.

## Compatibility
This tool is executable on Windows, macOS and most Linux distributions.

## Installation

### Linux and macOS

I recommend using [Anaconda](https://www.anaconda.com/download/) and to download the 3.6 Python version.

#### Creating a Python environment using Anaconda
Launch a Terminal and enter these following lines :
```
conda create -n Scraper
```
```
source activate Scraper
```
#### Installing the necessary packages
```
conda install pandas selenium beautifulsoup4 && pip install cython PyQt5
```

#### Installing chromedriver
Download the latest [chromedriver zip](https://chromedriver.storage.googleapis.com/index.html).
If you don't know which version is the latest, check the [LATEST_RELEASE](https://chromedriver.storage.googleapis.com/LATEST_RELEASE) file.

Unzip the downloaded file into this directory :
```
/usr/local/bin
```

### Windows

For Windows the installation process is the same than on Linux or macOS except for the chromedriver installation.

#### Installing chromedriver
Download the latest [chromedriver zip](https://chromedriver.storage.googleapis.com/index.html).
If you don't know which version is the latest, check the [LATEST_RELEASE](https://chromedriver.storage.googleapis.com/LATEST_RELEASE) file.

Unzip the downloaded file into this directory :
```
C:\Windows\
```

## Author

* **Guillaume Brocard** - French Student in Computer Science - [CreepMania](https://www.github.com/CreepMania) - [Linkedin](https://www.linkedin.com/in/guillaume-brocard/)

## Final Note

I hope you will find this tool useful, as imperfect as it is. 
It was created during an 11 weeks internship for my technological degree in Computer Science so of course every comment is appreciated and feel free to contribute !

I apologize for any possible grammatical mistake or any misspelling as English is not my mother langage.

Thanks for your time !


