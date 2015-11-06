# -*- coding: utf-8 -*-

# csv2cmi
# version 0.8.5
# Copyright (c) 2015 Klaus Rettinghaus
# programmed by Klaus Rettinghaus
# licensed under MIT license

# needs Python3
import os
import csv
from xml.etree.ElementTree import Element, SubElement, Comment, tostring, ElementTree
import datetime
from xml.dom import minidom

# enter here your name and the title of your edition
fileName = 'NicolaiLetters.csv'
projectName = 'Briefe Otto Nicolais'
editorName = 'Klaus Rettinghaus'
edition = 'Klaus Rettinghaus: Studien zum geistlichen Werk Otto Nicolais'
editionRef = 'http://nbn-resolving.de/urn/resolver.pl?urn:nbn:de:kobv:83-opus4-57390'
editionType = 'print'  # if your edition is online replace with 'online'

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

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

# function for putting the place in <correspAction>
def createPlace(placestring):
        if letter[placestring]:
            placeName = SubElement(sender, 'placeName')
            if letter[placestring].startswith('[') and letter[placestring].endswith(']'):
                placeName.set('evidence', 'conjecture')
                letter[placestring]=letter[placestring][1:-1]
                print ("Info: Added @evidence for <placeName> in line ",table.line_num)
            placeName.text = str(letter[placestring])
            if (placestring+'ID' in table.fieldnames) and (letter[placestring+'ID']):
                if 'http://www.geonames.org/' in letter[placestring+'ID']:
                    placeName.set('ref', str(letter[placestring+'ID']))
                else:
                    print (bcolors.WARNING,"Warning: No standardized ID in line",table.line_num,bcolors.ENDC)
            else:
                print (bcolors.WARNING,"Warning: Missing ID for",letter[placestring],"in line",table.line_num,bcolors.ENDC)

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
title.text = projectName
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
        if letter['sender']:
            sender = SubElement(entry, 'correspAction')
            sender.set('type', 'sent')
            senderName = SubElement(sender, 'persName')
            if letter['sender'].startswith('[') and letter['sender'].endswith(']'):
                senderName.set('evidence', 'conjecture')
                letter['sender']=letter['sender'][1:-1]
                print ("Info: Added @evidence for <persName> in line ",table.line_num)
            senderName.text = letter['sender']
            if str(letter['senderID']):
                senderName.set('ref', 'http://d-nb.info/gnd/' + str(letter['senderID']))

        if 'senderPlace' in table.fieldnames:
            createPlace('senderPlace')

        if isodate(letter['senderDate']) or isodate(letter['senderDate'][1:-1]):
            senderDate = SubElement(sender, 'date')
            if ('[' in str(letter['senderDate'])) and (']' in str(letter['senderDate'])):
                letter['senderDate']=letter['senderDate'][1:-1]
                senderDate.set('cert','medium')
                print ("Info: Added @cert for <date> in line ",table.line_num)
            senderDate.set('when', str(letter['senderDate']))
        else:
            print (bcolors.WARNING,"Warning: Couldn't set <date> for <correspAction> in line",table.line_num,"(no ISO format)",bcolors.ENDC)

        if letter['addressee']:
            addressee = SubElement(entry, 'correspAction')
            addressee.set('type', 'received')
            addresseeName = SubElement(addressee, 'persName')
            if letter['addressee'].startswith('[') and letter['addressee'].endswith(']'):
                addresseeName.set('evidence', 'conjecture')
                letter['addressee']=letter['addressee'][1:-1]
                print ("Info: Added @evidence for <persName> in line ",table.line_num)
            addresseeName.text = letter['addressee']
            if str(letter['addresseeID']):
                addresseeName.set(
                    'ref', 'http://d-nb.info/gnd/' + str(letter['addresseeID']))
        if 'addresseePlace' in table.fieldnames:
            createPlace('addresseePlace')

# generate empty body
text = SubElement(root, 'text')
body = SubElement(text, 'body')
p = SubElement(body, 'p')

# save cmi to file
tree = ElementTree(root)
tree.write(os.path.splitext(os.path.basename(fileName))[
           0] + '.xml', encoding="utf-8", xml_declaration=True, method="xml")
