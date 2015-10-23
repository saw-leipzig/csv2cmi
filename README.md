# CSV2CMI

## About

CSV2CMI is a little program to transform a table of letters (given as .csv) into the [CMI format](https://github.com/TEI-Correspondence-SIG/CMIF).
The CMI format is the underlying data format for the web service ‘[correspSearch](http://correspsearch.bbaw.de/)’ which facilitates searching across diverse distributed letter repositories.

It's intended for printed (print only) editions and catalogues of letters.

For now it is a rather stupid program:
* it assumes provided person ids are a [GND number from the German National Library](http://www.dnb.de/gnd)
* there is no way to differentiate between persons (persName) and organizations
* just one edition (sourceDesc/bibl) may be entered
* only a single date can be set

## Usage

You have to name your columns as follows: 
* name of the sender: "sender" 
* name of the addressee: "addressee"
* ids of the named person: "senderID" and "addresseeID"
* the date, when the letter has been sent: "senderDate"

You may provide places as additional information: 
* where a letter has been sent: "senderPlace" (with the appropriate "senderPlaceID" as proper [GeoNames URL](http://www.geonames.org/))
* where a letter has been received: "addresseePlace" (with the appropriate "addresseePlaceID" as proper [GeoNames URL](http://www.geonames.org/))

If your printed letters are numbered, put the numbers in a additional column named "key". 
If a name is put within brackets it sets @cert to 'medium'.

## License

This program is available under [The MIT License (MIT)](https://opensource.org/licenses/MIT)
