# WebtoonDownloader

![Demo](/demo.png)

Instruction:
1. install virtualenv (if you have some of the latest versions of python, virtualenv will come with it)
2. make the root directory of this repo virtual (python3 -m venv /path/to/new/virtual/environment if virtualenv came with python else google yourself)
3. activate the virtualenv: source bin/activate if python 3 came with virtual env else source venv/bin/activate
4. install dependencies: pip install -r requirements.txt
5. run: python ./downloader.py

Caveat:
Tested with python 3.8.3. No guarantee other versions of python will work.
At the time of writing this README part, python version 3.6 also worked.

**Note: Currently broken as of 2024.**

Things to be done
- add some error checking (especially the inputs)
- add downloader for other websites (daum, etc)

Nice to have
- add some help message (so users know what each input is)
- image vertial-concatenator 
