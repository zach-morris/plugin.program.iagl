import os, zlib, json, re, time, glob, requests, uuid
from pathlib import Path
# from kodi_six import xbmc, xbmcvfs, xbmcgui, xbmcaddon
import xbmc, xbmcvfs, xbmcgui, xbmcaddon
from infotagger.listitem import ListItemInfoTag
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
ADDON_PATH = ADDON_HANDLE.getAddonInfo('path')
ADDON_SPECIAL_PATH = 'special://xbmc/addons/plugin.program.iagl/' if xbmcvfs.translatePath('special://xbmc/addons/plugin.program.iagl/') == ADDON_PATH else 'special://home/addons/plugin.program.iagl/'
MEDIA_SPECIAL_PATH = ADDON_SPECIAL_PATH+'resources/skins/Default/media/%(filename)s'
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
IGNORE_THESE_FILETYPES = ['srm','sav','fs','state','auto','xml','nfo','.srm','.sav','.fs','.state','.auto','.xml','.nfo','.msu'] #Matching filetypes to ignore for re-launching
IGNORE_THESE_FILES = ['win31.bat'] #Matching files to ignore for re-launching
ARCHIVE_FILETYPES = ['001','7z','bz2','cbr','gz','iso','rar','tar','tarbz2','targz','tarxz','tbz2','tgz','xz','zip','.001', '.7z', '.bz2', '.cbr', '.gz', '.iso', '.rar', '.tar', '.tarbz2', '.targz', '.tarxz', '.tbz2', '.tgz', '.xz', '.zip']
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
	return dict(zip(['none','unzip_rom','unzip_and_launch_file','unzip_to_folder_and_launch_file','unzip_and_launch_scummvm_file','unzip_and_launch_win31_file','unarchive_neocd_launch_cue','unarchive_game_launch_cue','unzip_and_launch_exodos_file','process_chd_games','move_to_folder_cdimono1','move_to_folder_spectrum','move_to_folder_fmtowns_cd'],['None (Direct File Launch)','UnArchive Game','UnArchive Game, Launch File','UnArchive Game to Folder, Launch File','UnArchive Game, Generate SCUMMVM File','UnArchive Game, Generate WIN31 BAT File','UnArchive Game, Launch NeoCD CUE File','UnArchive Game, Launch CUE File','UnArchive Game, Generate ExoDOS Launch File','Process MAME and MAME CHD Files','Move Files to cdimono1 Folder','Move Files to spectrum Folder','Move Files to fmtowns_cd Folder']))

def get_downloadpath(path=None,default=None):
	if path=='default' or path is None:
		return default
	else:
		return Path(xbmcvfs.translatePath(path))

def zachs_debug(message=None,level_in=xbmc.LOGWARNING):
	if message is not None:
		xbmc.log(msg='*IAGL TEST*:  %(value_in)s' % {'value_in': message}, level=level_in)

def get_launch_parameter(setting_in=None,return_val=None):
	if isinstance(setting_in,str) or isinstance(setting_in,Path):
		return str(setting_in)
	else:
		return return_val

def move_file(file_in=None,path_in=None):
	success = False
	if file_in is not None and path_in is not None:
		if check_if_file_exists(file_in):
			success = xbmcvfs.rename(get_dest_as_str(file_in),os.path.join(path_in,Path(file_in).name))
			if not success: #Per docs note moving files between different filesystem (eg. local to nfs://) is not possible on all platforms. You may have to do it manually by using the copy and deleteFile functions.
				xbmc.log(msg='IAGL:  Unable to move file %(value_in_1)s to %(value_in_2)s, attempting copy / delete'%{'value_in_1':file_in,'value_in_2':path_in}, level=xbmc.LOGDEBUG)
				if xbmcvfs.copy(get_dest_as_str(file_in),os.path.join(path_in,Path(file_in).name)):
					success = xbmcvfs.delete(get_dest_as_str(file_in))
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
		if check_if_file_exists(get_dest_as_str(file_in)):
			if not confirm_delete:
				success = xbmcvfs.delete(get_dest_as_str(file_in))
			else:
				if xbmcgui.Dialog().yesno('Confirm Deletion','Are you sure you want to delete %(file_in)s'%{'file_in':file_in.name},'Cancel','Delete'): #Need to localize this eventually
					success = xbmcvfs.delete(get_dest_as_str(file_in))
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
	if dict_in.get('localization'):
		localized_label = loc_str(int(dict_in.get('localization')))
	else:
		localized_label = dict_in.get('label')
	if game_list_name is None:
		if dict_in.get('plot') and dict_in.get('plot').isdigit():
			plot = loc_str(int(dict_in.get('plot')))
		else:
			plot = dict_in.get('plot')
	else:
		if dict_in.get('plot') and dict_in.get('plot').isdigit():
			plot = '%(label)s for %(game_list_name)s'%{'label':loc_str(int(dict_in.get('plot'))),'game_list_name':game_list_name}
		else:
			plot = '%(label)s for %(game_list_name)s'%{'label':dict_in.get('plot'),'game_list_name':game_list_name}
	if dict_in.get('sort'):
		props = {'SpecialSort':dict_in.get('sort')}
	return {'values': {'label':localized_label,'label2':label2},
			'info':   {'originaltitle':localized_label,'title':localized_label,'plot':plot,'trailer':choose_trailer(dict_in.get('trailer'),default_dict.get('trailer'))},
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
					   'credits':[dict_in.get('emu_author')],
					   'plot':dict_in.get('emu_comment'),
					   'tag':['Launch using %(value_in)s'%{'value_in':dict_in.get('emu_launcher')}],
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

def map_game_listitem_dict(dict_in,parent_dict_in,default_dict,game_list_id,clean_titles,naming_convention,date_convention,type_in=None,include_extra_art=True,boxart_or_snapshot=True):
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
					   'studio':[dict_in.get('studio')],
					   'genre':split_value(dict_in.get('genre')),
					   'showlink':split_value(dict_in.get('groups')),
					   'rating':dict_in.get('rating'),
					   'mpaa':dict_in.get('ESRB'),
					   'plot':dict_in.get('plot'),
					   'tag':get_game_tags(dict_in.get('@name')),
					   'trailer':choose_trailer(dict_in.get('videoid')),
					   # 'path':'plugin://plugin.program.iagl/game/%(game_list_id)s/%(label2)s'%{'game_list_id':game_list_id,'label2':label2},
					   'size':get_game_size(dict_in.get('rom'))},
			'art':    {'poster':choose_image(dict_in.get('boxart1'),dict_in.get('snapshot1'),default_dict.get('thumb')) if boxart_or_snapshot else choose_image(dict_in.get('snapshot1'),dict_in.get('boxart1'),default_dict.get('thumb')),
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
					   'thumb':choose_image(dict_in.get('boxart1'),dict_in.get('snapshot1'),default_dict.get('thumb')) if boxart_or_snapshot else choose_image(dict_in.get('snapshot1'),dict_in.get('boxart1'),default_dict.get('thumb'))},
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
					   'genres':dict_in.get('info').get('genre'),
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
			if dict_in.get('info')[ii]:
				#script.module.infotagger v20
				info_tag = ListItemInfoTag(li,media_type)
				info_tag.set_info(dict_in.get('info')[ii])
				# li.setInfo(media_type,dict_in.get('info')[ii])
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
	li_dict = {'info':{'genre':loc_str(30600),'plot':loc_str(30601)},
	'art':{'icon':MEDIA_SPECIAL_PATH%{'filename':'icon.png'},
	'thumb':MEDIA_SPECIAL_PATH%{'filename':'last_played.jpg'},
	'poster':MEDIA_SPECIAL_PATH%{'filename':'last_played.jpg'},
	'banner':MEDIA_SPECIAL_PATH%{'filename':'last_played_banner.jpg'},
	'fanart':MEDIA_SPECIAL_PATH%{'filename':'fanart.jpg'}}}
	li = xbmcgui.ListItem(label=loc_str(30599),offscreen=True)
	#script.module.infotagger v20
	info_tag = ListItemInfoTag(li,media_type)
	info_tag.set_info(li_dict.get('info'))
	# li.setInfo(media_type,li_dict.get('info'))
	li.setArt(li_dict.get('art'))
	li.setProperties({'SpecialSort':'bottom'})
	return li

def get_next_page_listitem(current_page,page_count,next_page,total_items,media_type='video'):
	li = xbmcgui.ListItem(label=loc_str(30602),offscreen=True)
	#script.module.infotagger v20
	info_tag = ListItemInfoTag(li,media_type)
	info_tag.set_info({'plot':loc_str(30603)%{'current_page':current_page,'page_count':page_count,'next_page':next_page,'total_items':total_items}})
	# li.setInfo(media_type,{'plot':loc_str(30603)%{'current_page':current_page,'page_count':page_count,'next_page':next_page,'total_items':total_items}})
	li.setArt({'icon':MEDIA_SPECIAL_PATH%{'filename':'next.png'},'thumb':MEDIA_SPECIAL_PATH%{'filename':'next.png'}})
	li.setProperties({'SpecialSort':'bottom'})
	return li

def get_blank_favorites_listitem(media_type='video'):
	li = xbmcgui.ListItem(label=loc_str(30439),offscreen=True)
	li.setArt({'icon':MEDIA_SPECIAL_PATH%{'filename':'favorites_logo.png'},
				'thumb':MEDIA_SPECIAL_PATH%{'filename':'favorites.png'},
				'poster':MEDIA_SPECIAL_PATH%{'filename':'favorites.png'},
				'banner':MEDIA_SPECIAL_PATH%{'filename':'favorites_banner.png'},
				'fanart':MEDIA_SPECIAL_PATH%{'filename':'fanart.jpg'}})
	return li


def get_netplay_listitem(media_type='video'):
	li_dict = {'info':{'genre':loc_str(30004),'plot':loc_str(30598)},
	'art':{'icon':MEDIA_SPECIAL_PATH%{'filename':'netplay_logo.png'},
	'thumb':MEDIA_SPECIAL_PATH%{'filename':'netplay_box.jpg'},
	'poster':MEDIA_SPECIAL_PATH%{'filename':'netplay_box.jpg'},
	'banner':MEDIA_SPECIAL_PATH%{'filename':'last_played_banner.jpg'},
	'fanart':MEDIA_SPECIAL_PATH%{'filename':'fanart.jpg'}}}
	li = xbmcgui.ListItem(label=loc_str(30004),offscreen=True)
	#script.module.infotagger v20
	info_tag = ListItemInfoTag(li,media_type)
	info_tag.set_info(li_dict.get('info'))
	# li.setInfo(media_type,li_dict.get('info'))
	li.setArt(li_dict.get('art'))
	li.setProperties({'SpecialSort':'bottom'})
	return li

def get_database_listitem(dict_in,media_type='video'):
	if isinstance(dict_in,dict):
		li = xbmcgui.ListItem(label=dict_in.get('values').get('label'),label2=dict_in.get('values').get('label2'),offscreen=True)
		#script.module.infotagger v20
		info_tag = ListItemInfoTag(li,media_type)
		info_tag.set_info(dict_in.get('info'))
		# li.setInfo(media_type,dict_in.get('info'))
		li.setArt(dict_in.get('art'))
		li.setProperties(dict_in.get('properties'))
		return li
	else:
		return None

def get_game_list_listitem(dict_in,filter_in=None,media_type='video'):
	li=None
	if dict_in.get('properties').get('emu_visibility') != 'hidden' and (filter_in is None or (all([filter_in.get('info').get(kk) in dict_in.get('info').get(kk) if dict_in.get('info').get(kk) else False for kk in filter_in.get('info').keys()]) and all([filter_in.get('properties').get(kk) in dict_in.get('properties').get(kk) if dict_in.get('properties').get(kk) else False for kk in filter_in.get('properties').keys()]))):
		li = xbmcgui.ListItem(label=dict_in.get('values').get('label'),label2=dict_in.get('values').get('label2'),offscreen=True)
		#script.module.infotagger v20
		info_tag = ListItemInfoTag(li,media_type)
		info_tag.set_info(dict_in.get('info'))
		# li.setInfo(media_type,dict_in.get('info'))
		li.setArt(dict_in.get('art'))
	return li

def get_retroplayer_item_and_listitem(dict_in,launch_file,media_type='game'):
	# launch_item = None
	launch_li = None
	# if launch_file:
	# 	launch_item = str(launch_file)
	if launch_file and dict_in:
		launch_li = xbmcgui.ListItem(label=dict_in.get('values').get('label'),label2=dict_in.get('values').get('label2'),offscreen=True)
		#script.module.infotagger v20
		# info_tag = ListItemInfoTag(launch_li,media_type)
		# info_tag.set_info(dict_in.get('info'))
		launch_li.setInfo(media_type,dict_in.get('info')) #ListitemInfoTag doesnt seem to work, need to set it for the player after the fact, to be fixed
		launch_li.setArt(dict_in.get('art'))
		launch_li.setPath(path=str(launch_file))
	return launch_li

def get_game_choose_list_listitem(dict_in,filter_in=None,media_type='video'):
	if isinstance(dict_in,dict):
		li = xbmcgui.ListItem(label=dict_in.get('values').get('label'),label2=dict_in.get('values').get('label2'),offscreen=True)
		#script.module.infotagger v20
		info_tag = ListItemInfoTag(li,media_type)
		info_tag.set_info(dict_in.get('info'))
		# li.setInfo(media_type,dict_in.get('info'))
		li.setArt(dict_in.get('art'))
		li.setProperties(dict_in.get('properties'))
		return li
	else:
		return None

