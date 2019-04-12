#Internet Archive Game Launcher v2.X
#Zach Morris
#https://github.com/zach-morris/plugin.program.iagl
import os, re, json, zlib, shutil, time, io
# import random
from kodi_six import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs
from contextlib import closing
from collections import defaultdict
from dateutil import parser as date_parser
from ast import literal_eval as lit_eval
import xml.etree.ElementTree as ET
import paginate
import requests
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings() #Silence uneeded warnings

try:
	from scandir import scandir
	scandir_import_success = True
except:
	xbmc.log(msg='IAGL:  Using XBMCVFS for directory size.  You suck Android.', level=xbmc.LOGDEBUG)
	scandir_import_success = False
try:
	from urllib.parse import quote_plus as url_quote
	from urllib.parse import unquote_plus as url_unquote
	from urllib.parse import urlencode as url_encode
	xbmc.log(msg='IAGL:  Using python 3 urrlib', level=xbmc.LOGDEBUG)
except:
	from urllib import quote_plus as url_quote
	from urllib import unquote_plus as url_unquote
	from urllib import urlencode as url_encode
	xbmc.log(msg='IAGL:  Using python 2 urrlib', level=xbmc.LOGDEBUG)
# try:
#     import cPickle as pickle
# except ImportError:
# 	import pickle

