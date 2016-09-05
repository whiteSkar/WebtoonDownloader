from html.parser import HTMLParser

import os
import requests


webtoon_title = ""
imgs_to_dl = []


class NaverWebtoonParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        global imgs_to_dl

        if (tag == "img"):
            if len(attrs) > 2 and len(attrs[0]) > 0 and attrs[0][0] == 'src' and attrs[2][0] == 'alt' and attrs[2][1] == 'comic content':
                imgs_to_dl.append(attrs[0][1])

    def handle_data(self, data):
        global webtoon_title
        
        # Yay there is only one tag that starts with h3!
        if self.get_starttag_text() == "<h3>" and data.strip():
            webtoon_title = data


webtoon_id = 183559
start_id = 296

webtoon_ep_url = 'http://comic.naver.com/webtoon/detail.nhn?titleId={}&no={}&weekday=mon'.format(webtoon_id, start_id)

ep_main_page_r = requests.get(webtoon_ep_url)
if ep_main_page_r.status_code != 200:
    print("Get request for episode main page failed")
    exit()

parser = NaverWebtoonParser()
parser.feed(ep_main_page_r.text)

print("Images to download are:")
#for img_url in imgs_to_dl:
#   print(img_url)

headers = {'referer': 'http://comic.naver.com/webtoon/detail.nhn?titleId=183559&no=82'}

# start_id for sorting purposes
folder_path = ('%04d_' % (start_id,)) + webtoon_title
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

print(webtoon_title)
print(folder_path)
for i in range(len(imgs_to_dl)):
    r = requests.get(imgs_to_dl[i], headers=headers)
    if r.status_code != 200:
        print("Get request failed")
    
    img_file_name = '%03d.jpg' % (i,)
    with open(folder_path + '/' + img_file_name, 'wb') as outfile:
        outfile.write(r.content)