def update_listitem_title(li_in,update_item,media_type='video'):
	if update_item:
		info_tag = ListItemInfoTag(li_in,media_type)
		info_tag.set_info({'title':'%(emu_name)s - %(label)s'%{'emu_name':li_in.getProperty('platform_description'),'label':li_in.getLabel()}})
		# li_in.setInfo(media_type,{'title':'%(emu_name)s - %(label)s'%{'emu_name':li_in.getProperty('platform_description'),'label':li_in.getLabel()}})
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

def url_quote_query(query_in):
	if isinstance(query_in,dict):
		return url_quote(json.dumps(query_in))
	else:
		return None

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
		#script.module.infotagger v20
		info_tag = ListItemInfoTag(li,media_type)
		info_tag.set_info(dict_in.get('info'))
		# li.setInfo(media_type,dict_in.get('info'))
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
		stats_out['studio']['all'] = sorted(set(flatten_list([x.get('info').get('studio') for x in games if x.get('info').get('studio') and x.get('info').get('studio') not in [[],[None]]])))
		stats_out['tag']['all'] = sorted(set(flatten_list([x.get('info').get('tag') for x in games if x.get('info').get('tag') and x.get('info').get('tag') not in [[],[None]]])))
		stats_out['groups']['all'] = sorted(set(flatten_list([x.get('info').get('showlink') for x in games if x.get('info').get('showlink') and x.get('info').get('showlink') not in [[],[None]]])))
		if stats_out['alphabetical']['all']:
			# stats_out['alphabetical']['count'] = [sum([y.get('values').get('label').upper().startswith(x) for y in games]) for x in stats_out['alphabetical']['all']]
			# stats_out['alphabetical']['count'][0] = sum([not y.get('values').get('label')[0].isalpha() for y in games if isinstance(y.get('values').get('label'),str) and len()]) #Recalc the numerical stats
			stats_out['alphabetical']['count'] = [sum([y.get('properties').get('starts_with').startswith(x) for y in games if y.get('properties').get('starts_with')]) for x in stats_out['alphabetical']['all']]
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
		# game_filename = url_unquote(game_url.split('/')[-1].split('%2F')[-1])
		game_filename_path = Path(url_unquote(game_url))
		game_dl_dict = {'dl_source':emu_dl_source,
					'baseurl':emu_baseurl,
					'url':game_url,
					'downloadpath':next(iter([x for x in [game_downloadpath,emu_downloadpath] if x]),'default'),
					'url_resolved':os.path.join(emu_baseurl,game_url.strip(os.sep).strip('/')),
					'filename':game_filename_path.name,
					'filename_no_ext':game_filename_path.stem,
					'filename_ext':game_filename_path.suffix.replace('.','').lower(),
					'post_processor':next(iter([x for x in [game_post_processor,emu_post_processor] if x]),'none'),
					'launcher':next(iter([x for x in [game_launcher,emu_launcher] if x]),'retroplayer'),
					'default_addon':next(iter([x for x in [game_default_addon,emu_default_addon] if x]),'none'),
					'ext_launch_cmd':next(iter([x for x in [game_ext_launch_cmd,emu_ext_launch_cmd] if x]),'none'),
					'emu_command':game_emu_command,
					'downloadpath_resolved':Path(emu_downloadpath).joinpath(game_filename_path.name).expanduser(),
					}
		if organize_default_dir and game_dl_dict.get('downloadpath') == 'default' or str(game_dl_dict.get('downloadpath')) == str(default_dir) and emu_name:
			new_default_dir = check_userdata_directory(os.path.join(str(default_dir),emu_name))
			if new_default_dir:
				game_dl_dict['downloadpath'] = str(new_default_dir)
				game_dl_dict['downloadpath_resolved'] = Path(game_dl_dict.get('downloadpath')).joinpath(game_filename_path.name).expanduser()
		if game_dl_dict.get('downloadpath_resolved').parent.exists():
			if emu_post_processor in ['move_to_folder_cdimono1','move_to_folder_fmtowns_cd']: #Downloaded to a specific folder for softlists
				game_dl_dict['matching_existing_files'] = [x for x in game_dl_dict.get('downloadpath_resolved').parent.glob('**/'+glob.escape(game_dl_dict.get('downloadpath_resolved').stem)+'[.]*') if x.suffix.lower() in ['.zip','.ZIP','.chd','CHD']]
			else:
				if game_dl_dict.get('filename_ext') not in ARCHIVE_FILETYPES: #If file to be downloaded is not an archive, it should match exactly with a local file - currenly works because all post processed filetypes are archives.  This may have to be updated in the future
					if check_if_file_exists(game_dl_dict.get('downloadpath_resolved')):
						game_dl_dict['matching_existing_files'] = [game_dl_dict.get('downloadpath_resolved')]
					else:
						game_dl_dict['matching_existing_files'] = []
				else: #If the file to be downloaded is an archive, the name without extension should match with a local file
					game_dl_dict['matching_existing_files'] = [x for x in game_dl_dict.get('downloadpath_resolved').parent.glob('**/'+glob.escape(game_dl_dict.get('downloadpath_resolved').stem)+'[.]*') if x.suffix.lower() not in IGNORE_THESE_FILETYPES and x.name.lower() not in IGNORE_THESE_FILES]
		elif xbmcvfs.exists(get_dest_as_str(game_dl_dict.get('downloadpath'))): #Kodi network source save spot (like smb address) need to use xbmcvfs to check local files
			if game_dl_dict.get('filename_ext') not in ARCHIVE_FILETYPES:
				if check_if_file_exists(get_dest_as_str(game_dl_dict.get('downloadpath_resolved'))):
					game_dl_dict['matching_existing_files'] = [get_dest_as_str(game_dl_dict.get('downloadpath_resolved'))]
				else:
					game_dl_dict['matching_existing_files'] = []
			else:
				game_dl_dict['matching_existing_files'] = [x for x in get_all_files_in_directory_xbmcvfs(get_dest_as_str(game_dl_dict.get('downloadpath'))) if os.path.split(os.path.splitext(x)[0])[-1] == game_dl_dict.get('filename_no_ext') and os.path.splitext(x)[-1].lower() not in IGNORE_THESE_FILETYPES and os.path.split(os.path.splitext(x)[0])[-1] not in IGNORE_THESE_FILES]
		else:
			game_dl_dict['matching_existing_files'] = []
		if game_dl_dict.get('emu_command') and emu_post_processor not in ['move_to_folder_cdimono1','move_to_folder_fmtowns_cd']:
			if 'smb:' not in game_dl_dict.get('downloadpath') and 'nfs:' not in game_dl_dict.get('downloadpath'):
				#Faster search if not a network share
				game_dl_dict['matching_existing_files'] = list(set(game_dl_dict.get('matching_existing_files')+[x for x in game_dl_dict.get('downloadpath_resolved').parent.glob('**/'+glob.escape(game_dl_dict.get('emu_command'))+'*') if x.suffix.lower() not in IGNORE_THESE_FILETYPES and x.name.lower() not in IGNORE_THESE_FILES]))
			else:
				#Slower search if a network share
				game_dl_dict['matching_existing_files'] = list(set(game_dl_dict.get('matching_existing_files')+[x for x in get_all_files_in_directory_xbmcvfs(get_dest_as_str(game_dl_dict.get('downloadpath'))) if game_dl_dict.get('emu_command').lower() in x.lower() and Path(x).suffix.lower() not in IGNORE_THESE_FILETYPES and Path(x).name.lower() not in IGNORE_THESE_FILES]))
		if game_dl_dict.get('post_processor') in ['process_chd_games'] and game_dl_dict.get('filename_ext') in ['chd']: #Special case where chd files might be moved to a lower directory already, look for matching files there
			if game_dl_dict.get('downloadpath_resolved').parent.exists():
				if check_if_file_exists(Path(game_dl_dict.get('downloadpath_resolved')).parent.joinpath(Path(game_dl_dict.get('url_resolved')).parent.name,Path(game_dl_dict.get('downloadpath_resolved')).name)):
					game_dl_dict['matching_existing_files'] = list(set(game_dl_dict.get('matching_existing_files')+[game_dl_dict.get('downloadpath_resolved').parent.joinpath(Path(game_dl_dict.get('url_resolved')).parent.name,game_dl_dict.get('downloadpath_resolved').name)]))
			elif xbmcvfs.exists(get_dest_as_str(game_dl_dict.get('downloadpath'))): #Kodi network source save spot (like smb address) need to use xbmcvfs to check local files
				if check_if_file_exists(get_dest_as_str(Path(game_dl_dict.get('downloadpath_resolved')).parent.joinpath(Path(game_dl_dict.get('url_resolved')).parent.name,Path(game_dl_dict.get('downloadpath_resolved')).name))):
					game_dl_dict['matching_existing_files'] = list(set(game_dl_dict.get('matching_existing_files')+[get_dest_as_str(game_dl_dict.get('downloadpath_resolved').parent.joinpath(Path(game_dl_dict.get('url_resolved')).parent.name,game_dl_dict.get('downloadpath_resolved').name))]))
		if game_dl_dict.get('post_processor').startswith('move_to_folder_'): #Special case where files might be moved to a lower directory already, look for matching files there
			folder_to_check = game_dl_dict.get('post_processor').replace('move_to_folder_','')
			if game_dl_dict.get('downloadpath_resolved').parent.exists():
				if check_if_file_exists(Path(game_dl_dict.get('downloadpath_resolved')).parent.joinpath(folder_to_check,Path(game_dl_dict.get('downloadpath_resolved')).name)):
					game_dl_dict['matching_existing_files'] = list(set(game_dl_dict.get('matching_existing_files')+[game_dl_dict.get('downloadpath_resolved').parent.joinpath(folder_to_check,game_dl_dict.get('downloadpath_resolved').name)]))
			elif xbmcvfs.exists(get_dest_as_str(game_dl_dict.get('downloadpath'))): #Kodi network source save spot (like smb address) need to use xbmcvfs to check local files
				if check_if_file_exists(get_dest_as_str(Path(game_dl_dict.get('downloadpath_resolved')).parent.joinpath(folder_to_check,Path(game_dl_dict.get('downloadpath_resolved')).name))):
					game_dl_dict['matching_existing_files'] = list(set(game_dl_dict.get('matching_existing_files')+[get_dest_as_str(game_dl_dict.get('downloadpath_resolved').parent.joinpath(folder_to_check,game_dl_dict.get('downloadpath_resolved').name))]))
		if game_dl_dict.get('dl_source') in ['Archive.org']:
			game_dl_dict['downloader'] = 'archive_org'
		elif 'http' in game_dl_dict.get('dl_source'):
			game_dl_dict['downloader'] = 'generic'
		elif game_dl_dict.get('dl_source') in ['Local Network Source','Kodi Library Source','Local File Source']:
			game_dl_dict['downloader'] = 'local_source'
		else:
			game_dl_dict['downloader'] = None

	xbmc.log(msg='IAGL:  Current game download parameters %(game_dl_dict)s' % {'game_dl_dict': game_dl_dict}, level=xbmc.LOGDEBUG)
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

def remove_game_from_favorites(filename_in=None,game=None):
	success = False
	if isinstance(game,str) and check_if_file_exists(filename_in):
		games = get_xml_games(filename_in)
		if game in [x.get('@name') for x in games]:
			if len([x for x in games if x.get('@name')!=game])>=1:
				games_header = get_xml_header_path_et_fromstring(filename_in)
				if games_header:
					xml_out = xmltodict.unparse({'datafile':{'header':games_header}}, pretty=True).replace('</datafile>',''.join([xmltodict.unparse({'game':x},pretty=True).replace('<?xml version="1.0" encoding="utf-8"?>','') for x in games if x and x.get('@name') != game]))+'\n</datafile>'
					if '<datafile>' in xml_out and '</datafile>' in xml_out:
						success = write_text_to_file(xml_out,filename_in)
					else:
						xbmc.log(msg='IAGL:  The xml appears malformed so it will not be updated.', level=xbmc.LOGERROR)
				else:
					xbmc.log(msg='IAGL:  Unable to parse the header in the file %(filename_in)s'%{'filename_in':filename_in}, level=xbmc.LOGERROR)
			else:
				xbmc.log(msg='IAGL:  Unable to delete the game from the file because there is only one game listed.  Delete the list if desired.', level=xbmc.LOGERROR)
		else:
			xbmc.log(msg='IAGL:  Unable find the game %(game)s in the file %(filename_in)s'%{'game':game, 'filename_in':filename_in}, level=xbmc.LOGERROR)
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

def copy_file_xbmcvfs(file_in=None,path_in=None):
	success = False
	if isinstance(file_in,Path):
		file_in = get_dest_as_str(file_in) #Make this a string for xbmcvfs copying
	if file_in is not None and path_in is not None:
		if check_if_file_exists(file_in):
			if not check_if_file_exists(path_in.joinpath(Path(file_in).name)):
				success = xbmcvfs.copy(file_in,str(path_in.joinpath(Path(file_in).name)))
				if not success: #Per docs note moving files between different filesystem (eg. local to nfs://) is not possible on all platforms. You may have to do it manually by using the copy and deleteFile functions.
					xbmc.log(msg='IAGL:  Unable to copy file %(value_in_1)s to %(value_in_2)s'%{'value_in_1':file_in,'value_in_2':path_in}, level=xbmc.LOGDEBUG)
			else:
				xbmc.log(msg='IAGL:  The file %(value_in_1)s was found to already exist at the location requested'%{'value_in_1':Path(file_in).name}, level=xbmc.LOGDEBUG)
				success = True
		else:
			xbmc.log(msg='IAGL:  Unable to copy file %(value_in_1)s, could not be found.'%{'value_in_1':file_in}, level=xbmc.LOGDEBUG)
	if success:
		xbmc.log(msg='IAGL:  Copied file %(value_in_1)s to %(value_in_2)s'%{'value_in_1':file_in,'value_in_2':path_in}, level=xbmc.LOGDEBUG)
	return success

