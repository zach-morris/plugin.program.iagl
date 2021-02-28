import os, zlib, json, re, time, glob
from pathlib import Path
# from kodi_six import xbmc, xbmcvfs, xbmcgui, xbmcaddon
import xbmc, xbmcvfs, xbmcgui, xbmcaddon
from dateutil import parser as date_parser
from collections import defaultdict
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus as url_quote
from urllib.parse import unquote_plus as url_unquote
from . import xmltodict

ADDON_NAME = 'plugin.program.iagl'
WINDOW_ID = xbmcgui.getCurrentWindowId()
HOME_ID = 10000
ADDON_HANDLE = xbmcaddon.Addon(id=ADDON_NAME)
ADDON_TITLE = ADDON_HANDLE.getAddonInfo('name')
RESET_DIRECTORY_CACHE_TIME = 43200 #Rescan userdata directory every 12 hours unless otherwise updated, this to catch any game cache that needs to be purged
# CHUNK_SIZE = 1024
CHUNK_SIZE = 10485760 #10MB
HEADER_SIZE = 6000 #6kb
MAX_ART = 11 #Max number of arts in the xml files
TEXT_ENCODING='UTF-8'
NOTIFICATION_DEINIT_TIME = 300 #Time to wait after closing a notification for it to de-init
WAIT_FOR_PLAYER_TIME = 5000 #Time to wait after sending retroplayer play command to check status
WAIT_FOR_PROCESS_EXIT = 3 #Time in seconds to wait for subprocess to exit
IGNORE_THESE_FILETYPES = ['.srm','.sav','.fs','.state','.auto','.xml','.nfo'] #Matching filetypes to ignore for re-launching
IGNORE_THESE_FILES = ['win31.bat'] #Matching files to ignore for re-launching
ARCHIVE_FILETYPES = ['001','7z','bz2','cbr','gz','iso','rar','tar','tarbz2','targz','tarxz','tbz2','tgz','xz','zip']
re_game_tags = re.compile(r'\([^)]*\)')
re_game_codes = re.compile(r'\[[^)]*\]')
re_clean_alphanumeric = re.compile(r'([^\s\w]|_)+')

def get_mem_cache(key):
	if xbmcgui.Window(HOME_ID).getProperty(key):
		if key=='iagl_directory':
			dict_out = json.loads(xbmcgui.Window(HOME_ID).getProperty(key))
			#Retranslate all paths back into PosixPath
			dict_out['addon']['dat_files']['path'] = Path(dict_out['addon']['dat_files']['path'])
			dict_out['addon']['dat_files']['files'] = [Path(x) for x in dict_out['addon']['dat_files']['files']]
			dict_out['addon']['databases']['path'] = Path(dict_out['addon']['databases']['path'])
			dict_out['addon']['databases']['files'] = [Path(x) for x in dict_out['addon']['databases']['files']]
			dict_out['addon']['templates']['path'] = Path(dict_out['addon']['templates']['path'])
			dict_out['addon']['templates']['files'] = [Path(x) for x in dict_out['addon']['templates']['files']]
			dict_out['userdata']['game_cache']['path'] = Path(dict_out['userdata']['game_cache']['path'])
			dict_out['userdata']['game_cache']['files'] = [Path(x) for x in dict_out['userdata']['game_cache']['files']]
			dict_out['userdata']['game_cache']['folders'] = [Path(x) for x in dict_out['userdata']['game_cache']['folders']]
			dict_out['userdata']['list_cache']['path'] = Path(dict_out['userdata']['list_cache']['path'])
			dict_out['userdata']['list_cache']['files'] = [Path(x) for x in dict_out['userdata']['list_cache']['files']]
			dict_out['userdata']['dat_files']['path'] = Path(dict_out['userdata']['dat_files']['path'])
			dict_out['userdata']['dat_files']['files'] = [Path(x) for x in dict_out['userdata']['dat_files']['files']]
			return dict_out
		elif key in ['iagl_current_games_list','iagl_current_games_stats_list','iagl_current_game_id','iagl_current_game_list_id','TextViewer_Header','TextViewer_Text','iagl_script_started','iagl_version','iagl_start_time']: #String props
			return xbmcgui.Window(HOME_ID).getProperty(key)
		else: #JSON Props
			return json.loads(xbmcgui.Window(HOME_ID).getProperty(key))
	else:
		return None

def clear_mem_cache(key):
	xbmcgui.Window(HOME_ID).clearProperty(key)
	return True

def set_mem_cache(key,dict_in):
	success = False
	if isinstance(dict_in,dict) or isinstance(dict_in,list):
		xbmcgui.Window(HOME_ID).setProperty(key,json.dumps(dict_in,cls=iagl_encoder))
		success = True
	if isinstance(dict_in,str):
		xbmcgui.Window(HOME_ID).setProperty(key,dict_in)
		success = True
	return success

def set_disc_cache(file_in,games_in,stats_in):
	success = False
	if isinstance(stats_in,dict) and isinstance(games_in,list):
		if not check_if_file_exists(file_in):
			with xbmcvfs.File(str(file_in),'wb') as fi:
				json.dump([games_in,stats_in],fi)
		else:
			xbmc.log(msg='IAGL:  The cache file %(value_in)s already exists'%{'value_in':os.path.split(file_in)[-1]}, level=xbmc.LOGDEBUG)
		success = True
	elif isinstance(stats_in,dict) and games_in is None:
		if not check_if_file_exists(file_in):
			with xbmcvfs.File(str(file_in),'wb') as fi:
				json.dump(stats_in,fi)
		else:
			xbmc.log(msg='IAGL:  The stats cache file %(value_in)s already exists'%{'value_in':os.path.split(file_in)[-1]}, level=xbmc.LOGDEBUG)
		success = True
	return success

def get_disc_cache(file_in):
	with xbmcvfs.File(str(file_in),'rb') as fi:
		disc_cache = json.load(fi)
	if '_stats' in file_in:
		return disc_cache
	else:
		return disc_cache[0],disc_cache[1]

def flatten_list(list_in):
	if isinstance(list_in,list):
		try:
			return [item for sublist in list_in for item in sublist]
		except:
			return list_in
	else:
		return list_in

class iagl_encoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, Path): # Need to translate PosixPath to string for encoding
			return str(obj)
		return json.JSONEncoder.default(self, obj)

def check_userdata_directory(dir_in):
	if check_if_dir_exists(dir_in):
		return Path(xbmcvfs.translatePath(str(dir_in)))
	else:
		if xbmcvfs.mkdir(str(dir_in)):
			xbmc.log(msg='IAGL:  Created directory %(value_in)s'%{'value_in':os.path.split(str(dir_in))[-1]}, level=xbmc.LOGDEBUG)
			return Path(xbmcvfs.translatePath(str(dir_in)))
		else:
			xbmc.log(msg='IAGL:  Unable to create directory %(value_in)s'%{'value_in':os.path.split(dir_in)[-1]}, level=xbmc.LOGERROR)
			return None

def check_if_dir_exists(dir_in):
	if isinstance(dir_in,str):
		return xbmcvfs.exists(os.path.join(dir_in,''))
	elif isinstance(dir_in,Path):
		return dir_in.exists()
	else:
		return False

def check_if_file_exists(file_in):
	if isinstance(file_in,str):
		return xbmcvfs.exists(file_in)
	elif isinstance(file_in,Path):
		return file_in.exists()
	else:
		return False

def get_setting_as(setting_type=None,setting=None):
	if setting_type is not None and setting is not None:
		if setting_type == 'int':
			return int(setting)
		elif setting_type == 'bool':
			if setting.lower().strip() in ['true','enabled','show','0','visible']:
				return True
			else:
				return False
		elif setting_type == 'file_path':
			if setting and isinstance(setting,str) and Path(setting).is_file():
				return Path(setting)
			else:
				return None
		elif setting_type == 'dir_path':
			if setting and isinstance(setting,str) and Path(setting).is_dir():
				return Path(setting)
			else:
				return None
		elif setting_type == 'emulator_type':
			setting_map = {'0':'fs_uae',
						   '1':'pj_64',
						   '2':'dolphin',
						   '3':'mame',
						   '4':'demul',
						   '5':'epsxe'}
			return setting_map.get(setting)
		elif setting_type == 'emulator_name':
			setting_map = {'0':'FS-UAE',
						   '1':'Project 64',
						   '2':'Dolphin',
						   '3':'MAME',
						   '4':'DEMUL',
						   '5':'ePSXe'}
			return setting_map.get(setting)
		elif setting_type == 'emulator_cmd_rep':
			setting_map = {'0':'%APP_PATH_FS_UAE%',
						   '1':'%APP_PATH_PJ64%',
						   '2':'%APP_PATH_DOLPHIN%',
						   '3':'%APP_PATH_MAME%',
						   '4':'%APP_PATH_DEMUL%',
						   '5':'%APP_PATH_EPSXE%'}
			return setting_map.get(setting)
		elif setting_type == 'index_list_route':
			setting_map = {'1':'/archives/Browse All Lists',
						   '2':'/archives/Browse by Category',
						   '3':'/Favorites',
						   '4':'/Search',
						   '5':'/archives/Choose from List'}
			if setting_map.get(setting):
				return setting_map.get(setting)
			else:
				return setting_map.get('5')
		elif setting_type == 'set_content':
			setting_map = {'0':'movies',
						   '1':'tvshows',
						   '2':'videos',
						   '3':'mixed',
						   '4':'games',
						   '5':'None'}
			if setting_map.get(setting):
				return setting_map.get(setting)
			else:
				return setting_map.get('1')	
		elif setting_type == 'game_list_route':
			setting_map = {'0':'list_all',
						   '1':'choose_from_list',
						   '2':'Alphabetical',
						   '3':'Group by Genres',
						   '4':'Group by Years',
						   '5':'Group by Players',
						   '6':'Group by Studio',
						   '7':'Group by Tag',
						   '8':'Group by Custom Groups'}
			if setting_map.get(setting):
				return setting_map.get(setting)
			else:
				return setting_map.get('0')		   
		elif setting_type == 'game_naming_convention':
			setting_map = {'0':'%(title)s',
						   '1':'%(title)s | %(genre)s',
						   '2':'%(title)s | %(date)s',
						   '3':'%(title)s | %(nplayers)s',
						   '4':'%(title)s | %(genre)s | %(date)s',
						   '5':'%(title)s | %(genre)s | %(size)s',
						   '6':'%(title)s | %(genre)s | %(nplayers)s',
						   '7':'%(title)s | %(date)s | %(size)s',
						   '8':'%(title)s | %(date)s | %(nplayers)s',
						   '9':'%(genre)s | %(title)s',
						   '10':'%(date)s | %(title)s',
						   '11':'%(nplayers)s | %(title)s',
						   '12':'%(genre)s | %(title)s | %(date)s',
						   '13':'%(date)s | %(title)s | %(genre)s',
						   '14':'%(nplayers)s | %(title)s | %(genre)s',
						   '15':'%(nplayers)s | %(title)s | %(date)s',
						   '16':'%(title)s | %(genre)s | %(date)s | %(tag)s',
						   '17':'%(title)s | %(genre)s | %(date)s | %(nplayers)s',
						   '18':'%(title)s | %(genre)s | %(nplayers)s | %(tag)s',
						   '19':'%(title)s | %(genre)s | %(date)s | %(size)s'}
			if setting_map.get(setting):
				return setting_map.get(setting)
			else:
				return setting_map.get('0')	
		elif setting_type == 'games_per_page':
			setting_map = {'0':10,
						   '1':25,
						   '2':50,
						   '3':100,
						   '4':150,
						   '5':200,
						   '6':250,
						   '7':300,
						   '8':350,
						   '9':400,
						   '10':450,
						   '11':500}
			if setting_map.get(setting):
				return setting_map.get(setting)
			else:
				return None	   
		elif setting_type == 'forced_viewtype':
			setting_map = {'0': 0,
						 '1': '50',
						 '2': '51',
						 '3': '52',
						 '4': '501',
						 '5': '502',
						 '6': '503',
						 '7': '504',
						 '8': '505',
						 '9': '53',
						 '10': '54',
						 '11': '55',
						 '12': '506',
						 '13': '56',
						 '14': '57',
						 '15': '58',
						 '16': '59',
						 '17': '66',
						 '18': '69',
						 '19': '95',
						 '20': '97',
						 '21': '507',
						 '22': '508',
						 '23': '509',
						 '24': '510',
						 '25': '511',
						 '26': '512',
						 '27': '513',
						 '28': '514',
						 '29': '515',
						 '30': '516',
						 '31': '517',
						 '32': '518',
						 '33': '519',
						 '34': '520',
						 '35': '521',
						 '36': '522',
						 '37': '523',
						 '38': '524',
						 '39': '525',
						 '40': '500',
						 '41': '583',
						 '42': '588'}
			if setting_map.get(setting):
				return setting_map.get(setting)
			else:
				return 0
		elif setting_type == 'ext_launch_env':
			setting_map = {'1':'OSX',
						   '2':'linux',
						   '3':'windows',
						   '4':'android',
						   '5':'android_aarch64',
						   '6':'android_ra32'}
			return setting_map.get(setting)
		elif setting_type == 'display_date_format':
			if isinstance(setting,dict) and setting.get('result') and setting.get('result').get('value') and setting.get('result').get('value') != 'regional':
				return setting.get('result').get('value').replace('DD','%d').replace('MM','%m').replace('YYYY','%Y').replace('D','%-d').replace('M','%-m').replace('YYYY','%Y')
			else:
				return '%x'
	else:
		return None

