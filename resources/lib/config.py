from pathlib import Path
import xbmcaddon,xbmcplugin,xbmcvfs

class config(object):
	def __init__(self):
		self.addon = dict()
		self.paths = dict()
		self.files = dict()
		self.database = dict()
		self.media = dict()
		self.listitem = dict()
		self.debug = dict()
		self.defaults = dict()
		self.settings = dict()
		self.dialogs = dict()
		self.downloads = dict()
		self.netplay = dict()

		#Handle
		self.addon['addon_name'] = 'plugin.program.iagl'
		self.addon['addon_url'] = 'plugin://{}'.format(self.addon.get('addon_name'))
		self.addon['addon_handle'] = xbmcaddon.Addon(id=self.addon.get('addon_name'))	
		self.addon['version'] = self.addon.get('addon_handle').getAddonInfo('version')
		#Debug
		self.debug['print_query'] = False
		self.debug['factory_debug'] = False
		#Paths
		self.paths['self'] = Path(__file__)
		self.paths['addon'] = Path(xbmcvfs.translatePath(self.addon.get('addon_handle').getAddonInfo('path')))
		self.paths['addon_resources'] = self.paths['addon'].joinpath('resources')
		self.paths['addon_data'] = self.paths['addon_resources'].joinpath('data')
		self.paths['addon_skins'] = self.paths['addon_resources'].joinpath('skins')
		self.paths['addon_skin_media'] = self.paths['addon_skins'].joinpath('Default','media')
		self.paths['userdata'] = Path(xbmcvfs.translatePath(self.addon.get('addon_handle').getAddonInfo('profile')))
		self.paths['default_temp_dl'] = self.paths.get('userdata').joinpath('game_cache')
		try:
			self.paths['os_home'] = Path.home()
		except:
			self.paths['os_home'] = Path('~')
		if self.paths['default_temp_dl'].exists():
			self.files['default_temp_dl_file_listing'] = [x for x in self.paths.get('default_temp_dl').rglob('**/*') if x.is_file()]
			self.paths['default_temp_dl_size'] = sum(x.stat().st_size for x in self.files.get('default_temp_dl_file_listing'))
		else:
			self.files['default_temp_dl_file_listing'] = None
			self.paths['default_temp_dl_size'] = None
		self.paths['assets_url'] = 'special://home/addons/plugin.program.iagl/assets/default/{}'

		#Files
		self.files['addon_data_db'] = self.paths['addon_data'].joinpath('iagl.db')
		self.files['addon_data_db_zipped'] = self.paths['addon_data'].joinpath('iagl.db.zip')
		self.files['addon_data_db_zipped_backup'] = self.paths['addon_data'].joinpath('iagl_backup.db.zip')
		self.files['db'] = self.paths['userdata'].joinpath('iagl.db')
		self.files['ia_cookie'] = self.paths['userdata'].joinpath('ia.cookie')
		self.files['sounds'] = dict()
		self.files['sounds']['wizard_start'] = self.paths['addon_skin_media'].joinpath('wizard_start.wav')
		self.files['sounds']['wizard_done'] = self.paths['addon_skin_media'].joinpath('wizard_done.wav')
		# START_SOUND = MEDIA_SPECIAL_PATH%{'filename':'wizard_start.wav'}
		#Default Values
		self.defaults['home_id'] = 10000
		self.defaults['random_num_result_options'] = list(range(10,60,10))+list(range(100,251,50))+list(range(350,951,100))
		self.defaults['infinite_results_char'] = ['∞']
		self.defaults['default_num_results'] = '10'
		self.defaults['sleep'] = 500
		self.defaults['wait_for_stop_time'] = 500
		self.defaults['wait_for_player_time'] = 5000
		self.defaults['wait_for_process_time'] = 3
		self.defaults['launcher'] = 'retroplayer'
		self.defaults['threads'] = 5
		self.defaults['config_available_systems'] = ['windows','linux','OSX']
		self.defaults['other_emulator_settings'] = ['app_path_dolphin','app_path_mame','app_path_pj64','app_path_expsxe','app_path_demul','app_path_fsuae']
		self.defaults['android_activity_keys'] = ['package','intent','dataType','dataURI','flags','extras','action','category','className']
		self.defaults['retroarch_logging_n_lines'] = 500
		self.defaults['show_extract_progress_size'] = 10*1024*1024
		self.defaults['unzip_skip_bios_files'] = set(['advision.zip','gamecom.zip','crvision.zip','vsmile.zip','gmaster.zip','scv.zip'])
		#Media
		self.media['default_type'] = 'video'
		#Listitems
		self.listitem['art_keys'] = set(['thumb','poster','banner','fanart','clearlogo','fanart1','fanart2']) #https://alwinesch.github.io/group__python__xbmcgui__listitem.html#ga92f9aeb062ff50badcb8792d14a37394
		self.listitem['property_keys'] = set(['SpecialSort','table_filter','total_games','is_1g1r_list','total_1g1r_games','link_query']) #https://alwinesch.github.io/group__python__xbmcgui__listitem.html#ga96f1976952584c91e6d59c310ce86a25
		self.listitem['info_keys'] = set(['size','count','date']) #https://xbmc.github.io/docs.kodi.tv/master/kodi-base/d8/d29/group__python__xbmcgui__listitem.html#ga0b71166869bda87ad744942888fb5f14
		self.listitem['non_string_to_list_keys'] = [] #set(['studio']) #Remove these keys from json serializable list due to database encoding - fixed, now all expected values are json
		self.listitem['sort_methods'] = dict()
		self.listitem['sort_methods']['all'] = [xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,xbmcplugin.SORT_METHOD_DATE,xbmcplugin.SORT_METHOD_SIZE]
		self.listitem['sort_methods']['categories'] = [xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE]
		self.listitem['sort_methods']['playlists'] = [xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE]
		self.listitem['sort_methods']['by_category'] = [xbmcplugin.SORT_METHOD_NONE]
		self.listitem['sort_methods']['by_playlist'] = [xbmcplugin.SORT_METHOD_NONE]
		self.listitem['sort_methods']['search'] = [xbmcplugin.SORT_METHOD_NONE]
		self.listitem['sort_methods']['random'] = [xbmcplugin.SORT_METHOD_NONE]
		self.listitem['sort_methods']['game_list_choice'] = [xbmcplugin.SORT_METHOD_NONE]
		self.listitem['sort_methods']['game_list_choice_by'] = [xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE]
		self.listitem['sort_methods']['games'] = [xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE,xbmcplugin.SORT_METHOD_DATE,xbmcplugin.SORT_METHOD_GENRE,xbmcplugin.SORT_METHOD_STUDIO_IGNORE_THE,xbmcplugin.SORT_METHOD_SIZE,xbmcplugin.SORT_METHOD_PLAYCOUNT]
		self.listitem['sort_methods']['favorites'] = [xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE,xbmcplugin.SORT_METHOD_LABEL,xbmcplugin.SORT_METHOD_TITLE,xbmcplugin.SORT_METHOD_DATE,xbmcplugin.SORT_METHOD_GENRE,xbmcplugin.SORT_METHOD_STUDIO_IGNORE_THE,xbmcplugin.SORT_METHOD_SIZE]
		self.listitem['sort_methods']['history'] = [xbmcplugin.SORT_METHOD_NONE,xbmcplugin.SORT_METHOD_LASTPLAYED,xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE,xbmcplugin.SORT_METHOD_LABEL,xbmcplugin.SORT_METHOD_TITLE,xbmcplugin.SORT_METHOD_DATE,xbmcplugin.SORT_METHOD_GENRE,xbmcplugin.SORT_METHOD_STUDIO_IGNORE_THE,xbmcplugin.SORT_METHOD_SIZE,xbmcplugin.SORT_METHOD_PLAYCOUNT]
		self.listitem['sort_methods']['netplay_lobby'] = [xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE,xbmcplugin.SORT_METHOD_DATE]

		self.listitem['max_label_length'] = 15 #Truncate long search labels
		#Settings
		self.settings['front_page_display'] = dict() 
		self.settings['front_page_display']['options'] = dict(zip(['0','1','2','3','4','5','6','7'],['/browse','/all','/categories','/playlists','/favorites','/history','/search','/random']))
		self.settings['front_page_display']['default'] = '/browse'
		self.settings['game_list_page_display'] = dict() 
		self.settings['game_list_page_display']['options'] = dict(zip(['0','1','2','3','4','5','6','7','8'],['choose_from_list','by_all','by_alpha','by_genre','by_year','by_players','by_studio','by_tag','by_group']))
		self.settings['game_list_page_display']['default'] = 'choose_from_list'
		self.settings['favorites_page_display'] = dict() 
		self.settings['favorites_page_display']['options'] = dict(zip(['0','1','2'],['/favorites','/view_favorites/by_all','/view_favorites/by_group']))
		self.settings['favorites_page_display']['default'] = '/browse'
		self.settings['media_type_game'] = dict() 
		self.settings['media_type_game']['options'] = dict(zip(['0','1','2'],['episodes','movies','games']))
		self.settings['media_type_game']['default'] = 'episodes'
		self.settings['media_type_game']['listitem_type'] = dict(zip(['episodes','tvshows','movies','games'],['video','video','video','game']))
		self.settings['media_types'] = dict()
		self.settings['media_types']['by_genre'] = 'genres'
		self.settings['media_types']['by_studio'] = 'studios'
		self.settings['media_types']['by_tag'] = 'tags'
		self.settings['media_types']['by_code'] = 'tags'
		self.settings['media_types']['by_year'] = 'years'
		self.settings['game_title_setting'] = dict() 
		self.settings['game_title_setting']['options'] = dict(zip(['0','1'],['games_table.name_clean','games_table.originaltitle']))
		self.settings['game_title_setting']['default'] = 'games_table.originaltitle'
		self.settings['games_pagination'] = dict()
		self.settings['games_pagination']['options'] = dict(zip(['0','1','2','3','4','5','6'],[None,10,25,50,100,250,500]))
		self.settings['games_pagination']['default'] = None
		self.settings['filter_to_1g1r'] = dict()
		self.settings['filter_to_1g1r']['options'] = dict(zip(['0','1'],[' and (games_table.is_1g1r = 1 or game_lists_table.is_1g1r_list = 0)','']))
		self.settings['filter_to_1g1r']['default'] = ''
		self.settings['append_game_list_to_search_results'] = dict()
		self.settings['append_game_list_to_search_results']['options'] = dict(zip(['0','1'],['||" ("||games_table.game_list||")"','']))
		self.settings['append_game_list_to_search_results']['default'] = ''
		self.settings['append_game_list_to_playlist_results'] = dict()
		self.settings['append_game_list_to_playlist_results']['options'] = dict(zip(['0','1'],['||" ("||games_table.game_list||")"','']))
		self.settings['append_game_list_to_playlist_results']['default'] = ''
		self.settings['thumbnail_to_game_art'] = dict()
		self.settings['thumbnail_to_game_art']['options'] = dict(zip(['0','1'],['title_paths.url||games_table.art_title','snapshot_paths.url||games_table.art_snapshot']))
		self.settings['thumbnail_to_game_art']['default'] = 'snapshot_paths.url||games_table.art_snapshot'
		self.settings['landscape_to_game_art'] = dict()
		self.settings['landscape_to_game_art']['options'] = dict(zip(['0','1'],['title_paths.url||games_table.art_title','snapshot_paths.url||games_table.art_snapshot']))
		self.settings['landscape_to_game_art']['default'] = 'title_paths.url||games_table.art_title'
		self.settings['game_list_clearlogo_to_art'] = dict()
		self.settings['game_list_clearlogo_to_art']['options'] = dict(zip(['0','1','2'],['clearlogo_paths.url||game_lists_table.clearlogo','console_paths.url||game_lists_table.console','controller_paths.url||game_lists_table.controller']))
		self.settings['game_list_clearlogo_to_art']['default'] = 'clearlogo_paths.url||game_lists_table.clearlogo'
		self.settings['game_list_fanart_to_art'] = dict()
		self.settings['game_list_fanart_to_art']['options'] = dict(zip(['0','1','2'],['fanart_collage_paths.url||game_lists_table.fanart_collage','console_paths.url||game_lists_table.console','fanart_wallpaper_paths.url||game_lists_table.fanart_wallpaper']))
		self.settings['game_list_fanart_to_art']['default'] = 'fanart_collage_paths.url||game_lists_table.fanart_collage'
		self.settings['user_launch_os'] = dict()
		self.settings['user_launch_os']['options'] = dict(zip(['0','1','2','3','4','5','6'],[None,'windows','linux','OSX','android','android_aarch64','android_ra32']))
		self.settings['user_launch_os']['possible_app_locations'] = dict(zip(['windows','linux','OSX','android','android_aarch64','android_ra32'],[[Path('C:').joinpath('Program Files (x86)','Retroarch','retroarch.exe'),Path('C:').joinpath('Program Files','Retroarch','retroarch.exe')],[Path('usr').joinpath('local','bin','retroarch'),self.paths.get('os_home').joinpath('bin','retroarch'),self.paths.get('os_home').joinpath('ra','usr','local','bin','retroarch'),Path('var').joinpath('lib','flatpak','app','org.libretro.RetroArch','current','active','files','bin','retroarch'),Path('home').joinpath('kodi','bin','retroarch'),Path('opt').joinpath('retropie','emulators','retroarch','bin','retroarch'),Path('opt').joinpath('retroarch','bin','retroarch')],[Path('/Applications').joinpath('RetroArch.app','Contents','MacOS','RetroArch')],None,None,None]))
		self.settings['user_launch_os']['possible_config_locations'] = dict(zip(['windows','linux','OSX','android','android_aarch64','android_ra32'],[[Path('C:').joinpath('Program Files (x86)','Retroarch','retroarch.cfg'),Path('C:').joinpath('Program Files','Retroarch','retroarch.cfg'),self.paths.get('os_home').joinpath('AppData','Roaming','RetroArch','retroarch.cfg')],[self.paths.get('os_home').joinpath('.config','retroarch','retroarch.cfg'),self.paths.get('os_home').joinpath('.var','app','org.libretro.RetroArch','config','retroarch','retroarch.cfg'),Path('opt').joinpath('retropie','configs','all','retroarch.cfg')],[self.paths.get('os_home').joinpath('Library','Application Support','RetroArch','config','retroarch.cfg')],[Path('mnt').joinpath('internal_sd','Android','data','com.retroarch','files','retroarch.cfg'),Path('sdcard').joinpath('Android','data','com.retroarch','files','retroarch.cfg'),Path('data').joinpath('data','com.retroarch','retroarch.cfg'),Path('mnt').joinpath('internal_sd','Android','data','com.retroarch.aarch64','files','retroarch.cfg'),Path('sdcard').joinpath('Android','data','com.retroarch.aarch64','files','retroarch.cfg'),Path('data').joinpath('user','0','com.retroarch.aarch64','retroarch.cfg'),Path('data').joinpath('user','0','com.retroarch.aarch64','files','retroarch.cfg'),Path('mnt').joinpath('internal_sd','Android','data','com.retroarch.ra32','files','retroarch.cfg'),Path('sdcard').joinpath('Android','data','com.retroarch.ra32','files','retroarch.cfg'),Path('data').joinpath('data','com.retroarch.ra32','retroarch.cfg'),Path('data').joinpath('data','com.retroarch.ra32','files','retroarch.cfg')],[Path('mnt').joinpath('internal_sd','Android','data','com.retroarch','files','retroarch.cfg'),Path('sdcard').joinpath('Android','data','com.retroarch','files','retroarch.cfg'),Path('data').joinpath('data','com.retroarch','retroarch.cfg'),Path('mnt').joinpath('internal_sd','Android','data','com.retroarch.aarch64','files','retroarch.cfg'),Path('sdcard').joinpath('Android','data','com.retroarch.aarch64','files','retroarch.cfg'),Path('data').joinpath('user','0','com.retroarch.aarch64','retroarch.cfg'),Path('data').joinpath('user','0','com.retroarch.aarch64','files','retroarch.cfg')],[Path('mnt').joinpath('internal_sd','Android','data','com.retroarch','files','retroarch.cfg'),Path('sdcard').joinpath('Android','data','com.retroarch','files','retroarch.cfg'),Path('data').joinpath('data','com.retroarch','retroarch.cfg'),Path('mnt').joinpath('internal_sd','Android','data','com.retroarch.ra32','files','retroarch.cfg'),Path('sdcard').joinpath('Android','data','com.retroarch.ra32','files','retroarch.cfg'),Path('data').joinpath('data','com.retroarch.ra32','retroarch.cfg'),Path('data').joinpath('data','com.retroarch.ra32','files','retroarch.cfg')]]))
		self.settings['user_launch_os']['android_options'] = ['android','android_aarch64','android_ra32']
		self.settings['user_launch_os']['default'] = None
		self.settings['override_ra_directory'] = dict()
		self.settings['override_ra_directory']['options'] = dict(zip(['0','1'],[True,False]))
		self.settings['override_ra_directory']['default'] = False
		self.settings['enable_elec_prepend_command'] = dict()
		self.settings['enable_elec_prepend_command']['options'] = dict(zip(['0','1','2','3','4'],[None,('retroarch','systemd-run '),('all','systemd-run '),('retroarch','flatpak run '),('all','flatpak run ')]))
		self.settings['enable_elec_prepend_command']['default'] = None
		self.settings['alt_temp_dl_enable'] = dict()
		self.settings['alt_temp_dl_enable']['options'] = dict(zip(['0','1'],[True,False]))
		self.settings['alt_temp_dl_enable']['default'] = False
		self.settings['organize_temp_dl'] = dict()
		self.settings['organize_temp_dl']['options'] = dict(zip(['0','1'],[True,False]))
		self.settings['organize_temp_dl']['default'] = True
		self.settings['force_viewtypes'] = dict()
		self.settings['force_viewtypes']['options'] = dict(zip(['0','1'],[True,False]))
		self.settings['force_viewtypes']['default'] = False
		self.settings['page_viewtype_options'] = dict()
		self.settings['page_viewtype_options']['viewtype_settings'] = ['front_page_viewtype','game_lists_viewtype','game_categories_viewtype','games_viewtype','search_random_viewtype']
		self.settings['page_viewtype_options']['options'] = dict(zip(['0','1','2','3','4','5','6','7','8'],[None,'50','51','52','501','502','503','504','505']))
		self.settings['page_viewtype_options']['default'] = None
		self.settings['enable_netplay'] = dict()
		self.settings['enable_netplay']['options'] = dict(zip(['0','1'],[True,False]))
		self.settings['enable_netplay']['default'] = False
		self.settings['netplay_show_lobby'] = dict()
		self.settings['netplay_show_lobby']['options'] = dict(zip(['0','1'],[True,False]))
		self.settings['netplay_show_lobby']['default'] = False
		self.settings['netplay_username_type'] = dict()
		self.settings['netplay_username_type']['options'] = dict(zip(['0','1'],[0,1]))
		self.settings['netplay_username_type']['default'] = 0
		self.settings['netplay_filter_connectable'] = dict()
		self.settings['netplay_filter_connectable']['options'] = dict(zip(['0','1'],[True,False]))
		self.settings['netplay_filter_connectable']['default'] = True
		self.settings['netplay_filter_is_retroarch'] = dict()
		self.settings['netplay_filter_is_retroarch']['options'] = dict(zip(['0','1'],[True,False]))
		self.settings['netplay_filter_is_retroarch']['default'] = True
		self.settings['netplay_filter_is_IAGL'] = dict()
		self.settings['netplay_filter_is_IAGL']['options'] = dict(zip(['0','1'],[True,False]))
		self.settings['netplay_filter_is_IAGL']['default'] = True
		self.settings['netplay_filter_has_password'] = dict()
		self.settings['netplay_filter_has_password']['options'] = dict(zip(['0','1'],[True,False]))
		self.settings['netplay_filter_has_password']['default'] = True
		self.settings['netplay_filter_has_spectate_password'] = dict()
		self.settings['netplay_filter_has_spectate_password']['options'] = dict(zip(['0','1'],[True,False]))
		self.settings['netplay_filter_has_spectate_password']['default'] = True
		self.settings['netplay_filter_host_method'] = dict()
		self.settings['netplay_filter_host_method']['options'] = dict(zip(['0','1'],[True,False]))
		self.settings['netplay_filter_host_method']['default'] = True
		self.settings['netplay_filter_created'] = dict()
		self.settings['netplay_filter_created']['options'] = dict(zip(['0','1','2'],[30,60,None]))
		self.settings['netplay_filter_created']['default'] = None
		self.settings['netplay_launch_type'] = dict()
		self.settings['netplay_launch_type']['options'] = dict(zip(['0','1','2'],[0,1,2]))
		self.settings['netplay_launch_type']['default'] = 0
		self.settings['tou'] = dict()
		self.settings['tou']['options'] = dict(zip(['true','false'],[True,False]))
		self.settings['tou']['default'] = False
		self.settings['wizard_run'] = dict()
		self.settings['wizard_run']['options'] = dict(zip(['true','false'],[True,False]))
		self.settings['wizard_run']['default'] = False
		self.settings['kodi_on_launch'] = dict()
		self.settings['kodi_on_launch']['options'] = dict(zip(['0','1','2','3'],['0','1','2','3']))
		self.settings['kodi_on_launch']['default'] = '1'
		self.settings['no_user_command_present'] = dict()
		self.settings['no_user_command_present']['options'] = dict(zip(['0','1','2'],['0','1','2']))
		self.settings['no_user_command_present']['default'] = '1'
		self.settings['kodi_saa'] = dict()
		self.settings['kodi_saa']['options'] = dict(zip(['0','1'],['activities','commands']))
		self.settings['kodi_saa']['default'] = 'activities'
		self.settings['game_cache_size'] = dict()
		self.settings['game_cache_size']['options'] = dict(zip(['0','1','2','3','4','5','6','7','8','9','10'],[0,1024*1024*25,1024*1024*50,1024*1024*100,1024*1024*200,1024*1024*500,1024*1024*1000,1024*1024*2000,1024*1024*5000,1024*1024*10000,1024*1024*20000]))
		self.settings['game_cache_size']['options_to_string'] = dict(zip([0,1,2,3,4,5,6,7,8,9,10],['Zero (Current Game Only)','25 MB','50 MB','100 MB','200 MB','500 MB','1 GB','2 GB','5 GB','10 GB','20 GB']))
		self.settings['game_cache_size']['default'] = 0
		self.settings['if_game_exists'] = dict()
		self.settings['if_game_exists']['options'] = dict(zip(['0','1','2',],[0,1,2]))
		self.settings['if_game_exists']['default'] = 0
		self.settings['kodi_media_stop'] = dict()
		self.settings['kodi_media_stop']['options'] = dict(zip(['0','1'],[True,False]))
		self.settings['kodi_media_stop']['default'] = True
		self.settings['kodi_suspend'] = dict()
		self.settings['kodi_suspend']['options'] = dict(zip(['0','1'],[True,False]))
		self.settings['kodi_suspend']['default'] = True
		self.settings['kodi_wfr'] = dict()
		self.settings['kodi_wfr']['options'] = dict(zip(['0','1'],[True,False]))
		self.settings['kodi_wfr']['default'] = True
		#Dialogs
		self.dialogs['tou'] = dict()
		self.dialogs['tou']['actions'] = dict()
		self.dialogs['tou']['actions']['do_not_agree'] = [10,13,92]
		self.dialogs['tou']['buttons'] = dict()
		self.dialogs['tou']['buttons']['do_not_agree'] = 3003
		self.dialogs['tou']['buttons']['agree'] = 3001
		self.dialogs['donate'] = dict()
		self.dialogs['donate']['actions'] = dict()
		self.dialogs['donate']['actions']['ok'] = [10,13,92]
		self.dialogs['donate']['buttons'] = dict()
		self.dialogs['donate']['buttons']['ok'] = 3001
		self.dialogs['discord_invite'] = dict()
		self.dialogs['discord_invite']['actions'] = dict()
		self.dialogs['discord_invite']['actions']['ok'] = [10,13,92]
		self.dialogs['discord_invite']['buttons'] = dict()
		self.dialogs['discord_invite']['buttons']['ok'] = 3001

		#Downloads
		self.downloads['archive_org_login_url'] = 'https://archive.org/account/login'
		self.downloads['archive_org_check_acct'] = 'https://archive.org/services/user.php?op=whoami'
		self.downloads['chunk_size'] = 500000 #500 kb chunks
		self.downloads['bad_file_return_size'] = 10000 #Small size returned file may mean archive returned 'Not found' html.  Note chunk_size must be larger than this
		self.downloads['min_file_size'] = 2000000 #If a file is smaller than 2MB, only use 1 thread
		self.downloads['login_timeout'] = (12.1,5.1)
		self.downloads['timeout'] = (12.1,27)

		#Netplay
		self.netplay['lobby_url'] = 'http://lobby.libretro.com/list/'
		self.netplay['lobby_username'] = '{discord_username}-IAGL{game_id}'
		self.netplay['discord_channel'] = 'https://discordapp.com/api/channels/696566635166826526/messages?limit=100'
		self.netplay['channel_hook'] = 'https://discordapp.com/api/webhooks/696566666598809641/{}'
		self.netplay['discord_user'] = 'https://discordapp.com/api/users/{}'
		self.netplay['discord_user_avatar'] = 'https://cdn.discordapp.com/avatars/{discord_user_id}/{discord_user_avatar}.png'

		self.netplay['discord_user_at'] = '<@{discord_user_id}>'
		self.netplay['header_query'] = 'Obg Awx2BGZjZQxkZQHmZmHjBGLm.KbjSRj.bwRpgZk0f0Tg4Ucy6Z_qqvn9xFN'
		self.netplay['header_post'] = 'cDNaRo6zXMlTlwC-hnEnDXEEK6Lh_pxYnywkAyjdkGAIlmkza5QeTdQThHpXnUMXLJNt'
		self.netplay['discord_announce_json'] = '{{"username": "IAGL Netplay Bot", "avatar_url": "https://cdn.discordapp.com/avatars/696566666598809641/9fa63a6bd4a8783e9eaa2be13f2adae4.png", "content": "{discord_at} has started hosting {originaltitle}","embeds": [{{"author": {{"name": "{discord_username}"}}, "title": "{originaltitle}", "description": "Come play {originaltitle} with {discord_username}", "timestamp": "{discord_timestamp}", "fields": [{{"name": "platform", "value": "{platform}", "inline": true}},{{"name": "game_list", "value": "{game_list_id}", "inline": true}},{{"name": "uid", "value": "{uid}", "inline": false}}],"image":{{"url":"{image_url}"}}}}]}}'
		self.netplay['netplay_timeout'] = (12.1,5.1)
		self.netplay['ra_user_max_length'] = 32
		self.netplay['default_port'] = 55435
		self.netplay['default_art'] = 'https://raw.githubusercontent.com/zach-morris/iagl.media/master/icon.png'

		#Database
		self.database['process'] = dict()
		self.database['process']['game'] = dict()
		self.database['process']['game']['from_json'] = ['rom','extra_art','launch_parameters']
		self.database['query'] = dict()
		self.database['query']['browse'] = ('SELECT browse_table.label,browse_table.next_path,browse_table.localization,thumb_paths.url||browse_table.thumb as thumb,poster_paths.url||browse_table.poster as poster,banner_paths.url||browse_table.banner as banner,(SELECT url FROM default_art WHERE art_type="fanart") as fanart,clearlogo_paths.url||browse_table.clearlogo as clearlogo,browse_table.plot,browse_table.SpecialSort\n'
											'FROM browse as browse_table\n'
											'LEFT JOIN paths as thumb_paths\n'
											'ON thumb_paths."path" = browse_table.thumb_path\n'
											'LEFT JOIN paths as poster_paths\n'
											'ON poster_paths."path" = browse_table.poster_path\n'
											'LEFT JOIN paths as banner_paths\n'
											'ON banner_paths."path" = browse_table.banner_path\n'
											'LEFT JOIN paths as clearlogo_paths\n'
											'ON clearlogo_paths."path" = browse_table.clearlogo_path')
		self.database['query']['search'] = ('SELECT search_table.label,search_table.next_path,search_table.localization,thumb_paths.url||search_table.thumb as thumb,poster_paths.url||search_table.poster as poster,banner_paths.url||search_table.banner as banner,(SELECT url FROM default_art WHERE art_type="fanart") as fanart,clearlogo_paths.url||search_table.clearlogo as clearlogo,search_table.plot,search_table.SpecialSort\n'
											'FROM search as search_table\n'
											'LEFT JOIN paths as thumb_paths\n'
											'ON thumb_paths."path" = search_table.thumb_path\n'
											'LEFT JOIN paths as poster_paths\n'
											'ON poster_paths."path" = search_table.poster_path\n'
											'LEFT JOIN paths as banner_paths\n'
											'ON banner_paths."path" = search_table.banner_path\n'
											'LEFT JOIN paths as clearlogo_paths\n'
											'ON clearlogo_paths."path" = search_table.clearlogo_path')
		self.database['query']['random'] = ('SELECT random_table.label,random_table.next_path,random_table.localization,thumb_paths.url||random_table.thumb as thumb,poster_paths.url||random_table.poster as poster,banner_paths.url||random_table.banner as banner,(SELECT url FROM default_art WHERE art_type="fanart") as fanart,clearlogo_paths.url||random_table.clearlogo as clearlogo,random_table.plot,random_table.SpecialSort\n'
											'FROM random as random_table\n'
											'LEFT JOIN paths as thumb_paths\n'
											'ON thumb_paths."path" = random_table.thumb_path\n'
											'LEFT JOIN paths as poster_paths\n'
											'ON poster_paths."path" = random_table.poster_path\n'
											'LEFT JOIN paths as banner_paths\n'
											'ON banner_paths."path" = random_table.banner_path\n'
											'LEFT JOIN paths as clearlogo_paths\n'
											'ON clearlogo_paths."path" = random_table.clearlogo_path')
		self.database['query']['categories'] = ('SELECT categories_table.label||" ("||CAST(categories_table.total_count as TEXT)||")" as label,categories_table.next_path,categories_table.table_filter,thumb_paths.url||categories_table.thumb as thumb,poster_paths.url||categories_table.poster as poster,banner_paths.url||categories_table.banner as banner,(SELECT url FROM default_art WHERE art_type="fanart") as fanart,clearlogo_paths.url||categories_table.clearlogo as clearlogo,categories_table.plot||"[CR]"||CAST(categories_table.total_count as TEXT)||" game lists in this category" as plot\n'
												'FROM categories as categories_table\n'
												'LEFT JOIN paths as thumb_paths\n'
												'ON thumb_paths."path" = categories_table.thumb_path\n'
												'LEFT JOIN paths as poster_paths\n'
												'ON poster_paths."path" = categories_table.poster_path\n'
												'LEFT JOIN paths as banner_paths\n'
												'ON banner_paths."path" = categories_table.banner_path\n'
												'LEFT JOIN paths as clearlogo_paths\n'
												'ON clearlogo_paths."path" = categories_table.clearlogo_path\n'
												'ORDER BY categories_table.label COLLATE NOCASE ASC')
		self.database['query']['playlists'] = ('SELECT groups_table.label||" ("||CAST(groups_table.total_count as TEXT)||")" as label,"/by_playlist/"||groups_table.next_path as next_path,groups_table.table_filter,thumb_paths.url||groups_table.thumb as thumb,poster_paths.url||groups_table.poster as poster,banner_paths.url||groups_table.banner as banner,(SELECT url FROM default_art WHERE art_type="fanart") as fanart,clearlogo_paths.url||groups_table.clearlogo as clearlogo,groups_table.plot,groups_table.plot||"[CR]"||CAST(groups_table.total_count as TEXT)||" games in this playlist" as plot\n'
											'FROM groups as groups_table\n'
											'LEFT JOIN paths as thumb_paths\n'
											'ON thumb_paths."path" = groups_table.thumb_path\n'
											'LEFT JOIN paths as poster_paths\n'
											'ON poster_paths."path" = groups_table.poster_path\n'
											'LEFT JOIN paths as banner_paths\n'
											'ON banner_paths."path" = groups_table.banner_path\n'
											'LEFT JOIN paths as clearlogo_paths\n'
											'ON clearlogo_paths."path" = groups_table.clearlogo_path\n'
											'WHERE groups_table.total_count<5000\n' #Remove huge playlists as they return too many games
											'ORDER BY groups_table.label COLLATE NOCASE ASC')
		self.database['query']['all_game_lists'] = ('SELECT game_lists_table.label,game_lists_table.next_path,game_lists_table.table_filter,thumb_paths.url||game_lists_table.thumb as thumb,poster_paths.url||game_lists_table.poster as poster,banner_paths.url||game_lists_table.banner as banner,{game_list_fanart_to_art} as fanart,{game_list_clearlogo_to_art} as clearlogo,"plugin://plugin.video.youtube/play/?video_id="||game_lists_table.trailer as trailer,game_lists_table.plot,DATE(game_lists_table.date) as premiered,game_lists_table.total_games,game_lists_table.is_1g1r_list,game_lists_table.total_1g1r_games\n'
													'FROM game_list as game_lists_table\n'
													'LEFT JOIN paths as thumb_paths\n'
													'ON thumb_paths."path" = game_lists_table.thumb_path\n'
													'LEFT JOIN paths as poster_paths\n'
													'ON poster_paths."path" = game_lists_table.poster_path\n'
													'LEFT JOIN paths as banner_paths\n'
													'ON banner_paths."path" = game_lists_table.banner_path\n'
													'LEFT JOIN paths as clearlogo_paths\n'
													'ON clearlogo_paths."path" = game_lists_table.clearlogo_path\n'
													'LEFT JOIN paths as console_paths\n'
													'ON console_paths."path" = game_lists_table.console_path\n'
													'LEFT JOIN paths as controller_paths\n'
													'ON controller_paths."path" = game_lists_table.controller_path\n'
													'LEFT JOIN paths as fanart_collage_paths\n'
													'ON fanart_collage_paths."path" = game_lists_table.fanart_collage_path\n'
													'LEFT JOIN paths as fanart_wallpaper_paths\n'
													'ON fanart_wallpaper_paths."path" = game_lists_table.fanart_wallpaper_path\n'
													'WHERE game_lists_table.user_global_visibility is NULL and game_lists_table.label IN (SELECT DISTINCT(games_table.game_list) as available_lists FROM games AS games_table)'
													'ORDER BY game_lists_table.label COLLATE NOCASE ASC') #Checked
		self.database['query']['game_lists_by_category'] = ('SELECT game_lists_table.label,game_lists_table.next_path,game_lists_table.table_filter,thumb_paths.url||game_lists_table.thumb as thumb,poster_paths.url||game_lists_table.poster as poster,banner_paths.url||game_lists_table.banner as banner,{game_list_fanart_to_art} as fanart,{game_list_clearlogo_to_art} as clearlogo,"plugin://plugin.video.youtube/play/?video_id="||game_lists_table.trailer as trailer,game_lists_table.plot,DATE(game_lists_table.date) as date,DATE(game_lists_table.date) as premiered,game_lists_table.total_games,game_lists_table.is_1g1r_list,game_lists_table.total_1g1r_games\n'
													'FROM game_list as game_lists_table\n'
													'LEFT JOIN paths as thumb_paths\n'
													'ON thumb_paths."path" = game_lists_table.thumb_path\n'
													'LEFT JOIN paths as poster_paths\n'
													'ON poster_paths."path" = game_lists_table.poster_path\n'
													'LEFT JOIN paths as banner_paths\n'
													'ON banner_paths."path" = game_lists_table.banner_path\n'
													'LEFT JOIN paths as clearlogo_paths\n'
													'ON clearlogo_paths."path" = game_lists_table.clearlogo_path\n'
													'LEFT JOIN paths as console_paths\n'
													'ON console_paths."path" = game_lists_table.console_path\n'
													'LEFT JOIN paths as controller_paths\n'
													'ON controller_paths."path" = game_lists_table.controller_path\n'
													'LEFT JOIN paths as fanart_collage_paths\n'
													'ON fanart_collage_paths."path" = game_lists_table.fanart_collage_path\n'
													'LEFT JOIN paths as fanart_wallpaper_paths\n'
													'ON fanart_wallpaper_paths."path" = game_lists_table.fanart_wallpaper_path\n'
													'WHERE game_lists_table.user_global_visibility is NULL and game_lists_table.label IN (SELECT DISTINCT(games_table.game_list) as available_lists FROM games AS games_table) and game_lists_table.categories LIKE "%{category_id}%"'
													'ORDER BY game_lists_table.label COLLATE NOCASE ASC') #Checked
		self.database['query']['game_lists_by_playlist_no_page'] = ('SELECT "play_game/"||games_table.uid as next_path,games_table.originaltitle AS originaltitle,{game_title_setting} as label,{game_title_setting} as title,games_table.name_search as sorttitle,games_table.system as "set",games_table.genres AS genre,games_table.studio,DATE(games_table.date) AS date,DATE(games_table.date) as premiered,games_table.year,games_table.ESRB as mpaa,games_table.rating,games_table.tags as tag,games_table.size,games_table.plot,games_table.regions AS country,games_table.lastplayed,games_table.playcount,"plugin://plugin.video.youtube/play/?video_id="||games_table.trailer as trailer,banner_paths.url||games_table.art_banner as banner,box_paths.url||games_table.art_box as poster,clearlogo_paths.url||games_table.art_logo as clearlogo,title_paths.url||games_table.art_title as landscape,snapshot_paths.url||games_table.art_snapshot as thumb,fanart_paths.url||games_table.art_fanart as fanart\n'
																	'FROM games as games_table\n'
																	'LEFT JOIN game_list as game_lists_table\n'
																	'ON game_lists_table.label = games_table.game_list\n'
																	'LEFT JOIN paths as banner_paths\n'
																	'ON banner_paths."path" = games_table.art_banner_path\n'
																	'LEFT JOIN paths as box_paths\n'
																	'ON box_paths."path" = games_table.art_box_path\n'
																	'LEFT JOIN paths as clearlogo_paths\n'
																	'ON clearlogo_paths."path" = games_table.art_logo_path\n'
																	'LEFT JOIN paths as title_paths\n'
																	'ON title_paths."path" = games_table.art_title_path\n'
																	'LEFT JOIN paths as snapshot_paths\n'
																	'ON snapshot_paths."path" = games_table.art_snapshot_path\n'
																	'LEFT JOIN paths as fanart_paths\n'
																	'ON fanart_paths."path" = games_table.art_fanart_path\n'
																	'WHERE games_table.groups  LIKE "%""{playlist_id}""%"\n'
																	'AND game_lists_table.user_global_visibility is NULL')
		self.database['query']['game_lists_by_playlist_page'] = ('SELECT "play_game/"||games_table.uid as next_path,games_table.originaltitle AS originaltitle,{game_title_setting} as label,{game_title_setting} as title,games_table.name_search as sorttitle,games_table.system as "set",games_table.genres AS genre,games_table.studio,DATE(games_table.date) AS date,DATE(games_table.date) as premiered,games_table.year,games_table.ESRB as mpaa,games_table.rating,games_table.tags as tag,games_table.size,games_table.plot,games_table.regions AS country,games_table.lastplayed,games_table.playcount,"plugin://plugin.video.youtube/play/?video_id="||games_table.trailer as trailer,banner_paths.url||games_table.art_banner as banner,box_paths.url||games_table.art_box as poster,clearlogo_paths.url||games_table.art_logo as clearlogo,title_paths.url||games_table.art_title as landscape,snapshot_paths.url||games_table.art_snapshot as thumb,fanart_paths.url||games_table.art_fanart as fanart\n'
																'FROM games as games_table\n'
																'LEFT JOIN game_list as game_lists_table\n'
																'ON game_lists_table.label = games_table.game_list\n'
																'LEFT JOIN paths as banner_paths\n'
																'ON banner_paths."path" = games_table.art_banner_path\n'
																'LEFT JOIN paths as box_paths\n'
																'ON box_paths."path" = games_table.art_box_path\n'
																'LEFT JOIN paths as clearlogo_paths\n'
																'ON clearlogo_paths."path" = games_table.art_logo_path\n'
																'LEFT JOIN paths as title_paths\n'
																'ON title_paths."path" = games_table.art_title_path\n'
																'LEFT JOIN paths as snapshot_paths\n'
																'ON snapshot_paths."path" = games_table.art_snapshot_path\n'
																'LEFT JOIN paths as fanart_paths\n'
																'ON fanart_paths."path" = games_table.art_fanart_path\n'
																'WHERE games_table.groups  LIKE "%""{playlist_id}""%"\n'
																'AND game_lists_table.user_global_visibility is NULL\n'
																'ORDER BY games_table.originaltitle COLLATE NOCASE ASC\n'
																'LIMIT {items_per_page} OFFSET {starting_number}')
		self.database['query']['choose_from_list'] = ('SELECT choose_table.label,choose_table.next_path,choose_table.localization as localization,choose_table.choice_table as choice_table,thumb_paths.url||choose_table.thumb as thumb,poster_paths.url||choose_table.poster as poster,banner_paths.url||choose_table.banner as banner,(SELECT url FROM default_art WHERE art_type="fanart") as fanart,clearlogo_paths.url||choose_table.clearlogo as clearlogo,choose_table.plot\n'
														'FROM choose as choose_table\n'
														'LEFT JOIN paths as thumb_paths\n'
														'ON thumb_paths."path" = choose_table.thumb_path\n'
														'LEFT JOIN paths as poster_paths\n'
														'ON poster_paths."path" = choose_table.poster_path\n'
														'LEFT JOIN paths as banner_paths\n'
														'ON banner_paths."path" = choose_table.banner_path\n'
														'LEFT JOIN paths as clearlogo_paths\n'
														'ON clearlogo_paths."path" = choose_table.clearlogo_path')
		self.database['query']['by_alpha'] = ('SELECT choose_table.label,choose_table.next_path,choose_table.table_filter,thumb_paths.url||choose_table.thumb as thumb,poster_paths.url||choose_table.poster as poster,banner_paths.url||choose_table.banner as banner,(SELECT url FROM default_art WHERE art_type="fanart") as fanart,clearlogo_paths.url||choose_table.clearlogo as clearlogo,choose_table.plot\n'
												'FROM alphabetical as choose_table\n'
												'LEFT JOIN paths as thumb_paths\n'
												'ON thumb_paths."path" = choose_table.thumb_path\n'
												'LEFT JOIN paths as poster_paths\n'
												'ON poster_paths."path" = choose_table.poster_path\n'
												'LEFT JOIN paths as banner_paths\n'
												'ON banner_paths."path" = choose_table.banner_path\n'
												'LEFT JOIN paths as clearlogo_paths\n'
												'ON clearlogo_paths."path" = choose_table.clearlogo_path\n'
												'WHERE choose_table.matching_lists LIKE "%""{game_list_id}""%"')
		self.database['query']['by_genre'] = ('SELECT choose_table.label,choose_table.next_path,choose_table.table_filter,thumb_paths.url||choose_table.thumb as thumb,poster_paths.url||choose_table.poster as poster,banner_paths.url||choose_table.banner as banner,(SELECT url FROM default_art WHERE art_type="fanart") as fanart,clearlogo_paths.url||choose_table.clearlogo as clearlogo,choose_table.plot\n'
												'FROM genre as choose_table\n'
												'LEFT JOIN paths as thumb_paths\n'
												'ON thumb_paths."path" = choose_table.thumb_path\n'
												'LEFT JOIN paths as poster_paths\n'
												'ON poster_paths."path" = choose_table.poster_path\n'
												'LEFT JOIN paths as banner_paths\n'
												'ON banner_paths."path" = choose_table.banner_path\n'
												'LEFT JOIN paths as clearlogo_paths\n'
												'ON clearlogo_paths."path" = choose_table.clearlogo_path\n'
												'WHERE choose_table.matching_lists LIKE "%""{game_list_id}""%"')
		self.database['query']['by_year'] = ('SELECT choose_table.label,choose_table.next_path,choose_table.table_filter,thumb_paths.url||choose_table.thumb as thumb,poster_paths.url||choose_table.poster as poster,banner_paths.url||choose_table.banner as banner,(SELECT url FROM default_art WHERE art_type="fanart") as fanart,clearlogo_paths.url||choose_table.clearlogo as clearlogo,choose_table.plot\n'
												'FROM year as choose_table\n'
												'LEFT JOIN paths as thumb_paths\n'
												'ON thumb_paths."path" = choose_table.thumb_path\n'
												'LEFT JOIN paths as poster_paths\n'
												'ON poster_paths."path" = choose_table.poster_path\n'
												'LEFT JOIN paths as banner_paths\n'
												'ON banner_paths."path" = choose_table.banner_path\n'
												'LEFT JOIN paths as clearlogo_paths\n'
												'ON clearlogo_paths."path" = choose_table.clearlogo_path\n'
												'WHERE choose_table.matching_lists LIKE "%""{game_list_id}""%"')
		self.database['query']['by_players'] = ('SELECT choose_table.label,choose_table.next_path,choose_table.table_filter,thumb_paths.url||choose_table.thumb as thumb,poster_paths.url||choose_table.poster as poster,banner_paths.url||choose_table.banner as banner,(SELECT url FROM default_art WHERE art_type="fanart") as fanart,clearlogo_paths.url||choose_table.clearlogo as clearlogo,choose_table.plot\n'
												'FROM nplayers as choose_table\n'
												'LEFT JOIN paths as thumb_paths\n'
												'ON thumb_paths."path" = choose_table.thumb_path\n'
												'LEFT JOIN paths as poster_paths\n'
												'ON poster_paths."path" = choose_table.poster_path\n'
												'LEFT JOIN paths as banner_paths\n'
												'ON banner_paths."path" = choose_table.banner_path\n'
												'LEFT JOIN paths as clearlogo_paths\n'
												'ON clearlogo_paths."path" = choose_table.clearlogo_path\n'
												'WHERE choose_table.matching_lists LIKE "%""{game_list_id}""%"')
		self.database['query']['by_studio'] = ('SELECT choose_table.label,choose_table.next_path,choose_table.table_filter,thumb_paths.url||choose_table.thumb as thumb,poster_paths.url||choose_table.poster as poster,banner_paths.url||choose_table.banner as banner,(SELECT url FROM default_art WHERE art_type="fanart") as fanart,clearlogo_paths.url||choose_table.clearlogo as clearlogo,choose_table.plot\n'
												'FROM studio as choose_table\n'
												'LEFT JOIN paths as thumb_paths\n'
												'ON thumb_paths."path" = choose_table.thumb_path\n'
												'LEFT JOIN paths as poster_paths\n'
												'ON poster_paths."path" = choose_table.poster_path\n'
												'LEFT JOIN paths as banner_paths\n'
												'ON banner_paths."path" = choose_table.banner_path\n'
												'LEFT JOIN paths as clearlogo_paths\n'
												'ON clearlogo_paths."path" = choose_table.clearlogo_path\n'
												'WHERE choose_table.matching_lists LIKE "%""{game_list_id}""%"')
		self.database['query']['by_tag'] = ('SELECT choose_table.label,choose_table.next_path,choose_table.table_filter,thumb_paths.url||choose_table.thumb as thumb,poster_paths.url||choose_table.poster as poster,banner_paths.url||choose_table.banner as banner,(SELECT url FROM default_art WHERE art_type="fanart") as fanart,clearlogo_paths.url||choose_table.clearlogo as clearlogo,choose_table.plot\n'
												'FROM tag as choose_table\n'
												'LEFT JOIN paths as thumb_paths\n'
												'ON thumb_paths."path" = choose_table.thumb_path\n'
												'LEFT JOIN paths as poster_paths\n'
												'ON poster_paths."path" = choose_table.poster_path\n'
												'LEFT JOIN paths as banner_paths\n'
												'ON banner_paths."path" = choose_table.banner_path\n'
												'LEFT JOIN paths as clearlogo_paths\n'
												'ON clearlogo_paths."path" = choose_table.clearlogo_path\n'
												'WHERE choose_table.matching_lists LIKE "%""{game_list_id}""%"')
		self.database['query']['by_group'] = ('SELECT choose_table.label,choose_table.next_path,choose_table.table_filter,thumb_paths.url||choose_table.thumb as thumb,poster_paths.url||choose_table.poster as poster,banner_paths.url||choose_table.banner as banner,(SELECT url FROM default_art WHERE art_type="fanart") as fanart,clearlogo_paths.url||choose_table.clearlogo as clearlogo,choose_table.plot\n'
												'FROM groups as choose_table\n'
												'LEFT JOIN paths as thumb_paths\n'
												'ON thumb_paths."path" = choose_table.thumb_path\n'
												'LEFT JOIN paths as poster_paths\n'
												'ON poster_paths."path" = choose_table.poster_path\n'
												'LEFT JOIN paths as banner_paths\n'
												'ON banner_paths."path" = choose_table.banner_path\n'
												'LEFT JOIN paths as clearlogo_paths\n'
												'ON clearlogo_paths."path" = choose_table.clearlogo_path\n'
												'WHERE choose_table.matching_lists LIKE "%""{game_list_id}""%"') 
		self.database['query']['by_all_no_page'] = ('SELECT "play_game/"||games_table.uid as next_path,games_table.originaltitle AS originaltitle,{game_title_setting} as label,{game_title_setting} as title,games_table.name_search as sorttitle,games_table.system as "set",games_table.system as "tvshowtitle",games_table.genres AS genre,games_table.studio,DATE(games_table.date) AS date,DATE(games_table.date) as premiered,games_table.year,games_table.ESRB as mpaa,games_table.rating,games_table.tags as tag,games_table.size,games_table.plot,games_table.regions AS country,games_table.lastplayed,games_table.playcount,"plugin://plugin.video.youtube/play/?video_id="||games_table.trailer as trailer,banner_paths.url||games_table.art_banner as banner,box_paths.url||games_table.art_box as poster,clearlogo_paths.url||games_table.art_logo as clearlogo,{landscape_to_game_art} as landscape,{thumbnail_to_game_art} as thumb,fanart_paths.url||games_table.art_fanart as fanart\n'
													'FROM games as games_table\n'
													'LEFT JOIN game_list as game_lists_table\n'
													'ON game_lists_table.label = games_table.game_list\n'
													'LEFT JOIN paths as banner_paths\n'
													'ON banner_paths."path" = games_table.art_banner_path\n'
													'LEFT JOIN paths as box_paths\n'
													'ON box_paths."path" = games_table.art_box_path\n'
													'LEFT JOIN paths as clearlogo_paths\n'
													'ON clearlogo_paths."path" = games_table.art_logo_path\n'
													'LEFT JOIN paths as title_paths\n'
													'ON title_paths."path" = games_table.art_title_path\n'
													'LEFT JOIN paths as snapshot_paths\n'
													'ON snapshot_paths."path" = games_table.art_snapshot_path\n'
													'LEFT JOIN paths as fanart_paths\n'
													'ON fanart_paths."path" = games_table.art_fanart_path\n'
													'WHERE games_table.game_list = "{game_list_id}"{filter_to_1g1r}\n'
													'ORDER BY games_table.originaltitle COLLATE NOCASE ASC')
		self.database['query']['by_all_page'] = ('SELECT "play_game/"||games_table.uid as next_path,games_table.originaltitle AS originaltitle,{game_title_setting} as label,{game_title_setting} as title,games_table.name_search as sorttitle,games_table.system as "set",games_table.system as "tvshowtitle",games_table.genres AS genre,games_table.studio,DATE(games_table.date) AS date,DATE(games_table.date) as premiered,games_table.year,games_table.ESRB as mpaa,games_table.rating,games_table.tags as tag,games_table.size,games_table.plot,games_table.regions AS country,games_table.lastplayed,games_table.playcount,"plugin://plugin.video.youtube/play/?video_id="||games_table.trailer as trailer,banner_paths.url||games_table.art_banner as banner,box_paths.url||games_table.art_box as poster,clearlogo_paths.url||games_table.art_logo as clearlogo,title_paths.url||games_table.art_title as landscape,snapshot_paths.url||games_table.art_snapshot as thumb,fanart_paths.url||games_table.art_fanart as fanart\n'
													'FROM games as games_table\n'
													'LEFT JOIN game_list as game_lists_table\n'
													'ON game_lists_table.label = games_table.game_list\n'
													'LEFT JOIN paths as banner_paths\n'
													'ON banner_paths."path" = games_table.art_banner_path\n'
													'LEFT JOIN paths as box_paths\n'
													'ON box_paths."path" = games_table.art_box_path\n'
													'LEFT JOIN paths as clearlogo_paths\n'
													'ON clearlogo_paths."path" = games_table.art_logo_path\n'
													'LEFT JOIN paths as title_paths\n'
													'ON title_paths."path" = games_table.art_title_path\n'
													'LEFT JOIN paths as snapshot_paths\n'
													'ON snapshot_paths."path" = games_table.art_snapshot_path\n'
													'LEFT JOIN paths as fanart_paths\n'
													'ON fanart_paths."path" = games_table.art_fanart_path\n'
													'WHERE games_table.game_list = "{game_list_id}"{filter_to_1g1r}\n'
													'ORDER BY games_table.originaltitle COLLATE NOCASE ASC\n'
													'LIMIT {items_per_page} OFFSET {starting_number}')
		self.database['query']['get_game_table_filter'] = ('SELECT game_lists_table.table_filter\n'
															'FROM game_list as game_lists_table\n'
															'WHERE game_lists_table.label = "{}"')
		self.database['query']['get_game_table_filter_from_choice'] = ('SELECT "by_alpha" as choice_id,a.table_filter\n'
																		'from alphabetical a\n'
																		'WHERE choice_id = "{choose_id}" and a.label = "{choose_value}"\n'
																		'UNION\n'
																		'SELECT "by_genre" as choice_id,b.table_filter\n'
																		'from genre b\n'
																		'WHERE choice_id = "{choose_id}" and b.label = "{choose_value}"\n'
																		'UNION\n'
																		'SELECT "by_year" as choice_id,c.table_filter\n'
																		'from year c\n'
																		'WHERE choice_id = "{choose_id}" and c.label = "{choose_value}"\n'
																		'UNION\n'
																		'SELECT "by_players" as choice_id,d.table_filter\n'
																		'from nplayers d\n'
																		'WHERE choice_id = "{choose_id}" and d.label = "{choose_value}"\n'
																		'UNION\n'
																		'SELECT "by_studio" as choice_id,e.table_filter\n'
																		'from studio e\n'
																		'WHERE choice_id = "{choose_id}" and e.label = "{choose_value}"\n'
																		'UNION\n'
																		'SELECT "by_tag" as choice_id,f.table_filter\n'
																		'from tag f\n'
																		'WHERE choice_id = "{choose_id}" and f.label = "{choose_value}"\n'
																		'UNION\n'
																		'SELECT "by_group" as choice_id,g.table_filter\n'
																		'from groups g\n'
																		'WHERE choice_id = "{choose_id}" and g.label = "{choose_value}"')
		self.database['query']['get_games_from_choice_no_page'] = ('SELECT "play_game/"||games_table.uid as next_path,games_table.originaltitle AS originaltitle,{game_title_setting} as label,{game_title_setting} as title,games_table.name_search as sorttitle,games_table.system as "set",games_table.genres AS genre,games_table.studio,DATE(games_table.date) AS date,DATE(games_table.date) as premiered,games_table.year,games_table.ESRB as mpaa,games_table.rating,games_table.tags as tag,games_table.size,games_table.plot,games_table.regions AS country,games_table.lastplayed,games_table.playcount,"plugin://plugin.video.youtube/play/?video_id="||games_table.trailer as trailer,banner_paths.url||games_table.art_banner as banner,box_paths.url||games_table.art_box as poster,clearlogo_paths.url||games_table.art_logo as clearlogo,title_paths.url||games_table.art_title as landscape,snapshot_paths.url||games_table.art_snapshot as thumb,fanart_paths.url||games_table.art_fanart as fanart\n'
																	'FROM games as games_table\n'
																	'LEFT JOIN game_list as game_lists_table\n'
																	'ON game_lists_table.label = games_table.game_list\n'
																	'LEFT JOIN paths as banner_paths\n'
																	'ON banner_paths."path" = games_table.art_banner_path\n'
																	'LEFT JOIN paths as box_paths\n'
																	'ON box_paths."path" = games_table.art_box_path\n'
																	'LEFT JOIN paths as clearlogo_paths\n'
																	'ON clearlogo_paths."path" = games_table.art_logo_path\n'
																	'LEFT JOIN paths as title_paths\n'
																	'ON title_paths."path" = games_table.art_title_path\n'
																	'LEFT JOIN paths as snapshot_paths\n'
																	'ON snapshot_paths."path" = games_table.art_snapshot_path\n'
																	'LEFT JOIN paths as fanart_paths\n'
																	'ON fanart_paths."path" = games_table.art_fanart_path\n'
																	'WHERE games_table.game_list = "{game_list_id}" AND {choice_query}{filter_to_1g1r}\n'
																	'ORDER BY games_table.originaltitle COLLATE NOCASE ASC')
		self.database['query']['get_games_from_choice_page'] = ('SELECT "play_game/"||games_table.uid as next_path,games_table.originaltitle AS originaltitle,{game_title_setting} as label,{game_title_setting} as title,games_table.name_search as sorttitle,games_table.system as "set",games_table.genres AS genre,games_table.studio,DATE(games_table.date) AS date,DATE(games_table.date) as premiered,games_table.year,games_table.ESRB as mpaa,games_table.rating,games_table.tags as tag,games_table.size,games_table.plot,games_table.regions AS country,games_table.lastplayed,games_table.playcount,"plugin://plugin.video.youtube/play/?video_id="||games_table.trailer as trailer,banner_paths.url||games_table.art_banner as banner,box_paths.url||games_table.art_box as poster,clearlogo_paths.url||games_table.art_logo as clearlogo,title_paths.url||games_table.art_title as landscape,snapshot_paths.url||games_table.art_snapshot as thumb,fanart_paths.url||games_table.art_fanart as fanart\n'
																'FROM games as games_table\n'
																'LEFT JOIN game_list as game_lists_table\n'
																'ON game_lists_table.label = games_table.game_list\n'
																'LEFT JOIN paths as banner_paths\n'
																'ON banner_paths."path" = games_table.art_banner_path\n'
																'LEFT JOIN paths as box_paths\n'
																'ON box_paths."path" = games_table.art_box_path\n'
																'LEFT JOIN paths as clearlogo_paths\n'
																'ON clearlogo_paths."path" = games_table.art_logo_path\n'
																'LEFT JOIN paths as title_paths\n'
																'ON title_paths."path" = games_table.art_title_path\n'
																'LEFT JOIN paths as snapshot_paths\n'
																'ON snapshot_paths."path" = games_table.art_snapshot_path\n'
																'LEFT JOIN paths as fanart_paths\n'
																'ON fanart_paths."path" = games_table.art_fanart_path\n'
																'WHERE games_table.game_list = "{game_list_id}" AND {choice_query}{filter_to_1g1r}\n'
																'ORDER BY games_table.originaltitle COLLATE NOCASE ASC\n'
																'LIMIT {items_per_page} OFFSET {starting_number}')
		self.database['query']['game_launch_info_from_id'] = ('SELECT games_table.uid,games_table.launch_parameters,games_table.user_game_launcher,games_table.user_game_launch_addon,games_table.user_game_external_launch_command,games_table.user_game_post_download_process,game_list_table.default_global_post_download_process,game_list_table.default_global_launcher,game_list_table.user_post_download_process,game_list_table.user_global_launcher,game_list_table.user_global_launch_addon,game_list_table.user_global_external_launch_command,game_list_table.user_global_uses_applaunch,game_list_table.user_global_uses_apppause,game_list_table.user_global_download_path,game_list_table.default_global_launch_addon,game_list_table.default_global_external_launch_command\n'
															'FROM games as games_table\n'
															'LEFT JOIN game_list as game_list_table on games_table.game_list = game_list_table.label\n'
															'WHERE games_table.uid = "{game_id}"')
		self.database['query']['get_game_from_id'] = ('SELECT games_table.uid,games_table.game_list as game_list_id,games_table.originaltitle AS originaltitle,{game_title_setting} as label,{game_title_setting} as title,games_table.name_search as sorttitle,games_table.system as platform,games_table.genres AS genres,games_table.studio as publisher,games_table.year,games_table.size,games_table.plot as overview,banner_paths.url||games_table.art_banner as banner,box_paths.url||games_table.art_box as poster,clearlogo_paths.url||games_table.art_logo as clearlogo,title_paths.url||games_table.art_title as landscape,snapshot_paths.url||games_table.art_snapshot as thumb,fanart_paths.url||games_table.art_fanart as fanart,games_table.launch_parameters,games_table.user_game_launch_addon,games_table.user_game_external_launch_command,games_table.user_game_post_download_process,game_list_table.default_global_post_download_process,game_list_table.default_global_launcher,game_list_table.user_post_download_process,game_list_table.user_global_launcher,game_list_table.user_global_launch_addon,game_list_table.user_global_external_launch_command,game_list_table.user_global_uses_applaunch,game_list_table.user_global_uses_apppause,game_list_table.user_global_download_path,game_list_table.default_global_launch_addon,game_list_table.default_global_external_launch_command,games_table.rom\n'
														'FROM games as games_table\n'
														'LEFT JOIN game_list as game_list_table on games_table.game_list = game_list_table.label\n'
														'LEFT JOIN paths as banner_paths\n'
														'ON banner_paths."path" = games_table.art_banner_path\n'
														'LEFT JOIN paths as box_paths\n'
														'ON box_paths."path" = games_table.art_box_path\n'
														'LEFT JOIN paths as clearlogo_paths\n'
														'ON clearlogo_paths."path" = games_table.art_logo_path\n'
														'LEFT JOIN paths as title_paths\n'
														'ON title_paths."path" = games_table.art_title_path\n'
														'LEFT JOIN paths as snapshot_paths\n'
														'ON snapshot_paths."path" = games_table.art_snapshot_path\n'
														'LEFT JOIN paths as fanart_paths\n'
														'ON fanart_paths."path" = games_table.art_fanart_path\n'
														'WHERE games_table.uid = "{game_id}"')
		self.database['query']['get_game_from_id_for_netplay'] = ('SELECT games_table.uid,games_table.game_list as game_list_id,games_table.originaltitle AS originaltitle,games_table.system as platform,banner_paths.url||games_table.art_banner as art_banner,box_paths.url||games_table.art_box as art_box,clearlogo_paths.url||games_table.art_logo as art_logo,title_paths.url||games_table.art_title as art_title,snapshot_paths.url||games_table.art_snapshot as art_snapshot,fanart_paths.url||games_table.art_fanart as art_fanart,game_list_art_paths.url||game_list_table.poster as art_game_list\n'
														'FROM games as games_table\n'
														'LEFT JOIN game_list as game_list_table on games_table.game_list = game_list_table.label\n'
														'LEFT JOIN paths as banner_paths\n'
														'ON banner_paths."path" = games_table.art_banner_path\n'
														'LEFT JOIN paths as box_paths\n'
														'ON box_paths."path" = games_table.art_box_path\n'
														'LEFT JOIN paths as clearlogo_paths\n'
														'ON clearlogo_paths."path" = games_table.art_logo_path\n'
														'LEFT JOIN paths as title_paths\n'
														'ON title_paths."path" = games_table.art_title_path\n'
														'LEFT JOIN paths as snapshot_paths\n'
														'ON snapshot_paths."path" = games_table.art_snapshot_path\n'
														'LEFT JOIN paths as fanart_paths\n'
														'ON fanart_paths."path" = games_table.art_fanart_path\n'
														'LEFT JOIN paths as game_list_art_paths\n'
														'ON game_list_art_paths."path" = game_list_table.poster_path\n'
														'WHERE games_table.uid = "{game_id}"')
		self.database['query']['get_game_from_originaltitle_exact'] = ('SELECT "/play_game_external_netplay/"||games_table.uid as next_path,games_table.uid,games_table.game_list as game_list_id,games_table.originaltitle AS originaltitle,{game_title_setting} as label,games_table.game_list as label2,{game_title_setting} as title,games_table.name_search as sorttitle,games_table.system as platform,games_table.genres AS genres,games_table.studio as publisher,games_table.year,games_table.size,games_table.plot as overview,banner_paths.url||games_table.art_banner as banner,box_paths.url||games_table.art_box as poster,clearlogo_paths.url||games_table.art_logo as clearlogo,title_paths.url||games_table.art_title as landscape,snapshot_paths.url||games_table.art_snapshot as thumb,fanart_paths.url||games_table.art_fanart as fanart,games_table.launch_parameters,games_table.user_game_launch_addon,games_table.user_game_external_launch_command,games_table.user_game_post_download_process,game_list_table.default_global_post_download_process,game_list_table.default_global_launcher,game_list_table.user_post_download_process,game_list_table.user_global_launcher,game_list_table.user_global_launch_addon,game_list_table.user_global_external_launch_command,game_list_table.user_global_uses_applaunch,game_list_table.user_global_uses_apppause,game_list_table.user_global_download_path,game_list_table.default_global_launch_addon,game_list_table.default_global_external_launch_command,games_table.rom\n'
														'FROM games as games_table\n'
														'LEFT JOIN game_list as game_list_table on games_table.game_list = game_list_table.label\n'
														'LEFT JOIN paths as banner_paths\n'
														'ON banner_paths."path" = games_table.art_banner_path\n'
														'LEFT JOIN paths as box_paths\n'
														'ON box_paths."path" = games_table.art_box_path\n'
														'LEFT JOIN paths as clearlogo_paths\n'
														'ON clearlogo_paths."path" = games_table.art_logo_path\n'
														'LEFT JOIN paths as title_paths\n'
														'ON title_paths."path" = games_table.art_title_path\n'
														'LEFT JOIN paths as snapshot_paths\n'
														'ON snapshot_paths."path" = games_table.art_snapshot_path\n'
														'LEFT JOIN paths as fanart_paths\n'
														'ON fanart_paths."path" = games_table.art_fanart_path\n'
														'WHERE games_table.originaltitle = "{game_name}"')
		self.database['query']['netplay_by_uid'] = ('SELECT "/play_game_external_netplay/"||games_table.uid as next_path,games_table.uid,games_table.game_list as game_list_id,games_table.originaltitle AS originaltitle,{game_title_setting} as label,games_table.game_list as label2,{game_title_setting} as title,games_table.name_search as sorttitle,games_table.system as platform,games_table.genres AS genres,games_table.studio as publisher,games_table.year,games_table.size,games_table.plot as overview,banner_paths.url||games_table.art_banner as banner,box_paths.url||games_table.art_box as poster,clearlogo_paths.url||games_table.art_logo as clearlogo,title_paths.url||games_table.art_title as landscape,snapshot_paths.url||games_table.art_snapshot as thumb,fanart_paths.url||games_table.art_fanart as fanart,games_table.launch_parameters,games_table.user_game_launch_addon,games_table.user_game_external_launch_command,games_table.user_game_post_download_process,game_list_table.default_global_post_download_process,game_list_table.default_global_launcher,game_list_table.user_post_download_process,game_list_table.user_global_launcher,game_list_table.user_global_launch_addon,game_list_table.user_global_external_launch_command,game_list_table.user_global_uses_applaunch,game_list_table.user_global_uses_apppause,game_list_table.user_global_download_path,game_list_table.default_global_launch_addon,game_list_table.default_global_external_launch_command,games_table.rom\n'
													'FROM games as games_table\n'
													'LEFT JOIN game_list as game_list_table on games_table.game_list = game_list_table.label\n'
													'LEFT JOIN paths as banner_paths\n'
													'ON banner_paths."path" = games_table.art_banner_path\n'
													'LEFT JOIN paths as box_paths\n'
													'ON box_paths."path" = games_table.art_box_path\n'
													'LEFT JOIN paths as clearlogo_paths\n'
													'ON clearlogo_paths."path" = games_table.art_logo_path\n'
													'LEFT JOIN paths as title_paths\n'
													'ON title_paths."path" = games_table.art_title_path\n'
													'LEFT JOIN paths as snapshot_paths\n'
													'ON snapshot_paths."path" = games_table.art_snapshot_path\n'
													'LEFT JOIN paths as fanart_paths\n'
													'ON fanart_paths."path" = games_table.art_fanart_path\n'
													'WHERE games_table.uid = "{game_id}"')
		self.database['query']['get_game_from_originaltitle_fuzzy'] = ('SELECT "/play_game_external_netplay/"||games_table.uid as next_path,games_table.uid,games_table.game_list as game_list_id,games_table.originaltitle AS originaltitle,{game_title_setting} as label,games_table.game_list as label2,{game_title_setting} as title,games_table.name_search as sorttitle,games_table.system as platform,games_table.genres AS genres,games_table.studio as publisher,games_table.year,games_table.size,games_table.plot as overview,banner_paths.url||games_table.art_banner as banner,box_paths.url||games_table.art_box as poster,clearlogo_paths.url||games_table.art_logo as clearlogo,title_paths.url||games_table.art_title as landscape,snapshot_paths.url||games_table.art_snapshot as thumb,fanart_paths.url||games_table.art_fanart as fanart,games_table.launch_parameters,games_table.user_game_launch_addon,games_table.user_game_external_launch_command,games_table.user_game_post_download_process,game_list_table.default_global_post_download_process,game_list_table.default_global_launcher,game_list_table.user_post_download_process,game_list_table.user_global_launcher,game_list_table.user_global_launch_addon,game_list_table.user_global_external_launch_command,game_list_table.user_global_uses_applaunch,game_list_table.user_global_uses_apppause,game_list_table.user_global_download_path,game_list_table.default_global_launch_addon,game_list_table.default_global_external_launch_command,games_table.rom\n'
														'FROM games as games_table\n'
														'LEFT JOIN game_list as game_list_table on games_table.game_list = game_list_table.label\n'
														'LEFT JOIN paths as banner_paths\n'
														'ON banner_paths."path" = games_table.art_banner_path\n'
														'LEFT JOIN paths as box_paths\n'
														'ON box_paths."path" = games_table.art_box_path\n'
														'LEFT JOIN paths as clearlogo_paths\n'
														'ON clearlogo_paths."path" = games_table.art_logo_path\n'
														'LEFT JOIN paths as title_paths\n'
														'ON title_paths."path" = games_table.art_title_path\n'
														'LEFT JOIN paths as snapshot_paths\n'
														'ON snapshot_paths."path" = games_table.art_snapshot_path\n'
														'LEFT JOIN paths as fanart_paths\n'
														'ON fanart_paths."path" = games_table.art_fanart_path\n'
														'WHERE games_table.originaltitle = "{game_name}" or games_table.originaltitle LIKE "%{game_name}%" or games_table.rom LIKE "%{game_name}%"')
		self.database['query']['get_game_list_launcher'] = ('SELECT game_lists_table.default_global_launcher,game_lists_table.user_global_launcher\n'
															'FROM game_list as game_lists_table\n'
															'WHERE game_lists_table.label = "{game_list_id}"')
		self.database['query']['get_game_list_parameter'] = ('SELECT {parameter}\n'
															'FROM game_list as game_lists_table\n'
															'WHERE game_lists_table.label = "{game_list_id}"')
		self.database['query']['get_game_list_user_global_external_launch_command'] = ('SELECT game_lists_table.default_global_external_launch_command,game_lists_table.user_global_external_launch_command,game_lists_table.user_global_uses_applaunch,game_lists_table.user_global_uses_apppause\n'
																						'FROM game_list as game_lists_table\n'
																						'WHERE game_lists_table.label = "{game_list_id}"')
		self.database['query']['get_all_game_list_user_settings_for_transfer'] = ('SELECT games_list_table.label,games_list_table.user_global_download_path,games_list_table.user_global_external_launch_command,games_list_table.user_global_launch_addon,games_list_table.user_global_launcher,games_list_table.user_global_visibility,games_list_table.user_post_download_process,games_list_table.user_global_uses_apppause,games_list_table.user_global_uses_applaunch\n'
																				 'FROM game_list as games_list_table\n'
																				 'WHERE (games_list_table.user_global_download_path is not NULL or games_list_table.user_global_external_launch_command is not NULL or games_list_table.user_global_launch_addon is not NULL or games_list_table.user_global_launcher is not NULL or games_list_table.user_global_visibility is not NULL or games_list_table.user_post_download_process is not NULL or games_list_table.user_global_uses_apppause is not NULL or games_list_table.user_global_uses_applaunch is not NULL)')
		self.database['query']['transfer_game_list_user_settings'] = 'UPDATE game_list SET user_global_download_path={user_global_download_path},user_global_external_launch_command={user_global_external_launch_command},user_global_launch_addon={user_global_launch_addon},user_global_launcher={user_global_launcher},user_global_visibility={user_global_visibility},user_post_download_process={user_post_download_process},user_global_uses_apppause={user_global_uses_apppause},user_global_uses_applaunch={user_global_uses_applaunch} WHERE label="{label}"'
		self.database['query']['get_all_favorites_for_transfer'] = ('SELECT fav_table.uid,fav_table.fav_group,fav_table.fav_link_name,fav_table.is_search_link,fav_table.is_random_link,fav_table.link_query,games_table.originaltitle,games_table.game_list\n'
																	'FROM favorites as fav_table\n'
																	'LEFT JOIN games as games_table\n'
																	'ON games_table.uid = fav_table.uid')
		self.database['query']['get_all_history_for_transfer'] = ('SELECT history_table.uid,history_table.insert_time,games_table.originaltitle,games_table.game_list\n'
																'FROM history as history_table\n'
																'LEFT JOIN games as games_table\n'
																'ON games_table.uid = history_table.uid')
		self.database['query']['get_all_game_table_values_for_transfer'] = ('SELECT games_table.uid,games_table.originaltitle,games_table.game_list,games_table.user_game_launcher,games_table.user_game_launch_addon,games_table.user_game_external_launch_command,games_table.user_game_post_download_process,games_table.user_is_favorite,games_table.lastplayed,games_table.playcount\n'
																			'FROM games as games_table\n'
																			'WHERE (games_table.user_game_launcher is not NULL or games_table.user_game_launch_addon is not NULL or games_table.user_game_external_launch_command is not NULL or games_table.user_game_post_download_process is not NULL or games_table.user_is_favorite is not NULL or games_table.lastplayed is not NULL or games_table.playcount is not NULL)')
		self.database['query']['get_all_uids_in_new_db'] = 'SELECT games_table.uid from games as games_table WHERE games_table.uid in ({old_uids})'
		self.database['query']['get_all_old_uids_by_originaltitle_and_list'] = ('SELECT "{old_uid}" as old_uid,games_table.uid as new_uid\n'
																				'FROM games as games_table\n'
																				'LEFT JOIN game_list as game_lists_table on game_lists_table.label = games_table.game_list\n'
																				'WHERE games_table.originaltitle = "{game_title}" and game_lists_table.label = "{game_list}"')
		self.database['query']['get_game_list_info'] = ('SELECT game_lists_table.label,game_lists_table.system,game_lists_table.total_1g1r_games,game_lists_table.total_games,game_lists_table.default_global_external_launch_command,core_info_table.display_name as default_global_external_launch_core_name,game_lists_table.default_global_launch_addon,game_lists_table.default_global_launcher,game_lists_table.default_global_post_download_process,game_lists_table.user_global_download_path,game_lists_table.user_global_external_launch_command,game_lists_table.user_global_uses_applaunch,game_lists_table.user_global_uses_apppause,game_lists_table.user_global_launch_addon,game_lists_table.user_global_launcher,game_lists_table.user_global_visibility,game_lists_table.user_post_download_process,COUNT(games_table.user_is_favorite) as total_favorited_games\n'
														'FROM game_list as game_lists_table\n'
														'LEFT JOIN games as games_table on games_table.game_list = game_lists_table.label and games_table.user_is_favorite is NOT NULL\n'
														'LEFT JOIN core_info as core_info_table on core_info_table.core_stem = game_lists_table.default_global_external_launch_command\n'
														'WHERE game_lists_table.label = "{game_list_id}"')
		self.database['query']['get_game_list_info_from_game_id'] = ('SELECT game_lists_table.label,game_lists_table.system,game_lists_table.default_global_external_launch_command,core_info_table.display_name as default_global_external_launch_core_name,game_lists_table.default_global_launch_addon,game_lists_table.default_global_launcher,game_lists_table.default_global_post_download_process,game_lists_table.user_global_download_path,game_lists_table.user_global_external_launch_command,game_lists_table.user_global_uses_applaunch,game_lists_table.user_global_uses_apppause,game_lists_table.user_global_launch_addon,game_lists_table.user_global_launcher,game_lists_table.user_global_visibility,game_lists_table.user_post_download_process,games_table.uid,games_table.originaltitle AS originaltitle,games_table.name_search as sorttitle,games_table.system as platform,games_table.genres AS genres,games_table.studio as publisher,games_table.year,games_table.size,games_table.plot as overview,games_table.launch_parameters,games_table.user_game_launch_addon,games_table.user_game_external_launch_command,games_table.user_game_post_download_process,games_table.rom\n'
																	'FROM games as games_table\n'
																	'LEFT JOIN game_list as game_lists_table on game_lists_table.label = games_table.game_list\n'
																	'LEFT JOIN core_info as core_info_table on core_info_table.core_stem = game_lists_table.default_global_external_launch_command\n'
																	'WHERE games_table.uid = "{game_id}"')
		self.database['query']['search_random_get_game_lists'] = ('SELECT game_lists_table.label as label,NULL as next_path,poster_paths.url||game_lists_table.poster as thumb\n'
																'FROM game_list as game_lists_table\n'
																'LEFT JOIN paths as poster_paths\n'
																'ON poster_paths."path" = game_lists_table.poster_path\n'
																'WHERE game_lists_table.user_global_visibility is NULL\n'
																'ORDER BY game_lists_table.label COLLATE NOCASE ASC')
		self.database['query']['get_hidden_game_lists'] = ('SELECT game_lists_table.label as label,NULL as next_path,poster_paths.url||game_lists_table.poster as thumb\n'
															'FROM game_list as game_lists_table\n'
															'LEFT JOIN paths as poster_paths\n'
															'ON poster_paths."path" = game_lists_table.poster_path\n'
															'WHERE game_lists_table.user_global_visibility = "hidden"\n'
															'ORDER BY game_lists_table.label COLLATE NOCASE ASC')
		self.database['query']['search_random_choose_all'] = ('SELECT choose_table.label as label,NULL as next_path,thumb_paths.url||choose_table.thumb as thumb\n'
																'FROM {table_select} as choose_table\n'
																'LEFT JOIN paths as thumb_paths\n'
																'ON thumb_paths."path" = choose_table.thumb_path\n'
																'ORDER BY choose_table.label COLLATE NOCASE ASC')
		self.database['query']['search_random_choose_matching_lists'] = ('SELECT choose_table.label as label,NULL as next_path,thumb_paths.url||choose_table.thumb as thumb\n'
																		'FROM {table_select} as choose_table\n'
																		'LEFT JOIN paths as thumb_paths\n'
																		'ON thumb_paths."path" = choose_table.thumb_path\n'
																		'WHERE choose_table.matching_lists {game_list_query}\n'
																		'ORDER BY choose_table.label COLLATE NOCASE ASC')
		self.database['query']['browse_favorites'] = ('SELECT browse_table.label,browse_table.next_path,browse_table.localization,browse_table.plot,thumb_paths.url||browse_table.thumb as thumb,poster_paths.url||browse_table.poster as poster,banner_paths.url||browse_table.banner as banner,(SELECT url FROM default_art WHERE art_type="fanart") as fanart,clearlogo_paths.url||browse_table.clearlogo as clearlogo\n'
														'FROM choose_favorite as browse_table\n'
														'LEFT JOIN paths as thumb_paths\n'
														'ON thumb_paths."path" = browse_table.thumb_path\n'
														'LEFT JOIN paths as poster_paths\n'
														'ON poster_paths."path" = browse_table.poster_path\n'
														'LEFT JOIN paths as banner_paths\n'
														'ON banner_paths."path" = browse_table.banner_path\n'
														'LEFT JOIN paths as clearlogo_paths\n'
														'ON clearlogo_paths."path" = browse_table.clearlogo_path')
		self.database['query']['favorites_by_all_no_page'] = ('SELECT * FROM (\n'
															'SELECT "play_game/"||games_table.uid as next_path,games_table.originaltitle AS originaltitle,{game_title_setting} as label,{game_title_setting} as title,games_table.name_search as sorttitle,games_table.system as "set",games_table.system as "tvshowtitle",games_table.genres AS genre,games_table.studio,DATE(games_table.date) AS date,DATE(games_table.date) as premiered,games_table.year,games_table.ESRB as mpaa,games_table.rating,games_table.tags as tag,games_table.size,games_table.plot,games_table.regions AS country,games_table.lastplayed,games_table.playcount,"plugin://plugin.video.youtube/play/?video_id="||games_table.trailer as trailer,banner_paths.url||games_table.art_banner as banner,box_paths.url||games_table.art_box as poster,clearlogo_paths.url||games_table.art_logo as clearlogo,{landscape_to_game_art} as landscape,{thumbnail_to_game_art} as thumb,fanart_paths.url||games_table.art_fanart as fanart,NULL as link_query\n'
															'FROM favorites as fav_table\n'
															'LEFT JOIN games as games_table\n'
															'ON games_table.uid = fav_table.uid\n'
															'LEFT JOIN game_list as game_lists_table\n'
															'ON game_lists_table.label = games_table.game_list\n'
															'LEFT JOIN paths as banner_paths\n'
															'ON banner_paths."path" = games_table.art_banner_path\n'
															'LEFT JOIN paths as box_paths\n'
															'ON box_paths."path" = games_table.art_box_path\n'
															'LEFT JOIN paths as clearlogo_paths\n'
															'ON clearlogo_paths."path" = games_table.art_logo_path\n'
															'LEFT JOIN paths as title_paths\n'
															'ON title_paths."path" = games_table.art_title_path\n'
															'LEFT JOIN paths as snapshot_paths\n'
															'ON snapshot_paths."path" = games_table.art_snapshot_path\n'
															'LEFT JOIN paths as fanart_paths\n'
															'ON fanart_paths."path" = games_table.art_fanart_path\n'
															'WHERE fav_table.uid is not NULL\n'
															'UNION\n'
															'SELECT "search_from_link?query="||fav_table2.link_query as next_path,fav_table2.fav_link_name AS originaltitle,fav_table2.fav_link_name as label,fav_table2.fav_link_name as title,fav_table2.fav_link_name as sorttitle,"IAGL Search" as "set","IAGL Search" as "tvshowtitle",NULL AS genre,NULL as studio,NULL AS date,NULL as premiered,NULL as year,NULL as mpaa,NULL as rating,NULL as tag,NULL as size,"IAGL Search Link" as plot,NULL as country,NULL as trailer,NULL as lastplayed,NULL as playcount,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_banner.png" as banner,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_poster.png" as poster,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_clearlogo.png" as clearlogo,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_landscape.png" as landscape,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_thumb.png" as thumb,"special://xbmc/addons/plugin.program.iagl/fanart.png" as fanart,fav_table2.link_query as link_query\n'
															'FROM favorites as fav_table2\n'
															'WHERE fav_table2.is_search_link = 1\n'
															'UNION\n'
															'SELECT "random_from_link?query="||fav_table3.link_query as next_path,fav_table3.fav_link_name AS originaltitle,fav_table3.fav_link_name as label,fav_table3.fav_link_name as title,fav_table3.fav_link_name as sorttitle,"IAGL Search" as "set","IAGL Search" as "tvshowtitle",NULL AS genre,NULL as studio,NULL AS date,NULL as premiered,NULL as year,NULL as mpaa,NULL as rating,NULL as tag,NULL as size,"IAGL Random Link" as plot,NULL as country,NULL as trailer,NULL as lastplayed,NULL as playcount,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_banner.png" as banner,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_poster.png" as poster,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_clearlogo.png" as clearlogo,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_landscape.png" as landscape,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_thumb.png" as thumb,"special://xbmc/addons/plugin.program.iagl/fanart.png" as fanart,fav_table3.link_query as link_query\n'
															'FROM favorites as fav_table3\n'
															'WHERE fav_table3.is_random_link = 1\n'
															') as combined_table\n'
															'ORDER BY combined_table.originaltitle COLLATE NOCASE ASC')
		self.database['query']['favorites_by_all_page'] = ('SELECT * FROM (\n'
															'SELECT "play_game/"||games_table.uid as next_path,games_table.originaltitle AS originaltitle,{game_title_setting} as label,{game_title_setting} as title,games_table.name_search as sorttitle,games_table.system as "set",games_table.system as "tvshowtitle",games_table.genres AS genre,games_table.studio,DATE(games_table.date) AS date,DATE(games_table.date) as premiered,games_table.year,games_table.ESRB as mpaa,games_table.rating,games_table.tags as tag,games_table.size,games_table.plot,games_table.regions AS country,games_table.lastplayed,games_table.playcount,"plugin://plugin.video.youtube/play/?video_id="||games_table.trailer as trailer,banner_paths.url||games_table.art_banner as banner,box_paths.url||games_table.art_box as poster,clearlogo_paths.url||games_table.art_logo as clearlogo,{landscape_to_game_art} as landscape,{thumbnail_to_game_art} as thumb,fanart_paths.url||games_table.art_fanart as fanart,NULL as link_query\n'
															'FROM favorites as fav_table\n'
															'LEFT JOIN games as games_table\n'
															'ON games_table.uid = fav_table.uid\n'
															'LEFT JOIN game_list as game_lists_table\n'
															'ON game_lists_table.label = games_table.game_list\n'
															'LEFT JOIN paths as banner_paths\n'
															'ON banner_paths."path" = games_table.art_banner_path\n'
															'LEFT JOIN paths as box_paths\n'
															'ON box_paths."path" = games_table.art_box_path\n'
															'LEFT JOIN paths as clearlogo_paths\n'
															'ON clearlogo_paths."path" = games_table.art_logo_path\n'
															'LEFT JOIN paths as title_paths\n'
															'ON title_paths."path" = games_table.art_title_path\n'
															'LEFT JOIN paths as snapshot_paths\n'
															'ON snapshot_paths."path" = games_table.art_snapshot_path\n'
															'LEFT JOIN paths as fanart_paths\n'
															'ON fanart_paths."path" = games_table.art_fanart_path\n'
															'WHERE fav_table.uid is not NULL\n'
															'UNION\n'
															'SELECT "search_from_link?query="||fav_table2.link_query as next_path,fav_table2.fav_link_name AS originaltitle,fav_table2.fav_link_name as label,fav_table2.fav_link_name as title,fav_table2.fav_link_name as sorttitle,"IAGL Search" as "set","IAGL Search" as "tvshowtitle",NULL AS genre,NULL as studio,NULL AS date,NULL as premiered,NULL as year,NULL as mpaa,NULL as rating,NULL as tag,NULL as size,"IAGL Search Link" as plot,NULL as country,NULL as trailer,NULL as lastplayed,NULL as playcount,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_banner.png" as banner,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_poster.png" as poster,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_clearlogo.png" as clearlogo,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_landscape.png" as landscape,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_thumb.png" as thumb,"special://xbmc/addons/plugin.program.iagl/fanart.png" as fanart,fav_table2.link_query as link_query\n'
															'FROM favorites as fav_table2\n'
															'WHERE fav_table2.is_search_link = 1\n'
															'UNION\n'
															'SELECT "random_from_link?query="||fav_table3.link_query as next_path,fav_table3.fav_link_name AS originaltitle,fav_table3.fav_link_name as label,fav_table3.fav_link_name as title,fav_table3.fav_link_name as sorttitle,"IAGL Search" as "set","IAGL Search" as "tvshowtitle",NULL AS genre,NULL as studio,NULL AS date,NULL as premiered,NULL as year,NULL as mpaa,NULL as rating,NULL as tag,NULL as size,"IAGL Random Link" as plot,NULL as country,NULL as trailer,NULL as lastplayed,NULL as playcount,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_banner.png" as banner,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_poster.png" as poster,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_clearlogo.png" as clearlogo,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_landscape.png" as landscape,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_thumb.png" as thumb,"special://xbmc/addons/plugin.program.iagl/fanart.png" as fanart,fav_table3.link_query as link_query\n'
															'FROM favorites as fav_table3\n'
															'WHERE fav_table3.is_random_link = 1\n'
															') as combined_table\n'
															'ORDER BY combined_table.originaltitle COLLATE NOCASE ASC\n'
															'LIMIT {items_per_page} OFFSET {starting_number}')
		self.database['query']['favorites_by_group_no_page'] = ('SELECT * FROM (\n'
															'SELECT "play_game/"||games_table.uid as next_path,games_table.originaltitle AS originaltitle,{game_title_setting} as label,{game_title_setting} as title,games_table.name_search as sorttitle,games_table.system as "set",games_table.system as "tvshowtitle",games_table.genres AS genre,games_table.studio,DATE(games_table.date) AS date,DATE(games_table.date) as premiered,games_table.year,games_table.ESRB as mpaa,games_table.rating,games_table.tags as tag,games_table.size,games_table.plot,games_table.regions AS country,games_table.lastplayed,games_table.playcount,"plugin://plugin.video.youtube/play/?video_id="||games_table.trailer as trailer,banner_paths.url||games_table.art_banner as banner,box_paths.url||games_table.art_box as poster,clearlogo_paths.url||games_table.art_logo as clearlogo,{landscape_to_game_art} as landscape,{thumbnail_to_game_art} as thumb,fanart_paths.url||games_table.art_fanart as fanart,NULL as link_query\n'
															'FROM favorites as fav_table\n'
															'LEFT JOIN games as games_table\n'
															'ON games_table.uid = fav_table.uid\n'
															'LEFT JOIN game_list as game_lists_table\n'
															'ON game_lists_table.label = games_table.game_list\n'
															'LEFT JOIN paths as banner_paths\n'
															'ON banner_paths."path" = games_table.art_banner_path\n'
															'LEFT JOIN paths as box_paths\n'
															'ON box_paths."path" = games_table.art_box_path\n'
															'LEFT JOIN paths as clearlogo_paths\n'
															'ON clearlogo_paths."path" = games_table.art_logo_path\n'
															'LEFT JOIN paths as title_paths\n'
															'ON title_paths."path" = games_table.art_title_path\n'
															'LEFT JOIN paths as snapshot_paths\n'
															'ON snapshot_paths."path" = games_table.art_snapshot_path\n'
															'LEFT JOIN paths as fanart_paths\n'
															'ON fanart_paths."path" = games_table.art_fanart_path\n'
															'WHERE fav_table.uid is not NULL and fav_table.fav_group = "{group_id}"\n'
															'UNION\n'
															'SELECT "search_from_link?query="||fav_table2.link_query as next_path,fav_table2.fav_link_name AS originaltitle,fav_table2.fav_link_name as label,fav_table2.fav_link_name as title,fav_table2.fav_link_name as sorttitle,"IAGL Search" as "set","IAGL Search" as "tvshowtitle",NULL AS genre,NULL as studio,NULL AS date,NULL as premiered,NULL as year,NULL as mpaa,NULL as rating,NULL as tag,NULL as size,"IAGL Search Link" as plot,NULL as country,NULL as trailer,NULL as lastplayed,NULL as playcount,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_banner.png" as banner,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_poster.png" as poster,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_clearlogo.png" as clearlogo,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_landscape.png" as landscape,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_thumb.png" as thumb,"special://xbmc/addons/plugin.program.iagl/fanart.png" as fanart,fav_table2.link_query as link_query\n'
															'FROM favorites as fav_table2\n'
															'WHERE fav_table2.is_search_link = 1 and fav_table2.fav_group = "{group_id}"\n'
															'UNION\n'
															'SELECT "random_from_link?query="||fav_table3.link_query as next_path,fav_table3.fav_link_name AS originaltitle,fav_table3.fav_link_name as label,fav_table3.fav_link_name as title,fav_table3.fav_link_name as sorttitle,"IAGL Search" as "set","IAGL Search" as "tvshowtitle",NULL AS genre,NULL as studio,NULL AS date,NULL as premiered,NULL as year,NULL as mpaa,NULL as rating,NULL as tag,NULL as size,"IAGL Random Link" as plot,NULL as country,NULL as trailer,NULL as lastplayed,NULL as playcount,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_banner.png" as banner,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_poster.png" as poster,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_clearlogo.png" as clearlogo,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_landscape.png" as landscape,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_thumb.png" as thumb,"special://xbmc/addons/plugin.program.iagl/fanart.png" as fanart,fav_table3.link_query as link_query\n'
															'FROM favorites as fav_table3\n'
															'WHERE fav_table3.is_random_link = 1 and fav_table3.fav_group = "{group_id}"\n'
															') as combined_table\n'
															'ORDER BY combined_table.originaltitle COLLATE NOCASE ASC')
		self.database['query']['favorites_by_group_page'] = ('SELECT * FROM (\n'
															'SELECT "play_game/"||games_table.uid as next_path,games_table.originaltitle AS originaltitle,{game_title_setting} as label,{game_title_setting} as title,games_table.name_search as sorttitle,games_table.system as "set",games_table.system as "tvshowtitle",games_table.genres AS genre,games_table.studio,DATE(games_table.date) AS date,DATE(games_table.date) as premiered,games_table.year,games_table.ESRB as mpaa,games_table.rating,games_table.tags as tag,games_table.size,games_table.plot,games_table.regions AS country,games_table.lastplayed,games_table.playcount,"plugin://plugin.video.youtube/play/?video_id="||games_table.trailer as trailer,banner_paths.url||games_table.art_banner as banner,box_paths.url||games_table.art_box as poster,clearlogo_paths.url||games_table.art_logo as clearlogo,{landscape_to_game_art} as landscape,{thumbnail_to_game_art} as thumb,fanart_paths.url||games_table.art_fanart as fanart,NULL as link_query\n'
															'FROM favorites as fav_table\n'
															'LEFT JOIN games as games_table\n'
															'ON games_table.uid = fav_table.uid\n'
															'LEFT JOIN game_list as game_lists_table\n'
															'ON game_lists_table.label = games_table.game_list\n'
															'LEFT JOIN paths as banner_paths\n'
															'ON banner_paths."path" = games_table.art_banner_path\n'
															'LEFT JOIN paths as box_paths\n'
															'ON box_paths."path" = games_table.art_box_path\n'
															'LEFT JOIN paths as clearlogo_paths\n'
															'ON clearlogo_paths."path" = games_table.art_logo_path\n'
															'LEFT JOIN paths as title_paths\n'
															'ON title_paths."path" = games_table.art_title_path\n'
															'LEFT JOIN paths as snapshot_paths\n'
															'ON snapshot_paths."path" = games_table.art_snapshot_path\n'
															'LEFT JOIN paths as fanart_paths\n'
															'ON fanart_paths."path" = games_table.art_fanart_path\n'
															'WHERE fav_table.uid is not NULL and fav_table.fav_group = "{group_id}"\n'
															'UNION\n'
															'SELECT "search_from_link?query="||fav_table2.link_query as next_path,fav_table2.fav_link_name AS originaltitle,fav_table2.fav_link_name as label,fav_table2.fav_link_name as title,fav_table2.fav_link_name as sorttitle,"IAGL Search" as "set","IAGL Search" as "tvshowtitle",NULL AS genre,NULL as studio,NULL AS date,NULL as premiered,NULL as year,NULL as mpaa,NULL as rating,NULL as tag,NULL as size,"IAGL Search Link" as plot,NULL as country,NULL as trailer,NULL as lastplayed,NULL as playcount,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_banner.png" as banner,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_poster.png" as poster,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_clearlogo.png" as clearlogo,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_landscape.png" as landscape,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_thumb.png" as thumb,"special://xbmc/addons/plugin.program.iagl/fanart.png" as fanart,fav_table2.link_query as link_query\n'
															'FROM favorites as fav_table2\n'
															'WHERE fav_table2.is_search_link = 1 and fav_table2.fav_group = "{group_id}"\n'
															'UNION\n'
															'SELECT "random_from_link?query="||fav_table3.link_query as next_path,fav_table3.fav_link_name AS originaltitle,fav_table3.fav_link_name as label,fav_table3.fav_link_name as title,fav_table3.fav_link_name as sorttitle,"IAGL Search" as "set","IAGL Search" as "tvshowtitle",NULL AS genre,NULL as studio,NULL AS date,NULL as premiered,NULL as year,NULL as mpaa,NULL as rating,NULL as tag,NULL as size,"IAGL Random Link" as plot,NULL as country,NULL as trailer,NULL as lastplayed,NULL as playcount,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_banner.png" as banner,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_poster.png" as poster,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_clearlogo.png" as clearlogo,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_landscape.png" as landscape,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_thumb.png" as thumb,"special://xbmc/addons/plugin.program.iagl/fanart.png" as fanart,fav_table3.link_query as link_query\n'
															'FROM favorites as fav_table3\n'
															'WHERE fav_table3.is_random_link = 1 and fav_table3.fav_group = "{group_id}"\n'
															') as combined_table\n'
															'ORDER BY combined_table.originaltitle COLLATE NOCASE ASC\n'
															'LIMIT {items_per_page} OFFSET {starting_number}')
		self.database['query']['favorites_by_group'] = ('SELECT * FROM (\n'
														'SELECT fav_table.fav_group as label,fav_table.fav_group as next_path,banner_paths.url||games_table.art_banner as banner,box_paths.url||games_table.art_box as poster,clearlogo_paths.url||games_table.art_logo as clearlogo,title_paths.url||games_table.art_title as landscape,snapshot_paths.url||games_table.art_snapshot as thumb,fanart_paths.url||games_table.art_fanart as fanart\n'
														'FROM favorites as fav_table\n'
														'LEFT JOIN games as games_table\n'
														'ON games_table.uid = (SELECT fav_table2.uid FROM favorites as fav_table2 WHERE fav_table2.fav_group = fav_table.fav_group ORDER BY RANDOM())\n'
														'LEFT JOIN paths as banner_paths\n'
														'ON banner_paths."path" = games_table.art_banner_path\n'
														'LEFT JOIN paths as box_paths\n'
														'ON box_paths."path" = games_table.art_box_path\n'
														'LEFT JOIN paths as clearlogo_paths\n'
														'ON clearlogo_paths."path" = games_table.art_logo_path\n'
														'LEFT JOIN paths as title_paths\n'
														'ON title_paths."path" = games_table.art_title_path\n'
														'LEFT JOIN paths as snapshot_paths\n'
														'ON snapshot_paths."path" = games_table.art_snapshot_path\n'
														'LEFT JOIN paths as fanart_paths\n'
														'ON fanart_paths."path" = games_table.art_fanart_path\n'
														'WHERE fav_table.uid is not NULL\n'
														'GROUP BY fav_table.fav_group\n'
														'UNION\n'
														'SELECT fav_table2.fav_group as label,fav_table2.fav_group as next_path,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_banner.png" as banner,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_poster.png" as poster,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_clearlogo.png" as clearlogo,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_landscape.png" as landscape,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_thumb.png" as thumb,"special://xbmc/addons/plugin.program.iagl/fanart.png" as fanart\n'
														'FROM favorites as fav_table2\n'
														'WHERE fav_table2.is_search_link = 1\n'
														'GROUP BY fav_table2.fav_group\n'
														'UNION\n'
														'SELECT fav_table3.fav_group as label,fav_table3.fav_group as next_path,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_banner.png" as banner,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_poster.png" as poster,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_clearlogo.png" as clearlogo,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_landscape.png" as landscape,"special://xbmc/addons/plugin.program.iagl/assets/default/favorites_thumb.png" as thumb,"special://xbmc/addons/plugin.program.iagl/fanart.png" as fanart\n'
														'FROM favorites as fav_table3\n'
														'WHERE fav_table3.is_random_link = 1\n'
														'GROUP BY fav_table3.fav_group\n'
														') as combined_table\n'
														'GROUP BY combined_table.label\n'
														'ORDER BY combined_table.label COLLATE NOCASE ASC')
		self.database['query']['history_no_page'] = ('SELECT "play_game/"||games_table.uid as next_path,games_table.originaltitle AS originaltitle,{game_title_setting} as label,{game_title_setting} as title,games_table.name_search as sorttitle,games_table.system as "set",games_table.system as "tvshowtitle",games_table.genres AS genre,games_table.studio,DATE(games_table.date) AS date,DATE(games_table.date) as premiered,games_table.year,games_table.ESRB as mpaa,games_table.rating,games_table.tags as tag,games_table.size,games_table.plot,games_table.regions AS country,games_table.lastplayed,games_table.playcount,"plugin://plugin.video.youtube/play/?video_id="||games_table.trailer as trailer,banner_paths.url||games_table.art_banner as banner,box_paths.url||games_table.art_box as poster,clearlogo_paths.url||games_table.art_logo as clearlogo,{landscape_to_game_art} as landscape,{thumbnail_to_game_art} as thumb,fanart_paths.url||games_table.art_fanart as fanart\n'
													'FROM history as history_table\n'
													'LEFT JOIN games as games_table\n'
													'ON games_table.uid = history_table.uid\n'
													'LEFT JOIN game_list as game_lists_table\n'
													'ON game_lists_table.label = games_table.game_list\n'
													'LEFT JOIN paths as banner_paths\n'
													'ON banner_paths."path" = games_table.art_banner_path\n'
													'LEFT JOIN paths as box_paths\n'
													'ON box_paths."path" = games_table.art_box_path\n'
													'LEFT JOIN paths as clearlogo_paths\n'
													'ON clearlogo_paths."path" = games_table.art_logo_path\n'
													'LEFT JOIN paths as title_paths\n'
													'ON title_paths."path" = games_table.art_title_path\n'
													'LEFT JOIN paths as snapshot_paths\n'
													'ON snapshot_paths."path" = games_table.art_snapshot_path\n'
													'LEFT JOIN paths as fanart_paths\n'
													'ON fanart_paths."path" = games_table.art_fanart_path\n'
													'ORDER BY history_table.insert_time DESC')
		self.database['query']['history_page'] = ('SELECT "play_game/"||games_table.uid as next_path,games_table.originaltitle AS originaltitle,{game_title_setting} as label,{game_title_setting} as title,games_table.name_search as sorttitle,games_table.system as "set",games_table.system as "tvshowtitle",games_table.genres AS genre,games_table.studio,DATE(games_table.date) AS date,DATE(games_table.date) as premiered,games_table.year,games_table.ESRB as mpaa,games_table.rating,games_table.tags as tag,games_table.size,games_table.plot,games_table.regions AS country,games_table.lastplayed,games_table.playcount,"plugin://plugin.video.youtube/play/?video_id="||games_table.trailer as trailer,banner_paths.url||games_table.art_banner as banner,box_paths.url||games_table.art_box as poster,clearlogo_paths.url||games_table.art_logo as clearlogo,title_paths.url||games_table.art_title as landscape,snapshot_paths.url||games_table.art_snapshot as thumb,fanart_paths.url||games_table.art_fanart as fanart\n'
													'FROM history as history_table\n'
													'LEFT JOIN games as games_table\n'
													'ON games_table.uid = history_table.uid\n'
													'LEFT JOIN game_list as game_lists_table\n'
													'ON game_lists_table.label = games_table.game_list\n'
													'LEFT JOIN game_list as game_lists_table\n'
													'ON game_lists_table.label = games_table.game_list\n'
													'LEFT JOIN paths as banner_paths\n'
													'ON banner_paths."path" = games_table.art_banner_path\n'
													'LEFT JOIN paths as box_paths\n'
													'ON box_paths."path" = games_table.art_box_path\n'
													'LEFT JOIN paths as clearlogo_paths\n'
													'ON clearlogo_paths."path" = games_table.art_logo_path\n'
													'LEFT JOIN paths as title_paths\n'
													'ON title_paths."path" = games_table.art_title_path\n'
													'LEFT JOIN paths as snapshot_paths\n'
													'ON snapshot_paths."path" = games_table.art_snapshot_path\n'
													'LEFT JOIN paths as fanart_paths\n'
													'ON fanart_paths."path" = games_table.art_fanart_path\n'
													'ORDER BY history_table.insert_time DESC\n'
													'LIMIT {items_per_page} OFFSET {starting_number}')
		self.database['query']['get_favorite_group_names'] = ('SELECT DISTINCT fav_table.fav_group as label\n'
														'FROM favorites as fav_table')
		self.database['query']['insert_favorite'] = ('INSERT INTO favorites(uid,fav_link_name,fav_group,is_search_link,is_random_link,link_query)\n'
													 'VALUES(?,?,?,?,?,?)')
		self.database['query']['transfer_game_values'] = ('UPDATE games SET user_game_launcher={user_game_launcher},user_game_launch_addon={user_game_launch_addon},user_game_external_launch_command={user_game_external_launch_command},user_game_post_download_process={user_game_post_download_process},user_is_favorite={user_is_favorite},lastplayed={lastplayed},playcount={playcount}\n'
														  'WHERE uid="{uid}"')
		self.database['query']['mark_game_as_favorite'] = 'UPDATE games SET user_is_favorite=1 WHERE uid="{}"'
		self.database['query']['unmark_game_as_favorite'] = 'UPDATE games SET user_is_favorite=NULL WHERE uid="{}"'
		self.database['query']['insert_history'] = ('INSERT INTO history(uid,insert_time)\n'
													'VALUES(?,?)')
		
		self.database['query']['limit_history'] = ('DELETE FROM history\n'
													'WHERE uid NOT IN (SELECT history_table.uid FROM history as history_table order by history_table.insert_time DESC LIMIT {history_limit})')
		self.database['query']['delete_history_from_uid'] = 'DELETE FROM history WHERE uid = "{}"'
		self.database['query']['get_total_history'] = 'SELECT count(*) as total_history FROM history'
		self.database['query']['delete_favorite_from_uid'] = 'DELETE FROM favorites WHERE uid="{}"'
		self.database['query']['delete_favorite_from_link'] = 'DELETE FROM favorites WHERE link_query="{}"'
		self.database['query']['rename_favorite_link'] = ('UPDATE favorites SET fav_link_name="{}" WHERE link_query="{}"')
		self.database['query']['rename_favorites_group'] = ('UPDATE favorites SET fav_group="{}" WHERE fav_group="{}"')
		self.database['query']['search_games'] = ('SELECT "play_game/"||games_table.uid as next_path,games_table.originaltitle AS originaltitle,{game_title_setting} as label,{game_title_setting} as title,games_table.name_search as sorttitle,games_table.system as "set",games_table.system as "tvshowtitle",games_table.genres AS genre,games_table.studio,DATE(games_table.date) AS date,DATE(games_table.date) as premiered,games_table.year,games_table.ESRB as mpaa,games_table.rating,games_table.tags as tag,games_table.size,games_table.plot,games_table.regions AS country,games_table.lastplayed,games_table.playcount,"plugin://plugin.video.youtube/play/?video_id="||games_table.trailer as trailer,banner_paths.url||games_table.art_banner as banner,box_paths.url||games_table.art_box as poster,clearlogo_paths.url||games_table.art_logo as clearlogo,title_paths.url||games_table.art_title as landscape,snapshot_paths.url||games_table.art_snapshot as thumb,fanart_paths.url||games_table.art_fanart as fanart\n'
												'FROM games as games_table\n'
												'LEFT JOIN game_list as game_lists_table\n'
												'ON game_lists_table.label = games_table.game_list\n'
												'LEFT JOIN paths as banner_paths\n'
												'ON banner_paths."path" = games_table.art_banner_path\n'
												'LEFT JOIN paths as box_paths\n'
												'ON box_paths."path" = games_table.art_box_path\n'
												'LEFT JOIN paths as clearlogo_paths\n'
												'ON clearlogo_paths."path" = games_table.art_logo_path\n'
												'LEFT JOIN paths as title_paths\n'
												'ON title_paths."path" = games_table.art_title_path\n'
												'LEFT JOIN paths as snapshot_paths\n'
												'ON snapshot_paths."path" = games_table.art_snapshot_path\n'
												'LEFT JOIN paths as fanart_paths\n'
												'ON fanart_paths."path" = games_table.art_fanart_path\n'
												'{game_search_query}\n'
												'ORDER BY games_table.originaltitle COLLATE NOCASE ASC')
		self.database['query']['random_games'] = ('SELECT "play_game/"||games_table.uid as next_path,games_table.originaltitle AS originaltitle,{game_title_setting} as label,{game_title_setting} as title,games_table.name_search as sorttitle,games_table.system as "set",games_table.system as "tvshowtitle",games_table.genres AS genre,games_table.studio,DATE(games_table.date) AS date,DATE(games_table.date) as premiered,games_table.year,games_table.ESRB as mpaa,games_table.rating,games_table.tags as tag,games_table.size,games_table.plot,games_table.regions AS country,games_table.lastplayed,games_table.playcount,"plugin://plugin.video.youtube/play/?video_id="||games_table.trailer as trailer,banner_paths.url||games_table.art_banner as banner,box_paths.url||games_table.art_box as poster,clearlogo_paths.url||games_table.art_logo as clearlogo,title_paths.url||games_table.art_title as landscape,snapshot_paths.url||games_table.art_snapshot as thumb,fanart_paths.url||games_table.art_fanart as fanart\n'
												'FROM games as games_table\n'
												'LEFT JOIN game_list as game_lists_table\n'
												'ON game_lists_table.label = games_table.game_list\n'
												'LEFT JOIN paths as banner_paths\n'
												'ON banner_paths."path" = games_table.art_banner_path\n'
												'LEFT JOIN paths as box_paths\n'
												'ON box_paths."path" = games_table.art_box_path\n'
												'LEFT JOIN paths as clearlogo_paths\n'
												'ON clearlogo_paths."path" = games_table.art_logo_path\n'
												'LEFT JOIN paths as title_paths\n'
												'ON title_paths."path" = games_table.art_title_path\n'
												'LEFT JOIN paths as snapshot_paths\n'
												'ON snapshot_paths."path" = games_table.art_snapshot_path\n'
												'LEFT JOIN paths as fanart_paths\n'
												'ON fanart_paths."path" = games_table.art_fanart_path\n'
												'{game_search_query}\n'
												'ORDER BY RANDOM() LIMIT {num_results}')
		self.database['query']['get_playcount_and_lastplayed'] = 'SELECT playcount,lastplayed FROM games WHERE uid="{game_id}"'
		self.database['query']['update_playcount_and_lastplayed'] = 'UPDATE games SET playcount={},lastplayed="{}" WHERE uid="{}"'
		self.database['query']['update_game_list_user_parameter'] = 'UPDATE game_list set {parameter}="{new_value}" WHERE label="{game_list_id}"'
		self.database['query']['update_all_game_list_user_parameters'] = 'UPDATE game_list set {parameter}="{new_value}" WHERE label IN (SELECT label from game_list)'
		self.database['query']['update_some_game_list_user_parameters'] = 'UPDATE game_list set {parameter}="{new_value}" WHERE label IN ({game_lists})'
		self.database['query']['reset_game_list_user_parameter'] = 'UPDATE game_list set {parameter}=NULL WHERE label="{game_list_id}"'
		self.database['query']['reset_all_game_list_user_parameters'] = 'UPDATE game_list set {parameter}=NULL WHERE label IN (SELECT label from game_list)'
		self.database['query']['unhide_game_lists'] = 'UPDATE game_list set user_global_visibility=NULL WHERE {}'
		self.database['query']['uses_applauch'] = 'SELECT count(uses_applaunch) AS total FROM external_commands WHERE os = "{user_launch_os}" and uses_applaunch=1'
		self.database['query']['uses_apppause'] = 'SELECT count(uses_apppause) AS total FROM external_commands WHERE os = "{user_launch_os}" and uses_apppause=1'
		self.database['query']['get_retroarch_default_commands'] = 'SELECT * FROM external_commands WHERE os="{user_launch_os}" and is_retroarch=1 and uses_applaunch={applaunch} and uses_apppause={appause}'
		self.database['query']['get_retroarch_android'] = dict()
		self.database['query']['get_retroarch_android']['commands'] = 'SELECT display_name,corename,systemname,REPLACE(REPLACE(REPLACE((SELECT command FROM external_commands WHERE os="{}" and is_retroarch=1 LIMIT 1),"XXCORE_STEMXX",core_stem),"XXCFG_PATHXX","{}"),"XXCORE_BASE_PATHXX","{}") as command FROM core_info'
		self.database['query']['get_retroarch_android']['activities'] = 'SELECT display_name,corename,systemname,REPLACE(REPLACE(REPLACE((SELECT activity FROM external_commands WHERE os="{}" and is_retroarch=1 LIMIT 1),"XXCORE_STEMXX",core_stem),"XXCFG_PATHXX","{}"),"XXCORE_BASE_PATHXX","{}") as command FROM core_info'
		self.database['query']['get_other_emulator_commands'] = 'SELECT * FROM external_commands WHERE os="{}" and is_retroarch=0 and uses_applaunch={} and uses_apppause={}'
		self.database['query']['get_other_emulator_android'] = dict()
		self.database['query']['get_other_emulator_android']['commands'] = 'SELECT display_name,command FROM external_commands WHERE os="{}" and is_retroarch=0'
		self.database['query']['get_other_emulator_android']['activities'] = 'SELECT display_name,activity as command FROM external_commands WHERE os="{}" and is_retroarch=0'
		self.database['query']['get_db_stats'] = ('SELECT game_lists_table.label,\n'
													'CASE WHEN game_lists_table.is_1g1r_list = 1 THEN "Total Games: "||game_lists_table.total_games||" - Total 1G1R Games: "||game_lists_table.total_1g1r_games ELSE "Total Games: "||game_lists_table.total_games END as label2,\n'
													'NULL as next_path,game_lists_table.system,thumb_paths.url||game_lists_table.thumb as thumb,poster_paths.url||game_lists_table.poster as poster,banner_paths.url||game_lists_table.banner as banner,fanart_paths.url||game_lists_table.fanart_collage as fanart,clearlogo_paths.url||game_lists_table.clearlogo as clearlogo,game_lists_table.total_games,game_lists_table.is_1g1r_list,game_lists_table.total_1g1r_games\n'
													'FROM game_list as game_lists_table\n'
													'LEFT JOIN paths as thumb_paths\n'
													'ON thumb_paths."path" = game_lists_table.thumb_path\n'
													'LEFT JOIN paths as poster_paths\n'
													'ON poster_paths."path" = game_lists_table.poster_path\n'
													'LEFT JOIN paths as banner_paths\n'
													'ON banner_paths."path" = game_lists_table.banner_path\n'
													'LEFT JOIN paths as clearlogo_paths\n'
													'ON clearlogo_paths."path" = game_lists_table.clearlogo_path\n'
													'LEFT JOIN paths as fanart_paths\n'
													'ON fanart_paths."path" = game_lists_table.fanart_collage_path\n'
													'ORDER BY game_lists_table.label COLLATE NOCASE ASC') 
		self.database['query']['get_db_stats2'] = ('SELECT 1 as idx,"Unique Categories" as label, COUNT(*) as total_games\n'
													'FROM categories\n'
													'UNION\n'
													'SELECT 2 as idx,"Unique Playlists" as label, COUNT(*) as total_games\n'
													'FROM groups\n'
													'UNION\n'
													'SELECT 3 as idx,"Unique Genres" as label, COUNT(*) as total_games\n'
													'FROM genre\n'
													'UNION\n'
													'SELECT 4 as idx,"Unique Languages" as label, COUNT(*) as total_games\n'
													'FROM language\n'
													'UNION\n'
													'SELECT 5 as idx,"Unique Num Players" as label, COUNT(*) as total_games\n'
													'FROM nplayers\n'
													'UNION\n'
													'SELECT 6 as idx,"Unique Ratings" as label, COUNT(*) as total_games\n'
													'FROM rating\n'
													'UNION\n'
													'SELECT 7 as idx,"Unique Tags" as label, COUNT(*) as total_games\n'
													'FROM tag\n'
													'UNION\n'
													'SELECT 8 as idx,"Unique Codes" as label, COUNT(*) as total_games\n'
													'FROM code\n'
													'UNION\n'
													'SELECT 9 as idx,"Unique Studios" as label, COUNT(*) as total_games\n'
													'FROM studio\n'
													'UNION\n'
													'SELECT 10 as idx,"Unique Years" as label, COUNT(*) as total_games\n'
													'FROM year\n'
													'UNION\n'
													'SELECT 11 as idx,"Favorited Items" as label, COUNT(*) as total_games\n'
													'FROM favorites\n'
													'ORDER by idx')
