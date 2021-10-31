#Internet Archive Game Launcher v3.X (For Kodi v19+)
#Zach Morris
#https://github.com/zach-morris/plugin.program.iagl
# from kodi_six import xbmc, xbmcplugin, xbmcgui, xbmcvfs
import os
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
			elif post_processor == 'unarchive_neocd_launch_cue':
				xbmc.log(msg='IAGL:  Post processor set to UNZIP to neocdz folder and launch cue file',level=xbmc.LOGDEBUG)
				self.post_processor = self.unzip(settings=self.settings,directory=self.directory,game_list=self.game_list,game=self.game,game_files=self.game_files,to_folder=True,folder_name='neocd',point_to_file='.cue',flatten_archive=True)
			elif post_processor == 'unzip_and_launch_file':
				xbmc.log(msg='IAGL:  Post processor set to UNZIP and launch file',level=xbmc.LOGDEBUG)
				self.post_processor = self.unzip(settings=self.settings,directory=self.directory,game_list=self.game_list,game=self.game,game_files=self.game_files,to_folder=False,use_emu_command=True)
			elif post_processor == 'unarchive_game_launch_cue':
				xbmc.log(msg='IAGL:  Post processor set to UNZIP and launch CUE file',level=xbmc.LOGDEBUG)
				self.post_processor = self.unzip(settings=self.settings,directory=self.directory,game_list=self.game_list,game=self.game,game_files=self.game_files,point_to_file='.cue')
			elif post_processor == 'unzip_and_launch_scummvm_file':
				xbmc.log(msg='IAGL:  Post processor set to UNZIP and launch SCUMMVM file',level=xbmc.LOGDEBUG)
				self.post_processor = self.unzip(settings=self.settings,directory=self.directory,game_list=self.game_list,game=self.game,game_files=self.game_files,to_folder=True,generate_pointer_file='.scummvm')
			elif post_processor == 'unzip_and_launch_win31_file':
				xbmc.log(msg='IAGL:  Post processor set to UNZIP and launch WIN31 BAT file',level=xbmc.LOGDEBUG)
				self.post_processor = self.unzip(settings=self.settings,directory=self.directory,game_list=self.game_list,game=self.game,game_files=self.game_files,to_folder=True,generate_pointer_file='.bat',pointer_file_contents='@echo off\r\npath=%path%;\r\ncopy c:\\iniback\\*.* c:\\windows\\\r\nsetini c:\windows\system.ini boot shell "C:\XXEMU_COMMANDXX"\r\nc:\r\ncd \\\r\nc:\\windows\\win\r\n')
			elif post_processor == 'unzip_and_launch_exodos_file':
				xbmc.log(msg='IAGL:  Post processor set to UNZIP and launch EXODOS conf file',level=xbmc.LOGDEBUG)
				self.post_processor = self.unzip(settings=self.settings,directory=self.directory,game_list=self.game_list,game=self.game,game_files=self.game_files,to_folder=True,generate_pointer_file='.conf',pointer_file_contents=self.game.get('emu_command'))
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
			if show_progress:
				current_dialog = xbmcgui.DialogProgressBG()
				current_dialog.create(loc_str(30377),loc_str(30379))
			for ii,gf in enumerate(self.game_files):
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
				if show_progress:
					current_dialog.update(int(100*(ii+1)/(len(self.game_files)+.001)),loc_str(30377),loc_str(30379))
			if show_progress:
				xbmc.executebuiltin('Dialog.Close(extendedprogressdialog,true)')
				check_and_close_notification(notification_id='extendedprogressdialog')
				del current_dialog
		else:
			xbmc.log(msg='IAGL:  Badly formed game post process request.',level=xbmc.LOGERROR)
			return None
		#After download and post process, if the file(s) need to be copied to the local filesystem, do it here
		if self.settings.get('download').get('copy_network_to_local') and any([x for x in game_pp_status if (isinstance(x.get('post_process_launch_file'),str) or isinstance(x.get('post_process_launch_file'),Path)) and ('smb:' in str(x.get('post_process_launch_file')) or 'nfs:' in str(x.get('post_process_launch_file')))]):
			if game_pp_status[0].get('post_processor') in ['unzip_and_launch_file','unzip_and_launch_scummvm_file','unzip_and_launch_win31_file','unzip_and_launch_exodos_file']:
				#Copy parent directory, point to same file
				xbmc.log(msg='IAGL:  Copying Kodi Network sourced folder %(value)s to local filesystem temporary cache for launching'%{'value':Path(game_pp_status[0].get('post_process_launch_file')).parent},level=xbmc.LOGDEBUG)
				network_folder_name = Path(game_pp_status[0].get('post_process_launch_file')).parent.name
				copied_files, copy_success = copy_directory_xbmcvfs(directory_in=game_pp_status[0].get('post_process_launch_file').rsplit(network_folder_name,1)[0],directory_out=get_dest_as_str(self.directory.get('userdata').get('game_cache').get('path').joinpath(network_folder_name)))
				if all(copied_files):
					game_pp_status[0]['post_process_success'] = True
					game_pp_status[0]['post_process_message'] = 'Copied folder to local filesystem'
					game_pp_status[0]['post_process_launch_file'] = self.directory.get('userdata').get('game_cache').get('path').joinpath(network_folder_name,Path(game_pp_status[0].get('post_process_launch_file')).name)
				else:
					game_pp_status[0]['post_process_success'] = False
					game_pp_status[0]['post_process_message'] = 'Copied folder to local filesystem failed'
			elif game_pp_status[0].get('post_processor') in ['unzip_to_folder_and_launch_file']:
				#Copy parent directory, point to same file
				xbmc.log(msg='IAGL:  Copying Kodi Network sourced folder %(value)s to local filesystem temporary cache for launching (type 2)'%{'value':Path(game_pp_status[0].get('post_process_launch_file')).parent},level=xbmc.LOGDEBUG)
				network_folder_name = Path(game_pp_status[0].get('post_process_launch_file')).parent.name
				copied_files, copy_success = copy_directory_xbmcvfs(directory_in=os.path.join(game_pp_status[0].get('post_process_launch_file').rsplit(network_folder_name,1)[0],network_folder_name),directory_out=get_dest_as_str(self.directory.get('userdata').get('game_cache').get('path').joinpath(network_folder_name)))
				if all(copied_files):
					game_pp_status[0]['post_process_success'] = True
					game_pp_status[0]['post_process_message'] = 'Copied folder to local filesystem'
					game_pp_status[0]['post_process_launch_file'] = self.directory.get('userdata').get('game_cache').get('path').joinpath(network_folder_name,Path(game_pp_status[0].get('post_process_launch_file')).name)
				else:
					game_pp_status[0]['post_process_success'] = False
					game_pp_status[0]['post_process_message'] = 'Copied folder to local filesystem failed'
			elif game_pp_status[0].get('post_processor') in ['unarchive_game_launch_cue']:
				#Copy cue and iso/bin, point to cue
				xbmc.log(msg='IAGL:  Copying Kodi Network sourced ISO/BIN and CUE files %(value)s to local filesystem temporary cache for launching'%{'value':game_pp_status[0].get('post_process_launch_file')},level=xbmc.LOGDEBUG)
				files_to_copy = [x for x in get_all_files_in_directory_xbmcvfs(get_dest_as_str(Path(game_pp_status[0].get('post_process_launch_file')).parent)) if Path(game_pp_status[0].get('post_process_launch_file')).stem in os.path.split(os.path.splitext(x)[0])[-1] and ('bin' in os.path.splitext(x)[-1].lower() or 'iso' in os.path.splitext(x)[-1].lower())]
				if len(files_to_copy) > 0:
					files_to_copy.append(game_pp_status[0].get('post_process_launch_file'))
					overall_copy_success = all([copy_file_xbmcvfs(file_in=ftc,path_in=self.directory.get('userdata').get('game_cache').get('path')) for ftc in files_to_copy])
					if overall_copy_success:
						game_pp_status[0]['post_process_success'] = True
						game_pp_status[0]['post_process_message'] = 'Copied folder to local filesystem'
						game_pp_status[0]['post_process_launch_file'] = self.directory.get('userdata').get('game_cache').get('path').joinpath(Path(game_pp_status[0].get('post_process_launch_file')).name)
					else:
						game_pp_status[0]['post_process_success'] = False
						game_pp_status[0]['post_process_message'] = 'Copied folder to local filesystem failed'
				else:
					game_pp_status[0]['post_process_success'] = False
					game_pp_status[0]['post_process_message'] = 'Unable to locate ISO/BIN files on the Network Share'
			elif game_pp_status[0].get('post_processor') in ['unarchive_neocd_launch_cue']:
				#Copy cue and bin to a neocd folder, point to cue
				xbmc.log(msg='IAGL:  Copying Kodi Network sourced NEOCD BIN and CUE files %(value)s to local filesystem temporary cache for launching'%{'value':game_pp_status[0].get('post_process_launch_file')},level=xbmc.LOGDEBUG)
				files_to_copy = [x for x in get_all_files_in_directory_xbmcvfs(get_dest_as_str(Path(game_pp_status[0].get('post_process_launch_file')).parent)) if Path(game_pp_status[0].get('post_process_launch_file')).stem in os.path.split(os.path.splitext(x)[0])[-1] and 'bin' in os.path.splitext(x)[-1].lower()]
				if len(files_to_copy) > 0:
					files_to_copy.append(game_pp_status[0].get('post_process_launch_file'))
					overall_copy_success = all([copy_file_xbmcvfs(file_in=ftc,path_in=self.directory.get('userdata').get('game_cache').get('path').joinpath('neocd')) for ftc in files_to_copy])
					if overall_copy_success:
						game_pp_status[0]['post_process_success'] = True
						game_pp_status[0]['post_process_message'] = 'Copied folder to local filesystem'
						game_pp_status[0]['post_process_launch_file'] = self.directory.get('userdata').get('game_cache').get('path').joinpath('neocd',Path(game_pp_status[0].get('post_process_launch_file')).name)
					else:
						game_pp_status[0]['post_process_success'] = False
						game_pp_status[0]['post_process_message'] = 'Copied folder to local filesystem failed'
				else:
					game_pp_status[0]['post_process_success'] = False
					game_pp_status[0]['post_process_message'] = 'Unable to locate BIN files on the Network Share'
			else:
				for ii in range(len(game_pp_status)):
					xbmc.log(msg='IAGL:  Copying Kodi Network sourced file %(value)s to local filesystem temporary cache for launching'%{'value':game_pp_status[ii].get('post_process_launch_file')},level=xbmc.LOGDEBUG)
					if copy_file_xbmcvfs(file_in=game_pp_status[ii].get('post_process_launch_file'),path_in=self.directory.get('userdata').get('game_cache').get('path')):
						game_pp_status[ii]['post_process_success'] = True
						game_pp_status[ii]['post_process_message'] = 'Copied file to local filesystem'
						game_pp_status[ii]['post_process_launch_file'] = self.directory.get('userdata').get('game_cache').get('path').joinpath(Path(game_pp_status[ii].get('post_process_launch_file')).name)
					else:
						game_pp_status[ii]['post_process_success'] = False
						game_pp_status[ii]['post_process_message'] = 'Copy to local filesystem failed'

		return game_pp_status

	class unzip(object):
		def __init__(self,settings=dict(),directory=dict(),game_list=dict(),game=dict(),game_files=dict(),**kwargs):
			self.settings = settings
			self.directory= directory
			self.game_list = game_list
			self.game = game
			self.game_files = game_files
			self.pp_status = dict()
			self.flatten_archive = False
			if kwargs and kwargs.get('to_folder'):
				self.unzip_to_folder = True
			else:
				self.unzip_to_folder = False
			if kwargs and kwargs.get('flatten_archive'):
				self.flatten_archive = True
			if kwargs and kwargs.get('use_emu_command'):
				self.use_emu_command = kwargs.get('use_emu_command')
			else:
				self.use_emu_command = None
			if kwargs and kwargs.get('point_to_file'):
				self.point_to_file = kwargs.get('point_to_file')
			else:
				self.point_to_file = None
			if kwargs and kwargs.get('folder_name'):
				self.folder_name = kwargs.get('folder_name')
			else:
				self.folder_name = None
			if kwargs and kwargs.get('generate_pointer_file'):
				self.pointer_file = kwargs.get('generate_pointer_file')
			else:
				self.pointer_file = None
			if kwargs and kwargs.get('pointer_file_contents'):
				self.pointer_file_contents = kwargs.get('pointer_file_contents')
			else:
				self.pointer_file_contents = None
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
				if self.use_emu_command and kwargs and kwargs.get('emu_command') and any([kwargs.get('emu_command') in str(x) for x in matching_files]):
					self.pp_status['post_process_success'] = True
					self.pp_status['post_process_message'] = 'Existing emu command file found'
					self.pp_status['post_process_launch_file'] = [x for x in matching_files if kwargs.get('emu_command') in str(x)][0]
					xbmc.log(msg='IAGL:  Pointing to the existing emu_command file %(value)s'%{'value':self.pp_status.get('post_process_launch_file')},level=xbmc.LOGDEBUG)
				elif self.point_to_file and any([self.point_to_file==get_file_suffix(x) for x in matching_files]):
					self.pp_status['post_process_success'] = True
					self.pp_status['post_process_message'] = 'Existing %(type)s file type found'%{'type':self.point_to_file}
					self.pp_status['post_process_launch_file'] = [x for x in matching_files if self.point_to_file==get_file_suffix(x)][0]
					xbmc.log(msg='IAGL:  Pointing to the existing file %(value)s'%{'value':self.pp_status.get('post_process_launch_file')},level=xbmc.LOGDEBUG)
				elif self.pointer_file and any([self.pointer_file==get_file_suffix(x) for x in matching_files]):
					self.pp_status['post_process_success'] = True
					self.pp_status['post_process_message'] = 'Existing %(type)s file type found'%{'type':self.pointer_file}
					self.pp_status['post_process_launch_file'] = [x for x in matching_files if self.pointer_file==get_file_suffix(x)][0]
					xbmc.log(msg='IAGL:  Pointing to the existing pointer file %(value)s'%{'value':self.pp_status.get('post_process_launch_file')},level=xbmc.LOGDEBUG)
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
						if self.folder_name:
							directory_out = get_dest_as_str(Path(file).parent.joinpath(self.folder_name)) #Unzip to the specified folder
						else:
							directory_out = get_dest_as_str(Path(file).parent.joinpath(clean_file_folder_name(self.game.get('values').get('label2')))) #Unzip to a 'safe name' folder
					my_archive = archive_tool.archive_tool(archive_file=get_dest_as_str(file),directory_out=directory_out,flatten_archive=self.flatten_archive)
					extracted_files, success = my_archive.extract()
					if success:
						self.pp_status['post_process_success'] = True
						self.pp_status['post_process_message'] = 'Unzip complete'
						if self.use_emu_command:
							if kwargs and kwargs.get('emu_command') and any([os.path.join(*kwargs.get('emu_command').split('/')) in x for x in extracted_files]):
								self.pp_status['post_process_launch_file'] = [x for x in extracted_files if os.path.join(*kwargs.get('emu_command').split('/')) in x][0]
								xbmc.log(msg='IAGL:  Pointing to the extracted emu_command file %(value)s'%{'value':self.pp_status.get('post_process_launch_file')},level=xbmc.LOGDEBUG)
							else:
								xbmc.log(msg='IAGL:  Unable to find the file %(value)s in the extracted files'%{'value':kwargs.get('emu_command')},level=xbmc.LOGERROR)
						elif self.point_to_file:
							if any([self.point_to_file in x.lower() for x in extracted_files]):
								self.pp_status['post_process_launch_file'] = [x for x in extracted_files if self.point_to_file in x.lower()][0]
								xbmc.log(msg='IAGL:  Pointing to the extracted %(type)s file %(value)s'%{'type':self.point_to_file,'value':self.pp_status.get('post_process_launch_file')},level=xbmc.LOGDEBUG)
							else:
								xbmc.log(msg='IAGL:  Unable to find the file type %(value)s in the extracted files'%{'value':self.point_to_file},level=xbmc.LOGERROR)
						elif self.pointer_file:
							if self.pointer_file_contents and kwargs.get('emu_command'):
								current_pointer_file_contents = self.pointer_file_contents.replace('XXEMU_COMMANDXX',kwargs.get('emu_command'))
							else:
								current_pointer_file_contents = kwargs.get('emu_command')
							if self.pointer_file == '.conf' and 'XXGAME_DIRXX' in current_pointer_file_contents:
								current_pointer_file_contents = '\n'.join([x.replace('\\',os.path.sep) if '%GAMEDIR%' in x else x.replace('XXGAME_DIRXX',str(next(iter([x for x in [directory_out,self.directory.get('userdata').get('game_cache').get('path')]]),None))) for x in current_pointer_file_contents.split('[CR]')])
							current_pointer_file = generate_pointer_file(filename_in=file,pointer_file_type=self.pointer_file,pointer_contents=current_pointer_file_contents,directory=directory_out,default_dir=self.directory.get('userdata').get('game_cache').get('path'))
							if current_pointer_file:
								self.pp_status['post_process_launch_file'] = current_pointer_file
								xbmc.log(msg='IAGL:  Pointing to the generated %(type)s file %(value)s'%{'type':self.pointer_file,'value':self.pp_status.get('post_process_launch_file')},level=xbmc.LOGDEBUG)
							else:
								xbmc.log(msg='IAGL:  Unable to generate the requested pointer file type %(value)s'%{'value':self.pointer_file},level=xbmc.LOGERROR)
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