def get_post_dl_commands():
	return dict(zip(['none','unzip_rom','unzip_and_launch_file','unzip_to_folder_and_launch_file','unzip_and_launch_scummvm_file','unzip_and_launch_win31_file'],['None (Direct File Launch)','UnArchive Game','UnArchive Game, Launch File','UnArchive Game to Folder, Launch File','UnArchive Game, Generate SCUMMVM File','UnArchive Game, Generate WIN31 BAT File']))

def get_downloadpath(path=None,default=None):
	if path=='default' or path is None:
		return default
	else:
		return Path(xbmcvfs.translatePath(path))

def zachs_debug(message=None,level_in=xbmc.LOGWARNING):
	if message is not None:
		xbmc.log(msg='*IAGL TEST*:  %(value_in)s' % {'value_in': message}, level=level_in)

def get_launch_parameter(setting_in=None,retun_val=None):
	if isinstance(setting_in,str) or isinstance(setting_in,Path):
		return str(setting_in)
	else:
		return return_val

def move_file(file_in=None,path_in=None):
	success = False
	if file_in is not None and path_in is not None:
		if check_if_file_exists(file_in):
			success = xbmcvfs.rename(str(file_in),os.path.join(path_in,file_in.name))
			if not success: #Per docs note moving files between different filesystem (eg. local to nfs://) is not possible on all platforms. You may have to do it manually by using the copy and deleteFile functions.
				xbmc.log(msg='IAGL:  Unable to move file %(value_in_1)s to %(value_in_2)s, attempting copy / delete'%{'value_in_1':file_in,'value_in_2':path_in}, level=xbmc.LOGDEBUG)
				if xbmcvfs.copy(str(file_in),os.path.join(path_in,file_in.name)):
					success = xbmcvfs.delete(str(file_in))
	if success:
		xbmc.log(msg='IAGL:  Moved file %(value_in_1)s to %(value_in_2)s'%{'value_in_1':file_in,'value_in_2':path_in}, level=xbmc.LOGDEBUG)
	return success

def delete_file_pathlib(file_in=None,confirm_delete=False):
	success = False
	if file_in.is_file():
		if not confirm_delete:
			try:
				file_in.unlink()
				success = True
			except Exception as exc:
				xbmc.log(msg='IAGL:  Error deleting file %(value_in)s.  Exception %(exc)s' % {'value_in': file_in, 'exc': exc}, level=xbmc.LOGERROR)
				success = False
		else:
			if xbmcgui.Dialog().yesno('Confirm Deletion','Are you sure you want to delete the file %(file_in)s'%{'file_in':file_in.name},'Cancel','Delete'): #Need to localize this eventually
				try:
					file_in.unlink()
					success = True
				except Exception as exc:
					xbmc.log(msg='IAGL:  Error deleting file %(value_in)s.  Exception %(exc)s' % {'value_in': file_in, 'exc': exc}, level=xbmc.LOGERROR)
					success = False
	if success:
		xbmc.log(msg='IAGL:  Deleted file %(value_in)s'%{'value_in':file_in}, level=xbmc.LOGDEBUG)
	return success

def delete_folder_pathlib(folder_in=None,confirm_delete=False):
	success = False
	if folder_in.is_dir():
		if not confirm_delete:
			try:
				folder_in.rmdir()
				success = True
			except Exception as exc:
				xbmc.log(msg='IAGL:  Error deleting folder %(value_in)s.  Exception %(exc)s' % {'value_in': folder_in, 'exc': exc}, level=xbmc.LOGERROR)
				success = False
		else:
			if xbmcgui.Dialog().yesno('Confirm Deletion','Are you sure you want to delete the folder %(folder_in)s'%{'folder_in':folder_in.name},'Cancel','Delete'): #Need to localize this eventually
				try:
					folder_in.rmdir()
					success = True
				except Exception as exc:
					xbmc.log(msg='IAGL:  Error deleting folder %(value_in)s.  Exception %(exc)s' % {'value_in': folder_in, 'exc': exc}, level=xbmc.LOGERROR)
					success = False
	if success:
		xbmc.log(msg='IAGL:  Deleted folder %(value_in)s'%{'value_in':folder_in}, level=xbmc.LOGDEBUG)
	return success

def delete_file(file_in=None,confirm_delete=False):
	success = False
	if file_in is not None:
		if check_if_file_exists(file_in):
			if not confirm_delete:
				success = xbmcvfs.delete(str(file_in))
			else:
				if xbmcgui.Dialog().yesno('Confirm Deletion','Are you sure you want to delete %(file_in)s'%{'file_in':file_in.name},'Cancel','Delete'): #Need to localize this eventually
					success = xbmcvfs.delete(str(file_in))
	if success:
		xbmc.log(msg='IAGL:  Deleted file %(value_in_1)s'%{'value_in_1':file_in}, level=xbmc.LOGDEBUG)
	return success

def read_xml_file(file_in):
	if check_if_file_exists(file_in):
		with xbmcvfs.File(str(file_in)) as fi:
			try:
				return xmltodict.parse(bytes(fi.readBytes()))
			except Exception as exc:
				xbmc.log(msg='IAGL:  Error reading xml file %(value_in)s.  Exception %(exc)s' % {'value_in': file_in, 'exc': exc}, level=xbmc.LOGERROR)
				return None
	else:
		xbmc.log(msg='IAGL:  Error xml file %(value_in)s does not exist' % {'value_in': file_in}, level=xbmc.LOGERROR)
		return None

def read_xml_games(file_in):
	if check_if_file_exists(file_in):
		with xbmcvfs.File(str(file_in)) as fi:
			try:
				games_out = xmltodict.parse(bytes(fi.readBytes())).get('datafile').get('game')
				if isinstance(games_out,list):
					return games_out
				else:
					return [games_out]
			except Exception as exc:
				xbmc.log(msg='IAGL:  Error reading games xml file %(value_in)s.  Exception %(exc)s' % {'value_in': file_in, 'exc': exc}, level=xbmc.LOGERROR)
				return None
	else:
		xbmc.log(msg='IAGL:  Error games xml file %(value_in)s does not exist' % {'value_in': file_in}, level=xbmc.LOGERROR)
		return None

def read_xml_file_et(file_in):
	if check_if_file_exists(file_in):
		with xbmcvfs.File(str(file_in)) as fi:
			try:
				return etree_to_dict(ET.parse(fi).getroot())
			except Exception as exc:
				xbmc.log(msg='IAGL:  Error reading xml file %(value_in)s.  Exception %(exc)s' % {'value_in': file_in, 'exc': exc}, level=xbmc.LOGERROR)
				return None
	else:
		xbmc.log(msg='IAGL:  Error xml file %(value_in)s does not exist' % {'value_in': file_in}, level=xbmc.LOGERROR)
		return None

def get_xml_games(file_in):
	games_out = get_xml_games_path_et(file_in) #Try getting xml header from path (fast)
	# games_out = get_xml_games_path_xmltodict(file_in) #Try getting xml header from path (fast)
	if games_out:
		return games_out
	else:
		return get_xml_games_xbmcvfs_et(str(file_in)) #If it fails, use xbmcvfs (slower)
		# return get_xml_games_xbmcvfs_xmltodict(str(file_in)) #If it fails, use xbmcvfs (slower)

def get_xml_games_path_et(file_in):
	if check_if_file_exists(file_in):
		with file_in.open(mode='rb') as f:
			return [etree_to_dict(x).get('game') for x in ET.parse(f).getroot().iter('game')]
			# return [dict(zip(['@name']+[y.tag for y in list(x)],[x.get('name')]+[y.text for y in list(x)])) for x in ET.parse(f).getroot().iter('game')]
	else:
		xbmc.log(msg='IAGL:  Error xml file %(value_in)s does not exist' % {'value_in': file_in.name}, level=xbmc.LOGERROR)
		return None

def get_xml_games_path_xmltodict(file_in):
	if check_if_file_exists(file_in):
		with file_in.open(mode='rb') as f:
			games_out = xmltodict.parse(f).get('datafile').get('game')
		if isinstance(games_out,list):
			return games_out
		else:
			return [games_out]
	else:
		xbmc.log(msg='IAGL:  Error xml file %(value_in)s does not exist' % {'value_in': file_in.name}, level=xbmc.LOGERROR)
		return None

def get_xml_games_xbmcvfs_et(file_in):
	if check_if_file_exists(file_in):
		with xbmcvfs.File(str(file_in)) as fi:
			try:
				return [etree_to_dict(x).get('game') for x in ET.parse(fi).getroot().iter('game')]
			except Exception as exc:
				xbmc.log(msg='IAGL:  Error reading xml file %(value_in)s.  Exception %(exc)s' % {'value_in': file_in, 'exc': exc}, level=xbmc.LOGERROR)
				return None
	else:
		xbmc.log(msg='IAGL:  Error xml file %(value_in)s does not exist' % {'value_in': file_in}, level=xbmc.LOGERROR)
		return None

def split_value(value_in):
	if isinstance(value_in,str):
		return [x.strip() for x in value_in.split(',') if x]
	else:
		return None

def combine_value(value_in):
	if isinstance(value_in,list):
		return ','.join(value_in)
	elif isinstance(value_in,str):
		return value_in
	else:
		return None

def get_game_tags(value_in):
	if isinstance(value_in,str):
		return [x.strip() for x in flatten_list([x.replace('(','').replace(')','').split(',') for x in re_game_tags.findall(value_in)])]
	else:
		return None

def get_game_size(value_in):
	if isinstance(value_in,dict):
		return sum(map(int,[x.get('@size') for x in [value_in] if x and x.get('@size')]))
	elif isinstance(value_in,list):
		return sum(map(int,[x.get('@size') for x in value_in if x and x.get('@size')]))
	else:
		return None

