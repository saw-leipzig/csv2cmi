# CSV2CMI

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

If your letters are printed across different editions, add an "edition" column and put in there the bibliographic records. Numbering of letters should be stated in a additional column named "key". Alternatively you may enter in this column a link to the edited letter on the web.
If a date is put within brackets it sets `@cert` to `"medium"`, for `<persName>`, `<orgName>`, and `<placeName>`  alike `@evidence` is set.  
By default only edited letters (i.e. letters with a given edition) are transferred to CMI output. If you want to convert your complete catalogue, use the `-a` option.  
With the `--line-numbers` option activated, CSV2CMI will store the line number of each letter in the `n` attribute of `<correspDesc>`.

For sender and addressee IDs from the [GND](http://www.dnb.de/gnd) and the [VIAF](http://www.viaf.org/) are supported.

For providing essential CMI information like the editor's name or the publisher an [INI file](https://en.wikipedia.org/wiki/INI_file) is needed.

The output is a minified XML file.


#### Limitations
For now only a single date can be set; ISO format (YYYY-MM-DD) has to be used.

*Check, that your table is using UTF8-encoding!*

## License

This program is available under [The MIT License (MIT)](https://opensource.org/licenses/MIT)
