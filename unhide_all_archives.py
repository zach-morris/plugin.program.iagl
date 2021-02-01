import xbmc, xbmcgui, xbmcvfs
from resources.lib.utils import loc_str, get_mem_cache, set_mem_cache, clear_mem_cache
from resources.lib.main import iagl_addon
iagl_addon = iagl_addon()
clear_mem_cache('iagl_script_started')
if not get_mem_cache('iagl_script_started'):
	set_mem_cache('iagl_script_started','true')
	xbmc.log(msg='IAGL:  Set game lists to visible script started', level=xbmc.LOGDEBUG)
	for ii,hh in enumerate(iagl_addon.directory.get('userdata').get('dat_files').get('header')):
		if hh and hh.get('emu_visibility') and hh.get('emu_visibility') == 'hidden':
			current_fn = iagl_addon.directory.get('userdata').get('dat_files').get('files')[ii]
			game_list_id = current_fn.name.replace(current_fn.suffix,'')
			success = iagl_addon.game_lists.update_game_list_header(game_list_id,header_key='emu_visibility',header_value='visible',confirm_update=False)
	if iagl_addon.clear_list_cache_folder():
		current_dialog = xbmcgui.Dialog()
		ok_ret = current_dialog.ok(loc_str(30202),loc_str(30381))
		del current_dialog
	iagl_addon.clear_all_mem_cache()
	xbmc.executebuiltin('Container.Refresh')
	clear_mem_cache('iagl_script_started')
	xbmc.log(msg='IAGL:  Set game lists to visible script completed', level=xbmc.LOGDEBUG)
else:
	xbmc.log(msg='IAGL:  Script already running', level=xbmc.LOGDEBUG)
del iagl_addon, loc_str, get_mem_cache, set_mem_cache, clear_mem_cache