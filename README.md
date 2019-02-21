# CSV2CMI
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.1249332.svg)](https://doi.org/10.5281/zenodo.1249332)
![GitHub release](https://img.shields.io/github/release/saw-leipzig/csv2cmi.svg)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/fe9e5985815b4c72b5cd743205a1e416)](https://www.codacy.com/app/rettinghaus/csv2cmi?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=saw-leipzig/csv2cmi&amp;utm_campaign=Badge_Grade)
[![license](https://img.shields.io/github/license/saw-leipzig/csv2cmi.svg)](https://opensource.org/licenses/MIT)

## About

CSV2CMI is a little program to transform a table of letters (given as .csv) into the [CMI format](https://github.com/TEI-Correspondence-SIG/CMIF).
The CMI format is the underlying data format for the web service *[correspSearch](https://correspsearch.net)* which facilitates searching across diverse distributed letter repositories.

It is mainly intended for printed (print only) editions and catalogues of letters.

## Usage

You have to name your columns as follows:
* name of the sender: "sender"
* name of the addressee: "addressee"
* IDs of the named person or organization: "senderID" and "addresseeID" (this is essential for *correspSearch*)
* the date, when the letter has been sent: "senderDate"

You may provide additional information:
* where a letter has been sent: "senderPlace" (with the appropriate "senderPlaceID" as proper [GeoNames URL](http://www.geonames.org/))
* where a letter has been received: "addresseePlace" (with the appropriate "addresseePlaceID" as proper [GeoNames URL](http://www.geonames.org/))
* when a letter has been received: "addresseeDate"

Furthermore an "edition" column for a bibliographic record, a "key" column for the corresponding number of the edited letter, and even a "note" column can be added.

Various senders or addressees of a letter have to be written in the same cell with a separator that is specified with the `"--extra-delimiter"`-option (IDs have to follow the same order respectively).

Dates have to be entered in ISO format. Support for [EDTF](https://www.loc.gov/standards/datetime/edtf.html) is implemented to parse uncertain / approximate dates, intervals and sets.  

For providing essential CMI information like the editor's name or the publisher an [INI file](https://en.wikipedia.org/wiki/INI_file) is needed.

*Check, that your table is using UTF8-encoding!*

For options and further information check the [wiki](https://github.com/saw-leipzig/csv2cmi/wiki).

## License

This program is available under [The MIT License (MIT)](https://opensource.org/licenses/MIT)

__If you use this software, please cite it!__
