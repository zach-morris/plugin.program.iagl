from kodi_six import xbmc, xbmcgui, xbmcvfs
import os

WIN = xbmcgui.Window(10000)
if not WIN.getProperty('iagl.script_started'):
	WIN.setProperty('iagl.script_started','True')
	try:
		xbmc.log(msg='IAGL:  Clear cache script started', level=xbmc.LOGDEBUG)
		import shutil
		from main import iagl_utils
		IAGL = iagl_utils() #IAGL utils Class
		success = list()
		try:
			if not xbmcvfs.rmdir(os.path.join(IAGL.get_temp_cache_path(),'')):
				shutil.rmtree(IAGL.get_temp_cache_path(), ignore_errors=True)
				xbmc.log(msg='IAGL:  Cache directory was cleared with shutil', level=xbmc.LOGDEBUG)
			else:
				xbmc.log(msg='IAGL:  Cache directory was cleared', level=xbmc.LOGDEBUG)
			IAGL.get_temp_cache_path() #Remake folder
			success.append(True)
		except Exception as exc1:
			success.append(False)
			xbmc.log(msg='IAGL Error:  Cache directory could not be cleared, Exception %(exc)s' % {'exc': str(exc1)}, level=xbmc.LOGERROR)
		try:
			IAGL.delete_all_list_cache()
			success.append(True)
			xbmc.log(msg='IAGL:  List cache was cleared.', level=xbmc.LOGDEBUG)
		except Exception as exc2:
			success.append(False)
			xbmc.log(msg='IAGL Error:  List cache could not be cleared, Exception %(exc)s' % {'exc': str(exc2)}, level=xbmc.LOGERROR)
		if False not in success:
			current_dialog = xbmcgui.Dialog()
			ok_ret = current_dialog.ok('Completed','Addon cache was cleared')
		try:  #Clear mem cache if possible
			xbmcgui.Window(xbmcgui.getCurrentWindowId()).clearProperty('iagl_current_crc')
			xbmcgui.Window(xbmcgui.getCurrentWindowId()).clearProperty('iagl_game_list')
		except:
			pass
	except Exception as exc:
		xbmc.log(msg='IAGL Error:  List cache could not be cleared, Exception %(exc)s' % {'exc': str(exc)}, level=xbmc.LOGERROR)
	WIN.clearProperty('iagl.script_started')
	xbmc.log(msg='IAGL:  Clear cache script completed', level=xbmc.LOGDEBUG)
else:
	xbmc.log(msg='IAGL:  Script already running', level=xbmc.LOGDEBUG)