def map_database_listitem_dict(dict_in,default_dict,game_list_name,type_in=None):
	props = None
	if type_in is None:
		label2 = dict_in.get('label') #We will use label2 to carry the next route by default
	if game_list_name is None:
		# label = dict_in.get('label')
		plot = dict_in.get('plot')
	else:
		# label = '%(label)s for %(game_list_name)s'%{'label':dict_in.get('label'),'game_list_name':game_list_name}
		plot = '%(label)s for %(game_list_name)s'%{'label':dict_in.get('plot'),'game_list_name':game_list_name}
	if dict_in.get('sort'):
		props = {'SpecialSort':dict_in.get('sort')}
	return {'values': {'label':dict_in.get('label'),'label2':label2},
			'info':   {'originaltitle':dict_in.get('label'),'title':dict_in.get('label'),'plot':plot,'trailer':choose_trailer(dict_in.get('trailer'),default_dict.get('trailer'))},
			'art':    {'poster':choose_image(dict_in.get('thumb'),default_dict.get('thumb')),
					   'banner':choose_image(dict_in.get('banner'),default_dict.get('banner')),
					   'fanart':choose_image(dict_in.get('fanart'),default_dict.get('fanart')),
					   'clearlogo':choose_image(dict_in.get('logo'),default_dict.get('logo')),
					   'icon':choose_image(dict_in.get('logo'),default_dict.get('logo')),
					   'thumb':choose_image(dict_in.get('thumb'),default_dict.get('thumb')),
					   },
			'properties':props,
			}

def clean_query_values(value_in):
	if not value_in:
		return 'All'
	elif isinstance(value_in,list):
		return ', '.join(value_in)
	else:
		return value_in

def map_search_random_listitem_dict(dict_in,default_dict,search_query,type_in=None):
	if type_in is None:
		label2 = dict_in.get('label2') #We will use label2 to carry the next route by default
	if isinstance(search_query,dict) and search_query.get(dict_in.get('label2')):
		if isinstance(search_query.get(dict_in.get('label2')),list):
			label_value = ', '.join(search_query.get(dict_in.get('label2')))
		else:
			label_value = search_query.get(dict_in.get('label2'))
		label = '%(label)s[CR][COLOR FF12A0C7]%(value)s[/COLOR]'%{'label':dict_in.get('label'),'value':label_value}
		plot = '%(label)s[CR][CR]Current Setting:[CR]%(value)s'%{'label':dict_in.get('plot'),'value':label_value}
	else:
		label = dict_in.get('label')
		plot = dict_in.get('plot')
	if dict_in.get('label2') in ['execute','execute_link']:
		query_summary_map = {'lists':'Game Lists','genre':'Genres','nplayers':'Players','year':'Years','studio':'Studios','tag':'Tags','groups':'Custom Groups','title':'Title','num_of_results':'Number of Results'}
		if isinstance(search_query,dict):
			xbmc.log(msg='IAGL:  Search Query Mapping:', level=xbmc.LOGDEBUG)
			xbmc.log(msg='IAGL:  %(mapping)s'%{'mapping':['%(item)s: %(values)s'%{'item':query_summary_map.get(k),'values':clean_query_values(v)} for k,v in search_query.items() if k in query_summary_map.keys()]}, level=xbmc.LOGDEBUG)
			label_value = '[CR]'.join(['%(item)s: %(values)s'%{'item':query_summary_map.get(k),'values':clean_query_values(v)} for k,v in search_query.items() if k in query_summary_map.keys()])
			plot = '%(label)s%(query_string)s %(total)s[CR][CR]%(value)s'%{'label':dict_in.get('plot'),'query_string':loc_str(30394),'total':next(iter([x for x in [search_query.get('game_count')] if x]),'Unknown'),'value':label_value}
		return {'values': {'label':label,'label2':label2},
				'info':   {'originaltitle':dict_in.get('label'),'title':dict_in.get('label'),'plot':plot,'trailer':choose_trailer(dict_in.get('trailer'),default_dict.get('trailer'))},
				'art':    {'poster':choose_image(dict_in.get('thumb'),default_dict.get('thumb')),
						   'banner':choose_image(dict_in.get('banner'),default_dict.get('banner')),
						   'fanart':choose_image(dict_in.get('fanart'),default_dict.get('fanart')),
						   'clearlogo':choose_image(dict_in.get('logo'),default_dict.get('logo')),
						   'icon':choose_image(dict_in.get('logo'),default_dict.get('logo')),
						   'thumb':choose_image(dict_in.get('thumb'),default_dict.get('thumb')),
						   },
				'properties': {'query' : json.dumps(search_query)}
				}
	else:
		return {'values': {'label':label,'label2':label2},
				'info':   {'originaltitle':dict_in.get('label'),'title':dict_in.get('label'),'plot':plot,'trailer':choose_trailer(dict_in.get('trailer'),default_dict.get('trailer'))},
				'art':    {'poster':choose_image(dict_in.get('thumb'),default_dict.get('thumb')),
						   'banner':choose_image(dict_in.get('banner'),default_dict.get('banner')),
						   'fanart':choose_image(dict_in.get('fanart'),default_dict.get('fanart')),
						   'clearlogo':choose_image(dict_in.get('logo'),default_dict.get('logo')),
						   'icon':choose_image(dict_in.get('logo'),default_dict.get('logo')),
						   'thumb':choose_image(dict_in.get('thumb'),default_dict.get('thumb')),
						   },
				}

def map_game_list_listitem_dict(dict_in,default_dict,fn_in,type_in=None):
	if type_in is None:
		label2 = fn_in #We will use label2 to carry the next route by default
	return {'values': {'label':dict_in.get('emu_name'),'label2':label2},
			'info':   {'title':dict_in.get('emu_name'),
					   'originaltitle':dict_in.get('emu_name'),
					   'date':get_date(dict_in.get('emu_date')),
					   'credits':dict_in.get('emu_author'),
					   'plot':dict_in.get('emu_comment'),
					   'tag':'Launch using %(value_in)s'%{'value_in':dict_in.get('emu_launcher')},
					   'genre':split_value(dict_in.get('emu_category')),
					   'trailer':choose_trailer(dict_in.get('emu_trailer'))},
						# 'size' : game_lists_dict.get('dat_filesize')[aa]
			'art':    {'poster':choose_image(dict_in.get('emu_thumb'),default_dict.get('thumb')),
					   'banner':choose_image(dict_in.get('emu_banner'),default_dict.get('banner')),
					   'fanart':choose_image(dict_in.get('emu_fanart'),default_dict.get('fanart')),
					   'clearlogo':choose_image(dict_in.get('emu_logo')),
					   'icon':choose_image(dict_in.get('emu_logo')),
					   'thumb':choose_image(dict_in.get('emu_thumb'),default_dict.get('thumb'))},
		'properties': {'emu_visibility' : dict_in.get('emu_visibility'),
						'emu_category' : dict_in.get('emu_category'),
						'emu_description' : dict_in.get('emu_description'),
						'emu_version' : dict_in.get('emu_version'),
						'emu_date' : dict_in.get('emu_date'),
						'emu_baseurl' : dict_in.get('emu_baseurl'),
						'emu_launcher' : dict_in.get('emu_launcher'),
						'emu_ext_launch_cmd' : dict_in.get('emu_ext_launch_cmd'),
						'emu_default_addon' : dict_in.get('emu_default_addon'),
						'emu_downloadpath' : dict_in.get('emu_downloadpath'),
						'emu_comment' : dict_in.get('emu_comment'),
						'emu_author' : dict_in.get('emu_author'),
						'dat_filename' : fn_in},
			}

def map_game_choose_list_listitem_dict(category_label,category_count,default_dict,categories_in,game_list_name,type_in=None):
	dict_in = [x for x in categories_in if x.get('label')==category_label]
	if not dict_in:
		dict_in = [default_dict]
		dict_in[0]['label'] = category_label
		dict_in[0]['label2'] = category_label
	current_title = dict_in[0].get('label')
	current_plot = dict_in[0].get('plot')
	if category_count:
		current_title = '%(value)s (%(total)s)'%{'value':dict_in[0].get('label'),'total':category_count}
		current_plot = '%(value)s[CR][CR]Total Games in this Category: %(total)s'%{'value':dict_in[0].get('plot'),'total':category_count}
	return {'values': {'label':current_title,'label2':dict_in[0].get('label')},
			'info':   {'originaltitle':dict_in[0].get('label'),'title':current_title,'plot':current_plot,'trailer':choose_trailer(dict_in[0].get('trailer'),default_dict.get('trailer'))},
			'art':    {'poster':choose_image(dict_in[0].get('thumb'),dict_in[0].get('thumb')),
					   'banner':choose_image(dict_in[0].get('banner'),default_dict.get('banner')),
					   'fanart':choose_image(dict_in[0].get('fanart'),default_dict.get('fanart')),
					   'clearlogo':choose_image(dict_in[0].get('logo'),default_dict.get('logo')),
					   'icon':choose_image(dict_in[0].get('logo'),default_dict.get('logo')),
					   'thumb':choose_image(dict_in[0].get('thumb'),default_dict.get('thumb')),
					   },
			}

