#Internet Archive Game Launcher v3.X (For Kodi v19+)
#Zach Morris
#https://github.com/zach-morris/plugin.program.iagl
# from kodi_six import xbmc, xbmcplugin, xbmcgui, xbmcvfs
import xbmc, xbmcplugin, xbmcgui, xbmcvfs
from . utils import *

class iagl_launch(object):
	def __init__(self,settings=dict(),directory=dict(),game_list=dict(),game=dict(),game_files=dict(),launcher=None,netplay=False,netplay_query=None,uuid=None):
		self.settings = settings
		self.directory = directory
		self.game_list = game_list
		self.game = game
		self.game_files = game_files
		self.netplay = netplay
		self.netplay_query = netplay_query
		self.uuid=uuid
		#Default launcher is retroplayer
		self.set_launcher(launcher=launcher)

	def set_launcher(self,launcher=None):
		if isinstance(launcher,str) and launcher == 'external':
			xbmc.log(msg='IAGL:  Launcher set to EXTERNAL',level=xbmc.LOGDEBUG)
			self.launcher = self.external_launch(settings=self.settings,directory=self.directory,game_list=self.game_list,game=self.game,game_files=self.game_files,netplay=self.netplay,netplay_query=self.netplay_query,uuid=self.uuid)
		elif isinstance(launcher,str) and launcher == 'retroplayer':
			xbmc.log(msg='IAGL:  Launcher set to RETROPLAYER',level=xbmc.LOGDEBUG)
			self.launcher = self.retroplayer_launch(settings=self.settings,directory=self.directory,game_list=self.game_list,game=self.game,game_files=self.game_files)
		else:
			xbmc.log(msg='IAGL:  Launcher %(ll)s is unknown, defauling to RETROPLAYER'%{'ll':launcher},level=xbmc.LOGERROR)
			self.launcher = self.retroplayer_launch(settings=self.settings,directory=self.directory,game_list=self.game_list,game=self.game,game_files=self.game_files)
		if self.launcher:
			self.current_launcher = launcher
		else:
			self.current_launcher = None

	def launch_game(self):
		game_launch_status = None
		if self.launcher and self.game_files:
			current_launch = self.game_files[0].copy() #Always use the first processed file to determine which game file to launch
			if current_launch.get('post_process_success') and current_launch.get('post_process_launch_file'):
				if current_launch.get('launcher') and current_launch.get('launcher') != self.current_launcher:
					self.set_launcher(launcher=current_launch.get('launcher'))
				if self.launcher:
					launch_status = self.launcher.launch(launch_files=current_launch)
					current_launch['launch_process_success'] = launch_status.get('launch_process_success')
					current_launch['launch_process_message'] = launch_status.get('launch_process_message')
					current_launch['launch_process'] = launch_status.get('launch_process')
					current_launch['launch_log'] = launch_status.get('launch_log')
				else:
					current_launch['launch_process_success'] = False
					current_launch['launch_process_message'] = 'No launch method set, skipping launch'
					current_launch['launch_process'] = None
					current_launch['launch_log'] = None
			else:
				xbmc.log(msg='IAGL:  The file %(value)s did not succeed the post processing check, launching will be skipped'%{'value':current_launch.get('filename')},level=xbmc.LOGDEBUG)
				current_launch['launch_process_success'] = False
				current_launch['launch_process_message'] = 'Post process check failed, launching skipped'
				current_launch['launch_process'] = None
				current_launch['launch_log'] = None
			game_launch_status = current_launch
		else:
			xbmc.log(msg='IAGL:  Badly formed game launch request.',level=xbmc.LOGERROR)
		if current_launch.get('launch_process_success') and self.settings.get('game_list').get('game_history'):
				success = add_game_to_history(self.game,self.directory.get('userdata').get('list_cache').get('path').joinpath('history.json'),self.settings.get('game_list').get('game_history'))
		return game_launch_status

	def post_launch_check(self,game_launch_status=None,**kwargs):
		if game_launch_status and game_launch_status['launch_process'] and not self.settings.get('ext_launchers').get('close_kodi'):
			from subprocess import TimeoutExpired
			dp = xbmcgui.DialogProgress()
			dp.create(loc_str(30377),loc_str(30380))
			dp.update(0,loc_str(30380))
			perc = 0
			finished=False
			check=None
			while not finished:
				try:
					check = game_launch_status['launch_process'].wait(timeout=WAIT_FOR_PROCESS_EXIT)
				except TimeoutExpired:
					perc=perc+10
					dp.update(perc%100,loc_str(30380))
					finished=False
					check=None
				if dp.iscanceled():
					finished=True
					dp.close()
					break
				if isinstance(check,int):
					finished = True
					dp.close()
					break
				if finished:
					dp.close()
					break
			del dp
			if not self.settings.get('ext_launchers').get('close_kodi') and self.settings.get('ext_launchers').get('stop_audio_controller') and self.settings.get('ext_launchers').get('environment') not in ['android','android_ra32','android_aarch64']:
				xbmc.log(msg='IAGL:  Re-Enabling Audio and Controller Input',level=xbmc.LOGDEBUG)
				xbmc.audioResume()
				xbmc.enableNavSounds(True)
				xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Settings.SetSettingValue","params":{"setting":"input.enablejoystick","value":true},"id":"1"}')

	class retroplayer_launch(object):
		def __init__(self,settings=dict(),directory=dict(),game_list=dict(),game=dict(),game_files=dict(),**kwargs):
			self.settings = settings
			self.directory= directory
			self.game_list = game_list
			self.game = game
			self.game_files = game_files
			self.launch_status = dict()

		def launch(self,launch_files=None,**kwargs):
			if launch_files and launch_files.get('post_process_launch_file'):
				li = get_retroplayer_item_and_listitem(map_retroplayer_listitem_dict(self.game,launch_files),launch_files.get('post_process_launch_file'),media_type='game')
				if xbmc.Player().isPlaying():
					xbmc.Player().stop()
					xbmc.sleep(500) #If sleep is not called, Kodi will crash - does not like playing video and then swiching to a game
				xbmc.Player().play(item=str(launch_files.get('post_process_launch_file')),listitem=li)
				xbmc.sleep(WAIT_FOR_PLAYER_TIME) #Wait for player or select dialog
				if xbmc.Player().isPlaying():
					self.launch_status['launch_process_success'] = True
					self.launch_status['launch_process_message'] = 'Playing %(game)s'%{'game':self.game.get('info').get('originaltitle')}
					xbmc.log(msg='IAGL:  Playing game %(game)s'%{'game':self.game.get('info').get('originaltitle')},level=xbmc.LOGINFO)
				elif xbmcgui.getCurrentWindowDialogId() in [10820,10821,10822,10823,10824,10825,10826,10827,12000,10101]:
					self.launch_status['launch_process_success'] = True
					self.launch_status['launch_process_message'] = 'Launched Retroplayer for %(game)s'%{'game':self.game.get('info').get('originaltitle')}
					xbmc.log(msg='IAGL:  Launched Retroplayer for %(game)s'%{'game':self.game.get('info').get('originaltitle')},level=xbmc.LOGINFO)
				else:
					self.launch_status['launch_process_success'] = False
					self.launch_status['launch_process_message'] = 'Status of launch is unknown for %(game)s'%{'game':self.game.get('info').get('originaltitle')}
					xbmc.log(msg='IAGL:  Status of launch is unknown for %(game)s, current window id %(wid)s'%{'game':self.game.get('info').get('originaltitle'),'wid':xbmcgui.getCurrentWindowDialogId()},level=xbmc.LOGERROR)
			else:
				xbmc.log(msg='IAGL:  Badly formed launch request',level=xbmc.LOGERROR)
				return None
			return self.launch_status

	class external_launch(object):
		def __init__(self,settings=dict(),directory=dict(),game_list=dict(),game=dict(),game_files=dict(),netplay=False,uuid=None,netplay_query=None,**kwargs):
			self.settings = settings
			self.directory= directory
			self.game_list = game_list
			self.game = game
			self.game_files = game_files
			self.launch_status = dict()
			self.current_command = None
			self.netplay = netplay
			self.uuid = uuid
			self.netplay_query = netplay_query

		def launch(self,launch_files=None,**kwargs):
			import subprocess
			capture_launch_log = True #Hard code for now, to add as an advanced setting
			current_output = list()
			if capture_launch_log:
				from queue import Queue, Empty
				from threading import Thread
			if launch_files and launch_files.get('post_process_launch_file') and launch_files.get('ext_launch_cmd') and launch_files.get('ext_launch_cmd')!='none':
				self.current_command = launch_files.get('ext_launch_cmd').replace('%ROM_PATH%',str(launch_files.get('post_process_launch_file')))

				if self.netplay and self.netplay_query is None:
					xbmc.log(msg='IAGL:  Launch game with netplay as host requested',level=xbmc.LOGDEBUG)
					netplay_command = ' --host --nick "%(nn)s (%(ss)s)"'%{'nn':next(iter([x for x in [self.settings.get('game_action').get('netplay_nick'),xbmc.getInfoLabel('System.ProfileName')] if x]),'Kodi Player 1')[0:22],'ss':self.uuid}
					if self.settings.get('game_action').get('netplay_port') and len(self.settings.get('game_action').get('netplay_port')) and self.settings.get('game_action').get('netplay_port').isdigit():
						netplay_command = netplay_command+' --port %(pp)s'%{'pp':self.settings.get('game_action').get('netplay_port')}
					if self.settings.get('game_action').get('netplay_checkframes') and len(self.settings.get('game_action').get('netplay_checkframes')) and self.settings.get('game_action').get('netplay_checkframes').isdigit():
						netplay_command = netplay_command+' --check-frames %(pp)s'%{'pp':self.settings.get('game_action').get('netplay_checkframes')}
					self.current_command = self.current_command.replace(' %NETPLAY_COMMAND%',netplay_command)
				elif self.netplay and self.netplay_query:
					xbmc.log(msg='IAGL:  Launch game with netplay as client requested',level=xbmc.LOGDEBUG)
					if self.settings.get('game_action').get('use_relay'):
						current_host = next(iter([x for x in [self.netplay_query.get('mitm_ip'),self.netplay_query.get('ip'),self.netplay_query.get('host')] if x and len(x)>7]),self.netplay_query.get('ip'))
						current_port = next(iter([x for x in [self.netplay_query.get('mitm_port'),self.netplay_query.get('port')] if x and x != '0']),'55435')
					else:
						current_host = next(iter([x for x in [self.netplay_query.get('ip'),self.netplay_query.get('mitm_ip'),self.netplay_query.get('host')] if x and len(x)>7]),self.netplay_query.get('ip'))
						current_port = next(iter([x for x in [self.netplay_query.get('port'),self.netplay_query.get('mitm_port')] if x and x != '0']),'55435')
					xbmc.log(msg='IAGL:  Netplay Host is {}, Port is {}'.format(str(current_host),str(current_port)),level=xbmc.LOGDEBUG)
					netplay_command = ' --connect %(host)s --port %(pp)s --nick "%(nn)s (%(ss)s)"'%{'host':current_host,'pp':current_port,'nn':next(iter([x for x in [self.settings.get('game_action').get('netplay_nick'),xbmc.getInfoLabel('System.ProfileName')] if x]),'Kodi Player 1')[0:22],'ss':self.uuid}
					# if self.settings.get('game_action').get('netplay_port') and len(self.settings.get('game_action').get('netplay_port')) and self.settings.get('game_action').get('netplay_port').isdigit():
						# netplay_command = netplay_command+' --port %(pp)s'%{'pp':self.settings.get('game_action').get('netplay_port')}
					if self.settings.get('game_action').get('netplay_checkframes') and len(self.settings.get('game_action').get('netplay_checkframes')) and self.settings.get('game_action').get('netplay_checkframes').isdigit():
						netplay_command = netplay_command+' --check-frames %(pp)s'%{'pp':self.settings.get('game_action').get('netplay_checkframes')}
					self.current_command = self.current_command.replace(' %NETPLAY_COMMAND%',netplay_command)
				else:
					xbmc.log(msg='IAGL:  Launch game without netplay requested',level=xbmc.LOGDEBUG)
					self.current_command = self.current_command.replace(' %NETPLAY_COMMAND%','')

				if any([x in self.current_command for x in ['%ADDON_DIR%','%APP_PATH_RA%','%APP_PATH_DEMUL%','%APP_PATH_DOLPHIN%','%APP_PATH_EPSXE%','%APP_PATH_FS_UAE%','%APP_PATH_MAME%','%APP_PATH_PJ64%','%CFG_PATH%','%RETROARCH_CORE_DIR%','%ROM_PATH%','%ROM_RAW%']]):
					command_map = {'%ADDON_DIR%':self.directory.get('addon').get('path'),
									'%APP_PATH_RA%':get_launch_parameter(setting_in=self.settings.get('ext_launchers').get('ra').get('app_path'),return_val='%APP_PATH_RA%'),
									'%APP_PATH_DEMUL%':next(iter([str(x.get('app_path')) for x in self.settings.get('ext_launchers').get('other_ext_cmds') if x.get('app_path_cmd_replace')=='%APP_PATH_DEMUL%']),'%APP_PATH_DEMUL%'),
									'%APP_PATH_DOLPHIN%':next(iter([str(x.get('app_path')) for x in self.settings.get('ext_launchers').get('other_ext_cmds') if x.get('app_path_cmd_replace')=='%APP_PATH_DOLPHIN%']),'%APP_PATH_DOLPHIN%'),
									'%APP_PATH_EPSXE%':next(iter([str(x.get('app_path')) for x in self.settings.get('ext_launchers').get('other_ext_cmds') if x.get('app_path_cmd_replace')=='%APP_PATH_EPSXE%']),'%APP_PATH_EPSXE%'),
									'%APP_PATH_FS_UAE%':next(iter([str(x.get('app_path')) for x in self.settings.get('ext_launchers').get('other_ext_cmds') if x.get('app_path_cmd_replace')=='%APP_PATH_FS_UAE%']),'%APP_PATH_FS_UAE%'),
									'%APP_PATH_MAME%':next(iter([str(x.get('app_path')) for x in self.settings.get('ext_launchers').get('other_ext_cmds') if x.get('app_path_cmd_replace')=='%APP_PATH_MAME%']),'%APP_PATH_MAME%'),
									'%APP_PATH_PJ64%':next(iter([str(x.get('app_path')) for x in self.settings.get('ext_launchers').get('other_ext_cmds') if x.get('app_path_cmd_replace')=='%APP_PATH_PJ64%']),'%APP_PATH_PJ64%'),
									'%CFG_PATH%':get_launch_parameter(self.settings.get('ext_launchers').get('ra').get('cfg_path'),'%CFG_PATH%'),
									'%ROM_PATH%':str(launch_files.get('post_process_launch_file')),
									'%ROM_FILENAME%':os.path.split(str(launch_files.get('post_process_launch_file')))[-1],
									'%ROM_BASE_PATH%':os.path.split(str(launch_files.get('post_process_launch_file')))[0]}
					for k,v in command_map.items():
						self.current_command = self.current_command.replace(k,v)
					if '%RETROARCH_CORE_DIR%' in self.current_command: #Check this seperately because polling the RA config takes time, and it's rarely used
						ra_cfg = get_ra_libretro_config(self.settings.get('ext_launchers').get('ra').get('cfg_path'),self.settings.get('ext_launchers').get('ra').get('app_path'))
						self.current_command = self.current_command.replace('%RETROARCH_CORE_DIR%',ra_cfg.get('libretro_directory'))		

				if xbmc.Player().isPlaying() and self.settings.get('ext_launchers').get('stop_media_before_launch'):
					xbmc.Player().stop()
					xbmc.sleep(500) #If sleep is not called, Kodi will crash - does not like playing video and then swiching to a game
					
				if not any([x in self.current_command for x in ['%ADDON_DIR%','%APP_PATH_RA%','%APP_PATH_DEMUL%','%APP_PATH_DOLPHIN%','%APP_PATH_EPSXE%','%APP_PATH_FS_UAE%','%APP_PATH_MAME%','%APP_PATH_PJ64%','%CFG_PATH%','%NETPLAY_COMMAND%','%RETROARCH_CORE_DIR%','%ROM_PATH%','%ROM_RAW%']]):
					if not self.settings.get('ext_launchers').get('close_kodi') and self.settings.get('ext_launchers').get('stop_audio_controller') and self.settings.get('ext_launchers').get('environment') not in ['android','android_ra32','android_aarch64']:
						xbmc.log(msg='IAGL:  Disabling Audio and Controller Input',level=xbmc.LOGDEBUG)
						xbmc.audioSuspend()
						xbmc.enableNavSounds(False)
						xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Settings.SetSettingValue","params":{"setting":"input.enablejoystick","value":false},"id":"1"}')
					
					#No longer needed for kodi v20
					# if self.settings.get('ext_launchers').get('environment') in ['android','android_ra32','android_aarch64'] and self.settings.get('ext_launchers').get('send_stop_command'):
					# 	android_stop_commands = dict(zip(['android','android_ra32','android_aarch64'],['/system/bin/am force-stop com.retroarch','/system/bin/am force-stop com.retroarch','/system/bin/am force-stop com.retroarch.ra32','/system/bin/am force-stop com.retroarch.aarch64']))
					# 	xbmc.log(msg='IAGL:  Sending Android Stop Command: %(android_stop_command)s' % {'android_stop_command': android_stop_commands.get(self.settings.get('ext_launchers').get('environment'))}, level=xbmc.LOGDEBUG)
					# 	stop_process=subprocess.call(android_stop_commands.get(self.settings.get('ext_launchers').get('environment')),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,shell=True)
					# 	xbmc.log(msg='IAGL:  Android returned %(stop_process)s' % {'stop_process': stop_process}, level=xbmc.LOGDEBUG)
					
					if self.settings.get('ext_launchers').get('environment') in ['android','android_ra32','android_aarch64'] and self.settings.get('ext_launchers').get('use_startactivity') and 'am start' not in self.current_command.lower():
						xbmc.executebuiltin('StartAndroidActivity({})'.format(self.current_command),True) #Kodi v20 start android activity, modeled after https://github.com/chrisism/plugin.test.androidcmd/blob/main/addon.py
						self.launch_status['launch_process_success'] = True
						self.launch_status['launch_process_message'] = 'Sent launch command for %(game)s'%{'game':self.game.get('info').get('originaltitle')}
						self.launch_status['launch_process'] = None
						self.launch_status['launch_log'] = None
					else:
						launch_process=subprocess.Popen(self.current_command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,shell=True)
						if not self.settings.get('ext_launchers').get('close_kodi') and capture_launch_log:
							q = Queue()
							t = Thread(target=enqueue_output, args=(launch_process.stdout, q))
							t.daemon = True # thread dies with the program
							t.start()
						
						if not self.settings.get('ext_launchers').get('close_kodi') and capture_launch_log:
							xbmc.sleep(WAIT_FOR_PLAYER_TIME)
							while True:
								try:
									current_line = q.get_nowait()
								except:
									current_line = None
								if current_line and len(current_output)<500: #Read up to first 500 lines of output if available
									current_output.append(current_line.decode('utf-8',errors='ignore').replace('\n','').replace('\r',''))
								else:
									break
						if launch_process.poll() is None or (current_output and any(['starting: intent' in x.lower() for x in current_output]) and not any(['error: activity' in x.lower() for x in current_output])):
							self.launch_status['launch_process_success'] = True
							self.launch_status['launch_process_message'] = 'Sent launch command for %(game)s'%{'game':self.game.get('info').get('originaltitle')}
							self.launch_status['launch_process'] = launch_process
							self.launch_status['launch_log'] = current_output
							xbmc.log(msg='IAGL:  Sent external launch command for game %(game)s'%{'game':self.game.get('info').get('originaltitle')},level=xbmc.LOGINFO)
							xbmc.log(msg='IAGL:  %(command)s'%{'command':self.current_command},level=xbmc.LOGINFO)
							if capture_launch_log and current_output:
								xbmc.log(msg='IAGL:  External launch log for %(game)s'%{'game':self.game.get('info').get('originaltitle')},level=xbmc.LOGDEBUG)
								for co in current_output:
									xbmc.log(msg='IAGL:  %(log)s'%{'log':co},level=xbmc.LOGDEBUG)
						else:
							self.launch_status['launch_process_success'] = False
							self.launch_status['launch_process_message'] = 'Sent launch command for %(game)s but it is not running'%{'game':self.game.get('info').get('originaltitle')}
							self.launch_status['launch_process'] = None
							self.launch_status['launch_log'] = current_output
							xbmc.log(msg='IAGL:  Sent external launch command for game %(game)s but it does not appear to be running'%{'game':self.game.get('info').get('originaltitle')},level=xbmc.LOGERROR)
							xbmc.log(msg='IAGL:  %(command)s'%{'command':self.current_command},level=xbmc.LOGERROR)
							if capture_launch_log and current_output:
								xbmc.log(msg='IAGL:  External launch for %(game)s'%{'game':self.game.get('info').get('originaltitle')},level=xbmc.LOGDEBUG)
								for co in current_output:
									xbmc.log(msg='IAGL:  %(log)s'%{'log':co},level=xbmc.LOGDEBUG)
				else:
					self.launch_status['launch_process_success'] = False
					self.launch_status['launch_process_message'] = 'Launch command malformed for %(game)s'%{'game':self.game.get('info').get('originaltitle')}
					self.launch_status['launch_process'] = None
					self.launch_status['launch_log'] = None
					xbmc.log(msg='IAGL:  The external launch command for game %(game)s is not well formed'%{'game':self.game.get('info').get('originaltitle')},level=xbmc.LOGERROR)
					xbmc.log(msg='IAGL:  %(command)s'%{'command':self.current_command},level=xbmc.LOGERROR)
			else:
				xbmc.log(msg='IAGL:  Badly formed external launch command %(cmd)s'%{'cmd':self.current_command},level=xbmc.LOGERROR)
				return None
			return self.launch_status
