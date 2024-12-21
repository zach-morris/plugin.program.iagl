import xbmc,xbmcgui,xbmcaddon,xbmcvfs,json,os
from pathlib import Path
from urllib.parse import urlencode
import archive_tool

class common(object):
	def __init__(self,config=None):
		self.config=config
		self.files = self.files(config=config)

	def get_loc(self,value_in=None):
		return self.config.addon.get('addon_handle').getLocalizedString(value_in)

	def get_path_as_xbmc_str(self,path_in=None):
		cpath = None
		if isinstance(path_in,Path):
			cpath = str(path_in)
			if not cpath.endswith(os.sep):
				cpath = cpath+os.sep
		if isinstance(path_in,str) and len(path_in)>0:
			cpath = path_in
			if not cpath.endswith(os.sep):
				cpath = cpath+os.sep
		return cpath

	def xbmc_dir_exists(self,path_in=None):
		if isinstance(self.get_path_as_xbmc_str(path_in),str):
			return xbmcvfs.exists(self.get_path_as_xbmc_str(path_in))
		else:
			return False

	def xbmc_dir_size(self,path_in=None):
		if self.xbmc_dir_exists(path_in=path_in):
			return xbmcvfs.Stat(self.get_path_as_xbmc_str(path_in)).st_size()
		else:
			return None

	def xbmc_get_files(self,path_in=None):
		if self.xbmc_dir_exists(path_in=path_in):
			_,files = xbmcvfs.listdir(self.get_path_as_xbmc_str(path_in))
			return files
		else:
			return None

	def xbmc_mk_dir(self,path_in=None):
		if isinstance(self.get_path_as_xbmc_str(path_in),str):
			return xbmcvfs.mkdir(self.get_path_as_xbmc_str(path_in))
		else:
			return False

	def xbmc_del_dir(self,path_in=None,force=True):
		if self.xbmc_dir_exists(path_in=path_in):
			return xbmcvfs.rmdir(self.get_path_as_xbmc_str(path_in),force=force)
		else:
			return False

	def get_setting(self,setting_in=None):
		result = None
		if setting_in in self.config.settings.keys():
			cv = self.config.addon.get('addon_handle').getSetting(id=setting_in)
			if cv in self.config.settings.get(setting_in).get('options').keys():
				result = self.config.settings.get(setting_in).get('options').get(cv)
			else:
				result = self.config.settings.get(setting_in).get('default')
		elif setting_in == 'append_game_list_to_search_results_combined':
			result1 = self.config.settings.get('game_title_setting').get('options').get(self.config.addon.get('addon_handle').getSetting(id='game_title_setting')) or self.config.settings.get('game_title_setting').get('default')
			result2 = self.config.settings.get('append_game_list_to_search_results').get('options').get(self.config.addon.get('addon_handle').getSetting(id='append_game_list_to_search_results')) or self.config.settings.get('append_game_list_to_search_results').get('default')
			result = result1+result2
		elif setting_in == 'append_game_list_to_playlist_results_combined':
			result1 = self.config.settings.get('game_title_setting').get('options').get(self.config.addon.get('addon_handle').getSetting(id='game_title_setting')) or self.config.settings.get('game_title_setting').get('default')
			result2 = self.config.settings.get('append_game_list_to_playlist_results').get('options').get(self.config.addon.get('addon_handle').getSetting(id='append_game_list_to_playlist_results')) or self.config.settings.get('append_game_list_to_playlist_results').get('default')
			result = result1+result2		
		elif setting_in == 'default_dl_path': #Download paths are strings for xbmcvfs
			if isinstance(self.config.paths.get('default_temp_dl_size'),int) and self.config.paths.get('default_temp_dl_size')>self.get_setting('game_cache_size'):
				xbmc.log(msg='IAGL: game_cache directory size is {} bytes ({} total files), limit is {} bytes.  Purging folder.'.format(self.config.paths.get('default_temp_dl_size'),len(self.config.files.get('default_temp_dl_file_listing')),self.get_setting('game_cache_size')),level=xbmc.LOGDEBUG)
				if self.xbmc_del_dir(self.config.paths.get('default_temp_dl')):
					xbmc.log(msg='IAGL: game_cache directory purged',level=xbmc.LOGDEBUG)
			if self.get_setting('alt_temp_dl_enable')==True and self.xbmc_dir_exists(self.config.addon.get('addon_handle').getSetting(id='alt_temp_dl')):
				result = self.get_path_as_xbmc_str(self.config.addon.get('addon_handle').getSetting(id='alt_temp_dl'))
			else:
				if not self.xbmc_dir_exists(self.config.paths.get('default_temp_dl')):
					if self.xbmc_mk_dir(self.config.paths.get('default_temp_dl')):
						result = self.get_path_as_xbmc_str(self.config.paths.get('default_temp_dl'))
						xbmc.log(msg='IAGL: game_cache directory (re)created',level=xbmc.LOGDEBUG)
					else:
						xbmc.log(msg='IAGL: unable to create game_cache directory',level=xbmc.LOGERROR)
				else:
					result = self.get_path_as_xbmc_str(self.config.paths.get('default_temp_dl'))
		elif setting_in == 'media_type':
			result1 = self.config.settings.get('media_type_game').get('options').get(self.config.addon.get('addon_handle').getSetting(id='media_type_game')) or self.config.settings.get('media_type_game').get('default')
			result = self.config.settings.get('media_type_game').get('listitem_type').get(result1) or self.config.media.get('default_type')
		elif setting_in in self.config.settings.get('page_viewtype_options').get('viewtype_settings'):
			result1 = self.config.settings.get('force_viewtypes').get('options').get(self.config.addon.get('addon_handle').getSetting(id='force_viewtypes')) or self.config.settings.get('force_viewtypes').get('default')
			if result1:
				result = self.config.settings.get('page_viewtype_options').get('options').get(self.config.addon.get('addon_handle').getSetting(id=setting_in)) or self.config.settings.get('page_viewtype_options').get('default')
		else:
			result = self.config.addon.get('addon_handle').getSetting(id=setting_in)
		return result

	def update_home_property(self,type_in=None,**kwargs):
		result = False
		dict_updated = False
		if isinstance(xbmcgui.Window(self.config.defaults.get('home_id')).getProperty(type_in),str) and len(xbmcgui.Window(self.config.defaults.get('home_id')).getProperty(type_in))>0:
			current_property_dict = json.loads(xbmcgui.Window(self.config.defaults.get('home_id')).getProperty(type_in))
		else:
			current_property_dict = dict()
		if isinstance(kwargs,dict):
			for k,v in kwargs.items():
				dict_updated = True
				current_property_dict[k] = v
		if dict_updated:
			xbmcgui.Window(self.config.defaults.get('home_id')).setProperty(type_in,json.dumps(current_property_dict))
			xbmc.log(msg='IAGL:  {} updated to: {}'.format(type_in,current_property_dict),level=xbmc.LOGDEBUG)
			result = True
		return result

	def clear_home_property(self,type_in=None,**kwargs):
		result = False
		if isinstance(xbmcgui.Window(self.config.defaults.get('home_id')).getProperty(type_in),str) and len(xbmcgui.Window(self.config.defaults.get('home_id')).getProperty(type_in))>0:
			xbmcgui.Window(self.config.defaults.get('home_id')).clearProperty(type_in)
			result = True
		return result

	def get_home_property(self,type_in=None):
		if isinstance(xbmcgui.Window(self.config.defaults.get('home_id')).getProperty(type_in),str) and len(xbmcgui.Window(self.config.defaults.get('home_id')).getProperty(type_in))>0:
			current_property_dict = json.loads(xbmcgui.Window(self.config.defaults.get('home_id')).getProperty(type_in))
		else:
			current_property_dict = None
		return current_property_dict

	# def get_crc32(self,filename_in=None,chunk_size=10485760):
	# 	csum = None
	# 	if isinstance(filename_in,Path) and filename_in.exists():
	# 		with filename_in.open(mode='rb') as f:
	# 			for chunk in iter((lambda:f.read(chunk_size)),None):
	# 				if chunk:
	# 					if csum:
	# 						csum = zlib_crc32(chunk,csum)
	# 					else:
	# 						csum = zlib_crc32(chunk)
	# 				else:
	# 					break
	# 	if csum:
	# 		return format(csum & 0xFFFFFFFF,'X')
	# 	else:
	# 		return None

	def get_game_dl_path(self,path_in=None,game_list_id=None,organize_path=True):
		result = path_in
		if isinstance(path_in,str) and isinstance(game_list_id,str) and organize_path:
			
			if self.xbmc_dir_exists(str(Path(path_in).joinpath(xbmcvfs.makeLegalFilename(game_list_id)))):
				result = self.get_path_as_xbmc_str(str(Path(path_in).joinpath(xbmcvfs.makeLegalFilename(game_list_id))))
			else:
				if self.xbmc_mk_dir(str(Path(path_in).joinpath(xbmcvfs.makeLegalFilename(game_list_id)))):
					result = self.get_path_as_xbmc_str(str(Path(path_in).joinpath(xbmcvfs.makeLegalFilename(game_list_id))))
					xbmc.log(msg='IAGL: game_cache sub-directory {} created'.format(xbmcvfs.makeLegalFilename(game_list_id)),level=xbmc.LOGDEBUG)
				else:					
					xbmc.log(msg='IAGL: Unable to generate game_cache sub-directory {}'.format(xbmcvfs.makeLegalFilename(game_list_id)),level=xbmc.LOGERROR)
		return result

	def update_game_dl_path(self,path_in=None,new_folder=None):
		path_out = path_in
		if isinstance(path_in,str) and Path(path_in).name!=new_folder:
			game_dl_path = Path(path_in).joinpath(new_folder)
			if not game_dl_path.exists():
				game_dl_path.mkdir(exist_ok=True)
			path_out = str(game_dl_path)
			xbmc.log(msg='IAGL:  Download folder updated to {} per post process command'.format(path_out),level=xbmc.LOGDEBUG)
		return path_out

	def extract_addon_db(self,use_backup=False):
		success = False
		if use_backup:
			current_file = self.config.files.get('addon_data_db_zipped_backup')
		else:
			current_file = self.config.files.get('addon_data_db_zipped')
		if current_file.exists():
			my_archive = archive_tool.archive_tool(archive_file=str(current_file),directory_out=str(self.config.files.get('db').parent),flatten_archive=True)
			xbmc.log(msg='IAGL: Extracting zipped db {} to path {}'.format(current_file,self.config.files.get('db')),level=xbmc.LOGDEBUG)
			extracted_files, result = my_archive.extract()
			if result and self.config.files.get('db').exists():
				success = True
			else:
				success = False
		else:
			xbmc.log(msg='IAGL: File not found: {}'.format(current_file),level=xbmc.LOGDEBUG)
			success = False
		return success

	def check_db(self):
		result = False
		if self.config.files.get('db').exists():
			xbmc.log(msg='IAGL: db path {}'.format(self.config.files.get('db')),level=xbmc.LOGDEBUG)
			if self.get_setting('db_version') == self.config.addon.get('version'):
				xbmc.log(msg='IAGL: db version {}'.format(self.get_setting('db_version')),level=xbmc.LOGDEBUG)
				result = True
			else:
				if self.config.files.get('addon_data_db_zipped').exists():
					#Query user about updating db, copying settings here
					xbmc.log(msg='IAGL: new db version found',level=xbmc.LOGDEBUG)
					if xbmcgui.Dialog().yesno(self.get_loc(30373),self.get_loc(30372)):
						from resources.lib import database
						db = database.database(config=self.config,media_type=self.get_setting('media_type'))
						old_settings = db.query_db(db.get_query('get_all_game_list_user_settings'),return_as='dict')
						old_settings_filtered = [x for x in old_settings if any([x.get(y) is not None for y in x.keys() if y.startswith('user_')])]  #Filter down to only those lists that had user settings
						#Transfer new file over to db spot
						result = self.extract_addon_db()
						if result:
							xbmc.log(msg='IAGL: Extracted zipped db with version {} to path {}'.format(self.config.addon.get('version'),str(self.config.files.get('db').parent)),level=xbmc.LOGDEBUG)
							self.config.files.get('addon_data_db_zipped').rename(self.config.files.get('addon_data_db_zipped_backup'))
							xbmcaddon.Addon(id=self.config.addon.get('addon_name')).setSetting(id='db_version',value=self.config.addon.get('version'))
							xfer_results = list()
							#Transfer settings over, convert to the correct format for insert
							for os in old_settings_filtered:
								for k,v in os.items():
									if v is None:
										os[k] = 'NULL'
									elif isinstance(v,str):
										if k=='label':
											pass
										else:
											os[k] = '"{}"'.format(v.replace('"','""'))
									else:
										pass
								xfer_results.append(db.transfer_game_list_user_settings(old_settings=os))
							#Will need to add game specific settings here in the future
							if all([x is not None for x in xfer_results]):
								ok_ret = xbmcgui.Dialog().ok(self.get_loc(30233),self.get_loc(30374))
							elif any([x is not None for x in xfer_results]):
								ok_ret = xbmcgui.Dialog().ok(self.get_loc(30233),self.get_loc(30375))
							else:
								ok_ret = xbmcgui.Dialog().ok(self.get_loc(30270),self.get_loc(30376))
								xbmc.log(msg='IAGL:  Error transferring settings to new addon db: {}'.format(self.config.files.get('addon_data_db_zipped')),level=xbmc.LOGERROR)
						else:
							ok_ret = xbmcgui.Dialog().ok(self.get_loc(30270),self.get_loc(30376))
							xbmc.log(msg='IAGL:  Error extracting addon db: {}'.format(self.config.files.get('addon_data_db_zipped')),level=xbmc.LOGERROR)
						del db
					else:
						selected = xbmcgui.Dialog().select(heading=self.get_loc(30373),list=[self.get_loc(30377),self.get_loc(30378)],useDetails=False)
						if selected == 1:
							xbmc.log(msg='IAGL:  User requested not to be asked about update again.  Moving new db to backup.',level=xbmc.LOGDEBUG)
							self.config.files.get('addon_data_db_zipped').rename(self.config.files.get('addon_data_db_zipped_backup'))
						else:
							xbmc.log(msg='IAGL:  User will be asked about update again later...',level=xbmc.LOGDEBUG)
				else:
					xbmcaddon.Addon(id=self.config.addon.get('addon_name')).setSetting(id='db_version',value=self.config.addon.get('version'))
					xbmc.log(msg='IAGL: new db version not found (settings likely reset?) updating version number',level=xbmc.LOGDEBUG)
					result = True
		else:
			xbmc.log(msg='IAGL: userdata db not found, copying from addon data',level=xbmc.LOGDEBUG)
			if self.config.files.get('addon_data_db_zipped').exists():
				result = self.extract_addon_db()
				if result:
					xbmcaddon.Addon(id=self.config.addon.get('addon_name')).setSetting(id='db_version',value=self.config.addon.get('version'))
					xbmc.log(msg='IAGL: Extracted zipped db with version {} to path {}'.format(self.config.addon.get('version'),str(self.config.files.get('db').parent)),level=xbmc.LOGDEBUG)
					self.config.files.get('addon_data_db_zipped').rename(self.config.files.get('addon_data_db_zipped_backup'))
				else:
					xbmc.log(msg='IAGL:  Error extracting addon db: {}'.format(self.config.files.get('addon_data_db_zipped')),level=xbmc.LOGERROR)
			else:
				xbmc.log(msg='IAGL: addon database file not found, trying to restore from backup.',level=xbmc.LOGDEBUG)
				result = self.extract_addon_db(use_backup=True)
				if result==False:
					xbmc.log(msg='IAGL: addon database file not found, unable to restore from backup.',level=xbmc.LOGERROR)
		return result

	def reset_db(self):
		result = False
		xbmc.log(msg='IAGL: userdata db reset requested',level=xbmc.LOGDEBUG)
		if self.config.files.get('addon_data_db_zipped').exists():
			use_backup=False  #Use the non-backup if it exists
		elif self.config.files.get('addon_data_db_zipped_backup').exists():
			use_backup=True  #If it doesnt exist (likely), use the backup version
		else:
			use_backup = None
		if use_backup is not None:
			if self.config.files.get('db').exists():
				self.config.files.get('db').unlink()
				xbmc.log(msg='IAGL: old db deleted',level=xbmc.LOGDEBUG)
				result = self.extract_addon_db(use_backup=use_backup)
		else:
			xbmc.log(msg='IAGL: addon database file not found',level=xbmc.LOGERROR)
		return result

	def get_android_apps(self):
		result = None
		apps_json = json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Files.GetDirectory","params":{"directory":"androidapp://sources/apps/"},"id": "1"}'))
		if isinstance(apps_json,dict):
			if 'error' in apps_json.keys():
				xbmc.log(msg='IAGL: Kodi did not identify installed android apps: {}'.format(apps_json),level=xbmc.LOGDEBUG)
			else:
				if isinstance(apps_json.get('result'),dict) and isinstance(apps_json.get('result').get('files'),list):
					result = dict(zip([x.get('label') or 'Unknown' for x in apps_json.get('result').get('files') if isinstance(x,dict) and isinstance(x.get('file'),str) and 'androidapp' in x.get('file')],[x.get('file').split('/')[-1] for x in apps_json.get('result').get('files') if isinstance(x,dict) and isinstance(x.get('file'),str) and 'androidapp' in x.get('file')]))
				else:
					xbmc.log(msg='IAGL: Kodi did not identify installed android apps: {}'.format(apps_json),level=xbmc.LOGDEBUG)
		return result

	def get_game_addons(self,as_listitems=True,add_reset_to_default=True):
		result = list()
		addons_json = json.loads(xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Addons.GetAddons","params":{"type":"kodi.gameclient", "enabled": true}, "id": "1"}'))
		if isinstance(addons_json,dict) and isinstance(addons_json.get('result'),dict) and isinstance(addons_json.get('result').get('addons'),list):
			ids = [x.get('addonid') for x in addons_json.get('result').get('addons') if isinstance(x.get('addonid'),str) and x.get('addonid') not in ['game.libretro']]
			result_dict = sorted([{'id':x,'label':xbmcaddon.Addon(id=x).getAddonInfo('name'),'icon':xbmcaddon.Addon(id=x).getAddonInfo('icon')} for x in sorted(set(ids))],key=lambda x: x.get('label'))
			if as_listitems and len(result_dict)>0:
				for r in result_dict:
					li = xbmcgui.ListItem(r.get('label'),offscreen=True)
					li.setArt({k:r.get('icon') for k in ['banner','clearlogo','landscape','poster','thumb']})
					li.setProperties({'id':r.get('id')})
					result.append(li)
				if add_reset_to_default:
					li = xbmcgui.ListItem(self.get_loc(30299),offscreen=True)
					li.setProperties({'id':'reset'})
					result.append(li)
			else:
				result = result_dict
		return result

	def update_search(self,**kwargs):
		return self.update_home_property(type_in='iagl_search',**kwargs)

	def update_random(self,**kwargs):
		return self.update_home_property(type_in='iagl_random',**kwargs)

	def update_android_activity(self,key_in=None,value_in=None):
		if key_in in self.config.defaults.get('android_activity_keys') and value_in is not None:
			try:
				value_set = json.loads(value_in,parse_int=str,parse_float=str)  #Convert to list or dict if possible
			except Exception as exc:
				value_set = value_in
			return self.update_home_property(type_in='iagl_android_activity',**{key_in:value_set})
		else:
			return None

	def convert_android_value(self,value_in=None):
		if isinstance(value_in,str):
			value_out = value_in
		elif isinstance(value_in,list) or isinstance(value_in,dict):
			value_out = json.dumps(value_in)
		else:
			if value_in is not None:
				value_out = str(value_in)
			else:
				value_out = None
		return value_out

	def update_netplay_parameters(self,**kwargs):
		return self.update_home_property(type_in='iagl_netplay_parameters',**kwargs)

	def clear_search(self):
		return self.clear_home_property(type_in='iagl_search')

	def clear_random(self):
		return self.clear_home_property(type_in='iagl_random')

	def clear_android_activity(self):
		return self.clear_home_property(type_in='iagl_android_activity')

	def clear_netplay_parameters(self):
		return self.clear_home_property(type_in='iagl_netplay_parameters')

	def get_search(self):
		return self.get_home_property(type_in='iagl_search')

	def get_random(self):
		return self.get_home_property(type_in='iagl_random')

	def update_search_listitem(self,current_search=None,list_item_in=None,path_in=None):
		list_item_out = list_item_in
		if isinstance(current_search,dict):
			tag = list_item_out.getVideoInfoTag()
			if isinstance(current_search.get('game_lists'),list) and path_in=='search_enter_game_lists':
				list_item_out.setLabel('{} [{} {}]'.format(list_item_out.getLabel(),len(current_search.get('game_lists')),self.get_loc(30215)))
				tag.setPlot('{}[CR][CR]{}:[CR]{}'.format(tag.getPlot(),self.get_loc(30215),'[CR]'.join([x for x in current_search.get('game_lists') if isinstance(x,str)])))
			if isinstance(current_search.get('title'),str) and path_in=='search_enter_game_title':
				if len(current_search.get('title'))>self.config.listitem.get('max_label_length'):
					search_label = '{}...'.format(current_search.get('title')[0:self.config.listitem.get('max_label_length')])
				else:
					search_label = current_search.get('title')
				list_item_out.setLabel('{} [{}]'.format(list_item_out.getLabel(),search_label))
				tag.setPlot('{}[CR][CR]Current Query:[CR]{}'.format(tag.getPlot(),current_search.get('title')))
			if isinstance(current_search.get('genres'),list) and path_in=='search_filter_genre':
				list_item_out.setLabel('{} [{} {}]'.format(list_item_out.getLabel(),len(current_search.get('genres')),self.get_loc(30216)))
				tag.setPlot('{}[CR][CR]{}:[CR]{}'.format(tag.getPlot(),self.get_loc(30216),'[CR]'.join([x for x in current_search.get('genres') if isinstance(x,str)])))
			if isinstance(current_search.get('nplayers'),list) and path_in=='search_filter_nplayers':
				list_item_out.setLabel('{} [{} {}]'.format(list_item_out.getLabel(),len(current_search.get('nplayers')),self.get_loc(30217)))
				tag.setPlot('{}[CR][CR]{}:[CR]{}'.format(tag.getPlot(),self.get_loc(30217),'[CR]'.join([x for x in current_search.get('nplayers') if isinstance(x,str)])))
			if isinstance(current_search.get('studios'),list) and path_in=='search_filter_studio':
				list_item_out.setLabel('{} [{} {}]'.format(list_item_out.getLabel(),len(current_search.get('studios')),self.get_loc(30218)))
				tag.setPlot('{}[CR][CR]{}:[CR]{}'.format(tag.getPlot(),self.get_loc(30218),'[CR]'.join([x for x in current_search.get('studios') if isinstance(x,str)])))
			if isinstance(current_search.get('tags'),list) and path_in=='search_filter_tag':
				list_item_out.setLabel('{} [{} {}]'.format(list_item_out.getLabel(),len(current_search.get('tags')),self.get_loc(30219)))
				tag.setPlot('{}[CR][CR]{}:[CR]{}'.format(tag.getPlot(),self.get_loc(30219),'[CR]'.join([x for x in current_search.get('tags') if isinstance(x,str)])))
			if isinstance(current_search.get('playlists'),list) and path_in=='search_filter_playlist':
				list_item_out.setLabel('{} [{} {}]'.format(list_item_out.getLabel(),len(current_search.get('playlists')),self.get_loc(30220)))
				tag.setPlot('{}[CR][CR]{}:[CR]{}'.format(tag.getPlot(),self.get_loc(30220),'[CR]'.join([x for x in current_search.get('playlists') if isinstance(x,str)])))
			if isinstance(current_search.get('languages'),list) and path_in=='search_filter_language':
				list_item_out.setLabel('{} [{} {}]'.format(list_item_out.getLabel(),len(current_search.get('languages')),self.get_loc(30222)))
				tag.setPlot('{}[CR][CR]{}:[CR]{}'.format(tag.getPlot(),self.get_loc(30222),'[CR]'.join([x for x in current_search.get('languages') if isinstance(x,str)])))
			if isinstance(current_search.get('editions'),list) and path_in=='search_filter_edition':
				list_item_out.setLabel('{} [{} {}]'.format(list_item_out.getLabel(),len(current_search.get('editions')),self.get_loc(30223)))
				tag.setPlot('{}[CR][CR]{}:[CR]{}'.format(tag.getPlot(),self.get_loc(30223),'[CR]'.join([x for x in current_search.get('editions') if isinstance(x,str)])))
			if isinstance(current_search.get('codes'),list) and path_in=='search_filter_code':
				list_item_out.setLabel('{} [{} {}]'.format(list_item_out.getLabel(),len(current_search.get('codes')),self.get_loc(30224)))
				tag.setPlot('{}[CR][CR]{}:[CR]{}'.format(tag.getPlot(),self.get_loc(30224),'[CR]'.join([x for x in current_search.get('codes') if isinstance(x,str)])))
			if isinstance(current_search.get('regions'),list) and path_in=='search_filter_region':
				list_item_out.setLabel('{} [{} {}]'.format(list_item_out.getLabel(),len(current_search.get('regions')),self.get_loc(30221)))
				tag.setPlot('{}[CR][CR]{}:[CR]{}'.format(tag.getPlot(),self.get_loc(30221),'[CR]'.join([x for x in current_search.get('regions') if isinstance(x,str)])))
			if isinstance(current_search.get('ratings'),list) and path_in=='search_filter_rating':
				list_item_out.setLabel('{} [{} {}]'.format(list_item_out.getLabel(),len(current_search.get('ratings')),self.get_loc(30225)))
				tag.setPlot('{}[CR][CR]{}:[CR]{}'.format(tag.getPlot(),self.get_loc(30225),'[CR]'.join([x for x in current_search.get('ratings') if isinstance(x,str)])))
		list_item_out.addContextMenuItems([(self.get_loc(30229),'RunPlugin(plugin://plugin.program.iagl/context_menu/action/reset_{})'.format(path_in)),
											(self.get_loc(30243),'RunPlugin(plugin://plugin.program.iagl/context_menu/action/reset_all_search)'.format(path_in))])
		return list_item_out

	def update_random_listitem(self,current_search=None,list_item_in=None,path_in=None):
		list_item_out = list_item_in
		if isinstance(current_search,dict):
			tag = list_item_out.getVideoInfoTag()
			if isinstance(current_search.get('game_lists'),list) and path_in=='random_enter_game_lists':
				list_item_out.setLabel('{} [{} {}]'.format(list_item_out.getLabel(),len(current_search.get('game_lists')),self.get_loc(30215)))
				tag.setPlot('{}[CR][CR]{}:[CR]{}'.format(tag.getPlot(),self.get_loc(30215),'[CR]'.join([x for x in current_search.get('game_lists') if isinstance(x,str)])))
			if isinstance(current_search.get('num_results'),str) and path_in=='random_enter_num_results':
				if current_search.get('num_results').isdigit():
					list_item_out.setLabel('{} [{}]'.format(list_item_out.getLabel(),current_search.get('num_results')))
					tag.setPlot('{}[CR][CR]{}:[CR]{}'.format(tag.getPlot(),self.get_loc(30215),current_search.get('num_results')))
				else:
					list_item_out.setLabel('{} [All]'.format(list_item_out.getLabel()))
					tag.setPlot('{}[CR][CR]{}:[CR]{}'.format(tag.getPlot(),self.get_loc(30215),'[CR]All'))
			if isinstance(current_search.get('title'),str) and path_in=='random_enter_game_title':
				if len(current_search.get('title'))>self.config.listitem.get('max_label_length'):
					search_label = '{}...'.format(current_search.get('title')[0:self.config.listitem.get('max_label_length')])
				else:
					search_label = current_search.get('title')
				list_item_out.setLabel('{} [{}]'.format(list_item_out.getLabel(),search_label))
				tag.setPlot('{}[CR][CR]Current Query:[CR]{}'.format(tag.getPlot(),current_search.get('title')))
			if isinstance(current_search.get('genres'),list) and path_in=='random_filter_genre':
				list_item_out.setLabel('{} [{} {}]'.format(list_item_out.getLabel(),len(current_search.get('genres')),self.get_loc(30216)))
				tag.setPlot('{}[CR][CR]{}:[CR]{}'.format(tag.getPlot(),self.get_loc(30216),'[CR]'.join([x for x in current_search.get('genres') if isinstance(x,str)])))
			if isinstance(current_search.get('nplayers'),list) and path_in=='random_filter_nplayers':
				list_item_out.setLabel('{} [{} {}]'.format(list_item_out.getLabel(),len(current_search.get('nplayers')),self.get_loc(30217)))
				tag.setPlot('{}[CR][CR]{}:[CR]{}'.format(tag.getPlot(),self.get_loc(30217),'[CR]'.join([x for x in current_search.get('nplayers') if isinstance(x,str)])))
			if isinstance(current_search.get('studios'),list) and path_in=='random_filter_studio':
				list_item_out.setLabel('{} [{} {}]'.format(list_item_out.getLabel(),len(current_search.get('studios')),self.get_loc(30218)))
				tag.setPlot('{}[CR][CR]{}:[CR]{}'.format(tag.getPlot(),self.get_loc(30218),'[CR]'.join([x for x in current_search.get('studios') if isinstance(x,str)])))
			if isinstance(current_search.get('tags'),list) and path_in=='random_filter_tag':
				list_item_out.setLabel('{} [{} {}]'.format(list_item_out.getLabel(),len(current_search.get('tags')),self.get_loc(30219)))
				tag.setPlot('{}[CR][CR]{}:[CR]{}'.format(tag.getPlot(),self.get_loc(30219),'[CR]'.join([x for x in current_search.get('tags') if isinstance(x,str)])))
			if isinstance(current_search.get('playlists'),list) and path_in=='random_filter_playlist':
				list_item_out.setLabel('{} [{} {}]'.format(list_item_out.getLabel(),len(current_search.get('playlists')),self.get_loc(30220)))
				tag.setPlot('{}[CR][CR]{}:[CR]{}'.format(tag.getPlot(),self.get_loc(30220),'[CR]'.join([x for x in current_search.get('playlists') if isinstance(x,str)])))
			if isinstance(current_search.get('languages'),list) and path_in=='random_filter_language':
				list_item_out.setLabel('{} [{} {}]'.format(list_item_out.getLabel(),len(current_search.get('languages')),self.get_loc(30222)))
				tag.setPlot('{}[CR][CR]{}:[CR]{}'.format(tag.getPlot(),self.get_loc(30222),'[CR]'.join([x for x in current_search.get('languages') if isinstance(x,str)])))
			if isinstance(current_search.get('editions'),list) and path_in=='random_filter_edition':
				list_item_out.setLabel('{} [{} {}]'.format(list_item_out.getLabel(),len(current_search.get('editions')),self.get_loc(30223)))
				tag.setPlot('{}[CR][CR]{}:[CR]{}'.format(tag.getPlot(),self.get_loc(30223),'[CR]'.join([x for x in current_search.get('editions') if isinstance(x,str)])))
			if isinstance(current_search.get('codes'),list) and path_in=='random_filter_code':
				list_item_out.setLabel('{} [{} {}]'.format(list_item_out.getLabel(),len(current_search.get('codes')),self.get_loc(30224)))
				tag.setPlot('{}[CR][CR]{}:[CR]{}'.format(tag.getPlot(),self.get_loc(30224),'[CR]'.join([x for x in current_search.get('codes') if isinstance(x,str)])))
			if isinstance(current_search.get('regions'),list) and path_in=='random_filter_region':
				list_item_out.setLabel('{} [{} {}]'.format(list_item_out.getLabel(),len(current_search.get('regions')),self.get_loc(30221)))
				tag.setPlot('{}[CR][CR]{}:[CR]{}'.format(tag.getPlot(),self.get_loc(30221),'[CR]'.join([x for x in current_search.get('regions') if isinstance(x,str)])))
			if isinstance(current_search.get('ratings'),list) and path_in=='random_filter_rating':
				list_item_out.setLabel('{} [{} {}]'.format(list_item_out.getLabel(),len(current_search.get('ratings')),self.get_loc(30225)))
				tag.setPlot('{}[CR][CR]{}:[CR]{}'.format(tag.getPlot(),self.get_loc(30225),'[CR]'.join([x for x in current_search.get('ratings') if isinstance(x,str)])))
		list_item_out.addContextMenuItems([(self.get_loc(30229),'RunPlugin(plugin://plugin.program.iagl/context_menu/action/reset_{})'.format(path_in)),
											(self.get_loc(30243),'RunPlugin(plugin://plugin.program.iagl/context_menu/action/reset_all_random)'.format(path_in))])
		return list_item_out

	def get_search_query(self,current_search_in=None):
		query_out = None
		if isinstance(current_search_in,dict):
			current_search = current_search_in
		else:
			current_search = self.get_search()
		if isinstance(current_search,dict) and len(list(current_search.keys()))>0:
			query_out = ''
			if isinstance(current_search.get('title'),str) and len(current_search.get('title'))>0:
				q = 'games_table.name_search LIKE "%{}%"'.format(current_search.get('title').lower()).replace('%%','%')
				if len(query_out)==0:
					query_out = 'WHERE game_lists_table.user_global_visibility is NULL AND ({})'.format(q)
				else:
					query_out = '{} AND ({})'.format(query_out,q)
			if isinstance(current_search.get('game_lists'),list) and len([x for x in current_search.get('game_lists') if isinstance(x,str)])>0:
				q = 'games_table.game_list IN ({})'.format(','.join(['"{}"'.format(x) for x in current_search.get('game_lists') if isinstance(x,str)]))
				if len(query_out)==0:
					query_out = 'WHERE game_lists_table.user_global_visibility is NULL AND ({})'.format(q)
				else:
					query_out = '{} AND ({})'.format(query_out,q)
			if isinstance(current_search.get('genres'),list) and len([x for x in current_search.get('genres') if isinstance(x,str)])>0:
				q = 'games_table.genres LIKE '+' OR games_table.genres LIKE '.join(['"%""{}""%"'.format(x) for x in current_search.get('genres') if isinstance(x,str)])
				if len(query_out)==0:
					query_out = 'WHERE game_lists_table.user_global_visibility is NULL AND ({})'.format(q)
				else:
					query_out = '{} AND ({})'.format(query_out,q)
			if isinstance(current_search.get('nplayers'),list) and len([x for x in current_search.get('nplayers') if isinstance(x,str)])>0:
				q = 'games_table.nplayers IN ({})'.format(','.join(['"{}"'.format(x) for x in current_search.get('nplayers') if isinstance(x,str)]))
				if len(query_out)==0:
					query_out = 'WHERE game_lists_table.user_global_visibility is NULL AND ({})'.format(q)
				else:
					query_out = '{} AND ({})'.format(query_out,q)
			if isinstance(current_search.get('studios'),list) and len([x for x in current_search.get('studios') if isinstance(x,str)])>0:
				q = 'games_table.studio IN ({})'.format(','.join(['"{}"'.format(x) for x in current_search.get('studios') if isinstance(x,str)]))
				if len(query_out)==0:
					query_out = 'WHERE game_lists_table.user_global_visibility is NULL AND ({})'.format(q)
				else:
					query_out = '{} AND ({})'.format(query_out,q)
			if isinstance(current_search.get('tags'),list) and len([x for x in current_search.get('tags') if isinstance(x,str)])>0:
				q = 'games_table.tags LIKE '+' OR games_table.tags LIKE '.join(['"%""{}""%"'.format(x) for x in current_search.get('tags') if isinstance(x,str)])
				if len(query_out)==0:
					query_out = 'WHERE game_lists_table.user_global_visibility is NULL AND ({})'.format(q)
				else:
					query_out = '{} AND ({})'.format(query_out,q)
			if isinstance(current_search.get('playlists'),list) and len([x for x in current_search.get('playlists') if isinstance(x,str)])>0:
				q = 'games_table.groups LIKE '+' OR games_table.groups LIKE '.join(['"%""{}""%"'.format(x) for x in current_search.get('playlists') if isinstance(x,str)])
				if len(query_out)==0:
					query_out = 'WHERE game_lists_table.user_global_visibility is NULL AND ({})'.format(q)
				else:
					query_out = '{} AND ({})'.format(query_out,q)
			if isinstance(current_search.get('languages'),list) and len([x for x in current_search.get('languages') if isinstance(x,str)])>0:
				q = 'games_table.languages LIKE '+' OR games_table.languages LIKE '.join(['"%""{}""%"'.format(x) for x in current_search.get('languages') if isinstance(x,str)])
				if len(query_out)==0:
					query_out = 'WHERE game_lists_table.user_global_visibility is NULL AND ({})'.format(q)
				else:
					query_out = '{} AND ({})'.format(query_out,q)
			if isinstance(current_search.get('editions'),list) and len([x for x in current_search.get('editions') if isinstance(x,str)])>0:
				q = 'games_table.editions LIKE '+' OR games_table.editions LIKE '.join(['"%""{}""%"'.format(x) for x in current_search.get('editions') if isinstance(x,str)])
				if len(query_out)==0:
					query_out = 'WHERE game_lists_table.user_global_visibility is NULL AND ({})'.format(q)
				else:
					query_out = '{} AND ({})'.format(query_out,q)
			if isinstance(current_search.get('codes'),list) and len([x for x in current_search.get('codes') if isinstance(x,str)])>0:
				q = 'games_table.codes LIKE '+' OR games_table.codes LIKE '.join(['"%""{}""%"'.format(x) for x in current_search.get('codes') if isinstance(x,str)])
				if len(query_out)==0:
					query_out = 'WHERE game_lists_table.user_global_visibility is NULL AND ({})'.format(q)
				else:
					query_out = '{} AND ({})'.format(query_out,q)
			if isinstance(current_search.get('regions'),list) and len([x for x in current_search.get('regions') if isinstance(x,str)])>0:
				q = 'games_table.regions LIKE '+' OR games_table.regions LIKE '.join(['"%""{}""%"'.format(x) for x in current_search.get('regions') if isinstance(x,str)])
				if len(query_out)==0:
					query_out = 'WHERE game_lists_table.user_global_visibility is NULL AND ({})'.format(q)
				else:
					query_out = '{} AND ({})'.format(query_out,q)
			if isinstance(current_search.get('ratings'),list) and len([x for x in current_search.get('ratings') if isinstance(x,str)])>0:
				q = 'games_table.rating IN ({})'.format(','.join(['"{}"'.format(x) for x in current_search.get('ratings') if isinstance(x,str)]))
				if len(query_out)==0:
					query_out = 'WHERE game_lists_table.user_global_visibility is NULL AND ({})'.format(q)
				else:
					query_out = '{} AND ({})'.format(query_out,q)
			if len(query_out)==0:
				query_out = None
		return query_out

	def get_random_num_results(self,current_search_in=None):
		results_out = self.config.defaults.get('default_num_results')
		if isinstance(current_search_in,dict):
			current_search = current_search_in
		else:
			current_search = self.get_random()
		if isinstance(current_search.get('num_results'),str):
			if current_search.get('num_results').isdigit():
				results_out = current_search.get('num_results')
			else:
				results_out = '999999'
		return results_out

	def get_random_query(self,current_search_in=None):
		query_out = None
		if isinstance(current_search_in,dict):
			current_search = current_search_in
		else:
			current_search = self.get_random()
		if isinstance(current_search,dict) and len(list(current_search.keys()))>0:
			query_out = ''
			if isinstance(current_search.get('title'),str) and len(current_search.get('title'))>0:
				q = 'games_table.name_search LIKE "%{}%"'.format(current_search.get('title').lower()).replace('%%','%')
				if len(query_out)==0:
					query_out = 'WHERE game_lists_table.user_global_visibility is NULL AND ({})'.format(q)
				else:
					query_out = '{} AND ({})'.format(query_out,q)
			if isinstance(current_search.get('game_lists'),list) and len([x for x in current_search.get('game_lists') if isinstance(x,str)])>0:
				q = 'games_table.game_list IN ({})'.format(','.join(['"{}"'.format(x) for x in current_search.get('game_lists') if isinstance(x,str)]))
				if len(query_out)==0:
					query_out = 'WHERE game_lists_table.user_global_visibility is NULL AND ({})'.format(q)
				else:
					query_out = '{} AND ({})'.format(query_out,q)
			if isinstance(current_search.get('genres'),list) and len([x for x in current_search.get('genres') if isinstance(x,str)])>0:
				q = 'games_table.genres LIKE '+' OR games_table.genres LIKE '.join(['"%""{}""%"'.format(x) for x in current_search.get('genres') if isinstance(x,str)])
				if len(query_out)==0:
					query_out = 'WHERE game_lists_table.user_global_visibility is NULL AND ({})'.format(q)
				else:
					query_out = '{} AND ({})'.format(query_out,q)
			if isinstance(current_search.get('nplayers'),list) and len([x for x in current_search.get('nplayers') if isinstance(x,str)])>0:
				q = 'games_table.nplayers IN ({})'.format(','.join(['"{}"'.format(x) for x in current_search.get('nplayers') if isinstance(x,str)]))
				if len(query_out)==0:
					query_out = 'WHERE game_lists_table.user_global_visibility is NULL AND ({})'.format(q)
				else:
					query_out = '{} AND ({})'.format(query_out,q)
			if isinstance(current_search.get('studios'),list) and len([x for x in current_search.get('studios') if isinstance(x,str)])>0:
				q = 'games_table.studio IN ({})'.format(','.join(['"{}"'.format(x) for x in current_search.get('studios') if isinstance(x,str)]))
				if len(query_out)==0:
					query_out = 'WHERE game_lists_table.user_global_visibility is NULL AND ({})'.format(q)
				else:
					query_out = '{} AND ({})'.format(query_out,q)
			if isinstance(current_search.get('tags'),list) and len([x for x in current_search.get('tags') if isinstance(x,str)])>0:
				q = 'games_table.tags LIKE '+' OR games_table.tags LIKE '.join(['"%""{}""%"'.format(x) for x in current_search.get('tags') if isinstance(x,str)])
				if len(query_out)==0:
					query_out = 'WHERE game_lists_table.user_global_visibility is NULL AND ({})'.format(q)
				else:
					query_out = '{} AND ({})'.format(query_out,q)
			if isinstance(current_search.get('playlists'),list) and len([x for x in current_search.get('playlists') if isinstance(x,str)])>0:
				q = 'games_table.groups LIKE '+' OR games_table.groups LIKE '.join(['"%""{}""%"'.format(x) for x in current_search.get('playlists') if isinstance(x,str)])
				if len(query_out)==0:
					query_out = 'WHERE game_lists_table.user_global_visibility is NULL AND ({})'.format(q)
				else:
					query_out = '{} AND ({})'.format(query_out,q)
			if isinstance(current_search.get('languages'),list) and len([x for x in current_search.get('languages') if isinstance(x,str)])>0:
				q = 'games_table.languages LIKE '+' OR games_table.languages LIKE '.join(['"%""{}""%"'.format(x) for x in current_search.get('languages') if isinstance(x,str)])
				if len(query_out)==0:
					query_out = 'WHERE game_lists_table.user_global_visibility is NULL AND ({})'.format(q)
				else:
					query_out = '{} AND ({})'.format(query_out,q)
			if isinstance(current_search.get('editions'),list) and len([x for x in current_search.get('editions') if isinstance(x,str)])>0:
				q = 'games_table.editions LIKE '+' OR games_table.editions LIKE '.join(['"%""{}""%"'.format(x) for x in current_search.get('editions') if isinstance(x,str)])
				if len(query_out)==0:
					query_out = 'WHERE game_lists_table.user_global_visibility is NULL AND ({})'.format(q)
				else:
					query_out = '{} AND ({})'.format(query_out,q)
			if isinstance(current_search.get('codes'),list) and len([x for x in current_search.get('codes') if isinstance(x,str)])>0:
				q = 'games_table.codes LIKE '+' OR games_table.codes LIKE '.join(['"%""{}""%"'.format(x) for x in current_search.get('codes') if isinstance(x,str)])
				if len(query_out)==0:
					query_out = 'WHERE game_lists_table.user_global_visibility is NULL AND ({})'.format(q)
				else:
					query_out = '{} AND ({})'.format(query_out,q)
			if isinstance(current_search.get('regions'),list) and len([x for x in current_search.get('regions') if isinstance(x,str)])>0:
				q = 'games_table.regions LIKE '+' OR games_table.regions LIKE '.join(['"%""{}""%"'.format(x) for x in current_search.get('regions') if isinstance(x,str)])
				if len(query_out)==0:
					query_out = 'WHERE game_lists_table.user_global_visibility is NULL AND ({})'.format(q)
				else:
					query_out = '{} AND ({})'.format(query_out,q)
			if isinstance(current_search.get('ratings'),list) and len([x for x in current_search.get('ratings') if isinstance(x,str)])>0:
				q = 'games_table.rating IN ({})'.format(','.join(['"{}"'.format(x) for x in current_search.get('ratings') if isinstance(x,str)]))
				if len(query_out)==0:
					query_out = 'WHERE game_lists_table.user_global_visibility is NULL AND ({})'.format(q)
				else:
					query_out = '{} AND ({})'.format(query_out,q)
			if len(query_out)==0:
				query_out = None
		return query_out

	def get_next_li(self):
		li = xbmcgui.ListItem(self.get_loc(30009),offscreen=True)
		li.setArt({k:self.config.paths.get('assets_url').format('next_{}.png'.format(k)) for k in ['banner','clearlogo','landscape','poster','thumb']})
		li.setProperties({'SpecialSort':'bottom'})
		return li

	def get_history_li(self):
		li = xbmcgui.ListItem(self.get_loc(30006),offscreen=True)
		li.setArt({k:self.config.paths.get('assets_url').format('history_{}.png'.format(k)) for k in ['banner','clearlogo','landscape','poster','thumb']})
		return li

	def add_context_menu(self,li=None,ip=None,type_in=None):
		li_out = li
		if type_in == 'game' and isinstance(ip,str):
			li_out.addContextMenuItems([(self.get_loc(30088),'RunPlugin(plugin://plugin.program.iagl/context_menu/action/add_to_favorites/{})'.format(ip.split('/')[-1])),
										(self.get_loc(30342),'RunPlugin(plugin://plugin.program.iagl/context_menu/action/view_launch_parameters/{})'.format(ip.split('/')[-1])),
										(self.get_loc(30266),'RunPlugin(plugin://plugin.program.iagl/context_menu/action/download_game_to/{})'.format(ip.split('/')[-1])),
										(self.get_loc(30246),'RunPlugin(plugin://plugin.program.iagl/context_menu/action/update_launcher_from_uid/{})'.format(ip.split('/')[-1])),
										(self.get_loc(30247),'RunPlugin(plugin://plugin.program.iagl/context_menu/action/update_launch_command_from_uid/{})'.format(ip.split('/')[-1])),
										(self.get_loc(30248),'RunPlugin(plugin://plugin.program.iagl/context_menu/action/update_game_dl_path_from_uid/{})'.format(ip.split('/')[-1])),
										(self.get_loc(30328),'RunPlugin(plugin://plugin.program.iagl/context_menu/action/reset_game_list_settings_from_uid/{})'.format(ip.split('/')[-1]))])
		if type_in == 'search_link' and isinstance(ip,str):
			li_out.addContextMenuItems([(self.get_loc(30088),'RunPlugin(plugin://plugin.program.iagl/context_menu/action/add_to_favorites_search/{})'.format(ip))])
		if type_in == 'random_link' and isinstance(ip,str):
			li_out.addContextMenuItems([(self.get_loc(30088),'RunPlugin(plugin://plugin.program.iagl/context_menu/action/add_to_favorites_random/{})'.format(ip))])
		if type_in == 'remove_fav_game' and isinstance(ip,str):
			li_out.addContextMenuItems([(self.get_loc(30237),'RunPlugin(plugin://plugin.program.iagl/context_menu/action/remove_game_from_favorites/{})'.format(ip.split('/')[-1]))])
		if type_in == 'remove_fav_link' and isinstance(ip,str):
			li_out.addContextMenuItems([(self.get_loc(30237),'RunPlugin(plugin://plugin.program.iagl/context_menu/action/remove_link_from_favorites)')])
		if type_in == 'game_list' and isinstance(ip,str):
			li_out.addContextMenuItems([(self.get_loc(30303),'RunPlugin(plugin://plugin.program.iagl/context_menu/action/get_game_list_info/{})'.format(ip.split('/')[-1])),
										(self.get_loc(30246),'RunPlugin(plugin://plugin.program.iagl/context_menu/action/update_launcher/{})'.format(ip.split('/')[-1])),
										(self.get_loc(30247),'RunPlugin(plugin://plugin.program.iagl/context_menu/action/update_launch_command/{})'.format(ip.split('/')[-1])),
										(self.get_loc(30249),'RunPlugin(plugin://plugin.program.iagl/context_menu/action/hide_game_list/{})'.format(ip.split('/')[-1])),
										(self.get_loc(30248),'RunPlugin(plugin://plugin.program.iagl/context_menu/action/update_game_dl_path/{})'.format(ip.split('/')[-1])),
										(self.get_loc(30328),'RunPlugin(plugin://plugin.program.iagl/context_menu/action/reset_game_list_settings/{})'.format(ip.split('/')[-1]))])
		return li_out

	def get_current_launcher(self,params_in):
		launcher_out = self.config.defaults.get('launcher')
		if isinstance(params_in,dict) and isinstance(params_in.get('default_global_launcher'),str):
			launcher_out = params_in.get('default_global_launcher')
		if isinstance(params_in,dict) and isinstance(params_in.get('user_global_launcher'),str):
			launcher_out = params_in.get('user_global_launcher') #If user setting exists, it will be the value returned
		return launcher_out

	def create_game_li(self,game_data=None,game_addon=None):
		li = None
		if isinstance(game_data,dict):
			li = xbmcgui.ListItem(label=game_data.get('label'),offscreen=True)
			# li.setArt({k:v for k in game_data.items() if k in self.config.listitem.get('art_keys')})
			# li.setProperties({k:v for k in game_data.items() if k in self.config.listitem.get('property_keys')})
			ginfo = li.getGameInfoTag()
			ginfo.setTitle(game_data.get('label'))
			ginfo.setOverview(game_data.get('overview'))
			ginfo.setPlatform(game_data.get('platform'))
			ginfo.setPublisher(game_data.get('publisher'))
			if isinstance(game_data.get('year'),str) and game_data.get('year').isdigit():
				ginfo.setYear(int(game_data.get('year')))
			if isinstance(game_data.get('genres'),str):
				try:
					cgenres = json.loads(game_data.get('genres'))
					ginfo.setGenres(cgenres)
				except:
					pass
			if isinstance(game_addon,str):
				ginfo.setGameClient(game_addon)
				xbmc.log(msg='IAGL:  Game addon for {} set to {}'.format(game_data.get('label'),game_addon),level=xbmc.LOGINFO)
		return li

	def get_ra_parameter(self,parameter_in=None,text_in=None):
		param_out = None
		if isinstance(text_in,str) and len(text_in)>0 and isinstance(parameter_in,str) and parameter_in in text_in:
			param_out = text_in.split(parameter_in)[-1].split('\n')[0].split('\r')[0].replace('=','').replace('"','').replace("'",'').strip()
		else:
			xbmc.log(msg='IAGL:  Unable to query Retroarch Parameter: {}'.format(parameter_in),level=xbmc.LOGDEBUG)
		return param_out

	def get_core_parameters(self,core_path_in=None,info_files_in=None,ra_default_command=None):
		parameters_out = dict()
		parameters_out['core_path'] = core_path_in
		parameters_out['core_stem'] = core_path_in.stem
		parameters_out['info_file_path'] = info_files_in.get(core_path_in.stem)
		if isinstance(parameters_out.get('info_file_path'),Path) and parameters_out.get('info_file_path').exists():
			ra_info_text = parameters_out.get('info_file_path').read_text(encoding='utf-8',errors='ignore')
			if isinstance(ra_info_text,str) and len(ra_info_text)>0:
				for kk in ['display_name','corename','systemname','supported_extensions','description']:
					parameters_out[kk] = self.get_ra_parameter(parameter_in=kk,text_in=ra_info_text)
		else:
			xbmc.log(msg='IAGL:  Unable to read or find Retroarch info file for core: {}'.format(parameters_out.get('core_stem')),level=xbmc.LOGDEBUG)			
		if isinstance(ra_default_command,str):
			current_command = ra_default_command
			if isinstance(self.get_setting('ra_app_path'),str):
				current_command = current_command.replace('XXAPP_PATH_RAXX',self.get_setting('ra_app_path'))
			if isinstance(parameters_out.get('core_path'),Path):
				current_command = current_command.replace('XXCORE_PATHXX',str(parameters_out.get('core_path')))
			parameters_out['command'] = current_command
		return parameters_out

	def check_android_directory_exists(self,path_in=None):
		exists_out = False
		if isinstance(path_in,str):
			try:
				exists_out = xbmcvfs.exists(path_in)
			except:
				exists_out = False
		return exists_out

	def get_android_libretro_directory(self):
		dir_out = None
		use_alternate = False
		if self.check_android_directory_exists(path_in=self.get_setting('ra_cfg_path') or self.get_setting('ra_cfg_path_android')):
			try:
				dir_out = self.get_ra_parameter(parameter_in='libretro_directory',text_in=Path(self.get_setting('ra_cfg_path') or self.get_setting('ra_cfg_path_android')).read_text(encoding='utf-8',errors='ignore'))
				if isinstance(dir_out,str) and '~' in dir_out:
					dir_out = str(Path(dir_out).expanduser())
			except:
				use_alternate = True
		else:  #If the file does not exist or is not accessible, use the users manually entered value
			use_alternate = True
		if use_alternate and isinstance(self.get_setting('ra_cores_path_android'),str):
			xbmc.log(msg='IAGL:  User has manually set the Android Retroarch Core Path to : {}'.format(self.get_setting('ra_cores_path_android')),level=xbmc.LOGDEBUG)			
			if self.get_setting('ra_cores_path_android').endswith('/'):
				dir_out = self.get_setting('ra_cores_path_android')[:-1]  #Ensure no trailing slash
			else:
				dir_out = self.get_setting('ra_cores_path_android')
		return dir_out

	def get_installed_ra_cores(self,ra_default_command=None):
		cores_out = None
		if isinstance(ra_default_command,dict) and isinstance(ra_default_command.get('command'),str) and isinstance(self.get_setting('ra_cfg_path'),str) and xbmcvfs.exists(self.get_setting('ra_cfg_path')):
			xbmc.log(msg='IAGL:  Querying available RA cores for users system',level=xbmc.LOGDEBUG)
			try:
				ra_cfg_text = Path(self.get_setting('ra_cfg_path')).read_text(encoding='utf-8',errors='ignore')
			except Exception as exc:
				xbmc.log(msg='IAGL:  Unable to read Retroarch config file.  Error: {}'.format(exc),level=xbmc.LOGERROR)
				ra_cfg_text = None
			if isinstance(ra_cfg_text,str) and len(ra_cfg_text)>0:
				libretro_directory = self.get_ra_parameter(parameter_in='libretro_directory',text_in=ra_cfg_text)
				libretro_info_path = self.get_ra_parameter(parameter_in='libretro_info_path',text_in=ra_cfg_text)
				if isinstance(libretro_directory,str) and len(libretro_directory)>0 and Path(libretro_directory).expanduser().exists():
					installed_cores = [x for x in Path(libretro_directory).expanduser().glob('*') if x.is_file() and x.suffix.lower() in ['.dylib','.so','.dll','dylib','so','dll']]
					if isinstance(libretro_info_path,str) and len(libretro_info_path)>0 and Path(libretro_info_path).expanduser().exists():
						info_files = [x for x in Path(libretro_info_path).expanduser().glob('*') if x.is_file() and x.suffix.lower() in ['.info','info']]
						info_files_dict = dict(zip([y.stem for y in info_files],[y for y in info_files]))
					cores_out = [self.get_core_parameters(core_path_in=x,info_files_in=info_files_dict,ra_default_command=ra_default_command.get('command')) for x in installed_cores]
				else:
					xbmc.log(msg='IAGL:  Unable to read Retroarch config path: {}'.format(libretro_directory),level=xbmc.LOGERROR)
		return cores_out			

	def get_other_emus(self,other_emulator_commands=None,other_emulator_settings=None):
		emus_out = None
		if isinstance(other_emulator_commands,list) and len(other_emulator_commands)>0 and isinstance(other_emulator_settings,dict) and len(other_emulator_settings.keys())>0:
			current_emus = [x for x in other_emulator_commands if any([y in x.get('command') for y in other_emulator_settings])]
			if len(current_emus)>0:
				for ce in current_emus:
					for k in other_emulator_settings.keys():
						ce['command'] = ce['command'].replace('XX{}XX'.format(k),other_emulator_settings.get(k))
				emus_out = current_emus
		return emus_out

	class files(object):
		def __init__(self,config=None):
			self.config=config

		def copy_file(self,file_in=None,file_out=None,sucess_if_exists=True,create_directory=True,copy_as_text=False,delete_file_in_on_copy=False):
			sucess = False
			if isinstance(file_in,Path) and isinstance(file_out,Path):
				if file_in.exists():
					if not file_out.exists():
						if not file_out.parent.exists():
							if create_directory:
								file_out.parent.mkdir(parents=True)
							else:
								success = False
								xbmc.log(msg='IAGL:  Destination directory does not exist (use create_directory=True if necessary): {}'.format(file_out.parent),level=xbmc.LOGDEBUG)
						else:
							if copy_as_text:
								bytes_written=file_out.write_text(file_in.read_text(encoding='utf-8',errors='ignore'))
								if bytes_written>0:
									success = True
									xbmc.log(msg='IAGL:  File copied (as text): {} bytes'.format(bytes_written),level=xbmc.LOGDEBUG)
									xbmc.log(msg='IAGL:  From: {}'.format(file_in),level=xbmc.LOGDEBUG)
									xbmc.log(msg='IAGL:  To: {}'.format(file_out),level=xbmc.LOGDEBUG)
									if delete_file_in_on_copy:
										file_in.unlink()
										xbmc.log(msg='IAGL:  From: Deleted',level=xbmc.LOGDEBUG)
								else:
									success = False
									xbmc.log(msg='IAGL:  Failed to copy (0 bytes written): {}'.format(file_in),level=xbmc.LOGERROR)
							else:
								bytes_written=file_out.write_bytes(file_in.read_bytes())
								if bytes_written>0:
									success = True
									xbmc.log(msg='IAGL:  File copied (as bin): {}'.format(bytes_written),level=xbmc.LOGDEBUG)
									xbmc.log(msg='IAGL:  From: {}'.format(file_in),level=xbmc.LOGDEBUG)
									xbmc.log(msg='IAGL:  To: {}'.format(file_out),level=xbmc.LOGDEBUG)
									if delete_file_in_on_copy:
										file_in.unlink()
										xbmc.log(msg='IAGL:  From: Deleted',level=xbmc.LOGDEBUG)
								else:
									success = False
									xbmc.log(msg='IAGL:  Failed to copy (0 bytes written): {}'.format(file_in),level=xbmc.LOGERROR)
					else:
						if sucess_if_exists:
							success = True
							xbmc.log(msg='IAGL:  File already exists: {}'.format(file_out),level=xbmc.LOGDEBUG)
						else:
							success = False
							xbmc.log(msg='IAGL:  File already exists: {}'.format(file_out),level=xbmc.LOGERROR)
				else:
					success = False
					xbmc.log(msg='IAGL:  File to copy does not exist: {}'.format(file_in),level=xbmc.LOGDEBUG)
			else:
				xbmc.log(msg='IAGL:  file_in and file_out must be Path',level=xbmc.LOGERROR)
			return success