def map_game_listitem_dict(dict_in,parent_dict_in,default_dict,game_list_id,clean_titles,naming_convention,date_convention,type_in=None,include_extra_art=True):
	if type_in is None:
		label2 = dict_in.get('@name') #We will use label2 to carry the next route by default
	starts_with = None
	if dict_in.get('description'):
		if dict_in.get('description')[0].isdigit():
			starts_with = '#'
		else:
			starts_with = dict_in.get('description')[0].upper()
	dict_out = {'values': {'label':dict_in.get('description'),'label2':url_quote(label2)}, #Need to url_quote route in case its got wonky chars in it
			'info':   {'title':dict_in.get('description'),
					   'originaltitle':re_game_codes.sub('',re_game_tags.sub('',dict_in.get('description')).strip()).strip(), #Clean name
					   'date':get_date(dict_in.get('releasedate'),dict_in.get('year')),
					   'year':get_date(dict_in.get('releasedate'),dict_in.get('year'),format_in='%Y'),
					   'studio':dict_in.get('studio'),
					   'genre':split_value(dict_in.get('genre')),
					   'showlink':split_value(dict_in.get('groups')),
					   'rating':dict_in.get('rating'),
					   'mpaa':dict_in.get('ESRB'),
					   'plot':dict_in.get('plot'),
					   'tag':get_game_tags(dict_in.get('@name')),
					   'trailer':choose_trailer(dict_in.get('videoid')),
					   # 'path':'plugin://plugin.program.iagl/game/%(game_list_id)s/%(label2)s'%{'game_list_id':game_list_id,'label2':label2},
					   'size':get_game_size(dict_in.get('rom'))},
			'art':    {'poster':choose_image(dict_in.get('boxart1'),dict_in.get('snapshot1'),default_dict.get('thumb')),
					   'banner':choose_image(dict_in.get('banner1'),default_dict.get('banner')),
					   'fanart':choose_image(dict_in.get('fanart1'),default_dict.get('fanart')),
					   #Possibly to be added later if I clean up the xml format
					   # 'extrafanart1':choose_image(dict_in.get('fanart2')),
					   # 'extrafanart2':choose_image(dict_in.get('fanart3')),
					   # 'boxfront':choose_image(dict_in.get('boxfront'),dict_in.get('boxart1')),
					   # 'boxback':choose_image(dict_in.get('boxback'),dict_in.get('boxart2')),
					   # 'cartridge':choose_image(dict_in.get('cartridge'),dict_in.get('boxart3')),
					   # 'snap':choose_image(dict_in.get('snap'),dict_in.get('snapshot2')),
					   # 'title':choose_image(dict_in.get('title'),dict_in.get('snapshot1')),
					   # 'discart':choose_image(dict_in.get('discart'),dict_in.get('boxart3')),
					   'landscape':choose_image(dict_in.get('snapshot1')),
					   'clearlogo':choose_image(dict_in.get('clearlogo1')),
					   'icon':choose_image(dict_in.get('icon'),dict_in.get('clearlogo1')),
					   'thumb':choose_image(dict_in.get('boxart1'),dict_in.get('snapshot1'),default_dict.get('thumb'))},
		'properties': {'route' : next(iter([x for x in [dict_in.get('route'),game_list_id] if x]),game_list_id),  #Look for favorite hyperlink first, then default to current game list id
					   'nplayers':dict_in.get('nplayers'),
					   'perspective':dict_in.get('perspective'),
					   'description':dict_in.get('description'), #Need to carry a clean version of this for favorites if necessary
					   'starts_with':starts_with,
					   'platform_name':parent_dict_in.get('emu_name'),
					   'platform_description':parent_dict_in.get('emu_description'),
					   'platform_category':parent_dict_in.get('emu_category'),
					   'platform_banner':choose_image(parent_dict_in.get('emu_banner')),
					   'platform_fanart':choose_image(parent_dict_in.get('emu_fanart')),
					   'platform_clearlogo':choose_image(parent_dict_in.get('emu_logo')),
					   'platform_thumb':choose_image(parent_dict_in.get('emu_thumb')),
					   'platform_plot':parent_dict_in.get('emu_comment'),
					   'emu_command':dict_in.get('emu_command'),
					   'emu_baseurl':parent_dict_in.get('emu_baseurl'),
					   'emu_launcher':parent_dict_in.get('emu_launcher'),
					   'emu_ext_launch_cmd':next(iter([x for x in [dict_in.get('rom_override_cmd'),parent_dict_in.get('emu_ext_launch_cmd')] if x]),'none'), #Look for override commands first, then default to game list settings
					   'emu_default_addon':next(iter([x for x in [dict_in.get('rom_override_cmd'),parent_dict_in.get('emu_default_addon')] if x]),'default'),
					   'emu_downloadpath':next(iter([x for x in [dict_in.get('rom_override_downloadpath'),parent_dict_in.get('emu_downloadpath')] if x]),'default'),
					   'emu_postdlaction':next(iter([x for x in [dict_in.get('rom_override_postdl'),parent_dict_in.get('emu_postdlaction')] if x]),'none'),
					   'rom' : json.dumps(dict_in.get('rom')),
					   },
			}
	if include_extra_art:
		for kk in zip(['game_boxarts','game_banners','game_snapshots','game_logos','game_fanarts'],['boxart','banner','snapshot','clearlogo','fanart']):
			dict_out['properties'][kk[0]] = json.dumps([x for x in [dict_in.get('%(kk)s%(nn)s'%{'kk':kk[1],'nn':y}) for y in range(1,MAX_ART)] if x])
	else:
		for kk in zip(['game_boxarts','game_banners','game_snapshots','game_logos','game_fanarts'],['thumb','banner','landscape','clearlogo','fanart']):
			dict_out['properties'][kk[0]] = json.dumps([dict_out.get('art').get(kk[1])])

	if dict_out.get('info').get('date') is None: #Hack because Kodi spams the logs if date is None
		del dict_out['info']['date']
	if naming_convention != '%(title)s':
		if clean_titles:
			dict_out['values']['label'] = naming_convention%{'date':get_date(dict_in.get('releasedate'),dict_in.get('year'),format_in=date_convention),'genre':dict_in.get('genre'),'nplayers':dict_in.get('nplayers'),'size':bytes_to_string_size(dict_out.get('info').get('size')),'tag':combine_value(dict_out.get('info').get('tag')),'title':dict_out.get('info').get('originaltitle')}
		else:
			dict_out['values']['label'] = naming_convention%{'date':get_date(dict_in.get('releasedate'),dict_in.get('year'),format_in=date_convention),'genre':dict_in.get('genre'),'nplayers':dict_in.get('nplayers'),'size':bytes_to_string_size(dict_out.get('info').get('size')),'tag':combine_value(dict_out.get('info').get('tag')),'title':dict_in.get('description')}
		dict_out['values']['label'] = dict_out['values']['label'].replace('| None ','').replace('| None','').strip()
	else:
		if clean_titles:
			dict_out['values']['label'] = dict_out['info']['originaltitle']
	dict_out['info']['title'] = dict_out['values']['label'] #Estuary seems to use title now as the listitem label, so updating the title here is necessary
	return dict_out

def map_retroplayer_listitem_dict(dict_in,launch_dict_in): #https://codedocs.xyz/xbmc/xbmc/group__python__xbmcgui__listitem.html
	dict_out = {'values': {'label':dict_in.get('values').get('label'),'label2':dict_in.get('values').get('label2')},
			'info':   {'title':dict_in.get('info').get('originaltitle'),
					   'platform':dict_in.get('properties').get('platform_description'),
					   'genre':dict_in.get('info').get('genre'),
					   'publisher':dict_in.get('info').get('studio'),
					   'overview':dict_in.get('info').get('plot'),
					   'year':dict_in.get('info').get('year'),
					   'gameclient':next(iter([x for x in [launch_dict_in.get('default_addon')] if x and x!='none']),None)},
			'art':    {'poster':dict_in.get('art').get('poster'),
					   'banner':dict_in.get('art').get('banner'),
					   'fanart':dict_in.get('art').get('fanart'),
					   'landscape':dict_in.get('art').get('landscape'),
					   'clearlogo':dict_in.get('art').get('clearlogo'),
					   'icon':dict_in.get('art').get('icon'),
					   'thumb':dict_in.get('art').get('thumb')},
			}
	return dict_out

def map_wizard_report_listitem_dict(dict_in,media_type='video'):
	if isinstance(dict_in,dict):
		lis = list()
		for ii,dd in enumerate(dict_in.get('label')):
			li = xbmcgui.ListItem(label=dd,offscreen=True)
			if dict_in.get('info'):
				li.setInfo(media_type,dict_in.get('info')[ii])
			if dict_in.get('art'):
				li.setArt(dict_in.get('art')[ii])
			lis.append(li)
		return lis
	else:
		return None

def get_game_stat_set(game_stats_in=None,type_in=None):
	if isinstance(game_stats_in,list) and type_in:
		stats_out = sorted(set(flatten_list([x[type_in]['all'] for x in game_stats_in])))
		return stats_out
	else:
		return []

def get_history_listitem(media_type='video'):
	li_dict = {'info':{'genre':'History','plot':'View the games you have previously played'},
	'art':{'icon':'special://home/addons/plugin.program.iagl/resources/skins/Default/media/icon.png',
	'thumb':'special://home/addons/plugin.program.iagl/resources/skins/Default/media/last_played.jpg',
	'poster':'special://home/addons/plugin.program.iagl/resources/skins/Default/media/last_played.jpg',
	'banner':'special://home/addons/plugin.program.iagl/resources/skins/Default/media/last_played_banner.jpg',
	'fanart':'special://home/addons/plugin.program.iagl/resources/skins/Default/media/fanart.jpg'}}
	li = xbmcgui.ListItem(label='Last Played',offscreen=True)
	li.setInfo(media_type,li_dict.get('info'))
	li.setArt(li_dict.get('art'))
	li.setProperties({'SpecialSort':'bottom'})
	return li

def get_next_page_listitem(current_page,page_count,next_page,total_items,media_type='video'):
	li = xbmcgui.ListItem(label='Next >>',offscreen=True)
	li.setInfo(media_type,{'plot':'Page %(current_page)s of %(page_count)s.  Next page is %(next_page)s.  Total of %(total_items)s games in this archive.'%{'current_page':current_page,'page_count':page_count,'next_page':next_page,'total_items':total_items}})
	li.setArt({'icon':'special://home/addons/plugin.program.iagl/resources/skins/Default/media/next.png','thumb':'special://home/addons/plugin.program.iagl/resources/skins/Default/media/next.png'})
	li.setProperties({'SpecialSort':'bottom'})
	return li

def get_database_listitem(dict_in,media_type='video'):
	li = xbmcgui.ListItem(label=dict_in.get('values').get('label'),label2=dict_in.get('values').get('label2'),offscreen=True)
	li.setInfo(media_type,dict_in.get('info'))
	li.setArt(dict_in.get('art'))
	li.setProperties(dict_in.get('properties'))
	return li

def get_game_list_listitem(dict_in,filter_in=None,media_type='video'):
	li=None
	if dict_in.get('properties').get('emu_visibility') != 'hidden' and (filter_in is None or (all([filter_in.get('info').get(kk) in dict_in.get('info').get(kk) if dict_in.get('info').get(kk) else False for kk in filter_in.get('info').keys()]) and all([filter_in.get('properties').get(kk) in dict_in.get('properties').get(kk) if dict_in.get('properties').get(kk) else False for kk in filter_in.get('properties').keys()]))):
		li = xbmcgui.ListItem(label=dict_in.get('values').get('label'),label2=dict_in.get('values').get('label2'),offscreen=True)
		li.setInfo(media_type,dict_in.get('info'))
		li.setArt(dict_in.get('art'))
	return li

def get_retroplayer_item_and_listitem(dict_in,launch_file,media_type='game'):
	# launch_item = None
	launch_li = None
	# if launch_file:
	# 	launch_item = str(launch_file)
	if launch_file and dict_in:
		launch_li = xbmcgui.ListItem(label=dict_in.get('values').get('label'),label2=dict_in.get('values').get('label2'),offscreen=True)
		launch_li.setInfo(media_type,dict_in.get('info'))
		launch_li.setArt(dict_in.get('art'))
		launch_li.setPath(path=str(launch_file))
	return launch_li

def get_game_choose_list_listitem(dict_in,filter_in=None,media_type='video'):
	if isinstance(dict_in,dict):
		li = xbmcgui.ListItem(label=dict_in.get('values').get('label'),label2=dict_in.get('values').get('label2'),offscreen=True)
		li.setInfo(media_type,dict_in.get('info'))
		li.setArt(dict_in.get('art'))
		li.setProperties(dict_in.get('properties'))
		return li
	else:
		return None

def update_listitem_title(li_in,update_item,media_type='video'):
	if update_item:
		li_in.setInfo(media_type,{'title':'%(emu_name)s - %(label)s'%{'emu_name':li_in.getProperty('platform_description'),'label':li_in.getLabel()}})
		li_in.setLabel('%(emu_name)s - %(label)s'%{'emu_name':li_in.getProperty('platform_description'),'label':li_in.getLabel()})
		return li_in
	else:
		return li_in

def game_filter(dict_in,filter_in):
	include = list()
	if filter_in is not None: #Game must match all filter query props
		for kk in ['info','properties']:
			for k,v in filter_in.get(kk).items():
				if isinstance(v,str):
					if dict_in.get(kk).get(k) is None and v=='Unknown':
						include.append(True)
					elif isinstance(dict_in.get(kk).get(k),list) and v!='Unknown':
						if v in dict_in.get(kk).get(k):
							include.append(True)
						else:
							include.append(False)
					elif isinstance(dict_in.get(kk).get(k),str) and v!='Unknown':
						if v==dict_in.get(kk).get(k):
							include.append(True)
						else:
							include.append(False)
					else:
						include.append(False)
				if isinstance(v,list):
					if dict_in.get(kk).get(k) is None and 'Unknown' in v:
						include.append(True)
					elif isinstance(dict_in.get(kk).get(k),list) and 'Unknown' not in v:
						if any([vv in dict_in.get(kk).get(k) for vv in v]):
							include.append(True)
						else:
							include.append(False)
					elif isinstance(dict_in.get(kk).get(k),str) and 'Unknown' not in v:
						if any([vv==dict_in.get(kk).get(k) for vv in v]):
							include.append(True)
						else:
							include.append(False)
					else:
						include.append(False)
				if isinstance(v,re.Pattern):
					if isinstance(dict_in.get(kk).get(k),str):
						if v.findall(dict_in.get(kk).get(k)):
							include.append(True)
						else:
							include.append(False)
					else:
						include.append(False)
	else:
		include.append(True)
	return include

