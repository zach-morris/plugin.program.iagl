#Internet Archive Game Launcher v4.X (For Kodi v19+)
#Zach Morris
#https://github.com/zach-morris/plugin.program.iagl
import xbmc, xbmcgui, xbmcvfs
from pathlib import Path
import archive_tool
# import requests, time, json
# from requests.packages.urllib3.exceptions import InsecureRequestWarning
# requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class launch(object):
	def __init__(self,config=None,rom=None,list_item=None,game_name=None,launcher=None,launch_parameters=None,stop_media_on_launch=None):
		self.config = config
		self.rom = rom
		self.list_item = list_item
		self.game_name = game_name
		self.launch_parameters = launch_parameters
		self.stop_media_on_launch = stop_media_on_launch
		self.set_launcher(launcher=launcher)
		self.set_launch_parameters(launch_parameters=launch_parameters)
		self.set_list_item(list_item=list_item)

	def set_rom(self,rom=None):
		if isinstance(rom,dict):
			self.rom = rom
		if self.launcher is not None:
			self.launcher.set_rom(rom=self.rom)

	def set_list_item(self,list_item=None):
		if isinstance(list_item,xbmcgui.ListItem):
			self.list_item = list_item
		if self.launcher is not None:
			self.launcher.set_list_item(list_item=self.list_item)

	def set_game_name(self,game_name=None):
		if isinstance(game_name,str):
			self.game_name = game_name
		if self.launcher is not None:
			self.launcher.set_game_name(game_name=game_name)

	def set_launch_parameters(self,launch_parameters=None):
		if isinstance(launch_parameters,dict):
			self.launch_parameters = launch_parameters
		if self.launcher is not None:
			self.launcher.set_launch_parameters(launch_parameters=launch_parameters)

	def set_launcher(self,launcher=None):
		if launcher == 'external':
			xbmc.log(msg='IAGL:  Launcher set to external',level=xbmc.LOGDEBUG)
			self.launcher = self.external(config=self.config,rom=self.rom,list_item=self.list_item,game_name=self.game_name,launch_parameters=self.launch_parameters,stop_media_on_launch=self.stop_media_on_launch)
		else:
			xbmc.log(msg='IAGL:  Launcher set to retroplayer',level=xbmc.LOGDEBUG)
			self.launcher = self.retroplayer(config=self.config,rom=self.rom,game_name=self.game_name,launch_parameters=self.launch_parameters,stop_media_on_launch=self.stop_media_on_launch) #Default launcher to retroplayer
		self.current_launcher = launcher

	def launch_game(self):
		return self.launcher.launch()
			
	class retroplayer(object):
		def __init__(self,config=None,rom=None,list_item=None,game_name=None,launch_parameters=None,stop_media_on_launch=None):
			self.config = config
			self.rom = rom
			self.list_item = list_item
			self.game_name = game_name
			self.launch_parameters = launch_parameters
			self.stop_media_on_launch = stop_media_on_launch
			self.wait_for_stop_time = 500
			self.wait_for_player_time = 5000

		def set_rom(self,rom=None):
			if isinstance(rom,dict):
				self.rom = rom

		def set_list_item(self,list_item=None):
			if isinstance(list_item,xbmcgui.ListItem):
				self.list_item = list_item
		
		def set_game_name(self,game_name=None):
			if isinstance(game_name,str):
				self.game_name = game_name

		def set_launch_parameters(self,launch_parameters=None):
			if isinstance(launch_parameters,dict):
				self.launch_parameters = launch_parameters

		def launch(self):
			if isinstance(self.rom.get('launch_file'),str) and isinstance(self.list_item,xbmcgui.ListItem):
				if xbmc.Player().isPlaying():
					xbmc.Player().stop()
					xbmc.sleep(self.wait_for_stop_time) #If sleep is not called, Kodi will crash - does not like playing video and then swiching to a game
				xbmc.log(msg='IAGL:  Attempting to start game {}'.format(self.game_name),level=xbmc.LOGINFO)
				xbmc.Player().play(item=self.rom.get('launch_file'),listitem=self.list_item)
				xbmc.sleep(self.wait_for_player_time) #Wait for player or select dialog
				if xbmc.Player().isPlaying():
					self.rom['launch_success'] = True
					self.rom['launch_message'] = 'Playing game {}'.format(self.game_name)
					xbmc.log(msg='IAGL:  Playing game {}'.format(self.game_name),level=xbmc.LOGINFO)
				elif xbmcgui.getCurrentWindowDialogId() in [10820,10821,10822,10823,10824,10825,10826,10827,12000,10101]:
					self.rom['launch_success'] = True
					self.rom['launch_message'] = 'Launched Retroplayer for game {}'.format(self.game_name)
					xbmc.log(msg='IAGL:  Launched Retroplayer for game {}'.format(self.game_name),level=xbmc.LOGINFO)
				else:
					self.rom['launch_success'] = False
					self.rom['launch_message'] = 'Unknown launch status'
					xbmc.log(msg='IAGL:  Unknown launch status for: {}'.format(self.game_name),level=xbmc.LOGERROR)
			else:
				self.rom['launch_success'] = False
				self.rom['launch_message'] = 'Unexpected launch file'
				xbmc.log(msg='IAGL:  Launch file is malformed: {}'.format(self.rom.get('launch_file')),level=xbmc.LOGERROR)

	class external(object):
		def __init__(self,config=None,rom=None,game_name=None,launch_parameters=None,stop_media_on_launch=None):
			self.config = config
			self.rom = rom
			self.game_name = game_name
			self.launch_parameters = launch_parameters
			self.stop_media_on_launch = stop_media_on_launch
			self.wait_for_stop_time = 500
			self.wait_for_player_time = 5000

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

		def set_launch_parameters(self,launch_parameters=None):
			if isinstance(launch_parameters,dict):
				self.launch_parameters = launch_parameters

		def launch(self):
			if isinstance(self.rom,dict) and isinstance(self.rom.get('launch_file'),str):
				if xbmc.Player().isPlaying():
					xbmc.Player().stop()
					xbmc.sleep(self.wait_for_stop_time) #If sleep is not called, Kodi will crash - does not like playing video and then swiching to a game
					xbmc.Player().play(item=self.rom.get('launch_file'),listitem=li)
					xbmc.sleep(self.wait_for_player_time) #Wait for player or select dialog
				if xbmc.Player().isPlaying():
					self.rom['launch_success'] = True
					self.rom['launch_message'] = 'Playing game {}'.format(self.game_name)
					xbmc.log(msg='IAGL:  Playing game {}'.format(self.game_name),level=xbmc.LOGINFO)
				elif xbmcgui.getCurrentWindowDialogId() in [10820,10821,10822,10823,10824,10825,10826,10827,12000,10101]:
					self.rom['launch_success'] = True
					self.rom['launch_message'] = 'Launched Retroplayer for game {}'.format(self.game_name)
					xbmc.log(msg='IAGL:  Launched Retroplayer for game {}'.format(self.game_name),level=xbmc.LOGINFO)
				else:
					self.rom['launch_success'] = False
					self.rom['launch_message'] = 'Unknown launch status'
					xbmc.log(msg='IAGL:  Unknown launch status for: {}'.format(self.game_name),level=xbmc.LOGERROR)
			else:
				self.rom['launch_success'] = False
				self.rom['launch_message'] = 'Unexpected launch file'
				xbmc.log(msg='IAGL:  Launch file is malformed: {}'.format(self.rom.get('launch_file')),level=xbmc.LOGERROR)