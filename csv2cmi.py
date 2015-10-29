# -*- coding: utf-8 -*-

# csv2cmi
# version 0.8.2
# Copyright (c) 2015 Klaus Rettinghaus
# programmed by Klaus Rettinghaus
# licensed under MIT license

# needs Python3
import os
import csv
from xml.etree.ElementTree import Element, SubElement, Comment, tostring, ElementTree
import datetime
from xml.dom import minidom

def isodate(datestring):
        try:
            datetime.datetime.strptime(datestring, '%Y-%m-%d')
        except:
            try:
                datetime.datetime.strptime(datestring, '%Y-%m')
            except:
                try:
                    datetime.datetime.strptime(datestring, '%Y')
                except ValueError:
                    return False
                else:
                    return True
            else:
                return True
        else:
            return True

# enter here your name and the title of your edition
fileName = 'NicolaiLetters.csv'
editorName = 'Klaus Rettinghaus'
edition = 'Klaus Rettinghaus: Studien zum geistlichen Werk Otto Nicolais'
editionRef = 'http://nbn-resolving.de/urn/resolver.pl?urn:nbn:de:kobv:83-opus4-57390'
editionType = 'print'  # if your edition is online enter 'online'

# building cmi
# generating root element
root = Element('TEI')
root.set('xmlns', 'http://www.tei-c.org/ns/1.0')
root.append(Comment('Generated from table of letters with csv2cmi'))

# teiHeader
teiHeader = SubElement(root, 'teiHeader')
# file description
fileDesc = SubElement(teiHeader, 'fileDesc')
titleStmt = SubElement(fileDesc, 'titleStmt')
title = SubElement(titleStmt, 'title')
title.text = 'Briefe Otto Nicolais'
editor = SubElement(titleStmt, 'editor')
editor.text = editorName
publicationStmt = SubElement(fileDesc, 'publicationStmt')
publisher = SubElement(publicationStmt, 'publisher')
publisher.text = editorName
idno = SubElement(publicationStmt, 'idno')
idno.set('type', 'url')
idno.text = os.path.splitext(os.path.basename(fileName))[0] + '.xml'
date = SubElement(publicationStmt, 'date')
date.set('when', str(datetime.datetime.now().isoformat()))
availability = SubElement(publicationStmt, 'availability')
licence = SubElement(availability, 'licence')
licence.set('target', 'https://creativecommons.org/licenses/by/4.0/')
licence.text = 'This file is licensed under the terms of the Creative-Commons-License CC-BY 4.0'
# static source description
sourceDesc = SubElement(fileDesc, 'sourceDesc')
bibl = SubElement(sourceDesc, 'bibl')
bibl.set('type', editionType)
ref = SubElement(bibl, 'ref')
ref.set('target', editionRef)
ref.text = edition

# filling in correspondance meta-data
profileDesc = SubElement(teiHeader, 'profileDesc')

with open(fileName, 'rt') as letterTable:
    table = csv.DictReader(letterTable)
    print('Recognized columns:', table.fieldnames)
    for letter in table:
        entry = SubElement(profileDesc, 'correspDesc')
        if ('key' in table.fieldnames) and (str(letter['key'])):
            entry.set('key', str(letter['key']))
        if str(letter['sender']):
            sender = SubElement(entry, 'correspAction')
            sender.set('type', 'sent')
            senderName = SubElement(sender, 'persName')
            senderName.text = str(letter['sender'])
            if str(letter['senderID']):
                senderName.set('ref', 'http://d-nb.info/gnd/' +
                               str(letter['senderID']))
        if ('senderPlace' in table.fieldnames) and (str(letter['senderPlace'])):
            senderPlace = SubElement(sender, 'placeName')
            senderPlace.text = str(letter['senderPlace'])
            if (str(letter['senderPlace'])[0] == '[') and (str(letter['senderPlace'])[-1] == ']'):
                senderPlace.set('cert', 'medium')
            if str(letter['senderPlaceID']):
                senderPlace.set('ref', str(letter['senderPlaceID']))
        if isodate(letter['senderDate']) or isodate(letter['senderDate'][1:-1]):
            senderDate = SubElement(sender, 'date')
            if ('[' in str(letter['senderDate'])) and (']' in str(letter['senderDate'])):
                letter['senderDate']=letter['senderDate'][1:-1]
                senderDate.set('cert','medium')
                print ("Info: Added @cert for <date> in line ",table.line_num)
            senderDate.set('when', str(letter['senderDate']))
        else:
            print ("Warning: Couldn't set <date> for <correspAction> in line ",table.line_num," (no ISO format)")

        if str(letter['addressee']):
            addressee = SubElement(entry, 'correspAction')
            addressee.set('type', 'received')
            addresseeName = SubElement(addressee, 'persName')
            addresseeName.text = str(letter['addressee'])
            if (str(letter['addressee'])[0] == '[') and (str(letter['addressee'])[-1] == ']'):
                addresseeName.set('cert', 'medium')
            if str(letter['addresseeID']):
                addresseeName.set(
                    'ref', 'http://d-nb.info/gnd/' + str(letter['addresseeID']))
        if ('addresseePlace' in table.fieldnames) and (str(letter['addresseePlace'])):
            addresseePlace = SubElement(addressee, 'placeName')
            addresseePlace.text = str(letter['addresseePlace'])
            if (str(letter['addresseePlace'])[0] == '[') and (str(letter['addresseePlace'])[-1] == ']'):
                addresseeName.set('cert', 'medium')
            if str(letter['addresseePlaceID']):
                addresseePlace.set('ref', str(letter['addresseePlaceID']))

# generate empty body
text = SubElement(root, 'text')
body = SubElement(text, 'body')
p = SubElement(body, 'p')

# save cmi to file
tree = ElementTree(root)
tree.write(os.path.splitext(os.path.basename(fileName))[
           0] + '.xml', encoding="utf-8", xml_declaration=True, method="xml")
