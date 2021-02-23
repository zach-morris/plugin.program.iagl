import xbmc, xbmcgui, xbmcvfs
from resources.lib.utils import loc_str, get_mem_cache, set_mem_cache, clear_mem_cache
from resources.lib.main import iagl_addon
from resources.lib.download import iagl_download

iagl_addon = iagl_addon()
if not get_mem_cache('iagl_script_started'):
	set_mem_cache('iagl_script_started','true')
	xbmc.log(msg='IAGL:  Check archive.org login script started', level=xbmc.LOGDEBUG)
	iagl_download = iagl_download(settings=iagl_addon.settings,directory=iagl_addon.directory,game_list=None,game=None)
	iagl_download.downloader.login()
	if iagl_download.downloader.logged_in:
		current_dialog = xbmcgui.Dialog()
		ok_ret = current_dialog.ok(loc_str(30202),loc_str(30584))
		del current_dialog
		xbmc.log(msg='IAGL:  Login check was successful',level=xbmc.LOGINFO)
	else:
		current_dialog = xbmcgui.Dialog()
		ok_ret = current_dialog.ok(loc_str(30203),loc_str(30585))
		del current_dialog
		xbmc.log(msg='IAGL:  Login check failed',level=xbmc.LOGINFO)
	clear_mem_cache('iagl_script_started')
	xbmc.log(msg='IAGL:  Check archive.org login script completed', level=xbmc.LOGDEBUG)
else:
	xbmc.log(msg='IAGL:  Script already running', level=xbmc.LOGDEBUG)
del iagl_addon, iagl_download, loc_str, get_mem_cache, set_mem_cache, clear_mem_cache