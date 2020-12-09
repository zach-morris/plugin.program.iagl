from __future__ import print_function
import os
import unicodedata
import subprocess
import string
import json
import requests
import sys
import threading 
import time
import io

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


try:
    import xbmcaddon, xbmcgui, xbmcaddon, xbmc
    console_mode = False
except ImportError:
    console_mode = True

addonName = "IAGL"

def colorString(text, color=None):
    if type(text) is not int:
        text = display_string(text)

    if color is 'default' or color is '' or color is None:
        color = get_user_text_color()

    return '[COLOR %s]%s[/COLOR]' % (color, text)    

def display_string(object):
    try:
        if type(object) is str or type(object) is unicode:
            return deaccentString(object)
    except NameError:
        if type(object) is str:
            return deaccentString(object)
    if type(object) is int:
        return '%s' % object
    if type(object) is bytes:
        object = ''.join(chr(x) for x in object)
        return object

def get_user_text_color():
    color = getSetting('general.textColor')
    if color == '' or color == 'None':
        color = 'deepskyblue'

    return color

def deaccentString(text):
    try:
        if isinstance(text, bytes):
            text = text.decode('utf-8')
    except UnicodeDecodeError:
        text = u'%s' % text
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    return text

def safeStr(obj):
    try:
        return str(obj)
    except UnicodeEncodeError:
        return obj.encode('utf-8', 'ignore').decode('ascii', 'ignore')
    except:
        return ""

def strip_non_ascii_and_unprintable(text):
    result = ''.join(char for char in text if char in string.printable)
    return result.encode('ascii', errors='ignore').decode('ascii', errors='ignore')


def copy2clip(txt):
    platform = sys.platform

    if platform == 'win32':
        try:
            cmd = 'echo ' + txt.strip() + '|clip'
            return subprocess.check_call(cmd, shell=True)
            pass
        except:
            pass
    elif platform == 'linux2':
        try:
            from subprocess import Popen, PIPE

            p = Popen(['xsel', '-pi'], stdin=PIPE)
            p.communicate(input=txt)
        except:
            pass
    else:
        pass
    pass


def requests_dl(url, dst):
    response = requests.get(url, stream=True)
    # Throw an error for bad status codes
    response.raise_for_status()
    with open(dst, 'wb') as handle:
        for block in response.iter_content(1024):
            handle.write(block)


def get_cached_url(url, cache_path=".", downloader=requests_dl):
    a = urlparse(url)
    file_name = os.path.basename(a.path)
    path = os.path.join(cache_path,file_name)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    else:
        downloader(url, path)
        with open(path, "rb") as f:
            return f.read()

  
# based on https://www.geeksforgeeks.org/simple-multithreaded-download-manager-in-python/  
def Handler(start, end, url, filename, progress, session, chunk_size): 
     
    headers = {'Range': 'bytes=%d-%d' % (start, end)} 
    try:
        r = session.get(url, headers=headers, stream=True, allow_redirects=True) 
    except requests.exceptions.ConnectionError as e:
        log("Connection Error chunk {}-{}: {}".format(start,end,e),'error')
        # Some errors get dealt with by the retry mechanism in the session
        # inc We get ConnectionError: ('Connection aborted.', BadStatusLine("''",))
        progress(e) # will make the thread as bad
        # TODO: ensure these get retried again at the end?
        return
    with io.open(filename, "r+b") as fp: # see https://stackoverflow.com/questions/29729082/python-fails-to-open-11gb-csv-in-r-mode-but-opens-in-r-mode
        try: 
            fp.seek(start, 0) 
        except IOError as e:
            log("IOError seeking to start of write {}-{}: {}".format(start, end, e),"error")
            progress(e)
            return
        log("Starting Thread {}-{} fpos={}".format(start, end,fp.tell()),"debug")
        saved=0
        last_update = time.time()
        for block in r.iter_content(chunk_size):
            remain = end-start-saved-len(block)
            #if remain < 0:
            #    block = block[:remain]
            fp.write(block)
            saved += len(block)
            #if saved > end-start:
            #    break
            #    #raise Exception()
            if remain <= 0 or time.time() - last_update > 0.5: 
                fp.flush()
                last_update = time.time()
                new_start,new_end = progress(saved, start)
                if new_start != start:
                    # We've been told to do another part
                    # TODO: flush or close?
                    log("Switching Thread {}-{}({}/{}) to {}-{}(0/{})".format(start, end, saved, end-start, new_start, new_end, new_end-new_start),"debug")
                    Handler(new_start, new_end, url, filename, progress, session, chunk_size)
                    break
                elif new_end <= new_start:
                    # User cancelled or exception in other thread
                    log("Cancelling Thread {}-{}({}/{}) fpos={}".format(start, end, saved, end-start, fp.tell(), ),"debug")
                    break
                elif new_end == end and remain <= 0:
                    log("Stopping Thread {}-{}({}/{}) fpos={}".format(start, end, saved, end-start, fp.tell(), ),"debug")
                    break
                elif new_end < end:
                    # another thread is doing our work
                    log("Shorten Thread {}-{}({}/{}) to {}-{}({}/{}) fpos={}".format(start, end, saved, end-start, new_start, new_end, saved, new_end-new_start, fp.tell()),"debug")
                    end = new_end
                else:
                    # Continue on
                    pass

