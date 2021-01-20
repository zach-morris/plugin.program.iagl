#Internet Archive Game Launcher v3.X (For Kodi v19+)
#Zach Morris
#https://github.com/zach-morris/plugin.program.iagl
# from kodi_six import xbmc, xbmcplugin, xbmcgui, xbmcvfs
import xbmc, xbmcplugin, xbmcgui, xbmcvfs
from . utils import *
import archive_tool

class iagl_post_process(object):
	def __init__(self,settings=dict(),directory=dict(),game_list=dict(),game=dict(),game_files=dict(),post_processor=None):
		self.settings = settings
		self.directory = directory
		self.game_list = game_list
		self.game = game
		self.game_files = game_files
		self.current_pp_status = None
		#Default downloader is archive.org
		self.set_post_processor(post_processor=post_processor)

	def set_post_processor(self,post_processor=None):
		if post_processor:
			if post_processor == 'unzip_rom': #Standard unzip, assume the game file is named the same as the archive file (standard for no-intro,redump,etc)
				xbmc.log(msg='IAGL:  Post processor set to UNZIP',level=xbmc.LOGDEBUG)
				self.post_processor = self.unzip(settings=self.settings,directory=self.directory,game_list=self.game_list,game=self.game,game_files=self.game_files)
			elif post_processor == 'unzip_to_folder_and_launch_file': #Unarchive to a folder and point to the file specified in the emu_command which is already known to be contained the archive
				xbmc.log(msg='IAGL:  Post processor set to UNZIP to folder and launch file',level=xbmc.LOGDEBUG)
				self.post_processor = self.unzip(settings=self.settings,directory=self.directory,game_list=self.game_list,game=self.game,game_files=self.game_files,to_folder=True,use_emu_command=True)
			else:
				xbmc.log(msg='IAGL:  Post processor is unknown, setting to NONE to attempt launching',level=xbmc.LOGERROR)
				self.post_processor = None
		else:
			xbmc.log(msg='IAGL:  Post processor set to NONE',level=xbmc.LOGDEBUG)
			self.post_processor = None
		if self.post_processor:
			self.current_post_processor = post_processor
		else:
			self.current_post_processor = 'none'

	def post_process_game(self,show_progress=True):
		game_pp_status = list()
		if self.game_list and self.game_files:
			# if show_progress:
			# 	current_dialog = xbmcgui.Dialog()
			# 	current_dialog.notification(loc_str(30377),loc_str(30379),xbmcgui.NOTIFICATION_INFO,self.settings.get('notifications').get('background_notification_time'),sound=False)
			for gf in self.game_files:
				current_pp = gf.copy()
				if gf.get('download_success'):
					if gf.get('post_processor') and gf.get('post_processor') != self.current_post_processor:
						self.set_post_processor(post_processor=gf.get('post_processor'))
					if self.post_processor:
						pp_status = self.post_processor.process(file=gf.get('downloadpath_resolved'),emu_command=gf.get('emu_command'),current_pp=self.current_pp_status)
						current_pp['post_process_success'] = pp_status.get('post_process_success')
						current_pp['post_process_message'] = pp_status.get('post_process_message')
						current_pp['post_process_launch_file'] = pp_status.get('post_process_launch_file')
						xbmc.log(msg='IAGL:  Post processing complete for %(game)s'%{'game':gf.get('filename')},level=xbmc.LOGINFO)
					else:
						current_pp['post_process_success'] = True
						current_pp['post_process_message'] = 'No post processing method set, attempting launch'
						current_pp['post_process_launch_file'] = gf.get('downloadpath_resolved')
						xbmc.log(msg='IAGL:  Post processing skipped for %(game)s, attempting launch'%{'game':gf.get('filename')},level=xbmc.LOGINFO)
				else:
					xbmc.log(msg='IAGL:  The file %(value)s did not succeed the download check, post processing will be skipped'%{'value':gf.get('filename')},level=xbmc.LOGDEBUG)
					current_pp['post_process_success'] = False
					current_pp['post_process_message'] = 'Download check failed, post processing skipped'
				self.current_pp_status = current_pp
				game_pp_status.append(current_pp)
			# if show_progress:
			# 	xbmc.executebuiltin('Dialog.Close(notification,true)')
			# 	xbmc.sleep(NOTIFICATION_DEINIT_TIME) #Close the notification and wait for de-init to ensure any follow on notification are correctly shown, unsure if there's a better way to do this
			# 	del current_dialog
		else:
			xbmc.log(msg='IAGL:  Badly formed game post process request.',level=xbmc.LOGERROR)
			return None
		return game_pp_status

	class unzip(object):
		def __init__(self,settings=dict(),directory=dict(),game_list=dict(),game=dict(),game_files=dict(),**kwargs):
			self.settings = settings
			self.directory= directory
			self.game_list = game_list
			self.game = game
			self.game_files = game_files
			self.pp_status = dict()
			if kwargs and kwargs.get('to_folder'):
				self.unzip_to_folder = True
			else:
				self.unzip_to_folder = False
			if kwargs and kwargs.get('use_emu_command'):
				self.use_emu_command = kwargs.get('use_emu_command')
			else:
				self.use_emu_command = None
			if kwargs and kwargs.get('do_not_delete_archive'):
				self.delete_archive = False
			else:
				self.delete_archive = True #By default, delete the archive after a successful extraction
			if kwargs and kwargs.get('current_pp'):
				self.current_pp = kwargs.get('current_pp') #Provides the status/info of any previous post processed files
			else:
				self.current_pp = None

		def process(self,file=None,**kwargs):
			matching_files = None
			if isinstance(self.game_files,list):
				matching_files = flatten_list([x.get('matching_existing_files') for x in self.game_files if x.get('download_message') == 'File exists locally']) #Identify matching files if they were not redownloaded
			if matching_files and len(matching_files)>0:
				if kwargs and kwargs.get('emu_command') and any([kwargs.get('emu_command') in str(x) for x in matching_files]):
					self.pp_status['post_process_success'] = True
					self.pp_status['post_process_message'] = 'Existing emu command file found'
					self.pp_status['post_process_launch_file'] = [x for x in matching_files if kwargs.get('emu_command') in str(x)][0]
					xbmc.log(msg='IAGL:  Pointing to the existing emu_command file %(value)s'%{'value':self.pp_status.get('post_process_launch_file')},level=xbmc.LOGDEBUG)
				elif any(['.zip' not in str(x).lower() for x in matching_files]): #Pick the non-zipped matching file
					self.pp_status['post_process_success'] = True
					self.pp_status['post_process_message'] = 'Existing non zipped file found'
					self.pp_status['post_process_launch_file'] = [x for x in matching_files if '.zip' not in str(x).lower()][0]
					xbmc.log(msg='IAGL:  Pointing to the existing non-zipped version of the game file %(value)s'%{'value':self.pp_status.get('post_process_launch_file')},level=xbmc.LOGDEBUG)
				else:
					self.pp_status['post_process_success'] = True
					self.pp_status['post_process_message'] = 'Existing file found'
					self.pp_status['post_process_launch_file'] = matching_files[0]
					xbmc.log(msg='IAGL:  Unable to determine which matching file to launch, picking first available file %(value)s'%{'value':self.pp_status.get('post_process_launch_file')},level=xbmc.LOGDEBUG)
			else:
				if file:
					directory_out = None #Unzip to the folder the archive is located in
					if self.unzip_to_folder:
						if kwargs and kwargs.get('folder_name'):
							directory_out = str(Path(file).parent.joinpath(kwargs.get('folder_name'))) #Unzip to the specified folder
						else:
							directory_out = str(Path(file).parent.joinpath(clean_file_folder_name(self.game.get('values').get('label2')))) #Unzip to a 'safe name' folder
					my_archive = archive_tool.archive_tool(archive_file=str(file),directory_out=directory_out)
					extracted_files, success = my_archive.extract()
					if success:
						self.pp_status['post_process_success'] = True
						self.pp_status['post_process_message'] = 'Unzip complete'
						if self.use_emu_command:
							if kwargs and kwargs.get('emu_command') and any([kwargs.get('emu_command') in x for x in extracted_files]):
								self.pp_status['post_process_launch_file'] = [x for x in extracted_files if kwargs.get('emu_command') in x][0]
								xbmc.log(msg='IAGL:  Pointing to the extracted emu_command file %(value)s'%{'value':self.pp_status.get('post_process_launch_file')},level=xbmc.LOGDEBUG)
						else:
							if len(extracted_files)==1:
								self.pp_status['post_process_launch_file'] = extracted_files[0]
								xbmc.log(msg='IAGL:  Pointing to the only extracted file %(value)s'%{'value':self.pp_status.get('post_process_launch_file')},level=xbmc.LOGDEBUG)
							else:
								self.pp_status['post_process_launch_file'] = extracted_files[0]
								xbmc.log(msg='IAGL:  Multiple files extracted, pointing to the first extracted file %(value)s'%{'value':self.pp_status.get('post_process_launch_file')},level=xbmc.LOGDEBUG)
					else:
						self.pp_status['post_process_success'] = False
						self.pp_status['post_process_message'] = 'Unzip Failed'
						self.pp_status['post_process_launch_file'] = None
				else:
					xbmc.log(msg='IAGL:  Badly formed uzip request',level=xbmc.LOGDEBUG)
					return None
			if self.delete_archive and self.pp_status.get('post_process_success') and self.pp_status.get('post_process_message') and self.pp_status.get('post_process_message') == 'Unzip complete':
				delete_file(file)
			return self.pp_status