def get_game_listitem(dict_in,filter_in,media_type='video'):
	li=None
	include = game_filter(dict_in,filter_in)
	# 	zachs_debug('Filter')
	# 	zachs_debug(filter_in)
	# 	zachs_debug('Dict')
	# 	zachs_debug(dict_in)
	# 	zachs_debug('Unknowns')
	# 	zachs_debug([True if not dict_in.get('info').get(k) else False for k,v in filter_in.get('info').items() if v=='Unknown'])
	# 	zachs_debug([True if not dict_in.get('properties').get(k) else False for k,v in filter_in.get('properties').items() if v=='Unknown'])
	# 	zachs_debug('Knowns')
	# 	zachs_debug([v in dict_in.get('info').get(k) if (v is not None and dict_in.get('info').get(k) is not None) else False for k,v in filter_in.get('info').items() if v!='Unknown'])
	# 	zachs_debug([v in dict_in.get('info').get(k) if v is not None else False for k,v in filter_in.get('info').items() if v!='Unknown' and dict_in.get('info') is not None and dict_in.get('info').get(k) is not None])
	# 	zachs_debug([v in dict_in.get('properties').get(k) if (v is not None and dict_in.get('properties').get(k) is not None) else False for k,v in filter_in.get('properties').items() if v!='Unknown'])
	# 	zachs_debug([v in dict_in.get('properties').get(k) if v is not None else False for k,v in filter_in.get('properties').items() if v!='Uknown' and dict_in.get('properties') is not None and dict_in.get('properties').get(k) is not None])
	# if filter_in is None or (all([v in dict_in.get('info').get(k) if (v is not None and dict_in.get('info').get(k) is not None) else False for k,v in filter_in.get('info').items() if v!='Unknown']) and all([v in dict_in.get('properties').get(k) if (v is not None and dict_in.get('properties').get(k) is not None) else False for k,v in filter_in.get('properties').items() if v!='Unknown']) and all([True if not dict_in.get('info').get(k) else False for k,v in filter_in.get('info').items() if v=='Unknown']) and all([True if not dict_in.get('properties').get(k) else False for k,v in filter_in.get('properties').items() if v=='Unknown'])):
	if all(include):
		li = xbmcgui.ListItem(label=dict_in.get('values').get('label'),label2=dict_in.get('values').get('label2'),offscreen=True)
		li.setInfo(media_type,dict_in.get('info'))
		li.setArt(dict_in.get('art'))
		li.setProperties(dict_in.get('properties'))
	return li

def choose_image(*args):
	image = next(iter([x for x in args if x and isinstance(x,str)]), None)
	if image is not None and 'http' not in image and 'special:' not in image:
		return 'https://i.imgur.com/%(image)s'%{'image':image}
	else:
		return image

def clean_image_entry(value_in):
	if value_in and isinstance(value_in,str):
		valid_image_extensions = ['.png','.jpg','.jpeg','.gif','.tiff','.tif','.bmp','.ico','.pcx','.webp','.tga'] #https://kodi.wiki/view/Features_and_supported_formats
		if 'http' in value_in.lower():
			value_out = value_in
			if 'imgur.com' in value_in.lower():
				value_out = value_in.split('/')[-1]
			if any([x in value_out.lower() for x in valid_image_extensions]):
				return value_out
		elif 'special:' in value_in.lower() and check_if_file_exists(value_in) and any([x in value_in.lower() for x in valid_image_extensions]):
			return value_in
		else:
			xbmc.log(msg='IAGL:  The entry for a new art asset does not appear to be a valid web or local image file', level=xbmc.LOGERROR)
			return None
	else:
		return None

def choose_trailer(*args):
	vid = next(iter([x for x in args if x and isinstance(x,str)]), None)
	if vid is not None and 'http' not in vid:
		return 'plugin://plugin.video.youtube/play/?video_id=%(vid)s'%{'vid':vid}
	else:
		return vid

def clean_trailer_entry(value_in):
	if value_in and isinstance(value_in,str):
		valid_video_extensions = ['.mpg','.mp4','.m4v','.mpeg','.m4p','.mov','.avi','.wmv','.webm','.mp2','.mpe','.mpv','.ogg','.qt','.flv','.swf','.avchd']
		if 'youtube' in value_in.lower():
			return value_in.split('=')[-1]
		elif 'special:' in value_in.lower() and check_if_file_exists(value_in) and any([x in value_in.lower() for x in valid_video_extensions]):
			return value_in
		else:
			xbmc.log(msg='IAGL:  The entry for a new trailer asset does not appear to be a valid web or local video file', level=xbmc.LOGERROR)
			return None
	else:
		return None

def get_date(*args,format_in='%d.%m.%Y'):
	ignore_list = ['?','??','???','????','19??','197?','198?','199?','200?','201?','1980?','1990?','1981?','1987?','1996?'] #Known bad dates to speed things up, will try and remove these from the xmls in the future
	date_in = next(iter([x.strip() for x in args if x and isinstance(x,str) and x not in ignore_list]), None)
	if date_in:
		try:
			return date_parser.parse(date_in).strftime(format_in)
		except Exception as exc:
			xbmc.log(msg='IAGL:  Unable to parse date %(date_in)s.  Exception %(exc)s' % {'date_in': date_in, 'exc': exc}, level=xbmc.LOGDEBUG)
			return None
	else:
		return None

def get_xml_header(file_in,default_dir=None):
	header_out = get_calculated_header_values(get_xml_header_path_et_fromstring(file_in),filename_in=file_in,default_dir=default_dir) #Try getting xml header from path (fast)
	# header_out = get_xml_header_path_xmltodict(file_in) #Try getting xml header from path (fast)
	if header_out:
		return header_out
	else:
		return get_calculated_header_values(get_xml_header_xbmcvfs_et_fromstring(str(file_in)),filename_in=file_in,default_dir=default_dir) #If it fails, use xbmcvfs (slower)
		# return get_xml_header_xbmcvfs_xmltodict(str(file_in)) #If it fails, use xbmcvfs (slower)

def get_xml_header_path_et_fromstring(file_in):
	if check_if_file_exists(file_in):
		with file_in.open(mode='rb') as f:
			byte_string = f.read(HEADER_SIZE)
		if b'</header>' in byte_string:
			try:
				xml_etree = ET.fromstring(byte_string.split(b'</header>')[0]+b'</header></datafile>')
				return dict(zip([y.tag for y in [list(x) for x in xml_etree.iter('header')][0]],[y.text for y in [list(x) for x in xml_etree.iter('header')][0]]))
				# return etree_to_dict(ET.fromstring(byte_string.split(b'</header>')[0]+b'</header></datafile>')).get('datafile').get('header')
			except Exception as exc:
				xbmc.log(msg='IAGL:  Error reading header for %(value_in)s.  Exception %(exc)s' % {'value_in': file_in.name, 'exc': exc}, level=xbmc.LOGERROR)
				return None
		else:
			xbmc.log(msg='IAGL:  End of header not found for %(value_in)s' % {'value_in': file_in.name, 'exc': exc}, level=xbmc.LOGERROR)
			return None
	else:
		xbmc.log(msg='IAGL:  Error xml file %(value_in)s does not exist' % {'value_in': file_in.name}, level=xbmc.LOGERROR)
		return None

def get_calculated_header_values(dict_in,filename_in=None,default_dir=None):
	dict_in['download_source'] = 'Unknown'
	dict_in['emu_downloadpath_resolved'] = default_dir
	dict_in['download_destination'] = 'Cache'
	if filename_in:
		dict_in['game_list_id'] = os.path.splitext(os.path.split(filename_in)[-1])[0]
	else:
		dict_in['game_list_id'] = None
	if all([x in dict_in.get('emu_baseurl') for x in ['http','archive.org']]):
		dict_in['download_source'] = 'Archive.org'
	elif any([x in dict_in.get('emu_baseurl') for x in ['http:','https:']]):
		dict_in['download_source'] = dict_in.get('emu_baseurl')
	elif any([x in dict_in.get('emu_baseurl') for x in ['smb:','nfs:']]):
		dict_in['download_source'] = 'Local Network Source'
	elif any([x in dict_in.get('emu_baseurl') for x in ['special:','library:']]):
		dict_in['download_source'] = 'Kodi Library Source'
	elif Path(dict_in.get('emu_baseurl')).exists():
		dict_in['download_source'] = 'Local File Source'
	if dict_in.get('emu_downloadpath') != 'default' and check_if_dir_exists(Path(dict_in.get('emu_downloadpath'))):
		dict_in['emu_downloadpath_resolved'] = Path(xbmcvfs.translatePath(dict_in.get('emu_downloadpath'))).expanduser()
		dict_in['download_destination'] = 'Local File Destination'
	elif dict_in.get('emu_downloadpath') != 'default' and check_if_dir_exists(str(dict_in.get('emu_downloadpath'))):
		dict_in['emu_downloadpath_resolved'] = xbmcvfs.translatePath(dict_in.get('emu_downloadpath'))
		dict_in['download_destination'] = 'Kodi Library Destination'
	return dict_in

# def get_xml_header_path_xmltodict(file_in):
# 	if file_in.exists():
# 		with file_in.open(mode='rb') as f:
# 			byte_string = f.read(HEADER_SIZE)
# 		if b'</header>' in byte_string:
# 			try:
# 				return xmltodict.parse(byte_string.split(b'</header>')[0]+b'</header></datafile>').get('datafile').get('header')
# 			except Exception as exc:
# 				xbmc.log(msg='IAGL:  Error reading header for %(value_in)s.  Exception %(exc)s' % {'value_in': file_in.name, 'exc': exc}, level=xbmc.LOGERROR)
# 				return None
# 		else:
# 			xbmc.log(msg='IAGL:  End of header not found for %(value_in)s' % {'value_in': file_in.name, 'exc': exc}, level=xbmc.LOGERROR)
# 			return None
# 	else:
# 		xbmc.log(msg='IAGL:  Error xml file %(value_in)s does not exist' % {'value_in': file_in.name}, level=xbmc.LOGERROR)
# 		return None

def get_xml_header_xbmcvfs_et_fromstring(file_in):
	if check_if_file_exists(file_in):
		with xbmcvfs.File(str(file_in)) as fi:
			byte_string = bytes(fi.readBytes(HEADER_SIZE))
		if b'</header>' in byte_string:
			try:
				xml_etree = ET.fromstring(byte_string.split(b'</header>')[0]+b'</header></datafile>')
				return dict(zip([y.tag for y in [list(x) for x in xml_etree.iter('header')][0]],[y.text for y in [list(x) for x in xml_etree.iter('header')][0]]))
				# return etree_to_dict(ET.fromstring(byte_string.split(b'</header>')[0]+b'</header></datafile>')).get('datafile').get('header')
			except Exception as exc:
				xbmc.log(msg='IAGL:  Error reading header for %(value_in)s.  Exception %(exc)s' % {'value_in': file_in, 'exc': exc}, level=xbmc.LOGERROR)
				return None
		else:
			xbmc.log(msg='IAGL:  End of header not found for %(value_in)s' % {'value_in': file_in, 'exc': exc}, level=xbmc.LOGERROR)
			return None
	else:
		xbmc.log(msg='IAGL:  Error xml file %(value_in)s does not exist' % {'value_in': file_in}, level=xbmc.LOGERROR)
		return None

