import xbmc, xbmcgui, xbmcvfs
from resources.lib.utils import loc_str, get_mem_cache, set_mem_cache, clear_mem_cache
from resources.lib.main import iagl_addon
iagl_addon = iagl_addon()
if not get_mem_cache('iagl_script_started'):
	set_mem_cache('iagl_script_started','true')
	xbmc.log(msg='IAGL:  Clear cache script started', level=xbmc.LOGDEBUG)
	if iagl_addon.clear_list_cache_folder() and iagl_addon.clear_game_cache_folder():
		current_dialog = xbmcgui.Dialog()
		ok_ret = current_dialog.ok(loc_str(30202),loc_str(30306)%{'game_list_id':'All Lists and Games'})
		del current_dialog
	iagl_addon.clear_all_mem_cache()
	xbmc.executebuiltin('Container.Refresh')
	clear_mem_cache('iagl_script_started')
	xbmc.log(msg='IAGL:  Clear cache script completed', level=xbmc.LOGDEBUG)
else:
	xbmc.log(msg='IAGL:  Script already running', level=xbmc.LOGDEBUG)
del iagl_addon, loc_str, get_mem_cache, set_mem_cache, clear_mem_cache