#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import getopt
import hashlib
import requests
import os
import time
import threading
import re

MY_USERNAME = "KiepscyArchive"
MY_PASSWORD = "KiepscyArchive_0078224371"
BASE_URL = "https://chomikuj.pl/KiepscyArchive/mp4/"
FOLDER_PASSWORD = "KiepscyArchive_0078224371"

from xml.etree import ElementTree as et
from collections import OrderedDict

class Item(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.id = 0
        self.AgreementInfo = 'own'
        self.realId = 0
        self.name = ''
        self.url = ''
        self.num = 1
        self.status = 'open'
        self.directory = ""
        self.progress = None
        
    def getProgress(self):
        if self.progress is None:
            return "{:>2s}. {: <20s} : {}".format(str(self.num), self.name[:20], "Oczekuje...",)
        else:
            return self.progress
            
    def run(self):
        self.status = 'inprogress'
        path = self.directory+'/'+self.name
        try:
            file_size = os.path.getsize(path)
        except:
            file_size = 0

        r = requests.get(self.url, stream=True, verify=False, allow_redirects=True)
        total_length = int(r.headers.get('content-length'))
        file_attr = 'wb'

        if total_length > file_size and file_size > 0:
            file_attr = 'ab'
            resume_header = {'Range': 'bytes=%d-' % file_size}
            r = requests.get(self.url, headers=resume_header,  stream=True, verify=False, allow_redirects=True)

        if file_size < total_length:
            with open(path, file_attr) as fd:
                dl_size = file_size
                for chunk in r.iter_content(chunk_size=128):
                    dl_size += len(chunk)
                    progress = dl_size * 100. / total_length
                    self.progress = "{:>2s}. {: <20s} {: >10d}KB {: >3d}% [{: <25s}]".format(
                        str(self.num), self.name[:20], int(dl_size/(1024)),int(progress),"#"*int(progress/4))
                    fd.write(chunk)
            self.status = 'done'
        elif file_size == total_length:
            self.progress = "{:>2s}. {: <20s} : {}".format(str(self.num), self.name[:20], "Plik istnieje na dysku")
            self.status = 'done'
            
class Chomyk:

    def __init__(self, username, password, maxThreads, directory):
        self.isLogged = True
        self.lastLoginTime = 0
        self.hamsterId = 0
        self.token = ''
        self.items = 0
        self.threads = []
        self.accBalance = None
        self.maxThreads = int(maxThreads)
        self.directory = directory
        self.threadsChecker = None
        self.totalItems = 0
        self.username = username
        self.password = hashlib.md5(password.encode("utf-8")).hexdigest()
        self.checkThreads()
        self.login()
        self.download_links = []
        
    def cls(self):
        os.system('cls' if os.name=='nt' else 'clear')

    def printline(self, line, text):
        # sys.stdout.write("\x1b7\x1b[%d;%df%s\x1b8" % (line, 2, text))
        # sys.stdout.flush()
        
    def checkThreads(self):
        threadsInprogress = 0
        threadsOpen = 0
        threadsDone = 0

        for it in self.threads:
            self.printline(it.num+3, it.getProgress())
            if it.status == 'inprogress':
                threadsInprogress += 1
            if it.status == 'open':
                threadsOpen += 1
                if threadsInprogress < self.maxThreads:
                    threadsInprogress += 1
                    threadsOpen -= 1
                    it.start()
            if it.status == 'done':
                threadsDone += 1

        if threadsDone == self.totalItems and threadsDone > 0 and threadsOpen == 0:
            self.threadsChecker.cancel()
            self.cls()
            print("\r\nWszystkie pliki zostaly pobrane")
            print("\r")
        else:
            self.threadsChecker = threading.Timer(1.0, self.checkThreads)
            self.threadsChecker.start()
            
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

    def dl(self, url):
        fileUrl = re.search('[http|https]://chomikuj.pl(.*)', url).group(1)
        
        rootParams = {
            "xmlns:s": "http://schemas.xmlsoap.org/soap/envelope/",
            "s:encodingStyle": "http://schemas.xmlsoap.org/soap/encoding/"
        }

        root = et.Element('s:Envelope', rootParams)

        body = et.SubElement(root, "s:Body")
        downloadParams = {
            "xmlns": "http://chomikuj.pl/"
        }
        download = et.SubElement(body, "Download", downloadParams)
        downloadSubtree = OrderedDict([
            ("token", self.token,),
            ("sequence", [
                ("stamp", "123456789"),
                ("part", "0"),
                ("count", "1")
            ]),
            ("disposition", "download"),
            ("list",  [
                ("DownloadReqEntry", [
                    ("id", fileUrl),
                    ("password", FOLDER_PASSWORD)
                ])
            ])
        ])

        self.add_items(download, downloadSubtree)

        xmlDoc = """<?xml version="1.0" encoding="UTF-8"?>"""
        xmlDoc += et.tostring(root, encoding='unicode', method='xml')

        dts = {
            "body": xmlDoc,
            "SOAPAction": "http://chomikuj.pl/IChomikBoxService/Download"
        }
        self.postData(dts)

    def dl_step_2(self, idx, agreementInfo, cost = 0):
        rootParams = {
            "xmlns:s": "http://schemas.xmlsoap.org/soap/envelope/",
            "s:encodingStyle": "http://schemas.xmlsoap.org/soap/encoding/"
        }
        root = et.Element('s:Envelope', rootParams)

        body = et.SubElement(root, "s:Body")
        downloadParams = {
            "xmlns": "http://chomikuj.pl/"
        }
        download = et.SubElement(body, "Download", downloadParams)
        downloadSubtree = OrderedDict([
            ("token", self.token,),
            ("sequence", [
                ("stamp", "123456789"),
                ("part", "0"),
                ("count", "1")
            ]),
            ("disposition", "download"),
            ("list",  [
                ("DownloadReqEntry", [
                    ("id", idx),
                    ("agreementInfo", [
                        ("AgreementInfo", [
                            ("name", agreementInfo),
                            ("cost", cost),
                        ])
                    ])
                ])
            ])
        ])

        self.add_items(download, downloadSubtree)

        xmlDoc = """<?xml version="1.0" encoding="UTF-8"?>"""
        xmlDoc += et.tostring(root, encoding='unicode', method='xml')

        dts = {
            "body": xmlDoc,
            "SOAPAction": "http://chomikuj.pl/IChomikBoxService/Download"
        }

        self.postData(dts)

    def login(self):

        rootParams = {
            "xmlns:s": "http://schemas.xmlsoap.org/soap/envelope/",
            "s:encodingStyle": "http://schemas.xmlsoap.org/soap/encoding/"
        }
        root = et.Element('s:Envelope', rootParams)

        body = et.SubElement(root, "s:Body")
        authParams = {
            "xmlns": "http://chomikuj.pl/"
        }
        auth = et.SubElement(body, "Auth", authParams)

        authSubtree = OrderedDict([
            ("name", self.username,),
            ("passHash", self.password,),
            ("ver", "4"),
            ("client", OrderedDict([
                ("name", "chomikbox"),
                ("version", "2.0.5"),
            ]))
        ])

        self.add_items(auth, authSubtree)

        xmlDoc = """<?xml version="1.0" encoding="UTF-8"?>"""
        xmlDoc += et.tostring(root, encoding='unicode', method='xml')

        dts = {
            "body": xmlDoc,
            "SOAPAction": "http://chomikuj.pl/IChomikBoxService/Auth"
        }
        self.postData(dts)

    def add_items(self, root, items):
        if type(items) is OrderedDict:
            for name, text in items.items():
                if type(text) is str:
                    elem = et.SubElement(root, name)
                    elem.text = text
                if type(text) is list:
                    subroot = et.SubElement(root, name)
                    self.add_items(subroot, text)
        elif type(items) is list:
            for name, text in items:
                if type(text) is str:
                    elem = et.SubElement(root, name)
                    elem.text = text
                if type(text) is list:
                    subroot = et.SubElement(root, name)
                    self.add_items(subroot, text)

    def parseResponse(self, resp):
        self.printline (3, 'Maks watkow: ' + str(self.maxThreads))
        respTree = et.fromstring(resp)
        
        #Autoryzacja
        for dts in respTree.findall(".//{http://chomikuj.pl/}AuthResult/{http://chomikuj.pl}status"):
            status = dts.text
            if status.upper() == "OK":
                self.isLogged = True
                self.lastLoginTime = time.time()
                self.token = respTree.findall(".//{http://chomikuj.pl/}AuthResult/{http://chomikuj.pl}token")[0].text
                self.hamsterId = respTree.findall(".//{http://chomikuj.pl/}AuthResult/{http://chomikuj.pl}hamsterId")[0].text
                self.printline (1,"Login: OK")

            else:
                 self.isLogged = False
                 self.printline (1,"Login: " + status)

        #Pobieranie urli plikow
        accBalance = respTree.find(".//{http://chomikuj.pl/}DownloadResult/{http://chomikuj.pl}accountBalance/{http://chomikuj.pl/}transfer/{http://chomikuj.pl/}extra")
        if accBalance is not None:
            self.accBalance = accBalance.text
            
        for dts in respTree.findall(".//{http://chomikuj.pl/}DownloadResult/{http://chomikuj.pl}status"):
            status = dts.text
            if status.upper() == "OK":
                dlfiles = respTree.findall(".//{http://chomikuj.pl/}files/{http://chomikuj.pl/}FileEntry")
                for dlfile in dlfiles:
                    url = dlfile.find('{http://chomikuj.pl/}url')
                    idx = dlfile.find('{http://chomikuj.pl/}id').text
                    cost = dlfile.find('{http://chomikuj.pl/}cost')
                    if url is None or url.text is None:
                        agreementInfo = dlfile.find("{http://chomikuj.pl/}agreementInfo/{http://chomikuj.pl/}AgreementInfo/{http://chomikuj.pl/}name").text
                        costInfo = dlfile.find("{http://chomikuj.pl/}agreementInfo/{http://chomikuj.pl/}AgreementInfo/{http://chomikuj.pl/}cost")
                        
                        if costInfo.text == None:
                            cost = 0
                        else:
                            cost = costInfo.text
                        if int(self.accBalance) >= int(cost):
                            self.dl_step_2(idx, agreementInfo, cost)
                        else:
                            self.printline (2,"Blad: brak wystarczajacego limitu transferu")
                    elif url is not None and url.text:
                        name = dlfile.find('{http://chomikuj.pl/}name').text or "brak"
                        self.download_links.append({
                            "name": name,
                            "url": url.text
    })

                        
def main(argv):
    username = MY_USERNAME
    password = MY_PASSWORD
    threads = 5
    directory = os.getcwd() + "/"

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
        file_number = input("Podaj numer odcinka lub sezonu: ").strip().upper()
        files_to_download = []

        if file_number in COMMANDS:
            value = COMMANDS[file_number]
            if isinstance(value, tuple):
                start, end = value
                files_to_download = [f"{i:03}.mp4" for i in range(start, end + 1)]
            elif isinstance(value, list):
                files_to_download = value
        elif file_number == "ALL":
            max_files = 589
            files_to_download = [f"{i:03}.mp4" for i in range(0, max_files + 1)]
        else:
            if file_number.isdigit():
                num = int(file_number)
                if 0 <= num <= 589:
                    files_to_download = [f"{num:03}.mp4"]
            if not files_to_download:
                print("Błąd podczas wyszukiwania pliku")
                time.sleep(3)
                os.system('cls' if os.name == 'nt' else 'clear')
                continue  # ponownie zapytaj o numer

        if files_to_download:
            break

    if len(password) > 0 and len(username) > 0 and len(files_to_download) > 0:
        ch = Chomyk(username, password, threads, directory)
        for filename in files_to_download:
            ch.dl(BASE_URL + filename)

        # Po zalogowaniu i przetworzeniu – wypisz linki
        print("\nGotowe linki do pobrania:")
        for file_info in ch.download_links:
            print(f"{file_info['name']}: {file_info['url']}")


def printUsage():
    print ('chomyk.py --u username --p password --i <url>')
    sys.exit(2)

if __name__ == "__main__":
    main(sys.argv[1:])
