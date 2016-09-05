from html.parser import HTMLParser

import os
import requests


# Globals
webtoon_title = ""
imgs_to_dl = []


# Classes
class NaverWebtoonParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        global imgs_to_dl

        if (tag == "img"):
            if len(attrs) > 2 and len(attrs[0]) > 0 and attrs[0][0] == 'src' and len(attrs[2]) > 1 and attrs[2][0] == 'alt' and attrs[2][1] == 'comic content':
                imgs_to_dl.append(attrs[0][1])

    def handle_data(self, data):
        global webtoon_title
        
        # Yay there is only one tag that starts with h3!
        if self.get_starttag_text() == "<h3>" and data.strip():
            webtoon_title = data


# Functions
def download_ep(directory_path, webtoon_id, ep_id):
    webtoon_ep_url = 'http://comic.naver.com/webtoon/detail.nhn?titleId={}&no={}'.format(webtoon_id, ep_id)

    ep_main_page_r = requests.get(webtoon_ep_url)
    if ep_main_page_r.status_code != 200:
        print("Get request for episode main page failed")
        exit()

    parser = NaverWebtoonParser()
    parser.feed(ep_main_page_r.text)

    if len(imgs_to_dl) == 0:
        print("There are no images to download. Probably this ep is not released yet.")
        return False

    #print("Images to download are:")
    #for img_url in imgs_to_dl:
    #    print(img_url)

    headers = {'referer': 'http://comic.naver.com/webtoon/detail.nhn?titleId={}&no={}'.format(webtoon_id, ep_id)}

    # ep_id for sorting purposes
    folder_path = directory_path + ('%04d_' % (ep_id,)) + webtoon_title
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    for i in range(len(imgs_to_dl)):
        r = requests.get(imgs_to_dl[i], headers=headers)
        if r.status_code != 200:
            print("Get request failed")
        
        img_file_name = '%03d.jpg' % (i,)
        with open(folder_path + '/' + img_file_name, 'wb') as outfile:
            outfile.write(r.content)

    return True


directory_path = input('Input EXISTING directory path WITH SLASH AT THE BACK where you want to download the webtoon')
webtoon_id = input('Input the webtoon id (eg. 183559): ')
start_id = input('Input the episode id of the first episode you want to download (eg. 1): ')

# I'm too lazy to do error checking! I'm the only user!
webtoon_id = int(webtoon_id)
start_id = int(start_id)

while download_ep(directory_path, webtoon_id, start_id):
    print("Downloading " + webtoon_title + "complete.")
    imgs_to_dl = []
    start_id += 1

print("Downloading the webtoon complete.")
