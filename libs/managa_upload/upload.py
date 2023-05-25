import json

from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from urllib import request
from subprocess import CREATE_NO_WINDOW

import asyncio
import glob

service = ChromeService(ChromeDriverManager().install())
service.creationflags = CREATE_NO_WINDOW

AUTO_TRANSLATE = False


def add_cookies(driver, _cookies):
    for ck in _cookies:
        driver.add_cookie(ck)


def get_cookies_from_json(filename, allowed=None, exceptions=()):
    _cookies = json.load(open(filename, "r"))

    cookies = [{"name": el["name"], "value": el["value"]} for el in _cookies if el["name"] not in exceptions]
    if allowed:
        cookies = [e for e in cookies if e["name"] in allowed]
    return cookies



def login_driver(main_url, url, cookies):
    driver = webdriver.Chrome(service=service)
    driver.get(main_url)
    add_cookies(driver, cookies)
    sleep(1)
    driver.get(url, )
    sleep(1)
    return driver


def get_chapters(folder, start=0, end=1e9):
    chapters = []
    add_zips = []
    files = glob.glob(folder + "/*.zip", )
    files.sort(key=lambda s: s.replace("v", "!"))
    last_volume = 1
    for f_zip in files:
        filename = get_filename(f_zip)[:-4]

        if filename[0] == "v":
            volume = filename.split(" ", 1)[0][1:]
            last_volume = volume
            if "_" in filename:
                ch_num = filename.split(" ", 2)[1][1:-1]
                name = filename.split("_ ", 1)[1]

            else:
                ch_num = filename.split(" ", 1)[1][1:]
                name = ""
        else:
            volume = last_volume
            if "_" in filename:
                ch_num = filename.split(" ", 2)[0][1:-1]
                name = filename.split("_ ", 1)[1]
            else:
                ch_num = filename[1:]
                name = ""
        d = {
            "v": format_num(volume),
            "c": format_num(ch_num),
            "name": name.replace("_", '"'),
            "file": f_zip
        }
        print(d)

        if start <= float(ch_num) <= end:
            chapters.append(d)
    if AUTO_TRANSLATE:
        text = "\n".join([ch["name"] for ch in chapters])
        tr_text = translate(text)
        print("tr_text", tr_text)
        for i in range(len(chapters)):
            chapters[i]["name"] = tr_text[i]

    return chapters


def get_filename(path):
    return path.replace("\\", "/").rsplit("/", 1)[1]


def translate(text):
    from manga_image_translator.manga_translator import translators
    translate = translators.google.GoogleTranslator()
    loop = asyncio.new_event_loop()
    res = translate.translate("auto", "RUS", [text])
    res = loop.run_until_complete(res)
    print(res)
    loop.close()
    return res

def format_num(st):
    return str(float(st)).rstrip("0").rstrip(".")

clear_js_script = """
var elements = document.getElementsByTagName("input");
for (var ii=0; ii < elements.length; ii++) {
  if (elements[ii].type == "text") {
    elements[ii].value = "";
  }
}
"""
