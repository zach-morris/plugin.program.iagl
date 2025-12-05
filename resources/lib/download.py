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
	def __init__(self,config=None,rom=None,launch_parameters=None,game_name=None,dl_path=None,current_downloader='archive_org',threads=None,auto_login=True,show_dl_progress=True,show_login_progress=True,ia_email=None,ia_password=None,if_game_exists=0,ige_dialog=None):
		self.config = config
		self.show_dl_progress = show_dl_progress
		self.show_login_progress = show_login_progress
		self.downloader = None
		self.rom = rom
		self.launch_parameters = launch_parameters
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

	def set_launch_parameters(self,launch_parameters=None):
		if isinstance(launch_parameters,dict):
			self.launch_parameters = launch_parameters
		else:
			self.launch_parameters = None
		if self.downloader is not None:
			self.downloader.set_launch_parameters(launch_parameters=self.launch_parameters)

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
		def __init__(self,config=None,rom=None,launch_parameters=None,game_name=None,dl_path=None,threads=None,auto_login=True,show_dl_progress=True,show_login_progress=True,ia_email=None,ia_password=None,if_game_exists=0,ige_dialog=None):
			self.config = config
			self.rom = rom
			self.launch_parameters = launch_parameters
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

		def set_launch_parameters(self,launch_parameters=None):
			if isinstance(launch_parameters,dict):
				self.launch_parameters = launch_parameters
			else:
				self.launch_parameters = None

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

		def get_file_listing_xbmcvfs(self,directory_in,max_levels=4,current_level=0):
			files_in_dir = list()
			dirs_in_dir = list()
			if isinstance(directory_in,str) and xbmcvfs.exists(os.path.join(directory_in,'')):
				dirs_in_dir, files_in_dir = xbmcvfs.listdir(os.path.join(directory_in,''))
				if current_level<max_levels:
					for dd in dirs_in_dir:
						dirs_in_dir2, files_in_dir2 = self.get_file_listing_xbmcvfs(os.path.join(directory_in,dd,''),max_levels=max_levels,current_level=current_level+1)
						dirs_in_dir = dirs_in_dir+[x for x in dirs_in_dir2 if x not in dirs_in_dir]
						files_in_dir = files_in_dir+[x for x in files_in_dir2 if x not in files_in_dir]
			return dirs_in_dir, [os.path.join(directory_in,x) for x in files_in_dir]

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
				with self.session.get(self.config.downloads.get('archive_org_check_acct'),timeout=self.config.downloads.get('login_timeout'),headers=self.login_headers,allow_redirects=False) as r:
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
					xbmc.log(msg='IAGL:  Attempting Archive.org login',level=xbmc.LOGDEBUG)
					try:
						with self.session.post(self.config.downloads.get('archive_org_login_url'),verify=False,timeout=self.config.downloads.get('login_timeout'),params={'op': 'login'},data={'email': self.ia_email, 'password': self.ia_password}) as r:
							r.raise_for_status()
							if r.ok and isinstance(r.json(),dict) and r.json().get('success') == True:
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

		def get_matching_local_files(self):
			matching_files = []
			current_dl_path_files = list(Path(self.dl_path).rglob('**/*'))
			if isinstance(self.launch_parameters,dict) and isinstance(self.launch_parameters.get('launch_file'),dict):
				lf = self.launch_parameters.get('launch_file').get('filename') or self.launch_parameters.get('launch_file').get('file_name')
				if isinstance(lf,str):
					lf = str(Path().joinpath(*lf.split('/')))  #Correct any path seperation
					matching_files = matching_files+[x for x in current_dl_path_files if x.is_file() and x not in matching_files and lf == x.name]
					matching_files = matching_files+[x for x in current_dl_path_files if x.is_file() and x not in matching_files and lf in str(x)]
					if lf!=xbmcvfs.makeLegalFilename(lf):
						matching_files = matching_files+[x for x in current_dl_path_files if x.is_file() and x not in matching_files and xbmcvfs.makeLegalFilename(lf) == x.name]
						matching_files = matching_files+[x for x in current_dl_path_files if x.is_file() and x not in matching_files and xbmcvfs.makeLegalFilename(lf) in str(x)]
					if len(matching_files)>0:
						xbmc.log(msg='IAGL:  Matching launch_parameter file found locally for requested game:\n{}'.format(lf),level=xbmc.LOGDEBUG)
			if isinstance(self.rom,list):
				for rn,cr in enumerate(self.rom):
					cr['filename'] = xbmcvfs.makeLegalFilename(url_unquote(cr.get('url').split('/')[-1].split('%2F')[-1]))
					cr['dl_filepath'] = Path(self.dl_path).joinpath(cr.get('filename'))
					cr['filenum'] = rn
					matching_files = matching_files+[x for x in current_dl_path_files if x.is_file() and x not in matching_files and Path(cr.get('filename')).name == x.name]
					matching_files = matching_files+[x for x in current_dl_path_files if x.is_file() and x not in matching_files and Path(cr.get('filename')).stem == x.stem]
					# matching_files = matching_files+[x for x in current_dl_path_files if x.is_file() and x not in matching_files and Path(cr.get('filename')).name in str(x)]
					matching_files = matching_files+[x for x in current_dl_path_files if x.is_file() and x not in matching_files and str(x.stem) in Path(cr.get('filename')).stem]
					cr['matching_files'] = matching_files
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

		def get_rom_heads(self):
			if self.dp is not None:
				description = '{}{}'.format(self.config.addon.get('addon_handle').getLocalizedString(30274),self.game_name or 'Files')
				self.dp.update(2,description)
			if isinstance(self.rom,list):
				for rn,cr in enumerate(self.rom):
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
							cr['chunk_size'] = abs(cr.get('filesize') or self.config.downloads.get('min_file_size'))
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

			self.get_matching_local_files() #Look for local files first

			if isinstance(self.rom,list) and any([cr.get('continue_with_download')==True for cr in self.rom]):
				if any(['archive.org' in cr.get('url').lower() for cr in self.rom if isinstance(cr.get('url'),str)]):
					if isinstance(self.ia_email,str) and isinstance(self.ia_password,str):
						if not self.logged_in:
							self.login()
					else:
						xbmc.log(msg='IAGL:  Attempting download without login credentials',level=xbmc.LOGDEBUG)
				else:
					xbmc.log(msg='IAGL:  No archive.org url passed for download, skipping login',level=xbmc.LOGDEBUG)
			else:
				xbmc.log(msg='IAGL:  Skipping IA login check due to matching local files',level=xbmc.LOGDEBUG)
				
			self.get_rom_heads() #Initialize info needed for downloading if necessary

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
						if xbmcvfs.exists(cr.get('chunk_filenames')) and all([x.get('success') for x in futures_results]):
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
					bad_file_returned = False
					with self.session.get(rom.get('url'),headers={'Range':'bytes={}'.format(byte_range)},verify=False,stream=True,timeout=self.config.downloads.get('timeout'),allow_redirects=True) as r:
						r.raise_for_status()
						with xbmcvfs.File(chunk_filename,'wb') as game_file:
							current_time = time.time()
							if not xbmcgui.Window(self.dp_id).getProperty('start_time').isdigit():
								xbmcgui.Window(self.dp_id).setProperty('start_time',str(int(current_time*1000)))
							# for chunk in r.iter_content(chunk_size=rom.get('chunk_size')):
							for chunk in r.iter_content(chunk_size=self.config.downloads.get('chunk_size')): #Break download into chunks (approx 4 for min file size)
								game_file.write(bytearray(chunk))
								if len(chunk)<self.config.downloads.get('bad_file_return_size') and b'<title>Item not available' in chunk:
									bad_file_returned = True
								size = size+len(chunk) #chunks may be a different size when streaming
								if self.dp is not None and self.dp.iscanceled():
									self.download_cancelled = True
									raise Exception('User Cancelled Download')
								if self.dp is not None:
									if xbmcgui.Window(self.dp_id).getProperty('current_size').isdigit():
										current_size=int(xbmcgui.Window(self.dp_id).getProperty('current_size'))+len(chunk) #Get size of download combining all threads
									else:
										current_size=len(chunk)
									percent_complete = int(100*current_size/((rom.get('filesize') or 0)+1)) #Calculate overall progress for downloading this file combining all threads
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
						if bad_file_returned:
							result['success'] = False
							result['download_size'] = size
							result['message'] = 'Download error[CR]Archive returned file not found or requires login'
							xbmc.log(msg='IAGL:  Bad file returned in chunk {}.  Archive returned file not found.'.format(thread_id),level=xbmc.LOGDEBUG)
						else:
							result['success'] = True
							result['download_size'] = size
							result['message'] = 'Download completed'
							result['chunk_filename'] = chunk_filename
							xbmc.log(msg='IAGL:  Chunk {} download complete.  File size {}'.format(thread_id,size),level=xbmc.LOGDEBUG)
				except requests.exceptions.RequestException as rexc:
					result['success'] = False
					if rexc.response and isinstance(rexc.response.status_code,int):
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