def copy_directory_xbmcvfs(directory_in=None,directory_out=None):
	files_out = list()
	overall_success = True

	if not xbmcvfs.exists(directory_out):
		if xbmcvfs.mkdir(directory_out):
			xbmc.log(msg='IAGL:  Requested directory %(dd)s created' % {'dd': directory_out}, level=xbmc.LOGDEBUG)
		else:
			xbmc.log(msg='IAGL:  Requested directory %(dd)s failed to be created, copy may fail' % {'dd': directory_out}, level=xbmc.LOGERROR)

	dirs_in_archive, files_in_archive = xbmcvfs.listdir(directory_in)

	for ff in files_in_archive:
		file_from = os.path.join(directory_in,ff)
		if not xbmcvfs.exists(os.path.join(xbmcvfs.translatePath(directory_out),ff)):
			success = xbmcvfs.copy(file_from,os.path.join(xbmcvfs.translatePath(directory_out),ff)) #Extract the file to the correct directory
		else:
			xbmc.log(msg='IAGL: File %(ff)s already exists in the directory %(directory_in)s' % {'ff': ff,'directory_in':directory_in}, level=xbmc.LOGDEBUG)
			success = True
		if not success:
			xbmc.log(msg='IAGL:  Error copying file %(ff)s from directory %(directory_in)s' % {'ff': ff,'directory_in':directory_in}, level=xbmc.LOGERROR)
			overall_success = False
		else:
			xbmc.log(msg='IAGL: Copied file %(ff)s from directory %(directory_in)s' % {'ff': ff,'directory_in':directory_in}, level=xbmc.LOGDEBUG)
			files_out.append(os.path.join(xbmcvfs.translatePath(directory_out),ff)) #Append the file to the list of extracted files
	for dd in dirs_in_archive:
		if xbmcvfs.exists(os.path.join(xbmcvfs.translatePath(directory_out),dd)) or xbmcvfs.mkdir(os.path.join(xbmcvfs.translatePath(directory_out),dd)): #Make the archive directory in the directory_out
			files_out2, success2 = copy_directory_xbmcvfs(directory_in=os.path.join(directory_in,dd,''),directory_out=os.path.join(directory_out,dd))
			if success2:
				files_out = files_out + files_out2 #Append the files in the subdir to the list of extracted files
			else:
				xbmc.log(msg='IAGL:  Error copying files from the subdirectory %(dd)s in the directory %(directory_in)s' % {'dd': dd,'directory_in':directory_in}, level=xbmc.LOGERROR)
				overall_success = False
		else:
			overall_success = False
			xbmc.log(msg='IAGL:  Unable to create the subdirectory %(dir_from)s in the directory %(directory_in)s' % {'dir_from': os.path.join(xbmcvfs.translatePath(directory_out),dd),'archive_file':directory_in}, level=xbmc.LOGERROR)

	return files_out, overall_success

def get_file_suffix(file_in):
	if isinstance(file_in,Path):
		return file_in.suffix.lower()
	elif isinstance(file_in,str):
		return Path(file_in).suffix.lower()
	else:
		return None

def get_dest_as_str(dest):
	dest_str = str(dest)
	#Fix network share Kodi Path truncation
	if dest_str.startswith('smb:/') and not dest_str.startswith('smb://'):
		dest_str = dest_str.replace('smb:/','smb://')
	if dest_str.startswith('nfs:/') and not dest_str.startswith('nfs://'):
		dest_str = dest_str.replace('nfs:/','nfs://')
	return dest_str

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

def get_uuid():
	return str(uuid.uuid4()).split('-')[0]

def generate_discord_announcement(discord_id=None,username=None,uuid=None,game=None):
	if isinstance(username,str) and isinstance(uuid,str) and isinstance(game,dict):
		if isinstance(discord_id,str) and discord_id.isdigit():
			content_username = '<@!%(id)s>'%{'id':discord_id}
		else:
			content_username = username
		disc_json = {'username': 'IAGL Netplay Bot',
		'avatar_url': 'https://cdn.discordapp.com/avatars/696566666598809641/9fa63a6bd4a8783e9eaa2be13f2adae4.png',
		'content': '%(username)s has started hosting %(game_title)s'%{'username':content_username,'game_title':game.get('info').get('originaltitle')},
		'embeds': [{'author': {'name': username},
		'title': game.get('info').get('originaltitle'),
		'description': 'Come play %(game_title)s with %(username)s'%{'game_title':game.get('info').get('originaltitle'),'username':username},
		'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
		'fields': [{'name':'system',
					'value': next(iter([game.get('properties').get('platform_description')]),'Unknown'),
					'inline': True},
					{'name':'genre',
					'value': next(iter([','.join(game.get('info').get('genre'))]),'None'),
					'inline': True},
					{'name':'route',
					'value': game.get('properties').get('route'),
					'inline': False},
					{'name':'game_id',
					 'value': game.get('values').get('label2'),
					 'inline': False},
					 {'name':'uuid',
					 'value': uuid,
					 'inline': False},
					],
		'image': {'url':next(iter([x for x in [game.get('art').get('poster'),game.get('art').get('thumb')] if 'http' in x]),'https://cdn.discordapp.com/avatars/696566666598809641/9fa63a6bd4a8783e9eaa2be13f2adae4.png')}}]}
		with requests.Session() as s:
			response = s.post('https://discordapp.com/api/webhooks/%(chan)s/%(value)s'%{'chan':'696566666598809641','value':get_t_string('cDNaRo6zXMlTlwC-hnEnDXEEK6Lh_pxYnywkAyjdkGAIlmkza5QeTdQThHpXnUMXLJNt')},json=disc_json)
		return response.ok
	else:
		return False

