from kodi_six import xbmc, xbmcgui, xbmcvfs
from contextlib import closing
import os
WIN = xbmcgui.Window(10000)
if not WIN.getProperty('iagl.script_started'):
	WIN.setProperty('iagl.script_started','True')
	try:
		xbmc.log(msg='IAGL:  Update addon to provide programs', level=xbmc.LOGDEBUG)
		from main import iagl_utils
		IAGL = iagl_utils() #IAGL utils Class
		addon_xml_path = os.path.join(IAGL.get_addon_install_path(),'addon.xml')
		success = list()
		with closing(xbmcvfs.File(addon_xml_path)) as content_file:
			byte_string = bytes(content_file.readBytes())
		try:
			file_contents = byte_string.decode('utf-8',errors='ignore')
			success.append(True)
		except Exception as exc1:
			file_contents = None
			success.append(False)
			xbmc.log(msg='IAGL Error:  Update addon to provide programs, Exception %(exc)s' % {'exc': str(exc1)}, level=xbmc.LOGERROR)
		if file_contents is not None:
			new_content = file_contents.split('<provides>')[0]+'<provides>executable game</provides>'+file_contents.split('</provides>')[-1]
			with closing(xbmcvfs.File(addon_xml_path,'w')) as content_file:
				content_file.write(new_content)
			success.append(True)
		if False not in success:
			current_dialog = xbmcgui.Dialog()
			ok_ret = current_dialog.ok('Completed','Addon updated to provide programs')
			xbmc.executebuiltin('Container.Refresh')
	except Exception as exc:
		xbmc.log(msg='IAGL Error:  Addon xml could not be updated, Exception %(exc)s' % {'exc': str(exc)}, level=xbmc.LOGERROR)
	WIN.clearProperty('iagl.script_started')
	xbmc.log(msg='IAGL:  Update addon to provide programs completed', level=xbmc.LOGDEBUG)
else:
	xbmc.log(msg='IAGL:  Script already running', level=xbmc.LOGDEBUG)