from html.parser import HTMLParser

from time import sleep

import os
import queue
import requests
import threading
import base64
import random

# Globals
global_episode_title = ''
global_imgs_to_dl = []
global_episode_urls = []
global_start_ep_index = 0

DOMAIN = 'https://tkor.fun'
HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
}

DEFAULT_CF_CLEARANCE = 'DEFAULT_CF_CLEARANCE'
COOKIES = {
    'cf_clearance': DEFAULT_CF_CLEARANCE,
}


class Downloader(object):
    def __init__(self, webtoon_id, start_ep_index, directory_path):
        """
        webtoon_id: an identifier. Can be a string or an int.
        directory_path: should end with /
        """
        global global_start_ep_index

        global_start_ep_index = start_ep_index

        self.log_queue = queue.Queue()
        webtoon_list_page_url = '%s/%s' % (DOMAIN, webtoon_id)

        request_params = {
            'url': webtoon_list_page_url,
            'headers': HEADERS,
        }
        if COOKIES['cf_clearance'] != DEFAULT_CF_CLEARANCE:
            request_params['cookies'] = COOKIES

        webtoon_list_r = requests.get(**request_params)
        if webtoon_list_r.status_code != 200:
            self.log_queue.put('Get request for webtoon list page failed - url: %s' % webtoon_list_page_url)
            self.log_queue.put('webtoon_list_r is: %s' % webtoon_list_r)
            return

        parser = ListPageParser()
        parser.feed(webtoon_list_r.text)

        self._is_closing = False
        self._is_downloading = False
        self._lock = threading.Lock()
        self._th = threading.Thread(target=self.download_eps, kwargs={'directory_path': directory_path})
        self._th.start()

    def download_eps(self, directory_path):
        global global_imgs_to_dl, global_episode_urls

        with self._lock:
            self._is_downloading = True

        global_episode_urls.reverse()
        self.log_queue.put('Downloading %s episodes from ep: %s to ep: %s'
                           % (len(global_episode_urls),
                              global_episode_urls[global_start_ep_index][1:-5],
                              global_episode_urls[-1][1:-5]))

        for i in range(global_start_ep_index, len(global_episode_urls)):
            episode_url = global_episode_urls[i]
            if self._is_closing:  # _is_closing is shared but should be fine not to lock it
                break

            global_imgs_to_dl = []
            try:
                if self.download_ep(directory_path, episode_url, i):
                    self.log_queue.put('Downloading ' + global_episode_title + ' complete.')
                else:
                    self.log_queue.put('Failed to download episode with url ' + episode_url + '. Skipping.')
            except ValueError as e:
                self.log_queue.put('Failed to download episode: %s\n%s' % (global_episode_title, e))
                break

            sleep(random.uniform(0.75, 1.25))

        self.log_queue.put('Downloading the webtoon complete.')

        with self._lock:
            self._is_downloading = False

    def download_ep(self, directory_path, episode_url, index):
        webtoon_ep_url = '%s%s' % (DOMAIN, episode_url)
        print('Downloading ep with url: %s' % webtoon_ep_url)

        ep_main_page_r = requests.get(webtoon_ep_url, headers=HEADERS, cookies=COOKIES)
        if ep_main_page_r.status_code != 200:
            self.log_queue.put('Get request for episode main page failed')
            raise ValueError('download_ep request failed')

        # print('ep_main_page_r.text: %s' % ep_main_page_r.text)

        parser = EpParser()
        parser.feed(ep_main_page_r.text)

        if len(global_imgs_to_dl) == 0:
            self.log_queue.put('There are no images to download. Probably this ep is not released yet.')
            return False

        # print('Images to download are: %s' % global_imgs_to_dl)

        # ep_id for sorting purposes
        folder_path = directory_path + ('%04d_' % (index,)) + global_episode_title
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        for i in range(len(global_imgs_to_dl)):
            # print('Downloading img: %s' % global_imgs_to_dl[i])
            try:
                r = requests.get(global_imgs_to_dl[i], headers=HEADERS, cookies=COOKIES)
            except requests.exceptions.ConnectionError as e:
                raise ValueError(str(e))

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
        try:
            self._th.join()
        except AttributeError as e:
            self.log_queue.put('Downloader probably was not initialized - %s' % e)
            pass
        self.log_queue.put('Downloader closed.')


class EpParser(HTMLParser):
    def handle_data(self, data):
        global global_episode_title

        # Yay there is only one tag that starts with h1!
        if self.get_starttag_text() == '<h1>' and data.strip():
            global_episode_title = data
            # print('EpParser - global_episode_title: %s' % global_episode_title)

        if 'toon_img' in data:
            data_list = data.split('\'')
            encoded_toon_image_html = data_list[1]
            toon_image_html = base64.b64decode(encoded_toon_image_html).decode(encoding='utf-8')

            parser = ToonImageParser()
            parser.feed(toon_image_html)


class ListPageParser(HTMLParser):

    def __init__(self, *, convert_charrefs=True):
        super(ListPageParser, self).__init__(convert_charrefs=convert_charrefs)
        self.last_ep_url = None

    def handle_starttag(self, tag, attrs):
        global global_episode_urls

        if tag == 'td' and len(attrs) == 5 and len(attrs[3]) > 1 and attrs[3][0] == 'data-role':
            episode_url = attrs[3][1]
            # print('ListPageParser - handlestarttag - episode_url: %s' % episode_url)
            if self.last_ep_url and self.last_ep_url == episode_url:
                # The html has two components that match these rules. So skip every duplicates
                return

            self.last_ep_url = episode_url

            # print('episode_url: %s' % episode_url)
            global_episode_urls.append(episode_url)


class ToonImageParser(HTMLParser):
    global global_imgs_to_dl

    def handle_starttag(self, tag, attrs):
        # print('tag', tag, 'attrs', attrs)
        img_url = attrs[1][1]

        # global_imgs_to_dl.append('%s%s' % (DOMAIN, img_url))
        if DOMAIN not in img_url:
            img_url = '%s%s' % (DOMAIN, img_url)

        global_imgs_to_dl.append(img_url)
        # print('EpParser - img_url: %s' % img_url)
