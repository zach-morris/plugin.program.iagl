#Internet Archive Game Launcher v4.X (For Kodi v19+)
#Zach Morris
#https://github.com/zach-morris/plugin.program.iagl
import xbmc, xbmcgui, xbmcvfs
from pathlib import Path
import archive_tool
# import requests, time, json
# from requests.packages.urllib3.exceptions import InsecureRequestWarning
# requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class post_process(object):
	def __init__(self,config=None,rom=None,game_name=None,process=None,delete_zip_after_extract=True,delete_zip_on_fail=True):
		self.config = config
		self.rom = rom
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

	def set_game_name(self,game_name=None):
		if isinstance(game_name,str):
			self.game_name = game_name
		if self.process is not None:
			self.process.set_game_name(game_name=game_name)

	def set_process(self,process=None):
		if process == 'unzip':
			xbmc.log(msg='IAGL:  Process set to unzip',level=xbmc.LOGDEBUG)
			self.process = self.unzip(config=self.config,rom=self.rom,game_name=self.game_name,delete_zip_after_extract=self.delete_zip_after_extract,delete_zip_on_fail=self.delete_zip_on_fail)
		#Add additional processes here
		else:
			xbmc.log(msg='IAGL:  Process is set to NONE',level=xbmc.LOGDEBUG)
			self.process = self.no_process(config=self.config,rom=self.rom,game_name=self.game_name) #Default processor to no_process
		self.current_processer = process

	def process_games(self):
		#Check for matching files
		return self.process.process_games()
			
	class no_process(object):
		def __init__(self,config=None,rom=None,game_name=None):
			self.config = config
			self.rom = rom
			self.game_name = game_name

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

		def process_games(self): #No process = just pass the first game file back to launch
			output = dict()
			if isinstance(self.rom,list):
				output['rom'] = self.rom
				output['launch_file'] = next(iter([str(x.get('dl_filepath') or r.get('matching_files')) for x in self.rom]),None)
				if isinstance(output.get('launch_file'),str) and xbmcvfs.exists(output.get('launch_file')):
					output['process_success'] = True
					xbmc.log(msg='IAGL:  Passthrough process completed, launch file is {}'.format(output.get('launch_file')),level=xbmc.LOGDEBUG)
				else:
					output['process_success'] = False
					xbmc.log(msg='IAGL:  Passthrough process could not find launch file {}'.format(output.get('launch_file')),level=xbmc.LOGDEBUG)
			return output

	class unzip(object):
		def __init__(self,config=None,rom=None,game_name=None,flatten_archive=False,delete_zip_after_extract=True,delete_zip_on_fail=True):
			self.config = config
			self.rom = rom
			self.game_name = game_name
			self.flatten_archive = flatten_archive
			self.delete_zip_after_extract = delete_zip_after_extract
			self.delete_zip_on_fail = delete_zip_on_fail

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

		def set_game_name(self,game_name=None):
			if isinstance(game_name,str):
				self.game_name = game_name

		def process_games(self): #No process = just pass the first game file back to launch
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
						my_archive = archive_tool.archive_tool(archive_file=str(r.get('dl_filepath')),directory_out=str(r.get('dl_filepath').parent),flatten_archive=self.flatten_archive)
						extracted_files, success = my_archive.extract()
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
							output['process_success'] = False
							xbmc.log(msg='IAGL:  Unzip failed to complete',level=xbmc.LOGERROR)
							if self.delete_zip_on_fail:
								self.delete_file(str(r.get('dl_filepath')))
			return output
