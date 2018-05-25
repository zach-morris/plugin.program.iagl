from kodi_six import xbmc, xbmcgui
WIN = xbmcgui.Window(10000)
if not WIN.getProperty('iagl.script_started'):
	WIN.setProperty('iagl.script_started','True')
	try:
		xbmc.log(msg='IAGL:  Unhide all archives script started', level=xbmc.LOGDEBUG)
		from main import iagl_utils
		IAGL = iagl_utils() #IAGL utils Class
		success = list()
		game_lists = IAGL.get_game_lists()
		game_list_visiblity = [x for x in game_lists['emu_visibility']]
		total_unhidden = 0
		try:
			if any(['hidden' in x for x in game_list_visiblity]):
				for ii in range(0,len(game_list_visiblity)):
					if game_list_visiblity[ii] != 'visible':
						IAGL.update_xml_header(game_lists['fullpath'][ii],'emu_visibility','visible',silent_update=True)
						total_unhidden = total_unhidden+1
			else:
				xbmc.log(msg='IAGL:  No game lists were found to be hidden.', level=xbmc.LOGDEBUG)
			success.append(True)
		except Exception as exc1:
			success.append(False)
			xbmc.log(msg='IAGL Error:  Game list could not be unhidden, Exception %(exc)s' % {'exc': str(exc1)}, level=xbmc.LOGERROR)
		if False not in success:
			current_dialog = xbmcgui.Dialog()
			ok_ret = current_dialog.ok('Completed','%(game_lists)s more game lists now visible.'%{'game_lists':total_unhidden})
			xbmc.executebuiltin('Container.Refresh')
	except Exception as exc:
		xbmc.log(msg='IAGL Error:  List cache could not be cleared, Exception %(exc)s' % {'exc': str(exc)}, level=xbmc.LOGERROR)
	WIN.clearProperty('iagl.script_started')
	xbmc.log(msg='IAGL:  Unhide all archives script completed', level=xbmc.LOGDEBUG)
else:
	xbmc.log(msg='IAGL:  Script already running', level=xbmc.LOGDEBUG)