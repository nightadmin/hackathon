from bs4 import BeautifulSoup
import requests
def soup(request):
    req = request
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"}
    url = f'https://www.google.com/search?q={req}&tbm=shop&sclient=products-cc'
    html = requests.get(url, headers=headers)
    f = open('index.html', 'w', encoding="utf-8")
    f.write(html.text)
    f.close()
    soup = BeautifulSoup(html.text, "html.parser")
    divs = soup.select("div > div > div > div > div > div > div > a > div > div > img")
    
    # divs = divs[5:10:]
    # print(*divs, sep="\n"*3)
    imgs = []
    for div in divs:
        # img = div.select("div > div > div > div > div > div > div > a > div > div > img")
        # imgs.append(img[0]["src"])
        print(div, end="\n"*3)
    
    print(imgs)
print(soup('Ёлка'))
