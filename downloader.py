import tkinter as tk
import classes.NaverWebtoonDownloader as nwd

from tkinter import scrolledtext


class WebtoonDownloader(tk.Frame):
    def __init__(self, master=None):
        master.wm_title("Webtoon Downloader")
        master.protocol("WM_DELETE_WINDOWS", self.close_app)

        tk.Frame.__init__(self, master)
        self.pack(fill=tk.BOTH, expand=1)        
        self.create_widgets()

    def create_widgets(self):
        menubar = tk.Menu(self)
        
        menu = tk.Menu(menubar, tearoff=0)
        menu.add_command(label="Exit", command=self.close_app)
        menubar.add_cascade(label="Menu", menu=menu)

        self.master.config(menu=menubar)

        # webtoon info
        webtoon_info_frame = tk.Frame(self, relief=tk.RAISED, bd=1)
        webtoon_info_frame.pack(side=tk.TOP, fill=tk.X)

        # webtoon id/number
        webtoon_id_frame = tk.Frame(webtoon_info_frame)
        webtoon_id_frame.pack(side=tk.LEFT)

        webtoon_id_label = tk.Label(webtoon_id_frame, text="Webtoon No.:")
        webtoon_id_label.pack(side=tk.LEFT)
       
        max_webtoon_id_len = 6
        webtoon_id_entry = tk.Entry(webtoon_id_frame, width=max_webtoon_id_len)
        webtoon_id_entry.pack(side=tk.LEFT)
        self.webtoon_id_entry = webtoon_id_entry

        # the id/number of the episode of the webtoon you want to start downloading
        start_ep_id_frame = tk.Frame(webtoon_info_frame)
        start_ep_id_frame.pack(side=tk.LEFT)

        start_ep_id_label = tk.Label(start_ep_id_frame, text="Start Episode No.:")
        start_ep_id_label.pack(side=tk.LEFT)

        max_start_ep_id_len = 4
        start_ep_id_entry = tk.Entry(webtoon_info_frame, width=max_start_ep_id_len)
        start_ep_id_entry.pack(side=tk.LEFT)
        self.start_ep_id_entry = start_ep_id_entry
       
        # the location where you want the downloaded webtoons to be on disk
        output_dir_path_frame = tk.Frame(self)
        output_dir_path_frame.pack(side=tk.TOP, fill=tk.X)

        output_dir_path_label = tk.Label(output_dir_path_frame, text="Download Location:")
        output_dir_path_label.pack(side=tk.LEFT)

        max_path_len = 100
        output_dir_path_entry = tk.Entry(output_dir_path_frame, width=max_path_len)
        output_dir_path_entry.pack(side=tk.LEFT)
        self.output_dir_path_entry = output_dir_path_entry

        # log console
        log_frame = tk.Frame(self)
        log_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        log_window = scrolledtext.ScrolledText(log_frame, height=10)
        log_window.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        log_window.config(state=tk.DISABLED)
        self.log_window = log_window

        # download button        
        download_btn_frame = tk.Frame(self)
        download_btn_frame.pack(side=tk.BOTTOM, fill=tk.X)

        download_btn = tk.Button(download_btn_frame)
        download_btn["text"] = "Download"
        download_btn["command"] = self.download
        download_btn.pack(side=tk.RIGHT)
        self.download_btn = download_btn

        # master things
        self.master.update()
        temporary_menubar_height = 30   # hacky way to fix the min height
        min_height = self.master.winfo_height() + temporary_menubar_height
        self.master.minsize(self.master.winfo_width(), min_height)
        
        # I'm too lazy to do error checking! I'm the only user!
        
        
    def close_app(self):
        root.destroy()
       
    def download(self):
        webtoon_id = int(self.webtoon_id_entry.get())
        start_ep_id = int(self.start_ep_id_entry.get())
        output_dir_path = self.output_dir_path_entry.get()

        downloader = nwd.NaverWebtoonDownloader(webtoon_id, start_ep_id, output_dir_path)


root = tk.Tk()
downloader = WebtoonDownloader(master=root)
downloader.mainloop()