class iagl_utils(object):
	def __init__(self):
		self.name = 'plugin.program.iagl'
		self.handle = xbmcaddon.Addon(id='%(addon_name)s' % {'addon_name':self.name})
		self.kodi_version = xbmc.getInfoLabel('System.BuildVersion')
		try:
			junk = xbmcgui.ListItem(offscreen=True) #Is there a better way to do this?
			self.supports_offscreen = True
			xbmc.log(msg='IAGL:  Offscreen listitem supported', level=xbmc.LOGDEBUG)
			del(junk)
		except:
			self.supports_offscreen = False
			xbmc.log(msg='IAGL:  Offscreen listitem not supported', level=xbmc.LOGDEBUG)
		self.kodi_username = xbmc.getInfoLabel('System.ProfileName')
		self.listitem_date_format = '%d/%m/%Y'  #Must be length of 10
		self.display_date_format = '%x'  #Match locale date format by default
		try:
			self.gui_date_format = json.loads(xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Settings.GetSettingValue","params":{"setting":"locale.shortdateformat"}, "id": "1"}')).get('result').get('value')
			if self.gui_date_format is not None:
				if self.gui_date_format == 'regional':
					self.display_date_format = '%x'  #Match locale date format
				else: #Translate locale.shortdateformat to strftime format
					self.display_date_format = self.gui_date_format.replace('DD','%d').replace('MM','%m').replace('YYYY','%Y').replace('D','%-d').replace('M','%-m').replace('YYYY','%Y')
		except Exception as exc:
			xbmc.log(msg='IAGL:  Unable to parse Kodi GUI date format, defaulting to environment default.  Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGDEBUG)
		self.year_format = '%Y'
		self.total_arts = 10
		self.notification_time = 2000
		self.error_notification_time = 5000
		self.clean_game_tags = re.compile(r'\([^)]*\)')
		self.temp_cache_folder_name = 'temp_iagl'
		self.dat_folder_name = 'dat_files'
		self.list_cache_name = 'list_cache'
		self.addon_dat_folder_name = ['resources','data','dat_files']
		self.databases_folder_name = ['resources','data','databases']
		self.templates_folder_name = ['resources','data','templates']
		self.scripts_folder_name = ['resources','bin']
		self.media_folder_name = ['resources','skins','Default','media']
		# self.dat_file_cache_filename = 'dat_file_cache.pickle'
		self.dat_file_cache_filename = 'dat_file_cache.json'
		# self.game_history_filename = 'game_history.pickle'
		self.game_history_filename = 'game_history.json'
		self.browse_choose_filename = 'browse_database.xml'
		self.search_menu_filename = 'search_database.xml'
		self.random_menu_filename = 'random_database.xml'
		self.game_list_categories_filename = 'categories_database.xml'
		self.game_list_alphabetical_filename = 'alphabetical_database.xml'
		self.game_list_genre_filename = 'genres_database.xml'
		self.game_list_year_filename = 'years_database.xml'
		self.game_list_player_filename = 'players_database.xml'
		self.game_list_studio_filename = 'studio_database.xml'
		self.game_list_choose_filename = 'choose_database.xml'
		self.mame_softlist_db_filename = 'mame_softlist_database.xml'
		self.external_command_db_filename = ['resources','data','external_command_database.xml']
		self.favorites_template_filename = ['resources','data','templates','Favorites_Template.xml']
		self.media_type = 'video'
		self.youtube_plugin_url = 'plugin://plugin.video.youtube/play/?video_id=%(vid)s'
		self.base_image_url = 'https://i.imgur.com/'
		self.default_thumb = 'special://home/addons/plugin.program.iagl/resources/skins/Default/media/default_thumb.jpg'
		self.default_banner = 'special://home/addons/plugin.program.iagl/resources/skins/Default/media/default_banner.jpg'
		self.default_icon = 'special://home/addons/plugin.program.iagl/resources/skins/Default/media/icon.png'
		self.default_fanart = 'special://home/addons/plugin.program.iagl/fanart.jpg'
		self.label_sep = '  |  '
		self.dat_file_header_keys = ['emu_name','emu_visibility','emu_description','emu_category','emu_version','emu_date','emu_author','emu_homepage','emu_baseurl','emu_launcher','emu_default_addon','emu_ext_launch_cmd','emu_downloadpath','emu_postdlaction','emu_comment','emu_thumb','emu_banner','emu_fanart','emu_logo','emu_trailer']
		self.language = self.handle.getLocalizedString
		self.get_setting_as_bool = lambda nn: True if nn.lower()=='true' or nn.lower()=='enabled' or nn.lower()=='show' or nn.lower()=='0' else False
		self.change_search_terms_to_any = lambda nn: 'Any' if nn is None else nn
		self.flatten_list = lambda l: [item for sublist in l for item in sublist]
		self.game_label_settings = 'Title|Title, Genre|Title, Date|Title, Players|Title, Genre, Date|Title, Genre, Size|Title, Genre, Players|Title, Date, Size|Title, Date, Players|Genre, Title|Date, Title|Players, Title|Genre, Title, Date|Date, Title, Genre|Players, Title, Genre|Players, Title, Date|Title, Genre, Date, ROM Tag|Title, Genre, Date, Players|Title, Genre, Players, ROM Tag|Title, Genre, Date, Size'
		self.archive_listing_settings = 'Choose from List|Browse All Lists|Browse by Category|Search|Random Play'
		self.archive_listing_settings_routes = ['choose_from_list','all','categorized','search_menu','random_menu']
		self.archive_listing_settings_route = None
		self.game_listing_settings = 'One Big List|Choose from List|Alphabetical|Group by Genre|Group by Year|Group by Players|Group by Studio'
		self.game_listing_settings_routes = ['list_all','choose_from_list','alphabetical','list_by_genre','list_by_year','list_by_players','list_by_studio']
		self.current_game_listing_route = None
		self.items_per_page_settings = self.handle.getSetting(id='iagl_setting_items_pp')
		self.max_items_per_page = 99999
		self.number_cat = ['0','1','2','3','4','5','6','7','8','9']
		self.non_number_cat = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
		self.context_menu_items = [(self.loc_str(30400),'RunPlugin(plugin://plugin.program.iagl/context_menu/<game_list_id>/metadata)'),(self.loc_str(30402),'RunPlugin(plugin://plugin.program.iagl/context_menu/<game_list_id>/art)'),(self.loc_str(30403),'RunPlugin(plugin://plugin.program.iagl/context_menu/<game_list_id>/visibility)'),(self.loc_str(30404),'RunPlugin(plugin://plugin.program.iagl/context_menu/<game_list_id>/launcher)'),(self.loc_str(30405),'RunPlugin(plugin://plugin.program.iagl/context_menu/<game_list_id>/download_path)'),(self.loc_str(30406),'RunPlugin(plugin://plugin.program.iagl/context_menu/<game_list_id>/view_list_settings)'),(self.loc_str(30407),'RunPlugin(plugin://plugin.program.iagl/context_menu/<game_list_id>/refresh_list)')]
		self.context_menu_item_view_info = [(self.loc_str(30425),'RunPlugin(plugin://plugin.program.iagl/games_context_menu/<game_list_id>/<game_id>/view_info_page)')]
		self.context_menu_ext_launch_cmd = [(self.loc_str(30408),'RunPlugin(plugin://plugin.program.iagl/context_menu/<game_list_id>/launch_command)')]
		self.context_menu_default_addon_launch_cmd = [(self.loc_str(30409),'RunPlugin(plugin://plugin.program.iagl/context_menu/<game_list_id>/default_addon)')]
		self.context_menu_items_post_dl = [(self.loc_str(30410),'RunPlugin(plugin://plugin.program.iagl/context_menu/<game_list_id>/post_dl_command)')]
		self.post_dl_actions = ['None','UnZIP Game','UnZIP Game, Rename file','UnZIP Game, Point to Launch File','UnZIP Game to Folder, Point to Launch File','Unarchive Game','Unarchive Game, Rename file','Unarchive Game, Update file extension','Unarchive Game, Generate M3U containing CUE files','Unarchive Game, Generate M3U containing CUE files','Unarchive Game, Generate M3U containing ST files','Unarchive Game, Generate M3U containing ADF files','Create Game Folder, Generate M3U containing ADF files','Create Game Folder, Generate M3U containing D64 files','Unarchive Game, Point to BIN','Unarchive Game, Point to CUE','Unarchive Game, Point to ISO','Unarchive Game, Point to GDI','Unarchive Game, Point to ADF','Unarchive DOSBox, Point to EXE','Unarchive DOSBox, Generate Conf','Unarchive SCUMMVm, Generate Conf','Unarchive eXoDOS, Generate BAT','Unarchive WIN31, Point to BAT','Process MAME / MESS Softlist Game',]
		self.post_dl_action_keys = ['none','unzip_rom','unzip_and_rename_file','unzip_and_launch_file','unzip_to_folder_and_launch_file','unarchive_game','unarchive_game_rename_file','unarchive_game_rename_extension','unarchive_game_generate_m3u','unarchive_game_generate_m3u_cue','unarchive_game_generate_m3u_st','unarchive_game_generate_m3u_adf','save_adf_to_folder_and_launch_m3u_file','save_d64_to_folder_and_launch_m3u_file','unarchive_game_launch_bin','unarchive_game_launch_cue','unarchive_game_launch_iso','unarchive_game_launch_gdi','unarchive_game_launch_adf','unarchive_dosbox_launch_cmd','unarchive_dosbox_generate_conf','unzip_and_launch_scummvm_file','unzip_and_launch_exodos_file','unzip_and_launch_win31_file','launch_mame_softlist']
		self.context_menu_items_favorites = [(self.loc_str(30411),'RunPlugin(plugin://plugin.program.iagl/context_menu/<game_list_id>/share_favorite)')]
		self.context_menu_items_games = [(self.loc_str(30412),'RunPlugin(plugin://plugin.program.iagl/games_context_menu/<game_list_id>/<game_id>/add)')]
		self.context_menu_items_query = [(self.loc_str(30412),'RunPlugin(plugin://plugin.program.iagl/games_context_menu/query/<query_id>/add)')]
		self.context_menu_items_remove_favorite = [(self.loc_str(30413),'RunPlugin(plugin://plugin.program.iagl/games_context_menu/<game_list_id>/<game_id>/remove)')]
		self.context_menu_metadata_choices = [self.loc_str(30414),self.loc_str(30415),self.loc_str(30416),self.loc_str(30417),self.loc_str(30418),self.loc_str(30419),self.loc_str(30420)]
		self.context_menu_metadata_keys = ['emu_name','emu_category','emu_description', 'emu_comment', 'emu_trailer', 'emu_author', 'emu_date']
		self.context_menu_art_choices = [self.loc_str(30421),self.loc_str(30422),self.loc_str(30423),self.loc_str(30424)]
		self.context_menu_art_keys = ['emu_thumb', 'emu_logo', 'emu_banner', 'emu_fanart']
		self.ignore_these_game_addons = ['game.libretro','game.libretro.2048','game.libretro.dinothawr','game.libretro.mrboom']
		self.remove_these_filetypes = ['.srm','.sav','.fs','.state','.auto','.xml','.nfo']
		self.possible_linux_core_directories = ['/usr/lib/libretro','/usr/lib/x86_64-linux-gnu/libretro','/usr/lib/i386-linux-gnu/libretro','/usr/lib/s390x-linux-gnu/libretro','/usr/local/lib/libretro','~/.config/retroarch/cores','/tmp/cores','/home/kodi/bin/libretro/']
		self.default_linux_core_directory = '/usr/lib/libretro'
		self.possible_retroarch_app_locations = [os.path.join('/Applications','RetroArch.app','Contents','MacOS','RetroArch'),os.path.join('usr','bin','retroarch'),os.path.join('C:','Program Files (x86)','Retroarch','retroarch.exe'),os.path.join('opt','retropie','emulators','retroarch','bin','retroarch'),os.path.join('home','kodi','bin','retroarch')]
		self.possible_retroarch_config_locations = [os.path.join('mnt','internal_sd','Android','data','com.retroarch','files','retroarch.cfg'),os.path.join('sdcard','Android','data','com.retroarch','files','retroarch.cfg'),os.path.join('data','data','com.retroarch','retroarch.cfg'),os.path.join('data','data','com.retroarch','files','retroarch.cfg'),os.path.join('mnt','internal_sd','Android','data','com.retroarch.aarch64','files','retroarch.cfg'),os.path.join('sdcard','Android','data','com.retroarch.aarch64','files','retroarch.cfg'),os.path.join('data','user','0','com.retroarch.aarch64','retroarch.cfg'),os.path.join('data','user','0','com.retroarch.aarch64','files','retroarch.cfg')]
		self.additional_supported_external_emulators = ['APP_PATH_FS_UAE','APP_PATH_PJ64','APP_PATH_DOLPHIN','APP_PATH_MAME','APP_PATH_DEMUL','APP_PATH_EPSXE']
		self.additional_supported_external_emulator_settings = 'FS-UAE|Project 64 (Win)|Dolphin|MAME Standalone|DEMUL (Win)|ePSXe'
		self.windowid = xbmcgui.getCurrentWindowId()
		self.force_viewtype_options = [0,'50','51','52','501','502','503','504','505','53','54','55','506','56','57','58','59','66','69','95','97','507','508','509','510','511','512','513','514','515','516','517','518','519','520','521','522','523','524','525','500','583','588']
		#Define temp download cache size
		cache_options = [0,10*1e6,25*1e6,50*1e6,100*1e6,150*1e6,200*1e6,250*1e6,300*1e6,350*1e6,400*1e6,450*1e6,500*1e6,1000*1e6,2000*1e6,5000*1e6,10000*1e6,20000*1e6,32000*1e6,64000*1e6]
		cache_options_log = ['Zero (Current Game Only)','10 MB','25MB','50MB','100MB','150MB','200MB','250MB','300MB','350MB','400MB','450MB','500MB','1GB','2GB','5GB','10GB','20GB','32GB','64GB']
		try:
			self.cache_folder_size = cache_options[int(self.handle.getSetting(id='iagl_setting_dl_cache'))]
			xbmc.log(msg='IAGL:  Cache Size set to - %(current_size)s - %(current_cache_log_option)s' % {'current_size': self.cache_folder_size, 'current_cache_log_option': cache_options_log[int(self.handle.getSetting(id='iagl_setting_dl_cache'))]}, level=xbmc.LOGDEBUG)
		except ValueError:
			self.cache_folder_size = 0 #Default to 0 if not initialized correctly
			xbmc.log(msg='IAGL:  Cache Size set to is unknown - defaulting to zero', level=xbmc.LOGDEBUG)

	def loc_str(self,string_id_in):
		try:
			return self.handle.getLocalizedString(string_id_in)
		except:
			xbmc.log(msg='IAGL Error:  No translation available for %(string_id_in)s' % {'string_id_in': string_id_in}, level=xbmc.LOGERROR)
			return ''

	def initialize_IAGL_settings(self):
		if self.handle.getSetting(id='iagl_external_user_external_env') ==  'Select':  #Not yet defined, try and define for the user
			current_OS = xbmc.getInfoLabel('System.OSVersionInfo')
			xbmc.log(msg='IAGL:  OS found - %(current_OS)s' % {'current_OS': current_OS}, level=xbmc.LOGDEBUG)
			if 'OS X' in current_OS:
				self.handle.setSetting(id='iagl_external_user_external_env',value='OSX')
				xbmc.log(msg='IAGL:  External Launch Environment auto selected to OSX', level=xbmc.LOGDEBUG)
			elif 'Windows' in current_OS:
				self.handle.setSetting(id='iagl_external_user_external_env',value='Windows')
				xbmc.log(msg='IAGL:  External Launch Environment auto selected to Windows', level=xbmc.LOGDEBUG)
			elif 'Android' in current_OS:
				self.handle.setSetting(id='iagl_external_user_external_env',value='Android')
				xbmc.log(msg='IAGL:  External Launch Environment auto selected to Windows', level=xbmc.LOGDEBUG)
			elif 'Linux' in current_OS:
				self.handle.setSetting(id='iagl_external_user_external_env',value='Linux/Kodibuntu')
				xbmc.log(msg='IAGL:  External Launch Environment auto selected to Linux/Kodibuntu', level=xbmc.LOGDEBUG)				
			else:
				xbmc.log(msg='IAGL:  External Launch Environment is unknown', level=xbmc.LOGDEBUG)

		if self.handle.getSetting(id='iagl_external_user_external_env') in ['OSX','Windows','Linux/Kodibuntu']:  #External environment defined, try and find location of retroarch external app
			if len(self.handle.getSetting(id='iagl_external_path_to_retroarch'))<1:
				# possible_retroarch_app_locations = [os.path.join('/Applications','RetroArch.app','Contents','MacOS','RetroArch'),os.path.join('usr','bin','retroarch'),os.path.join('C:','Program Files (x86)','Retroarch','retroarch.exe')]
				pral_found = None
				for pral in self.possible_retroarch_app_locations:
					if xbmcvfs.exists(pral):
						self.handle.setSetting(id='iagl_external_path_to_retroarch',value=pral)
						pral_found = pral
				if pral_found is not None:
					xbmc.log(msg='IAGL:  External Retroarch location defined to %(pral_found)s' % {'pral_found': pral_found}, level=xbmc.LOGDEBUG)
				else:
					xbmc.log(msg='IAGL:  External Retroarch location is unknown', level=xbmc.LOGDEBUG)

		self.make_scripts_executable() #Attempt to chmod scripts, possibly find a way to only do this once

		# possible_retroarch_config_locations = [os.path.join('mnt','internal_sd','Android','data','com.retroarch','files','retroarch.cfg'),os.path.join('sdcard','Android','data','com.retroarch','files','retroarch.cfg'),os.path.join('data','data','com.retroarch','retroarch.cfg'),os.path.join('data','data','com.retroarch','files','retroarch.cfg')]

	def get_addon_install_path(self):
		return xbmc.translatePath(self.handle.getAddonInfo('path')).decode('utf-8')

	def get_addon_userdata_path(self):
		return xbmc.translatePath(self.handle.getAddonInfo('profile')).decode('utf-8')

	def get_temp_cache_path(self):
		current_path = os.path.join(self.get_addon_userdata_path(),self.temp_cache_folder_name)

		if not xbmcvfs.exists(os.path.join(current_path,'')):
			if not xbmcvfs.mkdir(current_path):
				xbmc.log(msg='IAGL Error:  Unable to create temp_cache_path', level=xbmc.LOGERROR)

		return current_path

	def check_temp_folder_and_clean(self):
		current_path_size = get_directory_size(self.get_temp_cache_path())
		# current_path_size = get_directory_size_xbmcvfs(self.get_temp_cache_path())
		if current_path_size > self.cache_folder_size:
			xbmc.log(msg='IAGL:  Cache directory size is %(current_path_size)s, limit is %(current_limit)s.  Clearing Cache.' % {'current_path_size': current_path_size,'current_limit': self.cache_folder_size}, level=xbmc.LOGDEBUG)
			xbmc.log(msg='IAGL:  Available free space %(free_space)s' % {'free_space': xbmc.getInfoLabel('System.FreeSpace')}, level=xbmc.LOGDEBUG)
			if not xbmcvfs.rmdir(os.path.join(self.get_temp_cache_path(),''),True):
				xbmc.log(msg='IAGL Error:  Unable to delete the temp_cache_path, attempting to use shutil', level=xbmc.LOGDEBUG)
				shutil.rmtree(self.get_temp_cache_path(), ignore_errors=True)
		else:
			xbmc.log(msg='IAGL:  Cache directory size is %(current_path_size)s' % {'current_path_size': current_path_size}, level=xbmc.LOGDEBUG)
			xbmc.log(msg='IAGL:  Available free space %(free_space)s' % {'free_space': xbmc.getInfoLabel('System.FreeSpace')}, level=xbmc.LOGDEBUG)
		self.get_temp_cache_path() #Remake folder

	def get_dat_folder_path(self):
		current_path = os.path.join(self.get_addon_userdata_path(),self.dat_folder_name)
		
		if not xbmcvfs.exists(os.path.join(current_path,'')):
			if not xbmcvfs.mkdir(current_path):
				xbmc.log(msg='IAGL Error:  Unable to create dat_folder_path', level=xbmc.LOGERROR)

		return current_path

	def get_addon_dat_folder_path(self):
		return os.path.join(self.get_addon_install_path(),*self.addon_dat_folder_name)

	def check_for_new_dat_files(self):
		dirs, files = xbmcvfs.listdir(self.get_addon_dat_folder_path())
		dat_file_cachename = os.path.join(self.get_list_cache_path(),self.dat_file_cache_filename)

		if len([x for x in files if 'xml' in x.lower()])>0:  #New dat files are in the addon folder
			current_game_lists = self.get_game_lists() #Get current userdata game lists
			new_game_lists = dict()  #Get new addon data game lists
			for kk in self.dat_file_header_keys:
				new_game_lists[kk] = list()
			new_game_lists['fullpath'] = list()
			new_game_lists['dat_filename'] = list()
			new_game_lists['dat_filesize'] = list()
			new_game_lists['total_num_archives'] = None
			for ff in [x for x in files if 'xml' in x.lower()]:
				with closing(xbmcvfs.File(os.path.join(self.get_addon_dat_folder_path(),ff))) as fo:
					byte_string = bytes(fo.readBytes(10000)) #Read first ~10kb of dat file to get header
				header_string = byte_string.decode('utf-8')
				if '</header>' in header_string:
					for kk in new_game_lists.keys():
						if kk in self.dat_file_header_keys:
							new_game_lists[kk].append(header_string.split('<%(tag)s>' % {'tag':kk})[-1].split('</%(tag)s>' % {'tag':kk})[0])
						if 'fullpath' in kk:
							new_game_lists[kk].append(os.path.join(self.get_addon_dat_folder_path(),ff))
						if 'dat_filesize' in kk:
							new_game_lists[kk].append(xbmcvfs.Stat(os.path.join(self.get_addon_dat_folder_path(),ff)).st_size())
						if 'dat_filename' in kk:
							new_game_lists[kk].append(ff.split('.')[0])			
				else:
					xbmc.log(msg='IAGL Error:  Unable to read file %(ff)s' % {'ff': ff}, level=xbmc.LOGERROR)
			new_game_lists['total_num_archives'] = len([x for x in new_game_lists['fullpath']])
			new_game_list_added = list()
			for ii, ff in enumerate([x for x in new_game_lists['fullpath']]):
				try:
					idx = current_game_lists['dat_filename'].index(new_game_lists['dat_filename'][ii])
				except:
					idx = None
				if idx is not None:  #A version of the dat file already exists in userdata
					new_game_list_added.append(False)
					current_game_list_version = current_game_lists.get('emu_version')[idx]
					new_game_list_version = new_game_lists.get('emu_version')[ii]
					if new_game_list_version == current_game_list_version:  #The version is the same, no need to update
						if xbmcvfs.delete(ff): #Current cache was deleted
							xbmc.log(msg='IAGL:  Deleting dat file %(ff)s, same version in userdata' % {'ff': ff}, level=xbmc.LOGDEBUG)
						else:
							xbmc.log(msg='IAGL:  Dat file %(ff)s could not be deleted from addon data' % {'ff': new_game_lists['dat_filename'][ii]}, level=xbmc.LOGERROR)
					else:  #New version, check if the file should be updated
						current_dialog = xbmcgui.Dialog()
						ok_ret = current_dialog.ok(self.loc_str(30322), self.loc_str(30323) % {'new_game_list_version': new_game_list_version, 'dat_filename': new_game_lists['dat_filename'][ii]})
						ret1 = current_dialog.select(self.loc_str(30324) % {'dat_filename': new_game_lists['dat_filename'][ii]}, [self.loc_str(30325),self.loc_str(30326),self.loc_str(30327)])
						del current_dialog
						if ret1>-1:
							if ret1==0: #Copy file from addon data to userdata and copy userdata settings
								if xbmcvfs.delete(current_game_lists.get('fullpath')[idx]):
									if xbmcvfs.rename(ff,current_game_lists.get('fullpath')[idx]):
										new_game_list_added.append(new_game_lists['dat_filename'][ii])
										self.delete_list_cache(new_game_lists['dat_filename'][ii])
										xbmc.log(msg='IAGL:  Dat file %(ff)s updated to new version' % {'ff': new_game_lists['dat_filename'][ii]}, level=xbmc.LOGDEBUG)
								else:
									xbmc.log(msg='IAGL:  Dat file %(ff)s was not because the original file could not be deleted' % {'ff': new_game_lists['dat_filename'][ii]}, level=xbmc.LOGERROR)
							elif ret1 == 1: #Do not update, but do not delete file in the addon folder
								xbmc.log(msg='IAGL:  Dat file %(ff)s was not updated, ask later' % {'ff': new_game_lists['dat_filename'][ii]}, level=xbmc.LOGDEBUG)
							else: #Delete the file in the addon folder
								if xbmcvfs.delete(ff): #Current cache was deleted
									xbmc.log(msg='IAGL:  Dat file %(ff)s was not updated and the file was deleted' % {'ff': new_game_lists['dat_filename'][ii]}, level=xbmc.LOGDEBUG)
								else:
									xbmc.log(msg='IAGL:  Dat file %(ff)s could not be deleted' % {'ff': new_game_lists['dat_filename'][ii]}, level=xbmc.LOGERROR)
				else: #The dat file with that name does not exist in userdata yet
					if xbmcvfs.rename(new_game_lists['fullpath'][ii],os.path.join(self.get_addon_userdata_path(),self.dat_folder_name,os.path.split(new_game_lists['fullpath'][ii])[-1])):
						xbmc.log(msg='IAGL:  Moving new dat file %(ff)s to userdata'% {'ff': new_game_lists['dat_filename'][ii]}, level=xbmc.LOGDEBUG)
						new_game_list_added.append(new_game_lists['dat_filename'][ii])
						self.delete_list_cache(new_game_lists['dat_filename'][ii])

			if len([x for x in new_game_list_added if x])>0:
				if xbmcvfs.exists(dat_file_cachename):
					xbmcvfs.delete(dat_file_cachename)
				if len([x for x in new_game_list_added if x])>2 and len(current_game_lists)>len([x for x in new_game_list_added if x]): #Only show new game list dialogs if addon is updated, do not show on initial install
					current_dialog = xbmcgui.Dialog()
					ok_ret = current_dialog.notification(self.loc_str(30328),self.loc_str(30329),xbmcgui.NOTIFICATION_INFO,self.notification_time)
					del current_dialog
				else:
					for ff in [x for x in new_game_list_added if x]:
						current_dialog = xbmcgui.Dialog()
						ok_ret = current_dialog.notification(self.loc_str(30328),self.loc_str(30330) % {'dat_filename': ff},xbmcgui.NOTIFICATION_INFO,self.notification_time)
						del current_dialog

	def make_scripts_executable(self):
	#Attempt to make addon scripts executable
		for ffiles in get_all_files_in_directory_xbmcvfs(self.get_scripts_folder_path()):
			try:
				os.chmod(ffiles, os.stat(ffiles).st_mode | 0o111)
			except Exception as exc:
				xbmc.log(msg='IAGL:  chmod failed for %(ffiles)s.  Exception %(exc)s' % {'ffiles': ffiles, 'exc': exc}, level=xbmc.LOGDEBUG)

	def get_list_cache_path(self):
		current_path = os.path.join(self.get_addon_userdata_path(),self.list_cache_name)
		if xbmcvfs.exists(os.path.join(current_path,'')) and not self.get_setting_as_bool(self.handle.getSetting(id='iagl_setting_cache_list')): #The list cache option is set to no cache
				if xbmcvfs.Stat(os.path.join(current_path,'')).st_size() > 500:  #Cache will be more than 500 bytes, so if the folder is larger than that it should be purged
					shutil.rmtree(current_path, ignore_errors=True)
					xbmc.log(msg='IAGL:  No cache option set, list_cache_path cleared', level=xbmc.LOGDEBUG)
		if not xbmcvfs.exists(os.path.join(current_path,'')):
			success = xbmcvfs.mkdir(current_path) #Create the empty directory if it doesnt exist
			if not success:
				xbmc.log(msg='IAGL Error:  Unable to create list_cache_path', level=xbmc.LOGERROR)

		return current_path

	def check_for_list_cache(self,file_crc):
		cache_exists = False
		cache_filename = None
		dirs, files = xbmcvfs.listdir(self.get_list_cache_path())
		
		if any([file_crc in x for x in files]):
			try:
				# cache_exists = True
				# cache_filename = files[[file_crc in x for x in files].index(True)]
				cache_filename = [x for x in files if file_crc in x][0]
				cache_exists = True
			except Exception as exc:
				cache_exists = False
				xbmc.log(msg='IAGL:  No cache found for file with crc %(file_crc)s.  Exception %(exc)s' % {'file_crc': file_crc, 'exc': exc}, level=xbmc.LOGDEBUG)

		return cache_exists, cache_filename

	def delete_list_cache(self,dat_filename):
		cache_exists = False
		delete_success = False
		cache_filename = None
		dirs, files = xbmcvfs.listdir(self.get_list_cache_path())
		
		if any([dat_filename in x for x in files]):
			try:
				# cache_filename = files[[dat_filename in x for x in files].index(True)]
				cache_filename = [x for x in files if dat_filename in x][0]
				cache_exists = True
			except Exception as exc:
				cache_exists = False
				xbmc.log(msg='IAGL:  No cache found for file with crc %(file_crc)s.  Exception %(exc)s' % {'file_crc': file_crc, 'exc': exc}, level=xbmc.LOGDEBUG)

		if cache_exists:
			if xbmcvfs.delete(os.path.join(self.get_list_cache_path(),cache_filename)): #Current cache was deleted
				delete_success = True
				xbmc.log(msg='IAGL:  Cache file %(cache_filename)s cleared' % {'cache_filename': cache_filename}, level=xbmc.LOGDEBUG)
			else:
				xbmc.log(msg='IAGL:  Cache file %(cache_filename)s could not be deleted' % {'cache_filename': cache_filename}, level=xbmc.LOGERROR)
		
		#Clear mem cache as well if it exists
		xbmcgui.Window(self.windowid).clearProperty('iagl_current_crc')
		xbmcgui.Window(self.windowid).clearProperty('iagl_game_list')
		
		return delete_success

	def get_list_of_favorites_lists(self):
		dirs, files = xbmcvfs.listdir(self.get_dat_folder_path())

		favorites_lists = dict()
		for kk in self.dat_file_header_keys:
			favorites_lists[kk] = list()
		favorites_lists['fullpath'] = list()
		favorites_lists['dat_filename'] = list()
		favorites_lists['dat_filesize'] = list()
		favorites_lists['total_num_archives'] = None

		for ff in [x for x in files if 'xml' in x.lower()]:
			with closing(xbmcvfs.File(os.path.join(self.get_dat_folder_path(),ff))) as fo:
				byte_string = bytes(fo.readBytes(10000)) #Read first ~10kb of dat file to get header
			header_string = byte_string.decode('utf-8')
			if '</header>' in header_string and '<!-- IAGL Favorites List -->' in header_string:
				for kk in favorites_lists.keys():
					if kk in self.dat_file_header_keys:
						favorites_lists[kk].append(header_string.split('<%(tag)s>' % {'tag':kk})[-1].split('</%(tag)s>' % {'tag':kk})[0])
					if 'fullpath' in kk:
						favorites_lists[kk].append(os.path.join(self.get_dat_folder_path(),ff))
					if 'dat_filesize' in kk:
						favorites_lists[kk].append(xbmcvfs.Stat(os.path.join(self.get_dat_folder_path(),ff)).st_size())
					if 'dat_filename' in kk:
						favorites_lists[kk].append(ff.split('.')[0])
		favorites_lists['total_num_archives'] = len([x for x in favorites_lists['fullpath']])

		return favorites_lists

	def delete_dat_file_cache(self):
		dat_file_cachename = os.path.join(self.get_list_cache_path(),self.dat_file_cache_filename) #Save the dat file listing in the list cache folder
		delete_success = xbmcvfs.delete(dat_file_cachename)
		xbmc.log(msg='IAGL:  DAT file list cache deleted', level=xbmc.LOGDEBUG)
		game_lists = self.get_game_lists() #Run the get_game_lists again but this time it will parse the available xmls
		return delete_success

	def delete_all_list_cache(self):
		dirs, files = xbmcvfs.listdir(self.get_list_cache_path())
		for ff in files:
			if not xbmcvfs.delete(os.path.join(self.get_list_cache_path(),ff)): #Current cache was deleted
				xbmc.log(msg='IAGL:  Cache file %(cache_filename)s could not be deleted' % {'cache_filename': ff}, level=xbmc.LOGERROR)

	def save_games_dict_to_cache(self,game_dict,game_list_id,current_crc32):
		# cache_filename = os.path.join(self.get_list_cache_path(),game_list_id+'_'+current_crc32+'.pickle')
		cache_filename = os.path.join(self.get_list_cache_path(),game_list_id+'_'+current_crc32+'.json')
		try:
			with open(cache_filename, 'wb') as fn:
			    # Pickle the 'data' dictionary using the highest protocol available.
			    # pickle.dump(game_dict, fn, pickle.HIGHEST_PROTOCOL)
			    json.dump(game_dict,fn)
			xbmc.log(msg='IAGL:  Saving disk cache for %(game_list_id)s, cache file %(cache_filename)s' % {'game_list_id': game_list_id, 'cache_filename': cache_filename}, level=xbmc.LOGDEBUG)
		except:
			try:
				xbmcvfs.delete(cache_filename)
			except Exception as exc: #except Exception, (exc):
				xbmc.log(msg='IAGL Error:  The disk cache file %(cache_filename)s may be corrupted. Exception %(exc)s' % {'cache_filename': cache_filename, 'exc': exc}, level=xbmc.LOGERROR)
			xbmc.log(msg='IAGL:  Unable to save disk cache for %(game_list_id)s, cache file %(cache_filename)s' % {'game_list_id': game_list_id, 'cache_filename': cache_filename}, level=xbmc.LOGERROR)

	def get_games_dict_from_cache(self,cache_filename):
		try:
			with open(os.path.join(self.get_list_cache_path(),cache_filename), 'rb') as fn:
				# return pickle.load(fn)
				return json.load(fn)
		except Exception as exc: #except Exception, (exc):
			xbmc.log(msg='IAGL Error:  The cache file %(cache_filename)s could not be loaded, it may be corrupted. Exception %(exc)s' % {'cache_filename': cache_filename, 'exc': exc}, level=xbmc.LOGERROR)

	def get_databases_folder_path(self):
		return os.path.join(self.get_addon_install_path(),*self.databases_folder_name)

	def get_templates_folder_path(self):
		return os.path.join(self.get_addon_install_path(),*self.templates_folder_name)

	def get_media_folder_path(self):
		return os.path.join(self.get_addon_install_path(),*self.media_folder_name)

	def get_scripts_folder_path(self):
		return os.path.join(self.get_addon_install_path(),*self.scripts_folder_name)

	def get_items_per_page(self):
		items_per_page = self.max_items_per_page
		try:
			items_per_page = int(self.items_per_page_settings.strip())
		except:
			pass
		return items_per_page

	def get_next_page_listitem(self,current_page,page_count,next_page,total_items):
		next_page_listitem = None
		if current_page < page_count:
			li = {'info': {'genre' : '\xc2\xa0',
			'date' : '01/01/2999',
			'plot' : 'Page %(current_page)s of %(page_count)s.  Next page is %(next_page)s.  Total of %(total_items)s games in this archive.' % {'current_page': current_page, 'page_count': page_count, 'next_page': next_page, 'total_items': total_items},
			},
			'art': {'icon' : os.path.join(self.get_media_folder_path(),'Next.png'),
			'thumb' : os.path.join(self.get_media_folder_path(),'Next.png'),
			},}
			# next_page_listitem = xbmcgui.ListItem('\xc2\xa0Next >>', offscreen=True)
			next_page_listitem = self.create_kodi_listitem('\xc2\xa0Next >>',None)
			next_page_listitem.setInfo(self.media_type,li['info'])
			next_page_listitem.setArt(li['art'])
		return next_page_listitem

	def get_game_history_listitem(self):
		game_history_listitem = None
		li = {'info': {'genre' : 'History',
		'date' : '01/01/2999',
		'plot' : 'View the games you have previously played.',
		},
		'art': {'icon' : os.path.join(self.get_media_folder_path(),'icon.png'),
		'thumb' : os.path.join(self.get_media_folder_path(),'last_played.jpg'),
		'poster' : os.path.join(self.get_media_folder_path(),'last_played.jpg'),
		'banner' : os.path.join(self.get_media_folder_path(),'last_played_banner.jpg'),
		'fanart' : os.path.join(self.get_media_folder_path(),'fanart.jpg'),
		},}
		# game_history_listitem = xbmcgui.ListItem('Last Played', offscreen=True)
		game_history_listitem = self.create_kodi_listitem('Last Played')
		game_history_listitem.setInfo(self.media_type,li['info'])
		game_history_listitem.setArt(li['art'])
		return game_history_listitem

	def get_search_query_listitem(self,label_in,current_query):
		search_query_listitem = None
		if type(self.change_search_terms_to_any(current_query['lists'])) is list:
			current_lists = '[CR]     '+'[CR]     '.join(self.change_search_terms_to_any(current_query['lists']))
		else:
			current_lists = self.change_search_terms_to_any(current_query['lists'])
		if type(self.change_search_terms_to_any(current_query['genre'])) is list:
			current_genres = '[CR]     '+'[CR]     '.join(self.change_search_terms_to_any(current_query['genre']))
		else:
			current_genres = self.change_search_terms_to_any(current_query['genre'])
		if type(self.change_search_terms_to_any(current_query['nplayers'])) is list:
			current_nplayers = '[CR]     '+'[CR]     '.join(self.change_search_terms_to_any(current_query['nplayers']))
		else:
			current_nplayers = self.change_search_terms_to_any(current_query['nplayers'])	
		if type(self.change_search_terms_to_any(current_query['year'])) is list:
			current_years = '[CR]     '+'[CR]     '.join(self.change_search_terms_to_any(current_query['year']))
		else:
			current_years = self.change_search_terms_to_any(current_query['year'])	
		if type(self.change_search_terms_to_any(current_query['studio'])) is list:
			current_studios = '[CR]     '+'[CR]     '.join(self.change_search_terms_to_any(current_query['studio']))
		else:
			current_studios = self.change_search_terms_to_any(current_query['studio'])		
		current_plot = '[B]Current Query[/B][CR]Search Title: '+self.change_search_terms_to_any(current_query['title'])+'[CR]Search Lists: '+current_lists+'[CR]Search Genres: '+current_genres+'[CR]Search Players: '+current_nplayers+'[CR]Search Years: '+current_years+'[CR]Search Studios: '+current_studios+'[CR]Search Tags: '+self.change_search_terms_to_any(current_query['tag'])+'[CR]'
		#Generate json for IAGL favorites
		json_item = dict()
		json_item['game'] = dict()
		json_item['game']['@name'] = label_in
		json_item['game']['description'] = label_in
		json_item['game']['rom'] = dict()
		json_item['game']['rom']['@name'] = self.get_query_as_url(current_query)
		json_item['game']['genre'] = 'Search'
		json_item['game']['plot'] = current_plot
		json_item['game']['boxart1'] = self.default_thumb
		json_item['game']['banner1'] = self.default_banner
		json_item['game']['fanart1'] = self.default_fanart
		li = {'info': {'genre' : 'Search',
		'date' : '01/01/2999',
		'plot' : current_plot,
		},
		'art': {'icon' : self.default_icon,
		'thumb' : self.default_thumb,
		'poster' : self.default_thumb,
		'banner' : self.default_banner,
		'fanart' : self.default_fanart,
		},
		'properties': {'iagl_json' : json.dumps(json_item),
		},
		}
		search_query_listitem = self.create_kodi_listitem(label_in)
		search_query_listitem.setInfo(self.media_type,li['info'])
		search_query_listitem.setArt(li['art'])
		#https://forum.kodi.tv/showthread.php?tid=332283
		for kk in li['properties'].keys():
			search_query_listitem.setProperty(kk,li['properties'][kk])
		search_query_listitem = self.add_query_context_menus(search_query_listitem,'search')
		return search_query_listitem

	def get_random_query_listitem(self,label_in,current_query):
		random_query_listitem = None
		if current_query['title'] is None:
			current_num_results = '1'
		else:
			current_num_results = str(current_query['title'])
		if type(self.change_search_terms_to_any(current_query['lists'])) is list:
			current_lists = '[CR]     '+'[CR]     '.join(self.change_search_terms_to_any(current_query['lists']))
		else:
			current_lists = self.change_search_terms_to_any(current_query['lists'])
		if type(self.change_search_terms_to_any(current_query['genre'])) is list:
			current_genres = '[CR]     '+'[CR]     '.join(self.change_search_terms_to_any(current_query['genre']))
		else:
			current_genres = self.change_search_terms_to_any(current_query['genre'])
		if type(self.change_search_terms_to_any(current_query['nplayers'])) is list:
			current_nplayers = '[CR]     '+'[CR]     '.join(self.change_search_terms_to_any(current_query['nplayers']))
		else:
			current_nplayers = self.change_search_terms_to_any(current_query['nplayers'])	
		if type(self.change_search_terms_to_any(current_query['year'])) is list:
			current_years = '[CR]     '+'[CR]     '.join(self.change_search_terms_to_any(current_query['year']))
		else:
			current_years = self.change_search_terms_to_any(current_query['year'])	
		if type(self.change_search_terms_to_any(current_query['studio'])) is list:
			current_studios = '[CR]     '+'[CR]     '.join(self.change_search_terms_to_any(current_query['studio']))
		else:
			current_studios = self.change_search_terms_to_any(current_query['studio'])		
		current_plot = '[B]Random Play[/B][CR]Num of Results: '+current_num_results+'[CR]Search Lists: '+current_lists+'[CR]Search Genres: '+current_genres+'[CR]Search Players: '+current_nplayers+'[CR]Search Years: '+current_years+'[CR]Search Studios: '+current_studios+'[CR]Search Tags: '+self.change_search_terms_to_any(current_query['tag'])+'[CR]'
		#Generate json for IAGL favorites
		json_item = dict()
		json_item['game'] = dict()
		json_item['game']['@name'] = label_in
		json_item['game']['description'] = label_in
		json_item['game']['rom'] = dict()
		json_item['game']['rom']['@name'] = self.get_query_as_url(current_query)
		json_item['game']['genre'] = 'Random'
		json_item['game']['plot'] = current_plot
		json_item['game']['boxart1'] = self.default_thumb
		json_item['game']['banner1'] = self.default_banner
		json_item['game']['fanart1'] = self.default_fanart
		li = {'info': {'genre' : 'Random',
		'date' : '01/01/2999',
		'plot' : current_plot,
		},
		'art': {'icon' : self.default_icon,
		'thumb' : self.default_thumb,
		'poster' : self.default_thumb,
		'banner' : self.default_banner,
		'fanart' : self.default_fanart,
		},
		'properties': {'iagl_json' : json.dumps(json_item),
		},
		}
		random_query_listitem = self.create_kodi_listitem(label_in)
		random_query_listitem.setInfo(self.media_type,li['info'])
		random_query_listitem.setArt(li['art'])
		for kk in li['properties'].keys():
			random_query_listitem.setProperty(kk,li['properties'][kk])
		random_query_listitem = self.add_query_context_menus(random_query_listitem,'random')
		return random_query_listitem

	def get_game_list_categories_file(self):
		return os.path.join(self.get_databases_folder_path(),self.game_list_categories_filename)

	def get_game_list_alphabetical_file(self):
		return os.path.join(self.get_databases_folder_path(),self.game_list_alphabetical_filename)

	def get_game_list_genre_file(self):
		return os.path.join(self.get_databases_folder_path(),self.game_list_genre_filename)

	def get_game_list_year_file(self):
		return os.path.join(self.get_databases_folder_path(),self.game_list_year_filename)

	def get_game_list_player_file(self):
		return os.path.join(self.get_databases_folder_path(),self.game_list_player_filename)

	def get_game_list_studio_file(self):
		return os.path.join(self.get_databases_folder_path(),self.game_list_studio_filename)

	def get_game_list_choose_file(self):
		return os.path.join(self.get_databases_folder_path(),self.game_list_choose_filename)

	def get_browse_choose_file(self):
		return os.path.join(self.get_databases_folder_path(),self.browse_choose_filename)

	def get_search_menu_file(self):
		return os.path.join(self.get_databases_folder_path(),self.search_menu_filename)

	def get_random_menu_file(self):
		return os.path.join(self.get_databases_folder_path(),self.random_menu_filename)

	def get_external_command_db_file(self):
		return os.path.join(self.get_addon_install_path(),*self.external_command_db_filename)

	def get_favorites_template_file(self):
		return os.path.join(self.get_addon_install_path(),*self.favorites_template_filename)

	def get_mame_softlist_db_file(self):
		return os.path.join(self.get_databases_folder_path(),self.mame_softlist_db_filename)

	def get_game_lists(self):
		cache_list_option = self.get_setting_as_bool(self.handle.getSetting(id='iagl_setting_cache_list'))
		dirs, files = xbmcvfs.listdir(self.get_dat_folder_path())
		files = list(sorted(files)) #Sort the list of files
		dat_file_cachename = os.path.join(self.get_list_cache_path(),self.dat_file_cache_filename) #Save the dat file listing in the list cache folder
		game_lists = None

		if cache_list_option and xbmcvfs.exists(dat_file_cachename):
			try:
				with open(dat_file_cachename, 'rb') as fn:
					# game_lists = pickle.load(fn)
					game_lists = json.load(fn)
					xbmc.log(msg='IAGL:  DAT file list cache found, cache file %(dat_file_cachename)s' % {'dat_file_cachename': dat_file_cachename}, level=xbmc.LOGDEBUG)
				if len([x for x in files if 'xml' in x.lower() and os.path.splitext(x)[0] not in game_lists['dat_filename']])>0 or len([x for x in files if 'xml' in x.lower()]) != game_lists['total_num_archives']:
					try:
						self.delete_dat_file_cache()
					except Exception as exc: #except Exception, (exc):
						xbmc.log(msg='IAGL Error:  The disk cache file %(dat_file_cachename)s may be corrupted. Exception %(exc)s' % {'dat_file_cachename': dat_file_cachename, 'exc': exc}, level=xbmc.LOGERROR)
			except Exception as exc: #except Exception, (exc):
				xbmc.log(msg='IAGL Error:  The cache file %(dat_file_cachename)s could not be loaded, it may be corrupted. Exception %(exc)s' % {'dat_file_cachename': dat_file_cachename, 'exc': exc}, level=xbmc.LOGERROR)
		else:
			game_lists = dict()
			for kk in self.dat_file_header_keys:
				game_lists[kk] = list()
			game_lists['fullpath'] = list()
			game_lists['dat_filename'] = list()
			game_lists['dat_filesize'] = list()
			game_lists['total_num_archives'] = None

			for ff in [x for x in files if 'xml' in x.lower()]:
				with closing(xbmcvfs.File(os.path.join(self.get_dat_folder_path(),ff))) as fo:
					byte_string = bytes(fo.readBytes(10000)) #Read first ~10kb of dat file to get header
				header_string = byte_string.decode('utf-8')
				if '</header>' in header_string:
					for kk in game_lists.keys():
						if kk in self.dat_file_header_keys:
							game_lists[kk].append(header_string.split('<%(tag)s>' % {'tag':kk})[-1].split('</%(tag)s>' % {'tag':kk})[0])
						if 'fullpath' in kk:
							game_lists[kk].append(os.path.join(self.get_dat_folder_path(),ff))
						if 'dat_filesize' in kk:
							game_lists[kk].append(xbmcvfs.Stat(os.path.join(self.get_dat_folder_path(),ff)).st_size())
						if 'dat_filename' in kk:
							game_lists[kk].append(ff.split('.')[0])
						# if 'dat_crc32' in kk:
							# game_lists[kk].append(get_crc32(os.path.join(self.get_dat_folder_path(),ff)))
				else:
					xbmc.log(msg='IAGL Error:  Unable to read file %(ff)s' % {'ff': ff}, level=xbmc.LOGERROR)
			game_lists['total_num_archives'] = len([x for x in game_lists['fullpath']])

			if cache_list_option:
				try:
					with open(dat_file_cachename, 'wb') as fn:
					    json.dump(game_lists,fn)
					xbmc.log(msg='IAGL:  Saving dat file listing to cache in cache file %(dat_file_cachename)s' % {'dat_file_cachename': dat_file_cachename}, level=xbmc.LOGDEBUG)
				except:
					try:
						xbmcvfs.delete(dat_file_cachename)
					except Exception as exc:
						xbmc.log(msg='IAGL:  Unable to save dat file listing to cache in cache file %(dat_file_cachename)s.  Exception %(exc)s' % {'dat_file_cachename': dat_file_cachename, 'exc': exc}, level=xbmc.LOGERROR)

		return game_lists

	def get_game_lists_as_listitems(self,return_categories=None):
		game_listitems = list()
		game_lists_dict = self.get_game_lists()
		#Ensure the return categories object is a list so it can be iterated on
		if type(return_categories) is str:
			return_cats = [return_categories]
		else:
			return_cats = return_categories

		for aa in range(0,game_lists_dict['total_num_archives']):
			li = {'values': {'label' : game_lists_dict.get('emu_name')[aa],
				'label2' : game_lists_dict.get('emu_description')[aa],
				},
				'info': {'originaltitle' : game_lists_dict['emu_name'][aa],
				'date' : self.get_date(game_lists_dict.get('emu_date')[aa]),
				'credits' : game_lists_dict.get('emu_author')[aa],
				'plot' : game_lists_dict.get('emu_comment')[aa],
				'trailer' : self.get_trailer(game_lists_dict.get('emu_trailer')[aa]),
				'size' : game_lists_dict.get('dat_filesize')[aa]
				},
				'art': {'poster' : self.choose_image(game_lists_dict.get('emu_thumb')[aa],self.default_thumb,None),
				'banner' : self.choose_image(game_lists_dict.get('emu_banner')[aa],self.default_banner,None),
				'fanart' : self.choose_image(game_lists_dict.get('emu_fanart')[aa],self.default_thumb,None),
				'clearlogo' : self.choose_image(game_lists_dict.get('emu_logo')[aa],None,None),
				'icon' : self.choose_image(game_lists_dict.get('emu_logo')[aa],None,None),
				'thumb' : self.choose_image(game_lists_dict.get('emu_thumb')[aa],self.default_thumb,None),
				},
				'properties': {'emu_visibility' : game_lists_dict.get('emu_visibility')[aa],
				'emu_category' : game_lists_dict.get('emu_category')[aa],
				'emu_description' : game_lists_dict.get('emu_description')[aa],
				'emu_version' : game_lists_dict.get('emu_version')[aa],
				'emu_date' : game_lists_dict.get('emu_date')[aa],
				'emu_baseurl' : game_lists_dict.get('emu_baseurl')[aa],
				'emu_launcher' : game_lists_dict.get('emu_launcher')[aa],
				'emu_ext_launch_cmd' : game_lists_dict.get('emu_ext_launch_cmd')[aa],
				'emu_default_addon' : game_lists_dict.get('emu_default_addon')[aa],
				'emu_downloadpath' : game_lists_dict.get('emu_downloadpath')[aa],
				'emu_comment' : game_lists_dict.get('emu_comment')[aa],
				'emu_author' : game_lists_dict.get('emu_author')[aa],
				'dat_filename' : game_lists_dict.get('dat_filename')[aa],
				'fullpath' : game_lists_dict.get('fullpath')[aa],
				},
				}
			# game_listitems.append(xbmcgui.ListItem(label=li['values']['label'],label2=li['values']['label2'], offscreen=True))
			game_listitems.append(self.create_kodi_listitem(li['values']['label'],li['values']['label2']))
			game_listitems[-1].setInfo(self.media_type,li['info'])
			game_listitems[-1].setArt(li['art'])
			#https://forum.kodi.tv/showthread.php?tid=332283
			for kk in li['properties'].keys():
				game_listitems[-1].setProperty(kk,li['properties'][kk])

			if return_cats is not None: #Remove any game lists not in the categories requested
				if len(set([x.strip() for x in game_lists_dict['emu_category'][aa].split(',')]).intersection(return_cats)) < 1:
					del(game_listitems[-1])

		if return_categories is not None:
			xbmc.log(msg='IAGL:  Returning %(num_lists)s game lists in categories %(game_cats)s' % {'num_lists':str(len(game_listitems)),'game_cats': ', '.join(return_cats)}, level=xbmc.LOGDEBUG)
		else:
			xbmc.log(msg='IAGL:  Returning %(num_lists)s (all) available game lists' % {'num_lists':str(len(game_listitems))}, level=xbmc.LOGDEBUG)

		return game_listitems

	def get_game_lists_categories(self):
		try:
			return etree_to_dict(ET.parse(self.get_game_list_categories_file()).getroot()) #No cache for this currently, since its small
		except Exception as exc: #except Exception, (exc):
			xbmc.log(msg='IAGL:  There was an error parsing the categories xml file, Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
			return None

	def get_alphabetical_game_listing(self):
		try:
			return etree_to_dict(ET.parse(self.get_game_list_alphabetical_file()).getroot()) #No cache for this currently, since its small
		except Exception as exc: #except Exception, (exc):
			xbmc.log(msg='IAGL:  There was an error parsing the alphabetical xml file, Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
			return None

	def get_genre_game_listing(self):
		try:
			return etree_to_dict(ET.parse(self.get_game_list_genre_file()).getroot()) #No cache for this currently, since its small
		except Exception as exc: #except Exception, (exc):
			xbmc.log(msg='IAGL:  There was an error parsing the genre xml file, Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
			return None

	def get_year_game_listing(self):
		try:
			return etree_to_dict(ET.parse(self.get_game_list_year_file()).getroot()) #No cache for this currently, since its small
		except Exception as exc: #except Exception, (exc):
			xbmc.log(msg='IAGL:  There was an error parsing the year xml file, Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
			return None

	def get_player_game_listing(self):
		try:
			return etree_to_dict(ET.parse(self.get_game_list_player_file()).getroot()) #No cache for this currently, since its small
		except Exception as exc: #except Exception, (exc):
			xbmc.log(msg='IAGL:  There was an error parsing the player xml file, Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
			return None

	def get_studio_game_listing(self):
		try:
			return etree_to_dict(ET.parse(self.get_game_list_studio_file()).getroot()) #No cache for this currently, since its small
		except Exception as exc: #except Exception, (exc):
			xbmc.log(msg='IAGL:  There was an error parsing the studio xml file, Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
			return None

	def get_choose_game_listing(self):
		try:
			return etree_to_dict(ET.parse(self.get_game_list_choose_file()).getroot()) #No cache for this currently, since its small
		except Exception as exc: #except Exception, (exc):
			xbmc.log(msg='IAGL:  There was an error parsing the choose xml file, Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
			return None

	def get_browse_listing(self):
		try:
			return etree_to_dict(ET.parse(self.get_browse_choose_file()).getroot()) #No cache for this currently, since its small
		except Exception as exc: #except Exception, (exc):
			xbmc.log(msg='IAGL:  There was an error parsing the browse xml file, Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
			return None

	def get_search_listing(self):
		try:
			return etree_to_dict(ET.parse(self.get_search_menu_file()).getroot()) #No cache for this currently, since its small
		except Exception as exc: #except Exception, (exc):
			xbmc.log(msg='IAGL:  There was an error parsing the search menu xml file, Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
			return None

	def get_random_listing(self):
		try:
			return etree_to_dict(ET.parse(self.get_random_menu_file()).getroot()) #No cache for this currently, since its small
		except Exception as exc: #except Exception, (exc):
			xbmc.log(msg='IAGL:  There was an error parsing the random menu xml file, Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
			return None

	def get_external_command_listing(self):
		try:
			return etree_to_dict(ET.parse(self.get_external_command_db_file()).getroot()) #No cache for this currently, since its small
		except Exception as exc: #except Exception, (exc):
			xbmc.log(msg='IAGL:  There was an error parsing the external command xml file, Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
			return None

	def get_mame_softlist_listing(self):
		try:
			return etree_to_dict(ET.parse(self.get_mame_softlist_db_file()).getroot()) #No cache for this currently, since its small
		except Exception as exc: #except Exception, (exc):
			xbmc.log(msg='IAGL:  There was an error parsing the mame softlist xml file, Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
			return None


	def get_game_list_categories_as_listitems(self):
		game_list_category_listitems = list()
		game_lists_dict = self.get_game_lists()
		game_lists_categories_dict = self.get_game_lists_categories()
		current_categories = sorted(list(set([y.strip() for y in self.flatten_list([x.split(',') for x in game_lists_dict['emu_category']]) if len(y)>0])))

		for aa, cats in enumerate(current_categories):
			try: #Find the current categories in the category database
				idx = [x['label'] for x in game_lists_categories_dict['categories']['category']].index(cats)
			except:
				try: #If the category is not present in the database, use the default info
					idx = [x['label'] for x in game_lists_categories_dict['categories']['category']].index('default')
					xbmc.log(msg='IAGL:  The category %(cats)s was not found, using IAGL default info for that item' % {'cats': cats}, level=xbmc.LOGDEBUG)
					default_idx = idx
				except:
					idx = None
			if idx is not None: #Fill in listitem parameters
				li = {'values': {'label' : cats,
				},
				'info': {'title' : cats,
				'plot' : game_lists_categories_dict['categories']['category'][idx].get('plot'),
				'trailer' : self.get_trailer(game_lists_categories_dict['categories']['category'][idx].get('trailer')),
				},
				'art': {'poster' : self.choose_image(game_lists_categories_dict['categories']['category'][idx].get('thumb'),self.default_thumb,None),
				'banner' : self.choose_image(game_lists_categories_dict['categories']['category'][idx].get('banner'),self.default_banner,None),
				'fanart' : self.choose_image(game_lists_categories_dict['categories']['category'][idx].get('fanart'),self.default_fanart,None),
				'clearlogo' : self.choose_image(game_lists_categories_dict['categories']['category'][idx].get('logo'),self.default_icon,None),
				'icon' : self.choose_image(game_lists_categories_dict['categories']['category'][idx].get('logo'),self.default_icon,None),
				'thumb' : self.choose_image(game_lists_categories_dict['categories']['category'][idx].get('thumb'),self.default_thumb,None),
				},
				}
				# game_list_category_listitems.append(xbmcgui.ListItem(label=li['values']['label'], offscreen=True))
				game_list_category_listitems.append(self.create_kodi_listitem(li['values']['label']))
				game_list_category_listitems[-1].setInfo(self.media_type,li['info'])
				game_list_category_listitems[-1].setArt(li['art'])
			else:
				xbmc.log(msg='IAGL Error:  An error occured and %(cats)s could not be displayed' % {'cats': cats}, level=xbmc.LOGERROR)

		return game_list_category_listitems

	def get_alphabetical_as_listitem(self, game_list_id):
		alphabetical_listitems = list()
		games_dict = self.get_games(game_list_id)
		alphabetical_dict = self.get_alphabetical_game_listing()
		current_game_letters = [x['values']['label2'][0].upper() for x in games_dict]
		alpha_dict_labels = [x['label'] for x in alphabetical_dict['categories']['category']]

		for cats in sorted(list(set(current_game_letters))):
			try: #Find the current letter in the alphabetical database
				if cats not in self.non_number_cat: #Anything that doesnt start with a letter will be put into the numerical category
					idx = alpha_dict_labels.index('#')
				else:
					idx = alpha_dict_labels.index(cats)
			except:
				try: #If the letter is not present in the database, use the default info
					idx = alpha_dict_labels.index('default')
					xbmc.log(msg='IAGL:  The letter %(cats)s was not found, using IAGL default info for that item' % {'cats': cats}, level=xbmc.LOGDEBUG)
					default_idx = idx
				except:
					idx = None
			if idx is not None: #Fill in listitem parameters
				if cats not in self.non_number_cat:
					total_starting_with_current_letter = len(current_game_letters)-sum(self.flatten_list([[w.startswith(x) for x in self.non_number_cat] for w in current_game_letters]))
					total_starting_with_current_letter_label = '#    ('+str(total_starting_with_current_letter)+')'
					total_starting_with_current_letter_label2 = '#'
				else:
					total_starting_with_current_letter = sum([w.startswith(cats) for w in current_game_letters])
					total_starting_with_current_letter_label = cats+'    ('+str(total_starting_with_current_letter)+')'
					total_starting_with_current_letter_label2 = cats
				current_trailer = self.get_trailer(alphabetical_dict['categories']['category'][idx].get('trailer'))
				li = {'values': {'label' : total_starting_with_current_letter_label,
						'label2' : total_starting_with_current_letter_label2,
						},
						'info': {'originaltitle' : total_starting_with_current_letter_label2,
						'title' : total_starting_with_current_letter_label,
						'plot' : alphabetical_dict['categories']['category'][idx]['plot'],
						'trailer' : current_trailer,
						},
						'art': {'poster' : self.choose_image(alphabetical_dict['categories']['category'][idx]['thumb'],self.default_thumb,None),
						'banner' : self.choose_image(alphabetical_dict['categories']['category'][idx]['banner'],self.default_banner,None),
						'fanart' : self.choose_image(alphabetical_dict['categories']['category'][idx]['fanart'],self.default_fanart,None),
						'clearlogo' : self.choose_image(alphabetical_dict['categories']['category'][idx]['logo'],None,None),
						'icon' : self.choose_image(alphabetical_dict['categories']['category'][idx]['logo'],None,None),
						'thumb' : self.choose_image(alphabetical_dict['categories']['category'][idx]['thumb'],self.default_thumb,None),
						},
						}
				# alphabetical_listitems.append(xbmcgui.ListItem(label=li['values']['label'],label2=li['values']['label2'], offscreen=True))
				alphabetical_listitems.append(self.create_kodi_listitem(li['values']['label'],li['values']['label2']))
				alphabetical_listitems[-1].setInfo(self.media_type,li['info'])
				alphabetical_listitems[-1].setArt(li['art'])
			else:
				xbmc.log(msg='IAGL Error:  An error occured and %(cats)s could not be displayed' % {'cats': cats}, level=xbmc.LOGERROR)

		for ii in reversed(range(1,len(alphabetical_listitems))):  #Remove duplicates for number category, quick and dirty currently
			if alphabetical_listitems[ii].getLabel() == alphabetical_listitems[ii-1].getLabel():
				alphabetical_listitems.pop(ii)

		return alphabetical_listitems

	def get_genres_from_game_lists(self, game_lists):
		genre_list_temp = list()
		genre_list_sorted = list()
		if game_lists is None: #Use all lists is the query is for None
			game_lists = [x for x in self.get_game_lists().get('dat_filename')]
		for game_list_id in game_lists:
			current_games_dict = self.get_games(game_list_id)
			current_game_genres = [y.strip().lower() for y in self.flatten_list([x.get('info').get('genre').split(',') for x in current_games_dict if x.get('info').get('genre') is not None]) if len(y)>0]
			current_game_genres_unknown = [x.get('info').get('genre') for x in current_games_dict if x.get('info').get('genre') is None]
			current_game_genres_sorted = sorted(list(set([y.strip() for y in self.flatten_list([x.get('info').get('genre').split(',') for x in current_games_dict if x.get('info').get('genre') is not None]) if len(y)>0])))
			if len(current_game_genres_unknown)>0:
				current_game_genres_sorted.append('Unknown')
			genre_list_temp = genre_list_temp+current_game_genres_sorted
		genre_list_sorted = sorted(list(set(genre_list_temp)))
		return genre_list_sorted

	def get_game_list_genres_as_listitems(self, game_list_id):
		genre_listitems = list()
		games_dict = self.get_games(game_list_id)
		genre_dict = self.get_genre_game_listing()
		current_game_genres = [y.strip().lower() for y in self.flatten_list([x.get('info').get('genre').split(',') for x in games_dict if x.get('info').get('genre') is not None]) if len(y)>0]
		current_game_genres_unknown = [x.get('info').get('genre') for x in games_dict if x.get('info').get('genre') is None]
		current_game_genres_sorted = sorted(list(set([y.strip() for y in self.flatten_list([x.get('info').get('genre').split(',') for x in games_dict if x.get('info').get('genre') is not None]) if len(y)>0])))
		if len(current_game_genres_unknown)>0:
			current_game_genres_sorted.append('Unknown')
		genre_dict_labels = [x['label'] for x in genre_dict['categories']['category']]

		for cats in current_game_genres_sorted:
			try: #Find the current letter in the alphabetical database
				idx = genre_dict_labels.index(cats)
			except:
				try: #If the letter is not present in the database, use the default info
					idx = genre_dict_labels.index('default')
					xbmc.log(msg='IAGL:  The genre %(cats)s was not found, using IAGL default info for that item' % {'cats': cats}, level=xbmc.LOGDEBUG)
					default_idx = idx
				except:
					idx = None
			if idx is not None: #Fill in listitem parameters
				if idx == genre_dict_labels.index('Unknown'):
					total_in_current_genre = len(current_game_genres_unknown)
				else:
					total_in_current_genre = current_game_genres.count(cats.lower())
				total_in_current_genre_label = cats+'    ('+str(total_in_current_genre)+')'
				total_in_current_genre_label2 = cats
				current_trailer = self.get_trailer(genre_dict['categories']['category'][idx].get('trailer'))
				li = {'values': {'label' : total_in_current_genre_label,
						'label2' : total_in_current_genre_label2,
						},
						'info': {'originaltitle' : total_in_current_genre_label2,
						'title' : total_in_current_genre_label,
						'plot' : genre_dict['categories']['category'][idx]['plot'],
						'trailer' : current_trailer,
						},
						'art': {'poster' : self.choose_image(genre_dict['categories']['category'][idx]['thumb'],self.default_thumb,None),
						'banner' : self.choose_image(genre_dict['categories']['category'][idx]['banner'],self.default_banner,None),
						'fanart' : self.choose_image(genre_dict['categories']['category'][idx]['fanart'],self.default_fanart,None),
						'clearlogo' : self.choose_image(genre_dict['categories']['category'][idx]['logo'],None,None),
						'icon' : self.choose_image(genre_dict['categories']['category'][idx]['logo'],None,None),
						'thumb' : self.choose_image(genre_dict['categories']['category'][idx]['thumb'],self.default_thumb,None),
						},
						}
				# genre_listitems.append(xbmcgui.ListItem(label=li['values']['label'],label2=li['values']['label2'], offscreen=True))
				genre_listitems.append(self.create_kodi_listitem(li['values']['label'],li['values']['label2']))
				genre_listitems[-1].setInfo(self.media_type,li['info'])
				genre_listitems[-1].setArt(li['art'])
			else:
				xbmc.log(msg='IAGL Error:  An error occured and genre %(cats)s could not be displayed' % {'cats': cats}, level=xbmc.LOGERROR)

		return genre_listitems

	def get_years_from_game_lists(self, game_lists):
		year_list_temp = list()
		year_list_sorted = list()
		if game_lists is None: #Use all lists is the query is for None
			game_lists = [x for x in self.get_game_lists().get('dat_filename')]
		for game_list_id in game_lists:
			current_games_dict = self.get_games(game_list_id)
			current_game_years = [str(y).strip().lower() for y in [x.get('info').get('year') for x in current_games_dict if x.get('info').get('year') is not None] if len(y)>0]
			current_game_years_unknown = [x.get('info').get('year') for x in current_games_dict if x.get('info').get('year') is None]
			current_game_years_sorted = sorted(list(set([str(y).strip() for y in [x.get('info').get('year') for x in current_games_dict if x.get('info').get('year') is not None] if len(y)>0])))
			if len(current_game_years_unknown)>0:
				current_game_years_sorted.append('Unknown')
			year_list_temp = year_list_temp+current_game_years_sorted
		year_list_sorted = sorted(list(set(year_list_temp)))
		return year_list_sorted

	def get_game_list_years_as_listitems(self, game_list_id):
		year_listitems = list()
		games_dict = self.get_games(game_list_id)
		year_dict = self.get_year_game_listing()
		current_game_years = [str(y).strip().lower() for y in [x.get('info').get('year') for x in games_dict if x.get('info').get('year') is not None] if len(y)>0]
		current_game_years_unknown = [x.get('info').get('year') for x in games_dict if x.get('info').get('year') is None]
		current_game_years_sorted = sorted(list(set([str(y).strip() for y in [x.get('info').get('year') for x in games_dict if x.get('info').get('year') is not None] if len(y)>0])))
		if len(current_game_years_unknown)>0:
			current_game_years_sorted.append('Unknown')
		year_dict_labels = [x['label'] for x in year_dict['categories']['category']]

		for cats in current_game_years_sorted:
			try: #Find the current letter in the alphabetical database
				idx = year_dict_labels.index(cats)
			except:
				try: #If the letter is not present in the database, use the default info
					idx = year_dict_labels.index('default')
					xbmc.log(msg='IAGL:  The year %(cats)s was not found, using IAGL default info for that item' % {'cats': cats}, level=xbmc.LOGDEBUG)
					default_idx = idx
				except:
					idx = None
			if idx is not None: #Fill in listitem parameters
				if idx == year_dict_labels.index('Unknown'):
					total_in_current_year= len(current_game_years_unknown)
				else:
					total_in_current_year = current_game_years.count(cats.lower())
				total_in_current_year_label = cats+'    ('+str(total_in_current_year)+')'
				total_in_current_year_label2 = cats
				current_trailer = self.get_trailer(year_dict['categories']['category'][idx].get('trailer'))
				li = {'values': {'label' : total_in_current_year_label,
						'label2' : total_in_current_year_label2,
						},
						'info': {'originaltitle' : total_in_current_year_label2,
						'title' : total_in_current_year_label,
						'plot' : year_dict['categories']['category'][idx]['plot'],
						'trailer' : current_trailer,
						},
						'art': {'poster' : self.choose_image(year_dict['categories']['category'][idx]['thumb'],self.default_thumb,None),
						'banner' : self.choose_image(year_dict['categories']['category'][idx]['banner'],self.default_banner,None),
						'fanart' : self.choose_image(year_dict['categories']['category'][idx]['fanart'],self.default_fanart,None),
						'clearlogo' : self.choose_image(year_dict['categories']['category'][idx]['logo'],None,None),
						'icon' : self.choose_image(year_dict['categories']['category'][idx]['logo'],None,None),
						'thumb' : self.choose_image(year_dict['categories']['category'][idx]['thumb'],self.default_thumb,None),
						},
						}
				# year_listitems.append(xbmcgui.ListItem(label=li['values']['label'],label2=li['values']['label2'], offscreen=True))
				year_listitems.append(self.create_kodi_listitem(li['values']['label'],li['values']['label2']))
				year_listitems[-1].setInfo(self.media_type,li['info'])
				year_listitems[-1].setArt(li['art'])
			else:
				xbmc.log(msg='IAGL Error:  An error occured and year %(cats)s could not be displayed' % {'cats': cats}, level=xbmc.LOGERROR)

		return year_listitems

	def get_players_from_game_lists(self, game_lists):
		players_list_temp = list()
		players_list_sorted = list()
		if game_lists is None: #Use all lists is the query is for None
			game_lists = [x for x in self.get_game_lists().get('dat_filename')]
		for game_list_id in game_lists:
			current_games_dict = self.get_games(game_list_id)
			current_game_players = [y.strip() for y in self.flatten_list([x.get('properties').get('nplayers').split(',') for x in current_games_dict if x.get('properties').get('nplayers') is not None]) if len(y)>0]
			current_game_players_unknown = [x.get('properties').get('nplayers') for x in current_games_dict if x.get('properties').get('nplayers') is None]
			current_game_players_sorted = sorted(list(set(current_game_players)))
			if len(current_game_players_unknown)>0:
				current_game_players_sorted.append('Unknown')
			players_list_temp = players_list_temp+current_game_players_sorted
		players_list_sorted = sorted(list(set(players_list_temp)))
		return players_list_sorted

	def get_game_list_players_as_listitems(self, game_list_id):
		player_listitems = list()
		games_dict = self.get_games(game_list_id)
		player_dict = self.get_player_game_listing()
		current_game_players = [y.strip() for y in self.flatten_list([x.get('properties').get('nplayers').split(',') for x in games_dict if x.get('properties').get('nplayers') is not None]) if len(y)>0]
		current_game_players_unknown = [x.get('properties').get('nplayers') for x in games_dict if x.get('properties').get('nplayers') is None]
		current_game_players_sorted = sorted(list(set(current_game_players)))
		if len(current_game_players_unknown)>0:
			current_game_players_sorted.append('Unknown')
		player_dict_labels = [x['label'] for x in player_dict['categories']['category']]

		for cats in current_game_players_sorted:
			try: #Find the current letter in the alphabetical database
				idx = player_dict_labels.index(cats)
			except:
				try: #If the letter is not present in the database, use the default info
					idx = player_dict_labels.index('default')
					xbmc.log(msg='IAGL:  The num players %(cats)s was not found, using IAGL default info for that item' % {'cats': cats}, level=xbmc.LOGDEBUG)
					default_idx = idx
				except:
					idx = None
			if idx is not None: #Fill in listitem parameters
				if idx == player_dict_labels.index('Unknown'):
					total_in_current_player= len(current_game_players_unknown)
				else:
					total_in_current_player = current_game_players.count(cats)
				total_in_current_player_label = cats+'    ('+str(total_in_current_player)+')'
				total_in_current_player_label2 = cats
				current_trailer = self.get_trailer(player_dict['categories']['category'][idx].get('trailer'))
				li = {'values': {'label' : total_in_current_player_label,
						'label2' : total_in_current_player_label2,
						},
						'info': {'originaltitle' : total_in_current_player_label2,
						'title' : total_in_current_player_label,
						'plot' : player_dict['categories']['category'][idx]['plot'],
						'trailer' : current_trailer,
						},
						'art': {'poster' : self.choose_image(player_dict['categories']['category'][idx]['thumb'],self.default_thumb,None),
						'banner' : self.choose_image(player_dict['categories']['category'][idx]['banner'],self.default_banner,None),
						'fanart' : self.choose_image(player_dict['categories']['category'][idx]['fanart'],self.default_fanart,None),
						'clearlogo' : self.choose_image(player_dict['categories']['category'][idx]['logo'],None,None),
						'icon' : self.choose_image(player_dict['categories']['category'][idx]['logo'],None,None),
						'thumb' : self.choose_image(player_dict['categories']['category'][idx]['thumb'],self.default_thumb,None),
						},
						}
				# player_listitems.append(xbmcgui.ListItem(label=li['values']['label'],label2=li['values']['label2'], offscreen=True))
				player_listitems.append(self.create_kodi_listitem(li['values']['label'],li['values']['label2']))
				player_listitems[-1].setInfo(self.media_type,li['info'])
				player_listitems[-1].setArt(li['art'])
			else:
				xbmc.log(msg='IAGL Error:  An error occured and num players %(cats)s could not be displayed' % {'cats': cats}, level=xbmc.LOGERROR)

		return player_listitems

	def get_studios_from_game_lists(self, game_lists):
		studio_list_temp = list()
		studio_list_sorted = list()
		if game_lists is None: #Use all lists is the query is for None
			game_lists = [x for x in self.get_game_lists().get('dat_filename')]
		for game_list_id in game_lists:
			current_games_dict = self.get_games(game_list_id)
			current_game_studios = [y.strip().lower() for y in self.flatten_list([x.get('info').get('studio').split(',') for x in current_games_dict if x.get('info').get('studio') is not None]) if len(y)>0]
			current_game_studios_unknown = [x.get('info').get('studio') for x in current_games_dict if x.get('info').get('studio') is None]
			current_game_studios_sorted = sorted(list(set([y.strip() for y in self.flatten_list([x.get('info').get('studio').split(',') for x in current_games_dict if x.get('info').get('studio') is not None]) if len(y)>0])))
			if len(current_game_studios_unknown)>0:
				current_game_studios_sorted.append('Unknown')
			studio_list_temp = studio_list_temp+current_game_studios_sorted
		studio_list_sorted = sorted(list(set(studio_list_temp)))
		return studio_list_sorted

	def get_game_list_studios_as_listitems(self, game_list_id):
		studio_listitems = list()
		games_dict = self.get_games(game_list_id)
		studio_dict = self.get_studio_game_listing()
		current_game_studios = [y.strip().lower() for y in self.flatten_list([x.get('info').get('studio').split(',') for x in games_dict if x.get('info').get('studio') is not None]) if len(y)>0]
		current_game_studios_unknown = [x.get('info').get('studio') for x in games_dict if x.get('info').get('studio') is None]
		current_game_studios_sorted = sorted(list(set([y.strip() for y in self.flatten_list([x.get('info').get('studio').split(',') for x in games_dict if x.get('info').get('studio') is not None]) if len(y)>0])))
		if len(current_game_studios_unknown)>0:
			current_game_studios_sorted.append('Unknown')
		studio_dict_labels = [x['label'] for x in studio_dict['categories']['category']]

		for cats in current_game_studios_sorted:
			try: #Find the current letter in the alphabetical database
				idx = studio_dict_labels.index(cats)
			except:
				try: #If the letter is not present in the database, use the default info
					idx = studio_dict_labels.index('default')
					xbmc.log(msg='IAGL:  The studio %(cats)s was not found, using IAGL default info for that item' % {'cats': cats}, level=xbmc.LOGDEBUG)
					default_idx = idx
				except:
					idx = None
			if idx is not None: #Fill in listitem parameters
				if idx == studio_dict_labels.index('Unknown'):
					total_in_current_studio = len(current_game_studios_unknown)
				else:
					total_in_current_studio = current_game_studios.count(cats.lower())
				total_in_current_studio_label = cats+'    ('+str(total_in_current_studio)+')'
				total_in_current_studio_label2 = cats
				current_trailer = self.get_trailer(studio_dict['categories']['category'][idx].get('trailer'))
				li = {'values': {'label' : total_in_current_studio_label,
						'label2' : total_in_current_studio_label2,
						},
						'info': {'originaltitle' : total_in_current_studio_label2,
						'title' : total_in_current_studio_label,
						'plot' : studio_dict['categories']['category'][idx]['plot'],
						'trailer' : current_trailer,
						},
						'art': {'poster' : self.choose_image(studio_dict['categories']['category'][idx]['thumb'],self.default_thumb,None),
						'banner' : self.choose_image(studio_dict['categories']['category'][idx]['banner'],self.default_banner,None),
						'fanart' : self.choose_image(studio_dict['categories']['category'][idx]['fanart'],self.default_fanart,None),
						'clearlogo' : self.choose_image(studio_dict['categories']['category'][idx]['logo'],None,None),
						'icon' : self.choose_image(studio_dict['categories']['category'][idx]['logo'],None,None),
						'thumb' : self.choose_image(studio_dict['categories']['category'][idx]['thumb'],self.default_thumb,None),
						},
						}
				# studio_listitems.append(xbmcgui.ListItem(label=li['values']['label'],label2=li['values']['label2'], offscreen=True))
				studio_listitems.append(self.create_kodi_listitem(li['values']['label'],li['values']['label2']))
				studio_listitems[-1].setInfo(self.media_type,li['info'])
				studio_listitems[-1].setArt(li['art'])
			else:
				xbmc.log(msg='IAGL Error:  An error occured and studio %(cats)s could not be displayed' % {'cats': cats}, level=xbmc.LOGERROR)

		return studio_listitems

	def get_game_list_choose_as_listitems(self, game_list_id):
		choose_listitems = list()
		choose_dict = self.get_choose_game_listing()
		current_choices = self.game_listing_settings.split('|')
		current_choices.pop(current_choices.index('Choose from List')) #Remove this from the list
		current_choices_routes = self.game_listing_settings_routes
		current_choices_routes.pop(current_choices_routes.index('choose_from_list')) #Remove this from the list
		choose_dict_labels = [x['label'] for x in choose_dict['categories']['category']]

		for cats in current_choices:
			try: #Find the current letter in the alphabetical database
				idx = choose_dict_labels.index(cats)
			except:
				try: #If the letter is not present in the database, use the default info
					idx = choose_dict_labels.index('default')
					xbmc.log(msg='IAGL:  The choose category %(cats)s was not found, using IAGL default info for that item' % {'cats': cats}, level=xbmc.LOGDEBUG)
					default_idx = idx
				except:
					idx = None
			if idx is not None: #Fill in listitem parameters
				current_trailer = self.get_trailer(choose_dict['categories']['category'][idx].get('trailer'))
				li = {'values': {'label' : cats,
						'label2' : current_choices_routes[idx],
						},
						'info': {'originaltitle' : choose_dict_labels[idx],
						'title' : cats,
						'plot' : choose_dict['categories']['category'][idx]['plot'],
						'trailer' : current_trailer,
						},
						'art': {'poster' : self.choose_image(choose_dict['categories']['category'][idx]['thumb'],self.default_thumb,None),
						'banner' : self.choose_image(choose_dict['categories']['category'][idx]['banner'],self.default_banner,None),
						'fanart' : self.choose_image(choose_dict['categories']['category'][idx]['fanart'],self.default_fanart,None),
						'clearlogo' : self.choose_image(choose_dict['categories']['category'][idx]['logo'],self.default_icon,None),
						'icon' : self.choose_image(choose_dict['categories']['category'][idx]['logo'],self.default_icon,None),
						'thumb' : self.choose_image(choose_dict['categories']['category'][idx]['thumb'],self.default_thumb,None),
						},
						}
				# choose_listitems.append(xbmcgui.ListItem(label=li['values']['label'],label2=li['values']['label2'], offscreen=True))
				choose_listitems.append(self.create_kodi_listitem(li['values']['label'],li['values']['label2']))
				choose_listitems[-1].setInfo(self.media_type,li['info'])
				choose_listitems[-1].setArt(li['art'])
			else:
				xbmc.log(msg='IAGL Error:  An error occured and choice %(cats)s could not be displayed' % {'cats': cats}, level=xbmc.LOGERROR)

		return choose_listitems

	def get_browse_lists_as_listitems(self):
		browse_listitems = list()
		browse_dict = self.get_browse_listing()
		current_choices = self.archive_listing_settings.split('|')
		current_choices.pop(current_choices.index('Choose from List')) #Remove this from the list
		current_choices_routes = self.archive_listing_settings_routes
		current_choices_routes.pop(current_choices_routes.index('choose_from_list')) #Remove this from the list
		browse_dict_labels = [x['label'] for x in browse_dict['categories']['category']]

		for cats in current_choices:
			try: #Find the current letter in the alphabetical database
				idx = browse_dict_labels.index(cats)
			except:
				try: #If the category is not present in the database, use the default info
					idx = browse_dict_labels.index('default')
					xbmc.log(msg='IAGL:  The browse category %(cats)s was not found, using IAGL default info for that item' % {'cats': cats}, level=xbmc.LOGDEBUG)
					default_idx = idx
				except:
					idx = None
			if idx is not None: #Fill in listitem parameters
				current_trailer = self.get_trailer(browse_dict['categories']['category'][idx].get('trailer'))
				li = {'values': {'label' : cats,
						'label2' : current_choices_routes[idx],
						},
						'info': {'originaltitle' : browse_dict_labels[idx],
						'title' : cats,
						'plot' : browse_dict['categories']['category'][idx]['plot'],
						'trailer' : current_trailer,
						},
						'art': {'poster' : self.choose_image(browse_dict['categories']['category'][idx]['thumb'],self.default_thumb,None),
						'banner' : self.choose_image(browse_dict['categories']['category'][idx]['banner'],self.default_banner,None),
						'fanart' : self.choose_image(browse_dict['categories']['category'][idx]['fanart'],self.default_fanart,None),
						'clearlogo' : self.choose_image(browse_dict['categories']['category'][idx]['logo'],self.default_icon,None),
						'icon' : self.choose_image(browse_dict['categories']['category'][idx]['logo'],self.default_icon,None),
						'thumb' : self.choose_image(browse_dict['categories']['category'][idx]['thumb'],self.default_thumb,None),
						},
						}
				# browse_listitems.append(xbmcgui.ListItem(label=li['values']['label'],label2=li['values']['label2'], offscreen=True))
				browse_listitems.append(self.create_kodi_listitem(li['values']['label'],li['values']['label2']))
				browse_listitems[-1].setInfo(self.media_type,li['info'])
				browse_listitems[-1].setArt(li['art'])
			else:
				xbmc.log(msg='IAGL Error:  An error occured and browse category %(cats)s could not be displayed' % {'cats': cats}, level=xbmc.LOGERROR)

		return browse_listitems

	def get_search_menu_items_as_listitems(self,current_query):
		search_listitems = list()
		search_dict = self.get_search_listing()
		search_dict_labels = [x['label'] for x in search_dict['categories']['category']]

		for ii,search_terms in enumerate(search_dict_labels):
			current_trailer = self.get_trailer(search_dict['categories']['category'][ii].get('trailer'))
			try:
				if type(current_query[search_dict['categories']['category'][ii].get('label2')]) is list:
					current_value = ','.join(current_query[search_dict['categories']['category'][ii].get('label2')])
				else:
					current_value = current_query[search_dict['categories']['category'][ii].get('label2')]
			except:
				current_value = None
			if current_value is not None:
				if len(current_value)> 50:
					current_value = current_value[0:50]+'...' #Shorten what is displayed
				current_label = search_terms+'[CR]'+current_value
			else:
				current_label = search_terms
			if search_dict['categories']['category'][ii].get('label2') == 'execute':
				if type(self.change_search_terms_to_any(current_query['lists'])) is list:
					current_lists = '[CR]     '+'[CR]     '.join(self.change_search_terms_to_any(current_query['lists']))
				else:
					current_lists = self.change_search_terms_to_any(current_query['lists'])
				if type(self.change_search_terms_to_any(current_query['genre'])) is list:
					current_genres = '[CR]     '+'[CR]     '.join(self.change_search_terms_to_any(current_query['genre']))
				else:
					current_genres = self.change_search_terms_to_any(current_query['genre'])
				if type(self.change_search_terms_to_any(current_query['nplayers'])) is list:
					current_nplayers = '[CR]     '+'[CR]     '.join(self.change_search_terms_to_any(current_query['nplayers']))
				else:
					current_nplayers = self.change_search_terms_to_any(current_query['nplayers'])	
				if type(self.change_search_terms_to_any(current_query['year'])) is list:
					current_years = '[CR]     '+'[CR]     '.join(self.change_search_terms_to_any(current_query['year']))
				else:
					current_years = self.change_search_terms_to_any(current_query['year'])	
				if type(self.change_search_terms_to_any(current_query['studio'])) is list:
					current_studios = '[CR]     '+'[CR]     '.join(self.change_search_terms_to_any(current_query['studio']))
				else:
					current_studios = self.change_search_terms_to_any(current_query['studio'])		
				current_plot = '[B]Current Query[/B][CR]Search Title: '+self.change_search_terms_to_any(current_query['title'])+'[CR]Search Lists: '+current_lists+'[CR]Search Genres: '+current_genres+'[CR]Search Players: '+current_nplayers+'[CR]Search Years: '+current_years+'[CR]Search Studios: '+current_studios+'[CR]Search Tags: '+self.change_search_terms_to_any(current_query['tag'])+'[CR]'
			else:
				if current_value is not None:
					current_plot = '[B]Current Entry[/B][CR]'+current_value
				else:
					current_plot = search_dict['categories']['category'][ii].get('plot')
			li = {'values': {'label' : current_label,
					'label2' : search_dict['categories']['category'][ii].get('label2'),
					},
					'info': {'originaltitle' : search_dict['categories']['category'][ii].get('label'),
					'title' : search_dict['categories']['category'][ii].get('label'),
					'plot' : current_plot,
					'trailer' : current_trailer,
					},
					'art': {'poster' : self.choose_image(search_dict['categories']['category'][ii]['thumb'],self.default_thumb,None),
					'banner' : self.choose_image(search_dict['categories']['category'][ii]['banner'],self.default_banner,None),
					'fanart' : self.choose_image(search_dict['categories']['category'][ii]['fanart'],self.default_fanart,None),
					'clearlogo' : self.choose_image(search_dict['categories']['category'][ii]['logo'],None,None),
					'icon' : self.choose_image(search_dict['categories']['category'][ii]['logo'],None,None),
					'thumb' : self.choose_image(search_dict['categories']['category'][ii]['thumb'],self.default_thumb,None),
					},
					}
			search_listitems.append(self.create_kodi_listitem(li['values']['label'],li['values']['label2']))
			search_listitems[-1].setInfo(self.media_type,li['info'])
			search_listitems[-1].setArt(li['art'])

		return search_listitems

	def get_random_menu_items_as_listitems(self,current_query):
		random_listitems = list()
		random_dict = self.get_random_listing()
		random_dict_labels = [x['label'] for x in random_dict['categories']['category']]

		for ii,random_terms in enumerate(random_dict_labels):
			current_trailer = self.get_trailer(random_dict['categories']['category'][ii].get('trailer'))
			try:
				if type(current_query[random_dict['categories']['category'][ii].get('label2')]) is list:
					current_value = ','.join(current_query[random_dict['categories']['category'][ii].get('label2')])
				else:
					current_value = current_query[random_dict['categories']['category'][ii].get('label2')]
			except:
				current_value = None
			if current_value is not None:
				if len(current_value)> 50:
					current_value = current_value[0:50]+'...' #Shorten what is displayed
				current_label = random_terms+'[CR]'+current_value
			else:
				current_label = random_terms
			if random_dict['categories']['category'][ii].get('label2') == 'execute':
				if current_query['title'] is None:
					current_num_results = '1'
				else:
					current_num_results = str(current_query['title'])
				if type(self.change_search_terms_to_any(current_query['lists'])) is list:
					current_lists = '[CR]     '+'[CR]     '.join(self.change_search_terms_to_any(current_query['lists']))
				else:
					current_lists = self.change_search_terms_to_any(current_query['lists'])
				if type(self.change_search_terms_to_any(current_query['genre'])) is list:
					current_genres = '[CR]     '+'[CR]     '.join(self.change_search_terms_to_any(current_query['genre']))
				else:
					current_genres = self.change_search_terms_to_any(current_query['genre'])
				if type(self.change_search_terms_to_any(current_query['nplayers'])) is list:
					current_nplayers = '[CR]     '+'[CR]     '.join(self.change_search_terms_to_any(current_query['nplayers']))
				else:
					current_nplayers = self.change_search_terms_to_any(current_query['nplayers'])	
				if type(self.change_search_terms_to_any(current_query['year'])) is list:
					current_years = '[CR]     '+'[CR]     '.join(self.change_search_terms_to_any(current_query['year']))
				else:
					current_years = self.change_search_terms_to_any(current_query['year'])	
				if type(self.change_search_terms_to_any(current_query['studio'])) is list:
					current_studios = '[CR]     '+'[CR]     '.join(self.change_search_terms_to_any(current_query['studio']))
				else:
					current_studios = self.change_search_terms_to_any(current_query['studio'])		
				current_plot = '[B]Random Play[/B][CR]Num of Results: '+current_num_results+'[CR]Search Lists: '+current_lists+'[CR]Search Genres: '+current_genres+'[CR]Search Players: '+current_nplayers+'[CR]Search Years: '+current_years+'[CR]Search Studios: '+current_studios+'[CR]Search Tags: '+self.change_search_terms_to_any(current_query['tag'])+'[CR]'
			else:
				if current_value is not None:
					current_plot = '[B]Current Entry[/B][CR]'+current_value
				else:
					current_plot = random_dict['categories']['category'][ii].get('plot')
			li = {'values': {'label' : current_label,
					'label2' : random_dict['categories']['category'][ii].get('label2'),
					},
					'info': {'originaltitle' : random_dict['categories']['category'][ii].get('label'),
					'title' : random_dict['categories']['category'][ii].get('label'),
					'plot' : current_plot,
					'trailer' : current_trailer,
					},
					'art': {'poster' : self.choose_image(random_dict['categories']['category'][ii]['thumb'],self.default_thumb,None),
					'banner' : self.choose_image(random_dict['categories']['category'][ii]['banner'],self.default_banner,None),
					'fanart' : self.choose_image(random_dict['categories']['category'][ii]['fanart'],self.default_fanart,None),
					'clearlogo' : self.choose_image(random_dict['categories']['category'][ii]['logo'],None,None),
					'icon' : self.choose_image(random_dict['categories']['category'][ii]['logo'],None,None),
					'thumb' : self.choose_image(random_dict['categories']['category'][ii]['thumb'],self.default_thumb,None),
					},
					}
			random_listitems.append(self.create_kodi_listitem(li['values']['label'],li['values']['label2']))
			random_listitems[-1].setInfo(self.media_type,li['info'])
			random_listitems[-1].setArt(li['art'])

		return random_listitems


	def initialize_search_query(self):
		current_query = dict()
		current_query['title'] = None
		current_query['tag'] = None
		current_query['lists'] = None
		current_query['year'] = None
		current_query['genre'] = None
		current_query['nplayers'] = None
		current_query['studio'] = None
		xbmcgui.Window(self.windowid).setProperty('iagl_search_query',json.dumps(current_query))

	def initialize_random_query(self):
		current_query = dict()
		current_query['title'] = None
		current_query['tag'] = None
		current_query['lists'] = None
		current_query['year'] = None
		current_query['genre'] = None
		current_query['nplayers'] = None
		current_query['studio'] = None
		xbmcgui.Window(self.windowid).setProperty('iagl_random_query',json.dumps(current_query))

	def get_query_as_url(self,query_in):
		return url_encode(query_in)

	def get_query_from_args(self,args_in):
		current_query = dict()
		current_query['title'] = None
		current_query['tag'] = None
		current_query['lists'] = None
		current_query['year'] = None
		current_query['genre'] = None
		current_query['nplayers'] = None
		current_query['studio'] = None
		try:
			current_query['title'] = args_in['title'][0]
			if current_query['title'].lower() == 'none':
				current_query['title'] = None
		except:
			pass
		try:
			current_query['tag'] = args_in['tag'][0]
			if current_query['tag'].lower() == 'none':
				current_query['tag'] = None
		except:
			pass
		try:
			current_query['lists'] = lit_eval(args_in['lists'][0])
		except:
			pass
		try:
			current_query['genre'] = lit_eval(args_in['genre'][0])
		except:
			pass
		try:
			current_query['year'] = lit_eval(args_in['year'][0])
		except:
			pass	
		try:
			current_query['nplayers'] = lit_eval(args_in['nplayers'][0])
		except:
			pass
		try:
			current_query['studio'] = lit_eval(args_in['studio'][0])
		except:
			pass
		return current_query

	def get_games(self, game_list_id):
		games_dict = None
		current_xml_file = os.path.join(self.get_dat_folder_path(),game_list_id+'.xml')
		cache_list_option = self.get_setting_as_bool(self.handle.getSetting(id='iagl_setting_cache_list'))
		mem_cache_option = self.get_setting_as_bool(self.handle.getSetting(id='iagl_setting_mem_cache'))
		current_crc32 = self.get_crc32_from_list_id(game_list_id)
		cache_exists, cache_filename = self.check_for_list_cache(current_crc32)

		#Load from mem cache if its present and crc matches
		if mem_cache_option:
			try:
				crc_compare = json.loads(str(xbmcgui.Window(self.windowid).getProperty('iagl_current_crc')))
			except:
				crc_compare = None
			if crc_compare is not None and crc_compare == current_crc32:
				try:
					games_dict = json.loads(xbmcgui.Window(self.windowid).getProperty('iagl_game_list'))
					xbmc.log(msg='IAGL:  Grabbing mem cache for %(game_list_id)s from %(current_crc)s' % {'game_list_id': game_list_id, 'current_crc': current_crc32}, level=xbmc.LOGDEBUG)
				except:
					games_dict = None

		#If mem cache was not available, load from disk cache if its present and crc matches
		if cache_exists and cache_list_option:
			if games_dict is None:
				xbmc.log(msg='IAGL:  Disk cache found for %(game_list_id)s, cache file %(cache_filename)s' % {'game_list_id': game_list_id, 'cache_filename': cache_filename}, level=xbmc.LOGDEBUG)
				games_dict = self.get_games_dict_from_cache(cache_filename)
		else: #If disk cache was not available, parse the file from the xml
			try:
				if games_dict is None:
					xbmc.log(msg='IAGL:  Parsing XMl file for %(game_list_id)s, file CRC %(current_crc)s' % {'game_list_id': game_list_id, 'current_crc': current_crc32}, level=xbmc.LOGDEBUG)
					games_dict_etree = etree_to_dict(ET.parse(current_xml_file).getroot())
					games_dict = list()
					if type(games_dict_etree['datafile']['game']) is not list:  #Needed to check for archives with only one item
						games_dict_etree['datafile']['game'] = [games_dict_etree['datafile']['game']]
					for game_item in games_dict_etree['datafile']['game']:
						current_date, current_year = self.get_date_and_year(game_item.get('releasedate'), game_item.get('year'))
						current_tag = self.get_rom_tag(game_item.get('description'))
						current_trailer = self.get_trailer(game_item.get('videoid'))
						current_size = self.get_rom_size(game_item)
						json_item = dict()
						json_item['emu'] = games_dict_etree['datafile']['header']
						json_item['emu']['game_list_id'] = game_list_id
						json_item['emu']['game_list_crc'] = current_crc32
						json_item['emu']['fullpath'] = current_xml_file
						json_item['game'] = game_item
						games_dict.append({'values': {'label' : game_item.get('description'),
										'label2' : game_item.get('@name'),
							},
							'info': {'originaltitle' : game_item.get('@name'),
							'title' : game_item.get('description'),
							'plot' : game_item.get('plot'),
							'date' : current_date,
							'year' : current_year,
							'studio' : game_item.get('studio'),
							'genre' : game_item.get('genre'),
							'rating' : game_item.get('rating'),
							'mpaa' : game_item.get('ESRB'),
							'trailer' : current_trailer,
							'size' : current_size,
							},
							'art': {'poster' : self.choose_image(game_item.get('boxart1'),game_item.get('snapshot1'),self.default_thumb),
							'banner' : self.choose_image(game_item.get('banner1'),self.default_banner,None),
							'fanart' : self.choose_image(game_item.get('fanart1'),self.default_fanart,None),
							'clearlogo' : self.choose_image(game_item.get('clearlogo1'),None,None),
							'icon' : self.choose_image(game_item.get('clearlogo1'),None,None),
							'thumb' : self.choose_image(game_item.get('boxart1'),game_item.get('snapshot1'),self.default_thumb),
							},
							'properties': {'iagl_json' : json.dumps(json_item),
							'tag': current_tag,
							'nplayers': game_item.get('nplayers'),
							},
							})
						if current_date is None:
							games_dict[-1]['info'].pop('date',None)
						if current_year is None:
							games_dict[-1]['info'].pop('year',None)

					if cache_list_option: #Save the parsed file to disk if enabled
						self.save_games_dict_to_cache(games_dict,game_list_id,current_crc32)
			except Exception as exc: #except Exception, (exc):
				xbmc.log(msg='IAGL Error:  Error parsing game list %(game_list_id)s.  Exception %(exc)s' % {'game_list_id': game_list_id, 'exc': exc}, level=xbmc.LOGERROR)
				games_dict = None

		if mem_cache_option: #Save the current game list to mem cache if enabled
			try:
				crc_compare = json.loads(str(xbmcgui.Window(self.windowid).getProperty('iagl_current_crc')))
			except:
				crc_compare = None
			if crc_compare is None or crc_compare != current_crc32:
				xbmc.log(msg='IAGL:  Mem Cache saved for %(game_list_id)s to %(current_crc)s' % {'game_list_id': game_list_id, 'current_crc': current_crc32}, level=xbmc.LOGDEBUG)
				xbmcgui.Window(self.windowid).setProperty('iagl_current_crc',json.dumps(current_crc32))
				xbmcgui.Window(self.windowid).setProperty('iagl_game_list',json.dumps(games_dict))
		else: #Ensure the mem cache is empty if not enabled
			xbmcgui.Window(self.windowid).setProperty('iagl_current_crc',None)
			xbmcgui.Window(self.windowid).setProperty('iagl_game_list',None)

		return games_dict

	def get_games_as_listitems(self, game_list_id, filter_method = None, filter_value = None, page_number = 1):
		game_list = list()
		page_info = dict()
		clean_label_option = self.get_setting_as_bool(self.handle.getSetting(id='iagl_setting_clean_list'))
		label_naming_convention = self.handle.getSetting(id='iagl_setting_naming')
		games_dict = self.get_games(game_list_id)
		current_categories = None
		if games_dict[0].get('properties').get('iagl_json') is not None:
			current_categories = json.loads(games_dict[0].get('properties').get('iagl_json')).get('emu').get('emu_category')

		if games_dict is not None:
			if filter_method == 'list_all' or filter_method == None:
				current_page = paginate.Page(games_dict, page=page_number, items_per_page=self.get_items_per_page())
				page_info['page'] = current_page.page
				page_info['page_count'] = current_page.page_count
				page_info['next_page'] = current_page.next_page
				page_info['item_count'] = current_page.item_count
				page_info['categories'] = current_categories
				for game_item in current_page:
					game_item['values']['label'] = self.update_game_label(self.get_clean_label(game_item['values']['label'],clean_label_option),game_item,label_naming_convention)
					# game_list.append(xbmcgui.ListItem(label=game_item['values']['label'],label2=game_item['values']['label2'], offscreen=True))
					game_list.append(self.create_kodi_listitem(game_item['values']['label'],game_item['values']['label2']))
					game_list[-1].setInfo(self.media_type,game_item['info'])
					game_list[-1].setArt(game_item['art'])
					game_list[-1].setProperty('iagl_json',game_item['properties']['iagl_json'])
			elif filter_method == 'alphabetical':
				if filter_value == '%23' or filter_value == '#':
					current_page = paginate.Page([x for x in games_dict if x['values']['label2'][0] not in self.non_number_cat], page=page_number, items_per_page=self.get_items_per_page())
				else:
					current_page = paginate.Page([x for x in games_dict if x['values']['label2'].startswith(filter_value.upper()) or x['values']['label2'].startswith(filter_value.lower())], page=page_number, items_per_page=self.get_items_per_page())
				page_info['page'] = current_page.page
				page_info['page_count'] = current_page.page_count
				page_info['next_page'] = current_page.next_page
				page_info['item_count'] = current_page.item_count
				page_info['categories'] = current_categories
				for game_item in current_page:
					game_item['values']['label'] = self.update_game_label(self.get_clean_label(game_item['values']['label'],clean_label_option),game_item,label_naming_convention)
					# game_list.append(xbmcgui.ListItem(label=game_item['values']['label'],label2=game_item['values']['label2'], offscreen=True))
					game_list.append(self.create_kodi_listitem(game_item['values']['label'],game_item['values']['label2']))
					game_list[-1].setInfo(self.media_type,game_item['info'])
					game_list[-1].setArt(game_item['art'])
					game_list[-1].setProperty('iagl_json',game_item['properties']['iagl_json'])
			elif filter_method == 'list_by_genre':
				if filter_value == 'Unknown' or filter_value == None:
					current_page = paginate.Page([x for x in games_dict if x.get('info').get('genre') is None], page=page_number, items_per_page=self.get_items_per_page())
				else:
					current_page = paginate.Page([x for x in games_dict if x.get('info').get('genre') is not None and filter_value.lower() in x.get('info').get('genre').lower()], page=page_number, items_per_page=self.get_items_per_page())
				page_info['page'] = current_page.page
				page_info['page_count'] = current_page.page_count
				page_info['next_page'] = current_page.next_page
				page_info['item_count'] = current_page.item_count
				page_info['categories'] = current_categories
				for game_item in current_page:
					game_item['values']['label'] = self.update_game_label(self.get_clean_label(game_item['values']['label'],clean_label_option),game_item,label_naming_convention)
					# game_list.append(xbmcgui.ListItem(label=game_item['values']['label'],label2=game_item['values']['label2'], offscreen=True))
					game_list.append(self.create_kodi_listitem(game_item['values']['label'],game_item['values']['label2']))
					game_list[-1].setInfo(self.media_type,game_item['info'])
					game_list[-1].setArt(game_item['art'])
					game_list[-1].setProperty('iagl_json',game_item['properties']['iagl_json'])
			elif filter_method == 'list_by_year':
				if filter_value == 'Unknown' or filter_value == None:
					current_page = paginate.Page([x for x in games_dict if x.get('info').get('year') is None], page=page_number, items_per_page=self.get_items_per_page())
				else:
					current_page = paginate.Page([x for x in games_dict if x.get('info').get('year') is not None and x.get('info').get('year') == filter_value], page=page_number, items_per_page=self.get_items_per_page())
				page_info['page'] = current_page.page
				page_info['page_count'] = current_page.page_count
				page_info['next_page'] = current_page.next_page
				page_info['item_count'] = current_page.item_count
				page_info['categories'] = current_categories
				for game_item in current_page:
					game_item['values']['label'] = self.update_game_label(self.get_clean_label(game_item['values']['label'],clean_label_option),game_item,label_naming_convention)
					# game_list.append(xbmcgui.ListItem(label=game_item['values']['label'],label2=game_item['values']['label2'], offscreen=True))
					game_list.append(self.create_kodi_listitem(game_item['values']['label'],game_item['values']['label2']))
					game_list[-1].setInfo(self.media_type,game_item['info'])
					game_list[-1].setArt(game_item['art'])
					game_list[-1].setProperty('iagl_json',game_item['properties']['iagl_json'])
			elif filter_method == 'list_by_players':
				if filter_value == 'Unknown' or filter_value == None:
					current_page = paginate.Page([x for x in games_dict if x.get('properties').get('nplayers') is None], page=page_number, items_per_page=self.get_items_per_page())
				else:
					# current_page = paginate.Page([x for x in games_dict if x.get('properties').get('nplayers') is not None and x.get('properties').get('nplayers') == filter_value], page=page_number, items_per_page=self.get_items_per_page())
					current_page = paginate.Page([x for x in games_dict if x.get('properties').get('nplayers') is not None and ((filter_value == x.get('properties').get('nplayers')) or (',' in x.get('properties').get('nplayers') and filter_value.lower() in x.get('properties').get('nplayers').lower()))], page=page_number, items_per_page=self.get_items_per_page())  #Players must exactly equal the filter value, or just be contained in the filter value in the case of a comma seperated list, example returning filter of 1-2 Alt and the item is 1-2 Sim, 3-4 Alt
				page_info['page'] = current_page.page
				page_info['page_count'] = current_page.page_count
				page_info['next_page'] = current_page.next_page
				page_info['item_count'] = current_page.item_count
				page_info['categories'] = current_categories
				for game_item in current_page:
					game_item['values']['label'] = self.update_game_label(self.get_clean_label(game_item['values']['label'],clean_label_option),game_item,label_naming_convention)
					# game_list.append(xbmcgui.ListItem(label=game_item['values']['label'],label2=game_item['values']['label2'], offscreen=True))
					game_list.append(self.create_kodi_listitem(game_item['values']['label'],game_item['values']['label2']))
					game_list[-1].setInfo(self.media_type,game_item['info'])
					game_list[-1].setArt(game_item['art'])
					game_list[-1].setProperty('iagl_json',game_item['properties']['iagl_json'])
			elif filter_method == 'list_by_studio':
				if filter_value == 'Unknown' or filter_value == None:
					current_page = paginate.Page([x for x in games_dict if x.get('info').get('studio') is None], page=page_number, items_per_page=self.get_items_per_page())
				else:
					current_page = paginate.Page([x for x in games_dict if x.get('info').get('studio') is not None and filter_value.lower() in x.get('info').get('studio').lower()], page=page_number, items_per_page=self.get_items_per_page())
				page_info['page'] = current_page.page
				page_info['page_count'] = current_page.page_count
				page_info['next_page'] = current_page.next_page
				page_info['item_count'] = current_page.item_count
				page_info['categories'] = current_categories
				for game_item in current_page:
					game_item['values']['label'] = self.update_game_label(self.get_clean_label(game_item['values']['label'],clean_label_option),game_item,label_naming_convention)
					# game_list.append(xbmcgui.ListItem(label=game_item['values']['label'],label2=game_item['values']['label2'], offscreen=True))
					game_list.append(self.create_kodi_listitem(game_item['values']['label'],game_item['values']['label2']))
					game_list[-1].setInfo(self.media_type,game_item['info'])
					game_list[-1].setArt(game_item['art'])
					game_list[-1].setProperty('iagl_json',game_item['properties']['iagl_json'])
			elif filter_method == 'list_single_game':
				page_info['page'] = None
				page_info['page_count'] = None
				page_info['next_page'] = None
				page_info['item_count'] = None
				page_info['categories'] = current_categories
				for game_item in [x for x in games_dict if x.get('values').get('label2') is not None and x.get('values').get('label2')==filter_value]:
					game_item['values']['label'] = self.update_game_label(self.get_clean_label(game_item['values']['label'],clean_label_option),game_item,label_naming_convention)
					# game_list.append(xbmcgui.ListItem(label=game_item['values']['label'],label2=game_item['values']['label2'], offscreen=True))
					game_list.append(self.create_kodi_listitem(game_item['values']['label'],game_item['values']['label2']))
					game_list[-1].setInfo(self.media_type,game_item['info'])
					game_list[-1].setArt(game_item['art'])
					game_list[-1].setProperty('iagl_json',game_item['properties']['iagl_json'])
			else:
				xbmc.log(msg='IAGL:  Unknown game filtering method %(filter_method)s' % {'filter_method': filter_method}, level=xbmc.LOGERROR)
		else:
			xbmc.log(msg='IAGL:  There was an error getting the game dict %(game_list_id)s' % {'game_list_id': game_list_id}, level=xbmc.LOGERROR)

		return game_list, page_info

	def get_games_from_search_query_as_listitems(self, current_query, filter_method = None, filter_value = None, page_number = 1):
		game_list = list()
		page_info = dict()
		games_dict = list()
		clean_label_option = self.get_setting_as_bool(self.handle.getSetting(id='iagl_setting_clean_list'))
		label_naming_convention = self.handle.getSetting(id='iagl_setting_naming')
		#1.  Get all games from all the lists
		if current_query['lists'] is None: #Use all lists is the query is for None
			current_query['lists'] = [x for x in self.get_game_lists().get('dat_filename')]
		for game_list_id in current_query['lists']:
			try:
				games_dict = games_dict+self.get_games(game_list_id)
			except Exception as exc: #except Exception, (exc):
				xbmc.log(msg='IAGL Error:  The game list could not be serached, it may be corrupted.  Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGDEBUG) 
		xbmc.log(msg='IAGL:  Search started from %(game_number)s total games' % {'game_number': len(games_dict)}, level=xbmc.LOGDEBUG)
		#2.  Filter by title (regex)
		if current_query['title'] is not None:
			title_filter = re.compile(current_query['title'], re.IGNORECASE)
			games_dict = [x for x in games_dict if x.get('values').get('label2') is not None and len(title_filter.findall(x.get('values').get('label2')))>0]
			xbmc.log(msg='IAGL:  Title search filtered results to %(game_number)s total games' % {'game_number': len(games_dict)}, level=xbmc.LOGDEBUG)
		#3.  Filter by tag
		if current_query['tag'] is not None:
			tag_filter = re.compile(current_query['tag'], re.IGNORECASE)
			games_dict = [x for x in games_dict if x.get('properties').get('tag') is not None and len(tag_filter.findall(x.get('properties').get('tag')))>0]
			xbmc.log(msg='IAGL:  Tag search filtered results to %(game_number)s total games' % {'game_number': len(games_dict)}, level=xbmc.LOGDEBUG)
		#4.  Filter by genre
		if current_query['genre'] is not None:
			games_dict = [x for x in games_dict if x.get('info').get('genre') is not None and any([y in x.get('info').get('genre') for y in current_query['genre']])]
			xbmc.log(msg='IAGL:  Genre search filtered results to %(game_number)s total games' % {'game_number': len(games_dict)}, level=xbmc.LOGDEBUG)
		#5.  Filter by nplayers
		if current_query['nplayers'] is not None:
			games_dict = [x for x in games_dict if x.get('properties').get('nplayers') is not None and any([y in x.get('properties').get('nplayers') for y in current_query['nplayers']])]
			xbmc.log(msg='IAGL:  Players search filtered results to %(game_number)s total games' % {'game_number': len(games_dict)}, level=xbmc.LOGDEBUG)
		#6.  Filter by year
		if current_query['year'] is not None:
			games_dict = [x for x in games_dict if x.get('info').get('year') is not None and any([y in x.get('info').get('year') for y in current_query['year']])]
			xbmc.log(msg='IAGL:  Years search filtered results to %(game_number)s total games' % {'game_number': len(games_dict)}, level=xbmc.LOGDEBUG)
		#7.  Filter by studio
		if current_query['studio'] is not None:
			games_dict = [x for x in games_dict if x.get('info').get('studio') is not None and any([y in x.get('info').get('studio') for y in current_query['studio']])]
			# games_dict = [x for x in games_dict if x.get('info').get('studio') is not None and x.get('info').get('studio') in current_query['studio']]
			xbmc.log(msg='IAGL:  Studio search filtered results to %(game_number)s total games' % {'game_number': len(games_dict)}, level=xbmc.LOGDEBUG)
		
		if games_dict is not None and len(games_dict)>0:
			current_categories = 'Search Results'
			# current_categories = None
			# if games_dict[0].get('properties').get('iagl_json') is not None:
			# 	current_categories = json.loads(games_dict[0].get('properties').get('iagl_json')).get('emu').get('emu_category')

			if filter_method == 'list_all' or filter_method == None:
				current_page = paginate.Page(games_dict, page=page_number, items_per_page=self.get_items_per_page())
				page_info['page'] = current_page.page
				page_info['page_count'] = current_page.page_count
				page_info['next_page'] = current_page.next_page
				page_info['item_count'] = current_page.item_count
				page_info['categories'] = current_categories
				for game_item in current_page:
					game_item['values']['label'] = self.update_game_label(self.get_clean_label(game_item['values']['label'],clean_label_option),game_item,label_naming_convention)
					# game_list.append(xbmcgui.ListItem(label=game_item['values']['label'],label2=game_item['values']['label2'], offscreen=True))
					game_list.append(self.create_kodi_listitem(game_item['values']['label'],game_item['values']['label2']))
					game_list[-1].setInfo(self.media_type,game_item['info'])
					game_list[-1].setArt(game_item['art'])
					game_list[-1].setProperty('iagl_json',game_item['properties']['iagl_json'])
			else:
				xbmc.log(msg='IAGL:  Unknown game filtering method %(filter_method)s' % {'filter_method': filter_method}, level=xbmc.LOGERROR)
		else:
			xbmc.log(msg='IAGL:  No Results Found for the search', level=xbmc.LOGDEBUG)
			game_dict = list()
			page_info['page'] = 0
			page_info['page_count'] = 0
			page_info['next_page'] = 0
			page_info['item_count'] = 0
			page_info['categories'] = None

		return game_list, page_info

	def get_games_from_random_query_as_listitems(self, current_query, filter_method = None, filter_value = None, page_number = 1):
		from random import sample as random_sample
		game_list = list()
		page_info = dict()
		games_dict = list()
		games_dict_random = list()
		random_numbers_chosen = list()
		clean_label_option = self.get_setting_as_bool(self.handle.getSetting(id='iagl_setting_clean_list'))
		label_naming_convention = self.handle.getSetting(id='iagl_setting_naming')
		#1.  Get all games from all the lists
		if current_query['lists'] is None: #Use all lists is the query is for None
			current_query['lists'] = [x for x in self.get_game_lists().get('dat_filename')]
		for game_list_id in current_query['lists']:
			games_dict = games_dict+self.get_games(game_list_id)
		xbmc.log(msg='IAGL:  Random play started from %(game_number)s total games' % {'game_number': len(games_dict)}, level=xbmc.LOGDEBUG)
		#2.  Filter by tag
		if current_query['tag'] is not None:
			tag_filter = re.compile(current_query['tag'], re.IGNORECASE)
			games_dict = [x for x in games_dict if x.get('properties').get('tag') is not None and len(tag_filter.findall(x.get('properties').get('tag')))>0]
			xbmc.log(msg='IAGL:  Tag search filtered results to %(game_number)s total games' % {'game_number': len(games_dict)}, level=xbmc.LOGDEBUG)
		#3.  Filter by genre
		if current_query['genre'] is not None:
			games_dict = [x for x in games_dict if x.get('info').get('genre') is not None and any([y in x.get('info').get('genre') for y in current_query['genre']])]
			xbmc.log(msg='IAGL:  Genre search filtered results to %(game_number)s total games' % {'game_number': len(games_dict)}, level=xbmc.LOGDEBUG)
		#4.  Filter by nplayers
		if current_query['nplayers'] is not None:
			games_dict = [x for x in games_dict if x.get('properties').get('nplayers') is not None and any([y in x.get('properties').get('nplayers') for y in current_query['nplayers']])]
			xbmc.log(msg='IAGL:  Players search filtered results to %(game_number)s total games' % {'game_number': len(games_dict)}, level=xbmc.LOGDEBUG)
		#5.  Filter by year
		if current_query['year'] is not None:
			games_dict = [x for x in games_dict if x.get('info').get('year') is not None and any([y in x.get('info').get('year') for y in current_query['year']])]
			xbmc.log(msg='IAGL:  Years search filtered results to %(game_number)s total games' % {'game_number': len(games_dict)}, level=xbmc.LOGDEBUG)
		#6.  Filter by studio
		if current_query['studio'] is not None:
			games_dict = [x for x in games_dict if x.get('info').get('studio') is not None and any([y in x.get('info').get('studio') for y in current_query['studio']])]
			xbmc.log(msg='IAGL:  Studio search filtered results to %(game_number)s total games' % {'game_number': len(games_dict)}, level=xbmc.LOGDEBUG)
		#7.  Get number of results
		if current_query['title'] is None:
			current_query['title'] = 1
		if len(games_dict)>0:
			random_numbers_chosen = random_sample(range(len(games_dict)), min(len(games_dict),int(current_query['title'])))  #Choose between smallest of length of game list and requested number of games
			for rnc in random_numbers_chosen:
				games_dict_random.append(games_dict[rnc])
			xbmc.log(msg='IAGL:  Random play filtered results to %(game_number)s total games' % {'game_number': len(games_dict_random)}, level=xbmc.LOGDEBUG)

		if games_dict_random is not None and len(games_dict_random)>0:
			current_categories = 'Random Results'
			# current_categories = None
			# if games_dict[0].get('properties').get('iagl_json') is not None:
			# 	current_categories = json.loads(games_dict[0].get('properties').get('iagl_json')).get('emu').get('emu_category')

			if filter_method == 'list_all' or filter_method == None:
				current_page = paginate.Page(games_dict_random, page=page_number, items_per_page=self.get_items_per_page())
				page_info['page'] = current_page.page
				page_info['page_count'] = current_page.page_count
				page_info['next_page'] = current_page.next_page
				page_info['item_count'] = current_page.item_count
				page_info['categories'] = current_categories
				for game_item in current_page:
					game_item['values']['label'] = self.update_game_label(self.get_clean_label(game_item['values']['label'],clean_label_option),game_item,label_naming_convention)
					# game_list.append(xbmcgui.ListItem(label=game_item['values']['label'],label2=game_item['values']['label2'], offscreen=True))
					game_list.append(self.create_kodi_listitem(game_item['values']['label'],game_item['values']['label2']))
					game_list[-1].setInfo(self.media_type,game_item['info'])
					game_list[-1].setArt(game_item['art'])
					game_list[-1].setProperty('iagl_json',game_item['properties']['iagl_json'])
			else:
				xbmc.log(msg='IAGL:  Unknown game filtering method %(filter_method)s' % {'filter_method': filter_method}, level=xbmc.LOGERROR)
		else:
			xbmc.log(msg='IAGL:  No Results Found for the search', level=xbmc.LOGDEBUG)
			game_dict = list()
			page_info['page'] = 0
			page_info['page_count'] = 0
			page_info['next_page'] = 0
			page_info['item_count'] = 0
			page_info['categories'] = None

		return game_list, page_info
		
	def get_route_from_json(self, json_string):
		json_in = json.loads(json_string)
		route_out = None
		if type(json_in.get('game').get('rom')) is list: #Multiple files
			route_out = [x.get('@name') for x in json_in['game']['rom']]
		else:
			if json_in.get('game').get('rom') is not None:
				route_out = [json_in['game']['rom']['@name']]
		return route_out

	def get_gamelistitem_from_json(self, json_string):
		game_dict = None
		json_in = json.loads(json_string)
		clean_label_option = self.get_setting_as_bool(self.handle.getSetting(id='iagl_setting_clean_list'))
		label_naming_convention = self.handle.getSetting(id='iagl_setting_naming')
		current_date, current_year = self.get_date_and_year(json_in.get('game').get('releasedate'), json_in.get('game').get('year'))
		current_tag = self.get_rom_tag(json_in.get('game').get('description'))
		current_trailer = self.get_trailer(json_in.get('game').get('videoid'))
		current_size = self.get_rom_size(json_in.get('game'))
		current_game_id = json_in.get('game').get('@name')
		# current_filenames = self.get_rom_filenames(json_in.get('emu').get('emu_baseurl'),json_in.get('game'))
		# current_filename_sizes = self.get_rom_filename_sizes(json_in.get('game'))
		game_dict = {'values': {'label' : json_in.get('game').get('description'),
						'label2' : current_game_id,
			},
			'info': {'originaltitle' : current_game_id,
			'title' : json_in.get('game').get('description'),
			'plot' : json_in.get('game').get('plot'),
			'date' : current_date,
			'year' : current_year,
			'studio' : json_in.get('game').get('studio'),
			'genre' : json_in.get('game').get('genre'),
			'rating' : json_in.get('game').get('rating'),
			'mpaa' : json_in.get('game').get('ESRB'),
			'trailer' : current_trailer,
			'size' : current_size,
			},
			'art': {'poster' : self.choose_image(json_in.get('game').get('boxart1'),json_in.get('game').get('snapshot1'),self.default_thumb),
			'banner' : self.choose_image(json_in.get('game').get('banner1'),self.default_banner,None),
			'fanart' : self.choose_image(json_in.get('game').get('fanart1'),self.default_fanart,None),
			'clearlogo' : self.choose_image(json_in.get('game').get('clearlogo1'),None,None),
			'icon' : self.choose_image(json_in.get('game').get('clearlogo1'),None,None),
			'thumb' : self.choose_image(json_in.get('game').get('boxart1'),json_in.get('game').get('snapshot1'),self.default_thumb),
			},
			'properties': {'iagl_json': json_in,
			'tag': current_tag,
			'nplayers': json_in.get('game').get('nplayers'),
			'rating': json_in.get('game').get('rating'),
			'perspective': json_in.get('game').get('perspective'),
			'esrb': json_in.get('game').get('ESRB'),
			'emu_name' : json_in.get('emu').get('emu_name'),
			'emu_plot' : json_in.get('emu').get('emu_comment'),
			'emu_author' : json_in.get('emu').get('emu_author'),
			'emu_visibility' : json_in.get('emu').get('emu_visibility'),
			'emu_category' : json_in.get('emu').get('emu_category'),
			'emu_description' : json_in.get('emu').get('emu_description'),
			'emu_downloadpath' : json_in.get('emu').get('emu_downloadpath'),
			'emu_postdlaction' : json_in.get('emu').get('emu_postdlaction'),
			'emu_launcher' : json_in.get('emu').get('emu_launcher'),
			'emu_default_addon' : json_in.get('emu').get('emu_default_addon'),
			'emu_boxart' : self.choose_image(json_in.get('emu').get('emu_thumb'),None,None),
			'emu_banner' : self.choose_image(json_in.get('emu').get('emu_banner'),None,None),
			'emu_fanart' : self.choose_image(json_in.get('emu').get('emu_fanart'),None,None),
			'emu_logo': self.choose_image(json_in.get('emu').get('emu_logo'),None,None),
			'emu_trailer': self.get_trailer(json_in.get('emu').get('emu_trailer')),
			'game_list_id': json_in.get('emu').get('game_list_id'),
			}, 
			}
		# game_listitem = xbmcgui.ListItem(label=game_dict['values']['label'],label2=game_dict['values']['label2'], offscreen=True)
		game_listitem = self.create_kodi_listitem(game_dict['values']['label'],game_dict['values']['label2'])
		game_listitem.setInfo(self.media_type,game_dict['info'])
		game_listitem.setArt(game_dict['art'])
		for kk in game_dict['properties'].keys():
			if kk != 'iagl_json':
				if game_dict['properties'][kk] is not None:
					game_listitem.setProperty(kk,game_dict['properties'][kk])

		game_fanart_listitem = list()
		game_boxart_listitem = list()
		game_snapshot_listitem = list()
		game_box_and_snap_listitem = list()
		game_banner_listitem = list()
		for ii in range(1,11):
			if json_in.get('game').get('fanart'+str(ii)) is not None: 
				li = {'values': {'label' : json_in.get('game').get('description')},'art': {'fanart' : self.choose_image(json_in.get('game').get('fanart'+str(ii)),None,None)}}
				# game_fanart_listitem.append(xbmcgui.ListItem(label=li['values']['label'], offscreen=True))
				game_fanart_listitem.append(self.create_kodi_listitem(li['values']['label']))
				game_fanart_listitem[-1].setArt(li['art'])
			if json_in.get('game').get('boxart'+str(ii)) is not None: 
				li = {'values': {'label' : json_in.get('game').get('description')},'art': {'poster' : self.choose_image(json_in.get('game').get('boxart'+str(ii)),None,None)}}
				# game_boxart_listitem.append(xbmcgui.ListItem(label=li['values']['label'], offscreen=True))
				game_boxart_listitem.append(self.create_kodi_listitem(li['values']['label']))
				game_boxart_listitem[-1].setArt(li['art'])
				# game_box_and_snap_listitem.append(xbmcgui.ListItem(label=li['values']['label'], offscreen=True))
				game_box_and_snap_listitem.append(self.create_kodi_listitem(li['values']['label']))
				game_box_and_snap_listitem[-1].setArt(li['art'])
			if json_in.get('game').get('snapshot'+str(ii)) is not None: 
				li = {'values': {'label' : json_in.get('game').get('description')},'art': {'poster' : self.choose_image(json_in.get('game').get('snapshot'+str(ii)),None,None)}}
				# game_snapshot_listitem.append(xbmcgui.ListItem(label=li['values']['label'], offscreen=True))
				game_snapshot_listitem.append(self.create_kodi_listitem(li['values']['label']))
				game_snapshot_listitem[-1].setArt(li['art'])
				# game_box_and_snap_listitem.append(xbmcgui.ListItem(label=li['values']['label'], offscreen=True))
				game_box_and_snap_listitem.append(self.create_kodi_listitem(li['values']['label']))
				game_box_and_snap_listitem[-1].setArt(li['art'])
			if json_in.get('game').get('banner'+str(ii)) is not None: 
				li = {'values': {'label' : json_in.get('game').get('description')},'art': {'banner' : self.choose_image(json_in.get('game').get('banner'+str(ii)),None,None)}}
				# game_banner_listitem.append(xbmcgui.ListItem(label=li['values']['label'], offscreen=True))
				game_banner_listitem.append(self.create_kodi_listitem(li['values']['label']))
				game_banner_listitem[-1].setArt(li['art'])

		return url_quote(current_game_id),game_listitem,game_fanart_listitem,game_box_and_snap_listitem,game_banner_listitem,current_trailer

	def check_to_show_history(self):
		game_history_filename = os.path.join(self.get_list_cache_path(),self.game_history_filename)
		if self.get_setting_as_bool(self.handle.getSetting(id='iagl_setting_show_gamehistory')) and self.get_setting_as_bool(self.handle.getSetting(id='iagl_setting_cache_list')) and xbmcvfs.exists(game_history_filename):
			return True
		else:
			return False

	def load_game_history(self):
		game_history_filename = os.path.join(self.get_list_cache_path(),self.game_history_filename)
		games_dict = list()
		if xbmcvfs.exists(game_history_filename):
			try:
				with open(game_history_filename, 'rb') as fn:
					# games_dict = pickle.load(fn)
					games_dict = json.load(fn)
					xbmc.log(msg='IAGL:  History file list cache found, cache file %(game_history_filename)s' % {'game_history_filename': game_history_filename}, level=xbmc.LOGDEBUG)
			except Exception as exc: #except Exception, (exc):
				xbmc.log(msg='IAGL Error:  The cache file %(game_history_filename)s could not be loaded, it may be corrupted.  Exception %(exc)s' % {'game_history_filename': game_history_filename, 'exc': exc}, level=xbmc.LOGDEBUG)
		return games_dict

	def save_game_history(self,games_dict):
		game_history_filename = os.path.join(self.get_list_cache_path(),self.game_history_filename)
		try:
			with open(game_history_filename, 'wb') as fn:
				# Pickle the 'data' dictionary using the highest protocol available.
				# pickle.dump(games_dict, fn, pickle.HIGHEST_PROTOCOL)
				json.dump(games_dict,fn)
			xbmc.log(msg='IAGL:  Saving game history cache file', level=xbmc.LOGDEBUG)
		except Exception as exc: #except Exception, (exc):
			xbmc.log(msg='IAGL:  Unable to save game history cache file %(cache_filename)s.  Exception %(exc)s' % {'cache_filename': game_history_filename,'exc': exc}, level=xbmc.LOGERROR)
			try:
				xbmcvfs.delete(game_history_filename)
			except Exception as exc: #except Exception, (exc):
				xbmc.log(msg='IAGL Error:  The game history cache file may be corrupted.  Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)

	def add_game_to_history(self,json_in,game_list_id_in,game_id_in):
		cache_list_option = self.get_setting_as_bool(self.handle.getSetting(id='iagl_setting_cache_list'))
		total_in_history = int(self.handle.getSetting(id='iagl_setting_history'))
		if cache_list_option:
			# games_dict = self.load_game_history()
			games_dict = list()
			current_date, current_year = self.get_date_and_year(json_in.get('game').get('releasedate'), json_in.get('game').get('year'))
			current_tag = self.get_rom_tag(json_in.get('game').get('description'))
			current_trailer = self.get_trailer(json_in.get('game').get('videoid'))
			current_size = self.get_rom_size(json_in.get('game'))
			current_route = 'plugin://plugin.program.iagl/game/<game_list_id>/<game_id>'.replace('<game_list_id>',url_unquote(game_list_id_in)).replace('<game_id>',url_unquote(game_id_in))
			
			if type(json_in.get('game').get('rom')) is list: #Multiple files
				json_in['game']['rom'][0]['@name'] = current_route #Set route for history game item
				for ii in range(1,len(json_in['game']['rom'])):
					json_in['game']['rom'][ii]['@name'] = None #Nullify the other roms, only the route should remain
			else: #One file
				json_in['game']['rom']['@name'] = current_route #Set route for history game item
			games_dict.append({'values': {'label' : json_in.get('game').get('description'),
											'label2' : url_unquote(game_id_in),
								},
								'info': {'originaltitle' : json_in.get('game').get('@name'),
								'title' : json_in.get('game').get('description'),
								'plot' : json_in.get('game').get('plot'),
								'date' : current_date,
								'year' : current_year,
								'studio' : json_in.get('game').get('studio'),
								'genre' : json_in.get('game').get('genre'),
								'rating' : json_in.get('game').get('rating'),
								'mpaa' : json_in.get('game').get('ESRB'),
								'trailer' : current_trailer,
								'size' : current_size,
								},
								'art': {'poster' : self.choose_image(json_in.get('game').get('boxart1'),json_in.get('game').get('snapshot1'),self.default_thumb),
								'banner' : self.choose_image(json_in.get('game').get('banner1'),self.default_banner,None),
								'fanart' : self.choose_image(json_in.get('game').get('fanart1'),self.default_fanart,None),
								'clearlogo' : self.choose_image(json_in.get('game').get('clearlogo1'),None,None),
								'icon' : self.choose_image(json_in.get('game').get('clearlogo1'),json_in.get('game').get('clearlogo1'),None),
								'thumb' : self.choose_image(json_in.get('game').get('boxart1'),json_in.get('game').get('snapshot1'),self.default_thumb),
								},
								'properties': {'iagl_json' : json.dumps(json_in),
								'tag': current_tag,
								'nplayers': json_in.get('game').get('nplayers'),
								},
								})
			history_dict = self.load_game_history()
			current_history_routes = [x.get('values').get('label2') for x in history_dict]
			if games_dict[-1]['values']['label2'] in current_history_routes:
				history_dict.pop(current_history_routes.index(games_dict[-1]['values']['label2'])) #Remove the previous index of the same route
			if len(history_dict)>0:
				games_dict = games_dict+history_dict
			if len(games_dict)>total_in_history: #Only save up to the number in settings
				games_dict = games_dict[0:total_in_history]
			self.save_game_history(games_dict)
			xbmc.log(msg='IAGL:  %(game_title)s added to gameplay history' % {'game_title': json_in.get('game').get('description')}, level=xbmc.LOGDEBUG)

	def add_list_context_menus(self, listitem_in,game_list_id_in):
		current_context_menus = [(labels,actions.replace('<game_list_id>',game_list_id_in)) for labels, actions in self.context_menu_items]
		if listitem_in.getProperty('emu_launcher') == 'external':
			current_context_menus = current_context_menus+[(labels,actions.replace('<game_list_id>',game_list_id_in)) for labels, actions in self.context_menu_ext_launch_cmd]
		else:
			current_context_menus = current_context_menus+[(labels,actions.replace('<game_list_id>',game_list_id_in)) for labels, actions in self.context_menu_default_addon_launch_cmd]
		# if self.handle.getSetting(id='iagl_enable_post_dl_edit') == 'Enabled':
		if self.get_setting_as_bool(self.handle.getSetting(id='iagl_enable_post_dl_edit')):
			current_context_menus = current_context_menus+[(labels,actions.replace('<game_list_id>',game_list_id_in)) for labels, actions in self.context_menu_items_post_dl]
		if 'Favorites' in listitem_in.getProperty('emu_category') or 'favorites' in listitem_in.getProperty('emu_category'):
			current_context_menus = current_context_menus+[(labels,actions.replace('<game_list_id>',game_list_id_in)) for labels, actions in self.context_menu_items_favorites]
		
		listitem_in.addContextMenuItems(current_context_menus)
		return listitem_in

	def add_game_context_menus(self,listitem_in,game_list_id_in,game_id_in,current_categories):
		current_context_menus = []
		# if 'Info Page' not in self.handle.getSetting(id='iagl_setting_default_action'): #Old method pre language update
		if int(self.handle.getSetting(id='iagl_setting_default_action')) < 2: #If Info page is not the default, add context option for viewing the info page
			current_context_menus = current_context_menus+[(labels,actions.replace('<game_list_id>',game_list_id_in).replace('<game_id>',game_id_in)) for labels, actions in self.context_menu_item_view_info]
		if current_categories is not None and 'favorites' not in current_categories.lower():
			current_context_menus = current_context_menus+[(labels,actions.replace('<game_list_id>',game_list_id_in).replace('<game_id>',game_id_in)) for labels, actions in self.context_menu_items_games]
		if current_categories is not None and 'favorites' in current_categories.lower():
			current_context_menus = current_context_menus+[(labels,actions.replace('<game_list_id>',game_list_id_in).replace('<game_id>',game_id_in)) for labels, actions in self.context_menu_items_remove_favorite]
		listitem_in.addContextMenuItems(current_context_menus)
		return listitem_in

	def add_query_context_menus(self,listitem_in,query_id_in):
		current_context_menus = [(labels,actions.replace('<query_id>',query_id_in)) for labels, actions in self.context_menu_items_query]
		listitem_in.addContextMenuItems(current_context_menus)
		return listitem_in

	def get_user_context_choice(self, setting_id):
		current_key = None
		current_choice = None
		if setting_id == 'metadata':
			current_dialog = xbmcgui.Dialog()
			ret1 = current_dialog.select(self.loc_str(30331),self.context_menu_metadata_choices)
			del current_dialog
			if ret1 > -1:
				current_key = self.context_menu_metadata_keys[ret1]
				current_choice = self.context_menu_metadata_choices[ret1]
			else:
				current_key = None
		elif setting_id == 'art':
			current_dialog = xbmcgui.Dialog()
			ret1 = current_dialog.select(self.loc_str(30332),self.context_menu_art_choices)
			del current_dialog
			if ret1 > -1:
				current_key = self.context_menu_art_keys[ret1]
				current_choice = self.context_menu_art_choices[ret1]
			else:
				current_key = None
		elif setting_id == 'visibility':
			current_key = 'emu_visibility'
			current_choice = 'Visibility'
		elif setting_id == 'launcher':
			current_key = 'emu_launcher'
			current_choice = 'Launcher'
		elif setting_id == 'launch_command':
			current_key = 'emu_ext_launch_cmd'
			current_choice = 'Launch Command'
		elif setting_id == 'default_addon':
			current_key = 'emu_default_addon'
			current_choice = 'Default Game Addon'
		elif setting_id == 'download_path':
			current_key = 'emu_downloadpath'
			current_choice = 'Download Path'
		elif setting_id == 'post_dl_command':
			current_key = 'emu_postdlaction'
			current_choice = 'Post DL Command'
		elif setting_id == 'view_list_settings':
			current_key = 'view_list_settings'
			current_choice = None
		elif setting_id == 'refresh_list':
			current_key = 'refresh_list'
			current_choice = None
		elif setting_id == 'view_info_page':
			current_key = 'view_info_page'
			current_choice = None
		else:
			xbmc.log(msg='IAGL:  Unknown context menu setting  %(setting_id)s' % {'setting_id': setting_id}, level=xbmc.LOGERROR)
		return current_choice, current_key

	def get_user_context_entry(self, current_key, old_value, current_choice):
		if current_key == 'emu_trailer':
			if 'plugin.video.youtube' in old_value:
				old_value = old_value.split('=')[-1]

		new_value = None
		current_dialog = xbmcgui.Dialog()
		if current_key == 'emu_launcher':
			ret1 = current_dialog.select(self.loc_str(30333), [self.loc_str(30205),self.loc_str(30206)])
			if ret1 > -1:
				new_value = ['retroplayer','external'][ret1]
		elif current_key == 'emu_visibility':
			ret1 = current_dialog.select(self.loc_str(30334), [self.loc_str(30204),self.loc_str(30200)])
			if ret1 > 0:
				new_value = ['visible','hidden'][ret1]
		elif current_key == 'emu_postdlaction':
			ret1 = current_dialog.select(self.loc_str(30335),self.post_dl_actions)
			if ret1 > -1:
				new_value = self.post_dl_action_keys[ret1]
		elif current_key == 'emu_downloadpath':
			ret1 = current_dialog.select(self.loc_str(30336), [self.loc_str(30207),self.loc_str(30208)])
			if ret1 > -1:
				if ret1 == 0:
					new_value = 'default'
				else:
					try:
						new_value = current_dialog.browse(0,self.loc_str(30337),'')
					except Exception as exc: #except Exception, (exc):
						xbmc.log(msg='IAGL:  Unable to browse default location, trying files source.  Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGDEBUG)
						new_value = current_dialog.browse(0,self.loc_str(30337),'files')
					if len(new_value)<1:
						new_value = None
		elif current_key == 'emu_default_addon':
			addons_available = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Addons.GetAddons","params":{"type":"kodi.gameclient"}, "id": "1"}')
			if '"error"' not in addons_available:
				# dont_include_these_addons = ['game.libretro','game.libretro.2048','game.libretro.dinothawr','game.libretro.mrboom']
				current_game_addon_values = [x.get('addonid') for x in json.loads(addons_available).get('result').get('addons') if x.get('type') == 'kodi.gameclient' and x.get('addonid') not in self.ignore_these_game_addons]
				current_game_addon_choices = [xbmcaddon.Addon(id='%(addon_name)s' % {'addon_name':x}).getAddonInfo('name') for x in current_game_addon_values]
				current_game_addon_values = ['none']+[current_game_addon_values[x] for x in sorted(range(len(current_game_addon_choices)), key=lambda k: current_game_addon_choices[k])]
				current_game_addon_choices = [self.loc_str(30338)]+[current_game_addon_choices[x] for x in sorted(range(len(current_game_addon_choices)), key=lambda k: current_game_addon_choices[k])]
				# current_game_addon_values = ['none']+current_game_addon_values
				# current_game_addon_choices = ['Auto']+current_game_addon_choices
				ret1 = current_dialog.select(self.loc_str(30339), current_game_addon_choices)
				if ret1 > -1:
					new_value = current_game_addon_values[ret1]
			else:
				new_value = None
				xbmc.log(msg='IAGL:  The Kodi default game addon cannot be updated because none were found.', level=xbmc.LOGDEBUG)
		elif current_key == 'emu_ext_launch_cmd':
			current_external_environment = self.handle.getSetting(id='iagl_external_user_external_env')
			if current_external_environment == 'Select':
				ok_ret = current_dialog.ok(self.loc_str(30203),self.loc_str(30340))
			else:
				if self.get_setting_as_bool(self.handle.getSetting(id='iagl_external_launch_close_kodi')):
					if current_external_environment in ['OSX','Linux/Kodibuntu','Windows']: #Close Kodi option only available for these systems
						current_ext_key = current_external_environment+' Close_Kodi'
					else:
						current_ext_key = current_external_environment
				elif self.get_setting_as_bool(self.handle.getSetting(id='iagl_external_launch_pause_kodi')):
					if current_external_environment in ['Linux/Kodibuntu']: #Pause Kodi option only available for these systems
						current_ext_key = current_external_environment+' Pause_Kodi'
					else:
						current_ext_key = current_external_environment
				else:
					current_ext_key = current_external_environment
				current_external_command_db = self.get_external_command_listing()
				current_external_command_choices = [x.get('@name') for x in current_external_command_db.get('system').get('launcher') if x.get('@os') == current_ext_key]
				current_external_command_values = [x.get('launcher_command') for x in current_external_command_db.get('system').get('launcher') if x.get('@os') == current_ext_key]
				current_external_command_choices = current_external_command_choices+['Manually Input Command']
				current_external_command_values = current_external_command_values+['manual_command']
				ret1 = current_dialog.select(self.loc_str(30341), current_external_command_choices)
				if ret1 > -1:
					new_value = current_external_command_values[ret1]
				if new_value == 'manual_command':
					new_value = current_dialog.input(self.loc_str(30342))
		elif current_key == 'emu_category':
			new_value = current_dialog.input(self.loc_str(30343) % {'current_choice':current_choice},old_value)
			if len(new_value)<1: #User hit cancel
				new_value = None
			if new_value == old_value: #User didnt change the value
				new_value = None
			if new_value is not None:
				if 'favorites' in old_value.lower() and 'favorites' not in new_value.lower():
					xbmc.log(msg='IAGL:  Favorites list category was updated to include the Favorites keyword', level=xbmc.LOGDEBUG)
					new_value = new_value+', Favorites' #Favories must remain in favorites
		else:
			new_value = current_dialog.input(self.loc_str(30343) % {'current_choice':current_choice},old_value)
			if len(new_value)<1: #User hit cancel
				new_value = None
			if new_value == old_value: #User didnt change the value
				new_value = None

		if current_key == 'emu_trailer':
			if new_value is not None and 'youtube.com' in new_value:
				new_value = new_value.split('=')[-1]

		if new_value is not None:
			ret2 = current_dialog.select(self.loc_str(30344) % {'current_choice':current_choice}, [self.loc_str(30200),self.loc_str(30201)])
			if ret2 != 0:
				new_value = None
		del current_dialog
		return new_value

	def update_xml_header(self,current_filename,current_key,new_value,silent_update=False):

		starting_tag = '<%(current_key)s>'%{'current_key':current_key}
		ending_tag = '</%(current_key)s>'%{'current_key':current_key}
		file_ending_tag = '</datafile>'

		new_value_line = '<%(current_key)s>%(new_value)s</%(current_key)s>'%{'current_key':current_key,'new_value':new_value.replace('\r\n','[CR]').replace('\r','[CR]').replace('\n','[CR]')}
		value_updated = False
		last_line_written = False

		with open(current_filename,'r') as input_file, open(os.path.join(self.get_dat_folder_path(),'temp.xml'), 'w') as output_file:
			for line in input_file:
				if not value_updated:  #Only update the first instance of the requested tag
					if starting_tag in line and ending_tag in line:
						try:
							output_file.write('%(start_value)s%(new_value)s%(end_value)s' % {'start_value': line.split(starting_tag)[0], 'new_value': new_value_line, 'end_value':line.split(ending_tag)[-1]})
							value_updated = True
							if file_ending_tag in line:  #Of course android does something totally unexpected with standard python code
								last_line_written = True
						except Exception as exc1: #except Exception, (exc):
							try:
								xbmc.log(msg='IAGL:  XML %(current_filename)s write error.  Exception %(exc)s.  Attempting to write again.' % {'current_filename': current_filename, 'exc': exc1}, level=xbmc.LOGERROR)
								output_file.write(new_value_line)
								value_updated = True
								if file_ending_tag in line:  #Of course android does something totally unexpected with standard python code
									last_line_written = True
							except Exception as exc2: #except Exception, (exc):
								value_updated = False
								xbmc.log(msg='IAGL:  XML %(current_filename)s write error.  Exception %(exc)s' % {'current_filename': current_filename, 'exc': exc2}, level=xbmc.LOGERROR)
					else:
						output_file.write(line)
						if file_ending_tag in line:
							last_line_written = True
				else:
					output_file.write(line)
					if file_ending_tag in line:
						last_line_written = True

		if value_updated and last_line_written: #Success
			if xbmcvfs.delete(current_filename): #Current file was deleted
				if xbmcvfs.rename(os.path.join(self.get_dat_folder_path(),'temp.xml'),current_filename):
					xbmc.log(msg='IAGL:  XML %(current_filename)s updated with value %(new_value)s' % {'current_filename': os.path.split(current_filename)[-1], 'new_value': new_value}, level=xbmc.LOGDEBUG)
					xbmcvfs.delete(os.path.join(self.get_list_cache_path(),self.dat_file_cache_filename)) #Delete dat file cache
					if self.delete_list_cache(os.path.splitext(os.path.split(current_filename)[-1])[0]):
						if not silent_update:
							current_dialog = xbmcgui.Dialog()
							ok_ret = current_dialog.notification(self.loc_str(30202),self.loc_str(30345) % {'current_filename': os.path.splitext(os.path.split(current_filename)[-1])[0]},xbmcgui.NOTIFICATION_INFO,self.notification_time)
							del current_dialog
					else: #Delete list file cache
						if not silent_update:
							current_dialog = xbmcgui.Dialog()
							ok_ret = current_dialog.notification(self.loc_str(30202),self.loc_str(30346) % {'current_filename': os.path.splitext(os.path.split(current_filename)[-1])[0]},xbmcgui.NOTIFICATION_INFO,self.notification_time)
							del current_dialog
				else:
					xbmc.log(msg='IAGL:  Temporary XML file could not be renamed.  How on earth did you get here?', level=xbmc.LOGDEBUG)
			else: #Cant delete the existing file
				xbmc.log(msg='IAGL:  XML %(current_filename)s could not be updated.  It is likely open in another application and not writeable.' % {'current_filename': os.path.split(current_filename)[-1], 'new_value': new_value}, level=xbmc.LOGDEBUG)
				if xbmcvfs.exists(os.path.join(self.get_dat_folder_path(),'temp.xml')):
					if not xbmcvfs.delete(os.path.join(self.get_dat_folder_path(),'temp.xml')):
						xbmc.log(msg='IAGL:  Temporary XML file could not be deleted.', level=xbmc.LOGDEBUG)
		else:
			if xbmcvfs.exists(os.path.join(self.get_dat_folder_path(),'temp.xml')):
				if not xbmcvfs.delete(os.path.join(self.get_dat_folder_path(),'temp.xml')):
					xbmc.log(msg='IAGL:  Temporary XML file could not be deleted.', level=xbmc.LOGDEBUG)
			current_dialog = xbmcgui.Dialog()
			ok_ret = current_dialog.notification(self.loc_str(30203),'Error updating %(current_filename)s, see log' % {'current_filename': os.path.splitext(os.path.split(current_filename)[-1])[0]},xbmcgui.NOTIFICATION_INFO,self.notification_time)
			del current_dialog
			if not value_updated:
				xbmc.log(msg='IAGL:  XML %(current_filename)s was not updated.  The tag %(current_key)s could not be located.' % {'current_filename': os.path.split(current_filename)[-1], 'current_key': current_key}, level=xbmc.LOGERROR)
			if not last_line_written:
				xbmc.log(msg='IAGL:  XML %(current_filename)s was not updated.  The file ending tag was never written.' % {'current_filename': os.path.split(current_filename)[-1]}, level=xbmc.LOGERROR)

	def add_game_to_IAGL_favorites(self,game_list_id_in,game_id_in,json_in):
		current_favorites_lists = self.get_list_of_favorites_lists()
		if type(current_favorites_lists['emu_name']) == list:
			current_list_choices = [x for x in current_favorites_lists.get('emu_name')]+[self.loc_str(30347)]
			current_list_values = [x for x in current_favorites_lists.get('fullpath')]+['create_new_list']
		else:
			current_list_choices = current_favorites_lists['emu_name']+[self.loc_str(30347)]
			current_list_values = current_favorites_lists['fullpath']+['create_new_list']
		
		current_dialog = xbmcgui.Dialog()
		ret1 = current_dialog.select(self.loc_str(30349), current_list_choices)
		if ret1 > -1:
			new_value = current_list_values[ret1]
			if new_value == 'create_new_list':
				if self.kodi_username.lower() == 'master user':
					default_fav_name = self.loc_str(30348) % {'default_number':len(current_list_values)}
				else:
					default_fav_name = self.loc_str(30350) % {'current_username':self.kodi_username, 'default_number':len(current_list_values)}
				ret2 = current_dialog.input(self.loc_str(30351),default_fav_name)
				if len(ret2)>0:
					new_favorites_filename = os.path.join(self.get_dat_folder_path(),clean_file_folder_name(ret2)+'.xml')
					if new_favorites_filename not in current_list_values:
						if xbmcvfs.copy(self.get_favorites_template_file(),new_favorites_filename): #Copy the template to the dat folder
							self.update_xml_header(new_favorites_filename,'emu_name',ret2,True) #Update name of the list to the name entered by the user
							self.add_game_to_xml(new_favorites_filename,game_list_id_in,game_id_in,json_in)  #Add the game to the file
						else:
							xbmc.log(msg='IAGL:  Unable to create favorites file %(current_filename)s' % {'current_filename': new_favorites_filename}, level=xbmc.LOGERROR)
					else:
						xbmc.log(msg='IAGL:  Error, the entered favorites name %(current_filename)s already exists.' % {'current_filename': new_favorites_filename}, level=xbmc.LOGERROR)
			else:
				self.add_game_to_xml(new_value,game_list_id_in,game_id_in,json_in)  #Add the game to the file
		del current_dialog

	def add_game_to_xml(self,filename_in,game_list_id_in,game_id_in,json_in):
		xbmc.log(msg='IAGL:  Adding game %(game_id_in)s to favorites list %(filename_in)s'%{'game_id_in':url_unquote(game_id_in),'filename_in':os.path.split(filename_in)[-1]}, level=xbmc.LOGDEBUG)
		favorite_dict = dict()
		favorite_dict['games'] = dict()
		favorite_dict['games']['game'] = json.loads(json_in).get('game')
		if favorite_dict['games']['game'] is not None:
			if game_list_id_in == 'query':
				if game_id_in == 'search':
					current_route = 'plugin://plugin.program.iagl/run_search/1/?'+favorite_dict['games']['game']['rom']['@name']
				else:
					current_route = 'plugin://plugin.program.iagl/run_random/1/?'+favorite_dict['games']['game']['rom']['@name']
			else:
				current_route = 'plugin://plugin.program.iagl/game/<game_list_id>/<game_id>'.replace('<game_list_id>',game_list_id_in).replace('<game_id>',game_id_in)
			current_size = self.get_rom_size(favorite_dict['games']['game'])
			if self.handle.getSetting(id='iagl_favorites_format') == 'Use Hyperlinks to other Lists': #Replace current game data with plugin route URL
				favorite_dict['games']['game']['rom'] = dict()
				favorite_dict['games']['game']['rom']['@name'] = current_route
				if current_size is not None:
					favorite_dict['games']['game']['rom']['@size'] = str(current_size)
			if self.handle.getSetting(id='iagl_favorites_format') == 'Copies all Data, adds Post DL Command Override': #Add post DL override command to the game based on current emu Post DL command
				current_post_dl_command = json.loads(json_in).get('emu').get('emu_postdlaction')
				if current_post_dl_command is not None and current_post_dl_command != 'none' and len(current_post_dl_command)>0:
					favorite_dict['games']['game']['rom_override_postdl'] = current_post_dl_command
			current_game_name = favorite_dict['games']['game'].get('@name')
			favorite_xml = ET.tostring(dict_to_etree(favorite_dict))
			crc_string = get_crc32_from_string(''.join([x.encode('utf-8',errors='ignore') for x in sorted(favorite_dict['games']['game'].values()) if type(x) is str or type(x) is unicode])) #Create a repeatable crc string to look for in the event the user attempts to delete the game from the list later
			if '<games>' in favorite_xml and '</games>' in favorite_xml:
				favorite_header = '<!-- IAGL Favorite XXXCRCXXX -->'.replace('XXXCRCXXX',crc_string)
				favorite_xml = favorite_xml.replace('<games>',favorite_header).replace('</games>',favorite_header).replace('><','>\r\n\t\t<').replace('\t\t<game ','\t<game ').replace('\t\t</game>','\t</game>').replace('\t\t<!--','<!--')+'\r\n</datafile>'
				favorite_xml = favorite_xml.replace('\n\n','\n').replace('\r\r','\r') #Remove extra newlines
				value_updated = False
				with open(filename_in,'r') as input_file, open(os.path.join(self.get_dat_folder_path(),'temp.xml'), 'w') as output_file:
					for line in input_file:
						if not value_updated:  #Only update the first instance of the requested tag
							if '</datafile>' in line:
								try:
									output_file.write(favorite_xml)
									value_updated = True
								except Exception as exc: #except Exception, (exc):
									value_updated = False
									xbmc.log(msg='IAGL:  Favorites XML %(current_filename)s write error.  Exception %(exc)s' % {'current_filename': filename_in, 'exc': exc}, level=xbmc.LOGERROR)
							else:
								output_file.write(line)
						else:
							output_file.write(line)
				if value_updated: #Success
					if xbmcvfs.delete(filename_in): #Current file was deleted
						if xbmcvfs.rename(os.path.join(self.get_dat_folder_path(),'temp.xml'),filename_in):
							xbmc.log(msg='IAGL:  Favorites XML %(current_filename)s updated with game %(new_value)s' % {'current_filename': os.path.split(filename_in)[-1], 'new_value': current_game_name}, level=xbmc.LOGDEBUG)
							xbmcvfs.delete(os.path.join(self.get_list_cache_path(),self.dat_file_cache_filename)) #Delete dat file cache
							if self.delete_list_cache(os.path.splitext(os.path.split(filename_in)[-1])[0]):
								current_dialog = xbmcgui.Dialog()
								ok_ret = current_dialog.notification(self.loc_str(30202),self.loc_str(30352) % {'current_game': current_game_name,'current_filename': os.path.splitext(os.path.split(filename_in)[-1])[0]},xbmcgui.NOTIFICATION_INFO,self.notification_time)
								del current_dialog
							else: #Delete list file cache
								current_dialog = xbmcgui.Dialog()
								ok_ret = current_dialog.notification(self.loc_str(30202),self.loc_str(30353) % {'current_game': current_game_name, 'current_filename': os.path.splitext(os.path.split(filename_in)[-1])[0]},xbmcgui.NOTIFICATION_INFO,self.notification_time)
								del current_dialog
						else:
							xbmc.log(msg='IAGL:  Temporary XML file could not be renamed.  How on earth did you get here?', level=xbmc.LOGDEBUG)
					else: #Cant delete the existing file
						xbmc.log(msg='IAGL:  XML %(current_filename)s could not be updated.  It is likely open in another application and not writeable.' % {'current_filename': os.path.split(filename_in)[-1]}, level=xbmc.LOGDEBUG)
						if xbmcvfs.exists(os.path.join(self.get_dat_folder_path(),'temp.xml')):
							if not xbmcvfs.delete(os.path.join(self.get_dat_folder_path(),'temp.xml')):
								xbmc.log(msg='IAGL:  Temporary XML file could not be deleted.', level=xbmc.LOGDEBUG)
				else:
					if xbmcvfs.exists(os.path.join(self.get_dat_folder_path(),'temp.xml')):
						if not xbmcvfs.delete(os.path.join(self.get_dat_folder_path(),'temp.xml')):
							xbmc.log(msg='IAGL:  Temporary XML file could not be deleted.', level=xbmc.LOGDEBUG)
					xbmc.log(msg='IAGL:  Favorites XML %(current_filename)s was not updated.' % {'current_filename': os.path.split(filename_in)[-1]}, level=xbmc.LOGERROR)

	def remove_game_from_IAGL_favorites(self,game_list_id_in,game_id_in,json_in):
		current_dialog = xbmcgui.Dialog()
		ret1 = current_dialog.select(self.loc_str(30354) % {'game_id_in':url_unquote(game_id_in),'game_list_id_in':url_unquote(game_list_id_in)}, [self.loc_str(30200),self.loc_str(30201)])
		if ret1 == 0:
			favorite_dict = dict()
			favorite_dict['games'] = dict()
			favorite_dict['games']['game'] = json.loads(json_in).get('game')
			crc_string = get_crc32_from_string(''.join([x.encode('utf-8',errors='ignore') for x in sorted(favorite_dict['games']['game'].values()) if type(x) is str or type(x) is unicode])) #Create a repeatable crc string to look for in the event the user attempts to delete the game from the list later
			current_filename = os.path.join(self.get_dat_folder_path(),url_unquote(game_list_id_in)+'.xml')
			file_contents = None
			if xbmcvfs.exists(current_filename):
				with closing(xbmcvfs.File(current_filename)) as content_file:
					byte_string = bytes(content_file.readBytes())
				try:
					file_contents = byte_string.decode('utf-8',errors='ignore')
				except:
					file_contents = None
				if file_contents is not None:
					new_file_list = file_contents.split('<!-- IAGL Favorite XXXCRCXXX -->'.replace('XXXCRCXXX',crc_string))
					if type(new_file_list) == list and len(new_file_list) == 3: #Favorite crc was found
						new_file_contents = new_file_list[0]+new_file_list[-1] #Combine the two parts of the file without the favorite
						new_file_contents = new_file_contents.replace('\r\n\r\n','\r\n').replace('\n\n','\n').replace('\r\r','\r')
						with closing(xbmcvfs.File(os.path.join(self.get_dat_folder_path(),'temp.xml'),'w')) as content_file:
							content_file.write(new_file_contents)
						if xbmcvfs.exists(os.path.join(self.get_dat_folder_path(),'temp.xml')): #If the temp file was written
							if xbmcvfs.delete(current_filename): #and the old favorites xml can be deleted
								if xbmcvfs.rename(os.path.join(self.get_dat_folder_path(),'temp.xml'),current_filename): #rename the temp file to the favorites xml
									xbmc.log(msg='IAGL:  Game %(game_id_in)s removed from XML %(current_filename)s' % {'game_id_in': game_id_in, 'current_filename': os.path.split(current_filename)[-1]}, level=xbmc.LOGDEBUG)
									xbmcvfs.delete(os.path.join(self.get_list_cache_path(),self.dat_file_cache_filename)) #Delete dat file cache
									if self.delete_list_cache(os.path.splitext(os.path.split(current_filename)[-1])[0]):
										current_dialog = xbmcgui.Dialog()
										ok_ret = current_dialog.notification(self.loc_str(30202),self.loc_str(30345) % {'current_filename': os.path.splitext(os.path.split(current_filename)[-1])[0]},xbmcgui.NOTIFICATION_INFO,self.notification_time)
									else: #Delete list file cache
										current_dialog = xbmcgui.Dialog()
										ok_ret = current_dialog.notification(self.loc_str(30202),self.loc_str(30346) % {'current_filename': os.path.splitext(os.path.split(current_filename)[-1])[0]},xbmcgui.NOTIFICATION_INFO,self.notification_time)
								else:
									xbmc.log(msg='IAGL:  Temporary XML file could not be renamed.  How on earth did you get here?', level=xbmc.LOGDEBUG)
							else:
								xbmc.log(msg='IAGL:  The favorites XML could not be deleted.  How on earth did you get here?', level=xbmc.LOGDEBUG)
						else:
							xbmc.log(msg='IAGL:  Temporary XML file could not be found.  How on earth did you get here?', level=xbmc.LOGDEBUG)
					else:
						xbmc.log(msg='IAGL Error:  Unable to find the favorite CRC in %(game_list_id_in)s' % {'game_list_id_in': game_list_id_in}, level=xbmc.LOGERROR)
			else:
				xbmc.log(msg='IAGL Error:  Unable to find the favorites file %(current_filename)s' % {'current_filename': current_filename}, level=xbmc.LOGERROR)
		del current_dialog

	def get_list_settings_text(self,current_game_list):
		launch_command_string = ''
		if current_game_list.get('emu_launcher') == 'retroplayer':
			if current_game_list.get('emu_default_addon') == 'none':
				launch_command_string = '[COLOR FF12A0C7]Launch Using Addon: [/COLOR]Auto (choose from list)'
			else:
				launch_command_string = '[COLOR FF12A0C7]Launch Using Addon: [/COLOR]%(emu_default_addon)s'%{'emu_default_addon':current_game_list.get('emu_default_addon')}
		else:
			launch_command_string = '[COLOR FF12A0C7]Launch with Command: [/COLOR]%(emu_ext_launch_cmd)s'%{'emu_ext_launch_cmd':current_game_list.get('emu_ext_launch_cmd')}
		download_parameter_string = ''
		if current_game_list.get('emu_downloadpath') == 'default':
			download_parameter_string = '[COLOR FF12A0C7]Download Path: [/COLOR]Addon Default'
		else:
			download_parameter_string = '[COLOR FF12A0C7]Download Path: [/COLOR]%(emu_downloadpath)s'%{'emu_downloadpath':xbmc.translatePath(current_game_list.get('emu_downloadpath'))}
		try:
			if 'launch_mame_softlist' in current_game_list.get('emu_postdlaction'):
				current_action_text = self.post_dl_actions[self.post_dl_action_keys.index(current_game_list.get('emu_postdlaction').split('(')[0])]+'[CR][COLOR FF12A0C7]Using: [/COLOR]%(mame_mess_choice)s  [COLOR FF12A0C7]Softlist: [/COLOR]%(softlist_choice)s'%{'mame_mess_choice':current_game_list.get('emu_postdlaction').split('(')[-1].split(')')[0].split(',')[0].replace("'",''),'softlist_choice':current_game_list.get('emu_postdlaction').split('(')[-1].split(')')[0].split(',')[-1].replace("'",'')}
			else:
				current_action_text = self.post_dl_actions[self.post_dl_action_keys.index(current_game_list.get('emu_postdlaction').split('(')[0])]
		except:
			current_action_text = None
		if current_action_text is not None:
			download_parameter_string = download_parameter_string+'[CR][COLOR FF12A0C7]Post Download Command: [/COLOR]%(current_action_text)s'%{'current_action_text':current_action_text}
		current_header = 'Settings for %(game_list_id)s'%{'game_list_id':current_game_list.get('game_list_id')}
		# current_text = '[B]Metadata[/B][CR][COLOR FF12A0C7]Game List Name: [/COLOR]%(emu_name)s[CR][COLOR FF12A0C7]Categories: [/COLOR]%(emu_category)s[CR][COLOR FF12A0C7]Platform: [/COLOR]%(emu_description)s[CR][COLOR FF12A0C7]Summary: [/COLOR]%(emu_comment)s[CR][COLOR FF12A0C7]Author: [/COLOR]%(emu_author)s[CR][COLOR FF12A0C7]Trailer: [/COLOR]%(emu_trailer)s[CR][COLOR FF12A0C7]Date: [/COLOR]%(emu_date)s[CR][B]Download Parameters[/B][CR][COLOR FF12A0C7]Download Path: [/COLOR]%(emu_downloadpath)s[CR][COLOR FF12A0C7]Post Download Command: [/COLOR]%(emu_postdlaction)s[CR][B]Launch Parameters[/B][CR][COLOR FF12A0C7]Launch With: [/COLOR]%(emu_launcher)s[CR]%(launch_command_string)s'%{'emu_name':current_game_list.get('emu_name'),'emu_category':current_game_list.get('emu_category'),'emu_description':current_game_list.get('emu_description'),'emu_comment':current_game_list.get('emu_comment'),'emu_author':current_game_list.get('emu_author'),'emu_trailer':current_game_list.get('emu_trailer'),'emu_date':current_game_list.get('emu_date'),'emu_downloadpath':current_game_list.get('emu_downloadpath'),'emu_postdlaction':current_game_list.get('emu_postdlaction'),'emu_launcher':current_game_list.get('emu_launcher'),'launch_command_string':launch_command_string}
		current_text = '[B]Metadata[/B][CR][COLOR FF12A0C7]Game List Name: [/COLOR]%(emu_name)s[CR][COLOR FF12A0C7]Categories: [/COLOR]%(emu_category)s[CR][COLOR FF12A0C7]Platform: [/COLOR]%(emu_description)s[CR][COLOR FF12A0C7]Author: [/COLOR]%(emu_author)s[CR][CR][B]Download Parameters[/B][CR]%(download_parameter_string)s[CR][CR][B]Launch Parameters[/B][CR][COLOR FF12A0C7]Launch With: [/COLOR]%(emu_launcher)s[CR]%(launch_command_string)s'%{'emu_name':current_game_list.get('emu_name'),'emu_category':current_game_list.get('emu_category'),'emu_description':current_game_list.get('emu_description'),'emu_comment':current_game_list.get('emu_comment'),'emu_author':current_game_list.get('emu_author'),'emu_trailer':current_game_list.get('emu_trailer'),'emu_date':current_game_list.get('emu_date'),'download_parameter_string':download_parameter_string,'emu_launcher':current_game_list.get('emu_launcher'),'launch_command_string':launch_command_string}
		xbmcgui.Window(10000).setProperty('TextViewer_Header',current_header)
		xbmcgui.Window(10000).setProperty('TextViewer_Text',current_text)

	def get_trailer(self, video_id_in):
		video_id_out = None
		try:
			if video_id_in is not None and len(video_id_in)>0:
				if 'http' in video_id_in:
					video_id_out = video_id_in
				else:
					video_id_out = self.youtube_plugin_url % {'vid': video_id_in}
		except Exception as exc: #except Exception, (exc):
			xbmc.log(msg='IAGL Error:  Unable to parse videoid %(video_id_in)s.  Exception %(exc)s' % {'video_id_in': video_id_in, 'exc': exc}, level=xbmc.LOGERROR)

		return video_id_out

	def get_current_time(self):
		date_time_out = None
		try:
			date_time_out = str(time.strftime(self.listitem_date_format,time.localtime()))
		except Exception as exc: #except Exception, (exc):
			date_time_out = '???'
			xbmc.log(msg='IAGL Error:  Unable to get local time as string.  Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGDEBUG)
		return date_time_out

	def get_random_time(self):
		date_time_out = None
		try:
			date_time_out = str(time.strftime('%d%H%M%S',time.localtime()))
		except Exception as exc: #except Exception, (exc):
			date_time_out = '???'
			xbmc.log(msg='IAGL Error:  Unable to get random local time as string.  Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGDEBUG)
		return date_time_out

	def get_date(self, date_in):
		date_out = date_in
		try:
			if date_in is not None and len(date_in)>0:
				date_out = str(date_parser.parse(date_in).strftime(self.listitem_date_format))
		except Exception as exc: #except Exception, (exc):
			xbmc.log(msg='IAGL Error:  Unable to parse date %(date_in)s.  Exception %(exc)s' % {'date_in': date_in, 'exc': exc}, level=xbmc.LOGERROR)

		return date_out

	def get_label_date(self, date_in):
		date_out = date_in
		try:
			if date_in is not None and len(date_in)>0:
				date_out = str(date_parser.parse(date_in,dayfirst=True).strftime(self.display_date_format))
		except Exception as exc: #except Exception, (exc):
			xbmc.log(msg='IAGL Error:  Unable to parse display date %(date_in)s.  Exception %(exc)s' % {'date_in': date_in, 'exc': exc}, level=xbmc.LOGERROR)
		return date_out

	def get_date_and_year(self, date_in, year_in):
		try:
			if date_in is not None and len(date_in)>0:
				date_out = str(date_parser.parse(date_in).strftime(self.listitem_date_format))
			elif year_in is not None and len(year_in)>0:
				date_out = str(date_parser.parse('01/01/%(year_in)s' % {'year_in': year_in}).strftime(self.listitem_date_format)) #If no release date is available, but year is available, make the date 01/01/YYYY
			else:
				date_out = None
		except Exception as exc: #except Exception, (exc):
			date_out = None
			xbmc.log(msg='IAGL Error:  Unable to parse date %(date_in)s.  Exception %(exc)s' % {'date_in': date_in, 'exc': exc}, level=xbmc.LOGERROR)
		try:
			if year_in is not None and len(year_in)>0:
				year_out = year_in
			elif date_in is not None and len(date_in)>0:
				year_out = str(date_parser.parse(date_in).strftime(self.year_format))
			else:
				year_out = None
		except Exception as exc: #except Exception, (exc):
			year_out = None
			xbmc.log(msg='IAGL Error:  Unable to parse year %(year_in)s.  Exception %(exc)s' % {'year_in': date_in, 'exc': exc}, level=xbmc.LOGERROR)

		return date_out, year_out

	def get_rom_size(self, dict_in):
		size_out = None
		try:
			# if 'rom' in dict_in.keys():
			if type(dict_in.get('rom')) is list: #Multiple files
				size_out = sum(map(int,[x['@size'] for x in dict_in['rom'] if x.get('@size') is not None]))
			else: #One file
				# if '@size' in dict_in['rom'].keys() and dict_in['rom']['@size'] is not None:
				if dict_in['rom'].get('@size') is not None:
					size_out = int(dict_in['rom']['@size'])
		except Exception as exc: #except Exception, (exc):
			xbmc.log(msg='IAGL Error:  Error calculating game size.  Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)

		return size_out

	def get_rom_filenames(self, base_url_in, dict_in):
		filenames_out = None
		try:
			if type(dict_in.get('rom')) is list: #Multiple files
				filenames_out = [base_url_in+x['@name'] for x in dict_in['rom'] if x.get('@name') is not None]
			else: #One file
				if dict_in['rom'].get('@name') is not None:
					filenames_out = [base_url_in+dict_in['rom']['@name']]
		except Exception as exc: #except Exception, (exc):
			xbmc.log(msg='IAGL Error:  Error finding rom filenames.  Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)

		return filenames_out

	def get_rom_filename_sizes(self, dict_in):
		sizes_out = list()
		try:
			if type(dict_in.get('rom')) is list: #Multiple files
				for ss in [x.get('@size') for x in dict_in['rom']]:
					if ss is not None:
						sizes_out.append(str(ss))
					else:
						sizes_out.append('0') #Unknown size, so make it 0
			else: #One file
				if dict_in['rom'].get('@size') is not None:
					sizes_out = [str(dict_in['rom']['@size'])]
				else:
					sizes_out = ['0'] #Unknown size, so make it 0
		except Exception as exc: #except Exception, (exc):
			xbmc.log(msg='IAGL Error:  Error calculating game size.  Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)

		return sizes_out

	def bytes_to_string_size(self, num, suffix='B'):
		if num is not None:
			num_sum = sum(map(int,[num,.001]))
			for unit in ['','k','M','G','T','P','E','Z']:
				if abs(num_sum) < 1024.0:
					return '%3.1f%s%s' % (num_sum, unit, suffix)
				num_sum /= 1024.0
			return str('%.1f%s%s') % (num_sum, 'Yi', suffix)
		else:
			return '0'

	def get_crc32_from_list_id(self,list_id_in):
		if list_id_in == 'game_history':
			return 'game_history'
		else:
			return get_crc32(os.path.join(self.get_dat_folder_path(),list_id_in+'.xml'))

	def get_clean_label(self, label_in, option_in):
		label_out = label_in
		try:
			if label_in is not None and len(label_in)>0:
				if option_in:
					label_out = self.clean_game_tags.sub('',label_in).strip()
				else:
					label_out = label_in
		except Exception as exc: #except Exception, (exc):
			xbmc.log(msg='IAGL Error:  Unable to clean label %(label_in)s.  Exception %(exc)s' % {'label_in': label_in, 'exc': exc}, level=xbmc.LOGERROR)

		return label_out

	def get_rom_tag(self, label_in):
		label_out = None
		try:
			if label_in is not None and len(label_in)>0:
				if '(' in label_in and ')' in label_in: #Tag found
					label_out = self.clean_game_tags.search(label_in).group(0).replace('(','').replace(')','').strip()
				else:
					label_out = None #No Tag
			else:
				label_out = None #No Label
		except Exception as exc: #except Exception, (exc):
			xbmc.log(msg='IAGL Error:  Unable to find game tag for %(label_in)s.  Exception %(exc)s' % {'label_in': label_in, 'exc': exc}, level=xbmc.LOGERROR)

		return label_out

	def choose_image(self,image1,image2,image3,set_source=True):
		if image1 is not None and len(image1)>4:
			if set_source and '/' not in image1:
				return self.base_image_url+image1
			else:
				return image1
		elif image2 is not None and len(image2)>4:
			if set_source and '/' not in image2:
				return self.base_image_url+image2
			else:
				return image2
		else:
			if image3 is not None:
				if set_source and '/' not in image3:
					return self.base_image_url+image3
				else:
					return image3
			else:
				return image3 #Default

	def update_game_label(self,current_label,game_item,naming_convention):
		label_out = current_label

		try:
			# label_key = self.game_label_settings.split('|').index(naming_convention) #Old method pre language update
			label_key = int(naming_convention)
		except:
			label_key = None
		if label_key is not None:
			if label_key == 0: #Title
				xbmc.log(msg='IAGL:  Naming convention title only', level=xbmc.LOGDEBUG)
			elif label_key == 1: #Title, Genre
				if game_item.get('info').get('genre') is not None:
					label_out = label_out+self.label_sep+game_item.get('info').get('genre')
			elif label_key == 2: #Title, Date
				if game_item.get('info').get('date') is not None:
					label_out = label_out+self.label_sep+self.get_label_date(game_item.get('info').get('date'))
			elif label_key == 3: #Title, Players
				if game_item.get('properties').get('nplayers') is not None:
					label_out = label_out+self.label_sep+game_item.get('properties').get('nplayers')
			elif label_key == 4: #Title, Genre, Date
				if game_item.get('info').get('genre') is not None:
					label_out = label_out+self.label_sep+game_item.get('info').get('genre')
				if game_item.get('info').get('date') is not None:
					label_out = label_out+self.label_sep+self.get_label_date(game_item.get('info').get('date'))
			elif label_key == 5: #Title, Genre, Size
				if game_item.get('info').get('genre') is not None:
					label_out = label_out+self.label_sep+game_item.get('info').get('genre')
				if game_item.get('info').get('size') is not None:
					label_out = label_out+self.label_sep+self.bytes_to_string_size(game_item.get('info').get('size'))
			elif label_key == 6: #Title, Genre, Players
				if game_item.get('info').get('genre') is not None:
					label_out = label_out+self.label_sep+game_item.get('info').get('genre')
				if game_item.get('properties').get('nplayers') is not None:
					label_out = label_out+self.label_sep+game_item.get('properties').get('nplayers')
			elif label_key == 7: #Title, Date, Size
				if game_item.get('info').get('date') is not None:
					label_out = label_out+self.label_sep+self.get_label_date(game_item.get('info').get('date'))
				if game_item.get('info').get('size') is not None:
					label_out = label_out+self.label_sep+self.bytes_to_string_size(game_item.get('info').get('size'))
			elif label_key == 8: #Title, Date, Players
				if game_item.get('info').get('date') is not None:
					label_out = label_out+self.label_sep+self.get_label_date(game_item.get('info').get('date'))
				if game_item.get('properties').get('nplayers') is not None:
					label_out = label_out+self.label_sep+game_item.get('properties').get('nplayers')
			# Non title first entries
			elif label_key == 9: #Genre, Title
				if game_item.get('info').get('genre') is not None:
					label_out = game_item.get('info').get('genre')+self.label_sep+current_label
			elif label_key == 10: #Date, Title
				if game_item.get('info').get('date') is not None:
					label_out = self.get_label_date(game_item.get('info').get('date'))+self.label_sep+current_label
			elif label_key == 11: #Players, Title
				if game_item.get('properties').get('nplayers') is not None:
					label_out = game_item.get('properties').get('nplayers')+self.label_sep+current_label
			elif label_key == 12: #Genre, Title, Date
				if game_item.get('info').get('genre') is not None:
					label_out = game_item.get('info').get('genre')+self.label_sep+current_label
				if game_item.get('info').get('date') is not None:
					label_out = label_out+self.label_sep+self.get_label_date(game_item.get('info').get('date'))
			elif label_key == 13: #Date, Title, Genre
				if game_item.get('info').get('date') is not None:
					label_out = self.get_label_date(game_item.get('info').get('date'))+self.label_sep+current_label
				if game_item.get('info').get('genre') is not None:
					label_out = label_out+self.label_sep+game_item.get('info').get('genre')
			elif label_key == 14: #Players, Title, Genre
				if game_item.get('properties').get('nplayers') is not None:
					label_out = game_item.get('properties').get('nplayers')+self.label_sep+current_label
				if game_item.get('info').get('genre') is not None:
					label_out = label_out+self.label_sep+game_item.get('info').get('genre')
			elif label_key == 15: #Players, Title, Date
				if game_item.get('properties').get('nplayers') is not None:
					label_out = game_item.get('properties').get('nplayers')+self.label_sep+current_label
				if game_item.get('info').get('date') is not None:
					label_out = label_out+self.label_sep+self.get_label_date(game_item.get('info').get('date'))
			# Title first entries with more stuff
			elif label_key == 16: #Title, Genre, Date, ROM Tag
				if game_item.get('info').get('genre') is not None:
					label_out = label_out+self.label_sep+game_item.get('info').get('genre')
				if game_item.get('info').get('date') is not None:
					label_out = label_out+self.label_sep+self.get_label_date(game_item.get('info').get('date'))
				if game_item.get('properties').get('tag') is not None:
					label_out = label_out+self.label_sep+game_item.get('properties').get('tag')
			elif label_key == 17: #Title, Genre, Date, Players
				if game_item.get('info').get('genre') is not None:
					label_out = label_out+self.label_sep+game_item.get('info').get('genre')
				if game_item.get('info').get('date') is not None:
					label_out = label_out+self.label_sep+self.get_label_date(game_item.get('info').get('date'))
				if game_item.get('properties').get('nplayers') is not None:
					label_out = label_out+self.label_sep+game_item.get('properties').get('nplayers')
			elif label_key == 18: #Title, Genre, Players, ROM Tag
				if game_item.get('info').get('genre') is not None:
					label_out = label_out+self.label_sep+game_item.get('info').get('genre')
				if game_item.get('properties').get('nplayers') is not None:
					label_out = label_out+self.label_sep+game_item.get('properties').get('nplayers')
				if game_item.get('properties').get('tag') is not None:
					label_out = label_out+self.label_sep+game_item.get('properties').get('tag')
			elif label_key == 19: #Title, Genre, Date, Size
				if game_item.get('info').get('genre') is not None:
					label_out = label_out+self.label_sep+game_item.get('info').get('genre')
				if game_item.get('info').get('date') is not None:
					label_out = label_out+self.label_sep+self.get_label_date(game_item.get('info').get('date'))
				if game_item.get('info').get('size') is not None:
					label_out = label_out+self.label_sep+self.bytes_to_string_size(game_item.get('info').get('size'))
			else: #Title or unknown option, to default to title
				xbmc.log(msg='IAGL:  Unknown naming convention option %(naming_convention)s' % {'naming_convention': naming_convention}, level=xbmc.LOGDEBUG)
				label_out = current_label

		return label_out

	def create_kodi_listitem(self,label1_in,label2_in=None):
		if self.supports_offscreen:
			return xbmcgui.ListItem(label=label1_in,label2=label2_in, offscreen=True)
		else:
			return xbmcgui.ListItem(label=label1_in,label2=label2_in)

	def get_external_command(self,command_in):
		command_out = command_in

		return command_out

#Download Class
class iagl_download(object):
	def __init__(self,json_in):
		self.IAGL = iagl_utils() #IAGL utils Class
		try:
			self.json = json.loads(json_in)
		except Exception as exc: #except Exception, (exc):
			self.json = None
			xbmc.log(msg='IAGL Error:  JSON data is not available.  Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)

		# self.login_setting = (True if self.IAGL.handle.getSetting(id='iagl_setting_enable_login') == 'Enabled' else False)
		self.login_setting = self.IAGL.get_setting_as_bool(self.IAGL.handle.getSetting(id='iagl_setting_enable_login'))
		self.username_setting = self.IAGL.handle.getSetting(id='iagl_setting_ia_username')
		self.password_setting = self.IAGL.handle.getSetting(id='iagl_setting_ia_password')
		# self.local_file_setting = self.IAGL.handle.getSetting(id='iagl_setting_localfile_action') #Old method pre language update
		self.local_file_setting = int(self.IAGL.handle.getSetting(id='iagl_setting_localfile_action'))
		try:
			if len([x for x in json.loads(xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Addons.GetAddons","params":{"type":"kodi.vfs"}, "id": "1"}')).get('result').get('addons') if x is not None and x.get('addonid')=='vfs.libarchive'])>0:
				self.libarchive_available = True
			else:
				self.libarchive_available = False
		except:
			self.libarchive_available = False
		self.libarchive_extensions = ['.7z','.tar.gz','.tar.bz2','.tar.xz','.zip','.rar','.tgz','.tbz2','.gz','.bz2','.xz']
		if self.username_setting is not None and len(self.username_setting)<1:
			self.username_setting = None
		if self.password_setting is not None and len(self.password_setting)<1:
			self.password_setting = None

		self.zero_byte_file_size = 1
		self.small_file_byte_size = 150000 #Small file, check if archive.org did not return a good game file
		self.small_file_text_check = '<title>' #Small file, check if archive.org did not return a good game file or login was wrong
		self.bad_login_text_check = '<h1>item not available</h1>' #Check if archive.org returned a 'requires login' page
		self.bad_file_text_check = '<h1>page not found</h1>' #Check if archive.org returned a 'requires login' page

		# self.user_agent_options = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36','Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/603.2.4 (KHTML, like Gecko) Version/10.1.1 Safari/603.2.4','Mozilla/5.0 (Windows NT 10.0; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36','Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36','Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36','Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36','Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko','Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:53.0) Gecko/20100101 Firefox/53.0','Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36','Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:53.0) Gecko/20100101 Firefox/53.0','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.86 Safari/537.36','Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.1 Safari/603.1.30','Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.86 Safari/537.36','Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.86 Safari/537.36','Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.86 Safari/537.36','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.104 Safari/537.36','Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/603.2.5 (KHTML, like Gecko) Version/10.1.1 Safari/603.2.5']
		# try:
			# self.user_agent = user_agent_options[random.randint(0,len(user_agent_options)-1)]  #Just pick a random user agent
		# except:
			# self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'
		self.chunk_size = 102400 #100 KB chunks
		self.download_timeout = (12.1,27) #Connect / Read timeouts
		self.default_file_size = 0
		self.current_game_title = self.json.get('game').get('@name')
		self.current_safe_filename = clean_file_folder_name(self.json.get('game').get('@name'))
		#Initialize filenames to download, location to download, post download action
		if self.json is not None:
			self.base_url = self.json.get('emu').get('emu_baseurl')
			self.default_download_location = self.IAGL.get_temp_cache_path()

			if self.json.get('emu').get('emu_downloadpath') is not None and len(self.json.get('emu').get('emu_downloadpath'))>0:
				if self.json.get('emu').get('emu_downloadpath').lower() == 'default':
					if self.IAGL.get_setting_as_bool(self.IAGL.handle.getSetting(id='iagl_organize_temp_files')) and self.json.get('emu').get('emu_description') is not None:
						organized_temp_folder = os.path.join(self.default_download_location,clean_file_folder_name(self.json.get('emu').get('emu_description')))
						if not xbmcvfs.exists(os.path.join(organized_temp_folder,'')):
							if not xbmcvfs.mkdir(organized_temp_folder):
								xbmc.log(msg='IAGL:  The folder %(folder_in)s could not be created so the default will be used'% {'folder_in': organized_temp_folder}, level=xbmc.LOGDEBUG)
								self.download_location = self.default_download_location
							else:
								self.download_location = organized_temp_folder
						else:
							self.download_location = organized_temp_folder
					else:
						self.download_location = self.default_download_location
				else:
					self.download_location = xbmc.translatePath(self.json.get('emu').get('emu_downloadpath')) #Translate the download path if the user used a source:// path
			else:
				self.download_location = None
			if self.json.get('game').get('rom_override_downloadpath') is not None and len(self.json.get('game').get('rom_override_downloadpath'))>0:
				self.game_download_location_override = self.json.get('game').get('rom_override_downloadpath')
			else:
				self.game_download_location_override = None
			if self.json.get('game').get('emu_command') is not None and len(self.json.get('game').get('emu_command'))>0:
				self.rom_emu_command = self.json.get('game').get('emu_command')
			else:
				self.rom_emu_command = None

			if self.json.get('emu').get('emu_postdlaction') is not None and len(self.json.get('emu').get('emu_postdlaction'))>0:
				if self.json.get('emu').get('emu_postdlaction').lower() == 'none':
					self.emu_post_download_action = None
				else:
					self.emu_post_download_action = self.json.get('emu').get('emu_postdlaction')
			else:
				self.emu_post_download_action = None
			if self.json.get('emu').get('emu_launcher') is not None and len(self.json.get('emu').get('emu_launcher'))>0:
				if self.json.get('emu').get('emu_launcher').lower() == 'none':
					self.launcher = None
				else:
					self.launcher = self.json.get('emu').get('emu_launcher')
			else:
				self.launcher = None
			if self.json.get('game').get('rom_override_postdl') is not None and len(self.json.get('game').get('rom_override_postdl'))>0:
				if self.json.get('game').get('rom_override_postdl').lower() == 'none':
					self.game_post_download_action_override = None
				else:
					self.game_post_download_action_override = self.json.get('game').get('rom_override_postdl')
			else:
				self.game_post_download_action_override = None
			if type(self.json.get('game').get('rom')) is list: #Multiple files
				self.current_files_to_download = [self.base_url+x.get('@name') for x in self.json['game']['rom']]
				self.current_files_to_download_skip = [False for x in self.current_files_to_download] #Used if the file is found to exist locally
				self.current_files_to_save = [url_unquote(x.split('%2F')[-1].split('/')[-1]) for x in self.current_files_to_download]
				self.current_files_to_save_no_ext = [os.path.splitext(x)[0] for x in self.current_files_to_save]
				self.current_files_to_save_exists_locally = [False for x in self.current_files_to_save]
				self.current_estimated_file_sizes = [x.get('@size') for x in self.json['game']['rom']]
				if self.emu_post_download_action is not None:
					if self.game_post_download_action_override is not None:
						self.current_post_download_actions = [self.game_post_download_action_override for x in self.current_files_to_download] #Use Game Post DL Override Command
					else:
						self.current_post_download_actions = [self.emu_post_download_action for x in self.current_files_to_download]  #Use Emu Post DL Command
				else:
					self.current_post_download_actions = [None for x in self.current_files_to_download] #No Post DL Command
				if self.download_location is not None:
					if self.game_download_location_override is not None:
						self.current_download_locations = [self.game_download_location_override for x in self.current_files_to_download] #Use Game DL Override Location
					else:
						self.current_download_locations = [self.download_location for x in self.current_files_to_download]  #Use Emu DL Location
				else:
					self.current_download_locations = [self.default_download_location for x in self.current_files_to_download] #Default Location
			else: #One file
				if self.json.get('game').get('rom') is not None:
					self.current_files_to_download = [self.base_url+self.json['game']['rom']['@name']]
					self.current_files_to_download_skip = [False for x in self.current_files_to_download] #Used if the file is found to exist locally
					self.current_files_to_save = [url_unquote(x.split('%2F')[-1].split('/')[-1]) for x in self.current_files_to_download]
					self.current_files_to_save_no_ext = [os.path.splitext(x)[0] for x in self.current_files_to_save]
					self.current_files_to_save_exists_locally = [False for x in self.current_files_to_save]
					self.current_estimated_file_sizes = [self.json['game']['rom']['@size']]
					if self.emu_post_download_action is not None:
						if self.game_post_download_action_override is not None:
							self.current_post_download_actions = [self.game_post_download_action_override] #Use Game Post DL Override Command
						else:
							self.current_post_download_actions = [self.emu_post_download_action]  #Use Emu Post DL Command
					else:
						self.current_post_download_actions = [None] #No Post DL Command
					if self.download_location is not None:
						if self.game_download_location_override is not None:
							self.current_download_locations = [self.game_download_location_override] #Use Game DL Override Location
						else:
							self.current_download_locations = [self.download_location]  #Use Emu DL Location
					else:
						self.current_download_locations = [self.default_download_location for x in self.current_files_to_download] #Default Location			
		self.current_saved_files = list()
		self.current_saved_files_success = list()
		self.current_saved_files_size = list()
		self.current_saved_files_crc = list()
		self.current_processed_files = list()
		self.current_processed_files_success = list()
		self.download_fail_reason = ''

	def download_with_login(self,url,dest,username=None,password=None,est_filesize=0,description='',heading='Downloading'):
		xbmc.log(msg='IAGL:  Attempting to download file %(url)s as logged in user' % {'url': url}, level=xbmc.LOGNOTICE)
		xbmc.log(msg='IAGL:  Saving file to %(dest)s as logged in user' % {'dest': dest}, level=xbmc.LOGNOTICE)
		dp = xbmcgui.DialogProgress()
		dp.create(heading,description,'')
		dp.update(0)
		if username is not None and len(username)>0 and password is not None and len(password)>0: #Attempt to login for downloading
			try:
				s = requests.Session()
				# s.headers.update({'User-Agent': self.user_agent})
				r = s.get('https://archive.org/account/login.php')
				data={'username': username,'password': password,'remember': 'CHECKED','action': 'login','submit': 'Log+in'}
				r = s.post('https://archive.org/account/login.php', data=data)
				if 'that password seems incorrect' in str(r.text.encode('utf-8')).lower():
					xbmc.log(msg='IAGL:  Login and Password were not accepted, we will try to download anyway', level=xbmc.LOGDEBUG)
				r = s.get(url,verify=False,stream=True,timeout=self.download_timeout)
				try:
					header_filesize = int(r.headers['Content-length'])
					xbmc.log(msg='IAGL:  Source URL returned filesize of %(header_size)s'%{'header_size': header_filesize}, level=xbmc.LOGDEBUG)
				except:
					header_filesize = None
					xbmc.log(msg='IAGL:  Source URL returned no filesize, current size estimate is %(est_filesize)s'%{'est_filesize': est_filesize}, level=xbmc.LOGDEBUG)
				if header_filesize is not None:
					est_filesize = header_filesize
				if est_filesize is not None and est_filesize>0:
					line2_description = 'current_size / %(estimated_size)s'% {'estimated_size': self.IAGL.bytes_to_string_size(est_filesize)}
				else:
					line2_description = ''
				# f = open(dest, 'wb')
				with closing(xbmcvfs.File(dest,'w')) as game_file:
					size = 0
					last_time = time.time()
					for chunk in r.iter_content(self.chunk_size):
						if dp.iscanceled():
							dp.close()
							self.download_fail_reason = 'Download was cancelled.'
							raise Exception('User Cancelled Download')
						# size = size + self.chunk_size
						size = size+len(chunk) #chunks may be a different size when streaming
						percent = 100.0 * size / (est_filesize + 1) #Added 1 byte to avoid div by zero
						game_file.write(chunk)
						now = time.time()
						diff = now - last_time
						if diff > 1:
							percent = int(percent)
							last_time = now
							dp.update(percent,description,line2_description.replace('current_size','%(current_estimated_size)s'% {'current_estimated_size': self.IAGL.bytes_to_string_size(size)}))
							if dp.iscanceled():
								dp.close()
								self.download_fail_reason = 'Download was cancelled.'
								raise Exception('User Cancelled Download')
				# f = xbmcvfs.File(dest,'w')
				# size = 0
				# last_time = time.time()
				# for chunk in r.iter_content(self.chunk_size):
				# 	if dp.iscanceled():
				# 		dp.close()
				# 		self.download_fail_reason = 'Download was cancelled.'
				# 		raise Exception('User Cancelled Download')
				# 	size = size + self.chunk_size
				# 	percent = 100.0 * size / (est_filesize + 1) #Added 1 byte to avoid div by zero
				# 	f.write(chunk)
				# 	now = time.time()
				# 	diff = now - last_time
				# 	if diff > 1:
				# 		percent = int(percent)
				# 		last_time = now
				# 		dp.update(percent)
				# 		if dp.iscanceled():
				# 			dp.close()
				# 			self.download_fail_reason = 'Download was cancelled.'
				# 			raise Exception('User Cancelled Download')
				# # f.flush()
				# f.close()
				self.current_saved_files_success.append(True)
				self.current_saved_files.append(dest)
				self.current_saved_files_size.append(xbmcvfs.Stat(dest).st_size())
				self.current_saved_files_crc.append(get_crc32(dest))
				xbmc.log(msg='IAGL:  File saved to location %(dest)s, file size %(filesize)s, file crc %(filecrc)s' % {'dest': dest, 'filesize': self.current_saved_files_size[-1], 'filecrc': self.current_saved_files_crc[-1]}, level=xbmc.LOGNOTICE)
				dp.close()
				
			except Exception as web_except:
				self.current_saved_files_success.append(False)
				self.current_saved_files.append(None)
				self.current_saved_files_size.append(None)
				self.current_saved_files_crc.append(None)
				if 'Failed to establish a new connection' in str(web_except):
					self.download_fail_reason = 'Failed to establish connection.'
				xbmc.log(msg='IAGL:  There was a download error (with login): %(url)s - %(web_except)s' % {'url': url, 'web_except': web_except}, level=xbmc.LOGERROR)
		else:
			self.current_saved_files_success.append(False)
			self.current_saved_files.append(None)
			self.current_saved_files_size.append(None)
			self.current_saved_files_crc.append(None)
			xbmc.log(msg='IAGL:  User credentials are not entered in settings', level=xbmc.LOGERROR)

	def download_no_login(self,url,dest,est_filesize=0,description='',heading='Downloading'):
		xbmc.log(msg='IAGL:  Attempting to download file %(url)s' % {'url': url}, level=xbmc.LOGNOTICE)
		xbmc.log(msg='IAGL:  Saving file to %(dest)s' % {'dest': dest}, level=xbmc.LOGNOTICE)
		dp = xbmcgui.DialogProgress()
		dp.create(heading,description,'')
		dp.update(0)
		try:
			s = requests.Session()
			# s.headers.update({'User-Agent': self.user_agent})
			r = s.get(url,verify=False,stream=True,timeout=self.download_timeout)
			try:
				header_filesize = int(r.headers['Content-length'])
				xbmc.log(msg='IAGL:  Source URL returned filesize of %(header_size)s'%{'header_size': header_filesize}, level=xbmc.LOGDEBUG)
			except:
				header_filesize = None
				xbmc.log(msg='IAGL:  Source URL returned no filesize, current size estimate is %(est_filesize)s'%{'est_filesize': est_filesize}, level=xbmc.LOGDEBUG)
			if header_filesize is not None:
				est_filesize = header_filesize
			if est_filesize is not None and est_filesize>0:
				line2_description = 'current_size / %(estimated_size)s'% {'estimated_size': self.IAGL.bytes_to_string_size(est_filesize)}
			else:
				line2_description = ''
			# f = open(dest, 'wb')
			with closing(xbmcvfs.File(dest,'w')) as game_file:
				size = 0
				last_time = time.time()
				for chunk in r.iter_content(self.chunk_size):
					if dp.iscanceled():
						dp.close()
						self.download_fail_reason = 'Download was cancelled.'
						raise Exception('User Cancelled Download')
					# size = size + self.chunk_size
					size = size+len(chunk) #chunks may be a different size when streaming
					percent = 100.0 * size / (est_filesize + 1) #Added 1 byte to avoid div by zero
					game_file.write(chunk)
					now = time.time()
					diff = now - last_time
					if diff > 1:
						percent = int(percent)
						last_time = now
						dp.update(percent,description,line2_description.replace('current_size','%(current_estimated_size)s'% {'current_estimated_size': self.IAGL.bytes_to_string_size(size)}))
						if dp.iscanceled():
							dp.close()
							self.download_fail_reason = 'Download was cancelled.'
							raise Exception('User Cancelled Download')
			# f.flush()
			# f.close()
			self.current_saved_files_success.append(True)
			self.current_saved_files.append(dest)
			self.current_saved_files_size.append(xbmcvfs.Stat(dest).st_size())
			self.current_saved_files_crc.append(get_crc32(dest))
			xbmc.log(msg='IAGL:  File saved to location %(dest)s, file size %(filesize)s, file crc %(filecrc)s' % {'dest': dest, 'filesize': self.current_saved_files_size[-1], 'filecrc': self.current_saved_files_crc[-1]}, level=xbmc.LOGNOTICE)
			dp.close()
		except Exception as web_except:
			self.current_saved_files_success.append(False)
			self.current_saved_files.append(None)
			self.current_saved_files_size.append(None)
			self.current_saved_files_crc.append(None)
			if 'Failed to establish a new connection' in str(web_except):
				self.download_fail_reason = 'Failed to establish connection.'
			xbmc.log(msg='IAGL:  There was a download error (no login): %(url)s - %(web_except)s' % {'url': url, 'web_except': web_except}, level=xbmc.LOGERROR)

	def post_process_unarchive_files(self,filename_in,crc_in):
		#Check for libarchive and use that if available, otherwise try xbmc builtin extract
		if self.libarchive_available:
			self.post_process_unarchive_files_libarchive(filename_in,crc_in)
		else:
			self.post_process_unarchive_files_xbmc_builtin(filename_in,crc_in)

	def post_process_unarchive_and_rename_files(self,filename_in,crc_in):
		#Check for libarchive and use that if available, otherwise try xbmc builtin extract
		if self.libarchive_available:
			self.post_process_unarchive_and_rename_files_libarchive(filename_in,crc_in)
		else:
			self.post_process_unarchive_and_rename_files_xbmc_builtin(filename_in,crc_in)			

	def post_process_unarchive_files_to_folder(self,filename_in,name_in):
		#Check for libarchive and use that if available, otherwise try xbmc builtin extract
		if self.libarchive_available:
			self.post_process_unarchive_files_to_folder_libarchive(filename_in,name_in)
		else:
			self.post_process_unarchive_files_to_folder_name_xbmc_builtin(filename_in,name_in)		

	def post_process_unarchive_files_to_folder_libarchive(self,filename_in,name_in):
		xbmc.log(msg='IAGL:  Post Process file %(filename_in)s - unarchive files to folder %(name_in)s (vfs.libarchive)'% {'filename_in': filename_in, 'name_in': name_in}, level=xbmc.LOGDEBUG)
		if any([x in filename_in.lower() for x in self.libarchive_extensions]):
			folder_name = xbmc.translatePath(os.path.join(os.path.split(filename_in)[0],str(name_in)))
			if xbmcvfs.mkdir(folder_name): #Create the folder to unarchive into
				files_extracted, files_extracted_success = extract_all_libarchive(filename_in,folder_name)
				if files_extracted_success:
					self.current_processed_files.extend(files_extracted)
					self.current_processed_files_success = [True for x in files_extracted]
					xbmc.log(msg='IAGL:  The file %(filename_in)s was unarchived.  First file extracted: %(files_extracted)s'% {'filename_in': filename_in, 'files_extracted':files_extracted[0]}, level=xbmc.LOGDEBUG)
					if not xbmcvfs.delete(filename_in):
						xbmc.log(msg='IAGL:  The file %(filename_in)s could not be deleted after processing'% {'filename_in': filename_in}, level=xbmc.LOGDEBUG)
				else:
					self.current_processed_files_success = False
			else:
				xbmc.log(msg='IAGL:  The folder %(folder_in)s could not be created for unarchiving.'% {'folder_in': folder_name}, level=xbmc.LOGERROR)
		else:
			self.current_processed_files.append(filename_in)
			self.current_processed_files_success.append(True) #Set this to true regardless in this case...
			xbmc.log(msg='IAGL:  The file %(filename_in)s does not appear to be an archive file and was not processed, pointing back to file in attempts to launch.'% {'filename_in': filename_in}, level=xbmc.LOGDEBUG)

	def post_process_unarchive_files_to_folder_name_xbmc_builtin(self,filename_in,name_in):
		xbmc.log(msg='IAGL:  Post Process file %(filename_in)s - unzip files to folder %(name_in)s (builtin)'% {'filename_in': filename_in, 'name_in': name_in}, level=xbmc.LOGDEBUG)
		if '.zip' in filename_in.lower():
			temp_folder =  os.path.join(os.path.split(filename_in)[0],str(name_in))
			# xbmc.executebuiltin('ActivateWindow(busydialog)')
			xbmc.executebuiltin(('XBMC.Extract("%(file_to_unzip)s","%(location_to_extract_to)s")' % {'file_to_unzip': xbmc.translatePath(filename_in), 'location_to_extract_to':xbmc.translatePath(temp_folder)}).encode('utf-8'), True) #Unzip the file(s) to a temp folder
			# xbmc.executebuiltin('Dialog.Close(busydialog)')
			if xbmcvfs.exists(os.path.join(temp_folder,'')): #Unzip generated a folder
				self.current_processed_files.extend(get_all_files_in_directory_xbmcvfs(temp_folder))
				self.current_processed_files_success = [True for x in self.current_processed_files]
				if not xbmcvfs.delete(filename_in):
					xbmc.log(msg='IAGL:  The file %(filename_in)s could not be deleted after processing'% {'filename_in': filename_in}, level=xbmc.LOGDEBUG)
		else:
			self.current_processed_files.append(filename_in)
			self.current_processed_files_success.append(True) #Set this to true regardless in this case...
			xbmc.log(msg='IAGL:  The file %(filename_in)s does not appear to be a zip file and was not processed, pointing back to file in attempts to launch.'% {'filename_in': filename_in}, level=xbmc.LOGDEBUG)

	def post_process_unarchive_files_libarchive(self,filename_in,crc_in):
		xbmc.log(msg='IAGL:  Post Process file %(filename_in)s - unarchive (vfs.libarchive)'% {'filename_in': filename_in}, level=xbmc.LOGDEBUG)
		if any([x in filename_in.lower() for x in self.libarchive_extensions]):
			files_extracted, files_extracted_success = extract_all_libarchive(filename_in,os.path.split(filename_in)[0])
			if files_extracted_success:
				self.current_processed_files.extend(files_extracted)
				self.current_processed_files_success = [True for x in files_extracted]
				xbmc.log(msg='IAGL:  The file %(filename_in)s was unarchived.  First file extracted: %(files_extracted)s'% {'filename_in': filename_in, 'files_extracted':files_extracted[0]}, level=xbmc.LOGDEBUG)
				if not xbmcvfs.delete(filename_in):
					xbmc.log(msg='IAGL:  The file %(filename_in)s could not be deleted after processing'% {'filename_in': filename_in}, level=xbmc.LOGDEBUG)
			else:
				self.current_processed_files_success = False
		else:
			self.current_processed_files.append(filename_in)
			self.current_processed_files_success.append(True) #Set this to true regardless in this case...
			xbmc.log(msg='IAGL:  The file %(filename_in)s does not appear to be an archive file and was not processed, pointing back to file in attempts to launch.'% {'filename_in': filename_in}, level=xbmc.LOGDEBUG)

	def post_process_unarchive_files_xbmc_builtin(self,filename_in,crc_in):
		xbmc.log(msg='IAGL:  Post Process file %(filename_in)s - unzip (builtin)'% {'filename_in': filename_in}, level=xbmc.LOGDEBUG)
		if '.zip' in filename_in.lower():
			temp_folder =  os.path.join(os.path.split(filename_in)[0],str(crc_in))
			# xbmc.executebuiltin('ActivateWindow(busydialog)')
			xbmc.executebuiltin(('XBMC.Extract("%(file_to_unzip)s","%(location_to_extract_to)s")' % {'file_to_unzip': xbmc.translatePath(filename_in), 'location_to_extract_to':xbmc.translatePath(temp_folder)}).encode('utf-8'), True) #Unzip the file(s) to a temp folder
			# xbmc.executebuiltin('Dialog.Close(busydialog)')
			if xbmcvfs.exists(os.path.join(temp_folder,'')): #Unzip generated a folder
				files_extracted, files_extracted_success = move_directory_contents_xbmcvfs(os.path.join(temp_folder,''),os.path.join(os.path.split(filename_in)[0],''))
				if files_extracted_success:
					self.current_processed_files.extend(files_extracted)
					self.current_processed_files_success = [True for x in files_extracted]
					xbmc.log(msg='IAGL:  The file %(filename_in)s was unarchived.  First file extracted: %(files_extracted)s'% {'filename_in': filename_in, 'files_extracted':files_extracted[0]}, level=xbmc.LOGDEBUG)
					if not xbmcvfs.delete(filename_in):
						xbmc.log(msg='IAGL:  The file %(filename_in)s could not be deleted after processing'% {'filename_in': filename_in}, level=xbmc.LOGDEBUG)
		else:
			self.current_processed_files.append(filename_in)
			self.current_processed_files_success.append(True) #Set this to true regardless in this case...
			xbmc.log(msg='IAGL:  The file %(filename_in)s does not appear to be a zip file and was not processed, pointing back to file in attempts to launch.'% {'filename_in': filename_in}, level=xbmc.LOGDEBUG)

	def post_process_unarchive_and_rename_files_libarchive(self,filename_in,crc_in):
		xbmc.log(msg='IAGL:  Post Process and rename file %(filename_in)s - unarchive (vfs.libarchive)'% {'filename_in': filename_in}, level=xbmc.LOGDEBUG)
		if any([x in filename_in.lower() for x in self.libarchive_extensions]):
			files_extracted, files_extracted_success = extract_all_libarchive(filename_in,os.path.split(filename_in)[0])
			if files_extracted_success:
				xbmc.log(msg='IAGL:  The file %(filename_in)s was unarchived.  First file extracted: %(files_extracted)s'% {'filename_in': filename_in, 'files_extracted':files_extracted[0]}, level=xbmc.LOGDEBUG)
				if not xbmcvfs.delete(filename_in):
					xbmc.log(msg='IAGL:  The file %(filename_in)s could not be deleted after processing'% {'filename_in': filename_in}, level=xbmc.LOGDEBUG)
				for ii,ff in enumerate(files_extracted):
					new_filename = os.path.join(os.path.split(filename_in)[0],os.path.splitext(os.path.split(filename_in)[-1])[0]+os.path.splitext(ff)[-1])
					if not xbmcvfs.exists(new_filename):
						if not xbmcvfs.rename(ff,new_filename):  #Attempt to move the file first
							if xbmcvfs.copy(ff,new_filename): #If move does not work, then copy
								self.current_processed_files.extend(new_filename)
								self.current_processed_files_success.append(True)
								xbmc.log(msg='IAGL:  File move failed, so the file was copied from: %(file_from)s, to: %(file_to)s' % {'file_from': ff, 'file_to': new_filename}, level=xbmc.LOGDEBUG)
								if not xbmcvfs.delete(ff):
									xbmc.log(msg='IAGL:  Unable to delete the file after copy: %(file_from)s' % {'file_from':ff}, level=xbmc.LOGDEBUG)
							else:
								self.current_processed_files_success.append(False)
								xbmc.log(msg='IAGL:  File move and copy failed: %(file_from)s, to: %(file_to)s' % {'file_from': ff, 'file_to': new_filename}, level=xbmc.LOGDEBUG)
						else:
							self.current_processed_files.extend(new_filename)
							self.current_processed_files_success.append(True)
							xbmc.log(msg='IAGL:  File renamed from: %(file_from)s, to: %(file_to)s' % {'file_from': ff, 'file_to': new_filename}, level=xbmc.LOGDEBUG)
					else:
						self.current_processed_files.extend(new_filename)
						self.current_processed_files_success.append(True)
						xbmc.log(msg='IAGL:  File %(filename_in)s is already exists'% {'filename_in': new_filename}, level=xbmc.LOGDEBUG)
			else:
				self.current_processed_files_success.append(True)
		else:
			self.current_processed_files = filename_in
			self.current_processed_files_success.append(True) #Set this to true regardless in this case...
			xbmc.log(msg='IAGL:  The file %(filename_in)s does not appear to be an archive file and was not processed, pointing back to file in attempts to launch.'% {'filename_in': filename_in}, level=xbmc.LOGDEBUG)

	def post_process_unarchive_and_rename_files_xbmc_builtin(self,filename_in,crc_in):
		xbmc.log(msg='IAGL:  Post Process file %(filename_in)s - unzip and rename (builtin)'% {'filename_in': self.current_saved_files[-1]}, level=xbmc.LOGDEBUG)
		self.post_process_unarchive_files_xbmc_builtin(filename_in,crc_in)
		for ii, ff in enumerate(self.current_processed_files):
			new_filename = os.path.join(os.path.split(filename_in)[0],os.path.splitext(os.path.split(filename_in)[-1])[0]+os.path.splitext(ff)[-1])
			if ff != new_filename:
				if not xbmcvfs.exists(new_filename):
					if not xbmcvfs.rename(ff,new_filename):  #Attempt to move the file first
						if xbmcvfs.copy(ff,new_filename): #If move does not work, then copy
							self.current_processed_files[ii] = new_filename
							self.current_processed_files_success[ii] = True
							xbmc.log(msg='IAGL:  File move failed, so the file was copied from: %(file_from)s, to: %(file_to)s' % {'file_from': ff, 'file_to': new_filename}, level=xbmc.LOGDEBUG)
							if not xbmcvfs.delete(ff):
								xbmc.log(msg='IAGL:  Unable to delete the file after copy: %(file_from)s' % {'file_from':ff}, level=xbmc.LOGDEBUG)
						else:
							self.current_processed_files_success[ii] = False
							xbmc.log(msg='IAGL:  File move and copy failed: %(file_from)s, to: %(file_to)s' % {'file_from': ff, 'file_to': new_filename}, level=xbmc.LOGDEBUG)
					else:
						self.current_processed_files[ii] = new_filename
						self.current_processed_files_success[ii] = True
						xbmc.log(msg='IAGL:  File renamed from: %(file_from)s, to: %(file_to)s' % {'file_from': ff, 'file_to': new_filename}, level=xbmc.LOGDEBUG)
				else:
					self.current_processed_files[ii] = new_filename
					self.current_processed_files_success[ii] = True
					xbmc.log(msg='IAGL:  File %(filename_in)s is already exists'% {'filename_in': new_filename}, level=xbmc.LOGDEBUG)
			else:
				xbmc.log(msg='IAGL:  File %(filename_in)s is already correctly named'% {'filename_in': ff}, level=xbmc.LOGDEBUG)

	def post_process_rename_files_to_parent(self):
		pass
	def post_process_update_file_extension(self):
		pass

	def post_process_unarchive_and_launch_pointer_file(self,filename_in):
		xbmc.log(msg='IAGL:  Post Process file %(filename_in)s - unarchive and point to launch file'% {'filename_in': self.current_saved_files[-1]}, level=xbmc.LOGDEBUG)
		if os.path.splitext(filename_in)[-1].lower() == '.iagl': #Attempt to launch from file already locally available
			current_files = get_all_files_in_directory_xbmcvfs(os.path.split(filename_in)[0]) #Get a list of files in the diectory with the pointer file
			if any([os.path.join(*os.path.split(self.rom_emu_command)).lower() in x.lower() for x in current_files]):
				# found_file = current_files[[self.rom_emu_command in x for x in current_files].index(True)]
				found_file = [x for x in current_files if os.path.join(*os.path.split(self.rom_emu_command)).lower() in x.lower()][0]
				xbmc.log(msg='IAGL:  File %(rom_emu_command)s was found for launching.'% {'rom_emu_command': found_file}, level=xbmc.LOGDEBUG)
				self.current_processed_files.insert(0,found_file)
				self.current_processed_files.append(found_file)
				self.current_processed_files_success.append(True)
			else:
				xbmc.log(msg='IAGL Error:  Unable to find the file %(rom_emu_command)s.  You may have to try downloading the game again.'% {'rom_emu_command': os.path.join(*os.path.split(self.rom_emu_command))}, level=xbmc.LOGERROR)
		else:
			self.post_process_unarchive_files(filename_in,self.current_safe_filename) #Unarchive to current directory
			if any([os.path.join(*os.path.split(self.rom_emu_command)).lower() in x.lower() for x in self.current_processed_files]):
				# found_file = self.current_processed_files[[self.rom_emu_command in x for x in self.current_processed_files].index(True)]
				found_file = [x for x in self.current_processed_files if os.path.join(*os.path.split(self.rom_emu_command)).lower() in x.lower()][0]
				self.current_processed_files.insert(0,found_file)
				# if not any([self.current_files_to_save_no_ext[0] in x for x in self.current_processed_files]): #The archive will have to be downloaded again unless a trace file is pla
				self.write_pointer_file(os.path.split(found_file)[0],self.current_files_to_save_no_ext[0],'.iagl',found_file) #Write a pointer file for later launching

	def post_process_unarchive_to_folder_and_launch_pointer_file(self,filename_in):
		xbmc.log(msg='IAGL:  Post Process file %(filename_in)s - unarchive to folder and point to launch file'% {'filename_in': self.current_saved_files[-1]}, level=xbmc.LOGDEBUG)
		if os.path.splitext(filename_in)[-1].lower() == '.iagl': #Attempt to launch from file already locally available
			current_files = get_all_files_in_directory_xbmcvfs(os.path.split(filename_in)[0]) #Get a list of files in the diectory with the pointer file
			if any([os.path.join(*os.path.split(self.rom_emu_command)).lower() in x.lower() for x in current_files]):
				# found_file = current_files[[self.rom_emu_command in x for x in current_files].index(True)]
				found_file = [x for x in current_files if os.path.join(*os.path.split(self.rom_emu_command)).lower() in x.lower()][0]
				xbmc.log(msg='IAGL:  File %(rom_emu_command)s was found for launching.'% {'rom_emu_command': found_file}, level=xbmc.LOGDEBUG)
				self.current_processed_files.append(found_file)
				self.current_processed_files_success.append(True)
			else:
				xbmc.log(msg='IAGL Error:  Unable to find the file %(rom_emu_command)s.  You may have to try downloading the game again.'% {'rom_emu_command': os.path.join(*os.path.split(self.rom_emu_command))}, level=xbmc.LOGERROR)
		else:
			self.post_process_unarchive_files_to_folder(filename_in,self.current_safe_filename) #Unarchive to folder in current directory
			if any([os.path.join(*os.path.split(self.rom_emu_command)).lower() in x.lower() for x in self.current_processed_files]):
				# found_file = self.current_processed_files[[self.rom_emu_command in x for x in self.current_processed_files].index(True)]
				found_file = [x for x in self.current_processed_files if os.path.join(*os.path.split(self.rom_emu_command)).lower() in x.lower()][0]
				self.current_processed_files.insert(0,found_file)
				# if not any([self.current_files_to_save_no_ext[0] in x for x in self.current_processed_files]): #The archive will have to be downloaded again unless a trace file is pla
				self.write_pointer_file(os.path.split(found_file)[0],self.current_files_to_save_no_ext[0],'.iagl',found_file) #Write a pointer file for later launching

	def post_process_unarchive_to_folder_and_launch_m3u_file(self,filetype_in,m3u_filename_in,filename_in):
		xbmc.log(msg='IAGL:  Post Process file %(filename_in)s - unarchive to folder and point to m3u file'% {'filename_in': self.current_saved_files[-1]}, level=xbmc.LOGDEBUG)
		m3u_filename = os.path.splitext(os.path.split(m3u_filename_in.split('(Disk')[0].split('Disk')[0].split('(Disc')[0].split('Disc')[0])[-1])[0].strip()+'.m3u'
		m3u_filename_no_ext = os.path.splitext(m3u_filename)[0]
		if os.path.splitext(filename_in)[-1].lower() != '.zip': #Attempt to launch from m3u file already locally available
			current_files = get_all_files_in_directory_xbmcvfs(os.path.split(filename_in)[0]) #Get a list of files in the directory
			if any([m3u_filename in x for x in current_files]):
				# found_file = current_files[[m3u_filename in x for x in current_files].index(True)]
				found_file = [x for x in current_files if m3u_filename in x][0]
				xbmc.log(msg='IAGL:  M3U File %(mtu_filename)s was found for launching.'% {'mtu_filename': found_file}, level=xbmc.LOGDEBUG)
				self.current_processed_files.append(found_file)
				self.current_processed_files_success.append(True)
			else:
				xbmc.log(msg='IAGL Error:  Unable to find the M3U file %(mtu_filename)s.  You may have to try downloading the game again.'% {'mtu_filename': m3u_filename}, level=xbmc.LOGERROR)
		else:
			self.post_process_unarchive_files_to_folder(filename_in,self.current_safe_filename) #Unarchive to folder in current directory
			current_files = get_all_files_in_directory_xbmcvfs(os.path.join(os.path.split(filename_in)[0],self.current_safe_filename)) #Get a list of files in the unarchive diectory
			if any([filetype_in in x for x in current_files]): #filetype exist in the file list
				# found_file = current_files[['.cue' in x for x in current_files].index(True)]
				found_file = [x for x in sorted(current_files) if filetype_in in x][0]  #Use the first file found and place the m3u file in the same directory
				m3u_content = '\r\n'.join([os.path.split(x)[-1] for x in sorted(current_files) if filetype_in in x]) #List all files of the correct filetype in the m3u
				self.write_pointer_file(os.path.split(found_file)[0],m3u_filename_no_ext,'.m3u',m3u_content)
				self.current_processed_files.insert(0,os.path.join(os.path.split(found_file)[0],m3u_filename))
				self.current_processed_files_success.insert(0,True)
			else:
				xbmc.log(msg='IAGL:  Unable to find any %(filetype_in)s to add to an M3U'% {'filetype_in': filetype_in}, level=xbmc.LOGDEBUG)

	def post_process_save_files_to_folder_and_launch_m3u_file(self,filetype_in,m3u_filename_in,filename_in,last_file_to_process):
		xbmc.log(msg='IAGL:  Post Process file %(filename_in)s - save %(filetype_in)s to folder and point to m3u file'% {'filename_in': self.current_saved_files[-1], 'filetype_in': filetype_in}, level=xbmc.LOGDEBUG)
		m3u_filename = os.path.splitext(os.path.split(m3u_filename_in.split('(Disk')[0].split('Disk')[0].split('(Disc')[0].split('Disc')[0])[-1])[0].strip()+'.m3u'
		m3u_filename_no_ext = os.path.splitext(m3u_filename)[0]
		current_files = get_all_files_in_directory_xbmcvfs(os.path.split(filename_in)[0]) #Get a list of files in the directory
		if any([m3u_filename in x for x in current_files]):  #M3U already exists
			found_file = [x for x in current_files if m3u_filename in x][0]
			xbmc.log(msg='IAGL:  M3U File %(mtu_filename)s was found for launching.'% {'mtu_filename': found_file}, level=xbmc.LOGDEBUG)
			self.current_processed_files.append(found_file)
			self.current_processed_files_success.append(True)
		else:
			if filename_in == last_file_to_process: #Last file, move it to the directory and make an m3u
				move_file_to_directory(filename_in,os.path.join(os.path.split(filename_in)[0],self.current_safe_filename))
				current_files = get_all_files_in_directory_xbmcvfs(os.path.join(os.path.split(filename_in)[0],self.current_safe_filename)) #Get a list of files in the unarchive diectory
				if any([filetype_in in x for x in current_files]): #filetype exist in the file list
					# found_file = current_files[['.cue' in x for x in current_files].index(True)]
					found_file = [x for x in sorted(current_files, key=lambda x:('disk' in x.lower(), x)) if filetype_in in x][0]  #Use the first file found and place the m3u file in the same directory
					m3u_content = '\r\n'.join([os.path.split(x)[-1] for x in sorted(current_files, key=lambda x:('disk' in x.lower(), x)) if filetype_in in x]) #List all files of the correct filetype in the m3u
					self.write_pointer_file(os.path.split(found_file)[0],m3u_filename_no_ext,'.m3u',m3u_content)
					self.current_processed_files.insert(0,os.path.join(os.path.split(found_file)[0],m3u_filename))
					self.current_processed_files_success.insert(0,True)
				else:
					xbmc.log(msg='IAGL:  Unable to find any %(filetype_in)s to add to an M3U'% {'filetype_in': filetype_in}, level=xbmc.LOGDEBUG)
			else: #Not the last file, move it to the directory
				move_file_to_directory(filename_in,os.path.join(os.path.split(filename_in)[0],self.current_safe_filename))

	def post_process_unarchive_to_folder_and_launch_requested_file(self,requested_file_type,filename_in):
		xbmc.log(msg='IAGL:  Post Process file %(filename_in)s - unarchive to folder and point to %(requested_file_type)s file'% {'filename_in': self.current_saved_files[-1], 'requested_file_type': requested_file_type}, level=xbmc.LOGDEBUG)
		if os.path.splitext(filename_in)[-1].lower() != '.zip' and os.path.splitext(filename_in)[-1].lower() != '.7z': #Attempt to launch from file already locally available
			current_files = get_all_files_in_directory_xbmcvfs(os.path.split(filename_in)[0]) #Get a list of files in the directory
			if any([requested_file_type in x for x in current_files]):
				# found_file = current_files[[requested_file_type in x for x in current_files].index(True)]
				found_file = [x for x in current_files if requested_file_type in x][0]
				xbmc.log(msg='IAGL: File %(found_file)s was found for launching.'% {'found_file': found_file}, level=xbmc.LOGDEBUG)
				self.current_processed_files.append(found_file)
				self.current_processed_files_success.append(True)
			else:
				xbmc.log(msg='IAGL Error:  Unable to find the file %(requested_file_type)s.  You may have to try downloading the game again.'% {'requested_file_type': requested_file_type}, level=xbmc.LOGERROR)
		else:
			self.post_process_unarchive_files_to_folder(filename_in,self.current_safe_filename) #Unarchive to folder in current directory
			current_files = get_all_files_in_directory_xbmcvfs(os.path.split(filename_in)[0]) #Get a list of files in the unarchive diectory
			if any([requested_file_type in x for x in current_files]): #cue files exist in the file list
				# found_file = current_files[[requested_file_type in x for x in current_files].index(True)]
				found_file = [x for x in current_files if requested_file_type in x][0]
				xbmc.log(msg='IAGL: File %(found_file)s was found for launching.'% {'found_file': found_file}, level=xbmc.LOGDEBUG)
				self.current_processed_files.insert(0,found_file)
				self.current_processed_files_success.insert(0,True)

	def post_process_unarchive_DOSBOX_and_run_command(self):
		pass
	def post_process_unarchive_DOSBOX_and_launch_bat_file(self,filename_in):
		xbmc.log(msg='IAGL:  Post Process file %(filename_in)s - unarchive to folder and point to DOSBOX BAT file'% {'filename_in': self.current_saved_files[-1]}, level=xbmc.LOGDEBUG)
		current_files = get_all_files_in_directory_xbmcvfs(os.path.split(filename_in)[0]) #Get a list of files in the diectory with the pointer file
		if os.path.splitext(filename_in)[-1].lower() == '.bat': #Attempt to launch from file already locally available
			if any([os.path.join(self.current_safe_filename,os.path.split(filename_in)[-1]) in x for x in current_files]): #If the bat was already found in the required folder, then this is a previously launched game
				found_file = [x for x in current_files if os.path.join(self.current_safe_filename,os.path.split(filename_in)[-1]) in x][0]
				# crc_string = get_crc32_from_string(os.path.split(filename_in)[-1].encode('utf-8',errors='ignore')) #Create a repeatable crc string for filename of correct 8.3 DOS format
				# print('ztest')
				# print(crc_string)
				xbmc.log(msg='IAGL:  DOSBOX BAT file %(found_file)s was found for launching.'% {'found_file': found_file}, level=xbmc.LOGDEBUG)
				self.current_processed_files.append(found_file)
				self.current_processed_files_success.append(True)
			else:
				if not xbmcvfs.exists(os.path.join(os.path.split(filename_in)[0],self.current_safe_filename)):
					if not xbmcvfs.mkdir(os.path.join(os.path.split(filename_in)[0],self.current_safe_filename)):
						xbmc.log(msg='IAGL:  The folder %(folder_in)s could not be created'% {'folder_in': filename_in}, level=xbmc.LOGDEBUG)
				if not xbmcvfs.rename(filename_in,os.path.join(os.path.split(filename_in)[0],self.current_safe_filename,os.path.split(filename_in)[-1])):
					xbmc.log(msg='IAGL:  The file %(filename_in)s could not be moved'% {'filename_in': filename_in}, level=xbmc.LOGDEBUG)
				else:
					self.current_processed_files.insert(0,os.path.join(os.path.split(filename_in)[0],self.current_safe_filename,os.path.split(filename_in)[-1]))
					self.current_processed_files_success.insert(0,True)
				xbmc.log(msg='IAGL Error:  Unable to find the DOSBOX BAT file.  You may have to try downloading the game again.', level=xbmc.LOGERROR)
		elif os.path.splitext(filename_in)[-1].lower() == '.zip':
			self.post_process_unarchive_files_to_folder(filename_in,self.current_safe_filename) #Unarchive files to folder
			# self.write_pointer_file(path_in=os.path.join(os.path.split(filename_in)[0],self.current_safe_filename),name_in=os.path.splitext(os.path.split(filename_in)[-1])[0],contents_in=self.current_safe_filename)
		elif os.path.splitext(filename_in)[-1].lower() == '.conf':
			if not any([os.path.join(self.current_safe_filename,os.path.split(filename_in)[-1]) in x for x in current_files]): #File not yet in new folder
				if not xbmcvfs.rename(filename_in,os.path.join(os.path.split(filename_in)[0],self.current_safe_filename,os.path.split(filename_in)[-1])):
					xbmc.log(msg='IAGL:  The file %(filename_in)s could not be moved'% {'filename_in': filename_in}, level=xbmc.LOGDEBUG)
				else:
					self.current_processed_files.append(os.path.join(os.path.split(filename_in)[0],self.current_safe_filename,os.path.split(filename_in)[-1]))
					self.current_processed_files_success.append(True)
		else:
			xbmc.log(msg='IAGL:  The file %(filename_in)s is not known to be an eXoDOS file'% {'filename_in': filename_in}, level=xbmc.LOGDEBUG)
	def post_process_unarchive_SCUMMVM_and_launch_config_file(self,filename_in):
		xbmc.log(msg='IAGL:  Post Process file %(filename_in)s - unarchive to folder and point to SCUMMVM file'% {'filename_in': self.current_saved_files[-1]}, level=xbmc.LOGDEBUG)
		if os.path.splitext(filename_in)[-1].lower() == '.scummvm': #Attempt to launch from file already locally available
			current_files = get_all_files_in_directory_xbmcvfs(os.path.split(filename_in)[0]) #Get a list of files in the diectory with the pointer file
			if any(['.scummvm' in x for x in current_files]):
				# found_file = current_files[['.scummvm' in x for x in current_files].index(True)]
				found_file = [x for x in current_files if '.scummvm' in x][0]
				xbmc.log(msg='IAGL:  SCUMMVM file %(found_file)s was found for launching.'% {'found_file': found_file}, level=xbmc.LOGDEBUG)
				self.current_processed_files.append(found_file)
				self.current_processed_files_success.append(True)
			else:
				xbmc.log(msg='IAGL Error:  Unable to find the SCUMMVM file.  You may have to try downloading the game again.', level=xbmc.LOGERROR)
		else:
			self.post_process_unarchive_files_to_folder(filename_in,self.current_safe_filename) #Unarchive files to folder
			scummvm_file = os.path.join(os.path.join(os.path.split(filename_in)[0],self.current_safe_filename),os.path.splitext(os.path.split(filename_in)[-1])[0]+'.scummvm')
			current_game_path = os.path.dirname(scummvm_file)
			# scummvm_template = '-p "%GAME_PATH%" %GAME_ID%'.replace('%GAME_ID%',self.rom_emu_command).replace('%GAME_PATH%',current_game_path) #No point in using a template
			scummvm_template = '%GAME_ID%'.replace('%GAME_ID%',self.rom_emu_command).replace('%GAME_PATH%',current_game_path) #No point in using a template
			xbmc.log(msg='IAGL:  Writing SCUMMVM configuration file %(scummvm_file)s'% {'scummvm_file': scummvm_file}, level=xbmc.LOGDEBUG)
			with closing(xbmcvfs.File(scummvm_file,'w')) as content_file:
				content_file.write(scummvm_template)
			self.current_processed_files.insert(0,scummvm_file)
			self.current_processed_files_success.insert(0,True)

	def post_process_unarchive_WIN31_and_launch_bat_file(self,bat_filename_in,filename_in):
		xbmc.log(msg='IAGL:  Post Process file %(filename_in)s - unarchive to folder and point to WIN31 bat file'% {'filename_in': filename_in}, level=xbmc.LOGDEBUG)
		bat_filename = os.path.splitext(os.path.split(bat_filename_in)[-1])[0]+'.bat'
		bat_filename_no_ext = os.path.splitext(bat_filename)[0]
		if os.path.splitext(filename_in)[-1].lower() != '.zip': #Attempt to launch from bat file already locally available
			current_files = get_all_files_in_directory_xbmcvfs(os.path.split(filename_in)[0]) #Get a list of files in the directory
			if any([bat_filename in x for x in current_files]):
				# found_file = current_files[[bat_filename in x for x in current_files].index(True)]
				found_file = [x for x in current_files if bat_filename in x][0]
				xbmc.log(msg='IAGL:  BAT File %(bat_filename)s was found for launching.'% {'bat_filename': found_file}, level=xbmc.LOGDEBUG)
				self.current_processed_files.append(found_file)
				self.current_processed_files_success.append(True)
			else:
				xbmc.log(msg='IAGL Error:  Unable to find the BAT file %(bat_filename)s.  You may have to try downloading the game again.'% {'bat_filename': bat_filename}, level=xbmc.LOGERROR)
		else:
			if 'win31.zip' in filename_in: #Temporarily make a new copy of win31
				win31_success = xbmcvfs.copy(filename_in,os.path.join(os.path.split(filename_in)[0],'win31_temp.zip'))
				if not win31_success:
					xbmc.log(msg='IAGL:  win31 file could not be copied: %(file_from)s' % {'file_from': filename_in}, level=xbmc.LOGDEBUG)
			self.post_process_unarchive_files_to_folder(filename_in,self.current_safe_filename) #Unarchive to folder in current directory
			if 'win31.zip' in filename_in: #Temporarily make a new copy of win31
				if win31_success: #Restore temp copy of win31
					win31_success2 = xbmcvfs.rename(os.path.join(os.path.split(filename_in)[0],'win31_temp.zip'),filename_in)
					if not win31_success2:
						xbmc.log(msg='IAGL:  win31 temp file could not be copied: %(file_from)s' % {'file_from': os.path.join(os.path.split(filename_in)[0],'win31_temp.zip')}, level=xbmc.LOGDEBUG)
			current_files = get_all_files_in_directory_xbmcvfs(os.path.join(os.path.split(filename_in)[0],self.current_safe_filename)) #Get a list of files in the unarchive diectory
			if any([self.rom_emu_command.lower() in x.lower() for x in current_files]):
				found_file = [x for x in current_files if self.rom_emu_command.lower() in x.lower()][0] #Place the bat file next to the exe file
				xbmc.log(msg='IAGL:  WIN31 File %(found_file)s was found'% {'found_file': found_file}, level=xbmc.LOGDEBUG)
				bat_content = '@echo off\r\npath=%path%;\r\ncopy c:\\iniback\\*.* c:\\windows\\\r\nsetini c:\windows\system.ini boot shell "C:\XXCOMMANDXX"\r\nc:\r\ncd \\\r\nc:\\windows\\win\r\n'.replace('XXCOMMANDXX',self.rom_emu_command)
				self.write_pointer_file(os.path.split(found_file)[0],bat_filename_no_ext,'.bat',bat_content)
				# self.write_pointer_file(os.path.split(found_file)[0],'win31','.iagl',self.rom_emu_command) #Need a pointer file for the win31 archive as well
				self.current_processed_files.insert(0,os.path.join(os.path.split(found_file)[0],bat_filename))
				self.current_processed_files_success.insert(0,True)

	def post_process_unarchive_FSUAE_and_launch_config_file(self):
		pass
	def post_process_unarchive_FSUAECD32_and_launch_config_file(self):
		pass
	def post_process_unarchive_UAE4ARM_and_launch_config_file(self):
		pass
	def post_process_launch_softlist_file(self,filename_in,emulator_in,system_folder_in):
		current_softlist_db = self.IAGL.get_mame_softlist_listing()
		if any([system_folder_in == x.get('@name') for x in current_softlist_db.get('systems').get('system')]):
			current_softlist_url = [x.get('web_url') for x in current_softlist_db.get('systems').get('system') if x.get('@name') == system_folder_in][0]
			current_folder_name = [x.get('folder_name') for x in current_softlist_db.get('systems').get('system') if x.get('@name') == system_folder_in][0]
			current_media_type = [x.get('media_type') for x in current_softlist_db.get('systems').get('system') if x.get('@name') == system_folder_in][0]
		else:
			xbmc.log(msg='IAGL:  Unable to find the softlist %(system_folder_in)s in the IAGL database, we will try and launch the game anyway.'% {'system_folder_in': system_folder_in}, level=xbmc.LOGDEBUG)
			current_softlist_url = None
			current_folder_name = system_folder_in #Assume the folder name is the same as the one in settings
			current_media_type = None
		current_softlist_directory = os.path.join(os.path.split(filename_in)[0],current_folder_name)

		#Put the files into the appropriate softlist folder
		if current_folder_name == os.path.split(os.path.split(filename_in)[0])[-1]: #The file is already in the appropriate directory
			xbmc.log(msg='IAGL:  The downloaded file appears to be in the correct directory %(current_folder_name)s for softlist launching.' % {'current_folder_name': current_folder_name}, level=xbmc.LOGDEBUG)
			self.current_processed_files.append(filename_in)
			self.current_processed_files_success.append(True)
		else:
			self.current_processed_files.append(move_file_to_directory(filename_in,current_softlist_directory)) #Move the file to the softlist directory.  Kodi will automatically generate the folder if necessary
			if self.current_processed_files[-1] is not None:
				self.current_processed_files_success.append(True)
			else:
				self.current_processed_files_success.append(False)
		
		#Download the hash file if needed
		if self.launcher.lower() == 'external':
			retroarch_sys_directory = self.IAGL.handle.getSetting(id='iagl_external_path_to_retroarch_system_dir')
			if len(retroarch_sys_directory)<1:
				xbmc.log(msg='IAGL:  The path to the external retroarch system directory is not defined, we will try to launch the game anyway.', level=xbmc.LOGDEBUG)
			else:
				retroarch_sys_directory = os.path.join(retroarch_sys_directory,emulator_in,'hash')
				if current_softlist_url is not None: #Download the softlist to the retroarch system directory defined in IAGL settings
					if not xbmcvfs.exists(os.path.join(retroarch_sys_directory,os.path.split(current_softlist_url)[-1])):
						self.download_no_login(current_softlist_url,os.path.join(retroarch_sys_directory,os.path.split(current_softlist_url)[-1]),description='Softlist Hash: %(hashfile)s'%{'hashfile':os.path.split(current_softlist_url)[-1]},heading='Downloading, please wait...')
					else:
						xbmc.log(msg='IAGL:  Softlist Hash file already exists in Retroarch system directory', level=xbmc.LOGDEBUG)
		if self.launcher.lower() == 'retroplayer':
			addons_available = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Addons.GetAddons","params":{"type":"kodi.gameclient"}, "id": "1"}')
			if '"error"' not in addons_available:
				# dont_include_these_addons = ['game.libretro','game.libretro.2048','game.libretro.dinothawr','game.libretro.mrboom']
				current_game_addon_values = [x.get('addonid') for x in json.loads(addons_available).get('result').get('addons') if x.get('type') == 'kodi.gameclient' and x.get('addonid') not in self.IAGL.ignore_these_game_addons]
				if 'game.libretro.%(emulator_in)s'%{'emulator_in':emulator_in} in current_game_addon_values:
					current_game_libretro_hash_path = os.path.join(xbmc.translatePath(xbmcaddon.Addon(id='game.libretro.%(emulator_in)s'%{'emulator_in':emulator_in}).getAddonInfo('profile')).decode('utf-8'),'resources','system','hash')
					if current_softlist_url is not None: #Download the softlist to the retroarch system directory defined in IAGL settings
						if not xbmcvfs.exists(os.path.join(current_game_libretro_hash_path,os.path.split(current_softlist_url)[-1])):
							self.download_no_login(current_softlist_url,os.path.join(current_game_libretro_hash_path,os.path.split(current_softlist_url)[-1]),description='Softlist Hash: %(hashfile)s'%{'hashfile':os.path.split(current_softlist_url)[-1]},heading='Downloading, please wait...')
						else:
							xbmc.log(msg='IAGL:  Softlist Hash file already exists for game.libretro.%(emulator_in)s'%{'emulator_in':emulator_in}, level=xbmc.LOGDEBUG)
				else:
					xbmc.log(msg='IAGL:  The addon game.libretro.%(emulator_in)s was not found.  We will try and launch the game anyway.'%{'emulator_in':emulator_in}, level=xbmc.LOGDEBUG)

	def write_pointer_file(self,path_in,name_in,extension_in='.iagl',contents_in=''):
		xbmc.log(msg='IAGL:  Writing pointer file %(filename_in)s'% {'filename_in': os.path.join(path_in,name_in+extension_in)}, level=xbmc.LOGDEBUG)
		with closing(xbmcvfs.File(os.path.join(path_in,name_in+extension_in),'w') ) as content_file:
			content_file.write(contents_in)

	def read_pointer_file(self,filename_in):
		xbmc.log(msg='IAGL:  Reading pointer file %(filename_in)s'% {'filename_in': filename_in}, level=xbmc.LOGDEBUG)
		with closing(xbmcvfs.File(filename_in)) as content_file:
			byte_string = bytes(content_file.readBytes())
		try:
			file_contents = byte_string.decode('utf-8',errors='ignore')
		except:
			file_contents = None

	def check_file_validity(self):
		xbmc.log(msg='IAGL:  Checking downloaded file %(filename_in)s validity'% {'filename_in': self.current_saved_files[-1]}, level=xbmc.LOGDEBUG)

		if self.current_saved_files_size[-1] <= self.zero_byte_file_size:
			self.current_saved_files_success[-1] = False
			self.download_fail_reason = 'The selected file was not available in the archive.'
			xbmcvfs.delete(self.current_saved_files[-1])
			xbmc.log(msg='IAGL:  The file %(filename_in)s was empty, deleted.'% {'filename_in': self.current_saved_files[-1]}, level=xbmc.LOGDEBUG)
		if self.current_saved_files_size[-1] > self.zero_byte_file_size and self.current_saved_files_size[-1] <= self.small_file_byte_size:
			try:
				with closing(xbmcvfs.File(self.current_saved_files[-1])) as content_file:
					byte_string = bytes(content_file.readBytes())
				try:
					file_contents = byte_string.decode('utf-8',errors='ignore')  #If this doesn't work, then it's binary data and likely a valid file
				except:
					file_contents = ''
				if self.small_file_text_check in file_contents.lower():
					self.current_saved_files_success[-1] = False
					self.download_fail_reason = 'Archive returned no file or requires login in settings.'
					if self.bad_login_text_check in file_contents.lower():
						self.download_fail_reason = 'Archive requires account email and password in settings.'
					if self.bad_file_text_check in file_contents.lower():
						self.download_fail_reason = 'Archive returned no file.'
					xbmcvfs.delete(self.current_saved_files[-1])
					xbmc.log(msg='IAGL:  The archive %(filename_in)s returned a bad file, deleted.  This archive is either no longer available or requires login credentials to be entered into IAGL settings.'% {'filename_in': self.current_saved_files[-1]}, level=xbmc.LOGDEBUG)
				else:
					xbmc.log(msg='IAGL:  File validity check passed.', level=xbmc.LOGDEBUG)
			except Exception as exc: #except Exception, (exc):
				self.current_saved_files_success[-1] = False
				try:
					xbmcvfs.delete(self.current_saved_files[-1])
				except:
					pass
				xbmc.log(msg='IAGL:  The file %(filename_in)s could not be checked for validity.  Exception %(exc)s'% {'filename_in': self.current_saved_files[-1], 'exc': exc}, level=xbmc.LOGDEBUG)
		else:
			xbmc.log(msg='IAGL:  File validity check passed.', level=xbmc.LOGDEBUG)

	def check_if_files_exists_locally(self):
		current_existing_files_fullpath = [item for sublist in [get_all_files_in_directory_xbmcvfs(x) for x in set(self.current_download_locations)] for item in sublist if os.path.splitext(item)[-1].lower() not in self.IAGL.remove_these_filetypes]
		current_existing_files = [os.path.split(x)[-1] for x in current_existing_files_fullpath]
		current_existing_files_no_ext = [os.path.splitext(x)[0] for x in current_existing_files]
		current_files_exist_locally_check = False
		for ii,fts in enumerate(self.current_files_to_save_no_ext):
			if fts in current_existing_files_no_ext:
				current_files_exist_locally_check = True
				xbmc.log(msg='IAGL:  The file %(fts)s was found to already exist locally.'% {'fts': fts}, level=xbmc.LOGDEBUG)
		if current_files_exist_locally_check:
			# if self.local_file_setting == 'Prompt': #Old method pre language update
			if self.local_file_setting == 0:
				current_dialog = xbmcgui.Dialog()
				ret1 = current_dialog.select(self.IAGL.loc_str(30355), [self.IAGL.loc_str(30204),self.IAGL.loc_str(30200)])
				del current_dialog
				if ret1 == 0: #Do not overwrite local files, so just point to them directly
					overwrite_files = False		
				else:
					overwrite_files = True
			# if self.local_file_setting == 'Do Not ReDownload': #Old method pre language update
			if self.local_file_setting == 1:
				overwrite_files = False
			# if self.local_file_setting == 'ReDownload and Overwrite': #Old method pre language update
			if self.local_file_setting == 2:
				overwrite_files = True
			if not overwrite_files: #Point to existing file rather than redownload
				xbmc.log(msg='IAGL:  File was found to exist locally, no overwrite option selected', level=xbmc.LOGDEBUG)
				for ii,fts in enumerate(self.current_files_to_save_no_ext):
					if fts in current_existing_files_no_ext:
						idx = current_existing_files_no_ext.index(fts)
						self.current_files_to_download_skip[ii] = True
						self.current_files_to_save_exists_locally[ii] = current_existing_files_fullpath[idx]
			else:
				xbmc.log(msg='IAGL:  File was found to exist locally, overwrite option selected', level=xbmc.LOGDEBUG)

	def download_and_process_game_files(self):
		self.IAGL.check_temp_folder_and_clean()
		self.check_if_files_exists_locally()
		for ii, current_file in enumerate(self.current_files_to_download):
			current_file_to_save_fullpath = os.path.join(self.current_download_locations[ii],self.current_files_to_save[ii])
			current_file_size = self.current_estimated_file_sizes[ii]
			if current_file_size is not None:
				if len(current_file_size)<1 or current_file_size=='0':
					current_file_size = self.default_file_size
				else:
					current_file_size = int(current_file_size)
			else:
				current_file_size = self.default_file_size
			if not self.current_files_to_download_skip[ii]:
				if self.login_setting:
					self.download_with_login(current_file,current_file_to_save_fullpath,username=self.username_setting,password=self.password_setting,est_filesize=current_file_size,description=self.current_files_to_save_no_ext[ii],heading='Downloading, please wait...')
				else:				
					self.download_no_login(current_file,current_file_to_save_fullpath,est_filesize=current_file_size,description=self.current_files_to_save_no_ext[ii],heading='Downloading, please wait...')
			else:
				self.current_saved_files_success.append(True)
				self.current_saved_files.append(self.current_files_to_save_exists_locally[ii])
				self.current_saved_files_size.append(xbmcvfs.Stat(self.current_files_to_save_exists_locally[ii]).st_size())
				self.current_saved_files_crc.append(get_crc32(self.current_files_to_save_exists_locally[ii]))
				xbmc.log(msg='IAGL:  Skipping download of file %(existing_file)s, file already exists' % {'existing_file': self.current_saved_files[-1]}, level=xbmc.LOGDEBUG)
			if self.current_saved_files_success[-1]:
				if self.current_saved_files[-1] is not None:
					self.check_file_validity() #Check files
		# if False not in self.current_saved_files_success:
		for ii, pda in enumerate(self.current_post_download_actions):
			if self.current_saved_files_success[ii]:
				if pda is not None:
					# xbmc.executebuiltin('ActivateWindow(busydialog)')
					if pda == 'unzip_rom':
						self.post_process_unarchive_files(self.current_saved_files[ii],self.current_saved_files_crc[ii])
					if pda == 'unzip_and_rename_file': 
						self.post_process_unarchive_and_rename_files(self.current_saved_files[ii],self.current_saved_files_crc[ii])
					if pda == 'unzip_to_folder_and_launch_file':
						self.post_process_unarchive_to_folder_and_launch_pointer_file(self.current_saved_files[ii])
					if pda == 'unzip_and_launch_file':
						self.post_process_unarchive_and_launch_pointer_file(self.current_saved_files[ii])
					if pda == 'unzip_and_launch_scummvm_file':
						self.post_process_unarchive_SCUMMVM_and_launch_config_file(self.current_saved_files[ii])
					if pda == 'unzip_and_launch_exodos_file':
						self.post_process_unarchive_DOSBOX_and_launch_bat_file(self.current_saved_files[ii])
					if pda == 'unzip_and_launch_win31_file':
						self.post_process_unarchive_WIN31_and_launch_bat_file(self.current_saved_files[0],self.current_saved_files[ii])
					if pda == 'unarchive_game_generate_m3u':
						self.post_process_unarchive_to_folder_and_launch_m3u_file('.cue',self.current_saved_files[0],self.current_saved_files[ii])
					if pda == 'unarchive_game_generate_m3u_cue':
						self.post_process_unarchive_to_folder_and_launch_m3u_file('.cue',self.current_saved_files[0],self.current_saved_files[ii])
					if pda == 'unarchive_game_generate_m3u_st':
						self.post_process_unarchive_to_folder_and_launch_m3u_file('.st',self.current_saved_files[0],self.current_saved_files[ii])	
					if pda == 'save_adf_to_folder_and_launch_m3u_file':
						self.post_process_save_files_to_folder_and_launch_m3u_file('.adf',self.current_saved_files[0],self.current_saved_files[ii],self.current_saved_files[-1])
					if pda == 'save_d64_to_folder_and_launch_m3u_file':
						self.post_process_save_files_to_folder_and_launch_m3u_file('.d64',self.current_saved_files[0],self.current_saved_files[ii],self.current_saved_files[-1])
					if pda == 'unarchive_game_launch_cue':
						self.post_process_unarchive_to_folder_and_launch_requested_file('.cue',self.current_saved_files[ii])
					if pda == 'unarchive_game_launch_gdi':
						self.post_process_unarchive_to_folder_and_launch_requested_file('.gdi',self.current_saved_files[ii])
					if pda == 'unarchive_game_launch_lst':
						self.post_process_unarchive_to_folder_and_launch_requested_file('.lst',self.current_saved_files[ii])
					if 'launch_mame_softlist' in pda:
						self.post_process_launch_softlist_file(self.current_saved_files[ii],pda.split('(')[-1].split(')')[0].split(',')[0].replace("'",''),pda.split('(')[-1].split(')')[0].split(',')[-1].replace("'",''))
					# xbmc.executebuiltin('Dialog.Close(busydialog)')
				else:
					self.current_processed_files.append(self.current_saved_files[ii])
					self.current_processed_files_success.append(True) #No processing requested, point to the saved file
			else:
				self.current_processed_files.append(self.current_saved_files[ii])
				self.current_processed_files_success.append(False) #No processing since the save faled somehow, point to the saved file
		return self.current_processed_files_success

class iagl_launch(object):
	def __init__(self,json_in,filenames_in,game_id_in):
		self.IAGL = iagl_utils() #IAGL utils Class
		self.json = None
		self.launcher = None
		self.external_launch_command = None
		self.launch_success = None #Default to unknown successfull launch
		self.game_id = game_id_in
		try:
			self.json = json.loads(json_in)
		except Exception as exc: #except Exception, (exc):
			self.json = None
			xbmc.log(msg='IAGL Error:  JSON data is not available for launcher.  Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)

		if self.json is not None:
			self.game_list_id = self.json.get('emu').get('game_list_id')
			self.launcher = self.json.get('emu').get('emu_launcher')
			self.external_launch_command = self.json.get('emu').get('emu_ext_launch_cmd')
			if self.json.get('game').get('rom_override_cmd') is not None and len(self.json.get('game').get('rom_override_cmd'))>0:
				self.external_launch_command = self.json.get('game').get('rom_override_cmd')
			if self.external_launch_command is not None:
				self.external_launch_command = self.IAGL.get_external_command(self.external_launch_command)
		if type(filenames_in) is str:
			self.launch_filenames = [filenames_in]
		else:
			self.launch_filenames = filenames_in

	def launch(self):
		if self.launcher.lower() == 'retroplayer':
			self.launch_success = self.launch_retroplayer()
		if self.launcher.lower() == 'external':
			if self.IAGL.handle.getSetting(id='iagl_external_user_external_env') == 'Android' or self.IAGL.handle.getSetting(id='iagl_external_user_external_env') == 'Android Aarch64':
				self.launch_success = self.launch_external_android()
			else:
				self.launch_success = self.launch_external()
		if self.launch_success:
			self.IAGL.add_game_to_history(self.json,self.game_list_id,self.game_id)

	def launch_retroplayer(self):
		# Infolabel	Description
		# title	string (Super Mario Bros.)
		# platform	string (Atari 2600)
		# genres	list (["Action","Strategy"])
		# publisher	string (Nintendo)
		# developer	string (Square)
		# overview	string (Long Description)
		# year	integer (1980)
		# gameclient	string (game.libretro.fceumm)
		current_date, current_year = self.IAGL.get_date_and_year(self.json.get('releasedate'), self.json.get('year'))
		if self.json.get('game').get('genre') is not None:
			current_genres = [x.strip() for x in self.json.get('game').get('genre').split(',')]
		else:
			current_genres = None
		current_gameclient = self.json.get('emu').get('emu_default_addon')
		if current_gameclient == 'none':
			current_gameclient = None
		game_dict = {'values': {'label' : self.json.get('game').get('description'),
		'label2' : self.json.get('game').get('@name'),
		},
		'info': {'title' : self.json.get('game').get('description'),
		'overview' : self.json.get('game').get('plot'),
		# 'date' : current_date,
		'year' : current_year,
		'developer' : self.json.get('game').get('studio'),
		# 'genre' : self.json.get('game').get('genre'),
		'genres': current_genres,
		# 'rating' : self.json.get('game').get('rating'),
		'url': self.launch_filenames[0],
		'gameclient' : current_gameclient
		},
		'art': {'poster' : self.IAGL.choose_image(self.json.get('game').get('boxart1'),self.json.get('game').get('snapshot1'),self.IAGL.default_thumb),
		'banner' : self.IAGL.choose_image(self.json.get('game').get('banner1'),None,self.IAGL.default_banner),
		'fanart' : self.IAGL.choose_image(self.json.get('game').get('fanart1'),None,self.IAGL.default_fanart),
		'clearlogo' : self.IAGL.choose_image(self.json.get('game').get('clearlogo1'),None,self.IAGL.default_icon),
		'icon' : self.IAGL.choose_image(self.json.get('game').get('clearlogo1'),self.json.get('game').get('clearlogo1'),self.IAGL.default_icon),
		'thumb' : self.IAGL.choose_image(self.json.get('game').get('boxart1'),self.json.get('game').get('snapshot1'),self.IAGL.default_thumb),
		}}
		if current_genres is None:
			game_dict['info'].pop('genres',None)
		if current_year is None:
			game_dict['info'].pop('year',None)
		game_listitem = self.IAGL.create_kodi_listitem(game_dict['values']['label'],game_dict['values']['label2'])
		# game_listitem = xbmcgui.ListItem(label=game_dict['values']['label'],label2=game_dict['values']['label2'], offscreen=True)
		game_listitem.setInfo('game',game_dict['info'])
		game_listitem.setArt(game_dict['art'])
		if xbmc.Player().isPlaying():
			xbmc.Player().stop()
			xbmc.sleep(500) #If sleep is not called, Kodi will crash - does not like playing video and then swiching to a game
		try:
			xbmc.log(msg='IAGL:  Gameclient for Retroplayer set to: %(current_gameclient)s' % {'current_gameclient': current_gameclient}, level=xbmc.LOGNOTICE)
			xbmc.log(msg='IAGL:  Attempting to play the following file through Retroplayer: %(url)s' % {'url': self.launch_filenames[0]}, level=xbmc.LOGNOTICE)
			xbmc.Player().play(xbmc.translatePath(self.launch_filenames[0]),game_listitem)
			return True
		except Exception as exc: #except Exception, (exc):
			xbmc.log(msg='IAGL Error:  Attempt to play game failed with exception %(exc)s' % {'exc': exc}, level=xbmc.LOGDEBUG)
			return False

	def update_external_launch_command(self):
		if self.external_launch_command == 'none':
			current_dialog = xbmcgui.Dialog()
			ok_ret = current_dialog.ok(self.IAGL.loc_str(30203),self.IAGL.loc_str(30356))
			del current_dialog
			return False
		else:
			#Define %APP_PATH% Variable
			if self.IAGL.handle.getSetting(id='iagl_external_user_external_env') == 'OSX':
				current_retroarch_path = xbmc.translatePath(self.IAGL.handle.getSetting(id='iagl_external_path_to_retroarch')).split('.app')[0]+'.app' #Make App Path for OSX only up to the container
			elif self.IAGL.handle.getSetting(id='iagl_external_user_external_env') == 'Windows':
				current_retroarch_path = os.path.split(xbmc.translatePath(self.IAGL.handle.getSetting(id='iagl_external_path_to_retroarch')))[0]
			else: #Linux
				current_retroarch_path = xbmc.translatePath(self.IAGL.handle.getSetting(id='iagl_external_path_to_retroarch'))

			#Define %CFG_PATH% Variable for Android
			current_cfg_path = ''
			if self.IAGL.handle.getSetting(id='iagl_external_user_external_env') == 'Android' or self.IAGL.handle.getSetting(id='iagl_external_user_external_env') == 'Android Aarch64':
				current_cfg_path = None
				if len(self.IAGL.handle.getSetting(id='iagl_external_path_to_retroarch_cfg'))<1: #Config is not defined in settings, try to find it in one of the default locales
					for cfg_files in self.IAGL.possible_retroarch_config_locations:
						if xbmcvfs.exists(cfg_files):
							if current_cfg_path is None: #If the current config path is not yet defined and the file was found, then define it
								current_cfg_path = cfg_files
				else:
					current_cfg_path = xbmc.translatePath(self.IAGL.handle.getSetting(id='iagl_external_path_to_retroarch_cfg')) #If the config path is defined in settings, use that
				if current_cfg_path is None:
					current_cfg_path = ''
					xbmc.log(msg='IAGL:  No Retroarch config file could be defined, please set your config file location in addon settings', level=xbmc.LOGERROR)

			self.external_launch_command = self.external_launch_command.replace('%APP_PATH%',current_retroarch_path) #Replace app path with user setting
			self.external_launch_command = self.external_launch_command.replace('%ADDON_DIR%',self.IAGL.get_addon_install_path()) #Replace helper script with the more generic ADDON_DIR
			self.external_launch_command = self.external_launch_command.replace('%CFG_PATH%',current_cfg_path) #Replace config path user setting
			self.external_launch_command = self.external_launch_command.replace('%ROM_PATH%',xbmc.translatePath(self.launch_filenames[0])) #Replace ROM filepath
			self.external_launch_command = self.external_launch_command.replace('%ROM_BASE_PATH%',os.path.join(os.path.split(xbmc.translatePath(self.launch_filenames[0]))[0],'')) #Replace ROM Base path
			
			if any([x in self.external_launch_command for x in self.IAGL.additional_supported_external_emulators]): #Non Retroarch emulator requested
				other_emulator_key = [x for x in self.IAGL.additional_supported_external_emulators if x in self.external_launch_command][0]
				other_emulator = self.IAGL.additional_supported_external_emulator_settings.split('|')[self.IAGL.additional_supported_external_emulators.index(other_emulator_key)]
				other_emulator_found = False
				xbmc.log(msg='IAGL:  Requested other emulator application %(other_emulator)s' % {'other_emulator': other_emulator}, level=xbmc.LOGDEBUG)
				for ii in range(1,4):
					try:
						if other_emulator in self.IAGL.handle.getSetting(id='iagl_external_additional_emulator_%(em_idx)s_type'%{'em_idx': ii}): #Emulator setting found
							if self.IAGL.handle.getSetting(id='iagl_external_additional_emulator_%(em_idx)s_path'%{'em_idx': ii}) is not None and len(self.IAGL.handle.getSetting(id='iagl_external_additional_emulator_%(em_idx)s_path'%{'em_idx': ii}))>0:
								other_emulator_found = True
								self.external_launch_command = self.external_launch_command.replace('%'+other_emulator_key+'%',xbmc.translatePath(self.IAGL.handle.getSetting(id='iagl_external_additional_emulator_%(em_idx)s_path'%{'em_idx': ii}))) #Replace app path with user setting
					except Exception as exc:
						xbmc.log(msg='IAGL:  Unable to identify other emulator.  Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGDEBUG)
				if not other_emulator_found:					
					xbmc.log(msg='IAGL:  Unable to find emulator application %(other_emulator)s in settings' % {'other_emulator': other_emulator}, level=xbmc.LOGDEBUG)

			if '%RETROARCH_CORE_DIR%' in self.external_launch_command:
				core_found_idx = None
				for jj in range(0,len(self.IAGL.possible_linux_core_directories)):
					try:
						if xbmcvfs.exists(os.path.join(self.IAGL.possible_linux_core_directories[jj],os.path.split(self.external_launch_command.split('%RETROARCH_CORE_DIR%')[-1].split('.so')[0]+'.so')[-1])):
							core_found_idx = jj
					except:
						pass
				if core_found_idx is not None:
					xbmc.log(msg='IAGL:  The Retroarch Core directory was found at %(core_dir)s' % {'core_dir': self.IAGL.possible_linux_core_directories[core_found_idx]}, level=xbmc.LOGDEBUG)
					self.external_launch_command = self.external_launch_command.replace('%RETROARCH_CORE_DIR%',self.IAGL.possible_linux_core_directories[core_found_idx])
				else:
					xbmc.log(msg='IAGL:  The Retroarch Core directory could not be found.  Defaulting to %(core_dir)s' % {'core_dir': self.IAGL.default_linux_core_directory}, level=xbmc.LOGDEBUG)
					self.external_launch_command = self.external_launch_command.replace('%RETROARCH_CORE_DIR%',self.IAGL.default_linux_core_directory)

			# if self.IAGL.handle.getSetting(id='iagl_netplay_enable_netplay') == 'Enabled':
			if self.IAGL.get_setting_as_bool(self.IAGL.handle.getSetting(id='iagl_netplay_enable_netplay')):
				current_netplay_command = ''
				# if self.IAGL.handle.getSetting(id='iagl_netplay_hostclient') == 'Player 1 Host': #Old method pre language update
				if int(self.IAGL.handle.getSetting(id='iagl_netplay_hostclient')) == 0:
					xbmc.log(msg='IAGL:  Attempting to start netplay as player 1 host', level=xbmc.LOGDEBUG)
					current_netplay_command = current_netplay_command+'--host '
					# if self.IAGL.handle.getSetting(id='iagl_netplay_frames') == 'Enabled':
					if self.IAGL.get_setting_as_bool(self.IAGL.handle.getSetting(id='iagl_netplay_frames')):
						current_netplay_command = current_netplay_command+'--frames '
						current_netplay_command = current_netplay_command+'--nick "'+str(self.IAGL.handle.getSetting(id='iagl_netplay_nickname1'))+'" '
				# elif self.IAGL.handle.getSetting(id='iagl_netplay_hostclient') == 'Player 2 Client':
				elif int(self.IAGL.handle.getSetting(id='iagl_netplay_hostclient')) == 1:
					xbmc.log(msg='IAGL:  Attempting to start netplay as player 2 client', level=xbmc.LOGDEBUG)
					current_netplay_command = current_netplay_command+'--connect '+str(self.IAGL.handle.getSetting(id='iagl_netplay_IP'))+' '
					current_netplay_command = current_netplay_command+'--port '+str(self.IAGL.handle.getSetting(id='iagl_netplay_port'))+' '
					# if self.IAGL.handle.getSetting(id='iagl_netplay_frames') == 'Enabled':
					if self.IAGL.get_setting_as_bool(self.IAGL.handle.getSetting(id='iagl_netplay_frames')):
						current_netplay_command = current_netplay_command+'--frames '
						current_netplay_command = current_netplay_command+'--nick "'+str(self.IAGL.handle.getSetting(id='iagl_netplay_nickname2'))+'" '
				# elif self.IAGL.handle.getSetting(id='iagl_netplay_hostclient') == 'Spectator':
				else:
					xbmc.log(msg='IAGL:  Attempting to start netplay as no player / spectator', level=xbmc.LOGDEBUG)
					current_netplay_command = current_netplay_command+'--spectate '+str(self.IAGL.handle.getSetting(id='iagl_netplay_IP'))+' '
					current_netplay_command = current_netplay_command+'--port '+str(self.IAGL.handle.getSetting(id='iagl_netplay_port'))+' '
					# if self.IAGL.handle.getSetting(id='iagl_netplay_frames') == 'Enabled':
					if self.IAGL.get_setting_as_bool(self.IAGL.handle.getSetting(id='iagl_netplay_frames')):
						current_netplay_command = current_netplay_command+'--frames '
						current_netplay_command = current_netplay_command+'--nick "'+str(self.IAGL.handle.getSetting(id='iagl_netplay_nickname3'))+'" '
					else:
						current_netplay_command = ''
			else: #Replace any netplay flags with blank space if netplay is not enabled
				current_netplay_command = ''

			self.external_launch_command = self.external_launch_command.replace('%NETPLAY_COMMAND%',current_netplay_command)

	def launch_external(self):
		import subprocess
		self.update_external_launch_command()
		if self.external_launch_command != 'none':
			if xbmc.Player().isPlaying() and not self.IAGL.get_setting_as_bool(self.IAGL.handle.getSetting(id='iagl_enable_stop_media_before_launch')):
				xbmc.Player().stop()
				xbmc.sleep(500)
			if not self.IAGL.get_setting_as_bool(self.IAGL.handle.getSetting(id='iagl_enable_stop_media_before_launch')):
				xbmc.audioSuspend()
				xbmc.enableNavSounds(False)
			xbmc.log(msg='IAGL:  Sending Launch Command: %(external_command)s' % {'external_command': self.external_launch_command}, level=xbmc.LOGNOTICE)
			external_command = subprocess.call(self.external_launch_command,shell=True)
			if not self.IAGL.get_setting_as_bool(self.IAGL.handle.getSetting(id='iagl_enable_stop_media_before_launch')):
				xbmc.audioResume()
				xbmc.enableNavSounds(True)
			return True
		else:
			return False

	def launch_external_android(self):
		import subprocess
		self.update_external_launch_command()
		if self.external_launch_command != 'none':
			if xbmc.Player().isPlaying():
				xbmc.Player().stop()
				xbmc.sleep(500)
			xbmc.audioSuspend()
			xbmc.enableNavSounds(False)
			if self.IAGL.handle.getSetting(id='iagl_external_user_external_env') == 'Android Aarch64':
				android_stop_command = '/system/bin/am force-stop com.retroarch.aarch64'  #Changed to add stop command in the external launch command arguments
			else:
				android_stop_command = '/system/bin/am force-stop com.retroarch'  #Changed to add stop command in the external launch command arguments
				
			if int(self.IAGL.handle.getSetting(id='iagl_android_command_type')) == 1: #Subprocess normal
				xbmc.log(msg='IAGL:  Android subprocess (normal shell) external launch selected', level=xbmc.LOGDEBUG)
				executable_path = '/system/bin/sh' #This is the path to the normal shell for most android installations
				if self.IAGL.get_setting_as_bool(self.IAGL.handle.getSetting(id='iagl_enable_android_stop_command')):
					try:
						xbmc.log(msg='IAGL:  Sending Android Stop Command: %(android_stop_command)s' % {'android_stop_command': android_stop_command}, level=xbmc.LOGNOTICE)
						retcode = subprocess.call(android_stop_command,shell=True,executable=executable_path)
						xbmc.log(msg='IAGL:  Android returned %(return_code)s' % {'return_code': retcode}, level=xbmc.LOGDEBUG)
					except Exception as exc:
						xbmc.log(msg='IAGL: Error sending subprocess (normal shell) stop command, Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
				xbmc.sleep(500)
				try:
					xbmc.log(msg='IAGL:  Sending Android Launch Command: %(external_command)s' % {'external_command': self.external_launch_command}, level=xbmc.LOGNOTICE)
					retcode = subprocess.call(self.external_launch_command,shell=True,executable=executable_path)
					xbmc.log(msg='IAGL:  Android returned %(return_code)s' % {'return_code': retcode}, level=xbmc.LOGDEBUG)
				except Exception as exc:
					xbmc.log(msg='IAGL: Error sending subprocess (normal shell) command, Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
			elif int(self.IAGL.handle.getSetting(id='iagl_android_command_type')) == 2: #Subprocess root
				xbmc.log(msg='IAGL:  Android subprocess (root shell) external launch selected', level=xbmc.LOGDEBUG)
				executable_path = '/system/xbin/su' #This is the method for root shell for most rooted android installations
				if self.IAGL.get_setting_as_bool(self.IAGL.handle.getSetting(id='iagl_enable_android_stop_command')):
					try:
						xbmc.log(msg='IAGL:  Sending Android Stop Command: %(android_stop_command)s' % {'android_stop_command': android_stop_command}, level=xbmc.LOGNOTICE)
						retcode = subprocess.call(android_stop_command,shell=True,executable=executable_path)
						xbmc.log(msg='IAGL:  Android returned %(return_code)s' % {'return_code': retcode}, level=xbmc.LOGDEBUG)
					except Exception as exc:
						xbmc.log(msg='IAGL: Error sending subprocess (root shell) stop command, Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
				xbmc.sleep(500)
				try:
					xbmc.log(msg='IAGL:  Sending Android Launch Command: %(external_command)s' % {'external_command': self.external_launch_command}, level=xbmc.LOGNOTICE)
					retcode = subprocess.call(self.external_launch_command,shell=True,executable=executable_path)
					xbmc.log(msg='IAGL:  Android returned %(return_code)s' % {'return_code': retcode}, level=xbmc.LOGDEBUG)
				except Exception as exc:
					xbmc.log(msg='IAGL: Error sending subprocess (root shell) command, Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
			else: #Default
				xbmc.log(msg='IAGL:  Android os.system external launch selected', level=xbmc.LOGDEBUG)
				if self.IAGL.get_setting_as_bool(self.IAGL.handle.getSetting(id='iagl_enable_android_stop_command')):
					try:
						xbmc.log(msg='IAGL:  Sending Android Stop Command: %(android_stop_command)s' % {'android_stop_command': android_stop_command}, level=xbmc.LOGNOTICE)
						retcode = os.system(android_stop_command)
						xbmc.log(msg='IAGL:  Android returned %(return_code)s' % {'return_code': retcode}, level=xbmc.LOGDEBUG)
					except Exception as exc:
						xbmc.log(msg='IAGL: Error sending os.system stop command, Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
				xbmc.sleep(500)
				try:
					xbmc.log(msg='IAGL:  Sending Android Launch Command: %(external_command)s' % {'external_command': self.external_launch_command}, level=xbmc.LOGNOTICE)
					retcode = os.system(self.external_launch_command)
					xbmc.log(msg='IAGL:  Android returned %(return_code)s' % {'return_code': retcode}, level=xbmc.LOGDEBUG)
				except Exception as exc:
					xbmc.log(msg='IAGL: Error sending os.system command, Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
			xbmc.audioResume()
			xbmc.enableNavSounds(True)
			return True
		else:
			return False

#InfoDialog class
class iagl_infodialog(xbmcgui.WindowXMLDialog):
	def __init__(self, *args, **kwargs):
		xbmcgui.Window(10000).setProperty('iagl.trailer_started','False')
		try:
			self.current_game = kwargs['current_game']['listitem']
		except Exception as exc: #except Exception, (exc):
			self.current_game = None
			xbmc.log(msg='IAGL Error:  Infodialog did not find current game, Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
		try:
			self.current_json = kwargs['current_game']['json']
		except Exception as exc: #except Exception, (exc):
			self.current_json = None
			xbmc.log(msg='IAGL Error:  Infodialog did not find current json, Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
		try:
			self.game_id = kwargs['current_game']['game_id']
		except Exception as exc: #except Exception, (exc):
			self.game_id = None
			xbmc.log(msg='IAGL Error:  Infodialog did not find current game_id, Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
		try:
			self.current_fanart = kwargs['current_game']['fanarts']
		except Exception as exc: #except Exception, (exc):
			self.current_fanart = None
			xbmc.log(msg='IAGL Error:  Infodialog did not find current fanart, Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
		try:
			self.current_boxart_and_snapshots = kwargs['current_game']['boxart_and_snapshots']
		except Exception as exc: #except Exception, (exc):
			self.current_boxart_and_snapshots = None
			xbmc.log(msg='IAGL Error:  Infodialog did not find current box and snapshots, Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
		try:
			self.current_banners = kwargs['current_game']['banners']
		except Exception as exc: #except Exception, (exc):
			self.current_banners = None
			xbmc.log(msg='IAGL Error:  Infodialog did not find current banners, Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
		try:
			self.current_trailer = kwargs['current_game']['trailer']
		except Exception as exc: #except Exception, (exc):
			self.current_trailer = None
			xbmc.log(msg='IAGL Error:  Infodialog did not find current trailer, Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
		try:
			self.autoplay_trailer = kwargs['current_game']['autoplay_trailer']
		except Exception as exc: #except Exception, (exc):
			self.autoplay_trailer = 'No'
			xbmc.log(msg='IAGL Error:  Infodialog did not find current trailer, Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
		try:
			self.return_home = kwargs['current_game']['return_home']
		except Exception as exc: #except Exception, (exc):
			self.return_home = False
			xbmc.log(msg='IAGL Error:  Infodialog did not find current return parameter, Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)

		xbmc.log(msg='IAGL:  InfoDialog Initialized', level=xbmc.LOGDEBUG)
	def onInit(self):
		self.onaction_id_exit = [10, 13, 92] #Default exit keys to close window via keyboard / controller
		self.onclick_id_download = 3001
		self.onclick_id_launch = 3002
		self.onclick_id_exit = 3003
		self.game_info_listitem_id = 113 #Invisible listitem for game metadata
		self.fanart_listitem_id = 114 #Invisible listitem for game fanart
		self.boxart_snapshot_listitem_id = 115 #Invisible listitem for game boxarts and snapshots
		self.banner_listitem_id = 116 #Invisible listitem for game banners

		self.current_game_listitem = self.getControl(self.game_info_listitem_id)
		self.current_game_listitem.addItem(self.current_game)

		if self.current_fanart is not None:
			self.current_fanart_listitems = self.getControl(self.fanart_listitem_id)
			for fanart_items in self.current_fanart:
				self.current_fanart_listitems.addItem(fanart_items)
		if self.current_boxart_and_snapshots is not None:
			self.boxart_and_snapshot_listitems = self.getControl(self.boxart_snapshot_listitem_id)
			for box_and_snap_items in self.current_boxart_and_snapshots:
				self.boxart_and_snapshot_listitems.addItem(box_and_snap_items)
		if self.current_banners is not None:
			self.banner_listitems = self.getControl(self.banner_listitem_id)
			for banner_items in self.current_banners:
				self.banner_listitems.addItem(banner_items)

		try:
			self.download_button = self.getControl(self.onclick_id_download) #Download Only
		except:
			self.download_button = None
			xbmc.log(msg='IAGL:  Download Button (Control 3001) is not present', level=xbmc.LOGDEBUG)
		try:
			self.launch_button = self.getControl(self.onclick_id_launch) #Download and Launch
		except:
			self.launch_button = None
			xbmc.log(msg='IAGL:  Download and Launch Button (Control 3002) is not present', level=xbmc.LOGDEBUG)
		try:
			self.exit_button = self.getControl(self.onclick_id_exit) #Close
		except:
			self.exit_button = None
			xbmc.log(msg='IAGL:  Close Button (Control 3003) is not present', level=xbmc.LOGDEBUG)

		#Enable the buttons, these are disabled when one is selected to avoid double taps
		if self.download_button is not None:
			self.download_button.setEnabled(True)
		if self.launch_button is not None:   
			self.launch_button.setEnabled(True)
		if self.exit_button is not None:   
			self.exit_button.setEnabled(True)

		#Auto play trailer if settings are defined
		if self.autoplay_trailer=='Yes' or self.autoplay_trailer=='1':
			if self.current_trailer is not None:
				if xbmc.Player().isPlaying():
					xbmc.Player().stop()
					xbmc.sleep(100)
				xbmcgui.Window(10000).setProperty('iagl.trailer_started','True')
				xbmc.sleep(250)
				xbmc.Player().play(self.current_trailer, windowed=True)
		else:
			xbmcgui.Window(10000).setProperty('iagl.trailer_started','False')

	def onAction(self, action):
		xbmc.log(msg='IAGL:  InfoDialog Action ID %(action)s' % {'action': action.getId()}, level=xbmc.LOGDEBUG)
		if action in self.onaction_id_exit:
			self.closeDialog()

	def onClick(self, controlId):
		xbmc.log(msg='IAGL:  InfoDialog Click %(controlId)s' % {'controlId': controlId}, level=xbmc.LOGDEBUG)
		if controlId == self.onclick_id_download: #Download Only
			self.action_download_only()

		if controlId == self.onclick_id_launch: #Download then Launch
			self.action_download_and_launch()

		if controlId == self.onclick_id_exit: #Exit Infodialog
			self.closeDialog()

	def closeDialog(self):
		xbmc.log(msg='IAGL:  InfoDialog Closed', level=xbmc.LOGDEBUG)
		xbmc.executebuiltin('Dialog.Close(busydialog)') #Try and close busy dialog if it is for some reason open
		self.close()
		if self.return_home:
			xbmc.log(msg='IAGL:  Returning to Home', level=xbmc.LOGDEBUG)
			self.close()
			xbmc.executebuiltin('ActivateWindow(home)')
			
	def action_download_only(self):
		#Temporarily disable these buttons to avoid double taps
		if self.download_button is not None:
			self.download_button.setEnabled(False)
		if self.launch_button is not None:   
			self.launch_button.setEnabled(False)
		IAGL_DL = iagl_download(self.current_json) #Initialize download object
		download_and_process_success = IAGL_DL.download_and_process_game_files() #Download files
		if type(download_and_process_success) is bool:
			download_and_process_success = [download_and_process_success]
		current_dialog = xbmcgui.Dialog()
		if False in download_and_process_success:  #Bad files found
			if True in download_and_process_success:  #Good and Bad files found
				ok_ret = current_dialog.ok(IAGL_DL.IAGL.loc_str(30203),IAGL_DL.IAGL.loc_str(30303) % {'game_title': IAGL_DL.current_game_title, 'fail_reason': IAGL_DL.download_fail_reason})
			else:  #Only bad files found
				ok_ret = current_dialog.ok(IAGL_DL.IAGL.loc_str(30203),IAGL_DL.IAGL.loc_str(30304) % {'game_title': IAGL_DL.current_game_title, 'fail_reason': IAGL_DL.download_fail_reason})
		else:  #So far so good, now process the files
			ok_ret = current_dialog.notification(IAGL_DL.IAGL.loc_str(30202),IAGL_DL.IAGL.loc_str(30302) % {'game_title': IAGL_DL.current_game_title},xbmcgui.NOTIFICATION_INFO,IAGL_DL.IAGL.notification_time)
		del current_dialog
		#Re-Enable buttons
		if self.download_button is not None:
			self.download_button.setEnabled(True)
		if self.launch_button is not None:   
			self.launch_button.setEnabled(True)

	def action_download_and_launch(self):
		#Temporarily disable these buttons to avoid double taps
		if self.download_button is not None:
			self.download_button.setEnabled(False)
		if self.launch_button is not None:   
			self.launch_button.setEnabled(False)
		IAGL_DL = iagl_download(self.current_json) #Initialize download object
		download_and_process_success = IAGL_DL.download_and_process_game_files() #Download files
		if type(download_and_process_success) is bool:
			download_and_process_success = [download_and_process_success]
		if False not in download_and_process_success:
			IAGL_LAUNCH = iagl_launch(self.current_json,IAGL_DL.current_processed_files,self.game_id) #Initialize launch object
			IAGL_LAUNCH.launch() #Launch Game
			if IAGL_LAUNCH.launch_success:
				xbmc.log(msg='IAGL:  Game Launched: %(game_title)s' % {'game_title': IAGL_DL.current_game_title}, level=xbmc.LOGDEBUG)
				self.closeDialog()
		else:
			current_dialog = xbmcgui.Dialog()
			ok_ret = current_dialog.ok(IAGL_DL.IAGL.loc_str(30203),IAGL_DL.IAGL.loc_str(30305) % {'game_title': IAGL_DL.current_game_title, 'fail_reason': IAGL_DL.download_fail_reason})
		#Re-Enable buttons
		if self.download_button is not None:
			self.download_button.setEnabled(True)
		if self.launch_button is not None:   
			self.launch_button.setEnabled(True)

#InfoDialog class
class iagl_TOUdialog(xbmcgui.WindowXMLDialog):
	def __init__(self, *args, **kwargs):
		xbmc.log(msg='IAGL:  TOU Dialog Initialized', level=xbmc.LOGDEBUG)
	def onInit(self):
		self.action_exitkeys_id = [10, 13, 92]
		self.control_id_button_action1 = 3001 #Agree and Close
		self.control_id_button_exit = 3003 #Do not Agree and Close
		self.button_action1 = self.getControl(self.control_id_button_action1)
		self.button_exit = self.getControl(self.control_id_button_exit)
	def onAction(self, action):
		# Same as normal python Windows.  Same as do not agree
		if action in self.action_exitkeys_id:
			self.closeDialog()
	def onClick(self, controlId):
		#Agree and Close
		if controlId == self.control_id_button_action1:
			xbmcaddon.Addon(id='plugin.program.iagl').setSetting(id='iagl_hidden_bool_tou',value='true')
			xbmc.log(msg='IARL:  Terms of Use Agree', level=xbmc.LOGDEBUG)
			self.closeDialog()
		#Do not Agree
		elif controlId == self.control_id_button_exit:
			xbmc.log(msg='IARL:  Terms of Use do not Agree', level=xbmc.LOGDEBUG)
			self.closeDialog()
	def closeDialog(self):
		self.close()

#Text Viewer Dialog class
class iagl_textviewer_dialog(xbmcgui.WindowXMLDialog):
	def __init__(self, *args, **kwargs):
		xbmc.log(msg='IAGL:  Text Viewer Dialog Initialized', level=xbmc.LOGDEBUG)
	def onInit(self):
		self.action_exitkeys_id = [10, 13, 92]
		self.control_id_button_close = [22003, 22004] #Close
	def onAction(self, action):
		if action in self.action_exitkeys_id:
			self.closeDialog()
	def onClick(self, controlId):
		if controlId in self.control_id_button_close:
			self.closeDialog()
	def closeDialog(self):
		xbmcgui.Window(10000).clearProperty('TextViewer_Header')
		xbmcgui.Window(10000).clearProperty('TextViewer_Text')
		self.close()

def etree_to_dict(t):
	d = {t.tag: {} if t.attrib else None}
	children = list(t)
	if children:
		dd = defaultdict(list)
		for dc in map(etree_to_dict, children):
			for k, v in dc.items():
				dd[k].append(v)
		d = {t.tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
	if t.attrib:
		d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
	if t.text:
		text = t.text.strip()
		if children or t.attrib:
			if text:
				d[t.tag]['#text'] = text
		else:
			d[t.tag] = text
	return d

def dict_to_etree(d):
	def _to_etree(d, root):
		if not d:
			pass
		elif isinstance(d, str) or isinstance(d,unicode):
			root.text = d
		elif isinstance(d, dict):
			for k,v in d.items():
				assert isinstance(k, str) or isinstance(k, unicode)
				if k.startswith('#'):
					assert k == '#text' and isinstance(v, str) or isinstance(v, unicode)
					root.text = v
				elif k.startswith('@'):
					assert isinstance(v, str) or isinstance(v, unicode)
					root.set(k[1:], v)
				elif isinstance(v, list):
					for e in v:
						_to_etree(e, ET.SubElement(root, k))
				else:
					_to_etree(v, ET.SubElement(root, k))
		else:
			assert d == 'invalid type', (type(d), d)
	assert isinstance(d, dict) and len(d) == 1
	tag, body = next(iter(d.items()))
	node = ET.Element(tag)
	_to_etree(body, node)
	return node

def get_crc32_from_string(string_in):
	return '%X'%(zlib.crc32(str(string_in)) & 0xFFFFFFFF)

def get_crc32(filename):
	# return zlib_csum(filename, zlib.crc32)
	return zlib_csum_xbmcvfs(filename, zlib.crc32)

def zlib_csum(filename, func):
	csum = None
	# chunk_size = 1024
	chunk_size = 10485760 #10MB
	# with open(filename, 'rb') as f:
	with io.FileIO(filename, 'rb') as f: #Using FileIO as open fails on Android
		try:
			chunk = f.read(chunk_size)
			if len(chunk)>0:
				csum = func(chunk)
				while True:
					chunk = f.read(chunk_size)
					if len(chunk)>0:
						csum = func(chunk, csum)
					else:
						break
		finally:
			f.close()
	if csum is not None:
		csum = csum & 0xffffffff

	return '%X'%(csum & 0xFFFFFFFF)

def zlib_csum_xbmcvfs(filename, func):
	csum = None
	# chunk_size = 1024
	chunk_size = 10485760 #10MB
	with closing(xbmcvfs.File(filename)) as f:
		try:
			chunk = bytes(f.readBytes(chunk_size))
			if len(chunk)>0:
				csum = func(chunk)
				while True:
					chunk = bytes(f.readBytes(chunk_size))
					if len(chunk)>0:
						csum = func(chunk, csum)
					else:
						break
		finally:
			f.close()
	if csum is None:
		return 'UNKNOWN'
	else:
		csum = csum & 0xffffffff
		return '%X'%(csum & 0xFFFFFFFF)

def get_directory_size(directory_in):
	if scandir_import_success:
		return get_directory_size_scandir(directory_in)
	else:
		return get_directory_size_xbmcvfs(directory_in)

def get_directory_size_scandir(directory_in):
	current_size = 0
	for entry in scandir(directory_in):
		if entry.is_file():
			current_size += entry.stat().st_size
		elif entry.is_dir():
			current_size += get_directory_size(entry.path)
	return current_size

def get_directory_size_xbmcvfs(directory_in): #Twice as slow as the method above, but maybe safer / more compatible?
	current_size = 0
	dirs_in_dir, files_in_dir = xbmcvfs.listdir(os.path.join(directory_in,''))
	for ff in files_in_dir:
		current_size += xbmcvfs.Stat(os.path.join(directory_in,ff)).st_size()
	for dd in dirs_in_dir:
		current_size += get_directory_size_xbmcvfs(os.path.join(directory_in,dd))
	return current_size

def get_all_files_in_directory(directory_in): #Dont use this by default, assume it could be a 'special' path
	current_files = list()
	for entry in scandir(directory_in):
		if entry.is_file():
			current_files.append(entry.path)
		elif entry.is_dir():
			current_files = current_files+get_all_files_in_directory(entry.path)
	return current_files

def get_all_files_in_directory_xbmcvfs(directory_in): #Twice as slow as the method above, but maybe safer / more compatible?
	current_files = list()
	dirs_in_dir, files_in_dir = xbmcvfs.listdir(os.path.join(directory_in,''))
	current_files = [os.path.join(directory_in,ff) for ff in files_in_dir if ff is not None]
	for dd in dirs_in_dir:
		dirs_in_dir2, files_in_dir2 = xbmcvfs.listdir(os.path.join(directory_in,dd,''))
		current_files = current_files+[os.path.join(directory_in,dd,ff) for ff in files_in_dir2 if ff is not None]
		for dd2 in dirs_in_dir2:
			dirs_in_dir3, files_in_dir3 = xbmcvfs.listdir(os.path.join(directory_in,dd,dd2,''))
			current_files = current_files+[os.path.join(directory_in,dd,dd2,ff) for ff in files_in_dir3 if ff is not None]
			for dd3 in dirs_in_dir3:
				dirs_in_dir4, files_in_dir4 = xbmcvfs.listdir(os.path.join(directory_in,dd,dd2,dd3,'')) #Go down 4 levels to look for various files for launching
				current_files = current_files+[os.path.join(directory_in,dd,dd2,dd3,ff) for ff in files_in_dir4 if ff is not None]
	return current_files

def move_file_to_directory(file_in,directory_to):
	overall_success = True
	file_out = None
	new_filepath = os.path.join(directory_to,os.path.split(file_in)[-1])
	success = xbmcvfs.rename(file_in,new_filepath)  #Attempt to move the file first
	if not success:
		success = xbmcvfs.copy(file_in,new_filepath) #If move does not work, then copy
		if not success:
			overall_success = False
			xbmc.log(msg='IAGL:  The file could not be moved and the copy failed: %(file_from)s, to: %(file_to)s' % {'file_from': file_in, 'file_to': new_filepath}, level=xbmc.LOGDEBUG)
		else:
			xbmc.log(msg='IAGL:  File move failed, so the file was copied from: %(file_from)s, to: %(file_to)s' % {'file_from': file_in, 'file_to': new_filepath}, level=xbmc.LOGDEBUG)
			if not xbmcvfs.delete(file_in):
				xbmc.log(msg='IAGL:  Unable to delete the file after copy: %(file_from)s' % {'file_from': file_in}, level=xbmc.LOGDEBUG)
	else:
		xbmc.log(msg='IAGL:  File moved from: %(file_from)s, to: %(file_to)s' % {'file_from': file_in, 'file_to': new_filepath}, level=xbmc.LOGDEBUG)
	if overall_success:
		file_out = new_filepath

	return file_out

def move_directory_contents_xbmcvfs(directory_from,directory_to):
	overall_success = True
	files_out = list()
	dirs_in_dir, files_in_dir = xbmcvfs.listdir(os.path.join(directory_from,''))
	for ff in files_in_dir:
		success = xbmcvfs.rename(os.path.join(directory_from,ff),os.path.join(directory_to,ff))  #Attempt to move the file first
		if not success:
			success = xbmcvfs.copy(os.path.join(directory_from,ff),os.path.join(directory_to,ff)) #If move does not work, then copy
			if not success:
				overall_success = False
			else:
				xbmc.log(msg='IAGL:  File move failed, so the file was copied from: %(file_from)s, to: %(file_to)s' % {'file_from': os.path.join(directory_from,ff), 'file_to': os.path.join(directory_to,ff)}, level=xbmc.LOGDEBUG)
				if not xbmcvfs.delete(os.path.join(directory_from,ff)):
					xbmc.log(msg='IAGL:  Unable to delete the file after copy: %(file_from)s' % {'file_from': os.path.join(directory_from,ff)}, level=xbmc.LOGDEBUG)
		else:
			xbmc.log(msg='IAGL:  File moved from: %(file_from)s, to: %(file_to)s' % {'file_from': os.path.join(directory_from,ff), 'file_to': os.path.join(directory_to,ff)}, level=xbmc.LOGDEBUG)
		if success:
			files_out.append(os.path.join(directory_to,ff))
	for dd in dirs_in_dir:
		success = xbmcvfs.mkdir(os.path.join(directory_to,dd))
		if not success:
			overall_success = False
		else:
			files_out2, success = move_directory_contents_xbmcvfs(os.path.join(directory_from,dd),os.path.join(directory_to,dd))
		if not success:
			overall_success = False
		else:
			files_out = files_out + files_out2
	if overall_success:
		if not xbmcvfs.rmdir(os.path.join(directory_from,'')):
			try:
				shutil.rmtree(os.path.join(directory_from,''))
			except Exception as exc: #except Exception, (exc):
				xbmc.log(msg='IAGL:  Unable to delete the folder after moving files: %(dir_from)s.  Exception %(exc)s' % {'dir_from': os.path.join(directory_from,''), 'exc': exc}, level=xbmc.LOGDEBUG)
	return files_out, overall_success

def extract_all_libarchive(archive_file,directory_to):
	overall_success = True
	files_out = list()
	if 'archive://' in archive_file:
		archive_path = archive_file
	else:
		archive_path = 'archive://%(archive_file)s' % {'archive_file': url_quote(xbmc.translatePath(archive_file))}
	dirs_in_archive, files_in_archive = xbmcvfs.listdir(archive_path)
	for ff in files_in_archive:
		if not xbmcvfs.exists(os.path.join(xbmc.translatePath(directory_to),ff)):
			file_from = os.path.join(archive_path,ff).replace('\\','/') #Windows unexpectadely requires a forward slash in the path
			success = xbmcvfs.copy(file_from,os.path.join(xbmc.translatePath(directory_to),ff)) #Attempt to move the file first
			if not success:
				xbmc.log(msg='IAGL:  Error extracting file %(ff)s from archive %(archive_file)s' % {'ff': ff,'archive_file':archive_file}, level=xbmc.LOGDEBUG)
				overall_success = False
			else:
				xbmc.log(msg='IAGL:  Extracted file %(ff)s from archive %(archive_file)s' % {'ff': ff,'archive_file':archive_file}, level=xbmc.LOGDEBUG)
				files_out.append(os.path.join(xbmc.translatePath(directory_to),ff))
		else:
			xbmc.log(msg='IAGL:  File %(ff)s already exists and was not extracted from archive %(archive_file)s' % {'ff': ff,'archive_file':archive_file}, level=xbmc.LOGDEBUG)
			files_out.append(os.path.join(xbmc.translatePath(directory_to),ff))
	for dd in dirs_in_archive:
		if xbmcvfs.exists(os.path.join(xbmc.translatePath(directory_to),dd)) or xbmcvfs.mkdir(os.path.join(xbmc.translatePath(directory_to),dd)):
			xbmc.log(msg='IAGL:  Created folder %(dd)s for archive %(archive_file)s' % {'dd': os.path.join(xbmc.translatePath(directory_to),dd,''),'archive_file':archive_file}, level=xbmc.LOGDEBUG)
			files_out2, success2 = extract_all_libarchive(os.path.join(archive_path,dd,'').replace('\\','/'),os.path.join(directory_to,dd)) #Windows unexpectadely requires a forward slash in the path
			if success2:
				files_out = files_out + files_out2
			else:
				overall_success = False
		else:
			overall_success = False
			xbmc.log(msg='IAGL:  Unable to create the folder %(dir_from)s for libarchive extraction' % {'dir_from': os.path.join(xbmc.translatePath(directory_to),dd)}, level=xbmc.LOGDEBUG)
	return files_out, overall_success

# def move_directory_contents_libarchive(directory_from,directory_to):
# 	#not yet working - seems to be a bug with libarchive
# 	overall_success = True
# 	files_out = list()

# 	dirs_in_dir, files_in_dir = xbmcvfs.listdir('archive://%(directory_from)s' % {'directory_from': url_quote(directory_from)})

# 	for ff in files_in_dir:
# 		success = xbmcvfs.copy(os.path.join('archive://%(directory_from)s' % {'directory_from': url_quote(directory_from)},ff),os.path.join(directory_to,ff))  #Attempt to move the file first
# 		if not success:
# 			overall_success = False
# 		else:
# 			files_out.append(os.path.join(directory_to,ff))
# 	for dd in dirs_in_dir:
# 		success = xbmcvfs.mkdir(os.path.join(directory_to,dd))
# 		if not success:
# 			overall_success = False
# 		else:
# 			files_out2, success = move_directory_contents_libarchive(os.path.join(directory_from,dd),os.path.join(directory_to,dd))
# 		if not success:
# 			overall_success = False
# 		else:
# 			files_out = files_out + files_out2
# 	# if overall_success:
# 	# 	if not xbmcvfs.delete(os.path.join(directory_from,'')):
# 	# 		xbmc.log(msg='IAGL:  Unable to delete the archive after moving files: %(dir_from)s' % {'dir_from': os.path.join(directory_from,'')}, level=xbmc.LOGDEBUG)
# 	return files_out, overall_success

def clean_file_folder_name(text_in):
	text_out = text_in
	keep_characters = [' ','_']
	try:
		text_out = ''.join(c for c in text_in if c.isalnum() or c in keep_characters).rstrip()
		text_out = text_out.replace('  ',' ').replace('  ',' ').replace('  ',' ').replace('  ',' ')
		for ii in range(1,50):
			text_out = text_out.replace('Disc %(int_in)s'%{'int_in':ii},'').replace('disc %(int_in)s'%{'int_in':ii},'')
			text_out = text_out.replace('Disk %(int_in)s'%{'int_in':ii},'').replace('disk %(int_in)s'%{'int_in':ii},'')
		text_out = text_out.replace(' ','_')
	except:
		text_out = text_in

	return text_out