def download_file(url_of_file,name=None,number_of_threads=15, progress=None, chunk_size=1024, timeout=10, session=None):
    session = session if session is not None else requests.Session()
    retries = requests.adapters.Retry(total=5,
                backoff_factor=0.1,
                status_forcelist=[ 500, 502, 503, 504 ])
    session.mount("http://", requests.adapters.HTTPAdapter(max_retries=retries))
    session.mount("https://", requests.adapters.HTTPAdapter(max_retries=retries))
    r = session.head(url_of_file, allow_redirects=True, timeout=timeout) 
    if name: 
        file_name = name 
    else: 
        file_name = url_of_file.split('/')[-1] 
    try: 
        file_size = int(r.headers['content-length']) 
    except: 
        return
    if r.headers['accept-ranges'] != 'bytes':
        return
    part = max(int(file_size / number_of_threads), 2*2**20)  # 2MB min so don't use lots of threads for small files
    with io.open(file_name, "wb") as fp:
    #fp.write(b'\0' * file_size) 
    #fp.truncate(file_size)  # TODO: might not be cross platform - https://stackoverflow.com/questions/8816059/create-file-of-particular-size-in-python
        try:
            #fp.seek(file_size-1)
            #fp.write(b'\0')
            fp.truncate(file_size)
            log("Sparse file created {}bytes: {}".format(file_size, file_name), 'notice')
        except IOError:
            log("Sparse file unsupported. Blanking out {}bytes: {}".format(file_size, file_name), 'notice')
            # This is a lot slower
            i = 0
            started = time.time()
            block = 20*2**20
            while i < file_size:
                fp.write(b'\0' * min(file_size-i,block))
                i += block
            log("Blanked out {}bytes in {}s: {}".format(file_size, time.time()-started, file_name), 'notice')
            #fp.truncate()
    state = {}
    ends = {}
    started = time.time()

    history = [(time.time(), 0)]
    end = -1
    for i in range(number_of_threads): 
        start = end + 1
        end = start + part
        if start > file_size: # due to min part size
            break
        if i+1 == number_of_threads or end > file_size:
            end = file_size 
        state[start] = 0
        ends[start] = end
        def update_state(saved, start):
            state[start] = saved
            end = ends[start]
            last_update, last_saved = history[-1]
            if last_update is None: # Special flag that dl is cancelled or exception happened
                # TODO: could be race condition if other thread adds to history without checking it first
                return (start, 0)
            if isinstance(saved, Exception):
                history.append( (None, saved)) # flag to other threads to stop. #TODO: retry?
                return (start, 0)
            # TODO: if this thread finished we can send instructions to get half of another
            # threads part and tell that other part to get less. Prevents the slow down
            # caused by idle threads at the end.
            remain = lambda start: ends[start]-start-state[start]
            if remain(start) <= 0:
                # we finished. Find the slowest who has the most remaining and help them out
                sstart= sorted(state.keys(),key=remain, reverse=False).pop()
                # ensure slowest only gets half
                send = ends[sstart]
                halfway = sstart + state[sstart] + int(remain(sstart)/2)
                if send-halfway < 2**17: 
                    # too small. Just end the thread
                    return (start,end)
                ends[sstart] = halfway-1 # will be picked up by this thread on its next update
                # create a new state
                state[halfway], ends[halfway] =0, send
                # tell the thread to switch to this
                return (halfway, send)

            dur = time.time() - last_update
            if progress is None or dur < 1:
                # don't update UI until every 1s
                return (start,end)
            saved = sum([s for s in state.values() if type(s) == int]) # can have exceptions
            speed = (saved - last_saved)/1000**2/dur 
            total_speed = saved/(time.time()-started)
            weighted_speed = (total_speed + speed*2)/3
            remain = 1/weighted_speed  * (file_size-saved)
            est = time.time()-started + remain
            if progress(saved, file_size, "{:0.1f}MB/s {:0.0f}/{:0.0f}s".format(speed, remain, est), dict(state=state)) is not False:
                history.append( (time.time(), saved))
                return (start,end)
            else:
                # TODO: Possibly might be better kept as an exception
                # set flag to stop all other threads
                history.append( (None, saved))
                log("User cancelled download {}".format(url_of_file), "warning")
                return (start,0)
        # create a Thread with start and end locations 
        t = threading.Thread(target=Handler, 
            kwargs={'start': start, 'end': end, 'url': url_of_file, 'filename': file_name, 'progress': update_state, 'session': session, 'chunk_size':chunk_size}) 
        t.setDaemon(True) 
        t.start()
    main_thread = threading.current_thread() 
    for t in threading.enumerate(): 
        if t is main_thread: 
            continue
        t.join()
    # TODO: if cancelled we should delete the file
    last_update, last_saved = history[-1]
    if last_update is None:
        return 0
    else:
        return last_saved
      


