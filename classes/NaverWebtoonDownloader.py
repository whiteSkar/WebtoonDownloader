from html.parser import HTMLParser

from time import sleep

import os
import queue
import requests
import threading


# Globals
webtoon_title = ''
imgs_to_dl = []
newest_ep_id = 0


class Downloader():
    def __init__(self, webtoon_id, start_id, directory_path):
        self.log_queue = queue.Queue()
        webtoon_list_page_url = 'http://comic.naver.com/webtoon/list.nhn?titleId={}'.format(webtoon_id)

        webtoon_list_r = requests.get(webtoon_list_page_url)
        if webtoon_list_r.status_code != 200:
            self.log_queue.put('Get request for webtoon list page failed')
            exit()

        parser = ListPageParser()
        parser.feed(webtoon_list_r.text)

        self._is_closing = False
        self._is_downloading = False
        self._lock = threading.Lock()
        self._th = threading.Thread(target=self.download_eps, kwargs={'webtoon_id': webtoon_id, 'start_id': start_id, 'directory_path': directory_path})
        self._th.start()

    def download_eps(self, webtoon_id, start_id, directory_path):
        global imgs_to_dl

        with self._lock:
            self._is_downloading = True

        self.log_queue.put('Downloading webtoon from ep_id:' + str(start_id) + ' to ep_id:' + str(newest_ep_id) + ' started.')
        while start_id <= newest_ep_id and not self._is_closing: # _is_closing is shared but should be fine not to lock it
            imgs_to_dl = []
            if self.download_ep(directory_path, webtoon_id, start_id):
                self.log_queue.put('Downloading ' + webtoon_title + ' with ep_id: ' + str(start_id) + ' complete.')
            else:
                self.log_queue.put('Episode #' + str(start_id) + ' doesn\'t exist. Skipping.')

            start_id += 1
            sleep(1)

        self.log_queue.put('Downloading the webtoon complete.')
        
        with self._lock:
            self._is_downloading = False

    def download_ep(self, directory_path, webtoon_id, ep_id):
        webtoon_ep_url = 'http://comic.naver.com/webtoon/detail.nhn?titleId={}&no={}'.format(webtoon_id, ep_id)

        ep_main_page_r = requests.get(webtoon_ep_url)
        if ep_main_page_r.status_code != 200:
            self.log_queue.put('Get request for episode main page failed')
            exit()

        parser = EpParser()
        parser.feed(ep_main_page_r.text)

        if len(imgs_to_dl) == 0:
            self.log_queue.put('There are no images to download. Probably this ep is not released yet.')
            return False

        #self.log_queue.put('Images to download are:')
        #for img_url in imgs_to_dl:
        #    self.log_queue.put(img_url)

        headers = {'referer': 'http://comic.naver.com/webtoon/detail.nhn?titleId={}&no={}'.format(webtoon_id, ep_id)}

        # ep_id for sorting purposes
        folder_path = directory_path + ('%04d_' % (ep_id,)) + webtoon_title
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        for i in range(len(imgs_to_dl)):
            r = requests.get(imgs_to_dl[i], headers=headers)
            if r.status_code != 200:
                self.log_queue.put('Get request failed')
            
            img_file_name = '%03d.jpg' % (i,)
            with open(folder_path + '/' + img_file_name, 'wb') as outfile:
                outfile.write(r.content)

        return True
    
    def get_new_logs(self):
        logs = []
        while not self.log_queue.empty():
            try:
                log = self.log_queue.get(block=False)
                logs.append(log)
            except queue.Empty():
                return logs
        return logs

    # Not bullet proof but enough
    def is_downloading(self):
        with self._lock:
            return self._is_downloading

    def destroy(self):
        self.log_queue.put('Closing Downloader.')
        self._is_closing = True
        self._th.join()
        self.log_queue.put('Downloader closed.')


class EpParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        global imgs_to_dl

        if tag == 'img':
            if len(attrs) > 2 and len(attrs[0]) > 0 and attrs[0][0] == 'src' and len(attrs[2]) > 1 and attrs[2][0] == 'alt' and attrs[2][1] == 'comic content':
                imgs_to_dl.append(attrs[0][1])
    
    def handle_data(self, data):
        global webtoon_title
        
        # Yay there is only one tag that starts with h3!
        if self.get_starttag_text() == '<h3>' and data.strip():
            webtoon_title = data


class ListPageParser(HTMLParser):
    '''
    Find the newest episode identifier.
    '''
    def handle_starttag(self, tag, attrs):
        global newest_ep_id
        
        if newest_ep_id == 0 and tag == 'td':
            if len(attrs) == 2 and len(attrs[0]) > 0 and attrs[0][0] == 'href': # len(attrs) == 2 is hacky but easy way to bypass '첫회보기' link
                ep_no_identifier = 'no='
                pos_ep_no = attrs[0][1].find(ep_no_identifier)
                if pos_ep_no >= 0:
                    pos_ep_no_end = attrs[0][1].find('&', pos_ep_no)
                    if pos_ep_no_end == -1:
                        pos_ep_no_end = len(attrs[0][1])
                    newest_ep_id = int(attrs[0][1][pos_ep_no + len(ep_no_identifier) : pos_ep_no_end]) # You know.. Not gonna error check

