import xbmc, xbmcgui, xbmcvfs
from resources.lib.utils import loc_str, get_mem_cache, set_mem_cache, clear_mem_cache
from resources.lib.main import iagl_addon
iagl_addon_handle = iagl_addon()
if not get_mem_cache('iagl_script_started'):
	set_mem_cache('iagl_script_started','true')
	xbmc.log(msg='IAGL:  Set game lists to visible script started', level=xbmc.LOGDEBUG)
	lists_to_unhide = []
	current_dialog = xbmcgui.Dialog()
	current_game_list_options = sorted([x for x in zip(iagl_addon_handle.game_lists.list_game_lists(),[(iagl_addon_handle.game_lists.get_game_list(x).get('emu_name'),iagl_addon_handle.game_lists.get_game_list(x).get('emu_visibility')) for x in iagl_addon_handle.game_lists.list_game_lists()]) if x[1][1]=='hidden'],key=lambda x:x[1][0])
	if current_game_list_options:
		current_game_list_ids = ['All']+[x[0] for x in current_game_list_options]
		current_game_list_titles = ['All']+[x[1][0] for x in current_game_list_options]
		new_value = current_dialog.multiselect(loc_str(30360),current_game_list_titles,0)
		if new_value:
			if 0 in new_value:
				lists_to_unhide = current_game_list_ids[1:]
			else:
				lists_to_unhide = [x for ii,x in enumerate(current_game_list_ids) if ii in new_value]
		if lists_to_unhide:
			for ltu in lists_to_unhide:
				current_game_crc = iagl_addon_handle.game_lists.get_crc(ltu)
				update_success = iagl_addon_handle.game_lists.update_game_list_header(ltu,header_key='emu_visibility',header_value='visible',confirm_update=False)
				refresh_success = iagl_addon_handle.refresh_list(current_game_crc)
			iagl_addon_handle.clear_all_mem_cache()
			ok_ret = current_dialog.ok(loc_str(30202),loc_str(30381))
	else:
		ok_ret = current_dialog.ok(loc_str(30202),loc_str(30381))
	del current_dialog
	xbmc.executebuiltin('Container.Refresh')
	clear_mem_cache('iagl_script_started')
	xbmc.log(msg='IAGL:  Set game lists to visible script completed', level=xbmc.LOGDEBUG)
else:
	xbmc.log(msg='IAGL:  Script already running', level=xbmc.LOGDEBUG)
del iagl_addon_handle, loc_str, get_mem_cache, set_mem_cache, clear_mem_cache