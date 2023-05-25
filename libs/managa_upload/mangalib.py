from upload import *
import json
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from time import sleep

AUTO_START = False

cookies_exceptions = {'XSRF-TOKEN', '_gid', '_ym_isad'}
cookies = get_cookies_from_json("mangalib-cookies.json", exceptions=cookies_exceptions)
print("cookies", cookies)


def upload_title(url, chapters):
    print("get_chrp_text", url)
    driver = login_driver("https://mangalib.me", url, cookies)
    filepath = chapters[0]
    add_ch_btn = driver.find_element(By.CLASS_NAME, "upload-footer__btn-add")

    el_section = driver.find_element(By.CLASS_NAME, "tabs__list").find_elements(By.TAG_NAME, "li")[1]
    el_section.click()
    sleep(0.1)
    for i in range(len(chapters) - 1):
        add_ch_btn.click()
    sleep(0.1)
    # for el in driver.find_elements(By.NAME, "number"):
    #     el.send_keys(str(111))
    # sleep(0.1)
    # driver.execute_script(clear_js_script)
    # sleep(0.1)
    _uploads_form = driver.find_element(By.CLASS_NAME, "upload-chapters-form")
    uploads_form = _uploads_form.find_elements(By.TAG_NAME, "form")

    for i in range(len(chapters)):
        volume, chapter, name = chapters[i]['v'], chapters[i]['c'], chapters[i].get('name', "")
        filepath = chapters[i]['file']
        print(volume, chapter, filepath)
        form = uploads_form[i]
        # form.find_element(By.NAME, "volume").clear()
        form.find_element(By.NAME, "volume").send_keys(Keys.BACKSPACE * 6 + str(volume))
        form.find_element(By.NAME, "volume").send_keys(Keys.BACKSPACE * 6 + str(volume))
        if name:
            form.find_element(By.NAME, "name").send_keys(str(name))
        # sleep(1)

        # form.find_element(By.NAME, "number").clear()
        form.find_element(By.NAME, "number").send_keys(Keys.BACKSPACE * 6 + str(chapter))
        # sleep(1)

        file_btn = form.find_element(By.CLASS_NAME, "upload-chapter__upload-btn").find_element(By.TAG_NAME, "input")
        file_btn.send_keys(filepath)
    if AUTO_START:
        driver.find_element(By.CLASS_NAME, "upload-footer__btn-upload").click()
    # driver.find_element(By.ID, "file-submit").submit()
    # sleep(30)

    # el = driver.find_element(By.CLASS_NAME, "reader-container")
    # text = el.text
    input("For close press ENTER")
    driver.close()


if __name__ == '__main__':
    # selenium 4
    url = "https://mangalib.me/manga/kawaii-kouhai-ni-iwasaretai/add-chapter"
    path = r"D:\PythonProjects\MangoEditer\translated\Kawaii Kouhai ni Iwasaretai\zip"

    chapters = get_chapters(path, 78)
    upload_title(url, chapters)
    # for i in range(0, len(chapters), 20):
    #     upload_title(url, chapters[i:i+20])
