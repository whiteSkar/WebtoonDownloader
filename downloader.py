import requests

url = 'http://imgcomic.naver.net/webtoon/183559/82/20120203183452_IMAG01_1.jpg'
headers = {'referer': 'http://comic.naver.com/webtoon/detail.nhn?titleId=183559&no=82&weekday=mon'}


r = requests.get(url, headers=headers)

with open('test.jpg', 'wb') as outfile:
    outfile.write(r.content)

if r.status_code != 200:
    print("Get request failed")
    exit()

with open('test.jpg', 'wb') as out_file:
    out_file.write(r.content)
