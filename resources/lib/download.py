#Internet Archive Game Launcher v4.X (For Kodi v19+)
#Zach Morris
#https://github.com/zach-morris/plugin.program.iagl
import xbmc, xbmcgui, xbmcvfs
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import current_thread
from urllib.parse import unquote_plus as url_unquote
import requests, time, json
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class download(object):
	def __init__(self,config=None,rom=None,game_name=None,dl_path=None,current_downloader='archive_org',threads=None,auto_login=True,show_dl_progress=True,show_login_progress=True,ia_email=None,ia_password=None,if_game_exists=0,ige_dialog=None):
		self.config = config
		self.show_dl_progress = show_dl_progress
		self.show_login_progress = show_login_progress
		self.downloader = None
		self.rom = rom
		self.game_name = game_name
		self.dl_path = dl_path
		self.auto_login = auto_login
		self.current_downloader = current_downloader
		self.ia_email = None
		self.ia_password = None
		self.if_game_exists = if_game_exists
		self.ige_dialog = ige_dialog
		if threads is None:
			self.threads = self.config.defaults.get('threads')
		else:
			if isinstance(threads,str) and threads.isdigit():
				self.threads = int(threads)
			elif isinstance(threads,int):
				self.threads = threads
			else:
				self.threads = self.config.defaults.get('threads')
		self.set_ia_creds(ia_email=ia_email,ia_password=ia_password)
		self.set_downloader(downloader=current_downloader)

	def set_rom(self,rom=None):
		if isinstance(rom,dict):
			self.rom = [rom]
		elif isinstance(rom,list):
			self.rom = rom
		else:
			self.rom = None
		if self.downloader is not None:
			self.downloader.set_rom(rom=self.rom)

	def set_threads(self,threads=None):
		if isinstance(threads,str) and threads.isdigit():
			self.threads = int(threads)
		elif isinstance(threads,int):
			self.threads = threads
		else:
			self.threads = self.config.defaults.get('threads')
		if self.downloader is not None:
			self.downloader.set_threads(threads=self.threads)

	def set_game_name(self,game_name=None):
		if isinstance(game_name,str):
			self.game_name = game_name
		if self.downloader is not None:
			self.downloader.set_game_name(game_name=game_name)

	def set_dl_path(self,path_in=None):
		if isinstance(path_in,str):
			self.dl_path = path_in
			xbmc.log(msg='IAGL:  Dowload path is set: {}'.format(self.dl_path),level=xbmc.LOGDEBUG)
		elif isinstance(path_in,Path):
			self.dl_path = str(path_in)
			xbmc.log(msg='IAGL:  Dowload path is set: {}'.format(self.dl_path),level=xbmc.LOGDEBUG)
		else:
			self.dl_path = None
		if self.downloader is not None:
			self.downloader.set_dl_path(path_in=self.dl_path)

	def set_ia_creds(self,ia_email=None,ia_password=None):
		if isinstance(ia_email,str) and len(ia_email)>0:
			self.ia_email = ia_email
			xbmc.log(msg='IAGL:  Archive.org email set: {}@{}'.format(''.join(['*' for x in self.ia_email.split('@')[0]]),self.ia_email.split('@')[-1]),level=xbmc.LOGDEBUG)
		if isinstance(ia_password,str) and len(ia_password)>0:
			self.ia_password = ia_password
			xbmc.log(msg='IAGL:  Archive.org password is set: {}'.format(''.join(['*' for x in self.ia_password])),level=xbmc.LOGDEBUG)

	def set_downloader(self,downloader='archive_org'):
		if downloader == 'generic':
			xbmc.log(msg='IAGL:  Downloader set to generic http downloader',level=xbmc.LOGDEBUG)
			self.downloader = self.generic_downloader(config=self.config,dl_path=self.dl_path,threads=self.threads,auto_login=self.auto_login,show_dl_progress=self.show_dl_progress,show_login_progress=self.show_login_progress,if_game_exists=self.if_game_exists,ige_dialog=self.ige_dialog)
		elif downloader == 'archive_org':
			xbmc.log(msg='IAGL:  Downloader set to archive.org',level=xbmc.LOGDEBUG)
			self.downloader = self.archive_org(config=self.config,dl_path=self.dl_path,threads=self.threads,auto_login=self.auto_login,show_dl_progress=self.show_dl_progress,show_login_progress=self.show_login_progress,ia_email=self.ia_email,ia_password=self.ia_password,if_game_exists=self.if_game_exists,ige_dialog=self.ige_dialog)
		elif downloader == 'local_source':
			xbmc.log(msg='IAGL:  Downloader set to Local File Source',level=xbmc.LOGDEBUG)
			self.downloader = self.local_source(config=self.config,dl_path=self.dl_path,threads=self.threads,auto_login=self.auto_login,show_dl_progress=self.show_dl_progress,show_login_progress=self.show_login_progress,if_game_exists=self.if_game_exists,ige_dialog=self.ige_dialog)
		else:
			xbmc.log(msg='IAGL:  Downloader type is unknown, defaulting to NONE',level=xbmc.LOGDEBUG)
			self.downloader = None #Default downloader to NONE unless otherwise specified, saves unecessary login attempt
		self.current_downloader = downloader

	def download_game(self):
		if isinstance(self.rom,list):
			self.downloader.set_dl_path(dl_path=self.dl_path)
			for r in self.rom:
				self.downloader.set_rom(rom=r)
				r['dl_status'] = self.downloader.download()
		else:
			xbmc.log(msg='IAGL:  Badly formed game download request: {}'.format(self.rom),level=xbmc.LOGERROR)
			
	class archive_org(object):
		def __init__(self,config=None,rom=None,game_name=None,dl_path=None,threads=None,auto_login=True,show_dl_progress=True,show_login_progress=True,ia_email=None,ia_password=None,if_game_exists=0,ige_dialog=None):
			self.config = config
			self.rom = rom
			self.game_name = game_name
			self.dl_path = dl_path
			if threads is None:
				self.threads = self.config.defaults.get('threads')
			else:
				self.threads = threads
			self.auto_login = auto_login
			self.show_dl_progress = show_dl_progress
			self.show_login_progress = show_login_progress
			self.ia_email = ia_email
			self.ia_password = ia_password
			self.if_game_exists = if_game_exists
			if isinstance(ige_dialog,dict):
				self.ige_dialog = ige_dialog
			else:
				self.ige_dialog = dict()
			self.if_game_exists_choice = None  #Account for multiple filed games, keep track of the users choice
			self.dp = None
			self.dp_id = 10101
			self.session = requests.Session()
			self.retries = requests.adapters.Retry(total=5,backoff_factor=0.1,status_forcelist=[500,502,503,504,499])
			self.session.mount("http://",requests.adapters.HTTPAdapter(max_retries=self.retries))
			self.session.mount("https://",requests.adapters.HTTPAdapter(max_retries=self.retries))
			self.ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.3'
			self.login_headers = {'User-Agent': self.ua,'Accept': '*/*','Accept-Language': 'en-US,en;q=0.5','Content-Type':'multipart/form-data; boundary=---------------------------239962525138460636124209110177','Sec-GPC': '1','Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors','Sec-Fetch-Site': 'same-origin','Priority': 'u=1'}
			if self.auto_login:
				self.logged_in = self.login()
			else:
				self.logged_in = False

		def set_rom(self,rom=None):
			if isinstance(rom,dict):
				self.rom = [rom]
			elif isinstance(rom,list):
				self.rom = rom
			else:
				self.rom = None

		def set_game_name(self,game_name=None):
			if isinstance(game_name,str):
				self.game_name = game_name

		def set_dl_path(self,path_in=None):
			if isinstance(path_in,str):
				self.dl_path = path_in
			elif isinstance(path_in,Path):
				self.dl_path = str(path_in)
			else:
				self.dl_path = None

		def set_threads(self,threads=None):
			if isinstance(threads,str) and threads.isdigit():
				self.threads = int(threads)
			elif isinstance(threads,int):
				self.threads = threads
			else:
				self.threads = self.config.defaults.get('threads')

		def load_previous_cookie(self):
			ia_cookie = None
			if self.config.files.get('ia_cookie').exists():
				try:
					ia_cookie = json.loads(self.config.files.get('ia_cookie').read_text())
				except Exception as exc:
					xbmc.log(msg='IAGL:  IA Cookie read error: {}'.format(exc),level=xbmc.LOGERROR)
			if isinstance(ia_cookie,dict) and isinstance(ia_cookie.get('cookie'),dict) and isinstance(ia_cookie.get('expires'),int) and ia_cookie.get('expires')>time.time():
				for k,v in ia_cookie.get('cookie').items():
					self.session.cookies.set(k,v,domain=ia_cookie.get('domain'))
				xbmc.log(msg='IAGL:  Archive.org cookie loaded from previous session',level=xbmc.LOGDEBUG)
			else:
				if self.config.files.get('ia_cookie').exists():
					self.config.files.get('ia_cookie').unlink()
					xbmc.log(msg='IAGL:  Archive.org cookie deleted from previous session (expired or malformed)',level=xbmc.LOGDEBUG)

		def bytes_to_string_size(self,bytes_in=None,format='%.1f',base=1024):
			if isinstance(bytes_in,float) or isinstance(bytes_in,int):
				suffix = ('kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')
				if abs(bytes_in) < base:
					return '%d Bytes' % bytes_in
				else:
					for i, s in enumerate(suffix):
						unit = base ** (i + 2)
						if abs(bytes_in)<unit:
							return (format + ' %s') % ((base * bytes_in / unit), s)
					return (format + ' %s') % ((base * bytes_in / unit), s)
			else:
				return None

		def delete_file(self,file_in=None):
			success = False
			if isinstance(file_in,str) and xbmcvfs.exists(file_in):
				success = xbmcvfs.delete(file_in)
				if success:
					xbmc.log(msg='IAGL:  File deleted {}'.format(file_in),level=xbmc.LOGDEBUG)
				else:
					xbmc.log(msg='IAGL:  Unable to delete file {}'.format(file_in),level=xbmc.LOGDEBUG)
			return success

		def combine_chunks(self,files_in=None,dest_file=None,overwrite=True):
			success = False
			if isinstance(files_in,list) and isinstance(dest_file,str):
				if all([xbmcvfs.exists(x) for x in files_in]):
					xbmc.log(msg='IAGL:  Combining {} chunks into file {}'.format(len(files_in),dest_file),level=xbmc.LOGDEBUG)
					if xbmcvfs.exists(dest_file) and overwrite:
						xbmc.log(msg='IAGL:  Destination file for combining already exists, deleting',level=xbmc.LOGDEBUG)
						self.delete_file(dest_file)
					with xbmcvfs.File(dest_file,'w') as fo:
						for fi in files_in:  #Files are passed in the correct order
							with xbmcvfs.File(fi) as fi:
								fo.write(fi.readBytes()) #Writing entire chunk file in one go
							#Delete chunks here
					if xbmcvfs.exists(dest_file):
						for df in files_in:
							self.delete_file(df) #Delete chunks after combining
						success = True
				else:
					xbmc.log(msg='IAGL:  One or more chunk files were not found, aborting combining',level=xbmc.LOGERROR)
			return success

		def check_login(self):
			self.load_previous_cookie()			
			try:
				with self.session.get(self.config.downloads.get('archive_org_check_acct'),timeout=self.config.downloads.get('timeout'),headers=self.login_headers,allow_redirects=False) as r:
					r.raise_for_status()
					if r.ok and isinstance(r.text,str) and len(r.text)>0:
						response = json.loads(r.text)
						if response.get('success'):
							self.logged_in = True
							if isinstance(response.get('value'),dict):
								xbmc.log(msg='IAGL:  Archive.org user is logged in: {}'.format(response.get('value').get('screenname')),level=xbmc.LOGERROR)
			except Exception as exc:
				xbmc.log(msg='IAGL:  Archive.org check exception: {}'.format(exc),level=xbmc.LOGERROR)
				self.logged_in = False

		def login(self):
			if self.dp is not None:
				description = '{}{}'.format(self.config.addon.get('addon_handle').getLocalizedString(30273),self.game_name or 'Files')
				self.dp.update(1,description)
			self.check_login()
			if not self.logged_in:
				if isinstance(self.ia_email,str) and isinstance(self.ia_password,str):
					try:
						with self.session.get(self.config.downloads.get('archive_org_login_url'),verify=False,headers=self.login_headers) as r1:
							if r1.ok:
								xbmc.log(msg='IAGL:  Attempting Archive.org login',level=xbmc.LOGDEBUG)
					except Exception as exc:
						xbmc.log(msg='IAGL:  Archive.org login attempt exception: {}'.format(exc),level=xbmc.LOGERROR)
					self.login_form_data = '-----------------------------239962525138460636124209110177\r\nContent-Disposition: form-data; name="username"\r\n\r\n{}\r\n-----------------------------239962525138460636124209110177\r\nContent-Disposition: form-data; name="password"\r\n\r\n{}\r\n-----------------------------239962525138460636124209110177\r\nContent-Disposition: form-data; name="remember"\r\n\r\ntrue\r\n-----------------------------239962525138460636124209110177\r\nContent-Disposition: form-data; name="referer"\r\n\r\nhttps://archive.org/\r\n-----------------------------239962525138460636124209110177\r\nContent-Disposition: form-data; name="login"\r\n\r\ntrue\r\n-----------------------------239962525138460636124209110177\r\nContent-Disposition: form-data; name="submit_by_js"\r\n\r\ntrue\r\n-----------------------------239962525138460636124209110177--\r\n'.format(self.ia_email,self.ia_password).encode('ascii')
					try:
						with self.session.post(self.config.downloads.get('archive_org_login_url'),verify=False,headers=self.login_headers,data=self.login_form_data) as r:
							r.raise_for_status()
							if r.ok and isinstance(r.text,str) and 'Successful login' in r.text:
								self.logged_in = True
								xbmc.log(msg='IAGL:  Archive.org login good',level=xbmc.LOGDEBUG)
								if isinstance(r.cookies.get_dict(),dict) and all([x in r.cookies.get_dict().keys() for x in ['logged-in-sig', 'logged-in-user']]):
									ia_cookie = {'cookie':r.cookies.get_dict(),'expires':max([x.expires for x in r.cookies]),'domain':next(iter([x.domain for x in r.cookies]),None)}
									self.config.files.get('ia_cookie').write_text(json.dumps(ia_cookie))
									xbmc.log(msg='IAGL:  Archive.org session cookie set, expires at: {}'.format(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(ia_cookie.get('expires')))),level=xbmc.LOGDEBUG)
							else:
								self.logged_in = False
								if isinstance(r.text,str):
									xbmc.log(msg='IAGL:  Archive.org login failed: {}'.format(r.text),level=xbmc.LOGERROR)
					except Exception as exc:
						xbmc.log(msg='IAGL:  Archive.org login exception: {}'.format(exc),level=xbmc.LOGERROR)
				else:
					xbmc.log(msg='IAGL:  Archive.org credentials are not entered yet',level=xbmc.LOGDEBUG)

		def get_rom_heads(self):
			if self.dp is not None:
				description = '{}{}'.format(self.config.addon.get('addon_handle').getLocalizedString(30274),self.game_name or 'Files')
				self.dp.update(2,description)
			if isinstance(self.rom,list):
				for rn,cr in enumerate(self.rom):
					cr['filename'] = url_unquote(cr.get('url').split('/')[-1].split('%2F')[-1])
					cr['dl_filepath'] = Path(self.dl_path).joinpath(cr.get('filename'))
					cr['filenum'] = rn
					matching_files = [x for x in Path(self.dl_path).rglob('**/{}*'.format(Path(cr.get('filename')).name))] #First find any exact matches
					matching_files = matching_files+[x for x in Path(self.dl_path).rglob('**/{}*'.format(Path(cr.get('filename')).stem)) if x not in matching_files] #Next add any stem matches
					cr['matching_files'] = matching_files  #May have to make this more fancy when pointer files are introduced for certain archives, or take care of it in post_process
					cr['matching_file_found'] = True if len(cr.get('matching_files'))>0 else False
					cr['continue_with_download'] = True #Default to download
					if cr.get('matching_file_found'):
						xbmc.log(msg='IAGL:  Matching file(s) found locally for requested game:\n{}'.format('\n'.join(['..{}/{}'.format(x.parent.name,x.name) for x in cr['matching_files']])),level=xbmc.LOGDEBUG)
						if self.if_game_exists == 0 or self.if_game_exists_choice == 0:
							cr['continue_with_download'] = False
						elif self.if_game_exists == 1 or self.if_game_exists_choice == 1:
							xbmc.log(msg='IAGL:  User setting is to re-download.  Ignoring matching files',level=xbmc.LOGDEBUG)
						elif self.if_game_exists == 2 and self.if_game_exists_choice is None: #Prompt user if they haven't yet made a choice
							selected = xbmcgui.Dialog().select(heading=self.ige_dialog.get('heading') or 'Matching local file',list=self.ige_dialog.get('list') or ['Do not re-download','Re-download and overwrite'],useDetails=False)
							if selected == 0:
								self.if_game_exists_choice = 0
								cr['continue_with_download'] = False
							elif selected == 1:
								self.if_game_exists_choice = 1
							else:
								pass #Continue with download, and re-ask if theres more files
						else:
							pass
					if cr.get('continue_with_download'):
						try:
							with self.session.head(cr.get('url'),verify=False,timeout=self.config.downloads.get('timeout'),allow_redirects=True) as r:
								if r.ok and r.headers:
									cr['head_success'] = True
									if isinstance(r.headers.get('Content-Length'),str) and r.headers.get('Content-Length').isdigit():
										cr['Content-Length'] = int(r.headers.get('Content-Length'))
									if isinstance(r.headers.get('Accept-Ranges'),str) and r.headers.get('Accept-Ranges')=='bytes':
										cr['Accept-Ranges'] = True
									else:
										cr['Accept-Ranges'] = False
								else:
									cr['head_success'] = False
									cr['Content-Length'] = None
									cr['Accept-Ranges'] = None
						except requests.exceptions.RequestException as rexc:
							xbmc.log(msg='IAGL:  Head request exception for {}.  Request Exception {}'.format(cr.get('url'),rexc),level=xbmc.LOGERROR)
							cr['head_success'] = False
							cr['Content-Length'] = None
							cr['Accept-Ranges'] = None
						except requests.exceptions.HTTPError as hexc:
							xbmc.log(msg='IAGL:  Head request exception for {}.  HTTP Exception {}'.format(cr.get('url'),hexc),level=xbmc.LOGERROR)
							cr['head_success'] = False
							cr['Content-Length'] = None
							cr['Accept-Ranges'] = None
						except requests.exceptions.ConnectionError as cexc:
							xbmc.log(msg='IAGL:  Head request exception for {}.  Connection Exception {}'.format(cr.get('url'),cexc),level=xbmc.LOGERROR)
							cr['head_success'] = False
							cr['Content-Length'] = None
							cr['Accept-Ranges'] = None
						except requests.exceptions.Timeout as texc:
							xbmc.log(msg='IAGL:  Head request exception for {}.  Timeout Exception {}'.format(cr.get('url'),texc),level=xbmc.LOGERROR)
							cr['head_success'] = False
							cr['Content-Length'] = None
							cr['Accept-Ranges'] = None
						except Exception as exc:
							xbmc.log(msg='IAGL:  Head request exception for {}. Exception {}'.format(cr.get('url'),exc),level=xbmc.LOGERROR)
							cr['head_success'] = False
							cr['Content-Length'] = None
							cr['Accept-Ranges'] = None
						cr['filesize'] = cr.get('Content-Length') or cr.get('size') #Use content length if provided
						if isinstance(cr.get('filesize'),str) and cr.get('filesize').isdigit():
							cr['filesize'] = int(cr.get('filesize')) #Ensure the size is an integer
						if cr.get('Accept-Ranges'):
							chunk_size = min([self.config.downloads.get('min_file_size'),cr.get('filesize')])
							if chunk_size <= 0: #Chunk size can't be 0 or less
								chunk_size = cr.get('filesize')
							if chunk_size==cr.get('filesize'):
								cr['chunk_size'] = abs(cr.get('filesize'))
								cr['byte_ranges'] = '0-'  #Small file, so we'll just request everything in one chunk
								cr['chunk_filenames'] = str(cr.get('dl_filepath'))
							else:
								rr=list(range(0,cr.get('filesize'),chunk_size))
								cr['chunk_size'] = chunk_size
								cr['byte_ranges'] = ['{}-{}'.format(r1,r2-1 if r2!='end' else '') for r1,r2 in zip(rr,rr[1:]+['end'])] #Otherwise break the file into chunks
								cr['chunk_filenames'] = [str(cr.get('dl_filepath').parent.joinpath(cr.get('dl_filepath').stem+'.{0:0=3d}'.format(ii)+cr.get('dl_filepath').suffix)) for ii,x in enumerate(cr.get('byte_ranges'))]
						else:
							cr['chunk_size'] = abs(cr.get('filesize'))
							cr['byte_ranges'] = '0-'
							cr['chunk_filenames'] = str(cr.get('dl_filepath'))

		def download(self):
			self.download_cancelled = False
			if self.show_dl_progress:
				self.dp = xbmcgui.DialogProgress()
				title = self.config.addon.get('addon_handle').getLocalizedString(30043)
				description = '{}{}'.format(self.config.addon.get('addon_handle').getLocalizedString(30271),self.game_name or 'Files')
				self.dp.create(title,description)
				self.dp.update(0,description)
			else:
				self.dp = None
			if isinstance(self.ia_email,str) and isinstance(self.ia_password,str):
				if not self.logged_in:
					self.login()
			else:
				xbmc.log(msg='IAGL:  Attempting download without login credentials',level=xbmc.LOGDEBUG)
			self.get_rom_heads() #Initialize info needed for downloading, look for local files
			for cr in self.rom: #Threaded download for each rom in order
				if cr.get('continue_with_download'):
					xbmcgui.Window(self.dp_id).setProperty('current_size',str(0))
					xbmcgui.Window(self.dp_id).clearProperty('start_time')
					xbmcgui.Window(self.dp_id).clearProperty('last_update')
					if cr.get('chunk_filenames') is None:
						num_workers = 1
					else:
						num_workers = self.threads
					executor = ThreadPoolExecutor(max_workers=num_workers)
					if isinstance(cr.get('chunk_filenames'),list):
						xbmc.log(msg='IAGL:  Creating {} chunks to download with {} threads'.format(len(cr.get('chunk_filenames')),num_workers),level=xbmc.LOGDEBUG)
						futures=[executor.submit(self.download_chunk,rom=cr,byte_range=br,chunk_filename=cf,thread_id=ii) for ii,(br,cf) in enumerate(zip(cr.get('byte_ranges'),cr.get('chunk_filenames')))]
					else:
						xbmc.log(msg='IAGL:  Creating 1 chunks to download with {} threads'.format(num_workers),level=xbmc.LOGDEBUG)
						futures=[executor.submit(self.download_chunk,rom=cr,byte_range=cr.get('byte_ranges'),chunk_filename=cr.get('chunk_filenames'),thread_id=0)]
					futures_results = [f.result() for f in futures] #Execute the threads, gather results
					if len(futures_results)>1:
						if all([x.get('success') for x in futures_results]):
							if self.combine_chunks(files_in=sorted([x.get('chunk_filename') for x in futures_results]),dest_file=str(cr.get('dl_filepath'))):
								cr['download_success'] = True
								cr['download_size'] = sum([x.get('download_size') for x in futures_results])
							else:
								cr['download_success'] = False
								cr['download_size'] = None
								self.delete_file(str(cr.get('dl_filepath'))) #Download of a chunk failed, so delete the resulting file(s)
								for fp in cr.get('chunk_filenames'):
									self.delete_file(fp)
						else:
							xbmc.log(msg='IAGL:  One or more chunk downloads failed',level=xbmc.LOGERROR)
							cr['download_success'] = False
							cr['download_size'] = None
							cr['download_message'] = next(iter([x.get('message') for x in futures_results if not x.get('success')]),None)
							for fp in cr.get('chunk_filenames'):
								self.delete_file(fp)
							for fp in [x.get('dl_filepath') for x in self.rom]:
								self.delete_file(str(fp))
					else:
						if xbmcvfs.exists(cr.get('chunk_filenames')):
							cr['download_success'] = True
							cr['download_size'] = sum([x.get('download_size') for x in futures_results])
						else:
							xbmc.log(msg='IAGL:  Single chunk download failed',level=xbmc.LOGERROR)
							cr['download_success'] = False
							cr['download_size'] = None
							cr['download_message'] = next(iter([x.get('message') for x in futures_results if not x.get('success') and isinstance(x.get('message'),str)]),None)
							self.delete_file(str(cr.get('dl_filepath')))
				else:
					cr['download_success'] = True
					cr['download_size'] = None
					cr['download_message'] = 'Matching file found'
			xbmcgui.Window(self.dp_id).clearProperty('current_size')
			xbmcgui.Window(self.dp_id).clearProperty('start_time')
			xbmcgui.Window(self.dp_id).clearProperty('last_update')
			self.dp.close()
			self.dp = None
			return self.rom

		def download_chunk(self,rom=None,byte_range=None,chunk_filename=None,thread_id=None):
			#Initialize the download chunk result to fail and no size
			result = dict()
			result['success'] = False
			result['download_size'] = None
			result['message'] = None
			result['chunk_filename'] = None
			r = None
			if not self.download_cancelled and isinstance(rom,dict) and isinstance(byte_range,str) and isinstance(chunk_filename,str) and isinstance(rom.get('chunk_size'),int): #Accepts byte range
				xbmc.log(msg='IAGL: {} downloading chunk {} of {} (byte range {})'.format(current_thread().getName(),thread_id,chunk_filename,byte_range),level=xbmc.LOGDEBUG)
				try:  #Start chunk download
					size = 0 #Initialize size of this threads download size
					with self.session.get(rom.get('url'),headers={'Range':'bytes={}'.format(byte_range)},verify=False,stream=True,timeout=self.config.downloads.get('timeout'),allow_redirects=True) as r:
						r.raise_for_status()
						with xbmcvfs.File(chunk_filename,'wb') as game_file:
							current_time = time.time()
							if not xbmcgui.Window(self.dp_id).getProperty('start_time').isdigit():
								xbmcgui.Window(self.dp_id).setProperty('start_time',str(int(current_time*1000)))
							# for chunk in r.iter_content(chunk_size=rom.get('chunk_size')):
							for chunk in r.iter_content(chunk_size=self.config.downloads.get('chunk_size')): #Break download into chunks (approx 4 for min file size)
								game_file.write(bytearray(chunk))
								size = size+len(chunk) #chunks may be a different size when streaming
								if self.dp is not None and self.dp.iscanceled():
									self.download_cancelled = True
									raise Exception('User Cancelled Download')
								if self.dp is not None:
									if xbmcgui.Window(self.dp_id).getProperty('current_size').isdigit():
										current_size=int(xbmcgui.Window(self.dp_id).getProperty('current_size'))+len(chunk) #Get size of download combining all threads
									else:
										current_size=len(chunk)
									percent_complete = int(100*current_size/(rom.get('filesize')+1)) #Calculate overall progress for downloading this file combining all threads
									xbmcgui.Window(self.dp_id).setProperty('current_size',str(current_size))
									if xbmcgui.Window(self.dp_id).getProperty('start_time').isdigit():
										bps_start = int(xbmcgui.Window(self.dp_id).getProperty('start_time'))/1000
									else:
										bps_start = current_time
									bytes_per_sec = current_size/(time.time() - bps_start + 0.000001) #Rudimentary bytes per sec
									if len(xbmcgui.Window(self.dp_id).getProperty('last_update')) == 0 or (xbmcgui.Window(self.dp_id).getProperty('last_update').isdigit() and abs(int(xbmcgui.Window(self.dp_id).getProperty('last_update'))-time.localtime().tm_sec)>1): #only update once per second
										xbmcgui.Window(self.dp_id).setProperty('last_update',str(time.localtime().tm_sec)) #Update dp global last update
										if isinstance(rom.get('filesize'),int):
											if bytes_per_sec>1 and bytes_per_sec<1e11:
												self.dp.update(percent_complete,'{}[CR]{} / {}[CR]{}/s'.format(rom.get('filename'),self.bytes_to_string_size(current_size),self.bytes_to_string_size(rom.get('filesize')),self.bytes_to_string_size(bytes_per_sec)))
											else:
												self.dp.update(percent_complete,'{}[CR]{} / {}'.format(rom.get('filename'),self.bytes_to_string_size(current_size),self.bytes_to_string_size(rom.get('filesize'))))
										else: #Unknown total filesize
											if bytes_per_sec>1 and bytes_per_sec<1e11: #Check for a sane xfer rate
												self.dp.update(percent_complete,'{}[CR]{}[CR]{}/s'.format(rom.get('filename'),self.bytes_to_string_size(current_size),self.bytes_to_string_size(bytes_per_sec)))
											else:
												self.dp.update(percent_complete,'{}[CR]{}'.format(rom.get('filename'),self.bytes_to_string_size(current_size)))
					if size<1:
						result['success'] = False
						result['download_size'] = size
						result['message'] = 'Download error[CR]Archive returned file size of 0'
						xbmc.log(msg='IAGL:  Chunk {} downloading failed.  Archive returned an empty file'.format(thread_id),level=xbmc.LOGDEBUG)
					else:
						result['success'] = True
						result['download_size'] = size
						result['message'] = 'Download completed'
						result['chunk_filename'] = chunk_filename
						xbmc.log(msg='IAGL:  Chunk {} download complete.  File size {}'.format(thread_id,size),level=xbmc.LOGDEBUG)
				except requests.exceptions.RequestException as rexc:
					result['success'] = False
					if isinstance(rexc.response.status_code,int):
						if rexc.response.status_code == 403:
							result['message'] = 'Download Request error[CR]Archive requires login'
						else:
							result['message'] = 'Download Request error {}[CR]File not available'.format(r.status_code)
					else:
						result['message'] = 'Download Request error[CR]File not available or Archive requires login'
					xbmc.log(msg='IAGL:  Download request exception for {}.  Request Exception {}'.format(rom.get('url'),rexc),level=xbmc.LOGERROR)
					self.delete_file(chunk_filename)
				except requests.exceptions.HTTPError as hexc:
					result['success'] = False
					result['message'] = 'Download HTTP error[CR]{}'.format(hexc)
					xbmc.log(msg='IAGL:  Download request exception for {}.  HTTP Exception {}'.format(rom.get('url'),hexc),level=xbmc.LOGERROR)
					self.delete_file(chunk_filename)
				except requests.exceptions.ConnectionError as cexc:
					result['success'] = False
					result['message'] = 'Download Connection error[CR]{}'.format(cexc)
					xbmc.log(msg='IAGL:  Download request exception for {}.  Connection Exception {}'.format(rom.get('url'),cexc),level=xbmc.LOGERROR)
					self.delete_file(chunk_filename)
				except requests.exceptions.Timeout as texc:
					result['success'] = False
					result['message'] = 'Download Timeout error[CR]{}'.format(texc)
					xbmc.log(msg='IAGL:  Download request exception for {}.  Timeout Exception {}'.format(rom.get('url'),texc),level=xbmc.LOGERROR)
					self.delete_file(chunk_filename)
				except Exception as exc:
					result['success'] = False
					result['download_size'] = None
					result['message'] = 'Download failed or was cancelled'
					xbmc.log(msg='IAGL:  Download request exception for {}. Exception {}'.format(rom.get('url'),exc),level=xbmc.LOGERROR)
					self.delete_file(chunk_filename)
			else:
				result['success'] = False
				result['download_size'] = None
				result['message'] = 'Download failed or was cancelled'
				self.delete_file(chunk_filename)
			return result

	# 		# # url_in=None,filename_in=None,chunk_filename_in=None,range_in=None,thread_in=None,dp_in=None,dp_description='',total_size=None):
	# 		# chunk_download_status = dict()
	# 		# if url_in and filename_in and chunk_filename_in and range_in and thread_in is not None:
	# 		# 	# chunk_filename = filename_in.parent.joinpath(filename_in.stem+'.{0:0=3d}'.format(thread_in)+filename_in.suffix)
	# 		# 	# xbmc.log(msg='IAGL:  Thread %(num)s downloading %(start)s-%(end)s to %(filename)s'%{'num':thread_in,'start':range_in[0],'end':range_in[-1],'filename':chunk_filename_in.name},level=xbmc.LOGDEBUG)
	# 		# 	try:
	# 		# 		with self.session.get(url_in,headers={'Range':'bytes=%(start)s-%(end)s'%{'start':range_in[0],'end':range_in[-1]}},verify=False,stream=True,timeout=self.timeout) as r:
	# 		# 			r.raise_for_status()
	# 		# 			with xbmcvfs.File(get_dest_as_str(chunk_filename_in),'wb') as game_file:
	# 		# 				size = 0
	# 		# 				last_time = time.time()
	# 		# 				start_time = last_time
	# 		# 				for chunk in r.iter_content(chunk_size=self.chunk_size):
	# 		# 					game_file.write(bytearray(chunk))
	# 		# 					size = size+len(chunk) #chunks may be a different size when streaming
	# 		# 					if dp_in and dp_in.iscanceled():
	# 		# 						raise Exception('User Cancelled Download')
	# 		# 					if dp_in:
	# 		# 						current_size=int(xbmcgui.Window(10101).getProperty('current_size'))+len(chunk) if xbmcgui.Window(10101).getProperty('current_size') else 0
	# 		# 						xbmcgui.Window(10101).setProperty('current_size',str(current_size))
	# 		# 						percent = int(100.0 * (current_size) / (total_size + 1)) #Added 1 byte to avoid div by zero
	# 		# 						now = time.time()
	# 		# 						diff = now - last_time
	# 		# 						bytes_per_sec = current_size/(now - start_time + 0.000001)
	# 		# 						if time.localtime().tm_sec in range(0,60)[thread_in::self.settings.get('download').get('max_threads')] and diff>1: #split up DP updates on any given second to each thread and only update once per second
	# 		# 							last_time = now
	# 		# 							if total_size:
	# 		# 								if bytes_per_sec>1 and bytes_per_sec<1e11: #Check for a sane xfer rate
	# 		# 									dp_in.update(percent,'%(fn)s[CR]%(current_size)s / %(estimated_size)s[CR]%(xfer_speed)s/s'%{'current_size':bytes_to_string_size(current_size),'fn':dp_description,'estimated_size':bytes_to_string_size(total_size),'xfer_speed':bytes_to_string_size(bytes_per_sec)})
	# 		# 								else:
	# 		# 									dp_in.update(percent,'%(fn)s[CR]%(current_size)s / %(estimated_size)s'%{'current_size':bytes_to_string_size(current_size),'fn':dp_description,'estimated_size':bytes_to_string_size(total_size)})
	# 		# 							else:
	# 		# 								if bytes_per_sec>1 and bytes_per_sec<1e11: #Check for a sane xfer rate
	# 		# 									dp_in.update(percent,'%(fn)s[CR]%(current_size)s / Unknown Size[CR]%(xfer_speed)s/s'%{'current_size':bytes_to_string_size(current_size),'fn':dp_description,'xfer_speed':bytes_to_string_size(bytes_per_sec)})
	# 		# 								else:
	# 		# 									dp_in.update(percent,'%(fn)s[CR]%(current_size)s / Unknown Size'%{'current_size':bytes_to_string_size(current_size),'fn':dp_description})
	# 		# 		if size<1:
	# 		# 			chunk_download_status['success'] = False
	# 		# 			chunk_download_status['message'] = 'Download returned file of size 0'
	# 		# 			chunk_download_status['download_size'] = size
	# 		# 			delete_file(chunk_filename_in)
	# 		# 			xbmc.log(msg='IAGL:  Download failed for thread %(num)s, %(url)s.  Archive returned an empty file'%{'num':thread_in,'url':url_in},level=xbmc.LOGERROR)
	# 		# 		else:
	# 		# 			chunk_download_status['success'] = True
	# 		# 			chunk_download_status['message'] = 'Download complete'
	# 		# 			chunk_download_status['file'] = chunk_filename_in
	# 		# 			chunk_download_status['download_size'] = size
	# 		# 			xbmc.log(msg='IAGL:  Download complete for thread %(num)s, %(url)s.  File size %(size)s'%{'num':thread_in,'url':url_in,'size':size},level=xbmc.LOGDEBUG)
	# 		# 	except requests.exceptions.RequestException as rexc:
	# 		# 		chunk_download_status['success'] = False
	# 		# 		if r and r.status_code == 403:
	# 		# 			chunk_download_status['message'] = 'Download Request Exception.  Archive requires login.'
	# 		# 		else:
	# 		# 			chunk_download_status['message'] = 'Download Request Exception.  See Kodi Log.'
	# 		# 		xbmc.log(msg='IAGL:  Download request exception for thread %(num)s, %(url)s.  Request Exception %(exc)s'%{'num':thread_in,'url':url_in,'exc':rexc},level=xbmc.LOGERROR)
	# 		# 		delete_file(chunk_filename_in)
	# 		# 	except requests.exceptions.HTTPError as hexc:
	# 		# 		chunk_download_status['success'] = False
	# 		# 		chunk_download_status['message'] = 'Download HTTP error %(exc)s'%{'exc':hexc}
	# 		# 		xbmc.log(msg='IAGL:  Download HTTP exception for thread %(num)s, %(url)s.  HTTP Exception %(exc)s'%{'num':thread_in,'url':url_in,'exc':hexc},level=xbmc.LOGERROR)
	# 		# 		delete_file(chunk_filename_in)
	# 		# 	except requests.exceptions.ConnectionError as cexc:
	# 		# 		chunk_download_status['success'] = False
	# 		# 		chunk_download_status['message'] = 'Download Connection error %(exc)s'%{'exc':cexc}
	# 		# 		xbmc.log(msg='IAGL:  Download connection exception for thread %(num)s, %(url)s.  Connection Exception %(exc)s'%{'num':thread_in,'url':url_in,'exc':cexc},level=xbmc.LOGERROR)
	# 		# 		delete_file(chunk_filename_in)
	# 		# 	except requests.exceptions.Timeout as texc:
	# 		# 		chunk_download_status['success'] = False
	# 		# 		chunk_download_status['message'] = 'Download Timeout error %(exc)s'%{'exc':texc}
	# 		# 		xbmc.log(msg='IAGL:  Download timeout exception for thread %(num)s, %(url)s.  Timeout Exception %(exc)s'%{'num':thread_in,'url':url_in,'exc':texc},level=xbmc.LOGERROR)
	# 		# 		delete_file(chunk_filename_in)
	# 		# 	except Exception as exc:
	# 		# 		chunk_download_status['success'] = False
	# 		# 		chunk_download_status['download_size'] = None
	# 		# 		chunk_download_status['message'] = 'Download failed or was cancelled'
	# 		# 		xbmc.log(msg='IAGL:  Download exception for thread %(num)s, %(url)s.  Exception %(exc)s'%{'num':thread_in,'url':url_in,'exc':exc},level=xbmc.LOGERROR)
	# 		# 		delete_file(chunk_filename_in)
	# 		# return chunk_download_status
		



	# 		# if url and dest:
	# 		# 	if not self.session:
	# 		# 		self.login()
	# 		# 	if self.settings.get('archive_org') and self.settings.get('archive_org').get('username') and self.settings.get('archive_org').get('password') and self.settings.get('archive_org').get('enabled'):
	# 		# 		xbmc.log(msg='IAGL:  Attempting download with login credentials',level=xbmc.LOGDEBUG)
	# 		# 	else:
	# 		# 		xbmc.log(msg='IAGL:  Attempting download without login credentials',level=xbmc.LOGDEBUG)
	# 		# 	xbmc.log(msg='IAGL:  URL: %(value)s'%{'value':url},level=xbmc.LOGDEBUG)
	# 		# 	xbmc.log(msg='IAGL:  Dest: %(value)s'%{'value':dest},level=xbmc.LOGDEBUG)
	# 		# 	if show_progress:
	# 		# 		dp = xbmcgui.DialogProgress()
	# 		# 		description = next(iter([str(x) for x in [dest.name,url_unquote(os.path.split(url)[-1].split('%2F')[-1])] if x]),'Unknown File')
	# 		# 		dp.create(loc_str(30376),description)
	# 		# 		dp.update(0,description)
	# 		# 	try:
	# 		# 		with self.session.get(url,verify=False,stream=True,timeout=self.timeout) as self.r:
	# 		# 			self.r.raise_for_status()
	# 		# 			if self.r.headers.get('Content-length') and self.r.headers.get('Content-length').isdigit():
	# 		# 				content_length=max(int(self.r.headers.get('Content-length')),0)
	# 		# 			else:
	# 		# 				content_length = None
	# 		# 	except Exception as exc:
	# 		# 		xbmc.log(msg='IAGL:  Download exception for %(url)s.  Exception %(exc)s'%{'url':url,'exc':exc},level=xbmc.LOGERROR)
	# 		# 		content_length = None
	# 		# 	if content_length and content_length>self.min_file_size and self.settings.get('download').get('max_threads')>1 and max([x for x in range(1,self.settings.get('download').get('max_threads')+1) if content_length/x>self.min_file_size])>1: #The filesize was found in the header, and the filesize is larger than the min, so use multiple threads
	# 		# 		xbmcgui.Window(10101).setProperty('file_size',str(content_length))
	# 		# 		xbmcgui.Window(10101).setProperty('current_size',str(0))
	# 		# 		num_workers = max([x for x in range(1,self.settings.get('download').get('max_threads')+1) if content_length/x>self.min_file_size]) #Determine max number of workers to use that will create chunks as small as ~2MB in size, up to max threads
	# 		# 		xbmc.log(msg='IAGL:  Multi-threaded download initiated for %(url)s, file size %(file_size)s using %(num_workers)s workers'%{'url':url,'file_size':content_length,'num_workers':num_workers},level=xbmc.LOGDEBUG)
	# 		# 		threaded_ranges = [list((x[0],x[-1])) for x in calculate_chunk_range(content_length,num_workers)] #Generate the byte ranges for each worker
	# 		# 		threaded_ranges[-1][-1] = content_length #Last byte in last range is off by 1 sometimes, so ensure the last range is up to the last byte					
	# 		# 		chunk_filenames = [dest.parent.joinpath(dest.stem+'.{0:0=3d}'.format(ii)+dest.suffix) for ii,rr in enumerate(threaded_ranges)] #Define chunk filenames in order
	# 		# 		executor = ThreadPoolExecutor(max_workers=num_workers)
	# 		# 		futures=[executor.submit(self.download_chunk,url_in=url,filename_in=dest,chunk_filename_in=chunk_filenames[ii],range_in=rr,thread_in=ii,dp_in=dp,dp_description=description,total_size=content_length) for ii,rr in enumerate(threaded_ranges)]
	# 		# 		futures_results = [f.result() for f in futures]
	# 		# 		if all([x.get('success') for x in futures_results]):
	# 		# 			if combine_chunks(files_in=sorted([x.get('file') for x in futures_results]),dest_file=dest):
	# 		# 				self.download_status['success'] = True
	# 		# 				self.download_status['download_size'] = sum([x.get('download_size') for x in futures_results])
	# 		# 				self.download_status['message'] = 'Download complete'					
	# 		# 			else:
	# 		# 				self.download_status['success'] = False
	# 		# 				self.download_status['download_size'] = None
	# 		# 				self.download_status['message'] = 'Chunk file merge failed'
	# 		# 				delete_file(dest)
	# 		# 				delete_results = [delete_file(xx) for xx in chunk_filenames]
	# 		# 		else:
	# 		# 			self.download_status['success'] = False
	# 		# 			self.download_status['download_size'] = None
	# 		# 			self.download_status['message'] = [x.get('message') for x in futures_results if not x.get('success')][0] #Use the first failure reason
	# 		# 			delete_file(dest)
	# 		# 			delete_results=[delete_file(xx) for xx in chunk_filenames]
	# 		# 		#Clean up
	# 		# 		xbmcgui.Window(10101).clearProperty('file_size')
	# 		# 		xbmcgui.Window(10101).clearProperty('current_size')
	# 		# 		dp.close()
	# 		# 		del dp
	# 		# 		return self.download_status

	# 		# 	else: #Non threaded download because the size of the file is either too small, or the size of the file could not be determined
	# 		# 		xbmc.log(msg='IAGL:  Single-threaded download initiated for %(url)s. File size %(file_size)s'%{'url':url,'file_size':(content_length or 'Unknown')},level=xbmc.LOGDEBUG)
	# 		# 		try:
	# 		# 			with self.session.get(url,verify=False,stream=True,timeout=self.timeout) as self.r:
	# 		# 				self.r.raise_for_status()
	# 		# 				filesize = next(iter([int(x) for x in [self.r.headers.get('Content-length'),est_size] if x]),0)
	# 		# 				filesize_str = bytes_to_string_size(filesize)
	# 		# 				with xbmcvfs.File(get_dest_as_str(dest),'wb') as game_file:
	# 		# 					size = 0
	# 		# 					last_time = time.time()
	# 		# 					start_time = last_time
	# 		# 					for chunk in self.r.iter_content(chunk_size=self.chunk_size):
	# 		# 						game_file.write(bytearray(chunk))
	# 		# 						if show_progress and dp.iscanceled():
	# 		# 							dp.close()
	# 		# 							raise Exception('User Cancelled Download')
	# 		# 						if show_progress:
	# 		# 							size = size+len(chunk) #chunks may be a different size when streaming
	# 		# 							percent = int(100.0 * size / (filesize + 1)) #Added 1 byte to avoid div by zero
	# 		# 							now = time.time()
	# 		# 							diff = now - last_time
	# 		# 							bytes_per_sec = size/(now - start_time + 0.000001)
	# 		# 							if diff > 1: #Only show progress updates in 1 second or greater intervals
	# 		# 								last_time = now
	# 		# 								if filesize:
	# 		# 									if bytes_per_sec>1 and bytes_per_sec<1e11: #Check for a sane xfer rate
	# 		# 										dp.update(percent,'%(fn)s[CR]%(current_size)s / %(estimated_size)s[CR]%(xfer_speed)s/s'%{'current_size':bytes_to_string_size(size),'fn':description,'estimated_size':filesize_str,'xfer_speed':bytes_to_string_size(bytes_per_sec)})
	# 		# 									else:
	# 		# 										dp.update(percent,'%(fn)s[CR]%(current_size)s / %(estimated_size)s'%{'current_size':bytes_to_string_size(size),'fn':description,'estimated_size':filesize_str})
	# 		# 								else:
	# 		# 									if bytes_per_sec>1 and bytes_per_sec<1e11: #Check for a sane xfer rate
	# 		# 										dp.update(percent,'%(fn)s[CR]%(current_size)s / Unknown Size[CR]%(xfer_speed)s/s'%{'current_size':bytes_to_string_size(size),'fn':description,'xfer_speed':bytes_to_string_size(bytes_per_sec)})
	# 		# 									else:
	# 		# 										dp.update(percent,'%(fn)s[CR]%(current_size)s / Unknown Size'%{'current_size':bytes_to_string_size(size),'fn':description})
	# 		# 			if size<1:
	# 		# 				self.download_status['success'] = False
	# 		# 				self.download_status['message'] = 'Download returned file of size 0'
	# 		# 				self.download_status['download_size'] = size
	# 		# 				delete_file(dest)
	# 		# 				xbmc.log(msg='IAGL:  Download failed for %(url)s.  Archive returned an empty file'%{'url':url,'size':size},level=xbmc.LOGERROR)
	# 		# 			else:
	# 		# 				self.download_status['success'] = True
	# 		# 				self.download_status['message'] = 'Download complete'
	# 		# 				self.download_status['download_size'] = size
	# 		# 				xbmc.log(msg='IAGL:  Download complete for %(url)s.  File size %(size)s'%{'url':url,'size':size},level=xbmc.LOGINFO)
	# 		# 		except requests.exceptions.RequestException as rexc:
	# 		# 			self.download_status['success'] = False
	# 		# 			if self.r and self.r.status_code == 403:
	# 		# 				self.download_status['message'] = 'Download Request Exception.  Archive requires login.'
	# 		# 			else:
	# 		# 				self.download_status['message'] = 'Download Request Exception.  See Kodi Log.'
	# 		# 			xbmc.log(msg='IAGL:  Download request exception for %(url)s.  Request Exception %(exc)s'%{'url':url,'exc':rexc},level=xbmc.LOGERROR)
	# 		# 			delete_file(dest)
	# 		# 		except requests.exceptions.HTTPError as hexc:
	# 		# 			self.download_status['success'] = False
	# 		# 			self.download_status['message'] = 'Download HTTP error %(exc)s'%{'exc':hexc}
	# 		# 			xbmc.log(msg='IAGL:  Download HTTP exception for %(url)s.  HTTP Exception %(exc)s'%{'url':url,'exc':hexc},level=xbmc.LOGERROR)
	# 		# 			delete_file(dest)
	# 		# 		except requests.exceptions.ConnectionError as cexc:
	# 		# 			self.download_status['success'] = False
	# 		# 			self.download_status['message'] = 'Download Connection error %(exc)s'%{'exc':cexc}
	# 		# 			xbmc.log(msg='IAGL:  Download connection exception for %(url)s.  Connection Exception %(exc)s'%{'url':url,'exc':cexc},level=xbmc.LOGERROR)
	# 		# 			delete_file(dest)
	# 		# 		except requests.exceptions.Timeout as texc:
	# 		# 			self.download_status['success'] = False
	# 		# 			self.download_status['message'] = 'Download Timeout error %(exc)s'%{'exc':texc}
	# 		# 			xbmc.log(msg='IAGL:  Download timeout exception for %(url)s.  Timeout Exception %(exc)s'%{'url':url,'exc':texc},level=xbmc.LOGERROR)
	# 		# 			delete_file(dest)
	# 		# 		except Exception as exc:
	# 		# 			self.download_status['success'] = False
	# 		# 			self.download_status['download_size'] = None
	# 		# 			self.download_status['message'] = 'Download failed or was cancelled'
	# 		# 			xbmc.log(msg='IAGL:  Download exception for %(url)s.  Exception %(exc)s'%{'url':url,'exc':exc},level=xbmc.LOGERROR)
	# 		# 			delete_file(dest)
	# 		# 		dp.close()
	# 		# 		del dp
	# 		# 		return self.download_status
	# 		# else:
	# 		# 	xbmc.log(msg='IAGL:  Badly formed download request.  URL %(url)s, Dest %(dest)s'%{'url':url,'dest':dest},level=xbmc.LOGDEBUG)
	# 		# 	return None
			

	# 		# if self.settings.get('archive_org') and self.settings.get('archive_org').get('username') and self.settings.get('archive_org').get('password') and self.settings.get('archive_org').get('enabled'):
	# 		# 	if show_progress:
	# 		# 		current_dialog = xbmcgui.Dialog()
	# 		# 		current_dialog.notification(loc_str(30377),loc_str(30378),xbmcgui.NOTIFICATION_INFO,self.settings.get('notifications').get('background_notification_time'),sound=False)
	# 		# 	if get_mem_cache('iagl_archive_org_login'):
	# 		# 		self.cookie = get_mem_cache('iagl_archive_org_login')
	# 		# 		xbmc.log(msg='IAGL:  Checking cached login credentials for archive.org',level=xbmc.LOGDEBUG)
	# 		# 		for k,v in self.cookie.items():
	# 		# 			self.session.cookies.set(k,v,domain='.archive.org')
	# 		# 		try:
	# 		# 			with self.session.get(self.check_account_url,verify=False,timeout=self.timeout) as self.r:
	# 		# 				self.r.raise_for_status()
	# 		# 				if self.r.ok and '<title>cannot find account</title>' not in self.r.text.lower():
	# 		# 					self.logged_in = True
	# 		# 					xbmc.log(msg='IAGL:  Login check passed for archive.org',level=xbmc.LOGDEBUG)
	# 		# 				elif self.r.ok and '<title>cannot find account</title>' in self.r.text.lower():
	# 		# 					self.logged_in = False
	# 		# 					xbmc.log(msg='IAGL:  First Login check failed for archive.org, attempting to re-login',level=xbmc.LOGDEBUG)
	# 		# 					clear_mem_cache('iagl_archive_org_login')
	# 		# 					self.login()
	# 		# 				else:
	# 		# 					clear_mem_cache('iagl_archive_org_login')
	# 		# 					xbmc.log(msg='IAGL:  Login check failed for archive.org because the login page could not be accessed.  Status code %(code)s'%{'code':self.r.status_code},level=xbmc.LOGERROR)
	# 		# 		except Exception as exc:
	# 		# 			xbmc.log(msg='IAGL:  Login exception for %(url)s.  Exception %(exc)s'%{'url':self.check_account_url,'exc':exc},level=xbmc.LOGERROR)
	# 		# 	else:
	# 		# 		try:
	# 		# 			with self.session.get(self.login_url,verify=False,timeout=self.timeout) as self.r:
	# 		# 				self.r.raise_for_status()
	# 		# 		except Exception as exc:
	# 		# 			xbmc.log(msg='IAGL:  Login exception for %(url)s.  Exception %(exc)s'%{'url':self.check_account_url,'exc':exc},level=xbmc.LOGERROR)
	# 		# 		try:
	# 		# 			with self.session.post(self.login_url,verify=False,timeout=self.timeout,data={'username':str(self.settings.get('archive_org').get('username')),'password':str(self.settings.get('archive_org').get('password')),'remember':'CHECKED','action':'login','submit': 'Log+in'},allow_redirects=True) as self.r:
	# 		# 				self.r.raise_for_status()
	# 		# 				if self.r.ok and dict(self.r.headers) and dict(self.r.headers).get('Set-Cookie'):
	# 		# 					hcookie = {z.split('=')[0].strip():z.split('=')[-1].strip() for z in [y.split(',')[-1].strip() for y in [x.strip() for x in dict(self.r.headers).get('Set-Cookie').split(';')]] if '=' in z}
	# 		# 					if hcookie.get('logged-in-sig') and hcookie.get('logged-in-user'):
	# 		# 						self.cookie = {'logged-in-user':hcookie.get('logged-in-user'),'logged-in-sig':hcookie.get('logged-in-sig'),'Max-Age':hcookie.get('Max-Age')}
	# 		# 						set_mem_cache('iagl_archive_org_login',self.cookie)
	# 		# 						self.logged_in = True
	# 		# 						xbmc.log(msg='IAGL:  Login to archive.org succeeded with the supplied user email and password',level=xbmc.LOGDEBUG)
	# 		# 					else:
	# 		# 						self.cookie = None
	# 		# 						self.logged_in = False
	# 		# 						xbmc.log(msg='IAGL:  Login to archive.org failed with the supplied user email and password',level=xbmc.LOGERROR)
	# 		# 				else:
	# 		# 					self.cookie = None
	# 		# 					self.logged_in = False
	# 		# 					xbmc.log(msg='IAGL:  Login failed to archive.org because the login page could not be accessed',level=xbmc.LOGERROR)
	# 		# 		except Exception as exc:
	# 		# 			xbmc.log(msg='IAGL:  Login exception for %(url)s.  Exception %(exc)s'%{'url':self.check_account_url,'exc':exc},level=xbmc.LOGERROR)
	# 		# 	if show_progress:
	# 		# 		xbmc.executebuiltin('Dialog.Close(notification,true)')
	# 		# 		check_and_close_notification()
	# 		# 		del current_dialog
	# 		# else:
	# 		# 	self.cookie = None
	# 		# 	self.logged_in = False
	# 		# 	xbmc.log(msg='IAGL:  Login information was not provided in addon settings',level=xbmc.LOGDEBUG)

	# 	def download_chunk(self,url_in=None,filename_in=None,chunk_filename_in=None,range_in=None,thread_in=None,dp_in=None,dp_description='',total_size=None):
	# 		chunk_download_status = dict()
	# 		if url_in and filename_in and chunk_filename_in and range_in and thread_in is not None:
	# 			# chunk_filename = filename_in.parent.joinpath(filename_in.stem+'.{0:0=3d}'.format(thread_in)+filename_in.suffix)
	# 			xbmc.log(msg='IAGL:  Thread %(num)s downloading %(start)s-%(end)s to %(filename)s'%{'num':thread_in,'start':range_in[0],'end':range_in[-1],'filename':chunk_filename_in.name},level=xbmc.LOGDEBUG)
	# 			try:
	# 				with self.session.get(url_in,headers={'Range':'bytes=%(start)s-%(end)s'%{'start':range_in[0],'end':range_in[-1]}},verify=False,stream=True,timeout=self.timeout) as r:
	# 					r.raise_for_status()
	# 					with xbmcvfs.File(get_dest_as_str(chunk_filename_in),'wb') as game_file:
	# 						size = 0
	# 						last_time = time.time()
	# 						start_time = last_time
	# 						for chunk in r.iter_content(chunk_size=self.chunk_size):
	# 							game_file.write(bytearray(chunk))
	# 							size = size+len(chunk) #chunks may be a different size when streaming
	# 							if dp_in and dp_in.iscanceled():
	# 								raise Exception('User Cancelled Download')
	# 							if dp_in:
	# 								current_size=int(xbmcgui.Window(10101).getProperty('current_size'))+len(chunk) if xbmcgui.Window(10101).getProperty('current_size') else 0
	# 								xbmcgui.Window(10101).setProperty('current_size',str(current_size))
	# 								percent = int(100.0 * (current_size) / (total_size + 1)) #Added 1 byte to avoid div by zero
	# 								now = time.time()
	# 								diff = now - last_time
	# 								bytes_per_sec = current_size/(now - start_time + 0.000001)
	# 								if time.localtime().tm_sec in range(0,60)[thread_in::self.settings.get('download').get('max_threads')] and diff>1: #split up DP updates on any given second to each thread and only update once per second
	# 									last_time = now
	# 									if total_size:
	# 										if bytes_per_sec>1 and bytes_per_sec<1e11: #Check for a sane xfer rate
	# 											dp_in.update(percent,'%(fn)s[CR]%(current_size)s / %(estimated_size)s[CR]%(xfer_speed)s/s'%{'current_size':bytes_to_string_size(current_size),'fn':dp_description,'estimated_size':bytes_to_string_size(total_size),'xfer_speed':bytes_to_string_size(bytes_per_sec)})
	# 										else:
	# 											dp_in.update(percent,'%(fn)s[CR]%(current_size)s / %(estimated_size)s'%{'current_size':bytes_to_string_size(current_size),'fn':dp_description,'estimated_size':bytes_to_string_size(total_size)})
	# 									else:
	# 										if bytes_per_sec>1 and bytes_per_sec<1e11: #Check for a sane xfer rate
	# 											dp_in.update(percent,'%(fn)s[CR]%(current_size)s / Unknown Size[CR]%(xfer_speed)s/s'%{'current_size':bytes_to_string_size(current_size),'fn':dp_description,'xfer_speed':bytes_to_string_size(bytes_per_sec)})
	# 										else:
	# 											dp_in.update(percent,'%(fn)s[CR]%(current_size)s / Unknown Size'%{'current_size':bytes_to_string_size(current_size),'fn':dp_description})
	# 				if size<1:
	# 					chunk_download_status['success'] = False
	# 					chunk_download_status['message'] = 'Download returned file of size 0'
	# 					chunk_download_status['download_size'] = size
	# 					delete_file(chunk_filename_in)
	# 					xbmc.log(msg='IAGL:  Download failed for thread %(num)s, %(url)s.  Archive returned an empty file'%{'num':thread_in,'url':url_in},level=xbmc.LOGERROR)
	# 				else:
	# 					chunk_download_status['success'] = True
	# 					chunk_download_status['message'] = 'Download complete'
	# 					chunk_download_status['file'] = chunk_filename_in
	# 					chunk_download_status['download_size'] = size
	# 					xbmc.log(msg='IAGL:  Download complete for thread %(num)s, %(url)s.  File size %(size)s'%{'num':thread_in,'url':url_in,'size':size},level=xbmc.LOGDEBUG)
	# 			except requests.exceptions.RequestException as rexc:
	# 				chunk_download_status['success'] = False
	# 				if r and r.status_code == 403:
	# 					chunk_download_status['message'] = 'Download Request Exception.  Archive requires login.'
	# 				else:
	# 					chunk_download_status['message'] = 'Download Request Exception.  See Kodi Log.'
	# 				xbmc.log(msg='IAGL:  Download request exception for thread %(num)s, %(url)s.  Request Exception %(exc)s'%{'num':thread_in,'url':url_in,'exc':rexc},level=xbmc.LOGERROR)
	# 				delete_file(chunk_filename_in)
	# 			except requests.exceptions.HTTPError as hexc:
	# 				chunk_download_status['success'] = False
	# 				chunk_download_status['message'] = 'Download HTTP error %(exc)s'%{'exc':hexc}
	# 				xbmc.log(msg='IAGL:  Download HTTP exception for thread %(num)s, %(url)s.  HTTP Exception %(exc)s'%{'num':thread_in,'url':url_in,'exc':hexc},level=xbmc.LOGERROR)
	# 				delete_file(chunk_filename_in)
	# 			except requests.exceptions.ConnectionError as cexc:
	# 				chunk_download_status['success'] = False
	# 				chunk_download_status['message'] = 'Download Connection error %(exc)s'%{'exc':cexc}
	# 				xbmc.log(msg='IAGL:  Download connection exception for thread %(num)s, %(url)s.  Connection Exception %(exc)s'%{'num':thread_in,'url':url_in,'exc':cexc},level=xbmc.LOGERROR)
	# 				delete_file(chunk_filename_in)
	# 			except requests.exceptions.Timeout as texc:
	# 				chunk_download_status['success'] = False
	# 				chunk_download_status['message'] = 'Download Timeout error %(exc)s'%{'exc':texc}
	# 				xbmc.log(msg='IAGL:  Download timeout exception for thread %(num)s, %(url)s.  Timeout Exception %(exc)s'%{'num':thread_in,'url':url_in,'exc':texc},level=xbmc.LOGERROR)
	# 				delete_file(chunk_filename_in)
	# 			except Exception as exc:
	# 				chunk_download_status['success'] = False
	# 				chunk_download_status['download_size'] = None
	# 				chunk_download_status['message'] = 'Download failed or was cancelled'
	# 				xbmc.log(msg='IAGL:  Download exception for thread %(num)s, %(url)s.  Exception %(exc)s'%{'num':thread_in,'url':url_in,'exc':exc},level=xbmc.LOGERROR)
	# 				delete_file(chunk_filename_in)
	# 		return chunk_download_status

	# 	# def download(self,url=None,dest=None,est_size=None,show_progress=True):
	# 	# 	if url and dest:
	# 	# 		if not self.session:
	# 	# 			self.login()
	# 	# 		if self.settings.get('archive_org') and self.settings.get('archive_org').get('username') and self.settings.get('archive_org').get('password') and self.settings.get('archive_org').get('enabled'):
	# 	# 			xbmc.log(msg='IAGL:  Attempting download with login credentials',level=xbmc.LOGDEBUG)
	# 	# 		else:
	# 	# 			xbmc.log(msg='IAGL:  Attempting download without login credentials',level=xbmc.LOGDEBUG)
	# 	# 		xbmc.log(msg='IAGL:  URL: %(value)s'%{'value':url},level=xbmc.LOGDEBUG)
	# 	# 		xbmc.log(msg='IAGL:  Dest: %(value)s'%{'value':dest},level=xbmc.LOGDEBUG)
	# 	# 		if show_progress:
	# 	# 			dp = xbmcgui.DialogProgress()
	# 	# 			description = next(iter([str(x) for x in [dest.name,url_unquote(os.path.split(url)[-1].split('%2F')[-1])] if x]),'Unknown File')
	# 	# 			dp.create(loc_str(30376),description)
	# 	# 			dp.update(0,description)
	# 	# 		try:
	# 	# 			with self.session.get(url,verify=False,stream=True,timeout=self.timeout) as self.r:
	# 	# 				self.r.raise_for_status()
	# 	# 				if self.r.headers.get('Content-length') and self.r.headers.get('Content-length').isdigit():
	# 	# 					content_length=max(int(self.r.headers.get('Content-length')),0)
	# 	# 				else:
	# 	# 					content_length = None
	# 	# 		except Exception as exc:
	# 	# 			xbmc.log(msg='IAGL:  Download exception for %(url)s.  Exception %(exc)s'%{'url':url,'exc':exc},level=xbmc.LOGERROR)
	# 	# 			content_length = None
	# 	# 		if content_length and content_length>self.min_file_size and self.settings.get('download').get('max_threads')>1 and max([x for x in range(1,self.settings.get('download').get('max_threads')+1) if content_length/x>self.min_file_size])>1: #The filesize was found in the header, and the filesize is larger than the min, so use multiple threads
	# 	# 			xbmcgui.Window(10101).setProperty('file_size',str(content_length))
	# 	# 			xbmcgui.Window(10101).setProperty('current_size',str(0))
	# 	# 			num_workers = max([x for x in range(1,self.settings.get('download').get('max_threads')+1) if content_length/x>self.min_file_size]) #Determine max number of workers to use that will create chunks as small as ~2MB in size, up to max threads
	# 	# 			xbmc.log(msg='IAGL:  Multi-threaded download initiated for %(url)s, file size %(file_size)s using %(num_workers)s workers'%{'url':url,'file_size':content_length,'num_workers':num_workers},level=xbmc.LOGDEBUG)
	# 	# 			threaded_ranges = [list((x[0],x[-1])) for x in calculate_chunk_range(content_length,num_workers)] #Generate the byte ranges for each worker
	# 	# 			threaded_ranges[-1][-1] = content_length #Last byte in last range is off by 1 sometimes, so ensure the last range is up to the last byte					
	# 	# 			chunk_filenames = [dest.parent.joinpath(dest.stem+'.{0:0=3d}'.format(ii)+dest.suffix) for ii,rr in enumerate(threaded_ranges)] #Define chunk filenames in order
	# 	# 			executor = ThreadPoolExecutor(max_workers=num_workers)
	# 	# 			futures=[executor.submit(self.download_chunk,url_in=url,filename_in=dest,chunk_filename_in=chunk_filenames[ii],range_in=rr,thread_in=ii,dp_in=dp,dp_description=description,total_size=content_length) for ii,rr in enumerate(threaded_ranges)]
	# 	# 			futures_results = [f.result() for f in futures]
	# 	# 			if all([x.get('success') for x in futures_results]):
	# 	# 				if combine_chunks(files_in=sorted([x.get('file') for x in futures_results]),dest_file=dest):
	# 	# 					self.download_status['success'] = True
	# 	# 					self.download_status['download_size'] = sum([x.get('download_size') for x in futures_results])
	# 	# 					self.download_status['message'] = 'Download complete'					
	# 	# 				else:
	# 	# 					self.download_status['success'] = False
	# 	# 					self.download_status['download_size'] = None
	# 	# 					self.download_status['message'] = 'Chunk file merge failed'
	# 	# 					delete_file(dest)
	# 	# 					delete_results = [delete_file(xx) for xx in chunk_filenames]
	# 	# 			else:
	# 	# 				self.download_status['success'] = False
	# 	# 				self.download_status['download_size'] = None
	# 	# 				self.download_status['message'] = [x.get('message') for x in futures_results if not x.get('success')][0] #Use the first failure reason
	# 	# 				delete_file(dest)
	# 	# 				delete_results=[delete_file(xx) for xx in chunk_filenames]
	# 	# 			#Clean up
	# 	# 			xbmcgui.Window(10101).clearProperty('file_size')
	# 	# 			xbmcgui.Window(10101).clearProperty('current_size')
	# 	# 			dp.close()
	# 	# 			del dp
	# 	# 			return self.download_status

	# 	# 		else: #Non threaded download because the size of the file is either too small, or the size of the file could not be determined
	# 	# 			xbmc.log(msg='IAGL:  Single-threaded download initiated for %(url)s. File size %(file_size)s'%{'url':url,'file_size':(content_length or 'Unknown')},level=xbmc.LOGDEBUG)
	# 	# 			try:
	# 	# 				with self.session.get(url,verify=False,stream=True,timeout=self.timeout) as self.r:
	# 	# 					self.r.raise_for_status()
	# 	# 					filesize = next(iter([int(x) for x in [self.r.headers.get('Content-length'),est_size] if x]),0)
	# 	# 					filesize_str = bytes_to_string_size(filesize)
	# 	# 					with xbmcvfs.File(get_dest_as_str(dest),'wb') as game_file:
	# 	# 						size = 0
	# 	# 						last_time = time.time()
	# 	# 						start_time = last_time
	# 	# 						for chunk in self.r.iter_content(chunk_size=self.chunk_size):
	# 	# 							game_file.write(bytearray(chunk))
	# 	# 							if show_progress and dp.iscanceled():
	# 	# 								dp.close()
	# 	# 								raise Exception('User Cancelled Download')
	# 	# 							if show_progress:
	# 	# 								size = size+len(chunk) #chunks may be a different size when streaming
	# 	# 								percent = int(100.0 * size / (filesize + 1)) #Added 1 byte to avoid div by zero
	# 	# 								now = time.time()
	# 	# 								diff = now - last_time
	# 	# 								bytes_per_sec = size/(now - start_time + 0.000001)
	# 	# 								if diff > 1: #Only show progress updates in 1 second or greater intervals
	# 	# 									last_time = now
	# 	# 									if filesize:
	# 	# 										if bytes_per_sec>1 and bytes_per_sec<1e11: #Check for a sane xfer rate
	# 	# 											dp.update(percent,'%(fn)s[CR]%(current_size)s / %(estimated_size)s[CR]%(xfer_speed)s/s'%{'current_size':bytes_to_string_size(size),'fn':description,'estimated_size':filesize_str,'xfer_speed':bytes_to_string_size(bytes_per_sec)})
	# 	# 										else:
	# 	# 											dp.update(percent,'%(fn)s[CR]%(current_size)s / %(estimated_size)s'%{'current_size':bytes_to_string_size(size),'fn':description,'estimated_size':filesize_str})
	# 	# 									else:
	# 	# 										if bytes_per_sec>1 and bytes_per_sec<1e11: #Check for a sane xfer rate
	# 	# 											dp.update(percent,'%(fn)s[CR]%(current_size)s / Unknown Size[CR]%(xfer_speed)s/s'%{'current_size':bytes_to_string_size(size),'fn':description,'xfer_speed':bytes_to_string_size(bytes_per_sec)})
	# 	# 										else:
	# 	# 											dp.update(percent,'%(fn)s[CR]%(current_size)s / Unknown Size'%{'current_size':bytes_to_string_size(size),'fn':description})
	# 	# 				if size<1:
	# 	# 					self.download_status['success'] = False
	# 	# 					self.download_status['message'] = 'Download returned file of size 0'
	# 	# 					self.download_status['download_size'] = size
	# 	# 					delete_file(dest)
	# 	# 					xbmc.log(msg='IAGL:  Download failed for %(url)s.  Archive returned an empty file'%{'url':url,'size':size},level=xbmc.LOGERROR)
	# 	# 				else:
	# 	# 					self.download_status['success'] = True
	# 	# 					self.download_status['message'] = 'Download complete'
	# 	# 					self.download_status['download_size'] = size
	# 	# 					xbmc.log(msg='IAGL:  Download complete for %(url)s.  File size %(size)s'%{'url':url,'size':size},level=xbmc.LOGINFO)
	# 	# 			except requests.exceptions.RequestException as rexc:
	# 	# 				self.download_status['success'] = False
	# 	# 				if self.r and self.r.status_code == 403:
	# 	# 					self.download_status['message'] = 'Download Request Exception.  Archive requires login.'
	# 	# 				else:
	# 	# 					self.download_status['message'] = 'Download Request Exception.  See Kodi Log.'
	# 	# 				xbmc.log(msg='IAGL:  Download request exception for %(url)s.  Request Exception %(exc)s'%{'url':url,'exc':rexc},level=xbmc.LOGERROR)
	# 	# 				delete_file(dest)
	# 	# 			except requests.exceptions.HTTPError as hexc:
	# 	# 				self.download_status['success'] = False
	# 	# 				self.download_status['message'] = 'Download HTTP error %(exc)s'%{'exc':hexc}
	# 	# 				xbmc.log(msg='IAGL:  Download HTTP exception for %(url)s.  HTTP Exception %(exc)s'%{'url':url,'exc':hexc},level=xbmc.LOGERROR)
	# 	# 				delete_file(dest)
	# 	# 			except requests.exceptions.ConnectionError as cexc:
	# 	# 				self.download_status['success'] = False
	# 	# 				self.download_status['message'] = 'Download Connection error %(exc)s'%{'exc':cexc}
	# 	# 				xbmc.log(msg='IAGL:  Download connection exception for %(url)s.  Connection Exception %(exc)s'%{'url':url,'exc':cexc},level=xbmc.LOGERROR)
	# 	# 				delete_file(dest)
	# 	# 			except requests.exceptions.Timeout as texc:
	# 	# 				self.download_status['success'] = False
	# 	# 				self.download_status['message'] = 'Download Timeout error %(exc)s'%{'exc':texc}
	# 	# 				xbmc.log(msg='IAGL:  Download timeout exception for %(url)s.  Timeout Exception %(exc)s'%{'url':url,'exc':texc},level=xbmc.LOGERROR)
	# 	# 				delete_file(dest)
	# 	# 			except Exception as exc:
	# 	# 				self.download_status['success'] = False
	# 	# 				self.download_status['download_size'] = None
	# 	# 				self.download_status['message'] = 'Download failed or was cancelled'
	# 	# 				xbmc.log(msg='IAGL:  Download exception for %(url)s.  Exception %(exc)s'%{'url':url,'exc':exc},level=xbmc.LOGERROR)
	# 	# 				delete_file(dest)
	# 	# 			dp.close()
	# 	# 			del dp
	# 	# 			return self.download_status
	# 	# 	else:
	# 	# 		xbmc.log(msg='IAGL:  Badly formed download request.  URL %(url)s, Dest %(dest)s'%{'url':url,'dest':dest},level=xbmc.LOGDEBUG)
	# 	# 		return None

	# 	# def download_old(self,url=None,dest=None,est_size=None,show_progress=True):
	# 	# 	if url and dest:
	# 	# 		if not self.session:
	# 	# 			self.login()
	# 	# 		if self.settings.get('archive_org') and self.settings.get('archive_org').get('username') and self.settings.get('archive_org').get('password') and self.settings.get('archive_org').get('enabled'):
	# 	# 			xbmc.log(msg='IAGL:  Attempting download with login credentials',level=xbmc.LOGDEBUG)
	# 	# 		else:
	# 	# 			xbmc.log(msg='IAGL:  Attempting download without login credentials',level=xbmc.LOGDEBUG)
	# 	# 		xbmc.log(msg='IAGL:  URL: %(value)s'%{'value':url},level=xbmc.LOGDEBUG)
	# 	# 		xbmc.log(msg='IAGL:  Dest: %(value)s'%{'value':dest},level=xbmc.LOGDEBUG)
	# 	# 		if show_progress:
	# 	# 			dp = xbmcgui.DialogProgress()
	# 	# 			description = next(iter([str(x) for x in [dest.name,url_unquote(os.path.split(url)[-1].split('%2F')[-1])] if x]),'Unknown File')
	# 	# 			dp.create(loc_str(30376),description)
	# 	# 			dp.update(0,description)
	# 	# 		try:
	# 	# 			with self.session.get(url,verify=False,stream=True,timeout=self.timeout) as self.r:
	# 	# 				self.r.raise_for_status()
	# 	# 				filesize = next(iter([int(x) for x in [self.r.headers.get('Content-length'),est_size] if x]),0)
	# 	# 				filesize_str = bytes_to_string_size(filesize)
	# 	# 				with xbmcvfs.File(str(dest),'wb') as game_file:
	# 	# 					size = 0
	# 	# 					last_time = time.time()
	# 	# 					for chunk in self.r.iter_content(chunk_size=self.chunk_size):
	# 	# 						game_file.write(bytearray(chunk))
	# 	# 						if show_progress and dp.iscanceled():
	# 	# 							dp.close()
	# 	# 							raise Exception('User Cancelled Download')
	# 	# 						if show_progress:
	# 	# 							size = size+len(chunk) #chunks may be a different size when streaming
	# 	# 							percent = int(100.0 * size / (filesize + 1)) #Added 1 byte to avoid div by zero
	# 	# 							now = time.time()
	# 	# 							diff = now - last_time
	# 	# 							if diff > 1: #Only show progress updates in 1 second or greater intervals
	# 	# 								last_time = now
	# 	# 								if filesize:
	# 	# 									dp.update(percent,'%(fn)s[CR]%(current_size)s / %(estimated_size)s'%{'current_size':bytes_to_string_size(size),'fn':description,'estimated_size':filesize_str})
	# 	# 								else:
	# 	# 									dp.update(percent,'%(fn)s[CR]%(current_size)s / Unknown Size'%{'current_size':bytes_to_string_size(size),'fn':description})
	# 	# 			if size<1:
	# 	# 				self.download_status['success'] = False
	# 	# 				self.download_status['message'] = 'Download returned file of size 0'
	# 	# 				self.download_status['download_size'] = size
	# 	# 				delete_file(str(dest))
	# 	# 				xbmc.log(msg='IAGL:  Download failed for %(url)s.  Archive returned an empty file'%{'url':url,'size':size},level=xbmc.LOGERROR)
	# 	# 			else:
	# 	# 				self.download_status['success'] = True
	# 	# 				self.download_status['message'] = 'Download complete'
	# 	# 				self.download_status['download_size'] = size
	# 	# 				xbmc.log(msg='IAGL:  Download complete for %(url)s.  File size %(size)s'%{'url':url,'size':size},level=xbmc.LOGINFO)
	# 	# 		except requests.exceptions.RequestException as rexc:
	# 	# 			self.download_status['success'] = False
	# 	# 			if self.r and self.r.status_code == 403:
	# 	# 				self.download_status['message'] = 'Download Request Exception.  Archive requires login.'
	# 	# 			else:
	# 	# 				self.download_status['message'] = 'Download Request Exception.  See Kodi Log.'
	# 	# 			xbmc.log(msg='IAGL:  Download request exception for %(url)s.  Request Exception %(exc)s'%{'url':url,'exc':rexc},level=xbmc.LOGERROR)
	# 	# 			delete_file(str(dest))
	# 	# 		except requests.exceptions.HTTPError as hexc:
	# 	# 			self.download_status['success'] = False
	# 	# 			self.download_status['message'] = 'Download HTTP error %(exc)s'%{'exc':hexc}
	# 	# 			xbmc.log(msg='IAGL:  Download HTTP exception for %(url)s.  HTTP Exception %(exc)s'%{'url':url,'exc':hexc},level=xbmc.LOGERROR)
	# 	# 			delete_file(str(dest))
	# 	# 		except requests.exceptions.ConnectionError as cexc:
	# 	# 			self.download_status['success'] = False
	# 	# 			self.download_status['message'] = 'Download Connection error %(exc)s'%{'exc':cexc}
	# 	# 			xbmc.log(msg='IAGL:  Download connection exception for %(url)s.  Connection Exception %(exc)s'%{'url':url,'exc':cexc},level=xbmc.LOGERROR)
	# 	# 			delete_file(str(dest))
	# 	# 		except requests.exceptions.Timeout as texc:
	# 	# 			self.download_status['success'] = False
	# 	# 			self.download_status['message'] = 'Download Timeout error %(exc)s'%{'exc':texc}
	# 	# 			xbmc.log(msg='IAGL:  Download timeout exception for %(url)s.  Timeout Exception %(exc)s'%{'url':url,'exc':texc},level=xbmc.LOGERROR)
	# 	# 			delete_file(str(dest))
	# 	# 		except Exception as exc:
	# 	# 			self.download_status['success'] = False
	# 	# 			self.download_status['download_size'] = None
	# 	# 			self.download_status['message'] = 'Download failed or was cancelled'
	# 	# 			xbmc.log(msg='IAGL:  Download exception for %(url)s.  Exception %(exc)s'%{'url':url,'exc':exc},level=xbmc.LOGERROR)
	# 	# 			delete_file(str(dest))
	# 	# 		dp.close()
	# 	# 		del dp
	# 	# 		return self.download_status
	# 	# 	else:
	# 	# 		xbmc.log(msg='IAGL:  Badly formed download request.  URL %(url)s, Dest %(dest)s'%{'url':url,'dest':dest},level=xbmc.LOGDEBUG)
	# 	# 		return None

	# class local_source(object):
	# 	def __init__(self,settings=dict(),directory=dict(),game_list=dict(),game=dict(),show_progress=False):
	# 		self.settings = settings
	# 		self.directory = directory
	# 		self.game_list = game_list
	# 		self.game = game
	# 		self.download_status = dict()

	# 	def download(self,url=None,dest=None,est_size=None,show_progress=False):
	# 		if url and check_if_file_exists(Path(url_unquote(url))):
	# 			self.download_status['success'] = True
	# 			self.download_status['message'] = 'File was accessible via local filesystem'
	# 			xbmc.log(msg='IAGL:  Game was found to exists on the local filesystem: %(url)s'%{'url':url},level=xbmc.LOGDEBUG)
	# 			self.download_status['updated_dest'] = Path(url_unquote(url))
	# 		elif url and check_if_file_exists(url_unquote(url)):
	# 			self.download_status['success'] = True
	# 			self.download_status['message'] = 'File was accessible via Kodi Source'
	# 			xbmc.log(msg='IAGL:  Game was found to exists at a Kodi Source: %(url)s'%{'url':url},level=xbmc.LOGDEBUG)
	# 			self.download_status['updated_dest'] = url_unquote(url)
	# 		else:
	# 			self.download_status['success'] = False
	# 			self.download_status['message'] = 'File was not accessible'
	# 			xbmc.log(msg='IAGL:  Game was not accessible: %(url)s'%{'url':url},level=xbmc.LOGERROR)
	# 		return self.download_status
	# 		# 	if self.cookies and isinstance(self.cookies,dict):
	# 		# 		domain = self.cookies.get('domain')
	# 		# 		for k,v in self.cookie.items():
	# 		# 			if k!='domain':
	# 		# 				self.session.cookies.set(k,v,domain=domain)
	# 		# 	xbmc.log(msg='IAGL:  Attempting download file',level=xbmc.LOGDEBUG)
	# 		# 	xbmc.log(msg='IAGL:  URL: %(value)s'%{'value':url},level=xbmc.LOGDEBUG)
	# 		# 	xbmc.log(msg='IAGL:  Dest: %(value)s'%{'value':dest},level=xbmc.LOGDEBUG)
	# 		# 	if show_progress:
	# 		# 		dp = xbmcgui.DialogProgress()
	# 		# 		description = next(iter([str(x) for x in [dest.name,url_unquote(os.path.split(url)[-1].split('%2F')[-1])] if x]),'Unknown File')
	# 		# 		dp.create(loc_str(30376),description)
	# 		# 		dp.update(0,description)
	# 		# 	try:
	# 		# 		with self.session.get(url,verify=False,stream=True,timeout=self.timeout,headers=self.header) as self.r:
	# 		# 			self.r.raise_for_status()
	# 		# 			filesize = next(iter([int(x) for x in [self.r.headers.get('Content-length'),est_size] if x]),0)
	# 		# 			filesize_str = bytes_to_string_size(filesize)
	# 		# 			with xbmcvfs.File(str(dest),'wb') as ff:
	# 		# 				size = 0
	# 		# 				last_time = time.time()
	# 		# 				for chunk in self.r.iter_content(chunk_size=self.chunk_size):
	# 		# 					ff.write(bytearray(chunk))
	# 		# 					if show_progress and dp.iscanceled():
	# 		# 						dp.close()
	# 		# 						raise Exception('User Cancelled Download')
	# 		# 					if show_progress:
	# 		# 						size = size+len(chunk) #chunks may be a different size when streaming
	# 		# 						percent = int(100.0 * size / (filesize + 1)) #Added 1 byte to avoid div by zero
	# 		# 						now = time.time()
	# 		# 						diff = now - last_time
	# 		# 						if diff > 1: #Only show progress updates in 1 second or greater intervals
	# 		# 							last_time = now
	# 		# 							if filesize:
	# 		# 								dp.update(percent,'%(fn)s[CR]%(current_size)s / %(estimated_size)s'%{'current_size':bytes_to_string_size(size),'fn':description,'estimated_size':filesize_str})
	# 		# 							else:
	# 		# 								dp.update(percent,'%(fn)s[CR]%(current_size)s / Unknown Size'%{'current_size':bytes_to_string_size(size),'fn':description})
	# 		# 	except requests.exceptions.RequestException as rexc:
	# 		# 		self.download_status['success'] = False
	# 		# 		if self.r.status_code == 403:
	# 		# 			self.download_status['message'] = 'Download Request Exception.  Access is forbidden (login required).'
	# 		# 		else:
	# 		# 			self.download_status['message'] = 'Download Request Exception.  See Kodi Log.'
	# 		# 		xbmc.log(msg='IAGL:  Download request exception for %(url)s.  Request Exception %(exc)s'%{'url':url,'exc':rexc},level=xbmc.LOGERROR)
	# 		# 	except requests.exceptions.HTTPError as hexc:
	# 		# 		self.download_status['success'] = False
	# 		# 		self.download_status['message'] = 'Download HTTP error %(exc)s'%{'exc':hexc}
	# 		# 		xbmc.log(msg='IAGL:  Download HTTP exception for %(url)s.  HTTP Exception %(exc)s'%{'url':url,'exc':hexc},level=xbmc.LOGERROR)
	# 		# 	except requests.exceptions.ConnectionError as cexc:
	# 		# 		self.download_status['success'] = False
	# 		# 		self.download_status['message'] = 'Download Connection error %(exc)s'%{'exc':cexc}
	# 		# 		xbmc.log(msg='IAGL:  Download connection exception for %(url)s.  Connection Exception %(exc)s'%{'url':url,'exc':cexc},level=xbmc.LOGERROR)
	# 		# 	except requests.exceptions.Timeout as texc:
	# 		# 		self.download_status['success'] = False
	# 		# 		self.download_status['message'] = 'Download Timeout error %(exc)s'%{'exc':texc}
	# 		# 		xbmc.log(msg='IAGL:  Download timeout exception for %(url)s.  Timeout Exception %(exc)s'%{'url':url,'exc':texc},level=xbmc.LOGERROR)
	# 		# 	except Exception as exc:
	# 		# 		self.download_status['success'] = False
	# 		# 		self.download_status['message'] = 'Download failed or was cancelled'
	# 		# 		xbmc.log(msg='IAGL:  Download exception for %(url)s.  Exception %(exc)s'%{'url':url,'exc':exc},level=xbmc.LOGERROR)
	# 		# 	self.download_status['success'] = True
	# 		# 	self.download_status['message'] = 'Download complete'
	# 		# 	dp.close()
	# 		# 	del dp
	# 		# 	return self.download_status
	# 		# else:
	# 		# 	xbmc.log(msg='IAGL:  Badly formed download request.  URL %(url)s, Dest %(dest)s'%{'url':url,'dest':dest},level=xbmc.LOGDEBUG)
	# 		# 	return None

	# class generic_downloader(object):
	# 	def __init__(self,settings=None,directory=None,game_list=None,game=None,header=None,cookies=None):
	# 		self.session = requests.Session()
	# 		self.header=header
	# 		self.cookies=cookies
	# 		self.settings=settings
	# 		self.directory=directory
	# 		self.game_list=game_list
	# 		self.game=game
	# 		self.download_status = dict()
	# 		self.chunk_size = 102400 #100 KB chunks
	# 		self.timeout = (12.1,27)

	# 	def set_header(self,header=None):
	# 		self.header=header
	# 	def set_cookies(self,cookies=None):
	# 		self.cookies=cookies

	# 	def download(self,url=None,dest=None,est_size=None,show_progress=True):
	# 		if url and dest:
	# 			if self.cookies and isinstance(self.cookies,dict):
	# 				domain = self.cookies.get('domain')
	# 				for k,v in self.cookies.items():
	# 					if k!='domain':
	# 						self.session.cookies.set(k,v,domain=domain)
	# 			xbmc.log(msg='IAGL:  Attempting download file',level=xbmc.LOGDEBUG)
	# 			xbmc.log(msg='IAGL:  URL: %(value)s'%{'value':url},level=xbmc.LOGDEBUG)
	# 			xbmc.log(msg='IAGL:  Dest: %(value)s'%{'value':get_dest_as_str(dest)},level=xbmc.LOGDEBUG)
	# 			if show_progress:
	# 				dp = xbmcgui.DialogProgress()
	# 				description = next(iter([str(x) for x in [dest.name,url_unquote(os.path.split(url)[-1].split('%2F')[-1])] if x]),'Unknown File')
	# 				dp.create(loc_str(30376),description)
	# 				dp.update(0,description)
	# 			try:
	# 				with self.session.get(url,verify=False,stream=True,timeout=self.timeout,headers=self.header) as self.r:
	# 					self.r.raise_for_status()
	# 					filesize = next(iter([int(x) for x in [self.r.headers.get('Content-length'),est_size] if x]),0)
	# 					filesize_str = bytes_to_string_size(filesize)
	# 					with xbmcvfs.File(get_dest_as_str(dest),'wb') as ff:
	# 						size = 0
	# 						last_time = time.time()
	# 						for chunk in self.r.iter_content(chunk_size=self.chunk_size):
	# 							ff.write(bytearray(chunk))
	# 							if show_progress and dp.iscanceled():
	# 								dp.close()
	# 								raise Exception('User Cancelled Download')
	# 							if show_progress:
	# 								size = size+len(chunk) #chunks may be a different size when streaming
	# 								percent = int(100.0 * size / (filesize + 1)) #Added 1 byte to avoid div by zero
	# 								now = time.time()
	# 								diff = now - last_time
	# 								if diff > 1: #Only show progress updates in 1 second or greater intervals
	# 									last_time = now
	# 									if filesize:
	# 										dp.update(percent,'%(fn)s[CR]%(current_size)s / %(estimated_size)s'%{'current_size':bytes_to_string_size(size),'fn':description,'estimated_size':filesize_str})
	# 									else:
	# 										dp.update(percent,'%(fn)s[CR]%(current_size)s / Unknown Size'%{'current_size':bytes_to_string_size(size),'fn':description})
	# 			except requests.exceptions.RequestException as rexc:
	# 				self.download_status['success'] = False
	# 				if self.r.status_code == 403:
	# 					self.download_status['message'] = 'Download Request Exception.  Access is forbidden (login required).'
	# 				else:
	# 					self.download_status['message'] = 'Download Request Exception.  See Kodi Log.'
	# 				xbmc.log(msg='IAGL:  Download request exception for %(url)s.  Request Exception %(exc)s'%{'url':url,'exc':rexc},level=xbmc.LOGERROR)
	# 			except requests.exceptions.HTTPError as hexc:
	# 				self.download_status['success'] = False
	# 				self.download_status['message'] = 'Download HTTP error %(exc)s'%{'exc':hexc}
	# 				xbmc.log(msg='IAGL:  Download HTTP exception for %(url)s.  HTTP Exception %(exc)s'%{'url':url,'exc':hexc},level=xbmc.LOGERROR)
	# 			except requests.exceptions.ConnectionError as cexc:
	# 				self.download_status['success'] = False
	# 				self.download_status['message'] = 'Download Connection error %(exc)s'%{'exc':cexc}
	# 				xbmc.log(msg='IAGL:  Download connection exception for %(url)s.  Connection Exception %(exc)s'%{'url':url,'exc':cexc},level=xbmc.LOGERROR)
	# 			except requests.exceptions.Timeout as texc:
	# 				self.download_status['success'] = False
	# 				self.download_status['message'] = 'Download Timeout error %(exc)s'%{'exc':texc}
	# 				xbmc.log(msg='IAGL:  Download timeout exception for %(url)s.  Timeout Exception %(exc)s'%{'url':url,'exc':texc},level=xbmc.LOGERROR)
	# 			except Exception as exc:
	# 				self.download_status['success'] = False
	# 				self.download_status['message'] = 'Download failed or was cancelled'
	# 				xbmc.log(msg='IAGL:  Download exception for %(url)s.  Exception %(exc)s'%{'url':url,'exc':exc},level=xbmc.LOGERROR)
	# 			self.download_status['success'] = True
	# 			self.download_status['message'] = 'Download complete'
	# 			dp.close()
	# 			del dp
	# 			return self.download_status
	# 		else:
	# 			xbmc.log(msg='IAGL:  Badly formed download request.  URL %(url)s, Dest %(dest)s'%{'url':url,'dest':dest},level=xbmc.LOGDEBUG)
	# 			return None

	# 	def return_download_text(self):
	# 		#Download file and return file text here
	# 		zachs_debug('Download file and return text')