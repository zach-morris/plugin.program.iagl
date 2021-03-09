import xbmc, xbmcgui, xbmcvfs, os
from pathlib import Path
from resources.lib.utils import loc_str, get_mem_cache, set_mem_cache, clear_mem_cache, check_if_file_exists, get_xml_games, get_xml_header_path_et_fromstring, write_text_to_file
from resources.lib import xmltodict
from resources.lib.main import iagl_addon
iagl_addon_handle = iagl_addon()
if not get_mem_cache('iagl_script_started'):
	set_mem_cache('iagl_script_started','true')
	xbmc.log(msg='IAGL:  Convert old favorites format script started', level=xbmc.LOGDEBUG)
	success = False
	current_dialog = xbmcgui.Dialog()
	old_file = current_dialog.browse(1,loc_str(30618),'')
	if old_file:
		old_file_path = Path(old_file)
		games = None
		if check_if_file_exists(old_file_path):
			games = get_xml_games(old_file_path)
			games_header = get_xml_header_path_et_fromstring(old_file_path)
			for gg in games:
				if gg.get('rom') and gg.get('rom').get('@name'):
					gg['route'] = gg.get('rom').get('@name').replace('plugin://plugin.program.iagl/game/','').split('/')[0]
					gg.pop('rom', None)
			new_file_path = iagl_addon_handle.directory.get('userdata').get('dat_files').get('path').joinpath(old_file_path.name)
			if not check_if_file_exists(new_file_path):
				xml_out = xmltodict.unparse({'datafile':{'header':games_header}}, pretty=True).replace('</datafile>',''.join([xmltodict.unparse({'game':x},pretty=True).replace('<?xml version="1.0" encoding="utf-8"?>','') for x in games if x and x.get('route')]))+'\n</datafile>'
				success = write_text_to_file(xml_out.replace('\n\n','\n'),new_file_path)
			else:
				xbmc.log(msg='IAGL:  A favorites file with the same name already exists.  Please rename the old file or delete the existing file.', level=xbmc.LOGERROR)
		else:
			xbmc.log(msg='IAGL:  Unable to stat old file, please ensure it is on the local filesystem', level=xbmc.LOGERROR)
	if success:
		ok_ret = current_dialog.ok(loc_str(30202),loc_str(30620))
		clear_mem_cache('iagl_directory')
	else:
		ok_ret = current_dialog.ok(loc_str(30203),loc_str(30621))
	clear_mem_cache('iagl_script_started')
	xbmc.log(msg='IAGL:  Convert old favorites format script completed', level=xbmc.LOGDEBUG)
else:
	xbmc.log(msg='IAGL:  Script already running', level=xbmc.LOGDEBUG)
del iagl_addon_handle, loc_str, get_mem_cache, set_mem_cache, clear_mem_cache, check_if_file_exists, get_xml_games, get_xml_header_path_et_fromstring, write_text_to_file
