import torch
import gc
import sys
from time import sleep
from manga_image_translator.manga_translator.args import parser
import logging
import os.path
import glob
import asyncio
from manga_image_translator.manga_translator import MangaTranslator, set_main_logger, translators
from manga_image_translator.manga_translator.utils import get_logger, set_log_level, init_logging, init_new_logging
import shutil

torch.cuda.empty_cache()
gc.collect()

BASE_PATH = os.getcwd()
# выключить комп после завершения
SHUTDOWN = False
# Удалить картинки не находящиеся в оргинальной папке
DEL_NOT_IN_ORIGINAL = True
IGNOR_DEL = {"000.png"}
# зазиповать каждую папку
TO_ZIP = False
# добавить в начала собственую картнку под 000.png
HEADER = "src/header.png"
# выводить в отдельные папки этапы создания файла
DEBUG = False
# создавать файлы для редактуры в фотошопе
CREATE_VECTOR_IMAGE = True
TRANSLATE_VECTOR_IMAGE = True
BASE64_VECTOR_IMAGE = True
SAVE_CLEANED_IMAGE = True
FONT_PATH = os.path.join(BASE_PATH, "fonts/Anime Ace.ttf")
TRANSLATED_PATH = os.path.join(BASE_PATH, "translated")
# переводить на язык
LANG = "RUS"
# rapid,google,youdao,baidu,deepl,papago,gpt3,gpt3.5,none,original,offline,nllb,nllb_big,sugoi,jparacrawl,jparacrawl_big,m2m100,m2m100_big
TRANSLATOR = "google"
# TRANSLATOR = "papago"
# задержка перед запуском (сек)
sleep_sec = 0

_rootLogPassImgs = logging.getLogger("pass_imgs")
init_new_logging(_rootLogPassImgs, level=logging.DEBUG, fileName="passImgs")

# from deep_translator import GoogleTranslator
if __name__ == '__main__' and 0:
    translate = translators.google.GoogleTranslator()
    loop = asyncio.new_event_loop()
    text = "\"so you're hugging again?\\nThis is seriously your final chance, senpai.\\nTell me that \\\"you like me please.\\nThat's the only thing stopping you Prou having your cute kouhai as your girlfriend.\"".replace(
        "\\n", "\n")
    res = translate.translate("auto", "RUS", [text])
    res = loop.run_until_complete(res)
    print(res)
    loop.close()
    exit()

init_logging()
set_log_level(level=logging.DEBUG)
logger = get_logger("batch")
set_main_logger(logger)


def get_filename(path):
    return path.replace("\\", "/").rsplit("/", 1)[1]


def get_filenames(paths):
    return [get_filename(p) for p in paths]


def get_images(path):
    return glob.glob(path + "/*.jpg") + glob.glob(path + "/*.png")


# -i test_manga.jpg --dest t_test_manga.jpg --inpainter default  -v  -l RUS --inpainting-size 512 --use-cuda --translator gpt3.5

def get_default_args():
    args_dict = {"target_lang": LANG, "translator": TRANSLATOR, "verbose": True, "inpainter": "default",
                 "inpainting_size": 512, "use_cuda": True, "font_path": FONT_PATH,
                 "bold_border": 5, "del_word_wrap": True,
                 "create_vector_file": CREATE_VECTOR_IMAGE, "translate_vector_file": TRANSLATE_VECTOR_IMAGE,
                 "base64_vector_file": BASE64_VECTOR_IMAGE, "cleaned_image_path": None}
    return args_dict


