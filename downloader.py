import tkinter as tk
import classes.NaverWebtoonDownloader as nwd
import classes.ToonKorDownloader as tkd

from tkinter import scrolledtext, filedialog

"""
TODO (not in particular order):

- Choosing which downloader to use
- (ToonKor) Get cache value as a parameter


Nice to have:
- (ToonKor) Bypass captcha (is this even possible?)
"""

"""
ToonKorDownloader Instruction if it doesn't work due to 403 error:

1. On your browser, load the website and pass the captcha
2. Reload your page find cf_clearance from the cache
3. Copy paste the value of cf_clearance to ToonKorDownloader.py
"""


class WebtoonDownloader(tk.Frame):
    def __init__(self, master=None):
        # initialize instance variables
        self.downloader = None
        self.webtoon_id_entry = None
        self.start_ep_index_entry = None
        self.log_window = None
        self.output_dir_path_chosen_label = None
        self.download_btn = None

        # initialize the UI
        master.wm_title('Webtoon Downloader')
        master.protocol('WM_DELETE_WINDOW', self.close_app)

        tk.Frame.__init__(self, master)
        self.pack(fill=tk.BOTH, expand=1)
        self.create_widgets()

        self.display_new_logs()

    def create_widgets(self):
        menubar = tk.Menu(self)
        
        menu = tk.Menu(menubar, tearoff=0)
        menu.add_command(label='Exit', command=self.close_app)
        menubar.add_cascade(label='Menu', menu=menu)

        self.master.config(menu=menubar)

        # webtoon info
        webtoon_info_frame = tk.Frame(self)
        webtoon_info_frame.pack(side=tk.TOP, fill=tk.X)

        # webtoon id/number
        webtoon_id_frame = tk.Frame(webtoon_info_frame)
        webtoon_id_frame.pack(side=tk.LEFT)

        webtoon_id_label = tk.Label(webtoon_id_frame, text='Webtoon No.:')
        webtoon_id_label.pack(side=tk.LEFT)
       
        max_webtoon_id_len = 6
        webtoon_id_entry = tk.Entry(webtoon_id_frame, width=max_webtoon_id_len)
        webtoon_id_entry.pack(side=tk.LEFT)
        self.webtoon_id_entry = webtoon_id_entry

        # the id/number of the episode of the webtoon you want to start downloading
        start_ep_index_frame = tk.Frame(webtoon_info_frame)
        start_ep_index_frame.pack(side=tk.LEFT)

        start_ep_index_label = tk.Label(start_ep_index_frame, text='Start Index No.:')
        start_ep_index_label.pack(side=tk.LEFT)

        max_start_ep_index_len = 4
        start_ep_index_entry = tk.Entry(webtoon_info_frame, width=max_start_ep_index_len)
        start_ep_index_entry.pack(side=tk.LEFT)
        self.start_ep_index_entry = start_ep_index_entry
       
        # the location where you want the downloaded webtoons to be on disk
        output_dir_path_frame = tk.Frame(self)
        output_dir_path_frame.pack(side=tk.TOP, fill=tk.X)

        output_dir_path_label = tk.Label(output_dir_path_frame, text='Download Location:')
        output_dir_path_label.pack(side=tk.LEFT)

        self.output_dir_path_chosen_label = tk.Label(output_dir_path_frame, text='/')  # default is current directory
        self.output_dir_path_chosen_label.pack(side=tk.LEFT)

        # output directory choose button
        output_dir_path_choose_btn = tk.Button(output_dir_path_frame)
        output_dir_path_choose_btn['text'] = 'Choosde Directory'
        output_dir_path_choose_btn['command'] = self._assign_output_directory_path
        output_dir_path_choose_btn.pack(side=tk.RIGHT)
        # self.output_dir_path_choose_btn = output_dir_path_choose_btn

        # log console
        log_frame = tk.Frame(self, relief=tk.SUNKEN, bd=1)
        log_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        log_window = scrolledtext.ScrolledText(log_frame, height=10)
        log_window.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        log_window.config(state=tk.DISABLED)
        self.log_window = log_window

        # download button        
        download_btn_frame = tk.Frame(self)
        download_btn_frame.pack(side=tk.BOTTOM, fill=tk.X)

        download_btn = tk.Button(download_btn_frame)
        download_btn['text'] = 'Download'
        download_btn['command'] = self.download
        download_btn.pack(side=tk.RIGHT)
        self.download_btn = download_btn

        # master things
        self.master.update()
        temporary_menubar_height = 30   # hacky way to fix the min height
        min_height = self.master.winfo_height() + temporary_menubar_height
        self.master.minsize(self.master.winfo_width(), min_height)
        
        # I'm too lazy to do error checking! I'm the only user!
        
    def close_app(self):
        if self.downloader is not None:
            self.downloader.destroy()
        root.destroy()
       
    def download(self):
        webtoon_id = self.webtoon_id_entry.get()
        try:
            webtoon_id = int(webtoon_id)
        except ValueError:
            # If not int, it must be the name of the webtoon.
            pass

        try:
            start_ep_index = int(self.start_ep_index_entry.get())
        except ValueError:
            start_ep_index = None
        output_dir_path = self.output_dir_path_chosen_label['text']

        if self.downloader is not None and self.downloader.is_downloading():
            self.display_log('Error: Download is in progress. Wait')
        else:   # better to use a function and reuse the instance but lazy
            # TODO: Naver needs start_ep_id and toon kor needs start_ep_indes
            self.downloader = nwd.Downloader(webtoon_id, start_ep_index, output_dir_path)
            # self.downloader = tkd.Downloader(webtoon_id, start_ep_index, output_dir_path)

    def display_new_logs(self):
        if self.downloader is not None:
            logs = self.downloader.get_new_logs()
            for log in logs:
                self.display_log(log)
        self.master.after(100, self.display_new_logs)

    def display_log(self, log):
        self.log_window.config(state=tk.NORMAL)
        self.log_window.insert(tk.END, '%s\n' % log)
        self.log_window.yview(tk.END)
        self.log_window.config(state=tk.DISABLED)

    def _assign_output_directory_path(self):
        self.output_dir_path_chosen_label['text'] = filedialog.askdirectory() + "/"


root = tk.Tk()
downloader = WebtoonDownloader(master=root)
downloader.mainloop()