# def get_xml_header_xbmcvfs_xmltodict(file_in):
# 	if xbmcvfs.exists(file_in):
# 		with xbmcvfs.File(file_in) as fi:
# 			byte_string = bytes(fi.readBytes(HEADER_SIZE))
# 		if b'</header>' in byte_string:
# 			try:
# 				return xmltodict.parse(byte_string.split(b'</header>')[0]+b'</header></datafile>').get('datafile').get('header')
# 			except Exception as exc:
# 				xbmc.log(msg='IAGL:  Error reading header for %(value_in)s.  Exception %(exc)s' % {'value_in': file_in, 'exc': exc}, level=xbmc.LOGERROR)
# 				return None
# 		else:
# 			xbmc.log(msg='IAGL:  End of header not found for %(value_in)s' % {'value_in': file_in, 'exc': exc}, level=xbmc.LOGERROR)
# 			return None
# 	else:
# 		xbmc.log(msg='IAGL:  Error xml file %(value_in)s does not exist' % {'value_in': file_in}, level=xbmc.LOGERROR)
# 		return None

def dict_to_xml_header(dict_in):
	xml_header_out = '<?xml version="1.0" encoding="UTF-8"?>\n<datafile>\n\t<header>\n\t\t<emu_name>%(emu_name)s</emu_name>\n\t\t<emu_description>%(emu_description)s</emu_description>\n\t\t<emu_category>%(emu_category)s</emu_category>\n\t\t<emu_version>%(emu_version)s</emu_version>\n\t\t<emu_date>%(emu_date)s</emu_date>\n\t\t<emu_author>%(emu_author)s</emu_author>\n\t\t<emu_visibility>%(emu_visibility)s</emu_visibility>\n\t\t<emu_homepage>%(emu_homepage)s</emu_homepage>\n\t\t<emu_baseurl>%(emu_baseurl)s</emu_baseurl>\n\t\t<emu_launcher>%(emu_launcher)s</emu_launcher>\n\t\t<emu_default_addon>%(emu_default_addon)s</emu_default_addon>\n\t\t<emu_ext_launch_cmd>%(emu_ext_launch_cmd)s</emu_ext_launch_cmd>\n\t\t<emu_downloadpath>%(emu_downloadpath)s</emu_downloadpath>\n\t\t<emu_postdlaction>%(emu_postdlaction)s</emu_postdlaction>\n\t\t<emu_comment>%(emu_comment)s</emu_comment>\n\t\t<emu_thumb>%(emu_thumb)s</emu_thumb>\n\t\t<emu_banner>%(emu_banner)s</emu_banner>\n\t\t<emu_fanart>%(emu_fanart)s</emu_fanart>\n\t\t<emu_logo>%(emu_logo)s</emu_logo>\n\t\t<emu_trailer>%(emu_trailer)s</emu_trailer>\n\t</header>'%{'emu_name':dict_in.get('emu_name'),'emu_description':dict_in.get('emu_description'),'emu_category':dict_in.get('emu_category'),'emu_version':dict_in.get('emu_version'),'emu_date':dict_in.get('emu_date'),'emu_author':dict_in.get('emu_author'),'emu_visibility':dict_in.get('emu_visibility'),'emu_homepage':dict_in.get('emu_homepage'),'emu_baseurl':dict_in.get('emu_baseurl'),'emu_launcher':dict_in.get('emu_launcher'),'emu_default_addon':dict_in.get('emu_default_addon'),'emu_ext_launch_cmd':dict_in.get('emu_ext_launch_cmd'),'emu_downloadpath':dict_in.get('emu_downloadpath'),'emu_postdlaction':dict_in.get('emu_postdlaction'),'emu_comment':dict_in.get('emu_comment'),'emu_thumb':dict_in.get('emu_thumb'),'emu_banner':dict_in.get('emu_banner'),'emu_fanart':dict_in.get('emu_fanart'),'emu_logo':dict_in.get('emu_logo'),'emu_trailer':dict_in.get('emu_trailer')}
	# if '%' in xml_header_out:
	if re.findall('\%\(.*?\)s',xml_header_out):
		xbmc.log(msg='IAGL:  The xml header was not well formed.  Current value %(value_in)s' % {'value_in': xml_header_out}, level=xbmc.LOGERROR)
		xml_header_out = None
	return xml_header_out

def update_xml_file(file_in,dict_in):
	success = False
	if file_in.is_file() and isinstance(dict_in,dict):
		new_file_text = '%(new_header)s%(file_data)s'%{'new_header':dict_to_xml_header(dict_in),'file_data':file_in.read_text(encoding=TEXT_ENCODING).split('</header>')[-1]}
		if all([x in new_file_text for x in ['<datafile>','<header>','</header>','</datafile>']]): #Verify all the required keys are in the file
			try:
				file_in.write_text(new_file_text,encoding=TEXT_ENCODING)
				success = True
			except Exception as exc:
				xbmc.log(msg='IAGL:  Error writing xml file %(value_in)s.  Exception %(exc)s' % {'value_in': file_in, 'exc': exc}, level=xbmc.LOGERROR)
		else:
			xbmc.log(msg='IAGL:  The xml file cannot be written because is was not well formed.  Current file %(file_in)s' % {'file_in': file_in}, level=xbmc.LOGERROR)
	else:
		xbmc.log(msg='IAGL:  The xml edit request was not well formed.  Current file %(file_in)s' % {'file_in': file_in}, level=xbmc.LOGERROR)
	return success

def get_ra_cmds(default_cmd,ra_cfg_path,ra_app_path):
	if isinstance(default_cmd,list) and len(default_cmd)==1 and check_if_file_exists(ra_cfg_path) and check_if_file_exists(ra_app_path):
		ra_cores = dict()
		ra_cfg = get_ra_libretro_config(ra_cfg_path,ra_app_path)
		if ra_cfg.get('libretro_directory') and ra_cfg.get('libretro_info_path'):
			xbmc.log(msg='IAGL:  The libretro directory is identified as %(libretro_directory)s and the core info path is %(libretro_info_path)s' % {'libretro_directory':ra_cfg.get('libretro_directory'),'libretro_info_path': ra_cfg.get('libretro_info_path')}, level=xbmc.LOGDEBUG)
			ra_cores['cores'] = sorted([x for x in ra_cfg.get('libretro_directory').glob('**/*') if x.is_file() and x.suffix in ['.dylib','.dll','.so']])
			info_files = [y for y in ra_cfg.get('libretro_info_path').glob('*.info') if y.is_file()]
			ra_cores['name'] = ['RetroArch %(core_name)s'%{'core_name':x[0].get('display_name')} if x[0].get('display_name') else 'RetroArch %(core_name)s'%{'core_name':x[1].stem} for x in zip([get_ra_info(x.stem,info_files) for x in ra_cores.get('cores')],ra_cores['cores'])]
			return [define_ra_cmd(x[0],x[1],default_cmd[0].copy(),ra_app_path) for x in zip(ra_cores['name'],ra_cores['cores'])]
		else:
			xbmc.log(msg='IAGL:  The libretro directory and info file path parameters are not present in the config file %(file_in)s' % {'file_in': ra_cfg_path}, level=xbmc.LOGERROR)
			return None
	else:
		return None

def get_game_list_stats(games):
	stats_out = dict()
	if games:
		stats_out['alphabetical'] = dict()
		stats_out['genres'] = dict()
		stats_out['years'] = dict()
		stats_out['players'] = dict()
		stats_out['studio'] = dict()
		stats_out['tag'] = dict()
		stats_out['groups'] = dict()
		stats_out['alphabetical']['all'] = ['#']+[chr(x) for x in range(ord('A'), ord('Z') + 1)]
		stats_out['genres']['all'] = sorted(set(flatten_list([x.get('info').get('genre') for x in games if x.get('info').get('genre')])))
		stats_out['years']['all'] = sorted(set([x.get('info').get('year') for x in games if x.get('info').get('year')]))
		stats_out['players']['all'] = sorted(set([x.get('properties').get('nplayers') for x in games if x.get('properties').get('nplayers')]))
		stats_out['studio']['all'] = sorted(set([x.get('info').get('studio') for x in games if x.get('info').get('studio')]))
		stats_out['tag']['all'] = sorted(set(flatten_list([x.get('info').get('tag') for x in games if x.get('info').get('tag')])))
		stats_out['groups']['all'] = sorted(set(flatten_list([x.get('info').get('showlink') for x in games if x.get('info').get('showlink')])))
		if stats_out['alphabetical']['all']:
			stats_out['alphabetical']['count'] = [sum([y.get('values').get('label').upper().startswith(x) for y in games]) for x in stats_out['alphabetical']['all']]
			stats_out['alphabetical']['count'][0] = sum([not y.get('values').get('label')[0].isalpha() for y in games]) #Recalc the numerical stats
			#Remove 0 count alphabetical
			stats_out['alphabetical']['all'] = [x[0] for x in zip(stats_out['alphabetical']['all'],stats_out['alphabetical']['count']) if x[1]>0]
			stats_out['alphabetical']['count'] = [x for x in stats_out['alphabetical']['count'] if x>0]
		if stats_out['genres']['all']:
			stats_out['genres']['count'] = [sum([x in y.get('info').get('genre') if y.get('info').get('genre') else False for y in games]) for x in stats_out['genres']['all']]
		if stats_out['years']['all']:
			stats_out['years']['count'] = [sum([x in y.get('info').get('year') if y.get('info').get('year') else False for y in games]) for x in stats_out['years']['all']]
		if stats_out['players']['all']:
			stats_out['players']['count'] = [sum([x in y.get('properties').get('nplayers') if y.get('properties').get('nplayers') else False for y in games]) for x in stats_out['players']['all']]
		if stats_out['studio']['all']:
			stats_out['studio']['count'] = [sum([x in y.get('info').get('studio') if y.get('info').get('studio') else False for y in games]) for x in stats_out['studio']['all']]
		if stats_out['tag']['all']:
			stats_out['tag']['count'] = [sum([x in y.get('info').get('tag') if y.get('info').get('tag') else False for y in games]) for x in stats_out['tag']['all']]
		if stats_out['groups']['all']:
			stats_out['groups']['count'] = [sum([x in y.get('info').get('showlink') if y.get('info').get('showlink') else False for y in games]) for x in stats_out['groups']['all']]
		#Add uncategorized / unset counts
		unknowns = dict()
		unknowns['genres'] = sum([not y.get('info').get('genre') for y in games]) #Uncategorized, unset count
		unknowns['years'] = sum([not y.get('info').get('year') for y in games]) #Uncategorized, unset count
		unknowns['players'] = sum([not y.get('properties').get('nplayers') for y in games]) #Uncategorized, unset count
		unknowns['studio'] = sum([not y.get('info').get('studio') for y in games]) #Uncategorized, unset count
		unknowns['tag'] = sum([not y.get('info').get('tag') for y in games]) #Uncategorized, unset count
		unknowns['groups'] = sum([not y.get('info').get('showlink') for y in games]) #Uncategorized, unset count
		for kk in ['genres','years','players','studio','tag','groups']:
			if unknowns[kk]>0:
				if stats_out[kk].get('all'):
					stats_out[kk]['all'].append('Unknown')
					stats_out[kk]['count'].append(unknowns[kk])
				else:
					stats_out[kk]['all'] = ['Unknown']
					stats_out[kk]['count'] = [unknowns[kk]]
		#Add overall stats, totals for each grouping and total games in the list
		stats_out['overall'] = dict()
		stats_out['overall']['count'] = len(games)
		stats_out['overall']['alphabetical'] = 0
		stats_out['overall']['genres'] = 0
		stats_out['overall']['years'] = 0
		stats_out['overall']['players'] = 0
		stats_out['overall']['studio'] = 0
		stats_out['overall']['tag'] = 0
		stats_out['overall']['groups'] = 0
		if stats_out['alphabetical'].get('all'):
			stats_out['overall']['alphabetical'] = len(stats_out['alphabetical']['all'])
		if stats_out['genres'].get('all'):
			stats_out['overall']['genres'] = len(stats_out['genres']['all'])
		if stats_out['years'].get('all'):
			stats_out['overall']['years'] = len(stats_out['years']['all'])
		if stats_out['players'].get('all'):
			stats_out['overall']['players'] = len(stats_out['players']['all'])
		if stats_out['studio'].get('all'):
			stats_out['overall']['studio'] = len(stats_out['studio']['all'])
		if stats_out['tag'].get('all'):
			stats_out['overall']['tag'] = len(stats_out['tag']['all'])
		if stats_out['groups'].get('all'):
			stats_out['overall']['groups'] = len(stats_out['groups']['all'])
	return stats_out