if not console_mode:
    setSetting = xbmcaddon.Addon().setSetting
    getSetting = xbmcaddon.Addon().getSetting
    getLangString = xbmcaddon.Addon().getLocalizedString

    progressDialog = xbmcgui.DialogProgress()

    bgProgressDialog = xbmcgui.DialogProgressBG

    showDialog = xbmcgui.Dialog()

    kodiVersion = int(xbmc.getInfoLabel("System.BuildVersion")[:2])

    def lang(language_id):
        text = getLangString(language_id)
        if kodiVersion < 19:
            text = text.encode('utf-8', 'replace')
        return text

    def log(msg, level='info'):
        msg = safeStr(msg)
        msg = addonName.upper() + ': ' + msg
        if level == 'error':
            xbmc.log(msg, level=xbmc.LOGERROR)
        elif level == 'info':
            xbmc.log(msg, level=xbmc.LOGINFO)
        elif level == 'notice':
            xbmc.log(msg, level=xbmc.LOGNOTICE)
        elif level == 'warning':
            xbmc.log(msg, level=xbmc.LOGWARNING)
        else:
            xbmc.log(msg)


if console_mode:

    """ A bunch of command line replacements for kodi for testing """
    SETTINGS_FILE = "settings.json"

    kodiVersion = 18

    def getSetting(setting):
        if not os.path.exists(SETTINGS_FILE):
            return ''
        with open(SETTINGS_FILE) as f:
            try:
                return json.load(f).get(setting,"")
            except json.JSONDecodeError as e:
                return ''

    def setSetting(setting, value):
        with open(SETTINGS_FILE, "r+") as f:
            try:
                settings = json.load(f)
            except:
                settings = {}
            settings[setting] = str(value)
            f.seek(0)
            f.truncate()
            json.dump(settings, f)
    
    def lang(number):
        return "{}"

    # def colorString(self, msg):
    #     return '{}'.format(msg)

    def log(msg, level="info"):
        if level != 'debug':
            print("LOG {}: {}".format(level,msg))

    class ProgressDialog():
        def create(self, msg):
            print("Dialog: {}".format(msg))
        def iscanceled(self):
            return False
        def close(self):
            pass
        def update(self, progress, *msgs):
            print(".")
            for msg in msgs:
                print(msg)

    progressDialog = ProgressDialog()

    class ShowDialog():
        def ok(self, msg1, msg2):
            print("Dialog: {} {} OK? Y/N: Y".format(msg1,msg2))

    showDialog = ShowDialog()


import zlib
class crc32(object):
    name = 'crc32'
    digest_size = 4
    block_size = 1

    def __init__(self, arg=''):
        self.__digest = 0
        self.update(arg)

    def copy(self):
        copy = super(self.__class__, self).__new__(self.__class__)
        copy.__digest = self.__digest
        return copy

    def digest(self):
        return self.__digest

    def hexdigest(self):
        return '{:08x}'.format(self.__digest)

    def update(self, arg):
        self.__digest = zlib.crc32(arg, self.__digest) & 0xffffffff


import hashlib
def compare_hashes(filename, hashes):
    BUF_SIZE = 65536
    size = 0        
    libs = dict(sha1=hashlib.sha1(), md5=hashlib.md5(),crc32=crc32())
    with open(file, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            size += len(data)
            if not data:
                break
            for lib in libs.values():
                lib.update(data)
    for hash in hashes:
        p = hash.split('=')
        print (libs.get(p[0]).hexdigest(), p[1])


if __name__ == '__main__':
    url,hashes = "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4", ["md5=yrCLNhle2xoSMdLQn6RQ4A=="]
    #url, hashes = "https://archive.org/download/RedumpSonyPlayStationAmerica20160617/Tony%20Hawk%27s%20Pro%20Skater%202%20%28USA%29.zip", ["md5=59b46cb4797b2d7cdd691c8e275d455f==", "sha1=3993a7b69818171f841a33a4fa93594052125b2b=="]
    #url = "https://archive.org/download/3DO_Redump/3DO_Redump_archive.torrent"
    #url = "https://archive.org/download/MAME2003_Reference_Set_MAME0.78_ROMs_CHDs_Samples/roms/invaders.zip"
    #url = "https://archive.org/download/PSP_EU_Arquivista/Worms%20-%20Open%20Warfare%20%28EU%29.iso"
    #   <rom name="PSP_US_Arquivista/Aliens%20vs%20Predator%20-%20Requiem%20%28US%29.iso" size="396492800" md5="9568c2c27f0c9701f6f27a418b41d05a" sha1="f6802ce9225b132cf8b6514e369046c719c98283" />
    #url, hash = "https://archive.org/download/PSP_US_Arquivista/Aliens%20vs%20Predator%20-%20Requiem%20%28US%29.iso","f6802ce9225b132cf8b6514e369046c719c98283"
    progress = lambda size, total, msg, *_: print(int(size/total*100), msg)
    file = url.split('/')[-1]
    download_file(url, file, progress=progress, number_of_threads=20)
    compare_hashes(file, hashes)



