import os
import sys




def download(url):
    os.system(f'gallery-dl -o "lang=en" {url}')


if __name__ == '__main__':
    url = "https://mangadex.org/title/8636c471-37ac-477e-815e-af0cfd724b91/5-more-chances"
    url = "https://mangadex.org/title/5f303853-4bde-4f69-a92f-0ed80672c4e4"
    url = r"https://mangadex.org/title/5c85ce34-c9de-4e28-85e5-13933fa7d5d7/return-survival"
    url = r"https://mangadex.org/title/4080db42-038f-4f6b-a8ab-0ddc71183e1a/kawaii-kouhai-ni-iwasaretai"
    url = r"https://mangadex.org/title/3ccb3bb4-43fb-4384-a235-7baaf1bdb3e6/ryuunen-shita-senpai-to-moto-kouhai-no-hanashi"
    download(url)
    url = r"https://mangadex.org/title/305c5759-4e7e-43d3-9d99-5360c6d9d6e1/houkago-no-goumon-shoujo"
    download(url)
