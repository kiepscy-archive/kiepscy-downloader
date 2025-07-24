#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import re
import time
import hashlib
import requests
from xml.etree import ElementTree as et
from collections import OrderedDict

MY_USERNAME = "KiepscyArchive"
MY_PASSWORD = "KiepscyArchive_0078224371"
BASE_URL = "https://chomikuj.pl/KiepscyArchive/mp4/"
FOLDER_PASSWORD = "KiepscyArchive_0078224371"

class Chomyk:
    def __init__(self, username, password):
        self.username = username
        self.password = hashlib.md5(password.encode("utf-8")).hexdigest()
        self.token = ''
        self.hamsterId = 0
        self.download_links = []
        self.login()

    def postData(self, postVars):
        url = "http://box.chomikuj.pl/services/ChomikBoxService.svc"
        body = postVars.get("body")
        headers = {
            "SOAPAction": postVars.get("SOAPAction"),
            "Content-Encoding": "identity",
            "Content-Type": "text/xml;charset=utf-8",
            "Content-Length": str(len(body)),
            "Connection": "Keep-Alive",
            "Accept-Encoding": "identity",
            "Accept-Language": "pl-PL,en,*",
            "User-Agent": "Mozilla/5.0",
            "Host": "box.chomikuj.pl",
        }

        response = requests.post(url, data=body, headers=headers)
        self.parseResponse(response.content)

    def login(self):
        rootParams = {
            "xmlns:s": "http://schemas.xmlsoap.org/soap/envelope/",
            "s:encodingStyle": "http://schemas.xmlsoap.org/soap/encoding/"
        }
        root = et.Element('s:Envelope', rootParams)
        body = et.SubElement(root, "s:Body")
        auth = et.SubElement(body, "Auth", {"xmlns": "http://chomikuj.pl/"})
        authSubtree = OrderedDict([
            ("name", self.username),
            ("passHash", self.password),
            ("ver", "4"),
            ("client", OrderedDict([
                ("name", "chomikbox"),
                ("version", "2.0.5"),
            ]))
        ])
        self.add_items(auth, authSubtree)
        xmlDoc = """<?xml version="1.0" encoding="UTF-8"?>""" + et.tostring(root, encoding='unicode', method='xml')
        self.postData({
            "body": xmlDoc,
            "SOAPAction": "http://chomikuj.pl/IChomikBoxService/Auth"
        })

    def add_items(self, root, items):
        if isinstance(items, OrderedDict):
            for name, text in items.items():
                sub = et.SubElement(root, name)
                if isinstance(text, str):
                    sub.text = text
                elif isinstance(text, list) or isinstance(text, OrderedDict):
                    self.add_items(sub, text)
        elif isinstance(items, list):
            for name, text in items:
                sub = et.SubElement(root, name)
                if isinstance(text, str):
                    sub.text = text
                elif isinstance(text, list):
                    self.add_items(sub, text)

    def dl(self, url):
        fileUrl = re.search('[http|https]://chomikuj.pl(.*)', url).group(1)
        rootParams = {
            "xmlns:s": "http://schemas.xmlsoap.org/soap/envelope/",
            "s:encodingStyle": "http://schemas.xmlsoap.org/soap/encoding/"
        }
        root = et.Element('s:Envelope', rootParams)
        body = et.SubElement(root, "s:Body")
        download = et.SubElement(body, "Download", {"xmlns": "http://chomikuj.pl/"})
        downloadSubtree = OrderedDict([
            ("token", self.token),
            ("sequence", [("stamp", "123456789"), ("part", "0"), ("count", "1")]),
            ("disposition", "download"),
            ("list", [("DownloadReqEntry", [("id", fileUrl), ("password", FOLDER_PASSWORD)])])
        ])
        self.add_items(download, downloadSubtree)
        xmlDoc = """<?xml version="1.0" encoding="UTF-8"?>""" + et.tostring(root, encoding='unicode', method='xml')
        self.postData({
            "body": xmlDoc,
            "SOAPAction": "http://chomikuj.pl/IChomikBoxService/Download"
        })

    def parseResponse(self, resp):
        respTree = et.fromstring(resp)
        for dts in respTree.findall(".//{http://chomikuj.pl/}DownloadResult/{http://chomikuj.pl}status"):
            if dts.text.upper() == "OK":
                dlfiles = respTree.findall(".//{http://chomikuj.pl/}files/{http://chomikuj.pl/}FileEntry")
                for dlfile in dlfiles:
                    url = dlfile.find('{http://chomikuj.pl/}url')
                    name = dlfile.find('{http://chomikuj.pl/}name').text
                    if url is not None and url.text:
                        self.download_links.append({
                            "name": name,
                            "url": url.text
                        })

def printUsage():
    print('Użycie: chomyk.py -- działa interaktywnie.')
    sys.exit(2)

def main():
    username = MY_USERNAME
    password = MY_PASSWORD
    COMMANDS = {
        "S00": [ "000.mp4", "589.mp4" ],
        "S01": (0, 145),
        "S02": (146, 154),
        "S03": (155, 171),
        "S04": (172, 202),
        "S05": (203, 244),
        "S06": (245, 265),
        "S07": (266, 282),
        "S08": (283, 297),
        "S09": (298, 307),
        "S10": (308, 322),
        "S11": (323, 337),
        "S12": (338, 352),
        "S13": (353, 365),
        "S14": (366, 379),
        "S15": (380, 392),
        "S16": (393, 405),
        "S17": (406, 418),
        "S18": (419, 431),
        "S19": (432, 444),
        "S20": (445, 456),
        "S21": (457, 468),
        "S22": (469, 480),
        "S23": (481, 492),
        "S24": (493, 504),
        "S25": (505, 516),
        "S26": (517, 528),
        "S27": (529, 540),
        "S28": (541, 552),
        "S29": (553, 564),
        "S30": (565, 576),
        "S31": (577, 588),
    }

    while True:
        file_number = input("Podaj numer odcinka lub sezonu (np. S01 lub 123): ").strip().upper()
        files_to_download = []

        if file_number in COMMANDS:
            value = COMMANDS[file_number]
            if isinstance(value, tuple):
                files_to_download = [f"{i:03}.mp4" for i in range(value[0], value[1] + 1)]
            else:
                files_to_download = value
        elif file_number == "ALL":
            files_to_download = [f"{i:03}.mp4" for i in range(0, 590)]
        elif file_number.isdigit() and 0 <= int(file_number) <= 589:
            files_to_download = [f"{int(file_number):03}.mp4"]
        else:
            print("Niepoprawny numer.")
            continue

        if files_to_download:
            break

    ch = Chomyk(username, password)
    for filename in files_to_download:
        ch.dl(BASE_URL + filename)

    print("\n🔗 Gotowe linki do pobrania:\n")
    for file in ch.download_links:
        print(f"{file['name']}: {file['url']}")

if __name__ == "__main__":
    main()