def add_game_to_history(dict_in,file_in,max_history):
	success = False
	if isinstance(dict_in,dict):
		dict_in['info']['lastplayed'] = time.strftime('%Y-%m-%d %H:%M:%S') #lastplayed	string (Y-m-d h:m:s = 2009-04-05 23:16:04)
		if check_if_file_exists(file_in):
			with xbmcvfs.File(str(file_in),'rb') as fi:
				history = json.load(fi)
			prev_history = [x for x in history[0] if not (x.get('values').get('label2') == dict_in.get('values').get('label2') and x.get('properties').get('route') == dict_in.get('properties').get('route'))]
			if len(prev_history) == len(history[0]): #Game was not previously in history
				with xbmcvfs.File(str(file_in),'wb') as fi:
					json.dump([[x for x in [dict_in]+history[0]][0:max_history],get_game_list_stats([x for x in [dict_in]+history[0]][0:max_history])],fi)
					# [games_in,stats_in]
					xbmc.log(msg='IAGL:  Added %(game)s to history file' % {'game': dict_in.get('info').get('originaltitle')}, level=xbmc.LOGDEBUG)
				with xbmcvfs.File(str(file_in).replace('.json','_stats.json'),'wb') as fi:
					json.dump(get_game_list_stats([x for x in [dict_in]+history[0]][0:max_history]),fi)
					success = True
			else: #Game was already in history, so remove old instance and replace it with new instance
				with xbmcvfs.File(str(file_in),'wb') as fi:
					json.dump([[x for x in [dict_in]+prev_history][0:max_history],get_game_list_stats([x for x in [dict_in]+prev_history][0:max_history])],fi)
					xbmc.log(msg='IAGL:  Updated %(game)s to last played game in history file' % {'game': dict_in.get('info').get('originaltitle')}, level=xbmc.LOGDEBUG)
				with xbmcvfs.File(str(file_in).replace('.json','_stats.json'),'wb') as fi:
					json.dump(get_game_list_stats([x for x in [dict_in]+prev_history][0:max_history]),fi)
					success = True
		else:
			with xbmcvfs.File(str(file_in),'wb') as fi:
				json.dump([[dict_in],get_game_list_stats([dict_in])],fi)
				xbmc.log(msg='IAGL:  Added %(game)s to new history file' % {'game': dict_in.get('info').get('originaltitle')}, level=xbmc.LOGDEBUG)
			with xbmcvfs.File(str(file_in).replace('.json','_stats.json'),'wb') as fi:
				json.dump(get_game_list_stats([dict_in]),fi)
				success = True
	return success

def define_ra_cmd(core_name,core_path,default_dict,ra_app_path):
	default_dict['@name'] = core_name
	default_dict['command'] = default_dict.get('command').replace("%APP_PATH_RA%",str(ra_app_path)).replace('%CORE_PATH%',str(core_path))
	return default_dict

def get_ra_info(core_in,ra_info_files):
	dict_out = dict()
	if core_in and ra_info_files:
		current_info = [x for x in ra_info_files if x.stem == core_in]
		if current_info:
			info_dict = get_ra_cfg_info_file(current_info[0])
			if info_dict:
				dict_out = info_dict
			else:
				xbmc.log(msg='IAGL:  No info could be found for the RA core %(file_in)s' % {'file_in': core_in}, level=xbmc.LOGDEBUG)
		else:
			xbmc.log(msg='IAGL:  No info could be found for the RA core %(file_in)s' % {'file_in': core_in}, level=xbmc.LOGDEBUG)
	return dict_out

def get_ra_libretro_config(ra_cfg_path,ra_app_path):
	ra_cfg = get_ra_cfg_info_file(ra_cfg_path)
	if ra_cfg:
		dict_out = dict()
		for kk in ['libretro_directory','libretro_info_path']:
			current_value = ra_cfg.get(kk)
			if current_value:
				if current_value.startswith(':'):
					current_app_path = ra_app_path.parent
					if str(current_app_path).endswith('MacOS'): #Special case for OSX
						current_app_path = ra_app_path.parents[2]
					dict_out[kk] = Path(current_app_path).joinpath(ra_cfg.get(kk).replace(':/','').replace(':\\','')).expanduser()
				else:
					dict_out[kk] = Path(xbmcvfs.translatePath(ra_cfg.get(kk))).expanduser()
			else:
				dict_out[kk] = None
		return dict_out
	else:
		return dict()

def get_ra_cfg_info_file(ra_path):
	if check_if_file_exists(ra_path):
		byte_string = None
		with xbmcvfs.File(str(ra_path)) as fi:
			byte_string = bytes(fi.readBytes())
		if byte_string:
			return {x[0].strip():x[-1].strip() for x in [l.split('=') for l in [p.replace('"','') for p in byte_string.decode(TEXT_ENCODING).replace('\r','\n').replace('\n\n','\n').split('\n')] if l and '=' in l] if isinstance(x,list) and len(x)==2}
		else:
			xbmc.log(msg='IAGL:  Error Retroarch cfg/info file %(value_in)s was empty' % {'value_in': file_in}, level=xbmc.LOGERROR)
			return None
	else:
		xbmc.log(msg='IAGL:  Error Retroarch cfg/info file %(value_in)s does not exist' % {'value_in': file_in}, level=xbmc.LOGERROR)
		return None

def loc_str(string_id_in):
	try:
		return ADDON_HANDLE.getLocalizedString(string_id_in)
	except:
		xbmc.log(msg='IAGL:  No translation available for %(string_id_in)s' % {'string_id_in': string_id_in}, level=xbmc.LOGERROR)
		return ''

def check_addondata_to_query(addon_files,userdata_files):
	query_out = list()
	for af in [x for x in zip(addon_files.get('files'),addon_files.get('header')) if x[0].name in [y.name for y in userdata_files.get('files')]]:
		if af[1].get('emu_version') != userdata_files.get('header')[[y.name for y in userdata_files.get('files')].index(af[0].name)].get('emu_version'):
			query_out.append((af[0],af[1].get('emu_name'),af[1].get('emu_version'),userdata_files.get('header')[[y.name for y in userdata_files.get('files')].index(af[0].name)].get('emu_version')))
			#file,name,new version,old version
		else:
			delete_file(af[0]) #The file already exists and is of the same version, so delete it
	return query_out

def get_game_download_dict(emu_baseurl=None,emu_downloadpath=None,emu_dl_source=None,emu_post_processor=None,emu_launcher=None,emu_default_addon=None,emu_ext_launch_cmd=None,game_url=None,game_downloadpath=None,game_post_processor=None,game_launcher=None,game_default_addon=None,game_ext_launch_cmd=None,game_emu_command=None,organize_default_dir=False,default_dir=None,emu_name=None):
	game_dl_dict = dict()
	if emu_dl_source and emu_baseurl and game_url and (emu_dl_source in ['Archive.org','Local Network Source','Kodi Library Source','Local File Source'] or 'http' in emu_dl_source):
		game_filename = url_unquote(game_url.split('/')[-1].split('%2F')[-1])
		game_dl_dict = {'dl_source':emu_dl_source,
					'baseurl':emu_baseurl,
					'url':game_url,
					'downloadpath':next(iter([x for x in [game_downloadpath,emu_downloadpath] if x]),'default'),
					'url_resolved':os.path.join(emu_baseurl,game_url.strip(os.sep).strip('/')),
					'filename':game_filename,
					'filename_no_ext':game_filename.split('.')[0],
					'filename_ext':game_filename.split('.')[-1].lower(),
					'post_processor':next(iter([x for x in [game_post_processor,emu_post_processor] if x]),'none'),
					'launcher':next(iter([x for x in [game_launcher,emu_launcher] if x]),'retroplayer'),
					'default_addon':next(iter([x for x in [game_default_addon,emu_default_addon] if x]),'none'),
					'ext_launch_cmd':next(iter([x for x in [game_ext_launch_cmd,emu_ext_launch_cmd] if x]),'none'),
					'emu_command':game_emu_command,
					'downloadpath_resolved':Path(emu_downloadpath).joinpath(game_filename).expanduser(),
					}
		if organize_default_dir and game_dl_dict.get('downloadpath') == 'default' or str(game_dl_dict.get('downloadpath')) == str(default_dir) and emu_name:
			new_default_dir = check_userdata_directory(os.path.join(str(default_dir),emu_name))
			if new_default_dir:
				game_dl_dict['downloadpath'] = str(new_default_dir)
				game_dl_dict['downloadpath_resolved'] = Path(game_dl_dict.get('downloadpath')).joinpath(game_filename).expanduser()
		if emu_post_processor in ['launch_mame_softlist_cdimono1']: #Download to a specific folder depending on the post process command
			post_process_dir = dict(zip(['launch_mame_softlist_cdimono1'],['cdimono1']))
			game_dl_dict['downloadpath_resolved'] = Path(game_dl_dict.get('downloadpath_resolved').parent).joinpath(post_process_dir.get(emu_post_processor),game_dl_dict.get('downloadpath_resolved').name).expanduser()
			check_userdata_directory(game_dl_dict.get('downloadpath_resolved').parent)
		if game_dl_dict.get('downloadpath_resolved').parent.exists():
			if game_dl_dict.get('filename_ext') not in ARCHIVE_FILETYPES: #If file to be downloaded is not an archive, it should match exactly with a local file - currenly works because all post processed filetypes are archives.  This may have to be updated in the future
				if check_if_file_exists(game_dl_dict.get('downloadpath_resolved')):
					game_dl_dict['matching_existing_files'] = [game_dl_dict.get('downloadpath_resolved')]
				else:
					game_dl_dict['matching_existing_files'] = []
			else: #If the file to be downloaded is an archive, the name without extension should match with a local file
				game_dl_dict['matching_existing_files'] = [x for x in game_dl_dict.get('downloadpath_resolved').parent.glob('**/'+glob.escape(game_dl_dict.get('downloadpath_resolved').stem)+'*') if x.suffix.lower() not in IGNORE_THESE_FILETYPES and x.name.lower() not in IGNORE_THESE_FILES]
		elif xbmcvfs.exists(str(game_dl_dict.get('downloadpath'))): #Kodi network source save spot (like smb address) need to use xbmcvfs to check local files
			if game_dl_dict.get('filename_ext') not in ARCHIVE_FILETYPES:
				if check_if_file_exists(str(game_dl_dict.get('downloadpath_resolved'))):
					game_dl_dict['matching_existing_files'] = [str(game_dl_dict.get('downloadpath_resolved'))]
				else:
					game_dl_dict['matching_existing_files'] = []
			else:
				game_dl_dict['matching_existing_files'] = [x for x in get_all_files_in_directory_xbmcvfs(str(game_dl_dict.get('downloadpath'))) if os.path.split(os.path.splitext(x)[0])[-1] == game_dl_dict.get('filename_no_ext') and os.path.splitext(x)[-1].lower() not in IGNORE_THESE_FILETYPES and os.path.split(os.path.splitext(x)[0])[-1] not in IGNORE_THESE_FILES]
		else:
			game_dl_dict['matching_existing_files'] = []
		if game_dl_dict.get('emu_command'):
			game_dl_dict['matching_existing_files'] = list(set(game_dl_dict.get('matching_existing_files')+[x for x in game_dl_dict.get('downloadpath_resolved').parent.glob('**/'+glob.escape(game_dl_dict.get('emu_command'))+'*') if x.suffix.lower() not in IGNORE_THESE_FILETYPES and x.name.lower() not in IGNORE_THESE_FILES]))
		if game_dl_dict.get('dl_source') in ['Archive.org']:
			game_dl_dict['downloader'] = 'archive_org'
		elif 'http' in game_dl_dict.get('dl_source'):
			game_dl_dict['downloader'] = 'generic'
		elif game_dl_dict.get('dl_source') in ['Local Network Source','Kodi Library Source','Local File Source']:
			game_dl_dict['downloader'] = 'local_source'
		else:
			game_dl_dict['downloader'] = None
	return game_dl_dict


