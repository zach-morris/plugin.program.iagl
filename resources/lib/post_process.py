#Internet Archive Game Launcher v4.X (For Kodi v19+)
#Zach Morris
#https://github.com/zach-morris/plugin.program.iagl
import xbmc, xbmcgui, xbmcvfs
from pathlib import Path
import archive_tool
from urllib.parse import unquote_plus as url_unquote
# import requests, time, json
# from requests.packages.urllib3.exceptions import InsecureRequestWarning
# requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class post_process(object):
	def __init__(self,config=None,rom=None,launch_parameters=None,game_name=None,process=None,delete_zip_after_extract=True,delete_zip_on_fail=True):
		self.config = config
		self.rom = rom
		self.launch_parameters = launch_parameters
		self.game_name = game_name
		self.delete_zip_after_extract = delete_zip_after_extract
		self.delete_zip_on_fail = delete_zip_on_fail
		self.set_process(process=process)

	def set_rom(self,rom=None):
		if isinstance(rom,dict):
			self.rom = [rom]
		elif isinstance(rom,list):
			self.rom = rom
		else:
			self.rom = None
		if self.process is not None:
			self.process.set_rom(rom=self.rom)

	def set_launch_parameters(self,launch_parameters=None):
		if isinstance(launch_parameters,dict):
			self.launch_parameters = launch_parameters
		else:
			self.launch_parameters = None
		if self.process is not None:
			self.process.set_launch_parameters(launch_parameters=self.launch_parameters)

	def set_game_name(self,game_name=None):
		if isinstance(game_name,str):
			self.game_name = game_name
		if self.process is not None:
			self.process.set_game_name(game_name=game_name)

	def set_process(self,process=None):
		if process == 'unzip':
			xbmc.log(msg='IAGL:  Process set to unzip',level=xbmc.LOGDEBUG)
			self.process = self.unzip(config=self.config,rom=self.rom,launch_parameters=self.launch_parameters,game_name=self.game_name,delete_zip_after_extract=self.delete_zip_after_extract,delete_zip_on_fail=self.delete_zip_on_fail)
		elif process == 'unzip_to_folder':
			xbmc.log(msg='IAGL:  Process set to unzip to folder',level=xbmc.LOGDEBUG)
			self.process = self.unzip(config=self.config,rom=self.rom,unzip_to_folder=True,launch_parameters=self.launch_parameters,game_name=self.game_name,delete_zip_after_extract=self.delete_zip_after_extract,delete_zip_on_fail=self.delete_zip_on_fail)
		elif process == 'unzip_skip_bios':
			xbmc.log(msg='IAGL:  Process set to unzip, skipping BIOS',level=xbmc.LOGDEBUG)
			self.process = self.unzip(config=self.config,rom=self.rom,skip_roms=True,launch_parameters=self.launch_parameters,game_name=self.game_name,delete_zip_after_extract=self.delete_zip_after_extract,delete_zip_on_fail=self.delete_zip_on_fail)
		elif process == 'move_chd_to_folder':
			self.process = self.move_chd_to_folder(config=self.config,rom=self.rom,launch_parameters=self.launch_parameters,game_name=self.game_name)
		else:
			xbmc.log(msg='IAGL:  Process is set to NONE',level=xbmc.LOGDEBUG)
			self.process = self.no_process(config=self.config,rom=self.rom,launch_parameters=self.launch_parameters,game_name=self.game_name) #Default processor to no_process
		self.current_processer = process

	def process_games(self):
		#Check for matching files
		return self.process.process_games()
			
	class no_process(object):
		def __init__(self,config=None,rom=None,launch_parameters=None,game_name=None):
			self.config = config
			self.rom = rom
			self.launch_parameters = launch_parameters
			self.game_name = game_name

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

		def process_games(self): #No process = just pass the first game file back to launch
			output = dict()
			if isinstance(self.rom,list):
				output['rom'] = self.rom
				output['launch_file'] = next(iter([str(x.get('dl_filepath') or x.get('matching_files')) for x in self.rom]),None)
				if isinstance(output.get('launch_file'),str) and xbmcvfs.exists(output.get('launch_file')):
					output['process_success'] = True
					xbmc.log(msg='IAGL:  Passthrough process completed, launch file is {}'.format(output.get('launch_file')),level=xbmc.LOGDEBUG)
				else:
					output['process_success'] = False
					xbmc.log(msg='IAGL:  Passthrough process could not find launch file {}'.format(output.get('launch_file')),level=xbmc.LOGDEBUG)
			#Further processing required for launch_parameter games
			if output.get('process_success') == True and isinstance(self.launch_parameters,dict):
				xbmc.log(msg='IAGL:  Launch parameters found',level=xbmc.LOGDEBUG)
				if isinstance(self.launch_parameters.get('launch_file'),dict):
					if self.launch_parameters.get('launch_file').get('type') == 'generate':
						if self.launch_parameters.get('launch_file').get('file_type') == 'm3u':
							if isinstance(self.launch_parameters.get('launch_file').get('contents'),str):
								xbmc.log(msg='IAGL:  Generating m3u file for launching',level=xbmc.LOGDEBUG)
								new_launch_filename = self.launch_parameters.get('launch_file').get('file_name') or Path(output['launch_file']).name
								new_launch_filepath = Path(output['launch_file']).parent.joinpath(new_launch_filename)
								if new_launch_filepath.parent.exists():
									if new_launch_filepath.exists():  #Launch file had already been written previously
										output['launch_file'] = str(new_launch_filepath)
										xbmc.log(msg='IAGL:  New launch file (pre-existing): {}'.format(output['launch_file']),level=xbmc.LOGDEBUG)
									else:
										new_launch_filepath.write_text(self.launch_parameters.get('launch_file').get('contents'))
										if new_launch_filepath.exists():
											output['launch_file'] = str(new_launch_filepath)
											xbmc.log(msg='IAGL:  New launch file: {}'.format(output['launch_file']),level=xbmc.LOGDEBUG)
										else:
											xbmc.log(msg='IAGL:  Error generating m3u launch file: {}'.format(output['launch_file']),level=xbmc.LOGERROR)
							else:
								xbmc.log(msg='IAGL:  m3u launch file generation failed (contents undefined)',level=xbmc.LOGERROR)
						else:
							xbmc.log(msg='IAGL:  Uknown launch file generation type: {}'.format(self.launch_parameters.get('launch_file').get('file_type')),level=xbmc.LOGERROR)
					else:
						xbmc.log(msg='IAGL:  Uknown post process type: {}'.format(self.launch_parameters.get('launch_file').get('type')),level=xbmc.LOGERROR)
				else:
					xbmc.log(msg='IAGL:  Uknown Launch parameter key: {}'.format(self.launch_parameters.keys()),level=xbmc.LOGERROR)
			return output

	class unzip(object):
		def __init__(self,config=None,rom=None,skip_roms=False,roms_to_skip=None,unzip_to_folder=False,folder_name=None,launch_parameters=None,game_name=None,flatten_archive=False,delete_zip_after_extract=True,delete_zip_on_fail=True,succeed_on_non_archive=True):
			self.supported_archives = '.7z|.tar.gz|.tar.bz2|.tar.xz|.zip|.rar|.tgz|.tbz2|.gz|.bz2|.xz|.cbr|.rar|.001|.cbr'.split('|') #https://github.com/xbmc/vfs.libarchive/blob/master/vfs.libarchive/addon.xml.in, https://github.com/xbmc/vfs.rar/blob/master/vfs.rar/addon.xml.in
			self.config = config
			self.rom = rom
			self.skip_roms = skip_roms
			self.roms_to_skip = roms_to_skip
			self.unzip_to_folder = unzip_to_folder
			self.launch_parameters = launch_parameters
			self.game_name = game_name
			self.folder_name = folder_name
			self.flatten_archive = flatten_archive
			self.delete_zip_after_extract = delete_zip_after_extract
			self.delete_zip_on_fail = delete_zip_on_fail
			self.succeed_on_non_archive = succeed_on_non_archive

		def delete_file(self,file_in=None):
			success = False
			if isinstance(file_in,str) and xbmcvfs.exists(file_in):
				success = xbmcvfs.delete(file_in)
				if success:
					xbmc.log(msg='IAGL:  ZIP File deleted {}'.format(file_in),level=xbmc.LOGDEBUG)
				else:
					xbmc.log(msg='IAGL:  Unable to delete ZIP file {}'.format(file_in),level=xbmc.LOGDEBUG)
			return success

		def set_rom(self,rom=None):
			if isinstance(rom,dict):
				self.rom = [rom]
			elif isinstance(rom,list):
				self.rom = rom
			else:
				self.rom = None
			if self.unzip_to_folder==True and isinstance(self.rom,list):
				self.set_folder_name(folder_name=next(iter([Path(url_unquote(x.get('url'))).stem for x in self.rom if isinstance(x,dict) and isinstance(x.get('url'),str)]),None))
			if self.skip_roms==True and isinstance(self.rom,list):
				self.set_roms_to_skip(roms_to_skip=[x for x in self.rom if Path(x.get('dl_filepath')).name in self.config.defaults.get('unzip_skip_bios_files')])

		def set_roms_to_skip(self,roms_to_skip=None):
			if isinstance(roms_to_skip,dict):
				self.roms_to_skip = [roms_to_skip]
			elif isinstance(roms_to_skip,list):
				self.roms_to_skip = roms_to_skip
			else:
				self.roms_to_skip = None

		def set_launch_parameters(self,launch_parameters=None):
			if isinstance(launch_parameters,dict):
				self.launch_parameters = launch_parameters
			else:
				self.launch_parameters = None

		def set_game_name(self,game_name=None):
			if isinstance(game_name,str):
				self.game_name = game_name

		def set_folder_name(self,folder_name=None):
			if isinstance(folder_name,str):
				self.folder_name = folder_name

		def process_games(self):
			output = dict()
			if isinstance(self.rom,list):
				output['rom'] = self.rom
				for r in self.rom:
					if r.get('matching_file_found'):
						if isinstance(r.get('matching_files'),list) and len(r.get('matching_files'))>0:
							output['launch_file'] = str(r.get('matching_files')[0]) #Only one file found to be matching
							output['process_success'] = True
							if len(r.get('matching_files'))==1:
								xbmc.log(msg='IAGL:  Pointing to the one matching file: {}'.format(output.get('launch_file')),level=xbmc.LOGDEBUG)
							else:
								xbmc.log(msg='IAGL:  Pointing to the first of multiple matching file: {}'.format(output.get('launch_file')),level=xbmc.LOGDEBUG)
						else:
							output['launch_file'] = None
							output['process_success'] = False
							xbmc.log(msg='IAGL:  Matching file could not be found',level=xbmc.LOGERROR)
					else:
						if self.skip_roms and isinstance(self.roms_to_skip,list) and r.get('dl_filepath') in [x.get('dl_filepath') for x in self.roms_to_skip if isinstance(x,dict)]:
							xbmc.log(msg='IAGL:  The following file is in the skip list and will remain archived: {}'.format(r.get('dl_filepath')),level=xbmc.LOGDEBUG)
						else:
							if isinstance(self.folder_name,str):  #Unzip to a specific folder name
								xbmc.log(msg='IAGL:  Unzip to folder set to: {}'.format(self.folder_name),level=xbmc.LOGDEBUG)
								my_archive = archive_tool.archive_tool(archive_file=str(r.get('dl_filepath')),directory_out=str(r.get('dl_filepath').parent.joinpath(self.folder_name)),flatten_archive=self.flatten_archive)
							else:
								my_archive = archive_tool.archive_tool(archive_file=str(r.get('dl_filepath')),directory_out=str(r.get('dl_filepath').parent),flatten_archive=self.flatten_archive)
							if isinstance(r.get('download_size'),int) and r.get('download_size')>self.config.defaults.get('show_extract_progress_size'):  #show extraction progress bigger than X MB in size
								pDialog = xbmcgui.DialogProgressBG()
								pDialog.create('Please Wait','Extracting files...')
							else:
								pDialog = None
							extracted_files, success = my_archive.extract()
							if pDialog is not None:
								pDialog.close()
							if success:
								output['launch_file'] = next(iter(extracted_files),None)
								if isinstance(output.get('launch_file'),str) and xbmcvfs.exists(output.get('launch_file')):
									output['process_success'] = True
									if self.delete_zip_after_extract:
										self.delete_file(str(r.get('dl_filepath')))
								else:
									output['process_success'] = False
									xbmc.log(msg='IAGL:  Unzip completed but the resulting file is missing!',level=xbmc.LOGERROR)
									if self.delete_zip_on_fail:
										self.delete_file(str(r.get('dl_filepath')))
							else:
								if self.succeed_on_non_archive and Path(r.get('dl_filepath')).suffix.lower() not in self.supported_archives:
									xbmc.log(msg='IAGL:  Unzip did not occur because the file appears to already be unpacked.  Attempting to continue...',level=xbmc.LOGDEBUG)
									output['process_success'] = True
									output['launch_file'] = str(r.get('dl_filepath'))
								else:
									output['process_success'] = False
									xbmc.log(msg='IAGL:  Unzip failed to complete',level=xbmc.LOGERROR)
									if self.delete_zip_on_fail:
										self.delete_file(str(r.get('dl_filepath')))
			#Further processing required for launch_parameter games
			if output.get('process_success') == True and isinstance(self.launch_parameters,dict):
				xbmc.log(msg='IAGL:  Launch parameters found',level=xbmc.LOGDEBUG)
				if isinstance(self.launch_parameters.get('launch_file'),dict):
					if self.launch_parameters.get('launch_file').get('type') == 'generate':
						if self.launch_parameters.get('launch_file').get('file_type') == 'm3u':
							if isinstance(self.launch_parameters.get('launch_file').get('contents'),str):
								xbmc.log(msg='IAGL:  Generating m3u file for launching',level=xbmc.LOGDEBUG)
								new_launch_filename = self.launch_parameters.get('launch_file').get('file_name') or Path(output['launch_file']).stem+'.m3u'
								new_launch_filepath = Path(output['launch_file']).parent.joinpath(new_launch_filename)
								if new_launch_filepath.parent.exists():
									if new_launch_filepath.exists():  #Launch file had already been written previously
										output['launch_file'] = str(new_launch_filepath)
										xbmc.log(msg='IAGL:  New launch file (pre-existing): {}'.format(output['launch_file']),level=xbmc.LOGDEBUG)
									else:
										new_launch_filepath.write_text(self.launch_parameters.get('launch_file').get('contents'))
										if new_launch_filepath.exists():
											output['launch_file'] = str(new_launch_filepath)
											xbmc.log(msg='IAGL:  New launch file: {}'.format(output['launch_file']),level=xbmc.LOGDEBUG)
										else:
											xbmc.log(msg='IAGL:  Error generating m3u launch file: {}'.format(output['launch_file']),level=xbmc.LOGERROR)
							else:
								xbmc.log(msg='IAGL:  m3u launch file generation failed (contents undefined)',level=xbmc.LOGERROR)
						elif self.launch_parameters.get('launch_file').get('file_type') == 'conf':
							if isinstance(self.launch_parameters.get('launch_file').get('contents'),str):
								xbmc.log(msg='IAGL:  Generating conf file for launching',level=xbmc.LOGDEBUG)
								new_launch_filename = self.launch_parameters.get('launch_file').get('file_name') or Path(output['launch_file']).stem+'.conf'
								new_launch_filepath = Path(output['launch_file']).parent.joinpath(new_launch_filename)
								game_base_dir = str(Path(output['launch_file']).parent)
								if new_launch_filepath.parent.exists():
									if new_launch_filepath.exists():  #Launch file had already been written previously
										output['launch_file'] = str(new_launch_filepath)
										xbmc.log(msg='IAGL:  New launch file (pre-existing): {}'.format(output['launch_file']),level=xbmc.LOGDEBUG)
									else:
										new_launch_filepath.write_text(self.launch_parameters.get('launch_file').get('contents').format(**{'game_base_dir':game_base_dir}))
										if new_launch_filepath.exists():
											output['launch_file'] = str(new_launch_filepath)
											xbmc.log(msg='IAGL:  New launch file: {}'.format(output['launch_file']),level=xbmc.LOGDEBUG)
										else:
											xbmc.log(msg='IAGL:  Error generating conf launch file: {}'.format(output['launch_file']),level=xbmc.LOGERROR)
							else:
								xbmc.log(msg='IAGL:  conf launch file generation failed (contents undefined)',level=xbmc.LOGERROR)
						elif self.launch_parameters.get('launch_file').get('file_type') == 'cmd':
							if isinstance(self.launch_parameters.get('launch_file').get('contents'),str):
								xbmc.log(msg='IAGL:  Generating cmd file for launching',level=xbmc.LOGDEBUG)
								new_launch_filename = self.launch_parameters.get('launch_file').get('file_name') or Path(output['launch_file']).stem+'.cmd'
								new_launch_filepath = Path(output['launch_file']).parent.joinpath(new_launch_filename)
								game_base_dir = str(Path(output['launch_file']).parent)
								if new_launch_filepath.parent.exists():
									if new_launch_filepath.exists():  #Launch file had already been written previously
										output['launch_file'] = str(new_launch_filepath)
										xbmc.log(msg='IAGL:  New launch file (pre-existing): {}'.format(output['launch_file']),level=xbmc.LOGDEBUG)
									else:
										new_launch_filepath.write_text(self.launch_parameters.get('launch_file').get('contents').format(**{'launch_file':Path(output['launch_file']).name}))
										if new_launch_filepath.exists():
											output['launch_file'] = str(new_launch_filepath)
											xbmc.log(msg='IAGL:  New launch file: {}'.format(output['launch_file']),level=xbmc.LOGDEBUG)
										else:
											xbmc.log(msg='IAGL:  Error generating cmd launch file: {}'.format(output['launch_file']),level=xbmc.LOGERROR)
							else:
								xbmc.log(msg='IAGL: cmd launch file generation failed (contents undefined)',level=xbmc.LOGERROR)
						elif self.launch_parameters.get('launch_file').get('file_type') == 'pointer':  #Pointer is the same filename name as the downloaded game with a different suffix, contents is the file_name
							if isinstance(self.launch_parameters.get('launch_file').get('file_name'),str):
								xbmc.log(msg='IAGL:  Generating pointer file for game',level=xbmc.LOGDEBUG)
								if isinstance(self.rom,list):
									pointer_url = next(iter([url_unquote(x.get('url')) for x in self.rom if isinstance(x.get('url'),str)]),None)
									if isinstance(pointer_url,str):
										new_launch_filename = Path(pointer_url).stem+(self.launch_parameters.get('launch_file').get('suffix') or '.scummvm')
										new_launch_filepath = Path(output['launch_file']).parent.joinpath(new_launch_filename)
										if new_launch_filepath.parent.exists():
											if new_launch_filepath.exists():  #Launch file had already been written previously
												output['launch_file'] = str(new_launch_filepath)
												xbmc.log(msg='IAGL:  New pointer file (pre-existing): {}'.format(output['launch_file']),level=xbmc.LOGDEBUG)
											else:
												new_launch_filepath.write_text(self.launch_parameters.get('launch_file').get('file_name'))
												if new_launch_filepath.exists():
													output['launch_file'] = str(new_launch_filepath)
													xbmc.log(msg='IAGL:  New launch file: {}'.format(output['launch_file']),level=xbmc.LOGDEBUG)
												else:
													xbmc.log(msg='IAGL:  Error generating pointer file: {}'.format(output['launch_file']),level=xbmc.LOGERROR)
									else:
										xbmc.log(msg='IAGL:  pointer launch file generation failed (pointer filename undefined)',level=xbmc.LOGERROR)
						else:
							xbmc.log(msg='IAGL:  Uknown launch file generation type: {}'.format(self.launch_parameters.get('launch_file').get('file_type')),level=xbmc.LOGERROR)
					elif self.launch_parameters.get('launch_file').get('type') == 'find':
						if isinstance(self.launch_parameters.get('launch_file').get('filename'),str):
							xbmc.log(msg='IAGL:  Looking for launch file for game: {}'.format(self.launch_parameters.get('launch_file').get('filename')),level=xbmc.LOGDEBUG)
							launch_file_part = str(Path().joinpath(*self.launch_parameters.get('launch_file').get('filename').split('/')))  #Correct any path seperation
							file_listing = [x for x in Path(output.get('launch_file')).parent.rglob('**/*') if launch_file_part in str(x) and x.is_file()]
							if len(file_listing)>0:
								if len(file_listing)>1:
									xbmc.log(msg='IAGL:  More than one file found matching the criteria, pointing to first available file',level=xbmc.LOGDEBUG)
								else:
									xbmc.log(msg='IAGL:  Pointing to the found file: {}'.format(next(iter([str(x) for x in file_listing]),None)),level=xbmc.LOGDEBUG)
								output['launch_file'] = next(iter([str(x) for x in file_listing]),None)
							else:
								xbmc.log(msg='IAGL:  File matching the criteria was not found',level=xbmc.LOGERROR)
						else:
							xbmc.log(msg='IAGL:  pointer launch file generation failed (pointer filename undefined)',level=xbmc.LOGERROR)
					else:
						xbmc.log(msg='IAGL:  Uknown post process type: {}'.format(self.launch_parameters.get('launch_file').get('type')),level=xbmc.LOGERROR)
				else:
					xbmc.log(msg='IAGL:  Uknown Launch parameter key: {}'.format(self.launch_parameters.keys()),level=xbmc.LOGERROR)
			return output

	class move_chd_to_folder(object):
		def __init__(self,config=None,rom=None,launch_parameters=None,game_name=None):
			self.config = config
			self.rom = rom
			self.launch_parameters = launch_parameters
			self.game_name = game_name

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

		def process_games(self): #No process = just pass the first game file back to launch
			output = dict()
			if isinstance(self.rom,list):
				output['rom'] = self.rom
				output['launch_file'] = next(iter([str(x.get('dl_filepath') or x.get('matching_files')) for x in self.rom]),None)
				if isinstance(output.get('launch_file'),str) and xbmcvfs.exists(output.get('launch_file')):
					output['process_success'] = True
					xbmc.log(msg='IAGL:  Move chd to folder process identified launch file as {}'.format(output.get('launch_file')),level=xbmc.LOGDEBUG)
					chd_files = [x for x in self.rom if x.get('dl_filepath').suffix.lower() == '.chd' and x.get('dl_filepath').parent.name!=Path(output['launch_file']).stem]  #Find any chd files that need to be moved
					if len(chd_files)>0:
						chd_folder = Path(output.get('launch_file')).parent.joinpath(Path(output.get('launch_file')).stem)
						chd_folder.mkdir(exist_ok=True)
						xbmc.log(msg='IAGL:  The following files will be moved to the folder {}: {}'.format(chd_folder.name,','.join([x.get('dl_filepath').name for x in chd_files])),level=xbmc.LOGDEBUG)
						for c in chd_files:
							if c.get('dl_filepath').exists():
								c.get('dl_filepath').rename(chd_folder.joinpath(c.get('dl_filepath').name))
				else:
					output['process_success'] = False
					xbmc.log(msg='IAGL:  Move chd to folder process not find launch file {}'.format(output.get('launch_file')),level=xbmc.LOGDEBUG)
			#Further processing required for launch_parameter games
			if output.get('process_success') == True and isinstance(self.launch_parameters,dict):
				xbmc.log(msg='IAGL:  Launch parameters found',level=xbmc.LOGDEBUG)
				if isinstance(self.launch_parameters.get('launch_file'),dict):
					if self.launch_parameters.get('launch_file').get('type') == 'generate':
						if self.launch_parameters.get('launch_file').get('file_type') == 'm3u':
							if isinstance(self.launch_parameters.get('launch_file').get('contents'),str):
								xbmc.log(msg='IAGL:  Generating m3u file for launching',level=xbmc.LOGDEBUG)
								new_launch_filename = self.launch_parameters.get('launch_file').get('file_name') or Path(output['launch_file']).name
								new_launch_filepath = Path(output['launch_file']).parent.joinpath(new_launch_filename)
								if new_launch_filepath.parent.exists():
									if new_launch_filepath.exists():  #Launch file had already been written previously
										output['launch_file'] = str(new_launch_filepath)
										xbmc.log(msg='IAGL:  New launch file (pre-existing): {}'.format(output['launch_file']),level=xbmc.LOGDEBUG)
									else:
										new_launch_filepath.write_text(self.launch_parameters.get('launch_file').get('contents'))
										if new_launch_filepath.exists():
											output['launch_file'] = str(new_launch_filepath)
											xbmc.log(msg='IAGL:  New launch file: {}'.format(output['launch_file']),level=xbmc.LOGDEBUG)
										else:
											xbmc.log(msg='IAGL:  Error generating m3u launch file: {}'.format(output['launch_file']),level=xbmc.LOGERROR)
							else:
								xbmc.log(msg='IAGL:  m3u launch file generation failed (contents undefined)',level=xbmc.LOGERROR)
						else:
							xbmc.log(msg='IAGL:  Uknown launch file generation type: {}'.format(self.launch_parameters.get('launch_file').get('file_type')),level=xbmc.LOGERROR)
					else:
						xbmc.log(msg='IAGL:  Uknown post process type: {}'.format(self.launch_parameters.get('launch_file').get('type')),level=xbmc.LOGERROR)
				else:
					xbmc.log(msg='IAGL:  Uknown Launch parameter key: {}'.format(self.launch_parameters.keys()),level=xbmc.LOGERROR)
			return output