async def translate_chapters(path_chapters, result_language=LANG, translate_with=TRANSLATOR, group="", use_cuda=True,
                             one_image=False):
    pass_imgs = 0
    args_dict = get_default_args()
    args_dict["target_lang"] = result_language
    args_dict["translator"] = translate_with

    if type(path_chapters) is str:
        path_chapters = [path_chapters]

    # args_dict["use_cuda"] = False
    # translator = MangaTranslator(dict(args_dict))
    args_dict["use_cuda"] = use_cuda
    print(f"use_cuda: {use_cuda} group: {group}")
    translator_cuda = MangaTranslator(args_dict)
    for path_chapter in path_chapters:
        path_chapter = path_chapter.replace("\\", "/")
        chapter = path_chapter.rsplit("/", 1)[1]
        res_path = os.path.join(TRANSLATED_PATH, group, chapter)
        if not os.path.exists(res_path):
            os.makedirs(res_path)
        if HEADER:
            shutil.copy(HEADER, os.path.join(res_path, "000.png"))
        print("path_chapter", path_chapter, res_path)
        images_path = get_images(path_chapter)
        i = 0
        if DEL_NOT_IN_ORIGINAL:
            imgs_in_res = set(get_filenames(get_images(res_path)))
            outsection_imgs = (set(get_filenames(images_path)) ^ imgs_in_res ^ IGNOR_DEL) & imgs_in_res
            print("outsection_imgs for del", outsection_imgs)
            for img_name in outsection_imgs:
                os.remove(os.path.join(res_path, img_name))
        for image_path in images_path:
            i += 1
            res_path_img = os.path.join(res_path, get_filename(image_path))
            if os.path.exists(res_path_img):
                print("image is exist", res_path_img)
                continue

            print("chapter progress:", i / len(images_path) * 100, f"%  ({i}/{len(images_path)})")
            # args_dict["use_cuda"] = True
            await _translate_image(args_dict, translator_cuda, image_path, res_path, try_exception=DEBUG)
            if one_image:
                return
        if TO_ZIP:
            zip_file = os.path.join(os.path.join(BASE_PATH, "translated", group), "zip", chapter)
            print("zip_file", zip_file)
            if not os.path.exists(zip_file + ".zip"):
                print("ZIP", zip_file, res_path)
                shutil.make_archive(zip_file, 'zip', res_path)
    return pass_imgs


async def _translate_image(args_dict, translator_cuda, image_path, res_path, try_exception=False,
                           group=None, path_chapter=None):
    args_dict["result"] = 0
    img_name = get_filename(image_path)
    res_path_img = os.path.join(res_path, img_name)
    print("image_path", image_path, res_path_img)
    args_dict["original_image_path"] = image_path
    args_dict["result_image_path"] = res_path_img
    if DEBUG:
        args_dict["cash_folder"] = res_path_img + "_"
        if not os.path.exists(args_dict["cash_folder"]):
            os.makedirs(args_dict["cash_folder"])
        args_dict["save_text_file"] = args_dict["cash_folder"]
    if SAVE_CLEANED_IMAGE:
        clean_path = os.path.join(res_path, "cleaned")
        if not os.path.exists(clean_path):
            os.makedirs(clean_path)
        args_dict["cleaned_image_path"] = os.path.join(clean_path, "cleaned_" + img_name)

    if args_dict["create_vector_file"]:
        args_dict["vector_file"] = res_path_img + ".svg"
    # await translator_cuda.translate_path(image_path, res_path_img, args_dict)
    if try_exception:
        try:
            await translator_cuda.translate_path(image_path, res_path_img, args_dict)
        except Exception as exc:
            logger.warning("translate_path Exception " + str(exc))
            if "cuda" in str(exc).lower():
                print("Run with not CUDA")
                os.system(__file__ + f' --dest "{group}" -i "{path_chapter}"')  # not use cuda
    else:
        await translator_cuda.translate_path(image_path, res_path_img, args_dict)
    print("translator_cuda.ctx.result", translator_cuda.ctx.result)
    if translator_cuda.ctx.result == 0:
        args_dict["pass_imgs"] = args_dict.get("pass_imgs", 0) + 1
        _rootLogPassImgs.warning(f"pass_img;{args_dict['pass_imgs']};{res_path_img};")


async def translate_image(image_path, res_path=None, use_cuda=True):
    if res_path is None:
        res_path = os.path.join(TRANSLATED_PATH, "images")
    args_dict = get_default_args()
    args_dict["use_cuda"] = use_cuda
    translator_cuda = MangaTranslator(args_dict)
    await _translate_image(args_dict, translator_cuda, image_path, res_path, try_exception=DEBUG)


async def load_dir(path):
    path = path.replace("\\", "/")
    group = path.rstrip("/").rsplit("/", 1)[1]
    _rootLogPassImgs.info(f"Load path: {path}")
    print("group", group)
    for root, subdirs, files in os.walk(path):
        chapters = [os.path.join(root, folder) for folder in subdirs]
        if chapters:
            print(chapters)
            c = await translate_chapters(chapters, group=group)
            print(path)
            print("Пропущено изображений", c)
            _rootLogPassImgs.warning(f"Pass images: {c} : {path}")


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    args = parser.parse_args()
    print(sys.argv)
    print(args)
    if args.input:
        loop.run_until_complete(
            translate_chapters([args.input], use_cuda=args.use_cuda, group=args.dest, one_image=True))
    else:
        sleep(sleep_sec)
        loop.run_until_complete(
            translate_image("gallery-dl\mango images\onepunch_man_172\onepunch_man_172_5.jpg"))
        # loop.run_until_complete(
        #     translate_chapters([r"gallery-dl\mango images\onepunch_man_172"]))
        if SHUTDOWN:
            os.system('shutdown -s')
