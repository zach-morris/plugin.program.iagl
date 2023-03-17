#Internet Archive Game Launcher v3.X (For Kodi v19+)
#Zach Morris
#https://github.com/zach-morris/plugin.program.iagl
import os, json
# from kodi_six import xbmc, xbmcplugin, xbmcgui, xbmcvfs
import xbmc, xbmcplugin, xbmcgui, xbmcvfs
from . utils import *
import time

class iagl_addon(object):
	def __init__(self):
		# last_time = time.time()
		self.name = ADDON_NAME
		self.handle = ADDON_HANDLE
		self.version = str(ADDON_HANDLE.getAddonInfo('version')) #The current version number that the addon is being run at
		self.addon_path = ADDON_PATH
		self.start_time = str(time.time()) #The current time that the addon was run
		self.last_version = get_mem_cache('iagl_version') #The last version number that the addon was run at
		self.last_start_time = get_mem_cache('iagl_start_time') #The last time the addon was run
		set_mem_cache('iagl_version',self.version)
		set_mem_cache('iagl_start_time',self.start_time)
		self.title = ADDON_TITLE
		self.kodi_user = dict()
		#Add this if it ever is merged https://github.com/xbmc/xbmc/pull/17265
		self.kodi_user['os'] = xbmc.getInfoLabel('System.OSVersionInfo')
		self.kodi_user['version'] = xbmc.getInfoLabel('System.BuildVersion')
		self.kodi_user['username'] = xbmc.getInfoLabel('System.ProfileName')
		#Network information for netplay
		self.kodi_user['IP'] = xbmc.getInfoLabel('Network.IPAddress').replace('\n','')
		self.kodi_user['gateway'] = xbmc.getInfoLabel('Network.GatewayAddress').replace('\n','')
		self.kodi_user['subnet'] = xbmc.getInfoLabel('Network.SubnetMask').replace('\n','')
		self.kodi_user['current_path'] = xbmc.getInfoLabel('Container.FolderPath')
		self.kodi_user['current_folder'] = xbmc.getInfoLabel('Container.FolderName')
		self.kodi_user['current_window'] = xbmc.getInfoLabel('System.CurrentWindow')
		#Resolved Settings
		self.settings = dict()
		self.settings['tou'] = get_setting_as(setting_type='bool',setting=self.handle.getSetting(id='iagl_hidden_bool_tou'))
		self.settings['run_wizard'] = get_setting_as(setting_type='bool',setting=self.handle.getSetting(id='iagl_run_wizard'))
		self.settings['index_list'] = dict()
		self.settings['index_list']['route'] = get_setting_as(setting_type='index_list_route',setting=self.handle.getSetting(id='iagl_setting_archive_listings'))
		self.settings['game_list'] = dict()
		self.settings['game_list']['route'] = get_setting_as(setting_type='game_list_route',setting=self.handle.getSetting(id='iagl_setting_listing'))
		self.settings['game_list']['clean_titles'] = get_setting_as(setting_type='bool',setting=self.handle.getSetting(id='iagl_setting_clean_list'))
		self.settings['game_list']['naming_convention'] = get_setting_as(setting_type='game_naming_convention',setting=self.handle.getSetting(id='iagl_setting_naming'))
		self.settings['game_list']['date_format'] = get_setting_as(setting_type='display_date_format',setting=xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Settings.GetSettingValue","params":{"setting":"locale.shortdateformat"},"id":"1"}'))
		self.settings['game_list']['games_per_page'] = get_setting_as(setting_type='games_per_page',setting=self.handle.getSetting(id='iagl_setting_items_pp'))
		self.settings['game_list']['force_viewtypes'] = get_setting_as(setting_type='bool',setting=self.handle.getSetting(id='iagl_enable_forced_views'))
		self.settings['game_list']['include_all_art'] = get_setting_as(setting_type='bool',setting=self.handle.getSetting(id='iagl_setting_include_all_art'))
		self.settings['game_list']['boxart_or_snapshot'] = get_setting_as(setting_type='bool',setting=self.handle.getSetting(id='iagl_setting_poster_thumb'))
		self.settings['game_list']['enable_post_dl_edit'] = get_setting_as(setting_type='bool',setting=self.handle.getSetting(id='iagl_enable_post_dl_edit'))
		self.settings['game_list']['append_emu_name'] = get_setting_as(setting_type='bool',setting=self.handle.getSetting(id='iagl_append_emu_name_to_results'))
		self.settings['game_list']['game_history'] = get_setting_as(setting_type='int',setting=self.handle.getSetting(id='iagl_setting_history'))
		self.settings['game_list']['show_netplay'] = get_setting_as(setting_type='bool',setting=self.handle.getSetting(id='iagl_netplay_show_netplay_lobby'))
		self.settings['game_list']['filter_lobby'] = get_setting_as(setting_type='bool',setting=self.handle.getSetting(id='iagl_netplay_filter_lobby'))
		self.settings['game_list']['announce_netplay'] = get_setting_as(setting_type='bool',setting=self.handle.getSetting(id='iagl_netplay_announce_netplay'))
		self.settings['game_list']['filter_to_1g1r'] = get_setting_as(setting_type='bool',setting=self.handle.getSetting(id='iagl_setting_filter_to_1g1r'))
		self.settings['game_list']['forced_views'] = dict()
		self.settings['game_list']['forced_views']['Alphabetical'] = 'iagl_enable_forced_views_5'
		self.settings['game_list']['forced_views']['Group by Genres'] = 'iagl_enable_forced_views_6'
		self.settings['game_list']['forced_views']['Group by Years'] = 'iagl_enable_forced_views_7'
		self.settings['game_list']['forced_views']['Group by Players'] = 'iagl_enable_forced_views_8'
		self.settings['game_list']['forced_views']['Group by Studio'] = 'iagl_enable_forced_views_9'
		self.settings['game_list']['forced_views']['Group by Tag'] = 'iagl_enable_forced_views_10'
		self.settings['game_list']['forced_views']['Group by Custom Groups'] = 'iagl_enable_forced_views_11'
		self.settings['game_action'] = dict()
		self.settings['game_action']['select'] = get_setting_as(setting_type='int',setting=self.handle.getSetting(id='iagl_setting_default_action'))
		self.settings['game_action']['local_file_found'] = get_setting_as(setting_type='int',setting=self.handle.getSetting(id='iagl_setting_localfile_action'))
		self.settings['game_action']['autoplay_trailer'] = get_setting_as(setting_type='bool',setting=self.handle.getSetting(id='iagl_setting_autoplay_trailer'))
		self.settings['game_action']['show_netplay'] = get_setting_as(setting_type='bool',setting=self.handle.getSetting(id='iagl_netplay_enable_netplay_launch'))
		self.settings['game_action']['netplay_launch_action'] = get_setting_as(setting_type='int',setting=self.handle.getSetting(id='iagl_netplay_netplay_launch_choose'))
		self.settings['game_action']['use_relay'] = get_setting_as(setting_type='bool',setting=self.handle.getSetting(id='iagl_netplay_use_relay'))
		self.settings['game_action']['netplay_nick'] = self.handle.getSetting(id='iagl_netplay_nickname')
		self.settings['game_action']['netplay_port'] = self.handle.getSetting(id='iagl_netplay_port')
		self.settings['game_action']['netplay_default_host'] = self.handle.getSetting(id='iagl_default_manual_ip')
		self.settings['game_action']['netplay_checkframes'] = self.handle.getSetting(id='iagl_netplay_frames')
		self.settings['archive_org'] = dict()
		self.settings['archive_org']['enabled'] = get_setting_as(setting_type='bool',setting=self.handle.getSetting(id='iagl_setting_enable_login'))
		self.settings['archive_org']['username'] = self.handle.getSetting(id='iagl_setting_ia_username')
		self.settings['archive_org']['password'] = self.handle.getSetting(id='iagl_setting_ia_password')
		self.settings['download'] = dict()
		self.settings['download']['organize_cache'] = get_setting_as(setting_type='bool',setting=self.handle.getSetting(id='iagl_organize_temp_files'))
		self.settings['download']['max_threads'] = get_setting_as(setting_type='int',setting=self.handle.getSetting(id='iagl_max_download_threads'))
		self.settings['download']['copy_network_to_local'] = get_setting_as(setting_type='bool',setting=self.handle.getSetting(id='iagl_copy_network_to_local'))
		self.settings['ext_launchers'] = dict()
		self.settings['ext_launchers']['environment'] = get_setting_as(setting_type='ext_launch_env',setting=self.handle.getSetting(id='iagl_external_user_external_env'))
		self.settings['ext_launchers']['close_kodi'] = get_setting_as(setting_type='bool',setting=self.handle.getSetting(id='iagl_external_launch_close_kodi'))
		self.settings['ext_launchers']['pause_kodi'] = get_setting_as(setting_type='bool',setting=self.handle.getSetting(id='iagl_external_launch_pause_kodi'))
		self.settings['ext_launchers']['stop_audio_controller'] = get_setting_as(setting_type='bool',setting=self.handle.getSetting(id='iagl_suspend_audio_and_input'))
		self.settings['ext_launchers']['stop_media_before_launch'] = get_setting_as(setting_type='bool',setting=self.handle.getSetting(id='iagl_enable_stop_media_before_launch'))
		# self.settings['ext_launchers']['send_stop_command'] = get_setting_as(setting_type='bool',setting=self.handle.getSetting(id='iagl_enable_android_stop_command')) #No longer used
		self.settings['ext_launchers']['use_startactivity'] = get_setting_as(setting_type='bool',setting=self.handle.getSetting(id='iagl_enable_android_startactivity'))
		self.settings['ext_launchers']['wait_for_return'] = get_setting_as(setting_type='bool',setting=self.handle.getSetting(id='iagl_enable_wait_for_return'))
		self.settings['ext_launchers']['ra'] = dict()
		self.settings['ext_launchers']['ra']['name'] = 'RetroArch'
		self.settings['ext_launchers']['ra']['app_path'] = get_setting_as(setting_type='file_path',setting=self.handle.getSetting(id='iagl_external_path_to_retroarch'))
		self.settings['ext_launchers']['ra']['app_path_cmd_replace'] = '%APP_PATH_RA%'
		self.settings['ext_launchers']['ra']['cfg_path'] = get_setting_as(setting_type='file_path',setting=self.handle.getSetting(id='iagl_external_path_to_retroarch_cfg'))
		self.settings['ext_launchers']['other_ext_cmds'] = list()
		if self.settings.get('ext_launchers').get('ra').get('app_path'):
			self.settings['ext_launchers']['other_ext_cmds'].append({'name':'Retroarch Standalone','app_path':self.settings.get('ext_launchers').get('ra').get('app_path'),'app_path_cmd_replace':self.settings.get('ext_launchers').get('ra').get('app_path_cmd_replace')})
		for ii in range(1,4):
			current_type = get_setting_as(setting_type='emulator_type',setting=self.handle.getSetting(id='iagl_external_additional_emulator_%(ii)s_type'%{'ii':ii}))
			current_path = get_setting_as(setting_type='file_path',setting=self.handle.getSetting(id='iagl_external_additional_emulator_%(ii)s_path'%{'ii':ii}))
			if current_type and current_path:
				self.settings['ext_launchers']['other_ext_cmds'].append({'name':get_setting_as(setting_type='emulator_name',setting=self.handle.getSetting(id='iagl_external_additional_emulator_%(ii)s_type'%{'ii':ii})),'app_path':current_path,'app_path_cmd_replace':get_setting_as(setting_type='emulator_cmd_rep',setting=self.handle.getSetting(id='iagl_external_additional_emulator_%(ii)s_type'%{'ii':ii}))})
		self.settings['views'] = dict()
		self.settings['views']['content_type'] = get_setting_as(setting_type='set_content',setting=self.handle.getSetting(id='iagl_setting_setcontent'))
		self.settings['notifications'] = dict()
		self.settings['notifications']['background_notification_time'] = 2000
		self.settings['notifications']['background_error_notification_time'] = 5000
		#Cache size
		cache_options = [0,10*1e6,25*1e6,50*1e6,100*1e6,150*1e6,200*1e6,250*1e6,300*1e6,350*1e6,400*1e6,450*1e6,500*1e6,1000*1e6,2000*1e6,5000*1e6,10000*1e6,20000*1e6,32000*1e6,64000*1e6]
		cache_options_log = ['Zero (Current Game Only)','10 MB','25MB','50MB','100MB','150MB','200MB','250MB','300MB','350MB','400MB','450MB','500MB','1GB','2GB','5GB','10GB','20GB','32GB','64GB']
		try:
			self.cache_folder_size = cache_options[get_setting_as(setting_type='int',setting=self.handle.getSetting(id='iagl_setting_dl_cache'))]
			xbmc.log(msg='IAGL:  Cache Size set to - %(current_size)s - %(current_cache_log_option)s'%{'current_size': self.cache_folder_size, 'current_cache_log_option': cache_options_log[cache_options.index(self.cache_folder_size)]}, level=xbmc.LOGDEBUG)
		except ValueError:
			self.cache_folder_size = 0 #Default to 0 if not initialized correctly
			xbmc.log(msg='IAGL:  Cache Size set to is unknown - defaulting to zero', level=xbmc.LOGDEBUG)

		#Directories / Files
		self.directory = None
		if self.last_version and self.last_start_time and self.version == self.last_version and float(self.start_time)-float(self.last_start_time)<RESET_DIRECTORY_CACHE_TIME:
			self.directory = get_mem_cache('iagl_directory') #First attempt to load directory info from cache if the last time the addon was run is less than X hours and the version is the same, otherwise rescan the directories
		if self.directory is None:
			self.directory = self.get_directories() #If cache isn't available, then parse it from files
			if self.directory.get('userdata').get('game_cache').get('size') and self.directory.get('userdata').get('game_cache').get('size')>self.cache_folder_size:
				self.clear_game_cache_folder()
				self.directory = self.get_directories() #Reparse after clearing game list cache
		self.routes = self.addon_routes(self.directory)
		self.game_lists = self.game_lists(self.directory,self.settings,self.routes)
		# zachs_debug('Init Time was %(value)s'%{'value':time.time() - last_time})

	class addon_routes(object):
		def __init__(self,directories=None):
			self.file = dict()
			self.route = dict()
			if directories is not None:
				route_keys = [x.name.replace(x.suffix,'').replace('_database','') for x in directories.get('addon').get('databases').get('files')]
				self.file = dict(zip(route_keys,directories.get('addon').get('databases').get('files')))
				self.route = dict(zip(route_keys,[x.get('categories').get('category') if 'categories' in x.keys() else None for x in directories.get('addon').get('databases').get('dict')]))
			self.route_context_menu_items = dict()
			self.route_context_menu_items['add_to_favs'] = [(loc_str(30412),'RunPlugin(plugin://plugin.program.iagl/category_context_menu/action/<category_choice>/<game_list_id>/add_to_favs)')]
			self.query_context_menu_items = dict()
			self.query_context_menu_items['add_to_favs_search'] = [(loc_str(30412),'RunPlugin(plugin://plugin.program.iagl/query_context_menu/action/add_to_favs_search?query=<query>&list=<list>)')]
			self.query_context_menu_items['add_to_favs_random'] = [(loc_str(30412),'RunPlugin(plugin://plugin.program.iagl/query_context_menu/action/add_to_favs_random?query=<query>&list=<list>)')]

		def get_file(self,route_in):
			return self.file.get(route_in)

		def get_filename(self,route_in):
			return self.file.get(route_in).name

		def get_route(self,route_in,include_default=False):
			if include_default:
				return self.route.get(route_in)
			else:
				return [x for x in self.route.get(route_in) if x.get('label')!='default']

		def get_route_default(self,route_in):
			if 'default' in [x.get('label') for x in self.route.get(route_in)]:
				# return [x for x in self.route.get(route_in) if x.get('label')=='default'][0]
				return next(iter([x for x in self.route.get(route_in) if x.get('label')=='default']),dict())
			else:
				return dict()

		def get_route_as_listitems(self,route_in,game_list_name=None,game_list_id=None):
			default_dict = self.get_route_default(route_in)
			# return [self.add_game_listitem_context_menus(listitem_in=get_database_listitem(dict_in=map_database_listitem_dict(dict_in=x,default_dict=default_dict,game_list_name=game_list_name)),route_in=x,game_list_id=game_list_id) for x in self.get_route(route_in) if x is not None] #Remove IAGL favorites from here for now
			return [get_database_listitem(dict_in=map_database_listitem_dict(dict_in=x,default_dict=default_dict,game_list_name=game_list_name)) for x in self.get_route(route_in) if x is not None]


		def add_game_listitem_context_menus(self,listitem_in=None,route_in=None,game_list_id=None):
			if game_list_id:
				current_context_menus = [(labels,actions.replace('<game_list_id>',game_list_id).replace('<category_choice>',route_in.get('label'))) for labels, actions in self.route_context_menu_items.get('add_to_favs')]
				listitem_in.addContextMenuItems(current_context_menus)
			return listitem_in

		def add_query_listitem_context_menus(self,listitem_in=None,query_in=None,list_in=None,type_in='search'):
			if query_in and list_in:
				if list_in.get('art'):
					for kk in list_in['art']:
						list_in['art'][kk] = list_in['art'][kk].replace('https://i.imgur.com/','')
					for k,v in dict(zip(['thumb','banner','landscape','clearlogo','fanart'],['game_boxarts','game_banners','game_snapshots','game_logos','game_fanarts'])).items():
						list_in['properties'][v] = json.dumps([list_in.get('art').get(k)])
				current_context_menus = [(labels,actions.replace('<query>',url_quote_query(query_in)).replace('<list>',url_quote_query(list_in))) for labels, actions in self.query_context_menu_items.get('add_to_favs_%(type)s'%{'type':type_in})]
				listitem_in.addContextMenuItems(current_context_menus)
			return listitem_in

		def get_search_random_route_as_listitems(self,route_in):
			default_dict = self.get_route_default(route_in)
			current_query = get_mem_cache('iagl_current_query') #First attempt to load games from cache
			return [get_database_listitem(dict_in=map_search_random_listitem_dict(dict_in=x,default_dict=default_dict,search_query=current_query)) for x in self.get_route(route_in) if x is not None]

		def list_filenames(self):
			return [self.file.get(x).name for x in self.file.keys()]

		def list_routes(self):
			return list(self.route.keys())

	class game_lists(object):
		def __init__(self,directories=None,settings=None,choose_routes=None):
			self.file = dict()
			self.crc = dict()
			self.cache_name = dict()
			self.route = dict()
			#Default Values
			self.defaults = dict()
			self.settings = dict()
			self.defaults['thumb'] = MEDIA_SPECIAL_PATH%{'filename':'default_thumb.jpg'}
			self.defaults['banner'] = MEDIA_SPECIAL_PATH%{'filename':'default_banner.jpg'}
			self.defaults['icon'] = MEDIA_SPECIAL_PATH%{'filename':'icon.png'}
			self.defaults['fanart'] = MEDIA_SPECIAL_PATH%{'filename':'fanart.jpg'}
			self.game_list_context_menu_items = dict()
			self.game_list_context_menu_items['defaults'] = [(loc_str(30406),'RunPlugin(plugin://plugin.program.iagl/context_menu/action/<game_list_id>/view_list_settings)'),(loc_str(30404),'RunPlugin(plugin://plugin.program.iagl/context_menu/edit/<game_list_id>/emu_launcher)'),(loc_str(30405),'RunPlugin(plugin://plugin.program.iagl/context_menu/select/<game_list_id>/emu_downloadpath)'),(loc_str(30400),'RunPlugin(plugin://plugin.program.iagl/context_menu/select/<game_list_id>/metadata)'),(loc_str(30402),'RunPlugin(plugin://plugin.program.iagl/context_menu/select/<game_list_id>/art)'),(loc_str(30403),'RunPlugin(plugin://plugin.program.iagl/context_menu/edit/<game_list_id>/emu_visibility)'),(loc_str(30407),'RunPlugin(plugin://plugin.program.iagl/context_menu/action/<game_list_id>/refresh_list)')]
			self.game_list_context_menu_items['external'] = [(loc_str(30408),'RunPlugin(plugin://plugin.program.iagl/context_menu/select/<game_list_id>/emu_ext_launch_cmd)')]
			self.game_list_context_menu_items['retroplayer'] = [(loc_str(30409),'RunPlugin(plugin://plugin.program.iagl/context_menu/edit/<game_list_id>/emu_default_addon)')]
			self.game_list_context_menu_items['favorites'] = [(loc_str(30413),'RunPlugin(plugin://plugin.program.iagl/context_menu/action/<game_list_id>/delete_favorite)')] #,(loc_str(30411),'RunPlugin(plugin://plugin.program.iagl/context_menu/action/<game_list_id>/share_favorite)'). #Removed for now
			self.game_list_context_menu_items['post_dl'] = [(loc_str(30410),'RunPlugin(plugin://plugin.program.iagl/context_menu/edit/<game_list_id>/emu_postdlaction)')]

			self.game_context_menu_items = dict()
			self.game_context_menu_items['add_to_favs'] = [(loc_str(30412),'RunPlugin(plugin://plugin.program.iagl/game_context_menu/action/<game_list_id>/<game_id>/add_to_favs)')]
			self.game_context_menu_items['remove_from_favs'] = [(loc_str(30413),'RunPlugin(plugin://plugin.program.iagl/game_context_menu/action/<game_list_id>/<game_id>/remove_from_favs)')]

			if directories is not None:
				files_in = directories.get('userdata').get('dat_files')
				route_keys = [x.name.replace(x.suffix,'') for x in files_in.get('files')]
				self.file = dict(zip(route_keys,files_in.get('files')))
				self.crc = dict(zip(route_keys,files_in.get('crc')))
				self.cache_name = dict(zip(route_keys+['history'],files_in.get('cache_name')+['history']))
				self.list_cache_path = directories.get('userdata').get('list_cache').get('path')
				self.userdata_dat_files_path = files_in.get('path')
				self.route = dict(zip(route_keys+['history'],[x for x in files_in.get('header')]+[dict()]))
				self.favorites_template = next(iter([x for x in directories.get('addon').get('templates').get('files') if x.name == 'Favorites_Template.xml']),None)

			if settings is not None:
				self.settings = settings
			if choose_routes is not None:
				self.choose_routes = choose_routes

		def get_file(self,route_in):
			return self.file.get(route_in)

		def get_crc(self,route_in):
			return self.crc.get(route_in)

		def get_cache_name(self,route_in):
			return self.cache_name.get(route_in)

		def get_filename(self,route_in):
			return self.file.get(route_in).name

		def get_filename_no_suffix(self,route_in):
			return self.file.get(route_in).name.replace(self.file.get(route_in).suffix,'')

		def get_game_list(self,route_in):
			return self.route.get(route_in)

		def create_favorites_list(self,name_in=None,filename_in=None):
			file_out=None
			if self.favorites_template and name_in and filename_in:
				if write_text_to_file(self.favorites_template.read_text(encoding=TEXT_ENCODING).replace('<emu_name>Favorites</emu_name>','<emu_name>%(name)s</emu_name>'%{'name':name_in}),self.userdata_dat_files_path.joinpath('%(name)s.xml'%{'name':filename_in})):
					file_out=self.userdata_dat_files_path.joinpath('%(name)s.xml'%{'name':filename_in})
			return file_out

		def update_game_list_header(self,game_list_id,header_key=None,header_value=None,confirm_update=True,current_choice=None):
			success = False
			update_confirmed = False
			current_game_list = self.get_game_list(game_list_id)
			if isinstance(header_key,str) and isinstance(header_value,str) and header_key in current_game_list.keys():
				if current_choice is None:
					current_choice = header_key
				if confirm_update:
					current_dialog = xbmcgui.Dialog()
					ret1 = current_dialog.select(loc_str(30344)%{'current_choice':current_choice},[loc_str(30200),loc_str(30201)])
					del current_dialog
					if ret1 == 0:
						update_confirmed = True
				else:
					update_confirmed = True
				if update_confirmed:
					current_game_list[header_key] = header_value.replace('\r\n','\n').replace('\r','\n').replace('\n','[CR]') #Set new value
					success = update_xml_file(file_in=self.get_file(game_list_id),dict_in=current_game_list)
			else:
				xbmc.log(msg='IAGL:  The game list xml key is not well formed or wasnt found in the header: %(header_key)s, %(header_value)s'%{'header_key':header_key,'header_value':header_value},level=xbmc.LOGERROR)
			return success

		def get_game_choose_list(self,route_in):
			return self.choose_routes.route.get(route_in)

		def get_games(self,route_in):
			return get_xml_games(self.get_file(route_in))

		def get_all_game_lists(self):
			return [self.get_game_list(x) for x in self.list_game_lists()]

		def get_all_game_choose_lists(self):
			return [self.get_game_choose_list(x) for x in self.list_game_lists()]

		def get_game_lists_as_listitems(self,filter_in=None):
			return [self.add_game_listitem_context_menus(listitem_in=get_game_list_listitem(dict_in=map_game_list_listitem_dict(dict_in=x[0],default_dict=self.defaults,fn_in=x[1]),filter_in=filter_in),list_in=x[0],game_list_id=x[1]) for x in zip(self.get_all_game_lists(),self.list_game_lists()) if x is not None]

		def add_game_listitem_context_menus(self,listitem_in=None,list_in=None,game_list_id=None):
			if listitem_in and list_in and game_list_id:
				current_context_menus = [(labels,actions.replace('<game_list_id>',game_list_id)) for labels, actions in self.game_list_context_menu_items.get('defaults')]
				if self.game_list_context_menu_items.get(list_in.get('emu_launcher')):
					current_context_menus = current_context_menus+[(labels,actions.replace('<game_list_id>',game_list_id)) for labels, actions in self.game_list_context_menu_items.get(list_in.get('emu_launcher'))]
				if self.settings.get('game_list').get('enable_post_dl_edit'):
					current_context_menus = current_context_menus+[(labels,actions.replace('<game_list_id>',game_list_id)) for labels, actions in self.game_list_context_menu_items.get('post_dl')]
				if 'favorites' in list_in.get('emu_category').lower():
					current_context_menus = current_context_menus+[(labels,actions.replace('<game_list_id>',game_list_id)) for labels, actions in self.game_list_context_menu_items.get('favorites')]
				listitem_in.addContextMenuItems(current_context_menus)
			return listitem_in

		def add_game_context_menus(self,listitem_in=None,game_list_id=None,game_id=None,is_favorite=False):
			if listitem_in and game_list_id and game_id:
				if is_favorite:
					current_context_menus = [(labels,actions.replace('<game_list_id>',game_list_id).replace('<game_id>',game_id)) for labels, actions in self.game_context_menu_items.get('remove_from_favs')]
					listitem_in.addContextMenuItems(current_context_menus)
				else:
					current_context_menus = [(labels,actions.replace('<game_list_id>',game_list_id).replace('<game_id>',game_id)) for labels, actions in self.game_context_menu_items.get('add_to_favs')]
					listitem_in.addContextMenuItems(current_context_menus)
			return listitem_in

		def get_games_as_listitems(self,game_list_id=None,filter_in=None):
			#Possilbly add multiprocessing at this step
			return [self.add_game_context_menus(listitem_in=get_game_listitem(dict_in=x,filter_in=filter_in),game_list_id=game_list_id,game_id=x.get('values').get('label2'),is_favorite=(isinstance(x.get('properties').get('platform_category'),str) and 'favorites' in x.get('properties').get('platform_category').lower())) for x in self.get_games_from_cache(game_list_id=game_list_id) if x]

		def get_game_as_dict(self,game_list_id=None,game_id=None):
			if game_list_id == get_mem_cache('iagl_current_game_list_id') and game_id == get_mem_cache('iagl_current_game_id'):
				game = get_mem_cache('iagl_current_game')
			else:
				game = [x for x in self.get_games_from_cache(game_list_id=game_list_id) if x and game_id and x.get('values').get('label2')==game_id]
				set_mem_cache('iagl_current_game_id',game_id)
				set_mem_cache('iagl_current_game_list_id',game_list_id)
				set_mem_cache('iagl_current_game',game)
			if len(game)==1: #Should always be here
				xbmc.log(msg='IAGL:  Found game %(game_id)s in list %(game_list_id)s'%{'game_id':game_id,'game_list_id':game_list_id},level=xbmc.LOGDEBUG)
				# return game[0]
				return next(iter(game),None)
			elif len(game)>1:
				xbmc.log(msg='IAGL:  Found more than one game matching %(game_id)s in list %(game_list_id)s, returning first match'%{'game_id':game_id,'game_list_id':game_list_id},level=xbmc.LOGWARNING)
				# return game[0]
				return next(iter(game),None)
			else:
				xbmc.log(msg='IAGL:  Unable to find game matching %(game_id)s in list %(game_list_id)s, returning None'%{'game_id':game_id,'game_list_id':game_list_id},level=xbmc.LOGERROR)
				return None

		def get_game_choose_categories_as_listitems(self,game_list_id=None,category_choice=None,game_list_name=None):
			if category_choice:
				category_choice=category_choice.lower().replace('group by ','').replace(' ','_').replace('custom_','') #Map category to database route
			game_stats = self.get_game_stats(game_list_id=game_list_id)
			return [get_game_choose_list_listitem(dict_in=map_game_choose_list_listitem_dict(category_label=x[0],category_count=x[1],default_dict=self.defaults,categories_in=self.get_game_choose_list(category_choice),game_list_name=game_list_name)) for x in zip(game_stats.get(category_choice).get('all'),game_stats.get(category_choice).get('count')) if x is not None]

		def get_games_from_cache(self,game_list_id=None):
			games = None
			existing_cached_games_list = get_mem_cache('iagl_current_games_list') #First attempt to load games from cache
			if existing_cached_games_list and existing_cached_games_list==self.get_cache_name(game_list_id): #Check to verify result matches current crc for RAM cache
				games = get_mem_cache('iagl_current_games')
				# game_stats = get_mem_cache('iagl_current_games_stats')
			elif self.list_cache_path.joinpath(self.get_cache_name(game_list_id)+'.json').is_file():
				games,game_stats = get_disc_cache(os.path.join(self.list_cache_path,self.get_cache_name(game_list_id)+'.json'))
				self.update_cached_game_list(games=games,game_stats=game_stats,games_list=self.get_cache_name(game_list_id))
			else: #Parse from xml
				games = self.set_cached_game_list(games=[map_game_listitem_dict(dict_in=x,parent_dict_in=self.get_game_list(game_list_id),default_dict=self.defaults,game_list_id=game_list_id,clean_titles=self.settings.get('game_list').get('clean_titles'),naming_convention=self.settings.get('game_list').get('naming_convention'),date_convention=self.settings.get('game_list').get('date_format'),include_extra_art=self.settings.get('game_list').get('include_all_art'),boxart_or_snapshot=self.settings.get('game_list').get('boxart_or_snapshot')) for x in self.get_games(game_list_id) if x is not None],games_list=self.get_cache_name(game_list_id),type_in='games')
			return games

		def get_game_stats(self,game_list_id=None):
			game_stats = None
			existing_cached_games_list = get_mem_cache('iagl_current_games_stats_list') #First attempt to load dat from cache
			if existing_cached_games_list and existing_cached_games_list==self.get_cache_name(game_list_id): #Check to verify result matches current crc
				game_stats = get_mem_cache('iagl_current_games_stats')
			elif self.list_cache_path.joinpath(self.get_cache_name(game_list_id)+'_stats.json').is_file():
				game_stats = get_disc_cache(os.path.join(self.list_cache_path,self.get_cache_name(game_list_id)+'_stats.json'))
				self.update_cached_game_list(games=None,game_stats=game_stats,games_list=self.get_cache_name(game_list_id))
			else:
				game_stats = self.set_cached_game_list(games=[map_game_listitem_dict(dict_in=x,parent_dict_in=self.get_game_list(game_list_id),default_dict=self.defaults,game_list_id=game_list_id,clean_titles=self.settings.get('game_list').get('clean_titles'),naming_convention=self.settings.get('game_list').get('naming_convention'),date_convention=self.settings.get('game_list').get('date_format')) for x in self.get_games(game_list_id) if x is not None],games_list=self.get_cache_name(game_list_id),type_in='game_stats')
			return game_stats

		def update_cached_game_list(self,games,game_stats,games_list):
			if games and games_list:
				set_mem_cache('iagl_current_games_list',games_list)
				set_mem_cache('iagl_current_games',games)
			if game_stats and games_list:
				set_mem_cache('iagl_current_games_stats_list',games_list)
				set_mem_cache('iagl_current_games_stats',game_stats)

		def set_cached_game_list(self,games,games_list,type_in):
			if games and games_list:
				set_mem_cache('iagl_current_games_list',games_list)
				set_mem_cache('iagl_current_games',games)
				game_stats = get_game_list_stats(games)
				set_mem_cache('iagl_current_games_stats_list',games_list)
				set_mem_cache('iagl_current_games_stats',game_stats)
				set_disc_cache(os.path.join(self.list_cache_path,games_list+'.json'),games,game_stats)
				set_disc_cache(os.path.join(self.list_cache_path,games_list+'_stats.json'),None,game_stats)
				if type_in == 'games':
					return games
				elif type_in == 'game_stats':
					return game_stats
				else:
					return games, game_stats
			else:
				xbmc.log(msg='IAGL:  Games list %(value_in)s was empty, so cache was cleared'%{'value_in':games_list},level=xbmc.LOGDEBUG)
				clear_mem_cache('iagl_current_games_list')
				clear_mem_cache('iagl_current_games')
				clear_mem_cache('iagl_current_games_stats_list')
				clear_mem_cache('iagl_current_games_stats')
				return None
		
		def update_search_random_query(self,value_in):
			current_dialog = xbmcgui.Dialog()
			current_query = get_mem_cache('iagl_current_query') #First attempt to load games from cache
			if current_query is None:
				current_query = dict()
			if value_in == 'num_of_results':
				new_value = current_dialog.select(loc_str(30321),['1','2','5','10','25','100'],0,0)
				if new_value>-1:
					current_query['num_of_results'] = ['1','2','5','10','25','100'][new_value]
					# set_mem_cache('iagl_current_query',current_query)
			if value_in == 'title':
				new_value = current_dialog.input(loc_str(30320),current_query.get('title'))
				if new_value.strip():
					current_query['title'] = new_value
					# set_mem_cache('iagl_current_query',current_query)
			if value_in == 'lists':
				current_game_list_options = sorted([x for x in zip(self.list_game_lists(),[self.get_game_list(x).get('emu_name') for x in self.list_game_lists()]) if x[1]],key=lambda x:x[1])
				current_game_list_ids = ['All']+[x[0] for x in current_game_list_options]
				current_game_list_titles = ['All']+[x[1] for x in current_game_list_options]
				if current_query.get('lists'):
					current_selection = [ii for ii,x in enumerate(current_game_list_ids) if x in current_query.get('lists')]
				else:
					current_selection = []
				new_value = current_dialog.multiselect(loc_str(30360),current_game_list_titles,0,current_selection)
				if new_value:
					current_query['lists'] = [x for ii,x in enumerate(current_game_list_ids) if ii in new_value]
					current_query['game_count'] = sum([y.get('overall').get('count') for y in [self.get_game_stats(game_list_id=x) for ii,x in enumerate(current_game_list_ids) if x and ii in new_value] if y and y.get('overall') and isinstance(y.get('overall').get('count'),int)])
					# set_mem_cache('iagl_current_query',current_query)
			if value_in in ['genre','nplayers','year','studio','tag','groups']:
				value_map = {'genre':'genres','nplayers':'players','year':'years','studio':'studio','tag':'tag','groups':'groups'}
				perform_query = True
				if current_query.get('lists') is None or 'All' in current_query.get('lists'):
					if current_dialog.select(loc_str(30315),[loc_str(30200),loc_str(30201)]) != 0:
						perform_query = False
				if perform_query:
					if not current_query.get('lists'):
						value_set = get_game_stat_set(game_stats_in=[self.get_game_stats(game_list_id=x) for x in self.list_game_lists()],type_in=value_map.get(value_in))
					else:
						value_set = get_game_stat_set(game_stats_in=[self.get_game_stats(game_list_id=x) for x in current_query.get('lists')],type_in=value_map.get(value_in))
					if current_query.get(value_in):
						current_selection = [ii for ii,x in enumerate(value_set) if x in current_query.get(value_in)]
					else:
						current_selection = []
					if value_set:
						new_value = current_dialog.multiselect(loc_str(30393),value_set,0,current_selection)
					if new_value is not None:
						current_query[value_in] = [x for ii,x in enumerate(value_set) if ii in new_value]
			set_mem_cache('iagl_current_query',current_query)
			del current_dialog

		def list_filenames(self):
			return [self.file.get(x).name for x in self.file.keys()]

		def list_crcs(self):
			return [self.crc.get(x) for x in self.crc.keys()]

		def list_cache_names(self):
			return [self.cache_name.get(x) for x in self.cache_name.keys()]

		def list_game_lists(self):
			return list(self.route.keys())

		def list_game_choose_lists(self):
			return list(self.choose_routes.route.keys())

		def get_wizard_report_as_listitems(self):
			if get_mem_cache('iagl_wizard_results'):
				return map_wizard_report_listitem_dict(get_mem_cache('iagl_wizard_results'))
			else:
				return []

		def get_netplay_lobby_as_listitems(self,filter_lobby=True):
			discord_dict = get_discord_dict()
			return [get_database_listitem(dict_in=map_lobby_listitem_dict(libretro_dict=x,discord_dict=discord_dict,filter_lobby=filter_lobby)) for x in [y.get('fields') for y in get_libretro_dict()] if x]	

	def get_sort_methods(self,route_in):
		if route_in == 'Browse All Lists':
			return [xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,xbmcplugin.SORT_METHOD_DATE,xbmcplugin.SORT_METHOD_SIZE]
		if route_in == 'Browse by Category':
			return [xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE]
		if route_in == 'Choose from List':
			return [xbmcplugin.SORT_METHOD_NONE]
		if route_in == 'Games':
			return [xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE,xbmcplugin.SORT_METHOD_LABEL,xbmcplugin.SORT_METHOD_TITLE,xbmcplugin.SORT_METHOD_DATE,xbmcplugin.SORT_METHOD_GENRE,xbmcplugin.SORT_METHOD_STUDIO_IGNORE_THE,xbmcplugin.SORT_METHOD_SIZE]
		if route_in == 'History':
			return [xbmcplugin.SORT_METHOD_LASTPLAYED,xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE,xbmcplugin.SORT_METHOD_LABEL,xbmcplugin.SORT_METHOD_TITLE,xbmcplugin.SORT_METHOD_DATE,xbmcplugin.SORT_METHOD_GENRE,xbmcplugin.SORT_METHOD_STUDIO_IGNORE_THE,xbmcplugin.SORT_METHOD_SIZE]
		else:
			return [xbmcplugin.SORT_METHOD_LABEL]

	def query_user_for_updated_files(self,updates_list):
		query_out = list()
		for updates in updates_list:
			current_dialog = xbmcgui.Dialog()
			#file,name,new version,old version
			ok_ret = current_dialog.ok(loc_str(30322),loc_str(30323)%{'new_game_list_version':updates[2], 'dat_filename':updates[1]})
			ret1 = current_dialog.select(loc_str(30324)%{'dat_filename':updates[1]},[loc_str(30325),loc_str(30326),loc_str(30327)])
			del current_dialog
			if ret1==0: #Yes update
				query_out.append(updates[0])
			elif ret1 == 2: #No, delete forever
				delete_file(updates[0])
			else:
				xbmc.log(msg='IAGL:  File %(value_in)s will be queried on next addon start'%{'value_in':updates[1]},level=xbmc.LOGDEBUG)
		return query_out

	def add_new_dat_files(self,files_to_add,userdata_path):
		files_moved = False
		if isinstance(files_to_add,list) and len(files_to_add)>0:
			for ff in files_to_add:
				copy_settings = False
				if check_if_file_exists(userdata_path.joinpath(ff.name)):
					old_settings = get_xml_header(userdata_path.joinpath(ff.name),userdata_path)
					new_settings = get_xml_header(ff,userdata_path)
					if old_settings is not None:
						for kk in ['emu_visibility','emu_launcher','emu_default_addon','emu_ext_launch_cmd','emu_downloadpath']:
							if new_settings.get(kk) != old_settings.get(kk):
								copy_settings = True
								new_settings[kk] = old_settings.get(kk)
				if move_file(ff,userdata_path):
					files_moved = True
					if copy_settings: #Copy over settings from old file if necessary
						xbmc.log(msg='IAGL:  Copying old settings over to new data file %(value_in)s'%{'value_in':ff.name},level=xbmc.LOGDEBUG)
						settings_updated = update_xml_file(file_in=userdata_path.joinpath(ff.name),dict_in=new_settings)
			if files_moved:
				current_dialog = xbmcgui.Dialog()
				ok_ret = current_dialog.notification(loc_str(30328),loc_str(30329),xbmcgui.NOTIFICATION_INFO,self.settings.get('notifications').get('background_notification_time'))
				del current_dialog
		return files_moved

	def refresh_list(self,crc_in):
		success = False
		self.clear_all_mem_cache()
		success = all([delete_file_pathlib(x) for x in self.directory.get('userdata').get('list_cache').get('path').glob('*.json') if x.is_file() and crc_in in x.name])
		self.directory = self.get_directories()
		return success

	def clear_game_cache_folder(self):
		xbmc.log(msg='IAGL:  Purging game cache of size %(value_in)s'%{'value_in':self.directory.get('userdata').get('game_cache').get('size')}, level=xbmc.LOGDEBUG)
		if self.directory.get('userdata').get('game_cache').get('files'):
			all_files = [x for x in self.directory.get('userdata').get('game_cache').get('files')][::-1]
			xbmc.log(msg='IAGL: Game cache files to delete %(value_in)s'%{'value_in':all_files}, level=xbmc.LOGDEBUG)
		else:
			all_files = None
		if self.directory.get('userdata').get('game_cache').get('folders'):
			all_folders = [x for x in self.directory.get('userdata').get('game_cache').get('folders')][::-1]
			xbmc.log(msg='IAGL: Game cache folders to delete %(value_in)s'%{'value_in':all_folders}, level=xbmc.LOGDEBUG)
		else:
			all_folders = None
		if all_files:
			success1 = all([delete_file_pathlib(x) for x in all_files if x])
		else:
			success1 = True
		if all_folders:
			success2 = all([delete_folder_pathlib(x) for x in all_folders if x])
		else:
			success2 = True
		return all([success1,success2])

	def clear_list_cache_folder(self):
		xbmc.log(msg='IAGL:  Purging list cache folder', level=xbmc.LOGDEBUG)
		return all([delete_file_pathlib(x) for x in self.directory.get('userdata').get('list_cache').get('path').glob('*.json') if x.is_file()])

	def get_ext_launch_cmds(self):
		xbmc.log(msg='IAGL:  Querying current external launcher configurations', level=xbmc.LOGDEBUG)
		cmds_out = None
		if self.settings.get('ext_launchers').get('environment') and self.settings.get('ext_launchers').get('ra').get('app_path') and self.settings.get('ext_launchers').get('ra').get('cfg_path'):
			if self.settings.get('ext_launchers').get('close_kodi') and self.settings.get('ext_launchers').get('environment') in ['OSX','linux','windows']:
				if self.settings.get('ext_launchers').get('pause_kodi') and self.settings.get('ext_launchers').get('environment') in ['linux']:
					default_ra_cmd = [x for x in self.directory['addon']['external_command_database'].get('system').get('launcher') if x.get('@os') == self.settings.get('ext_launchers').get('environment') and x.get('@pause_kodi') and x.get('@default')]
					other_ext_cmds = [x for x in self.directory['addon']['external_command_database'].get('system').get('launcher') if x.get('@os') == self.settings.get('ext_launchers').get('environment') and x.get('@pause_kodi') and not x.get('@default')]
				else:
					default_ra_cmd = [x for x in self.directory['addon']['external_command_database'].get('system').get('launcher') if x.get('@os') == self.settings.get('ext_launchers').get('environment') and x.get('@close_kodi') and x.get('@default')]
					other_ext_cmds = [x for x in self.directory['addon']['external_command_database'].get('system').get('launcher') if x.get('@os') == self.settings.get('ext_launchers').get('environment') and x.get('@close_kodi') and not x.get('@default')]
			else:
				default_ra_cmd = [x for x in self.directory['addon']['external_command_database'].get('system').get('launcher') if x.get('@os') == self.settings.get('ext_launchers').get('environment') and not x.get('@close_kodi') and not x.get('@pause_kodi') and x.get('@default')]
				other_ext_cmds = [x for x in self.directory['addon']['external_command_database'].get('system').get('launcher') if x.get('@os') == self.settings.get('ext_launchers').get('environment') and not x.get('@close_kodi') and not x.get('@pause_kodi') and not x.get('@default')]
			ra_cmds = get_ra_cmds(default_ra_cmd,self.settings.get('ext_launchers').get('ra').get('cfg_path'),self.settings.get('ext_launchers').get('ra').get('app_path'))
			for cc in self.settings.get('ext_launchers').get('other_ext_cmds'):
				for oec in other_ext_cmds:
					oec['command'] = oec.get('command').replace(cc.get('app_path_cmd_replace'),str(cc.get('app_path')))
			cmds_out = [x for x in ra_cmds if '%APP_PATH' not in x.get('command')]+[x for x in other_ext_cmds if '%APP_PATH' not in x.get('command')]  #Remove any commands that dont have a path defined
		elif self.settings.get('ext_launchers').get('environment') and self.settings.get('ext_launchers').get('ra').get('cfg_path') and self.settings.get('ext_launchers').get('environment') in ['android','android_ra32','android_aarch64']:
			ra_config = get_ra_libretro_config(self.settings.get('ext_launchers').get('ra').get('cfg_path'),None)
			android_cmds = [x for x in self.directory['addon']['external_command_database'].get('system').get('launcher') if x.get('@os') == self.settings.get('ext_launchers').get('environment')]
			if ra_config.get('libretro_directory'):
				for ac in android_cmds:
					if isinstance(ac.get('command'),str):
						ac['command'] = ac.get('command').replace('%CFG_PATH%',str(self.settings.get('ext_launchers').get('ra').get('cfg_path')))
						ac['command'] = ac.get('command').replace('%CORE_BASE_PATH%',str(ra_config.get('libretro_directory')))
					if isinstance(ac.get('activity'),str):
						ac['activity'] = ac.get('activity').replace('%CFG_PATH%',str(self.settings.get('ext_launchers').get('ra').get('cfg_path')))
						ac['activity'] = ac.get('activity').replace('%CORE_BASE_PATH%',str(ra_config.get('libretro_directory')))
				cmds_out = [x for x in android_cmds if (isinstance(x.get('command'),str) and '%CORE_BASE_PATH%' not in x.get('command')) or (isinstance(x.get('activity'),str) and '%CORE_BASE_PATH%' not in x.get('activity'))]
			else:
				current_dialog = xbmcgui.Dialog()
				ok_ret = current_dialog.ok(loc_str(30203),loc_str(30375))
				del current_dialog
		elif self.settings.get('ext_launchers').get('environment') and not (self.settings.get('ext_launchers').get('ra').get('app_path') or self.settings.get('ext_launchers').get('ra').get('cfg_path')) and len(self.settings.get('ext_launchers').get('other_ext_cmds')) > 0:
			if self.settings.get('ext_launchers').get('close_kodi') and self.settings.get('ext_launchers').get('environment') in ['OSX','linux','windows']:
				if self.settings.get('ext_launchers').get('pause_kodi') and self.settings.get('ext_launchers').get('environment') in ['linux']:
					other_ext_cmds = [x for x in self.directory['addon']['external_command_database'].get('system').get('launcher') if x.get('@os') == self.settings.get('ext_launchers').get('environment') and x.get('@pause_kodi') and not x.get('@default')]
				else:
					other_ext_cmds = [x for x in self.directory['addon']['external_command_database'].get('system').get('launcher') if x.get('@os') == self.settings.get('ext_launchers').get('environment') and x.get('@close_kodi') and not x.get('@default')]
			else:
				other_ext_cmds = [x for x in self.directory['addon']['external_command_database'].get('system').get('launcher') if x.get('@os') == self.settings.get('ext_launchers').get('environment') and not x.get('@close_kodi') and not x.get('@pause_kodi') and not x.get('@default')]
			for cc in self.settings.get('ext_launchers').get('other_ext_cmds'):
				for oec in other_ext_cmds:
					oec['command'] = oec.get('command').replace(cc.get('app_path_cmd_replace'),str(cc.get('app_path')))
			cmds_out = [x for x in other_ext_cmds if '%APP_PATH' not in x.get('command')]  #Remove any commands that dont have a path defined
		#Add another option here - RA not defined but other emulators are defined
		else:
			current_dialog = xbmcgui.Dialog()
			ok_ret = current_dialog.ok(loc_str(30203),loc_str(30375))
			del current_dialog
		return cmds_out

	def get_directories(self):
		dict_out = dict()
		dict_out['addon'] = dict()
		dict_out['addon']['path'] = xbmcvfs.translatePath(self.handle.getAddonInfo('path'))
		dict_out['userdata'] = dict()
		dict_out['userdata']['path'] = xbmcvfs.translatePath(self.handle.getAddonInfo('profile'))
		dict_out['userdata']['game_cache'] = dict()
		dict_out['userdata']['game_cache']['path'] = check_userdata_directory(os.path.join(dict_out['userdata']['path'],'game_cache'))
		dict_out['userdata']['game_cache']['files'] = [x for x in dict_out['userdata']['game_cache']['path'].glob('**/*') if x.is_file()]
		dict_out['userdata']['game_cache']['folders'] = [x for x in dict_out['userdata']['game_cache']['path'].glob('**/*') if x.is_dir()]
		dict_out['userdata']['game_cache']['size'] = sum([x.stat().st_size for x in dict_out['userdata']['game_cache']['files']])
		dict_out['addon']['dat_files'] = dict()
		dict_out['addon']['dat_files']['path'] = Path(xbmcvfs.translatePath(os.path.join(dict_out['addon']['path'],'resources','data','dat_files')))
		dict_out['addon']['dat_files']['files'] = [x for x in dict_out['addon']['dat_files']['path'].glob('*.xml') if x.is_file()]
		dict_out['addon']['dat_files']['crc'] = [get_crc32(x) for x in dict_out['addon']['dat_files']['files']]
		dict_out['addon']['dat_files']['header'] = [get_xml_header(x,default_dir=dict_out['userdata']['game_cache']['path']) for x in dict_out['addon']['dat_files']['files']]
		dict_out['addon']['databases'] = dict()
		dict_out['addon']['databases']['path'] = Path(xbmcvfs.translatePath(os.path.join(dict_out['addon']['path'],'resources','data','databases')))
		dict_out['addon']['databases']['files'] = [x for x in dict_out['addon']['databases']['path'].glob('*.xml') if x.is_file()]
		dict_out['addon']['databases']['crc'] = [get_crc32(x) for x in dict_out['addon']['databases']['files']]
		dict_out['addon']['databases']['dict'] = [read_xml_file_et(str(x)) for x in dict_out['addon']['databases']['files']]
		dict_out['addon']['templates'] = dict()
		dict_out['addon']['templates']['path'] = Path(xbmcvfs.translatePath(os.path.join(dict_out['addon']['path'],'resources','data','templates')))
		dict_out['addon']['templates']['files'] = [x for x in dict_out['addon']['templates']['path'].iterdir() if x.is_file()]
		dict_out['addon']['templates']['crc'] = [get_crc32(x) for x in dict_out['addon']['templates']['files']]
		dict_out['addon']['external_command_database'] = read_xml_file_et(os.path.join(dict_out['addon']['path'],'resources','data','external_command_database.xml'))
		dict_out['addon']['external_command_database']['path'] = os.path.join(dict_out['addon']['path'],'resources','data','external_command_database.xml')
		dict_out['userdata']['list_cache'] = dict()
		dict_out['userdata']['list_cache']['path'] = check_userdata_directory(os.path.join(dict_out['userdata']['path'],'list_cache'))
		dict_out['userdata']['list_cache']['files'] = [x for x in dict_out['userdata']['list_cache']['path'].glob('*.json') if x.is_file()]
		dict_out['userdata']['dat_files'] = dict()
		dict_out['userdata']['dat_files']['path'] = check_userdata_directory(os.path.join(dict_out['userdata']['path'],'dat_files'))
		dict_out['userdata']['dat_files']['files'] = [x for x in dict_out['userdata']['dat_files']['path'].glob('*.xml') if x.is_file()]
		dict_out['userdata']['dat_files']['crc'] = [get_crc32(x) for x in dict_out['userdata']['dat_files']['files']]
		dict_out['userdata']['dat_files']['header'] = [get_xml_header(x,default_dir=dict_out['userdata']['game_cache']['path']) for x in dict_out['userdata']['dat_files']['files']]
		dict_out['userdata']['dat_files']['cache_name'] = ['%(fn)s_%(crc)s'%{'fn':x[0].name.replace(x[0].suffix,''),'crc':x[1]} for x in zip(dict_out['userdata']['dat_files']['files'],dict_out['userdata']['dat_files']['crc'])]
		dict_out['addon']['dat_files']['to_add'] = [x for x in dict_out['addon']['dat_files']['files'] if x.name not in [y.name for y in dict_out['userdata']['dat_files']['files']]] #These files are not yet in userdata and need to be moved
		dict_out['addon']['dat_files']['to_add_from_query'] = self.query_user_for_updated_files(check_addondata_to_query(dict_out['addon']['dat_files'],dict_out['userdata']['dat_files']))
		if self.add_new_dat_files(dict_out['addon']['dat_files']['to_add']+dict_out['addon']['dat_files']['to_add_from_query'],dict_out['userdata']['dat_files']['path']): #Recalc userdata after files were moved
			self.clear_all_mem_cache()
			dict_out['userdata']['dat_files']['path'] = check_userdata_directory(os.path.join(dict_out['userdata']['path'],'dat_files'))
			dict_out['userdata']['dat_files']['files'] = [x for x in dict_out['userdata']['dat_files']['path'].glob('*.xml') if x.is_file()]
			dict_out['userdata']['dat_files']['crc'] = [get_crc32(x) for x in dict_out['userdata']['dat_files']['files']]
			dict_out['userdata']['dat_files']['header'] = [get_xml_header(x,default_dir=dict_out['userdata']['game_cache']['path']) for x in dict_out['userdata']['dat_files']['files']]
			dict_out['userdata']['dat_files']['cache_name'] = ['%(fn)s_%(crc)s'%{'fn':x[0].name.replace(x[0].suffix,''),'crc':x[1]} for x in zip(dict_out['userdata']['dat_files']['files'],dict_out['userdata']['dat_files']['crc'])]
			dict_out['userdata']['game_cache']['path'] = check_userdata_directory(os.path.join(dict_out['userdata']['path'],'game_cache'))
			dict_out['userdata']['game_cache']['files'] = [x for x in dict_out['userdata']['game_cache']['path'].glob('**/*') if x.is_file()]
			dict_out['userdata']['game_cache']['folders'] = [x for x in dict_out['userdata']['game_cache']['path'].glob('**/*') if x.is_dir()]
			dict_out['userdata']['game_cache']['size'] = sum([x.stat().st_size for x in dict_out['userdata']['game_cache']['files']])
		cache_files_to_delete = [delete_file_pathlib(x) for x in dict_out['userdata']['list_cache']['files'] if (x.name.replace(x.suffix,'').replace('_stats','').split('_')[-1] not in dict_out['userdata']['dat_files']['crc'] and x.name not in ['history.json','history_stats.json'])] #Delete old cache files if the crc does not match
		dict_out['userdata']['settings'] = dict()
		dict_out['userdata']['settings']['path'] = os.path.join(dict_out['userdata']['path'],'settings.xml')
		set_mem_cache('iagl_directory',dict_out)
		return dict_out

	def clear_all_mem_cache(self):
		xbmc.log(msg='IAGL:  Clearing all Memory Cache values', level=xbmc.LOGDEBUG)
		return all([clear_mem_cache(x) for x in ['iagl_current_games_list','iagl_current_games_stats_list','iagl_current_games','iagl_current_games_stats','iagl_current_game_id','iagl_current_game_list_id','iagl_current_game','iagl_directory','TextViewer_Header','TextViewer_Text','iagl_archive_org_login','iagl_wizard_results']])

#TOU Dialog, only shown on first run and prior to agreeing to TOU
class iagl_dialog_TOU(xbmcgui.WindowXMLDialog):
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
			xbmcaddon.Addon(id=ADDON_NAME).setSetting(id='iagl_hidden_bool_tou',value='true')
			xbmc.log(msg='IAGL:  Terms of Use Agree', level=xbmc.LOGDEBUG)
			self.closeDialog()
		#Do not Agree
		elif controlId == self.control_id_button_exit:
			xbmc.log(msg='IAGL:  Terms of Use do not Agree', level=xbmc.LOGDEBUG)
			self.closeDialog()
	def closeDialog(self):
		self.close()

#Text Viewer Dialog class, for expanded view of a game plot
class iagl_dialog_text_viewer(xbmcgui.WindowXMLDialog):
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
		clear_mem_cache('TextViewer_Header')
		clear_mem_cache('TextViewer_Text')
		self.close()

class IAGLPlayer(xbmc.Player):
	def onPlayBackEnded(self):
		set_mem_cache('iagl_trailer_started','False')

#InfoDialog class
class iagl_dialog_info_page(xbmcgui.WindowXMLDialog):
	def __init__(self, *args, **kwargs):
		self.game_id = kwargs.get('game_id')
		self.game_list_id = kwargs.get('game_list_id')
		self.game = kwargs.get('game')
		self.game_listitem = kwargs.get('game_listitem')
		self.autoplay_trailer = kwargs.get('autoplay_trailer')
		self.show_netplay = kwargs.get('show_netplay')
		self.netplay_launch_action = kwargs.get('netplay_launch_action')
		self.art = dict()
		for kk in ['game_boxarts','game_banners','game_snapshots','game_logos','game_fanarts']:
			if self.game.get('properties') and self.game.get('properties').get(kk):
				self.art[kk] = json.loads(self.game.get('properties').get(kk))
		self.action_requested = None
		self.netplay_options = None
		self.dialog_player = IAGLPlayer()

		self.onaction_id_exit = [10, 13, 92] #Default exit keys to close window via keyboard / controller
		self.onclick_id_download = 3001
		self.onclick_id_launch = 3002
		self.onclick_id_netplay = 3004
		self.onclick_id_exit = 3003
		self.listitem_id = dict()
		self.listitem_id['game'] = 113 #Invisible listitem for game metadata
		self.listitem_id['game_fanarts'] = 114 #Invisible listitem for game fanart
		self.listitem_id['game_boxarts'] = 115 #Invisible listitem for game boxarts, same as snapshots
		self.listitem_id['game_snapshots'] = 115 #Invisible listitem for game snapshots, same as boxarts
		self.listitem_id['game_banners'] = 116 #Invisible listitem for game banners
		self.listitem_id['game_logos'] = None #Invisible listitem for game logos
		xbmc.log(msg='IAGL:  Info Page Initialized for game %(game_id)s in list %(game_list_id)s'%{'game_id':self.game_id,'game_list_id':self.game_list_id}, level=xbmc.LOGDEBUG)

	def onInit(self):
		self.download_button = self.getControl(self.onclick_id_download)
		self.download_button.setEnabled(True)
		self.launch_button = self.getControl(self.onclick_id_launch)
		self.launch_button.setEnabled(True)
		self.netplay_button = self.getControl(self.onclick_id_netplay)
		if self.show_netplay:
			self.netplay_button.setEnabled(True)
			self.netplay_button.setVisible(True)
		else:
			self.netplay_button.setEnabled(False)
			self.netplay_button.setVisible(False)
		self.exit_button = self.getControl(self.onclick_id_exit)
		self.exit_button.setEnabled(True)
		self.current_game_listitem = self.getControl(self.listitem_id.get('game'))
		self.current_game_listitem.addItem(self.game_listitem)

		for kk in zip(['game_boxarts','game_banners','game_snapshots','game_logos','game_fanarts'],['poster','banner','poster','clearlogo','fanart']):
			if self.art.get(kk[0]) and self.listitem_id.get(kk[0]):
				current_listitems = list()
				current_control = self.getControl(self.listitem_id.get(kk[0]))
				for aa in self.art.get(kk[0]):
					li = xbmcgui.ListItem(label=self.game_list_id,offscreen=True)
					li.setArt({kk[1]:choose_image(aa)})
					current_listitems.append(li)
				current_control.addItems(current_listitems)

		if self.autoplay_trailer and self.game.get('info').get('trailer'):
			if self.dialog_player.isPlaying():
				self.dialog_player.stop()
				xbmc.sleep(100)
			set_mem_cache('iagl_trailer_started','True')
			xbmc.executebuiltin('Dialog.Close(busydialog,true)')
			xbmc.sleep(100)
			self.dialog_player.play(self.game.get('info').get('trailer'),windowed=True)
		else:
			set_mem_cache('iagl_trailer_started','False')

	def onAction(self, action):
		if action in self.onaction_id_exit:
			self.closeDialog()

	def onClick(self, controlId):
		if controlId == self.onclick_id_exit:
			self.closeDialog()
		if controlId == self.onclick_id_launch:
			self.action_requested = 0
			self.closeDialog()
		if controlId == self.onclick_id_download:
			self.action_requested = 1
			self.closeDialog()
		if controlId == self.onclick_id_netplay:
			if self.netplay_launch_action == 0:
				choose_dialog = xbmcgui.Dialog()
				ret1 = choose_dialog.select(loc_str(30607),[loc_str(30608),loc_str(30609)]) #,loc_str(30610)
				if ret1 in [0,1,2]:
					self.action_requested = 2+ret1
					self.closeDialog()
				del choose_dialog
			else:
				self.action_requested = 1+self.netplay_launch_action
				self.closeDialog()

	def closeDialog(self):
		xbmc.executebuiltin('Dialog.Close(busydialog,true)') #Try and close busy dialog if it is for some reason open
		if self.autoplay_trailer and self.game.get('info').get('trailer'):
			if self.dialog_player.isPlaying():
				self.dialog_player.stop()
				xbmc.sleep(100)
			set_mem_cache('iagl_trailer_started','False')
		self.close()

class iagl_dialog_netplay_settings_page(xbmcgui.WindowXMLDialog):
	def __init__(self, *args, **kwargs):
		self.netplay_inputs = kwargs.get('netplay_inputs')
		self.default_host = kwargs.get('default_host')
		self.default_port = kwargs.get('default_port')
		self.manual_netplay_parameters = get_mem_cache('iagl_netplay_parameters')
		self.onaction_id_exit = [10, 13, 92] #Default exit keys to close window via keyboard / controller
		self.onclick_id_netplay = 3007
		self.onclick_id_exit = 3008
		self.value_id = dict()
		self.value_id['host'] = 3003
		self.value_id['port'] = 3004
		self.value_id['password'] = 3005
		self.value_id['spectate'] = 3006
		self.values_out = None
		xbmc.log(msg='IAGL:  Netplay manual settings page Initialized', level=xbmc.LOGDEBUG)

	def onInit(self):
		self.dialog_values = dict()
		self.dialog_values['host'] = self.getControl(self.value_id['host'])
		self.dialog_values['port'] = self.getControl(self.value_id['port'])
		self.dialog_values['password'] = self.getControl(self.value_id['password'])
		self.dialog_buttons = dict()
		self.dialog_buttons['spectate'] = self.getControl(self.value_id['spectate'])
		if self.manual_netplay_parameters:
			current_host = next(iter([x for x in [self.manual_netplay_parameters.get('mitm_ip'),self.manual_netplay_parameters.get('ip'),self.default_host] if x and len(str(x))>1 and x!='0']),None)
			current_port = next(iter([x for x in [self.manual_netplay_parameters.get('mitm_port'),self.manual_netplay_parameters.get('port'),self.default_port] if x and len(str(x))>1 and x!='0']),'55435')
		else:
			current_host = next(iter([x for x in [self.default_host] if x and len(str(x))>1 and x!='0']),None)
			current_port = next(iter([x for x in [self.default_port] if x and len(str(x))>1 and x!='0']),'55435')
		if current_host:
			self.dialog_values.get('host').setText(str(current_host))
		if current_port:
			self.dialog_values.get('port').setText(str(current_port))

	def onAction(self, action):
		if action in self.onaction_id_exit:
			self.closeDialog()

	def onClick(self, controlId):
		if controlId == self.onclick_id_exit:
			self.closeDialog()
		if controlId == self.onclick_id_netplay:
			netplay_settings = dict()
			for kk in self.dialog_values.keys():
				value = self.dialog_values.get(kk).getText()
				netplay_settings[kk] = value
			for kk in self.dialog_buttons.keys():
				value = self.dialog_buttons.get(kk).isSelected()
				netplay_settings[kk] = value
			if not netplay_settings.get('host') or len(netplay_settings.get('host'))<1:
				current_dialog = xbmcgui.Dialog()
				ok_ret = current_dialog.ok(loc_str(30203),loc_str(30445))
			else:
				if not netplay_settings.get('port') or len(netplay_settings.get('port'))<1:
					netplay_settings[kk] = self.default_port
				if not netplay_settings.get('password') or len(netplay_settings.get('password'))<1:
					netplay_settings[kk] = None
				self.values_out = netplay_settings
				self.closeDialog()

	def closeDialog(self):
		xbmc.executebuiltin('Dialog.Close(busydialog)')
		self.close()
