from html.parser import HTMLParser

from time import sleep

import os
import queue
import requests
import threading
import base64
import re

# Globals
episode_title = ''
imgs_to_dl = []
episode_urls = []
start_ep_id = None
number_of_eps_before_start = 0

DOMAIN = 'https://tkor.life'
HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
}
COOKIES = {
    'cf_clearance': 'COPYPASTEHERE',
}


class Downloader(object):
    def __init__(self, webtoon_id, start_id, directory_path):
        """
        :param webtoon_id: an identifier. Can be a string or an int.
        """
        global start_ep_id, number_of_eps_before_start

        start_ep_id = start_id
        number_of_eps_before_start = 0

        self.log_queue = queue.Queue()
        webtoon_list_page_url = '%s/%s' % (DOMAIN, webtoon_id)

        webtoon_list_r = requests.get(webtoon_list_page_url, headers=HEADERS, cookies=COOKIES)
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
        global imgs_to_dl, number_of_eps_before_start

        with self._lock:
            self._is_downloading = True

        episode_urls.reverse()
        self.log_queue.put('Downloading %s episodes from ep: %s to ep: %s'
                           % (len(episode_urls), episode_urls[0][1:-5], episode_urls[-1][1:-5]))

        number_of_eps_before_start += 1  # index starts from 1 so add 1
        for episode_url in episode_urls:
            if self._is_closing:  # _is_closing is shared but should be fine not to lock it
                break

            imgs_to_dl = []
            try:
                if self.download_ep(directory_path, episode_url, number_of_eps_before_start):
                    self.log_queue.put('Downloading ' + episode_title + ' complete.')
                else:
                    self.log_queue.put('Failed to download episode with url ' + episode_url + '. Skipping.')
            except ValueError as e:
                print('Failed to download episode - e: ' % e)
                break

            number_of_eps_before_start += 1
            sleep(1)

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

        if len(imgs_to_dl) == 0:
            self.log_queue.put('There are no images to download. Probably this ep is not released yet.')
            return False

        # self.log_queue.put('Images to download are:')
        # for img_url in imgs_to_dl:
        #    self.log_queue.put(img_url)

        headers = {'referer': webtoon_ep_url}

        # ep_id for sorting purposes
        folder_path = directory_path + ('%04d_' % (index,)) + episode_title
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        for i in range(len(imgs_to_dl)):
            # print('Downloading img: %s' % imgs_to_dl[i])
            r = requests.get(imgs_to_dl[i], headers=HEADERS, cookies=COOKIES)
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
        global episode_title

        # Yay there is only one tag that starts with h1!
        if self.get_starttag_text() == '<h1>' and data.strip():
            episode_title = data
            # print('EpParser - episode_title: %s' % episode_title)

        if 'toon_img' in data:
            data_list = data.split('\'')
            encoded_toon_image_html = data_list[1]
            toon_image_html = base64.b64decode(encoded_toon_image_html).decode(encoding='utf-8')

            parser = ToonImageParser()
            parser.feed(toon_image_html)


class ListPageParser(HTMLParser):

    def __init__(self, *, convert_charrefs=True):
        super(ListPageParser, self).__init__(convert_charrefs=convert_charrefs)
        self.found_start_ep = False
        self.last_ep_url = None

    def handle_starttag(self, tag, attrs):
        global episode_urls, number_of_eps_before_start

        if tag == 'td' and len(attrs) == 5 and len(attrs[3]) > 1 and attrs[3][0] == 'data-role':
            episode_url = attrs[3][1]
            # print('ListPageParser - handlestarttag - episode_url: %s' % episode_url)
            if self.last_ep_url and self.last_ep_url == episode_url:
                # The html has two components that match these rules. So skip every duplicates
                return

            self.last_ep_url = episode_url

            if start_ep_id and self.found_start_ep or int(re.search(r'\d+', episode_url).group()) < start_ep_id:
                # the last ep may not have a number. So use this flag to capture that edge case
                self.found_start_ep = True
                number_of_eps_before_start += 1
                return

            # print('episode_url: %s' % episode_url)
            episode_urls.append(episode_url)


class ToonImageParser(HTMLParser):
    global imgs_to_dl

    def handle_starttag(self, tag, attrs):
        img_url = attrs[1][1]
        imgs_to_dl.append('%s%s' % (DOMAIN, img_url))
        # print('EpParser - img_url: %s' % img_url)
