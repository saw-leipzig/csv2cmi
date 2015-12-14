# CSV2CMI

## About

CSV2CMI is a little program to transform a table of letters (given as .csv) into the [CMI format](https://github.com/TEI-Correspondence-SIG/CMIF).
The CMI format is the underlying data format for the web service ‘[correspSearch](http://correspsearch.bbaw.de/)’ which facilitates searching across diverse distributed letter repositories.

It's intended for printed (print only) editions and catalogues of letters.

## Usage

You have to name your columns as follows:
* name of the sender: "sender"
* name of the addressee: "addressee"
* IDs of the named person: "senderID" and "addresseeID"
* the date, when the letter has been sent: "senderDate"

You may provide places as additional information:
* where a letter has been sent: "senderPlace" (with the appropriate "senderPlaceID" as proper [GeoNames URL](http://www.geonames.org/))
* where a letter has been received: "addresseePlace" (with the appropriate "addresseePlaceID" as proper [GeoNames URL](http://www.geonames.org/))

If your letters are printed across different editions, add an "edition" column and put in there the bibliographic records. Numbering of letters should be stated in a additional column named "key". Alternatively you may enter in this column a link to the edited letter on the web.
If a date is put within brackets it sets @cert to 'medium', for persName and placeName alike @evidence is set.

For sender and addressee IDs from the [GND](http://www.dnb.de/gnd) and the [VIAF](http://www.viaf.org/) are supported. 

For now only a single date can be set. 

*Check, that your table is using UTF8-encoding!*

## License

This program is available under [The MIT License (MIT)](https://opensource.org/licenses/MIT)