def dict_to_game_xml(game=None):
	xml_out = None
	if isinstance(game,dict) and game.get('values') and game.get('info'):
		dict_out_keys = ['@name','plot','releasedate','year','studio','genre','rating','ESRB','videoid','description','route','nplayers','perspective']+['boxart%(nn)s'%{'nn':x} for x in range(1,11)]+['snapshot%(nn)s'%{'nn':x} for x in range(1,11)]+['banner%(nn)s'%{'nn':x} for x in range(1,11)]+['fanart%(nn)s'%{'nn':x} for x in range(1,11)]+['clearlogo%(nn)s'%{'nn':x} for x in range(1,11)]
		dict_out = {'game': dict(zip(dict_out_keys,[None for x in dict_out_keys]))}
		dict_out_mapping = dict()
		dict_out_mapping['values'] = dict(zip(['@name'],['label2']))
		dict_out_mapping['info'] = dict(zip(['plot','releasedate','year','studio','genre','rating','ESRB','videoid'],['plot','date','year','studio','genre','rating','mpaa','trailer']))
		dict_out_mapping['properties'] = dict(zip(['description','route','nplayers','perspective'],['description','route','nplayers','perspective']))
		dict_out_art_mapping = dict(zip(['game_boxarts','game_banners','game_snapshots','game_logos','game_fanarts'],['boxart','banner','snapshot','clearlogo','fanart']))
		for kk in dict_out_mapping.keys():
			for k,v in dict_out_mapping.get(kk).items():
				if isinstance(game.get(kk).get(v),str):
					if k in ['@name']:
						dict_out['game'][k] = url_unquote(game.get(kk).get(v))
					else:
						dict_out['game'][k] = game.get(kk).get(v)
				elif isinstance(game.get(kk).get(v),list):
					dict_out['game'][k] = ','.join(game.get(kk).get(v))
		if dict_out.get('game').get('videoid'):
			dict_out['game']['videoid'] = dict_out.get('game').get('videoid').split('=')[-1]
		for k,v in dict_out_art_mapping.items():
			if game.get('properties') and isinstance(game.get('properties').get(k),str):
				for ii,art in enumerate(json.loads(game.get('properties').get(k))):
					dict_out['game']['%(type)s%(nn)s'%{'type':v,'nn':ii+1}] = art
		for kk in dict_out_keys:
			if not dict_out.get('game').get(kk):
				dict_out['game'].pop(kk, None)
		try:
			xml_out = xmltodict.unparse(dict_out, pretty=True).replace('<?xml version="1.0" encoding="utf-8"?>\n','')
		except Exception as exc:
			xbmc.log(msg='IAGL:  Error generating favorites xml.  Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
	return xml_out

def add_game_to_favorites(filename_in=None,game=None):
	success = False
	if isinstance(game,dict) and check_if_file_exists(filename_in):
		xml_out = dict_to_game_xml(game=game)+'\n</datafile>'
		if isinstance(xml_out,str) and '<game ' in xml_out and '</game>' in xml_out:
			success = write_text_to_file(filename_in.read_text(encoding=TEXT_ENCODING).replace('</datafile>',xml_out),filename_in)
	return success

def bytes_to_string_size(value, format='%.1f'):
	if isinstance(value,int) or isinstance(value,float): # or (isinstance(num,str) and num.isdigit())
		suffix = ('kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')
		base = 1024
		value_bytes = float(value)
		if abs(value_bytes) < base:
			return '%d Bytes' % value_bytes
		for i, s in enumerate(suffix):
			unit = base ** (i + 2)
			if abs(value_bytes) < unit:
				return (format + ' %s') % ((base * value_bytes / unit), s)
		return (format + ' %s') % ((base * value_bytes / unit), s)
	else:
		return None

# def get_all_files_in_directory_xbmcvfs(directory_in,current_files=None):
# 	dirs_in_dir, files_in_dir = xbmcvfs.listdir(os.path.join(directory_in,''))
# 	if isinstance(current_files,list):
# 		current_files = current_files+[os.path.join(directory_in,ff) for ff in files_in_dir if ff]
# 	else:
# 		current_files = [os.path.join(directory_in,ff) for ff in files_in_dir if ff]
# 	for dd in dirs_in_dir:
# 		current_files = get_all_files_in_directory_xbmcvfs(os.path.join(directory_in,dd,''),current_files)
# 	return current_files

def generate_pointer_file(filename_in=None,pointer_file_type=None,pointer_contents=None,directory=None,default_dir=None):
	filename_out = None
	if filename_in and pointer_file_type:
		if directory:
			filename_out = os.path.join(directory,filename_in.stem+pointer_file_type)
		else:
			filename_out = os.path.join(str(default_dir),filename_in.stem+pointer_file_type)
		if not pointer_contents:
			pointer_contents = ''
		if write_text_to_file(text_in=pointer_contents,filename_in=filename_out):
			return filename_out
		else:
			return None

def get_all_files_in_directory_xbmcvfs(directory_in):
	directory_in = directory_in
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

def clean_file_folder_name(text_in):
	text_out = text_in
	if isinstance(text_in,str):
		text_out = re.sub(' +',' ',''.join(c for c in url_unquote(text_out) if c.isalnum() or c in [' ','_']).rstrip())
		text_out = re.sub('dis[ck] [0-9]+','',text_out,flags=re.I)
		text_out = re.sub(' +','_',text_out)
	return text_out

def check_and_close_notification(notification_id=None):
	if not notification_id:
		notification_id = 'notification'
	is_closed = False
	for ii in range(4):
		if xbmc.getCondVisibility('Window.IsActive(%(notification_id)s)'%{'notification_id':notification_id}):
			xbmc.executebuiltin('Dialog.Close(%(notification_id)s,true)'%{'notification_id':notification_id})
			xbmc.sleep(NOTIFICATION_DEINIT_TIME)
			if not xbmc.getCondVisibility('Window.IsActive(%(notification_id)s)'%{'notification_id':notification_id}):	
				is_closed=True
				break
		else:
			is_closed=True
			break
		if ii==3:
			xbmc.log(msg='IAGL:  Unable to close the notification window', level=xbmc.LOGERROR)
	return is_closed

def enqueue_output(out, queue):
	for line in iter(out.readline, b''):
		queue.put(line)
	out.close()
	
def get_crc32_from_string(string_in):
	if isinstance(string_in,str):
		return format(zlib.crc32(string_in) & 0xFFFFFFFF,'X')
	else:
		return None

def get_crc32(filename):
	crc_out = zlib_csum(filename, zlib.crc32) #First try zlib using posixpath (fast)
	if crc_out:
		return crc_out
	else:
		return zlib_csum_xbmcvfs(str(filename), zlib.crc32) #If it fails try xbmcvfs (slower)


def write_text_to_file(text_in,filename_in):
	success = False
	if filename_in and Path(filename_in):
		try:
			Path(filename_in).write_text(text_in,encoding=TEXT_ENCODING)
			success = True
		except Exception as exc:
			xbmc.log(msg='IAGL:  Error writing text file %(value_in)s.  Exception %(exc)s' % {'value_in': file_in, 'exc': exc}, level=xbmc.LOGERROR)
	elif filename_in and check_if_file_exists(filename_in):
		try:
			with xbmcvfs.File(str(filename_in), 'w') as fo:
			    fo.write(bytearray(text_in.encode('utf-8')))
			    success = True
		except:
			xbmc.log(msg='IAGL:  Error writing text file %(value_in)s.  Exception %(exc)s' % {'value_in': file_in, 'exc': exc}, level=xbmc.LOGERROR)

	else:
		success = False
	return success
# def zlib_csum(filename, func):
# 	csum = None
# 	last_read = False
# 	if filename.exists():
# 		with filename.open(mode='rb') as f:
# 			while not last_read:
# 				chunk = f.read(CHUNK_SIZE)
# 				if chunk:
# 					if csum is None:
# 						csum = func(chunk)
# 					else:
# 						csum = func(chunk, csum)
# 				else:
# 					last_read=True
# 					break
# 	if csum:
# 		return format(csum & 0xFFFFFFFF,'X')
# 	else:
# 		return None

def zlib_csum(filename, func):
	csum = None
	if filename.exists():
		with filename.open(mode='rb') as f:
			for chunk in iter((lambda:f.read(CHUNK_SIZE)),None):
				if chunk:
					if csum:
						csum = func(chunk, csum)
					else:
						csum = func(chunk)
				else:
					break
	if csum:
		return format(csum & 0xFFFFFFFF,'X')
	else:
		return None

def zlib_csum_xbmcvfs(filename, func):
	csum = None
	last_read = False
	if check_if_file_exists(filename):
		with xbmcvfs.File(str(filename)) as f:
			while not last_read:
				chunk = f.readBytes(CHUNK_SIZE)
				if chunk:
					if csum is None:
						csum = func(chunk)
					else:
						csum = func(chunk, csum)
				else:
					last_read=True
					break
	if csum:
		return format(csum & 0xFFFFFFFF,'X')
	else:
		return None

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

# def dict_to_etree(d):
# 	def _to_etree(d, root):
# 		if not d:
# 			pass
# 		elif isinstance(d, str):
# 			root.text = d
# 		elif isinstance(d, dict):
# 			for k,v in d.items():
# 				assert isinstance(k, str)
# 				if k.startswith('#'):
# 					assert k == '#text' and isinstance(v, str)
# 					root.text = v
# 				elif k.startswith('@'):
# 					assert isinstance(v, str)
# 					root.set(k[1:], v)
# 				elif isinstance(v, list):
# 					for e in v:
# 						_to_etree(e, ET.SubElement(root, k))
# 				else:
# 					_to_etree(v, ET.SubElement(root, k))
# 		else:
# 			assert d == 'invalid type', (type(d), d)
# 	assert isinstance(d, dict) and len(d) == 1
# 	tag, body = next(iter(d.items()))
# 	node = ET.Element(tag)
# 	_to_etree(body, node)
#     return node