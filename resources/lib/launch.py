#Internet Archive Game Launcher v4.X (For Kodi v19+)
#Zach Morris
#https://github.com/zach-morris/plugin.program.iagl
import xbmc, xbmcgui, xbmcvfs
from pathlib import Path
from queue import Queue, Empty
from threading import Thread
from subprocess import Popen, TimeoutExpired, PIPE, STDOUT

class launch(object):
	def __init__(self,config=None,rom=None,list_item=None,game_name=None,launcher=None,launch_parameters=None,user_launch_os=None,kodi_suspend=None,kodi_media_stop=None,kodi_saa=None,kodi_wfr=None,applaunch=None,appause=None):
		self.config = config
		self.rom = rom
		self.list_item = list_item
		self.game_name = game_name
		self.launch_parameters = launch_parameters
		self.kodi_media_stop = kodi_media_stop
		self.user_launch_os=user_launch_os
		self.kodi_suspend=kodi_suspend
		self.kodi_saa=kodi_saa
		self.kodi_wfr=kodi_wfr
		self.appause=appause
		self.applaunch=applaunch
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
			if self.user_launch_os in self.config.settings.get('user_launch_os').get('android_options'):
				self.launcher = self.external_android(config=self.config,rom=self.rom,game_name=self.game_name,launch_parameters=self.launch_parameters,kodi_suspend=self.kodi_suspend,kodi_media_stop=self.kodi_media_stop,kodi_saa=self.kodi_saa,kodi_wfr=self.kodi_wfr)
			elif self.user_launch_os is not None:
				self.launcher = self.external(config=self.config,rom=self.rom,game_name=self.game_name,launch_parameters=self.launch_parameters,kodi_suspend=self.kodi_suspend,kodi_media_stop=self.kodi_media_stop,kodi_wfr=self.kodi_wfr,appause=self.appause,applaunch=self.applaunch)
			else:
				xbmc.log(msg='IAGL:  No User OS set in launch settings',level=xbmc.LOGERROR)
		else:
			xbmc.log(msg='IAGL:  Launcher set to retroplayer',level=xbmc.LOGDEBUG)
			self.launcher = self.retroplayer(config=self.config,rom=self.rom,game_name=self.game_name,launch_parameters=self.launch_parameters,kodi_media_stop=self.kodi_media_stop) #Default launcher to retroplayer
		self.current_launcher = launcher

	def launch_game(self):
		return self.launcher.launch()
			
	class retroplayer(object):
		def __init__(self,config=None,rom=None,list_item=None,game_name=None,launch_parameters=None,kodi_media_stop=None):
			self.config = config
			self.rom = rom
			self.list_item = list_item
			self.game_name = game_name
			self.launch_parameters = launch_parameters
			self.kodi_media_stop = kodi_media_stop

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
				if xbmc.Player().isPlaying(): #and self.kodi_media_stop, for retroplayer currently, stopping current media seems the only way to work
					xbmc.Player().stop()
					xbmc.sleep(self.config.defaults.get('wait_for_stop_time')) #If sleep is not called, Kodi will crash - does not like playing video and then swiching to a game
				xbmc.log(msg='IAGL:  Attempting to start game {}'.format(self.game_name),level=xbmc.LOGINFO)
				xbmc.Player().play(item=self.rom.get('launch_file'),listitem=self.list_item)
				xbmc.sleep(self.config.defaults.get('wait_for_player_time')) #Wait for player or select dialog
				if xbmc.Player().isPlayingGame() or xbmc.Player().isPlaying():
					self.rom['launch_success'] = True
					self.rom['launch_message'] = 'Playing game: {}'.format(self.game_name)
					xbmc.log(msg='IAGL:  Playing game: {}'.format(self.game_name),level=xbmc.LOGINFO)
				elif xbmcgui.getCurrentWindowDialogId() in [10820,10821,10822,10823,10824,10825,10826,10827,12000,10101]:
					self.rom['launch_success'] = True
					self.rom['launch_message'] = 'Launched Retroplayer for game: {}'.format(self.game_name)
					xbmc.log(msg='IAGL:  Launched Retroplayer for game {}'.format(self.game_name),level=xbmc.LOGINFO)
				else:
					self.rom['launch_success'] = False
					self.rom['launch_message'] = 'Failed launch for game: {}'.format(self.game_name)
					xbmc.log(msg='IAGL:  Failed launch for game: {}'.format(self.game_name),level=xbmc.LOGERROR)
			else:
				self.rom['launch_success'] = False
				self.rom['launch_message'] = 'Unexpected launch file'
				xbmc.log(msg='IAGL:  Launch file is malformed: {}'.format(self.rom.get('launch_file')),level=xbmc.LOGERROR)

			return self.rom

	class external(object):
		def __init__(self,config=None,rom=None,game_name=None,launch_parameters=None,kodi_suspend=None,kodi_media_stop=None,kodi_wfr=None,appause=None,applaunch=None):
			self.config = config
			self.rom = rom
			self.game_name = game_name
			self.launch_parameters = launch_parameters
			self.kodi_media_stop = kodi_media_stop
			self.kodi_suspend = kodi_suspend
			self.kodi_wfr = kodi_wfr
			self.appause = appause
			self.applaunch = applaunch
			self.current_launch_command = None
			self.io_is_suspended = False
			self.current_launch_log = list()

		def set_rom(self,rom=None):
			if isinstance(rom,dict):
				self.rom = rom

		def set_game_name(self,game_name=None):
			if isinstance(game_name,str):
				self.game_name = game_name

		def set_launch_parameters(self,launch_parameters=None):
			if isinstance(launch_parameters,dict):
				self.launch_parameters = launch_parameters

		def generate_launch_command(self):
			if isinstance(self.launch_parameters,dict) and isinstance(self.launch_parameters.get('launch_process'),str):
				self.current_launch_command = self.launch_parameters.get('launch_process')
			if isinstance(self.current_launch_command,str):
				if isinstance(self.rom,dict) and isinstance(self.rom.get('launch_file'),str):
					self.current_launch_command = self.current_launch_command.replace('XXROM_PATHXX',self.rom.get('launch_file'))
				if isinstance(self.launch_parameters.get('netplay'),str):
					self.current_launch_command = self.current_launch_command.replace(' XXNETPLAY_COMMANDXX',self.rom.get('netplay'))
				else:
					self.current_launch_command = self.current_launch_command.replace(' XXNETPLAY_COMMANDXX','') #If no netplay command was provided, remove the keyword
				xbmc.log(msg='IAGL:  External command generated:  {}'.format(self.current_launch_command),level=xbmc.LOGDEBUG)

		def enqueue_output(self,out,queue):
			for line in iter(out.readline, b''):
				queue.put(line)
			out.close()

		def launch(self):
			self.generate_launch_command()
			if isinstance(self.current_launch_command,str):
				if self.kodi_media_stop and xbmc.Player().isPlaying():
					xbmc.Player().stop()
					xbmc.sleep(self.config.defaults.get('wait_for_stop_time')) #If sleep is not called, Kodi will crash - does not like playing video and then swiching to a game

				if self.kodi_suspend and self.appause=='0' and self.applaunch=='0':  #Only disbable audio and joystick if enabled in settings and Kodi is not about to be suspended or closed
					xbmc.log(msg='IAGL:  Stopping the Kodi Audio and joystick inputs for external launching',level=xbmc.LOGDEBUG)
					xbmc.audioSuspend()
					xbmc.enableNavSounds(False)
					xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Settings.SetSettingValue","params":{"setting":"input.enablejoystick","value":false},"id":"1"}')
					self.io_is_suspended = True

				#Insert external launch code here
				xbmc.log(msg='IAGL:  Launching game with command:\n{}'.format(self.current_launch_command),level=xbmc.LOGINFO)
				launch_process=Popen(self.current_launch_command,stdout=PIPE,stderr=STDOUT,shell=True)
				
				#Capture launch process log output
				if self.appause=='0' and self.applaunch=='0':
					q = Queue()
					t = Thread(target=self.enqueue_output,args=(launch_process.stdout,q))
					t.daemon = True # thread dies with the program
					t.start()
					xbmc.sleep(self.config.defaults.get('wait_for_player_time')) #Wait for launching to occur in the process before capturing log
					while True:
						try:
							current_line = q.get_nowait()
						except:
							current_line = None
						if current_line and len(self.current_launch_log)<500: #Read up to first 500 lines of output if available
							self.current_launch_log.append(current_line.decode('utf-8',errors='ignore').replace('\n','').replace('\r',''))
						else:
							break

					if launch_process.poll() is None or (isinstance(self.current_launch_log,list) and len(self.current_launch_log)>0 and any(['starting: intent' in x.lower() for x in self.current_launch_log]) and not any(['error: activity' in x.lower() for x in self.current_launch_log])):  #Check if process is running, for android we can only see the intent was starting (if we're not using startandroidactivity)
						self.rom['launch_success'] = True
						self.rom['launch_message'] = 'Playing game {}'.format(self.game_name)
						xbmc.log(msg='IAGL:  Playing game {}'.format(self.game_name),level=xbmc.LOGINFO)
						if isinstance(self.current_launch_log,list) and len(self.current_launch_log)>0:
							xbmc.log(msg='IAGL:  Log output for {}'.format(self.game_name),level=xbmc.LOGDEBUG)
							for cl in self.current_launch_log:
								xbmc.log(msg='IAGL EXT LOG:  {}'.format(cl),level=xbmc.LOGDEBUG)
						self.kodi_wfr 
						dp = xbmcgui.DialogProgress()
						dp.create('Please Wait','Waiting for game to exit...')
						perc = 0
						dp.update(perc,'Waiting for game to exit...')
						returned_to_kodi=False
						check=None
						xbmc.log(msg='IAGL:  Waiting game to exit...',level=xbmc.LOGDEBUG)
						while not returned_to_kodi:
							try:
								check = launch_process.wait(timeout=self.config.defaults.get('wait_for_process_time'))
							except TimeoutExpired:
								perc=perc+10
								dp.update(perc%100,'Waiting for game to exit...')
								returned_to_kodi=False
								check=None
							if dp.iscanceled():
								xbmc.log(msg='IAGL:  User has cancelled waiting for the game to exit',level=xbmc.LOGDEBUG)
								returned_to_kodi=True
								dp.close()
								break
							if isinstance(check,int):
								xbmc.log(msg='IAGL:  Detected the game has exited',level=xbmc.LOGDEBUG)
								returned_to_kodi = True
								dp.close()
								break
							if returned_to_kodi:
								dp.close()
								break
						del dp
					else:
						self.rom['launch_success'] = False
						self.rom['launch_message'] = 'Game did not launch {}'.format(self.game_name)
						xbmc.log(msg='IAGL:  Sent the launch command but the game doesnt appear to be running: {}'.format(self.game_name),level=xbmc.LOGINFO)
						if isinstance(self.current_launch_log,list) and len(self.current_launch_log)>0:
							xbmc.log(msg='IAGL:  Log output for {}'.format(self.game_name),level=xbmc.LOGDEBUG)
							for cl in self.current_launch_log:
								xbmc.log(msg='IAGL EXT LOG:  {}'.format(cl),level=xbmc.LOGDEBUG)				
				else:  #Closing Kodi or suspending Kodi
					xbmc.log(msg='IAGL:  Launch command sent, expecting Kodi to shutdown or suspend...',level=xbmc.LOGDEBUG)
					self.rom['launch_success'] = False  #Leaving false for now, not sure if I can update db in time / before Kodi shuts down...
					self.rom['launch_message'] = 'Game with shutdown launch {}'.format(self.game_name)

				if self.io_is_suspended: #Re-enable audio and joystick if it was previously suspended
					xbmc.log(msg='IAGL:  Resuming the Kodi Audio and joystick inputs',level=xbmc.LOGDEBUG)
					xbmc.audioResume()
					xbmc.enableNavSounds(True)
					xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Settings.SetSettingValue","params":{"setting":"input.enablejoystick","value":true},"id":"1"}')
			else:
				self.rom['launch_success'] = False
				self.rom['launch_message'] = 'Launch command could not be generated'
				xbmc.log(msg='IAGL:  Unable to generate the launch command for: {}'.format(self.rom.get('launch_file')),level=xbmc.LOGERROR)

			return self.rom