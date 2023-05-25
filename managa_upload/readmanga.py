from upload import *
import json
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from time import sleep

AUTO_START = True
url = "https://readmanga.live/internal/upload/index/24135"
path = r"D:\PythonProjects\MangoEditer\translated\Kawaii Kouhai ni Iwasaretai\zip"
_chapters = get_chapters(path, 11, 100)

translate_group = "Niplix"
main_url = "https://readmanga.live/"
# allowed = ('remember_me',)
cookies = get_cookies_from_json("readmanga-cookies.json", )
print("cookies", cookies)

add_tr = """
function getElementByXPath(xpath) {return new XPathEvaluator().createExpression(xpath).evaluate(document, XPathResult.FIRST_ORDERED_NODE_TYPE).singleNodeValue}
e = getElementByXPath('//*[@id="tab-SERIES"]/div[1]/div[1]/select')
e.innerHTML += '<option value="115167:4" selected="selected">Niplix</option>'
"""

def upload_title(url, _chapters):
    print("get_chrp_text", url)
    driver = login_driver(main_url, url, cookies)
    step = 10
    for j in range(0, len(_chapters), step):
        chapters = _chapters[j:j + step]
        driver.refresh()
        sleep(0.5)
        # groups.
        driver.execute_script(add_tr)
        groups = driver.find_element(By.CLASS_NAME, "selectize-input")
        groups = groups.find_element(By.TAG_NAME, "input")
        print(groups)
        groups.send_keys(translate_group)
        uploads = driver.find_elements(By.CLASS_NAME, "upload-chapter-row")
        print(uploads)
        last_form = None
        for i in range(len(chapters)):
            volume, chapter, name = chapters[i]['v'], chapters[i]['c'], chapters[i].get('name', "")
            filepath = chapters[i]['file']
            print(volume, chapter, filepath)
            last_form = form = uploads[i]
            form.find_element(By.NAME, "vol").send_keys(Keys.BACKSPACE * 6 + str(volume))
            form.find_element(By.NAME, "formattedNum").send_keys(Keys.BACKSPACE * 6 + str(chapter))
            if name:
                form.find_element(By.NAME, "title").send_keys(str(name))
            form.find_element(By.NAME, "mangaFile").send_keys(filepath)
        if AUTO_START:
            driver.find_element(By.ID, "startButton").click()
        else:
            input("Press enter for continue")
        while True:
            sleep(0.5)
            mangaDone = last_form.find_element(By.CLASS_NAME, "mangaDone")
            uploadError = last_form.find_element(By.CLASS_NAME, "upload-error")
            if "hide" not in mangaDone.get_attribute("class") or "hide" not in uploadError.get_attribute("class"):
                print("mangaDone", j)
                sleep(0.5)
                break

    input("For close press ENTER")
    driver.close()


if __name__ == '__main__':
    # selenium 4

    upload_title(url, _chapters)
    # step = 10
    # for i in range(0, len(chapters), step):
    #     upload_title(url, chapters[i:i + step])
