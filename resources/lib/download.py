#Internet Archive Game Launcher v3.X (For Kodi v19+)
#Zach Morris
#https://github.com/zach-morris/plugin.program.iagl
import os, json
# from kodi_six import xbmc, xbmcplugin, xbmcgui, xbmcvfs
import xbmc, xbmcplugin, xbmcgui, xbmcvfs
from . utils import *
from urllib.parse import unquote_plus as url_unquote
import requests, time
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class iagl_download(object):
	def __init__(self,settings=dict(),directory=dict(),game_list=dict(),game=dict(),downloader='archive_org'):
		self.settings = settings
		self.directory = directory
		self.game_list = game_list
		self.game = game
		#Default downloader is archive.org
		self.set_downloader(downloader=downloader)

	def set_downloader(self,downloader='archive_org'):
		#Currently the only downloader is archive.org (the default), this is where other downloader options would go if they were added based on the settings, game and game list
		if downloader == 'generic':
			xbmc.log(msg='IAGL:  Downloader set to generic http downloader',level=xbmc.LOGDEBUG)
			self.downloader = self.generic_downloader(settings=self.settings,directory=self.directory,game_list=self.game_list,game=self.game)
		elif downloader == 'archive_org':
			xbmc.log(msg='IAGL:  Downloader set to archive.org',level=xbmc.LOGDEBUG)
			self.downloader = self.archive_org(settings=self.settings,directory=self.directory,game_list=self.game_list,game=self.game)
		elif downloader == 'local_source':
			xbmc.log(msg='IAGL:  Downloader set to Local File Source',level=xbmc.LOGDEBUG)
			self.downloader = self.local_source(settings=self.settings,directory=self.directory,game_list=self.game_list,game=self.game)
		else:
			xbmc.log(msg='IAGL:  Downloader %(downloader)s is unknown, defaulting to NONE'%{'downloader':downloader},level=xbmc.LOGDEBUG)
			self.downloader = None #Default downloader to NONE unless otherwise specified, saves unecessary login attempt
			downloader = 'Unknown'
			# self.downloader = self.archive_org(settings=self.settings,directory=self.directory,game_list=self.game_list,game=self.game,show_login_progress=False) #Default to archive.org unless otherwise specified
		self.current_downloader = downloader

	def download_game(self,show_progress=True):
		game_download_status = list()
		if self.game_list and self.game and self.game.get('properties') and self.game.get('properties').get('rom') and isinstance(self.game.get('properties').get('rom'),str):
			try:
				current_game = json.loads(self.game.get('properties').get('rom'))
			except:
				current_game = None
				xbmc.log(msg='IAGL:  Badly formed game in xml file.  Game %(game)s'%{'game':self.game.get('values').get('label2')},level=xbmc.LOGERROR)
			if current_game:
				if isinstance(current_game,dict):
					current_game = [current_game]
				for cg in current_game:
					current_dl = get_game_download_dict(emu_baseurl=self.game_list.get('emu_baseurl'),emu_downloadpath=self.game_list.get('emu_downloadpath_resolved'),emu_dl_source=self.game_list.get('download_source'),emu_post_processor=self.game_list.get('emu_postdlaction'),emu_launcher=self.game_list.get('emu_launcher'),emu_default_addon=self.game_list.get('emu_default_addon'),emu_ext_launch_cmd=self.game_list.get('emu_ext_launch_cmd'),game_url=cg.get('@name'),game_downloadpath=self.game.get('properties').get('emu_downloadpath'),game_post_processor=self.game.get('properties').get('emu_postdlaction'),game_launcher=self.game.get('properties').get('emu_launcher'),game_default_addon=self.game.get('properties').get('emu_default_addon'),game_ext_launch_cmd=self.game.get('properties').get('emu_ext_launch_cmd'),game_emu_command=self.game.get('properties').get('emu_command'),organize_default_dir=self.settings.get('download').get('organize_cache'),default_dir=self.directory.get('userdata').get('game_cache').get('path'),emu_name=self.game_list.get('emu_description'))
					download_file = True
					current_dl['downloaded_file'] = False
					if len(current_dl.get('matching_existing_files'))>0:
						if self.settings.get('game_action').get('local_file_found') == 0: #Prompt
							current_dialog = xbmcgui.Dialog()
							ret1 = current_dialog.select(loc_str(30355)%{'filename':current_dl.get('filename_no_ext')}, [loc_str(30204),loc_str(30200)])
							del current_dialog
							if ret1 == 0: #Do not overwrite local files, so just point to them directly
								xbmc.log(msg='IAGL: %(value)s exists locally and will not be re-downloaded'%{'value':current_dl.get('filename_no_ext')},level=xbmc.LOGDEBUG)
								download_file = False
								current_dl['download_success'] = True
								current_dl['download_message'] = 'File exists locally'	
							else:
								xbmc.log(msg='IAGL: %(value)s exists locally but will be re-downloaded'%{'value':current_dl.get('filename_no_ext')},level=xbmc.LOGDEBUG)
								download_file = True
						if self.settings.get('game_action').get('local_file_found') == 1: #Do not redownload
							xbmc.log(msg='IAGL: %(value)s exists locally and will not be re-downloaded'%{'value':current_dl.get('filename_no_ext')},level=xbmc.LOGDEBUG)
							download_file = False
							current_dl['download_success'] = True
							current_dl['download_message'] = 'File exists locally'
					if download_file:
						if current_dl.get('downloader') and current_dl.get('downloader') != self.current_downloader:
							self.set_downloader(downloader=current_dl.get('downloader'))
						download_status = self.downloader.download(url=current_dl.get('url_resolved'),dest=current_dl.get('downloadpath_resolved'),est_size=cg.get('@size'),show_progress=show_progress)
						current_dl['download_success'] = download_status.get('success')
						current_dl['download_message'] = download_status.get('message')
						if download_status.get('success'):
							current_dl['downloaded_file'] = True
							if current_dl.get('dl_source') in ['Local File Source'] and download_status.get('updated_dest'): #The file was found locally, so point to that source location
								current_dl['downloadpath_resolved'] = download_status.get('updated_dest')
							if current_dl.get('dl_source') in ['Local Network Source'] and download_status.get('updated_dest'): #The file was found locally, so point to that kodi location if launching with retroplayer
								if current_dl.get('launcher') == 'retroplayer':
									current_dl['downloadpath_resolved'] = download_status.get('updated_dest')
								else:
									current_dl['downloaded_file'] = False
									current_dl['downloadpath_resolved'] = None
									current_dl['download_success'] = False
									current_dl['download_message'] = 'Unable to externally launch games from a Kodi source'
									xbmc.log(msg='IAGL:  Unable to externally launch games from a Kodi source',level=xbmc.LOGERROR)
					game_download_status.append(current_dl)
		else:
			xbmc.log(msg='IAGL:  Badly formed game download request.',level=xbmc.LOGERROR)
			return None
		return game_download_status

	class archive_org(object):
		def __init__(self,settings=dict(),directory=dict(),game_list=dict(),game=dict(),show_login_progress=True):
			self.session = None
			self.r = None
			self.settings = settings
			self.directory = directory
			self.game_list = game_list
			self.game = game
			self.chunk_size = 102400 #100 KB chunks
			self.timeout = (12.1,27)
			self.logged_in = False
			self.cookie = None
			self.download_status = dict()
			self.login_url = 'https://archive.org/account/login.php'
			self.check_account_url = 'https://archive.org/account/index.php'
			self.login(show_progress=show_login_progress)

		def login(self,show_progress=True):
			self.session = requests.Session()
			if self.settings.get('archive_org') and self.settings.get('archive_org').get('username') and self.settings.get('archive_org').get('password') and self.settings.get('archive_org').get('enabled'):
				if show_progress:
					current_dialog = xbmcgui.Dialog()
					current_dialog.notification(loc_str(30377),loc_str(30378),xbmcgui.NOTIFICATION_INFO,self.settings.get('notifications').get('background_notification_time'),sound=False)
				if get_mem_cache('iagl_archive_org_login'):
					self.cookie = get_mem_cache('iagl_archive_org_login')
					xbmc.log(msg='IAGL:  Checking cached login credentials for archive.org',level=xbmc.LOGDEBUG)
					for k,v in self.cookie.items():
						self.session.cookies.set(k,v,domain='.archive.org')
					try:
						with self.session.get(self.check_account_url,verify=False,timeout=self.timeout) as self.r:
							self.r.raise_for_status()
							if self.r.ok and '<title>cannot find account</title>' not in self.r.text.lower():
								xbmc.log(msg='IAGL:  Login check passed for archive.org',level=xbmc.LOGDEBUG)
							elif self.r.ok and '<title>cannot find account</title>' in self.r.text.lower():
								xbmc.log(msg='IAGL:  First Login check failed for archive.org, attempting to re-login',level=xbmc.LOGDEBUG)
								clear_mem_cache('iagl_archive_org_login')
								self.login()
							else:
								clear_mem_cache('iagl_archive_org_login')
								xbmc.log(msg='IAGL:  Login check failed for archive.org because the login page could not be accessed.  Status code %(code)s'%{'code':self.r.status_code},level=xbmc.LOGERROR)
					except Exception as exc:
						xbmc.log(msg='IAGL:  Login exception for %(url)s.  Exception %(exc)s'%{'url':self.check_account_url,'exc':exc},level=xbmc.LOGERROR)
				else:
					try:
						with self.session.get(self.login_url,verify=False,timeout=self.timeout) as self.r:
							self.r.raise_for_status()
					except Exception as exc:
						xbmc.log(msg='IAGL:  Login exception for %(url)s.  Exception %(exc)s'%{'url':self.check_account_url,'exc':exc},level=xbmc.LOGERROR)
					try:
						with self.session.post(self.login_url,verify=False,timeout=self.timeout,data={'username':str(self.settings.get('archive_org').get('username')),'password':str(self.settings.get('archive_org').get('password')),'remember':'CHECKED','action':'login','submit': 'Log+in'},allow_redirects=True) as self.r:
							self.r.raise_for_status()
							if self.r.ok and dict(self.r.headers) and dict(self.r.headers).get('Set-Cookie'):
								hcookie = {z.split('=')[0].strip():z.split('=')[-1].strip() for z in [y.split(',')[-1].strip() for y in [x.strip() for x in dict(self.r.headers).get('Set-Cookie').split(';')]] if '=' in z}
								if hcookie.get('logged-in-sig') and hcookie.get('logged-in-user'):
									self.cookie = {'logged-in-user':hcookie.get('logged-in-user'),'logged-in-sig':hcookie.get('logged-in-sig'),'Max-Age':hcookie.get('Max-Age')}
									set_mem_cache('iagl_archive_org_login',self.cookie)
									self.logged_in = True
									xbmc.log(msg='IAGL:  Login to archive.org succeeded with the supplied user email and password',level=xbmc.LOGDEBUG)
								else:
									self.cookie = None
									self.logged_in = False
									xbmc.log(msg='IAGL:  Login to archive.org failed with the supplied user email and password',level=xbmc.LOGERROR)
							else:
								self.cookie = None
								self.logged_in = False
								xbmc.log(msg='IAGL:  Login failed to archive.org because the login page could not be accessed',level=xbmc.LOGERROR)
					except Exception as exc:
						xbmc.log(msg='IAGL:  Login exception for %(url)s.  Exception %(exc)s'%{'url':self.check_account_url,'exc':exc},level=xbmc.LOGERROR)
				if show_progress:
					xbmc.executebuiltin('Dialog.Close(notification,true)')
					check_and_close_notification()
					del current_dialog
			else:
				self.cookie = None
				self.logged_in = False
				xbmc.log(msg='IAGL:  Login information was not provided in addon settings',level=xbmc.LOGDEBUG)

		def download(self,url=None,dest=None,est_size=None,show_progress=True):
			if url and dest:
				if not self.session:
					self.login()
				if self.settings.get('archive_org') and self.settings.get('archive_org').get('username') and self.settings.get('archive_org').get('password') and self.settings.get('archive_org').get('enabled'):
					xbmc.log(msg='IAGL:  Attempting download with login credentials',level=xbmc.LOGDEBUG)
				else:
					xbmc.log(msg='IAGL:  Attempting download without login credentials',level=xbmc.LOGDEBUG)
				xbmc.log(msg='IAGL:  URL: %(value)s'%{'value':url},level=xbmc.LOGDEBUG)
				xbmc.log(msg='IAGL:  Dest: %(value)s'%{'value':dest},level=xbmc.LOGDEBUG)
				if show_progress:
					dp = xbmcgui.DialogProgress()
					description = next(iter([str(x) for x in [dest.name,url_unquote(os.path.split(url)[-1].split('%2F')[-1])] if x]),'Unknown File')
					dp.create(loc_str(30376),description)
					dp.update(0,description)
				try:
					with self.session.get(url,verify=False,stream=True,timeout=self.timeout) as self.r:
						self.r.raise_for_status()
						filesize = next(iter([int(x) for x in [self.r.headers.get('Content-length'),est_size] if x]),0)
						filesize_str = bytes_to_string_size(filesize)
						with xbmcvfs.File(str(dest),'wb') as game_file:
							size = 0
							last_time = time.time()
							for chunk in self.r.iter_content(chunk_size=self.chunk_size):
								game_file.write(bytearray(chunk))
								if show_progress and dp.iscanceled():
									dp.close()
									raise Exception('User Cancelled Download')
								if show_progress:
									size = size+len(chunk) #chunks may be a different size when streaming
									percent = int(100.0 * size / (filesize + 1)) #Added 1 byte to avoid div by zero
									now = time.time()
									diff = now - last_time
									if diff > 1: #Only show progress updates in 1 second or greater intervals
										last_time = now
										if filesize:
											dp.update(percent,'%(fn)s[CR]%(current_size)s / %(estimated_size)s'%{'current_size':bytes_to_string_size(size),'fn':description,'estimated_size':filesize_str})
										else:
											dp.update(percent,'%(fn)s[CR]%(current_size)s / Unknown Size'%{'current_size':bytes_to_string_size(size),'fn':description})
					self.download_status['success'] = True
					self.download_status['message'] = 'Download complete'
					self.download_status['download_size'] = size
					xbmc.log(msg='IAGL:  Download complete for %(url)s.  File size %(size)s'%{'url':url,'size':size},level=xbmc.LOGINFO)
				except requests.exceptions.RequestException as rexc:
					self.download_status['success'] = False
					if self.r and self.r.status_code == 403:
						self.download_status['message'] = 'Download Request Exception.  Archive requires login.'
					else:
						self.download_status['message'] = 'Download Request Exception.  See Kodi Log.'
					xbmc.log(msg='IAGL:  Download request exception for %(url)s.  Request Exception %(exc)s'%{'url':url,'exc':rexc},level=xbmc.LOGERROR)
					delete_file(str(dest))
				except requests.exceptions.HTTPError as hexc:
					self.download_status['success'] = False
					self.download_status['message'] = 'Download HTTP error %(exc)s'%{'exc':hexc}
					xbmc.log(msg='IAGL:  Download HTTP exception for %(url)s.  HTTP Exception %(exc)s'%{'url':url,'exc':hexc},level=xbmc.LOGERROR)
					delete_file(str(dest))
				except requests.exceptions.ConnectionError as cexc:
					self.download_status['success'] = False
					self.download_status['message'] = 'Download Connection error %(exc)s'%{'exc':cexc}
					xbmc.log(msg='IAGL:  Download connection exception for %(url)s.  Connection Exception %(exc)s'%{'url':url,'exc':cexc},level=xbmc.LOGERROR)
					delete_file(str(dest))
				except requests.exceptions.Timeout as texc:
					self.download_status['success'] = False
					self.download_status['message'] = 'Download Timeout error %(exc)s'%{'exc':texc}
					xbmc.log(msg='IAGL:  Download timeout exception for %(url)s.  Timeout Exception %(exc)s'%{'url':url,'exc':texc},level=xbmc.LOGERROR)
					delete_file(str(dest))
				except Exception as exc:
					self.download_status['success'] = False
					self.download_status['download_size'] = None
					self.download_status['message'] = 'Download failed or was cancelled'
					xbmc.log(msg='IAGL:  Download exception for %(url)s.  Exception %(exc)s'%{'url':url,'exc':exc},level=xbmc.LOGERROR)
					delete_file(str(dest))
				dp.close()
				del dp
				return self.download_status
			else:
				xbmc.log(msg='IAGL:  Badly formed download request.  URL %(url)s, Dest %(dest)s'%{'url':url,'dest':dest},level=xbmc.LOGDEBUG)
				return None

	class local_source(object):
		def __init__(self,settings=dict(),directory=dict(),game_list=dict(),game=dict(),show_progress=False):
			self.settings = settings
			self.directory = directory
			self.game_list = game_list
			self.game = game
			self.download_status = dict()

		def download(self,url=None,dest=None,est_size=None,show_progress=False):
			if url and check_if_file_exists(Path(url_unquote(url))):
				self.download_status['success'] = True
				self.download_status['message'] = 'File was accessible via local filesystem'
				xbmc.log(msg='IAGL:  Game was found to exists on the local filesystem: %(url)s'%{'url':url},level=xbmc.LOGDEBUG)
				self.download_status['updated_dest'] = Path(url_unquote(url))
			elif url and check_if_file_exists(url_unquote(url)):
				self.download_status['success'] = True
				self.download_status['message'] = 'File was accessible via Kodi Source'
				xbmc.log(msg='IAGL:  Game was found to exists at a Kodi Source: %(url)s'%{'url':url},level=xbmc.LOGDEBUG)
				self.download_status['updated_dest'] = url_unquote(url)
			else:
				self.download_status['success'] = False
				self.download_status['message'] = 'File was not accessible'
				xbmc.log(msg='IAGL:  Game was not accessible: %(url)s'%{'url':url},level=xbmc.LOGERROR)
			return self.download_status
			# 	if self.cookies and isinstance(self.cookies,dict):
			# 		domain = self.cookies.get('domain')
			# 		for k,v in self.cookie.items():
			# 			if k!='domain':
			# 				self.session.cookies.set(k,v,domain=domain)
			# 	xbmc.log(msg='IAGL:  Attempting download file',level=xbmc.LOGDEBUG)
			# 	xbmc.log(msg='IAGL:  URL: %(value)s'%{'value':url},level=xbmc.LOGDEBUG)
			# 	xbmc.log(msg='IAGL:  Dest: %(value)s'%{'value':dest},level=xbmc.LOGDEBUG)
			# 	if show_progress:
			# 		dp = xbmcgui.DialogProgress()
			# 		description = next(iter([str(x) for x in [dest.name,url_unquote(os.path.split(url)[-1].split('%2F')[-1])] if x]),'Unknown File')
			# 		dp.create(loc_str(30376),description)
			# 		dp.update(0,description)
			# 	try:
			# 		with self.session.get(url,verify=False,stream=True,timeout=self.timeout,headers=self.header) as self.r:
			# 			self.r.raise_for_status()
			# 			filesize = next(iter([int(x) for x in [self.r.headers.get('Content-length'),est_size] if x]),0)
			# 			filesize_str = bytes_to_string_size(filesize)
			# 			with xbmcvfs.File(str(dest),'wb') as ff:
			# 				size = 0
			# 				last_time = time.time()
			# 				for chunk in self.r.iter_content(chunk_size=self.chunk_size):
			# 					ff.write(bytearray(chunk))
			# 					if show_progress and dp.iscanceled():
			# 						dp.close()
			# 						raise Exception('User Cancelled Download')
			# 					if show_progress:
			# 						size = size+len(chunk) #chunks may be a different size when streaming
			# 						percent = int(100.0 * size / (filesize + 1)) #Added 1 byte to avoid div by zero
			# 						now = time.time()
			# 						diff = now - last_time
			# 						if diff > 1: #Only show progress updates in 1 second or greater intervals
			# 							last_time = now
			# 							if filesize:
			# 								dp.update(percent,'%(fn)s[CR]%(current_size)s / %(estimated_size)s'%{'current_size':bytes_to_string_size(size),'fn':description,'estimated_size':filesize_str})
			# 							else:
			# 								dp.update(percent,'%(fn)s[CR]%(current_size)s / Unknown Size'%{'current_size':bytes_to_string_size(size),'fn':description})
			# 	except requests.exceptions.RequestException as rexc:
			# 		self.download_status['success'] = False
			# 		if self.r.status_code == 403:
			# 			self.download_status['message'] = 'Download Request Exception.  Access is forbidden (login required).'
			# 		else:
			# 			self.download_status['message'] = 'Download Request Exception.  See Kodi Log.'
			# 		xbmc.log(msg='IAGL:  Download request exception for %(url)s.  Request Exception %(exc)s'%{'url':url,'exc':rexc},level=xbmc.LOGERROR)
			# 	except requests.exceptions.HTTPError as hexc:
			# 		self.download_status['success'] = False
			# 		self.download_status['message'] = 'Download HTTP error %(exc)s'%{'exc':hexc}
			# 		xbmc.log(msg='IAGL:  Download HTTP exception for %(url)s.  HTTP Exception %(exc)s'%{'url':url,'exc':hexc},level=xbmc.LOGERROR)
			# 	except requests.exceptions.ConnectionError as cexc:
			# 		self.download_status['success'] = False
			# 		self.download_status['message'] = 'Download Connection error %(exc)s'%{'exc':cexc}
			# 		xbmc.log(msg='IAGL:  Download connection exception for %(url)s.  Connection Exception %(exc)s'%{'url':url,'exc':cexc},level=xbmc.LOGERROR)
			# 	except requests.exceptions.Timeout as texc:
			# 		self.download_status['success'] = False
			# 		self.download_status['message'] = 'Download Timeout error %(exc)s'%{'exc':texc}
			# 		xbmc.log(msg='IAGL:  Download timeout exception for %(url)s.  Timeout Exception %(exc)s'%{'url':url,'exc':texc},level=xbmc.LOGERROR)
			# 	except Exception as exc:
			# 		self.download_status['success'] = False
			# 		self.download_status['message'] = 'Download failed or was cancelled'
			# 		xbmc.log(msg='IAGL:  Download exception for %(url)s.  Exception %(exc)s'%{'url':url,'exc':exc},level=xbmc.LOGERROR)
			# 	self.download_status['success'] = True
			# 	self.download_status['message'] = 'Download complete'
			# 	dp.close()
			# 	del dp
			# 	return self.download_status
			# else:
			# 	xbmc.log(msg='IAGL:  Badly formed download request.  URL %(url)s, Dest %(dest)s'%{'url':url,'dest':dest},level=xbmc.LOGDEBUG)
			# 	return None

	class generic_downloader(object):
		def __init__(self,header=None,cookies=None):
			self.session = requests.Session()
			self.header=header
			self.cookies=cookies

		def set_header(self,header=None):
			self.header=header
		def set_cookies(self,cookies=None):
			self.cookies=cookies

		def download_file(self,url=None,dest=None,est_size=None,show_progress=True):
			if url and dest:
				if self.cookies and isinstance(self.cookies,dict):
					domain = self.cookies.get('domain')
					for k,v in self.cookie.items():
						if k!='domain':
							self.session.cookies.set(k,v,domain=domain)
				xbmc.log(msg='IAGL:  Attempting download file',level=xbmc.LOGDEBUG)
				xbmc.log(msg='IAGL:  URL: %(value)s'%{'value':url},level=xbmc.LOGDEBUG)
				xbmc.log(msg='IAGL:  Dest: %(value)s'%{'value':dest},level=xbmc.LOGDEBUG)
				if show_progress:
					dp = xbmcgui.DialogProgress()
					description = next(iter([str(x) for x in [dest.name,url_unquote(os.path.split(url)[-1].split('%2F')[-1])] if x]),'Unknown File')
					dp.create(loc_str(30376),description)
					dp.update(0,description)
				try:
					with self.session.get(url,verify=False,stream=True,timeout=self.timeout,headers=self.header) as self.r:
						self.r.raise_for_status()
						filesize = next(iter([int(x) for x in [self.r.headers.get('Content-length'),est_size] if x]),0)
						filesize_str = bytes_to_string_size(filesize)
						with xbmcvfs.File(str(dest),'wb') as ff:
							size = 0
							last_time = time.time()
							for chunk in self.r.iter_content(chunk_size=self.chunk_size):
								ff.write(bytearray(chunk))
								if show_progress and dp.iscanceled():
									dp.close()
									raise Exception('User Cancelled Download')
								if show_progress:
									size = size+len(chunk) #chunks may be a different size when streaming
									percent = int(100.0 * size / (filesize + 1)) #Added 1 byte to avoid div by zero
									now = time.time()
									diff = now - last_time
									if diff > 1: #Only show progress updates in 1 second or greater intervals
										last_time = now
										if filesize:
											dp.update(percent,'%(fn)s[CR]%(current_size)s / %(estimated_size)s'%{'current_size':bytes_to_string_size(size),'fn':description,'estimated_size':filesize_str})
										else:
											dp.update(percent,'%(fn)s[CR]%(current_size)s / Unknown Size'%{'current_size':bytes_to_string_size(size),'fn':description})
				except requests.exceptions.RequestException as rexc:
					self.download_status['success'] = False
					if self.r.status_code == 403:
						self.download_status['message'] = 'Download Request Exception.  Access is forbidden (login required).'
					else:
						self.download_status['message'] = 'Download Request Exception.  See Kodi Log.'
					xbmc.log(msg='IAGL:  Download request exception for %(url)s.  Request Exception %(exc)s'%{'url':url,'exc':rexc},level=xbmc.LOGERROR)
				except requests.exceptions.HTTPError as hexc:
					self.download_status['success'] = False
					self.download_status['message'] = 'Download HTTP error %(exc)s'%{'exc':hexc}
					xbmc.log(msg='IAGL:  Download HTTP exception for %(url)s.  HTTP Exception %(exc)s'%{'url':url,'exc':hexc},level=xbmc.LOGERROR)
				except requests.exceptions.ConnectionError as cexc:
					self.download_status['success'] = False
					self.download_status['message'] = 'Download Connection error %(exc)s'%{'exc':cexc}
					xbmc.log(msg='IAGL:  Download connection exception for %(url)s.  Connection Exception %(exc)s'%{'url':url,'exc':cexc},level=xbmc.LOGERROR)
				except requests.exceptions.Timeout as texc:
					self.download_status['success'] = False
					self.download_status['message'] = 'Download Timeout error %(exc)s'%{'exc':texc}
					xbmc.log(msg='IAGL:  Download timeout exception for %(url)s.  Timeout Exception %(exc)s'%{'url':url,'exc':texc},level=xbmc.LOGERROR)
				except Exception as exc:
					self.download_status['success'] = False
					self.download_status['message'] = 'Download failed or was cancelled'
					xbmc.log(msg='IAGL:  Download exception for %(url)s.  Exception %(exc)s'%{'url':url,'exc':exc},level=xbmc.LOGERROR)
				self.download_status['success'] = True
				self.download_status['message'] = 'Download complete'
				dp.close()
				del dp
				return self.download_status
			else:
				xbmc.log(msg='IAGL:  Badly formed download request.  URL %(url)s, Dest %(dest)s'%{'url':url,'dest':dest},level=xbmc.LOGDEBUG)
				return None

		def return_download_text(self):
			#Download file and return file text here
			zachs_debug('Download file and return text')