def map_lobby_listitem_dict(libretro_dict=None,discord_dict=None,filter_lobby=True):
	dict_out = None
	current_query=dict()
	uuid_match = next(iter(get_game_tags(libretro_dict.get('username'))),None)
	current_discords = [dict(zip([z.get('name') for z in y[0]]+['author','description','timestamp','image'],[z.get('value') for z in y[0]]+[y[1].get('name'),y[2],y[3],y[4].get('url')])) for y in [(x.get('embeds')[0].get('fields'),x.get('embeds')[0].get('author'),x.get('embeds')[0].get('description'),x.get('embeds')[0].get('timestamp'),x.get('embeds')[0].get('image')) for x in discord_dict if x.get('embeds') and isinstance(x.get('embeds'),list) and x.get('embeds')[0].get('fields')] if any([z.get('name') == 'uuid' for z in y[0]])]
	discord_match = next(iter([x for x in current_discords if uuid_match and x.get('uuid')==uuid_match]),None)
	country_codes = [{"name":"Afghanistan","alpha-2":"AF","alpha-3":"AFG","country-code":"004","iso_3166-2":"ISO 3166-2:AF","region":"Asia","sub-region":"Southern Asia","intermediate-region":"","region-code":"142","sub-region-code":"034","intermediate-region-code":""},{"name":"Åland Islands","alpha-2":"AX","alpha-3":"ALA","country-code":"248","iso_3166-2":"ISO 3166-2:AX","region":"Europe","sub-region":"Northern Europe","intermediate-region":"","region-code":"150","sub-region-code":"154","intermediate-region-code":""},{"name":"Albania","alpha-2":"AL","alpha-3":"ALB","country-code":"008","iso_3166-2":"ISO 3166-2:AL","region":"Europe","sub-region":"Southern Europe","intermediate-region":"","region-code":"150","sub-region-code":"039","intermediate-region-code":""},{"name":"Algeria","alpha-2":"DZ","alpha-3":"DZA","country-code":"012","iso_3166-2":"ISO 3166-2:DZ","region":"Africa","sub-region":"Northern Africa","intermediate-region":"","region-code":"002","sub-region-code":"015","intermediate-region-code":""},{"name":"American Samoa","alpha-2":"AS","alpha-3":"ASM","country-code":"016","iso_3166-2":"ISO 3166-2:AS","region":"Oceania","sub-region":"Polynesia","intermediate-region":"","region-code":"009","sub-region-code":"061","intermediate-region-code":""},{"name":"Andorra","alpha-2":"AD","alpha-3":"AND","country-code":"020","iso_3166-2":"ISO 3166-2:AD","region":"Europe","sub-region":"Southern Europe","intermediate-region":"","region-code":"150","sub-region-code":"039","intermediate-region-code":""},{"name":"Angola","alpha-2":"AO","alpha-3":"AGO","country-code":"024","iso_3166-2":"ISO 3166-2:AO","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Middle Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"017"},{"name":"Anguilla","alpha-2":"AI","alpha-3":"AIA","country-code":"660","iso_3166-2":"ISO 3166-2:AI","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Caribbean","region-code":"019","sub-region-code":"419","intermediate-region-code":"029"},{"name":"Antarctica","alpha-2":"AQ","alpha-3":"ATA","country-code":"010","iso_3166-2":"ISO 3166-2:AQ","region":"","sub-region":"","intermediate-region":"","region-code":"","sub-region-code":"","intermediate-region-code":""},{"name":"Antigua and Barbuda","alpha-2":"AG","alpha-3":"ATG","country-code":"028","iso_3166-2":"ISO 3166-2:AG","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Caribbean","region-code":"019","sub-region-code":"419","intermediate-region-code":"029"},{"name":"Argentina","alpha-2":"AR","alpha-3":"ARG","country-code":"032","iso_3166-2":"ISO 3166-2:AR","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"South America","region-code":"019","sub-region-code":"419","intermediate-region-code":"005"},{"name":"Armenia","alpha-2":"AM","alpha-3":"ARM","country-code":"051","iso_3166-2":"ISO 3166-2:AM","region":"Asia","sub-region":"Western Asia","intermediate-region":"","region-code":"142","sub-region-code":"145","intermediate-region-code":""},{"name":"Aruba","alpha-2":"AW","alpha-3":"ABW","country-code":"533","iso_3166-2":"ISO 3166-2:AW","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Caribbean","region-code":"019","sub-region-code":"419","intermediate-region-code":"029"},{"name":"Australia","alpha-2":"AU","alpha-3":"AUS","country-code":"036","iso_3166-2":"ISO 3166-2:AU","region":"Oceania","sub-region":"Australia and New Zealand","intermediate-region":"","region-code":"009","sub-region-code":"053","intermediate-region-code":""},{"name":"Austria","alpha-2":"AT","alpha-3":"AUT","country-code":"040","iso_3166-2":"ISO 3166-2:AT","region":"Europe","sub-region":"Western Europe","intermediate-region":"","region-code":"150","sub-region-code":"155","intermediate-region-code":""},{"name":"Azerbaijan","alpha-2":"AZ","alpha-3":"AZE","country-code":"031","iso_3166-2":"ISO 3166-2:AZ","region":"Asia","sub-region":"Western Asia","intermediate-region":"","region-code":"142","sub-region-code":"145","intermediate-region-code":""},{"name":"Bahamas","alpha-2":"BS","alpha-3":"BHS","country-code":"044","iso_3166-2":"ISO 3166-2:BS","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Caribbean","region-code":"019","sub-region-code":"419","intermediate-region-code":"029"},{"name":"Bahrain","alpha-2":"BH","alpha-3":"BHR","country-code":"048","iso_3166-2":"ISO 3166-2:BH","region":"Asia","sub-region":"Western Asia","intermediate-region":"","region-code":"142","sub-region-code":"145","intermediate-region-code":""},{"name":"Bangladesh","alpha-2":"BD","alpha-3":"BGD","country-code":"050","iso_3166-2":"ISO 3166-2:BD","region":"Asia","sub-region":"Southern Asia","intermediate-region":"","region-code":"142","sub-region-code":"034","intermediate-region-code":""},{"name":"Barbados","alpha-2":"BB","alpha-3":"BRB","country-code":"052","iso_3166-2":"ISO 3166-2:BB","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Caribbean","region-code":"019","sub-region-code":"419","intermediate-region-code":"029"},{"name":"Belarus","alpha-2":"BY","alpha-3":"BLR","country-code":"112","iso_3166-2":"ISO 3166-2:BY","region":"Europe","sub-region":"Eastern Europe","intermediate-region":"","region-code":"150","sub-region-code":"151","intermediate-region-code":""},{"name":"Belgium","alpha-2":"BE","alpha-3":"BEL","country-code":"056","iso_3166-2":"ISO 3166-2:BE","region":"Europe","sub-region":"Western Europe","intermediate-region":"","region-code":"150","sub-region-code":"155","intermediate-region-code":""},{"name":"Belize","alpha-2":"BZ","alpha-3":"BLZ","country-code":"084","iso_3166-2":"ISO 3166-2:BZ","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Central America","region-code":"019","sub-region-code":"419","intermediate-region-code":"013"},{"name":"Benin","alpha-2":"BJ","alpha-3":"BEN","country-code":"204","iso_3166-2":"ISO 3166-2:BJ","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Western Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"011"},{"name":"Bermuda","alpha-2":"BM","alpha-3":"BMU","country-code":"060","iso_3166-2":"ISO 3166-2:BM","region":"Americas","sub-region":"Northern America","intermediate-region":"","region-code":"019","sub-region-code":"021","intermediate-region-code":""},{"name":"Bhutan","alpha-2":"BT","alpha-3":"BTN","country-code":"064","iso_3166-2":"ISO 3166-2:BT","region":"Asia","sub-region":"Southern Asia","intermediate-region":"","region-code":"142","sub-region-code":"034","intermediate-region-code":""},{"name":"Bolivia (Plurinational State of)","alpha-2":"BO","alpha-3":"BOL","country-code":"068","iso_3166-2":"ISO 3166-2:BO","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"South America","region-code":"019","sub-region-code":"419","intermediate-region-code":"005"},{"name":"Bonaire, Sint Eustatius and Saba","alpha-2":"BQ","alpha-3":"BES","country-code":"535","iso_3166-2":"ISO 3166-2:BQ","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Caribbean","region-code":"019","sub-region-code":"419","intermediate-region-code":"029"},{"name":"Bosnia and Herzegovina","alpha-2":"BA","alpha-3":"BIH","country-code":"070","iso_3166-2":"ISO 3166-2:BA","region":"Europe","sub-region":"Southern Europe","intermediate-region":"","region-code":"150","sub-region-code":"039","intermediate-region-code":""},{"name":"Botswana","alpha-2":"BW","alpha-3":"BWA","country-code":"072","iso_3166-2":"ISO 3166-2:BW","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Southern Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"018"},{"name":"Bouvet Island","alpha-2":"BV","alpha-3":"BVT","country-code":"074","iso_3166-2":"ISO 3166-2:BV","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"South America","region-code":"019","sub-region-code":"419","intermediate-region-code":"005"},{"name":"Brazil","alpha-2":"BR","alpha-3":"BRA","country-code":"076","iso_3166-2":"ISO 3166-2:BR","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"South America","region-code":"019","sub-region-code":"419","intermediate-region-code":"005"},{"name":"British Indian Ocean Territory","alpha-2":"IO","alpha-3":"IOT","country-code":"086","iso_3166-2":"ISO 3166-2:IO","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Eastern Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"014"},{"name":"Brunei Darussalam","alpha-2":"BN","alpha-3":"BRN","country-code":"096","iso_3166-2":"ISO 3166-2:BN","region":"Asia","sub-region":"South-eastern Asia","intermediate-region":"","region-code":"142","sub-region-code":"035","intermediate-region-code":""},{"name":"Bulgaria","alpha-2":"BG","alpha-3":"BGR","country-code":"100","iso_3166-2":"ISO 3166-2:BG","region":"Europe","sub-region":"Eastern Europe","intermediate-region":"","region-code":"150","sub-region-code":"151","intermediate-region-code":""},{"name":"Burkina Faso","alpha-2":"BF","alpha-3":"BFA","country-code":"854","iso_3166-2":"ISO 3166-2:BF","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Western Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"011"},{"name":"Burundi","alpha-2":"BI","alpha-3":"BDI","country-code":"108","iso_3166-2":"ISO 3166-2:BI","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Eastern Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"014"},{"name":"Cabo Verde","alpha-2":"CV","alpha-3":"CPV","country-code":"132","iso_3166-2":"ISO 3166-2:CV","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Western Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"011"},{"name":"Cambodia","alpha-2":"KH","alpha-3":"KHM","country-code":"116","iso_3166-2":"ISO 3166-2:KH","region":"Asia","sub-region":"South-eastern Asia","intermediate-region":"","region-code":"142","sub-region-code":"035","intermediate-region-code":""},{"name":"Cameroon","alpha-2":"CM","alpha-3":"CMR","country-code":"120","iso_3166-2":"ISO 3166-2:CM","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Middle Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"017"},{"name":"Canada","alpha-2":"CA","alpha-3":"CAN","country-code":"124","iso_3166-2":"ISO 3166-2:CA","region":"Americas","sub-region":"Northern America","intermediate-region":"","region-code":"019","sub-region-code":"021","intermediate-region-code":""},{"name":"Cayman Islands","alpha-2":"KY","alpha-3":"CYM","country-code":"136","iso_3166-2":"ISO 3166-2:KY","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Caribbean","region-code":"019","sub-region-code":"419","intermediate-region-code":"029"},{"name":"Central African Republic","alpha-2":"CF","alpha-3":"CAF","country-code":"140","iso_3166-2":"ISO 3166-2:CF","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Middle Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"017"},{"name":"Chad","alpha-2":"TD","alpha-3":"TCD","country-code":"148","iso_3166-2":"ISO 3166-2:TD","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Middle Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"017"},{"name":"Chile","alpha-2":"CL","alpha-3":"CHL","country-code":"152","iso_3166-2":"ISO 3166-2:CL","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"South America","region-code":"019","sub-region-code":"419","intermediate-region-code":"005"},{"name":"China","alpha-2":"CN","alpha-3":"CHN","country-code":"156","iso_3166-2":"ISO 3166-2:CN","region":"Asia","sub-region":"Eastern Asia","intermediate-region":"","region-code":"142","sub-region-code":"030","intermediate-region-code":""},{"name":"Christmas Island","alpha-2":"CX","alpha-3":"CXR","country-code":"162","iso_3166-2":"ISO 3166-2:CX","region":"Oceania","sub-region":"Australia and New Zealand","intermediate-region":"","region-code":"009","sub-region-code":"053","intermediate-region-code":""},{"name":"Cocos (Keeling) Islands","alpha-2":"CC","alpha-3":"CCK","country-code":"166","iso_3166-2":"ISO 3166-2:CC","region":"Oceania","sub-region":"Australia and New Zealand","intermediate-region":"","region-code":"009","sub-region-code":"053","intermediate-region-code":""},{"name":"Colombia","alpha-2":"CO","alpha-3":"COL","country-code":"170","iso_3166-2":"ISO 3166-2:CO","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"South America","region-code":"019","sub-region-code":"419","intermediate-region-code":"005"},{"name":"Comoros","alpha-2":"KM","alpha-3":"COM","country-code":"174","iso_3166-2":"ISO 3166-2:KM","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Eastern Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"014"},{"name":"Congo","alpha-2":"CG","alpha-3":"COG","country-code":"178","iso_3166-2":"ISO 3166-2:CG","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Middle Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"017"},{"name":"Congo, Democratic Republic of the","alpha-2":"CD","alpha-3":"COD","country-code":"180","iso_3166-2":"ISO 3166-2:CD","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Middle Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"017"},{"name":"Cook Islands","alpha-2":"CK","alpha-3":"COK","country-code":"184","iso_3166-2":"ISO 3166-2:CK","region":"Oceania","sub-region":"Polynesia","intermediate-region":"","region-code":"009","sub-region-code":"061","intermediate-region-code":""},{"name":"Costa Rica","alpha-2":"CR","alpha-3":"CRI","country-code":"188","iso_3166-2":"ISO 3166-2:CR","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Central America","region-code":"019","sub-region-code":"419","intermediate-region-code":"013"},{"name":"Côte d'Ivoire","alpha-2":"CI","alpha-3":"CIV","country-code":"384","iso_3166-2":"ISO 3166-2:CI","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Western Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"011"},{"name":"Croatia","alpha-2":"HR","alpha-3":"HRV","country-code":"191","iso_3166-2":"ISO 3166-2:HR","region":"Europe","sub-region":"Southern Europe","intermediate-region":"","region-code":"150","sub-region-code":"039","intermediate-region-code":""},{"name":"Cuba","alpha-2":"CU","alpha-3":"CUB","country-code":"192","iso_3166-2":"ISO 3166-2:CU","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Caribbean","region-code":"019","sub-region-code":"419","intermediate-region-code":"029"},{"name":"Curaçao","alpha-2":"CW","alpha-3":"CUW","country-code":"531","iso_3166-2":"ISO 3166-2:CW","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Caribbean","region-code":"019","sub-region-code":"419","intermediate-region-code":"029"},{"name":"Cyprus","alpha-2":"CY","alpha-3":"CYP","country-code":"196","iso_3166-2":"ISO 3166-2:CY","region":"Asia","sub-region":"Western Asia","intermediate-region":"","region-code":"142","sub-region-code":"145","intermediate-region-code":""},{"name":"Czechia","alpha-2":"CZ","alpha-3":"CZE","country-code":"203","iso_3166-2":"ISO 3166-2:CZ","region":"Europe","sub-region":"Eastern Europe","intermediate-region":"","region-code":"150","sub-region-code":"151","intermediate-region-code":""},{"name":"Denmark","alpha-2":"DK","alpha-3":"DNK","country-code":"208","iso_3166-2":"ISO 3166-2:DK","region":"Europe","sub-region":"Northern Europe","intermediate-region":"","region-code":"150","sub-region-code":"154","intermediate-region-code":""},{"name":"Djibouti","alpha-2":"DJ","alpha-3":"DJI","country-code":"262","iso_3166-2":"ISO 3166-2:DJ","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Eastern Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"014"},{"name":"Dominica","alpha-2":"DM","alpha-3":"DMA","country-code":"212","iso_3166-2":"ISO 3166-2:DM","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Caribbean","region-code":"019","sub-region-code":"419","intermediate-region-code":"029"},{"name":"Dominican Republic","alpha-2":"DO","alpha-3":"DOM","country-code":"214","iso_3166-2":"ISO 3166-2:DO","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Caribbean","region-code":"019","sub-region-code":"419","intermediate-region-code":"029"},{"name":"Ecuador","alpha-2":"EC","alpha-3":"ECU","country-code":"218","iso_3166-2":"ISO 3166-2:EC","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"South America","region-code":"019","sub-region-code":"419","intermediate-region-code":"005"},{"name":"Egypt","alpha-2":"EG","alpha-3":"EGY","country-code":"818","iso_3166-2":"ISO 3166-2:EG","region":"Africa","sub-region":"Northern Africa","intermediate-region":"","region-code":"002","sub-region-code":"015","intermediate-region-code":""},{"name":"El Salvador","alpha-2":"SV","alpha-3":"SLV","country-code":"222","iso_3166-2":"ISO 3166-2:SV","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Central America","region-code":"019","sub-region-code":"419","intermediate-region-code":"013"},{"name":"Equatorial Guinea","alpha-2":"GQ","alpha-3":"GNQ","country-code":"226","iso_3166-2":"ISO 3166-2:GQ","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Middle Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"017"},{"name":"Eritrea","alpha-2":"ER","alpha-3":"ERI","country-code":"232","iso_3166-2":"ISO 3166-2:ER","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Eastern Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"014"},{"name":"Estonia","alpha-2":"EE","alpha-3":"EST","country-code":"233","iso_3166-2":"ISO 3166-2:EE","region":"Europe","sub-region":"Northern Europe","intermediate-region":"","region-code":"150","sub-region-code":"154","intermediate-region-code":""},{"name":"Eswatini","alpha-2":"SZ","alpha-3":"SWZ","country-code":"748","iso_3166-2":"ISO 3166-2:SZ","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Southern Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"018"},{"name":"Ethiopia","alpha-2":"ET","alpha-3":"ETH","country-code":"231","iso_3166-2":"ISO 3166-2:ET","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Eastern Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"014"},{"name":"Falkland Islands (Malvinas)","alpha-2":"FK","alpha-3":"FLK","country-code":"238","iso_3166-2":"ISO 3166-2:FK","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"South America","region-code":"019","sub-region-code":"419","intermediate-region-code":"005"},{"name":"Faroe Islands","alpha-2":"FO","alpha-3":"FRO","country-code":"234","iso_3166-2":"ISO 3166-2:FO","region":"Europe","sub-region":"Northern Europe","intermediate-region":"","region-code":"150","sub-region-code":"154","intermediate-region-code":""},{"name":"Fiji","alpha-2":"FJ","alpha-3":"FJI","country-code":"242","iso_3166-2":"ISO 3166-2:FJ","region":"Oceania","sub-region":"Melanesia","intermediate-region":"","region-code":"009","sub-region-code":"054","intermediate-region-code":""},{"name":"Finland","alpha-2":"FI","alpha-3":"FIN","country-code":"246","iso_3166-2":"ISO 3166-2:FI","region":"Europe","sub-region":"Northern Europe","intermediate-region":"","region-code":"150","sub-region-code":"154","intermediate-region-code":""},{"name":"France","alpha-2":"FR","alpha-3":"FRA","country-code":"250","iso_3166-2":"ISO 3166-2:FR","region":"Europe","sub-region":"Western Europe","intermediate-region":"","region-code":"150","sub-region-code":"155","intermediate-region-code":""},{"name":"French Guiana","alpha-2":"GF","alpha-3":"GUF","country-code":"254","iso_3166-2":"ISO 3166-2:GF","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"South America","region-code":"019","sub-region-code":"419","intermediate-region-code":"005"},{"name":"French Polynesia","alpha-2":"PF","alpha-3":"PYF","country-code":"258","iso_3166-2":"ISO 3166-2:PF","region":"Oceania","sub-region":"Polynesia","intermediate-region":"","region-code":"009","sub-region-code":"061","intermediate-region-code":""},{"name":"French Southern Territories","alpha-2":"TF","alpha-3":"ATF","country-code":"260","iso_3166-2":"ISO 3166-2:TF","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Eastern Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"014"},{"name":"Gabon","alpha-2":"GA","alpha-3":"GAB","country-code":"266","iso_3166-2":"ISO 3166-2:GA","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Middle Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"017"},{"name":"Gambia","alpha-2":"GM","alpha-3":"GMB","country-code":"270","iso_3166-2":"ISO 3166-2:GM","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Western Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"011"},{"name":"Georgia","alpha-2":"GE","alpha-3":"GEO","country-code":"268","iso_3166-2":"ISO 3166-2:GE","region":"Asia","sub-region":"Western Asia","intermediate-region":"","region-code":"142","sub-region-code":"145","intermediate-region-code":""},{"name":"Germany","alpha-2":"DE","alpha-3":"DEU","country-code":"276","iso_3166-2":"ISO 3166-2:DE","region":"Europe","sub-region":"Western Europe","intermediate-region":"","region-code":"150","sub-region-code":"155","intermediate-region-code":""},{"name":"Ghana","alpha-2":"GH","alpha-3":"GHA","country-code":"288","iso_3166-2":"ISO 3166-2:GH","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Western Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"011"},{"name":"Gibraltar","alpha-2":"GI","alpha-3":"GIB","country-code":"292","iso_3166-2":"ISO 3166-2:GI","region":"Europe","sub-region":"Southern Europe","intermediate-region":"","region-code":"150","sub-region-code":"039","intermediate-region-code":""},{"name":"Greece","alpha-2":"GR","alpha-3":"GRC","country-code":"300","iso_3166-2":"ISO 3166-2:GR","region":"Europe","sub-region":"Southern Europe","intermediate-region":"","region-code":"150","sub-region-code":"039","intermediate-region-code":""},{"name":"Greenland","alpha-2":"GL","alpha-3":"GRL","country-code":"304","iso_3166-2":"ISO 3166-2:GL","region":"Americas","sub-region":"Northern America","intermediate-region":"","region-code":"019","sub-region-code":"021","intermediate-region-code":""},{"name":"Grenada","alpha-2":"GD","alpha-3":"GRD","country-code":"308","iso_3166-2":"ISO 3166-2:GD","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Caribbean","region-code":"019","sub-region-code":"419","intermediate-region-code":"029"},{"name":"Guadeloupe","alpha-2":"GP","alpha-3":"GLP","country-code":"312","iso_3166-2":"ISO 3166-2:GP","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Caribbean","region-code":"019","sub-region-code":"419","intermediate-region-code":"029"},{"name":"Guam","alpha-2":"GU","alpha-3":"GUM","country-code":"316","iso_3166-2":"ISO 3166-2:GU","region":"Oceania","sub-region":"Micronesia","intermediate-region":"","region-code":"009","sub-region-code":"057","intermediate-region-code":""},{"name":"Guatemala","alpha-2":"GT","alpha-3":"GTM","country-code":"320","iso_3166-2":"ISO 3166-2:GT","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Central America","region-code":"019","sub-region-code":"419","intermediate-region-code":"013"},{"name":"Guernsey","alpha-2":"GG","alpha-3":"GGY","country-code":"831","iso_3166-2":"ISO 3166-2:GG","region":"Europe","sub-region":"Northern Europe","intermediate-region":"Channel Islands","region-code":"150","sub-region-code":"154","intermediate-region-code":"830"},{"name":"Guinea","alpha-2":"GN","alpha-3":"GIN","country-code":"324","iso_3166-2":"ISO 3166-2:GN","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Western Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"011"},{"name":"Guinea-Bissau","alpha-2":"GW","alpha-3":"GNB","country-code":"624","iso_3166-2":"ISO 3166-2:GW","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Western Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"011"},{"name":"Guyana","alpha-2":"GY","alpha-3":"GUY","country-code":"328","iso_3166-2":"ISO 3166-2:GY","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"South America","region-code":"019","sub-region-code":"419","intermediate-region-code":"005"},{"name":"Haiti","alpha-2":"HT","alpha-3":"HTI","country-code":"332","iso_3166-2":"ISO 3166-2:HT","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Caribbean","region-code":"019","sub-region-code":"419","intermediate-region-code":"029"},{"name":"Heard Island and McDonald Islands","alpha-2":"HM","alpha-3":"HMD","country-code":"334","iso_3166-2":"ISO 3166-2:HM","region":"Oceania","sub-region":"Australia and New Zealand","intermediate-region":"","region-code":"009","sub-region-code":"053","intermediate-region-code":""},{"name":"Holy See","alpha-2":"VA","alpha-3":"VAT","country-code":"336","iso_3166-2":"ISO 3166-2:VA","region":"Europe","sub-region":"Southern Europe","intermediate-region":"","region-code":"150","sub-region-code":"039","intermediate-region-code":""},{"name":"Honduras","alpha-2":"HN","alpha-3":"HND","country-code":"340","iso_3166-2":"ISO 3166-2:HN","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Central America","region-code":"019","sub-region-code":"419","intermediate-region-code":"013"},{"name":"Hong Kong","alpha-2":"HK","alpha-3":"HKG","country-code":"344","iso_3166-2":"ISO 3166-2:HK","region":"Asia","sub-region":"Eastern Asia","intermediate-region":"","region-code":"142","sub-region-code":"030","intermediate-region-code":""},{"name":"Hungary","alpha-2":"HU","alpha-3":"HUN","country-code":"348","iso_3166-2":"ISO 3166-2:HU","region":"Europe","sub-region":"Eastern Europe","intermediate-region":"","region-code":"150","sub-region-code":"151","intermediate-region-code":""},{"name":"Iceland","alpha-2":"IS","alpha-3":"ISL","country-code":"352","iso_3166-2":"ISO 3166-2:IS","region":"Europe","sub-region":"Northern Europe","intermediate-region":"","region-code":"150","sub-region-code":"154","intermediate-region-code":""},{"name":"India","alpha-2":"IN","alpha-3":"IND","country-code":"356","iso_3166-2":"ISO 3166-2:IN","region":"Asia","sub-region":"Southern Asia","intermediate-region":"","region-code":"142","sub-region-code":"034","intermediate-region-code":""},{"name":"Indonesia","alpha-2":"ID","alpha-3":"IDN","country-code":"360","iso_3166-2":"ISO 3166-2:ID","region":"Asia","sub-region":"South-eastern Asia","intermediate-region":"","region-code":"142","sub-region-code":"035","intermediate-region-code":""},{"name":"Iran (Islamic Republic of)","alpha-2":"IR","alpha-3":"IRN","country-code":"364","iso_3166-2":"ISO 3166-2:IR","region":"Asia","sub-region":"Southern Asia","intermediate-region":"","region-code":"142","sub-region-code":"034","intermediate-region-code":""},{"name":"Iraq","alpha-2":"IQ","alpha-3":"IRQ","country-code":"368","iso_3166-2":"ISO 3166-2:IQ","region":"Asia","sub-region":"Western Asia","intermediate-region":"","region-code":"142","sub-region-code":"145","intermediate-region-code":""},{"name":"Ireland","alpha-2":"IE","alpha-3":"IRL","country-code":"372","iso_3166-2":"ISO 3166-2:IE","region":"Europe","sub-region":"Northern Europe","intermediate-region":"","region-code":"150","sub-region-code":"154","intermediate-region-code":""},{"name":"Isle of Man","alpha-2":"IM","alpha-3":"IMN","country-code":"833","iso_3166-2":"ISO 3166-2:IM","region":"Europe","sub-region":"Northern Europe","intermediate-region":"","region-code":"150","sub-region-code":"154","intermediate-region-code":""},{"name":"Israel","alpha-2":"IL","alpha-3":"ISR","country-code":"376","iso_3166-2":"ISO 3166-2:IL","region":"Asia","sub-region":"Western Asia","intermediate-region":"","region-code":"142","sub-region-code":"145","intermediate-region-code":""},{"name":"Italy","alpha-2":"IT","alpha-3":"ITA","country-code":"380","iso_3166-2":"ISO 3166-2:IT","region":"Europe","sub-region":"Southern Europe","intermediate-region":"","region-code":"150","sub-region-code":"039","intermediate-region-code":""},{"name":"Jamaica","alpha-2":"JM","alpha-3":"JAM","country-code":"388","iso_3166-2":"ISO 3166-2:JM","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Caribbean","region-code":"019","sub-region-code":"419","intermediate-region-code":"029"},{"name":"Japan","alpha-2":"JP","alpha-3":"JPN","country-code":"392","iso_3166-2":"ISO 3166-2:JP","region":"Asia","sub-region":"Eastern Asia","intermediate-region":"","region-code":"142","sub-region-code":"030","intermediate-region-code":""},{"name":"Jersey","alpha-2":"JE","alpha-3":"JEY","country-code":"832","iso_3166-2":"ISO 3166-2:JE","region":"Europe","sub-region":"Northern Europe","intermediate-region":"Channel Islands","region-code":"150","sub-region-code":"154","intermediate-region-code":"830"},{"name":"Jordan","alpha-2":"JO","alpha-3":"JOR","country-code":"400","iso_3166-2":"ISO 3166-2:JO","region":"Asia","sub-region":"Western Asia","intermediate-region":"","region-code":"142","sub-region-code":"145","intermediate-region-code":""},{"name":"Kazakhstan","alpha-2":"KZ","alpha-3":"KAZ","country-code":"398","iso_3166-2":"ISO 3166-2:KZ","region":"Asia","sub-region":"Central Asia","intermediate-region":"","region-code":"142","sub-region-code":"143","intermediate-region-code":""},{"name":"Kenya","alpha-2":"KE","alpha-3":"KEN","country-code":"404","iso_3166-2":"ISO 3166-2:KE","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Eastern Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"014"},{"name":"Kiribati","alpha-2":"KI","alpha-3":"KIR","country-code":"296","iso_3166-2":"ISO 3166-2:KI","region":"Oceania","sub-region":"Micronesia","intermediate-region":"","region-code":"009","sub-region-code":"057","intermediate-region-code":""},{"name":"Korea (Democratic People's Republic of)","alpha-2":"KP","alpha-3":"PRK","country-code":"408","iso_3166-2":"ISO 3166-2:KP","region":"Asia","sub-region":"Eastern Asia","intermediate-region":"","region-code":"142","sub-region-code":"030","intermediate-region-code":""},{"name":"Korea, Republic of","alpha-2":"KR","alpha-3":"KOR","country-code":"410","iso_3166-2":"ISO 3166-2:KR","region":"Asia","sub-region":"Eastern Asia","intermediate-region":"","region-code":"142","sub-region-code":"030","intermediate-region-code":""},{"name":"Kuwait","alpha-2":"KW","alpha-3":"KWT","country-code":"414","iso_3166-2":"ISO 3166-2:KW","region":"Asia","sub-region":"Western Asia","intermediate-region":"","region-code":"142","sub-region-code":"145","intermediate-region-code":""},{"name":"Kyrgyzstan","alpha-2":"KG","alpha-3":"KGZ","country-code":"417","iso_3166-2":"ISO 3166-2:KG","region":"Asia","sub-region":"Central Asia","intermediate-region":"","region-code":"142","sub-region-code":"143","intermediate-region-code":""},{"name":"Lao People's Democratic Republic","alpha-2":"LA","alpha-3":"LAO","country-code":"418","iso_3166-2":"ISO 3166-2:LA","region":"Asia","sub-region":"South-eastern Asia","intermediate-region":"","region-code":"142","sub-region-code":"035","intermediate-region-code":""},{"name":"Latvia","alpha-2":"LV","alpha-3":"LVA","country-code":"428","iso_3166-2":"ISO 3166-2:LV","region":"Europe","sub-region":"Northern Europe","intermediate-region":"","region-code":"150","sub-region-code":"154","intermediate-region-code":""},{"name":"Lebanon","alpha-2":"LB","alpha-3":"LBN","country-code":"422","iso_3166-2":"ISO 3166-2:LB","region":"Asia","sub-region":"Western Asia","intermediate-region":"","region-code":"142","sub-region-code":"145","intermediate-region-code":""},{"name":"Lesotho","alpha-2":"LS","alpha-3":"LSO","country-code":"426","iso_3166-2":"ISO 3166-2:LS","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Southern Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"018"},{"name":"Liberia","alpha-2":"LR","alpha-3":"LBR","country-code":"430","iso_3166-2":"ISO 3166-2:LR","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Western Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"011"},{"name":"Libya","alpha-2":"LY","alpha-3":"LBY","country-code":"434","iso_3166-2":"ISO 3166-2:LY","region":"Africa","sub-region":"Northern Africa","intermediate-region":"","region-code":"002","sub-region-code":"015","intermediate-region-code":""},{"name":"Liechtenstein","alpha-2":"LI","alpha-3":"LIE","country-code":"438","iso_3166-2":"ISO 3166-2:LI","region":"Europe","sub-region":"Western Europe","intermediate-region":"","region-code":"150","sub-region-code":"155","intermediate-region-code":""},{"name":"Lithuania","alpha-2":"LT","alpha-3":"LTU","country-code":"440","iso_3166-2":"ISO 3166-2:LT","region":"Europe","sub-region":"Northern Europe","intermediate-region":"","region-code":"150","sub-region-code":"154","intermediate-region-code":""},{"name":"Luxembourg","alpha-2":"LU","alpha-3":"LUX","country-code":"442","iso_3166-2":"ISO 3166-2:LU","region":"Europe","sub-region":"Western Europe","intermediate-region":"","region-code":"150","sub-region-code":"155","intermediate-region-code":""},{"name":"Macao","alpha-2":"MO","alpha-3":"MAC","country-code":"446","iso_3166-2":"ISO 3166-2:MO","region":"Asia","sub-region":"Eastern Asia","intermediate-region":"","region-code":"142","sub-region-code":"030","intermediate-region-code":""},{"name":"Madagascar","alpha-2":"MG","alpha-3":"MDG","country-code":"450","iso_3166-2":"ISO 3166-2:MG","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Eastern Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"014"},{"name":"Malawi","alpha-2":"MW","alpha-3":"MWI","country-code":"454","iso_3166-2":"ISO 3166-2:MW","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Eastern Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"014"},{"name":"Malaysia","alpha-2":"MY","alpha-3":"MYS","country-code":"458","iso_3166-2":"ISO 3166-2:MY","region":"Asia","sub-region":"South-eastern Asia","intermediate-region":"","region-code":"142","sub-region-code":"035","intermediate-region-code":""},{"name":"Maldives","alpha-2":"MV","alpha-3":"MDV","country-code":"462","iso_3166-2":"ISO 3166-2:MV","region":"Asia","sub-region":"Southern Asia","intermediate-region":"","region-code":"142","sub-region-code":"034","intermediate-region-code":""},{"name":"Mali","alpha-2":"ML","alpha-3":"MLI","country-code":"466","iso_3166-2":"ISO 3166-2:ML","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Western Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"011"},{"name":"Malta","alpha-2":"MT","alpha-3":"MLT","country-code":"470","iso_3166-2":"ISO 3166-2:MT","region":"Europe","sub-region":"Southern Europe","intermediate-region":"","region-code":"150","sub-region-code":"039","intermediate-region-code":""},{"name":"Marshall Islands","alpha-2":"MH","alpha-3":"MHL","country-code":"584","iso_3166-2":"ISO 3166-2:MH","region":"Oceania","sub-region":"Micronesia","intermediate-region":"","region-code":"009","sub-region-code":"057","intermediate-region-code":""},{"name":"Martinique","alpha-2":"MQ","alpha-3":"MTQ","country-code":"474","iso_3166-2":"ISO 3166-2:MQ","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Caribbean","region-code":"019","sub-region-code":"419","intermediate-region-code":"029"},{"name":"Mauritania","alpha-2":"MR","alpha-3":"MRT","country-code":"478","iso_3166-2":"ISO 3166-2:MR","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Western Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"011"},{"name":"Mauritius","alpha-2":"MU","alpha-3":"MUS","country-code":"480","iso_3166-2":"ISO 3166-2:MU","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Eastern Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"014"},{"name":"Mayotte","alpha-2":"YT","alpha-3":"MYT","country-code":"175","iso_3166-2":"ISO 3166-2:YT","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Eastern Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"014"},{"name":"Mexico","alpha-2":"MX","alpha-3":"MEX","country-code":"484","iso_3166-2":"ISO 3166-2:MX","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Central America","region-code":"019","sub-region-code":"419","intermediate-region-code":"013"},{"name":"Micronesia (Federated States of)","alpha-2":"FM","alpha-3":"FSM","country-code":"583","iso_3166-2":"ISO 3166-2:FM","region":"Oceania","sub-region":"Micronesia","intermediate-region":"","region-code":"009","sub-region-code":"057","intermediate-region-code":""},{"name":"Moldova, Republic of","alpha-2":"MD","alpha-3":"MDA","country-code":"498","iso_3166-2":"ISO 3166-2:MD","region":"Europe","sub-region":"Eastern Europe","intermediate-region":"","region-code":"150","sub-region-code":"151","intermediate-region-code":""},{"name":"Monaco","alpha-2":"MC","alpha-3":"MCO","country-code":"492","iso_3166-2":"ISO 3166-2:MC","region":"Europe","sub-region":"Western Europe","intermediate-region":"","region-code":"150","sub-region-code":"155","intermediate-region-code":""},{"name":"Mongolia","alpha-2":"MN","alpha-3":"MNG","country-code":"496","iso_3166-2":"ISO 3166-2:MN","region":"Asia","sub-region":"Eastern Asia","intermediate-region":"","region-code":"142","sub-region-code":"030","intermediate-region-code":""},{"name":"Montenegro","alpha-2":"ME","alpha-3":"MNE","country-code":"499","iso_3166-2":"ISO 3166-2:ME","region":"Europe","sub-region":"Southern Europe","intermediate-region":"","region-code":"150","sub-region-code":"039","intermediate-region-code":""},{"name":"Montserrat","alpha-2":"MS","alpha-3":"MSR","country-code":"500","iso_3166-2":"ISO 3166-2:MS","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Caribbean","region-code":"019","sub-region-code":"419","intermediate-region-code":"029"},{"name":"Morocco","alpha-2":"MA","alpha-3":"MAR","country-code":"504","iso_3166-2":"ISO 3166-2:MA","region":"Africa","sub-region":"Northern Africa","intermediate-region":"","region-code":"002","sub-region-code":"015","intermediate-region-code":""},{"name":"Mozambique","alpha-2":"MZ","alpha-3":"MOZ","country-code":"508","iso_3166-2":"ISO 3166-2:MZ","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Eastern Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"014"},{"name":"Myanmar","alpha-2":"MM","alpha-3":"MMR","country-code":"104","iso_3166-2":"ISO 3166-2:MM","region":"Asia","sub-region":"South-eastern Asia","intermediate-region":"","region-code":"142","sub-region-code":"035","intermediate-region-code":""},{"name":"Namibia","alpha-2":"NA","alpha-3":"NAM","country-code":"516","iso_3166-2":"ISO 3166-2:NA","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Southern Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"018"},{"name":"Nauru","alpha-2":"NR","alpha-3":"NRU","country-code":"520","iso_3166-2":"ISO 3166-2:NR","region":"Oceania","sub-region":"Micronesia","intermediate-region":"","region-code":"009","sub-region-code":"057","intermediate-region-code":""},{"name":"Nepal","alpha-2":"NP","alpha-3":"NPL","country-code":"524","iso_3166-2":"ISO 3166-2:NP","region":"Asia","sub-region":"Southern Asia","intermediate-region":"","region-code":"142","sub-region-code":"034","intermediate-region-code":""},{"name":"Netherlands","alpha-2":"NL","alpha-3":"NLD","country-code":"528","iso_3166-2":"ISO 3166-2:NL","region":"Europe","sub-region":"Western Europe","intermediate-region":"","region-code":"150","sub-region-code":"155","intermediate-region-code":""},{"name":"New Caledonia","alpha-2":"NC","alpha-3":"NCL","country-code":"540","iso_3166-2":"ISO 3166-2:NC","region":"Oceania","sub-region":"Melanesia","intermediate-region":"","region-code":"009","sub-region-code":"054","intermediate-region-code":""},{"name":"New Zealand","alpha-2":"NZ","alpha-3":"NZL","country-code":"554","iso_3166-2":"ISO 3166-2:NZ","region":"Oceania","sub-region":"Australia and New Zealand","intermediate-region":"","region-code":"009","sub-region-code":"053","intermediate-region-code":""},{"name":"Nicaragua","alpha-2":"NI","alpha-3":"NIC","country-code":"558","iso_3166-2":"ISO 3166-2:NI","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Central America","region-code":"019","sub-region-code":"419","intermediate-region-code":"013"},{"name":"Niger","alpha-2":"NE","alpha-3":"NER","country-code":"562","iso_3166-2":"ISO 3166-2:NE","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Western Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"011"},{"name":"Nigeria","alpha-2":"NG","alpha-3":"NGA","country-code":"566","iso_3166-2":"ISO 3166-2:NG","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Western Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"011"},{"name":"Niue","alpha-2":"NU","alpha-3":"NIU","country-code":"570","iso_3166-2":"ISO 3166-2:NU","region":"Oceania","sub-region":"Polynesia","intermediate-region":"","region-code":"009","sub-region-code":"061","intermediate-region-code":""},{"name":"Norfolk Island","alpha-2":"NF","alpha-3":"NFK","country-code":"574","iso_3166-2":"ISO 3166-2:NF","region":"Oceania","sub-region":"Australia and New Zealand","intermediate-region":"","region-code":"009","sub-region-code":"053","intermediate-region-code":""},{"name":"North Macedonia","alpha-2":"MK","alpha-3":"MKD","country-code":"807","iso_3166-2":"ISO 3166-2:MK","region":"Europe","sub-region":"Southern Europe","intermediate-region":"","region-code":"150","sub-region-code":"039","intermediate-region-code":""},{"name":"Northern Mariana Islands","alpha-2":"MP","alpha-3":"MNP","country-code":"580","iso_3166-2":"ISO 3166-2:MP","region":"Oceania","sub-region":"Micronesia","intermediate-region":"","region-code":"009","sub-region-code":"057","intermediate-region-code":""},{"name":"Norway","alpha-2":"NO","alpha-3":"NOR","country-code":"578","iso_3166-2":"ISO 3166-2:NO","region":"Europe","sub-region":"Northern Europe","intermediate-region":"","region-code":"150","sub-region-code":"154","intermediate-region-code":""},{"name":"Oman","alpha-2":"OM","alpha-3":"OMN","country-code":"512","iso_3166-2":"ISO 3166-2:OM","region":"Asia","sub-region":"Western Asia","intermediate-region":"","region-code":"142","sub-region-code":"145","intermediate-region-code":""},{"name":"Pakistan","alpha-2":"PK","alpha-3":"PAK","country-code":"586","iso_3166-2":"ISO 3166-2:PK","region":"Asia","sub-region":"Southern Asia","intermediate-region":"","region-code":"142","sub-region-code":"034","intermediate-region-code":""},{"name":"Palau","alpha-2":"PW","alpha-3":"PLW","country-code":"585","iso_3166-2":"ISO 3166-2:PW","region":"Oceania","sub-region":"Micronesia","intermediate-region":"","region-code":"009","sub-region-code":"057","intermediate-region-code":""},{"name":"Palestine, State of","alpha-2":"PS","alpha-3":"PSE","country-code":"275","iso_3166-2":"ISO 3166-2:PS","region":"Asia","sub-region":"Western Asia","intermediate-region":"","region-code":"142","sub-region-code":"145","intermediate-region-code":""},{"name":"Panama","alpha-2":"PA","alpha-3":"PAN","country-code":"591","iso_3166-2":"ISO 3166-2:PA","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Central America","region-code":"019","sub-region-code":"419","intermediate-region-code":"013"},{"name":"Papua New Guinea","alpha-2":"PG","alpha-3":"PNG","country-code":"598","iso_3166-2":"ISO 3166-2:PG","region":"Oceania","sub-region":"Melanesia","intermediate-region":"","region-code":"009","sub-region-code":"054","intermediate-region-code":""},{"name":"Paraguay","alpha-2":"PY","alpha-3":"PRY","country-code":"600","iso_3166-2":"ISO 3166-2:PY","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"South America","region-code":"019","sub-region-code":"419","intermediate-region-code":"005"},{"name":"Peru","alpha-2":"PE","alpha-3":"PER","country-code":"604","iso_3166-2":"ISO 3166-2:PE","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"South America","region-code":"019","sub-region-code":"419","intermediate-region-code":"005"},{"name":"Philippines","alpha-2":"PH","alpha-3":"PHL","country-code":"608","iso_3166-2":"ISO 3166-2:PH","region":"Asia","sub-region":"South-eastern Asia","intermediate-region":"","region-code":"142","sub-region-code":"035","intermediate-region-code":""},{"name":"Pitcairn","alpha-2":"PN","alpha-3":"PCN","country-code":"612","iso_3166-2":"ISO 3166-2:PN","region":"Oceania","sub-region":"Polynesia","intermediate-region":"","region-code":"009","sub-region-code":"061","intermediate-region-code":""},{"name":"Poland","alpha-2":"PL","alpha-3":"POL","country-code":"616","iso_3166-2":"ISO 3166-2:PL","region":"Europe","sub-region":"Eastern Europe","intermediate-region":"","region-code":"150","sub-region-code":"151","intermediate-region-code":""},{"name":"Portugal","alpha-2":"PT","alpha-3":"PRT","country-code":"620","iso_3166-2":"ISO 3166-2:PT","region":"Europe","sub-region":"Southern Europe","intermediate-region":"","region-code":"150","sub-region-code":"039","intermediate-region-code":""},{"name":"Puerto Rico","alpha-2":"PR","alpha-3":"PRI","country-code":"630","iso_3166-2":"ISO 3166-2:PR","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Caribbean","region-code":"019","sub-region-code":"419","intermediate-region-code":"029"},{"name":"Qatar","alpha-2":"QA","alpha-3":"QAT","country-code":"634","iso_3166-2":"ISO 3166-2:QA","region":"Asia","sub-region":"Western Asia","intermediate-region":"","region-code":"142","sub-region-code":"145","intermediate-region-code":""},{"name":"Réunion","alpha-2":"RE","alpha-3":"REU","country-code":"638","iso_3166-2":"ISO 3166-2:RE","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Eastern Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"014"},{"name":"Romania","alpha-2":"RO","alpha-3":"ROU","country-code":"642","iso_3166-2":"ISO 3166-2:RO","region":"Europe","sub-region":"Eastern Europe","intermediate-region":"","region-code":"150","sub-region-code":"151","intermediate-region-code":""},{"name":"Russian Federation","alpha-2":"RU","alpha-3":"RUS","country-code":"643","iso_3166-2":"ISO 3166-2:RU","region":"Europe","sub-region":"Eastern Europe","intermediate-region":"","region-code":"150","sub-region-code":"151","intermediate-region-code":""},{"name":"Rwanda","alpha-2":"RW","alpha-3":"RWA","country-code":"646","iso_3166-2":"ISO 3166-2:RW","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Eastern Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"014"},{"name":"Saint Barthélemy","alpha-2":"BL","alpha-3":"BLM","country-code":"652","iso_3166-2":"ISO 3166-2:BL","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Caribbean","region-code":"019","sub-region-code":"419","intermediate-region-code":"029"},{"name":"Saint Helena, Ascension and Tristan da Cunha","alpha-2":"SH","alpha-3":"SHN","country-code":"654","iso_3166-2":"ISO 3166-2:SH","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Western Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"011"},{"name":"Saint Kitts and Nevis","alpha-2":"KN","alpha-3":"KNA","country-code":"659","iso_3166-2":"ISO 3166-2:KN","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Caribbean","region-code":"019","sub-region-code":"419","intermediate-region-code":"029"},{"name":"Saint Lucia","alpha-2":"LC","alpha-3":"LCA","country-code":"662","iso_3166-2":"ISO 3166-2:LC","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Caribbean","region-code":"019","sub-region-code":"419","intermediate-region-code":"029"},{"name":"Saint Martin (French part)","alpha-2":"MF","alpha-3":"MAF","country-code":"663","iso_3166-2":"ISO 3166-2:MF","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Caribbean","region-code":"019","sub-region-code":"419","intermediate-region-code":"029"},{"name":"Saint Pierre and Miquelon","alpha-2":"PM","alpha-3":"SPM","country-code":"666","iso_3166-2":"ISO 3166-2:PM","region":"Americas","sub-region":"Northern America","intermediate-region":"","region-code":"019","sub-region-code":"021","intermediate-region-code":""},{"name":"Saint Vincent and the Grenadines","alpha-2":"VC","alpha-3":"VCT","country-code":"670","iso_3166-2":"ISO 3166-2:VC","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Caribbean","region-code":"019","sub-region-code":"419","intermediate-region-code":"029"},{"name":"Samoa","alpha-2":"WS","alpha-3":"WSM","country-code":"882","iso_3166-2":"ISO 3166-2:WS","region":"Oceania","sub-region":"Polynesia","intermediate-region":"","region-code":"009","sub-region-code":"061","intermediate-region-code":""},{"name":"San Marino","alpha-2":"SM","alpha-3":"SMR","country-code":"674","iso_3166-2":"ISO 3166-2:SM","region":"Europe","sub-region":"Southern Europe","intermediate-region":"","region-code":"150","sub-region-code":"039","intermediate-region-code":""},{"name":"Sao Tome and Principe","alpha-2":"ST","alpha-3":"STP","country-code":"678","iso_3166-2":"ISO 3166-2:ST","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Middle Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"017"},{"name":"Saudi Arabia","alpha-2":"SA","alpha-3":"SAU","country-code":"682","iso_3166-2":"ISO 3166-2:SA","region":"Asia","sub-region":"Western Asia","intermediate-region":"","region-code":"142","sub-region-code":"145","intermediate-region-code":""},{"name":"Senegal","alpha-2":"SN","alpha-3":"SEN","country-code":"686","iso_3166-2":"ISO 3166-2:SN","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Western Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"011"},{"name":"Serbia","alpha-2":"RS","alpha-3":"SRB","country-code":"688","iso_3166-2":"ISO 3166-2:RS","region":"Europe","sub-region":"Southern Europe","intermediate-region":"","region-code":"150","sub-region-code":"039","intermediate-region-code":""},{"name":"Seychelles","alpha-2":"SC","alpha-3":"SYC","country-code":"690","iso_3166-2":"ISO 3166-2:SC","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Eastern Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"014"},{"name":"Sierra Leone","alpha-2":"SL","alpha-3":"SLE","country-code":"694","iso_3166-2":"ISO 3166-2:SL","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Western Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"011"},{"name":"Singapore","alpha-2":"SG","alpha-3":"SGP","country-code":"702","iso_3166-2":"ISO 3166-2:SG","region":"Asia","sub-region":"South-eastern Asia","intermediate-region":"","region-code":"142","sub-region-code":"035","intermediate-region-code":""},{"name":"Sint Maarten (Dutch part)","alpha-2":"SX","alpha-3":"SXM","country-code":"534","iso_3166-2":"ISO 3166-2:SX","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Caribbean","region-code":"019","sub-region-code":"419","intermediate-region-code":"029"},{"name":"Slovakia","alpha-2":"SK","alpha-3":"SVK","country-code":"703","iso_3166-2":"ISO 3166-2:SK","region":"Europe","sub-region":"Eastern Europe","intermediate-region":"","region-code":"150","sub-region-code":"151","intermediate-region-code":""},{"name":"Slovenia","alpha-2":"SI","alpha-3":"SVN","country-code":"705","iso_3166-2":"ISO 3166-2:SI","region":"Europe","sub-region":"Southern Europe","intermediate-region":"","region-code":"150","sub-region-code":"039","intermediate-region-code":""},{"name":"Solomon Islands","alpha-2":"SB","alpha-3":"SLB","country-code":"090","iso_3166-2":"ISO 3166-2:SB","region":"Oceania","sub-region":"Melanesia","intermediate-region":"","region-code":"009","sub-region-code":"054","intermediate-region-code":""},{"name":"Somalia","alpha-2":"SO","alpha-3":"SOM","country-code":"706","iso_3166-2":"ISO 3166-2:SO","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Eastern Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"014"},{"name":"South Africa","alpha-2":"ZA","alpha-3":"ZAF","country-code":"710","iso_3166-2":"ISO 3166-2:ZA","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Southern Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"018"},{"name":"South Georgia and the South Sandwich Islands","alpha-2":"GS","alpha-3":"SGS","country-code":"239","iso_3166-2":"ISO 3166-2:GS","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"South America","region-code":"019","sub-region-code":"419","intermediate-region-code":"005"},{"name":"South Sudan","alpha-2":"SS","alpha-3":"SSD","country-code":"728","iso_3166-2":"ISO 3166-2:SS","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Eastern Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"014"},{"name":"Spain","alpha-2":"ES","alpha-3":"ESP","country-code":"724","iso_3166-2":"ISO 3166-2:ES","region":"Europe","sub-region":"Southern Europe","intermediate-region":"","region-code":"150","sub-region-code":"039","intermediate-region-code":""},{"name":"Sri Lanka","alpha-2":"LK","alpha-3":"LKA","country-code":"144","iso_3166-2":"ISO 3166-2:LK","region":"Asia","sub-region":"Southern Asia","intermediate-region":"","region-code":"142","sub-region-code":"034","intermediate-region-code":""},{"name":"Sudan","alpha-2":"SD","alpha-3":"SDN","country-code":"729","iso_3166-2":"ISO 3166-2:SD","region":"Africa","sub-region":"Northern Africa","intermediate-region":"","region-code":"002","sub-region-code":"015","intermediate-region-code":""},{"name":"Suriname","alpha-2":"SR","alpha-3":"SUR","country-code":"740","iso_3166-2":"ISO 3166-2:SR","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"South America","region-code":"019","sub-region-code":"419","intermediate-region-code":"005"},{"name":"Svalbard and Jan Mayen","alpha-2":"SJ","alpha-3":"SJM","country-code":"744","iso_3166-2":"ISO 3166-2:SJ","region":"Europe","sub-region":"Northern Europe","intermediate-region":"","region-code":"150","sub-region-code":"154","intermediate-region-code":""},{"name":"Sweden","alpha-2":"SE","alpha-3":"SWE","country-code":"752","iso_3166-2":"ISO 3166-2:SE","region":"Europe","sub-region":"Northern Europe","intermediate-region":"","region-code":"150","sub-region-code":"154","intermediate-region-code":""},{"name":"Switzerland","alpha-2":"CH","alpha-3":"CHE","country-code":"756","iso_3166-2":"ISO 3166-2:CH","region":"Europe","sub-region":"Western Europe","intermediate-region":"","region-code":"150","sub-region-code":"155","intermediate-region-code":""},{"name":"Syrian Arab Republic","alpha-2":"SY","alpha-3":"SYR","country-code":"760","iso_3166-2":"ISO 3166-2:SY","region":"Asia","sub-region":"Western Asia","intermediate-region":"","region-code":"142","sub-region-code":"145","intermediate-region-code":""},{"name":"Taiwan, Province of China","alpha-2":"TW","alpha-3":"TWN","country-code":"158","iso_3166-2":"ISO 3166-2:TW","region":"Asia","sub-region":"Eastern Asia","intermediate-region":"","region-code":"142","sub-region-code":"030","intermediate-region-code":""},{"name":"Tajikistan","alpha-2":"TJ","alpha-3":"TJK","country-code":"762","iso_3166-2":"ISO 3166-2:TJ","region":"Asia","sub-region":"Central Asia","intermediate-region":"","region-code":"142","sub-region-code":"143","intermediate-region-code":""},{"name":"Tanzania, United Republic of","alpha-2":"TZ","alpha-3":"TZA","country-code":"834","iso_3166-2":"ISO 3166-2:TZ","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Eastern Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"014"},{"name":"Thailand","alpha-2":"TH","alpha-3":"THA","country-code":"764","iso_3166-2":"ISO 3166-2:TH","region":"Asia","sub-region":"South-eastern Asia","intermediate-region":"","region-code":"142","sub-region-code":"035","intermediate-region-code":""},{"name":"Timor-Leste","alpha-2":"TL","alpha-3":"TLS","country-code":"626","iso_3166-2":"ISO 3166-2:TL","region":"Asia","sub-region":"South-eastern Asia","intermediate-region":"","region-code":"142","sub-region-code":"035","intermediate-region-code":""},{"name":"Togo","alpha-2":"TG","alpha-3":"TGO","country-code":"768","iso_3166-2":"ISO 3166-2:TG","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Western Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"011"},{"name":"Tokelau","alpha-2":"TK","alpha-3":"TKL","country-code":"772","iso_3166-2":"ISO 3166-2:TK","region":"Oceania","sub-region":"Polynesia","intermediate-region":"","region-code":"009","sub-region-code":"061","intermediate-region-code":""},{"name":"Tonga","alpha-2":"TO","alpha-3":"TON","country-code":"776","iso_3166-2":"ISO 3166-2:TO","region":"Oceania","sub-region":"Polynesia","intermediate-region":"","region-code":"009","sub-region-code":"061","intermediate-region-code":""},{"name":"Trinidad and Tobago","alpha-2":"TT","alpha-3":"TTO","country-code":"780","iso_3166-2":"ISO 3166-2:TT","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Caribbean","region-code":"019","sub-region-code":"419","intermediate-region-code":"029"},{"name":"Tunisia","alpha-2":"TN","alpha-3":"TUN","country-code":"788","iso_3166-2":"ISO 3166-2:TN","region":"Africa","sub-region":"Northern Africa","intermediate-region":"","region-code":"002","sub-region-code":"015","intermediate-region-code":""},{"name":"Turkey","alpha-2":"TR","alpha-3":"TUR","country-code":"792","iso_3166-2":"ISO 3166-2:TR","region":"Asia","sub-region":"Western Asia","intermediate-region":"","region-code":"142","sub-region-code":"145","intermediate-region-code":""},{"name":"Turkmenistan","alpha-2":"TM","alpha-3":"TKM","country-code":"795","iso_3166-2":"ISO 3166-2:TM","region":"Asia","sub-region":"Central Asia","intermediate-region":"","region-code":"142","sub-region-code":"143","intermediate-region-code":""},{"name":"Turks and Caicos Islands","alpha-2":"TC","alpha-3":"TCA","country-code":"796","iso_3166-2":"ISO 3166-2:TC","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Caribbean","region-code":"019","sub-region-code":"419","intermediate-region-code":"029"},{"name":"Tuvalu","alpha-2":"TV","alpha-3":"TUV","country-code":"798","iso_3166-2":"ISO 3166-2:TV","region":"Oceania","sub-region":"Polynesia","intermediate-region":"","region-code":"009","sub-region-code":"061","intermediate-region-code":""},{"name":"Uganda","alpha-2":"UG","alpha-3":"UGA","country-code":"800","iso_3166-2":"ISO 3166-2:UG","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Eastern Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"014"},{"name":"Ukraine","alpha-2":"UA","alpha-3":"UKR","country-code":"804","iso_3166-2":"ISO 3166-2:UA","region":"Europe","sub-region":"Eastern Europe","intermediate-region":"","region-code":"150","sub-region-code":"151","intermediate-region-code":""},{"name":"United Arab Emirates","alpha-2":"AE","alpha-3":"ARE","country-code":"784","iso_3166-2":"ISO 3166-2:AE","region":"Asia","sub-region":"Western Asia","intermediate-region":"","region-code":"142","sub-region-code":"145","intermediate-region-code":""},{"name":"United Kingdom of Great Britain and Northern Ireland","alpha-2":"GB","alpha-3":"GBR","country-code":"826","iso_3166-2":"ISO 3166-2:GB","region":"Europe","sub-region":"Northern Europe","intermediate-region":"","region-code":"150","sub-region-code":"154","intermediate-region-code":""},{"name":"United States of America","alpha-2":"US","alpha-3":"USA","country-code":"840","iso_3166-2":"ISO 3166-2:US","region":"Americas","sub-region":"Northern America","intermediate-region":"","region-code":"019","sub-region-code":"021","intermediate-region-code":""},{"name":"United States Minor Outlying Islands","alpha-2":"UM","alpha-3":"UMI","country-code":"581","iso_3166-2":"ISO 3166-2:UM","region":"Oceania","sub-region":"Micronesia","intermediate-region":"","region-code":"009","sub-region-code":"057","intermediate-region-code":""},{"name":"Uruguay","alpha-2":"UY","alpha-3":"URY","country-code":"858","iso_3166-2":"ISO 3166-2:UY","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"South America","region-code":"019","sub-region-code":"419","intermediate-region-code":"005"},{"name":"Uzbekistan","alpha-2":"UZ","alpha-3":"UZB","country-code":"860","iso_3166-2":"ISO 3166-2:UZ","region":"Asia","sub-region":"Central Asia","intermediate-region":"","region-code":"142","sub-region-code":"143","intermediate-region-code":""},{"name":"Vanuatu","alpha-2":"VU","alpha-3":"VUT","country-code":"548","iso_3166-2":"ISO 3166-2:VU","region":"Oceania","sub-region":"Melanesia","intermediate-region":"","region-code":"009","sub-region-code":"054","intermediate-region-code":""},{"name":"Venezuela (Bolivarian Republic of)","alpha-2":"VE","alpha-3":"VEN","country-code":"862","iso_3166-2":"ISO 3166-2:VE","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"South America","region-code":"019","sub-region-code":"419","intermediate-region-code":"005"},{"name":"Viet Nam","alpha-2":"VN","alpha-3":"VNM","country-code":"704","iso_3166-2":"ISO 3166-2:VN","region":"Asia","sub-region":"South-eastern Asia","intermediate-region":"","region-code":"142","sub-region-code":"035","intermediate-region-code":""},{"name":"Virgin Islands (British)","alpha-2":"VG","alpha-3":"VGB","country-code":"092","iso_3166-2":"ISO 3166-2:VG","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Caribbean","region-code":"019","sub-region-code":"419","intermediate-region-code":"029"},{"name":"Virgin Islands (U.S.)","alpha-2":"VI","alpha-3":"VIR","country-code":"850","iso_3166-2":"ISO 3166-2:VI","region":"Americas","sub-region":"Latin America and the Caribbean","intermediate-region":"Caribbean","region-code":"019","sub-region-code":"419","intermediate-region-code":"029"},{"name":"Wallis and Futuna","alpha-2":"WF","alpha-3":"WLF","country-code":"876","iso_3166-2":"ISO 3166-2:WF","region":"Oceania","sub-region":"Polynesia","intermediate-region":"","region-code":"009","sub-region-code":"061","intermediate-region-code":""},{"name":"Western Sahara","alpha-2":"EH","alpha-3":"ESH","country-code":"732","iso_3166-2":"ISO 3166-2:EH","region":"Africa","sub-region":"Northern Africa","intermediate-region":"","region-code":"002","sub-region-code":"015","intermediate-region-code":""},{"name":"Yemen","alpha-2":"YE","alpha-3":"YEM","country-code":"887","iso_3166-2":"ISO 3166-2:YE","region":"Asia","sub-region":"Western Asia","intermediate-region":"","region-code":"142","sub-region-code":"145","intermediate-region-code":""},{"name":"Zambia","alpha-2":"ZM","alpha-3":"ZMB","country-code":"894","iso_3166-2":"ISO 3166-2:ZM","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Eastern Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"014"},{"name":"Zimbabwe","alpha-2":"ZW","alpha-3":"ZWE","country-code":"716","iso_3166-2":"ISO 3166-2:ZW","region":"Africa","sub-region":"Sub-Saharan Africa","intermediate-region":"Eastern Africa","region-code":"002","sub-region-code":"202","intermediate-region-code":"014"}]
	if filter_lobby and libretro_dict and uuid_match and discord_match:
		current_query['ip']=libretro_dict.get('ip')
		current_query['port']=libretro_dict.get('port')
		current_query['mitm_ip']=libretro_dict.get('mitm_ip')
		current_query['mitm_port']=libretro_dict.get('mitm_port')
		dict_out = {'values': {'label':'%(title)s on %(system)s'%{'title':libretro_dict.get('game_name'),'system':discord_match.get('system')},'label2':discord_match.get('game_id')},
				'info':   {'title':'%(title)s on %(system)s'%{'title':libretro_dict.get('game_name'),'system':discord_match.get('system')},
						   'originaltitle':libretro_dict.get('game_name'),
						   'date':get_date(libretro_dict.get('updated'),format_in='%Y-%m-%dT%H:%M:%SZ'),
						   'credits':[re_game_tags.sub('',libretro_dict.get('username')).strip()],
						   'genre':split_value(discord_match.get('genre')),
						   'lastplayed':discord_match.get('timestamp'),
						   'plot':discord_match.get('description')+'[CR][CR]'+loc_str(30606)%{'username':re_game_tags.sub('',libretro_dict.get('username')).strip(),'country':next(iter([x.get('name') for x in country_codes if x and x.get('alpha-2').lower() == libretro_dict.get('country')]),'Unknown'),'game_name':libretro_dict.get('game_name'),'pp':libretro_dict.get('has_password'),'spectate':next(iter([not x for x in [libretro_dict.get('has_spectate_password')] if isinstance(x,bool)]),False),'core_name':libretro_dict.get('core_name'),'core_version':libretro_dict.get('core_version'),'frontend':libretro_dict.get('frontend')}},
			    'art':{'icon':MEDIA_SPECIAL_PATH%{'filename':'netplay_logo.png'},
					  'thumb':choose_image(discord_match.get('image'),MEDIA_SPECIAL_PATH%{'filename':'netplay_box.jpg'}),
					  'poster':choose_image(discord_match.get('image'),MEDIA_SPECIAL_PATH%{'filename':'netplay_box.jpg'}),
					  'banner':MEDIA_SPECIAL_PATH%{'filename':'netplay_banner.jpg'},
					  'fanart':MEDIA_SPECIAL_PATH%{'filename':'fanart.jpg'}},
				'properties': {'route':discord_match.get('route'),
							   'query': json.dumps(current_query)},
				}
	elif not filter_lobby and libretro_dict:
		current_query['ip']=libretro_dict.get('ip')
		current_query['port']=libretro_dict.get('port')
		current_query['mitm_ip']=libretro_dict.get('mitm_ip')
		current_query['mitm_port']=libretro_dict.get('mitm_port')
		dict_out = {'values': {'label':libretro_dict.get('game_name'),'label2':libretro_dict.get('game_name')},
				'info':   {'title':libretro_dict.get('game_name'),
						   'originaltitle':libretro_dict.get('game_name'),
						   'date':get_date(libretro_dict.get('updated'),format_in='%Y-%m-%dT%H:%M:%SZ'),
						   'credits':[re_game_tags.sub('',libretro_dict.get('username')).strip()],
						   'lastplayed':libretro_dict.get('created'),
						   'plot':loc_str(30606)%{'username':re_game_tags.sub('',libretro_dict.get('username')).strip(),'country':next(iter([x.get('name') for x in country_codes if x and x.get('alpha-2').lower() == libretro_dict.get('country')]),'Unknown'),'game_name':libretro_dict.get('game_name'),'pp':libretro_dict.get('has_password'),'spectate':next(iter([not x for x in [libretro_dict.get('has_spectate_password')] if isinstance(x,bool)]),False),'core_name':libretro_dict.get('core_name'),'core_version':libretro_dict.get('core_version'),'frontend':libretro_dict.get('frontend')}},
			    'art':{'icon':MEDIA_SPECIAL_PATH%{'filename':'netplay_logo.png'},
					  'thumb':MEDIA_SPECIAL_PATH%{'filename':'netplay_box.jpg'},
					  'poster':MEDIA_SPECIAL_PATH%{'filename':'netplay_box.jpg'},
					  'banner':MEDIA_SPECIAL_PATH%{'filename':'netplay_banner.jpg'},
					  'fanart':MEDIA_SPECIAL_PATH%{'filename':'fanart.jpg'}},
				'properties': {'route':'game_search?query=%(query)s'%{'query':url_quote_query(libretro_dict)},
							   'query': json.dumps(current_query)},
				}
				
				# /%(game_id)s'%{'game_id':libretro_dict.get('core_name')}
	return dict_out

def get_libretro_dict():
	lobby_dict = None
	with requests.Session() as s:
		libretro_result = s.get('http://lobby.libretro.com/list/')
	if libretro_result.ok:
		try:
			libretro_result = json.loads(libretro_result.text)
		except Exception as exc:
			xbmc.log(msg='IAGL:  Error with libretro lobby query.  Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
	else:
		xbmc.log(msg='IAGL:  Libretro lobby returned no results. Response:  %(value)s' % {'exc': libretro_result.text}, level=xbmc.LOGERROR)
	return libretro_result

def get_discord_dict():
	discord_dict = None
	with requests.Session() as s:
		discord_result = s.get('https://discordapp.com/api/channels/%(channel)s/messages?limit=100'%{'channel':'696566635166826526'},headers={'Authorization':get_t_string('Obg Awx2BGZjZQxkZQHmZmHjBGLm.KbjSRj.bwRpgZk0f0Tg4Ucy6Z_qqvn9xFN'),'content-type':'application/json'})
	if discord_result.ok:
		try:
			discord_dict = json.loads(discord_result.text)
		except Exception as exc:
			xbmc.log(msg='IAGL:  Error with discord channel query.  Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
	else:
		xbmc.log(msg='IAGL:  Discord returned no results. Response:  %(value)s' % {'exc': discord_result.text}, level=xbmc.LOGERROR)
	return discord_dict

def get_t_string(string_in):
	if isinstance(string_in,str):
		return string_in.translate(bytes.maketrans(b'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',b'nopqrstuvwxyzabcdefghijklmNOPQRSTUVWXYZABCDEFGHIJKLM'))
	else:
		return None

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

def write_sparse_file(filename_in,file_size_in=0):
	success = False
	file_size = max(file_size_in,0)

	if filename_in and file_size>0:
		try:
			filename_in.write_bytes(b'\0' * file_size)
			success = True
			xbmc.log(msg='IAGL:  Sparse file of size %(value_in)s was created with pathlib'%{'value_in':file_size}, level=xbmc.LOGDEBUG)
		except Exception as exc:
			xbmc.log(msg='IAGL:  Error writing sparse file %(value_in)s with pathlib, will attempt xbmcvfs.  Exception %(exc)s' % {'value_in': file_in, 'exc': exc}, level=xbmc.LOGERROR)
			try:
				with xbmcvfs.File(str(filename_in), 'w') as fo:
					fo.write(bytearray(file_size))
					success = True
					xbmc.log(msg='IAGL:  Sparse file of size %(value_in)s was created with xbmcvfs'%{'value_in':file_size}, level=xbmc.LOGDEBUG)
			except:
				xbmc.log(msg='IAGL:  Error writing sparse file %(value_in)s.  Exception %(exc)s' % {'value_in': file_in, 'exc': exc}, level=xbmc.LOGERROR)

	return success

def combine_chunks(files_in,dest_file):
	success = False
	try:
		xbmc.log(msg='IAGL:  Combining chunk files into file %(dest_file)s using pathlib' % {'dest_file': dest_file}, level=xbmc.LOGDEBUG)
		with dest_file.open('ab') as fo:
			for ff in files_in:
				xbmc.log(msg='IAGL:  Combining chunk file %(ff)s' % {'ff': ff}, level=xbmc.LOGDEBUG)
				last_read = False
				with ff.open('rb') as f:
					while not last_read:
						chunk = f.read(CHUNK_SIZE)
						if chunk:
							fo.write(chunk)
						else:
							last_read=True
							break
				delete_file(ff)
		success = True
	except Exception as exc1:
		xbmc.log(msg='IAGL:  Pathlib failed %(exc1)s, attempting xbmcvfs' % {'exc1': exc1}, level=xbmc.LOGDEBUG)
		xbmc.log(msg='IAGL:  Combining chunk files into file %(dest_file)s using xbmcvfs' % {'dest_file': get_dest_as_str(dest_file)}, level=xbmc.LOGDEBUG)
		try:
			with xbmcvfs.File(get_dest_as_str(dest_file), 'wb') as fo:
				for ff in files_in:
					xbmc.log(msg='IAGL:  Combining chunk file %(ff)s' % {'ff': get_dest_as_str(ff)}, level=xbmc.LOGDEBUG)
					last_read = False
					with xbmcvfs.File(get_dest_as_str(ff)) as f:
						while not last_read:
							chunk = f.readBytes(CHUNK_SIZE)
							if chunk:
								fo.write(chunk)
							else:
								last_read=True
								break
					delete_file(ff)
			success = True
		except Exception as exc2:
			xbmc.log(msg='IAGL:  Combining chunk files failed %(exc)s' % {'exc': exc2}, level=xbmc.LOGERROR)
	return success

def calculate_chunk_range(l, n):
	newn = int(l / n)
	for i in range(0, n-1):
		yield range(l)[i*newn:i*newn+newn]
	yield range(l)[n*newn-newn:]

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