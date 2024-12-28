#Internet Archive Game Launcher v4.X
#Zach Morris
#https://github.com/zach-morris/plugin.program.iagl
import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs, json
xbmc.log(msg='IAGL:  Lets Play!',level=xbmc.LOGINFO)
xbmc.log(msg='IAGL:  Version %(addon_version)s'%{'addon_version':xbmcaddon.Addon().getAddonInfo('version')},level=xbmc.LOGDEBUG)
from resources.lib import routing
from resources.lib import config
from resources.lib import database
from resources.lib import download
from resources.lib import netplay
from resources.lib import post_process
from resources.lib import launch
from resources.lib import common
from resources.lib import dialogs
from urllib.parse import unquote
# ## Plugin Initialization Stuff ##
# SLEEP_HACK=50  #https://github.com/xbmc/xbmc/issues/18576
plugin = routing.Plugin()
config = config.config()

cm = common.common(config=config)
db = database.database(config=config,media_type=cm.get_setting('media_type'))
dl = download.download(config=config,ia_email=cm.get_setting('ia_u'),ia_password=cm.get_setting('ia_p'),dl_path=cm.get_setting('default_dl_path'),threads=cm.get_setting('dl_threads'),auto_login=False,if_game_exists=cm.get_setting('if_game_exists'),ige_dialog={'heading':cm.get_loc(30331),'list':[cm.get_loc(30055),cm.get_loc(30056)]}) #Dont login right away for speed, only set the dl path to the current default
nt = netplay.netplay(config=config)
pp = post_process.post_process(config=config)
ln = launch.launch(config=config,user_launch_os=cm.get_setting('user_launch_os'),kodi_suspend=cm.get_setting('kodi_suspend'),kodi_media_stop=cm.get_setting('kodi_media_stop'),kodi_saa=cm.get_setting('kodi_saa'),kodi_wfr=cm.get_setting('kodi_wfr'))
dialogs = dialogs.dialogs(config=config)

# ## Plugin Routes ##
@plugin.route('/')
def route_root():
	xbmc.log(msg='IAGL:  Root',level=xbmc.LOGDEBUG)
	if not cm.get_setting('tou'):
		xbmc.executebuiltin('Dialog.Close(busydialog)')
		TOU_dialog = dialogs.get_tou()
		TOU_dialog.doModal()
		del TOU_dialog
		if not cm.get_setting('tou'):
			xbmc.executebuiltin('Dialog.Close(busydialog)')
			xbmc.sleep(config.defaults.get('sleep'))
			xbmc.executebuiltin('ActivateWindow(home)')
		else:
			check_result = cm.check_db()
			plugin.redirect(cm.get_setting('front_page_display'))
	else:
		check_result = cm.check_db()
		plugin.redirect(cm.get_setting('front_page_display'))

@plugin.route('/browse')
def view_browse():
	xbmc.log(msg='IAGL:  /browse',level=xbmc.LOGDEBUG)
	if not cm.get_setting('wizard_run'):
		if xbmcgui.Dialog().yesno(cm.get_loc(30245),cm.get_loc(30244)):
			plugin.redirect('/wizard_start')
		else:
			xbmcaddon.Addon(id=config.addon.get('addon_name')).setSetting(id='wizard_run',value='true')
			#Browse
			xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
			xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path(item_path),list_item,True) for list_item,item_path in db.query_db(db.get_query('browse')) if isinstance(list_item,xbmcgui.ListItem)])
			if db.get_total_history()>0:
				xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path('/history'),cm.get_history_li(),True)])
			xbmcplugin.endOfDirectory(plugin.handle)
	else:
		#Browse
		xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
		xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path(item_path),list_item,True) for list_item,item_path in db.query_db(db.get_query('browse')) if isinstance(list_item,xbmcgui.ListItem)])
		if db.get_total_history()>0:
			xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path('/history'),cm.get_history_li(),True)])
		xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/all')
def view_all():
	xbmc.log(msg='IAGL:  /all',level=xbmc.LOGDEBUG)
	# choose_from_list will be replaced by setting
	xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
	xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path('{}/{}'.format(item_path,'choose_from_list')),cm.add_context_menu(li=list_item,ip=item_path,type_in='game_list'),True) if isinstance(list_item.getProperty('total_games'),str) and list_item.getProperty('total_games').isdigit() and int(list_item.getProperty('total_games'))>1 else (plugin.url_for_path('{}/{}'.format(item_path,'by_all')),cm.add_context_menu(li=list_item,ip=item_path,type_in='game_list'),True) for list_item,item_path in db.query_db(db.get_query('all_game_lists',game_list_fanart_to_art=cm.get_setting('game_list_fanart_to_art'),game_list_clearlogo_to_art=cm.get_setting('game_list_clearlogo_to_art'))) if isinstance(list_item,xbmcgui.ListItem)])
	for sm in config.listitem.get('sort_methods').get('all'):
		xbmcplugin.addSortMethod(plugin.handle,sm)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/categories')
def view_categories():
	xbmc.log(msg='IAGL:  /categories',level=xbmc.LOGDEBUG)
	xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
	xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path(item_path),list_item,True) for list_item,item_path in db.query_db(db.get_query('categories')) if isinstance(list_item,xbmcgui.ListItem)])
	for sm in config.listitem.get('sort_methods').get('categories'):
		xbmcplugin.addSortMethod(plugin.handle,sm)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/groups')
def view_groups():
	xbmc.log(msg='IAGL:  /groups',level=xbmc.LOGDEBUG)
	xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
	xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path(item_path),list_item,True) for list_item,item_path in db.query_db(db.get_query('playlists')) if isinstance(list_item,xbmcgui.ListItem)])
	for sm in config.listitem.get('sort_methods').get('playlists'):
		xbmcplugin.addSortMethod(plugin.handle,sm)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/by_category/<category_id>')
def view_by_category(category_id):
	if category_id in ['favorites','search','random']:
		plugin.redirect(category_id)
	else:
		xbmc.log(msg='IAGL:  /by_category/{}'.format(category_id),level=xbmc.LOGDEBUG)
		xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
		xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path('{}/{}'.format(item_path,'choose_from_list')),list_item,True) if isinstance(list_item.getProperty('total_games'),str) and list_item.getProperty('total_games').isdigit() and int(list_item.getProperty('total_games'))>1 else (plugin.url_for_path('{}/{}'.format(item_path,'by_all')),list_item,True) for list_item,item_path in db.query_db(db.get_query('game_lists_by_category',category_id=category_id,game_list_fanart_to_art=cm.get_setting('game_list_fanart_to_art'),game_list_clearlogo_to_art=cm.get_setting('game_list_clearlogo_to_art'))) if isinstance(list_item,xbmcgui.ListItem)])
		for sm in config.listitem.get('sort_methods').get('by_category'):
			xbmcplugin.addSortMethod(plugin.handle,sm)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/by_playlist/<playlist_id>')
def view_by_playlist(playlist_id):
	if isinstance(cm.get_setting('games_pagination'),int):
		plugin.redirect('/by_playlist_paged/{}/{}'.format(playlist_id,0))
	else:
		xbmc.log(msg='IAGL:  /by_playlist/{}'.format(playlist_id),level=xbmc.LOGDEBUG)
		xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
		xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path(item_path),cm.add_context_menu(li=list_item,ip=item_path,type_in='game'),False) for list_item,item_path in db.query_db(db.get_query('game_lists_by_playlist_no_page',playlist_id=playlist_id,game_title_setting=cm.get_setting('append_game_list_to_playlist_results_combined'))) if isinstance(list_item,xbmcgui.ListItem)])
		for sm in config.listitem.get('sort_methods').get('by_playlist'):
			xbmcplugin.addSortMethod(plugin.handle,sm)
		xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/by_playlist_paged/<playlist_id>/<page_id>')
def view_by_playlist_paged(playlist_id,page_id):
	if page_id == '0':
		starting_number = 0
		next_page = '1'
	else:
		starting_number = int(page_id)*cm.get_setting('games_pagination')
		next_page = str(int(page_id)+1)
	xbmc.log(msg='IAGL:  /by_playlist_paged/{}/{}'.format(playlist_id,page_id),level=xbmc.LOGDEBUG)
	xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
	page_result = [(plugin.url_for_path(item_path),cm.add_context_menu(li=list_item,ip=item_path,type_in='game'),False) for list_item,item_path in db.query_db(db.get_query('game_lists_by_playlist_page',playlist_id=playlist_id,game_title_setting=cm.get_setting('append_game_list_to_playlist_results_combined'),items_per_page=cm.get_setting('games_pagination'),starting_number=starting_number)) if isinstance(list_item,xbmcgui.ListItem)]
	xbmcplugin.addDirectoryItems(plugin.handle,page_result)
	if len(page_result)==cm.get_setting('games_pagination'):
		xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for(view_by_playlist_paged,playlist_id=playlist_id,page_id=next_page),cm.get_next_li(),True)])
	for sm in config.listitem.get('sort_methods').get('by_playlist'):
		xbmcplugin.addSortMethod(plugin.handle,sm)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/favorites')
def view_favorites():
	xbmc.log(msg='IAGL:  /favorites',level=xbmc.LOGDEBUG)
	if cm.get_setting('favorites_page_display')=='/favorites':
		xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
		xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path('{}/{}'.format('view_favorites',item_path)),list_item,True) for list_item,item_path in db.query_db(db.get_query('browse_favorites')) if isinstance(list_item,xbmcgui.ListItem)])
		xbmcplugin.endOfDirectory(plugin.handle)
	else:
		plugin.redirect(cm.get_setting('favorites_page_display'))

@plugin.route('/view_favorites/<choose_id>')
def view_favorites_by(choose_id):
	xbmc.log(msg='IAGL:  /view_favorites',level=xbmc.LOGDEBUG)
	if choose_id == 'by_all':
		if isinstance(cm.get_setting('games_pagination'),int):
			plugin.redirect('/view_favorites_paged/{}/{}'.format(choose_id,0))
		else:
			xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
			xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path(item_path),cm.add_context_menu(li=list_item,ip=item_path,type_in='remove_fav_game') if 'play_game' in item_path else cm.add_context_menu(li=list_item,ip=item_path,type_in='remove_fav_link'),False if 'play_game' in item_path else True) for list_item,item_path in db.query_db(db.get_query('favorites_by_all_no_page',game_title_setting=cm.get_setting('game_title_setting'),thumbnail_to_game_art=cm.get_setting('thumbnail_to_game_art'),landscape_to_game_art=cm.get_setting('landscape_to_game_art'))) if isinstance(list_item,xbmcgui.ListItem)])
			xbmcplugin.endOfDirectory(plugin.handle)
	else: #by_fav_group
		xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
		xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path('{}/{}'.format('view_favorites_group',item_path)),list_item,True) for list_item,item_path in db.query_db(db.get_query('favorites_by_group')) if isinstance(list_item,xbmcgui.ListItem)])
		for sm in config.listitem.get('sort_methods').get('categories'):
			xbmcplugin.addSortMethod(plugin.handle,sm)
		xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/view_favorites_paged/<choose_id>/<page_id>')
def view_favorites_paged(choose_id,page_id):
	xbmc.log(msg='IAGL:  /view_favorites_paged/{}/{}'.format(choose_id,page_id),level=xbmc.LOGDEBUG)
	xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
	if page_id == '0':
		starting_number = 0
		next_page = '1'
	else:
		starting_number = int(page_id)*cm.get_setting('games_pagination')
		next_page = str(int(page_id)+1)
	if choose_id == 'by_all':
		page_result = [(plugin.url_for_path(item_path),cm.add_context_menu(li=list_item,ip=item_path,type_in='remove_fav_game') if 'play_game' in item_path else cm.add_context_menu(li=list_item,ip=item_path,type_in='remove_fav_link'),False if 'play_game' in item_path else True) for list_item,item_path in db.query_db(db.get_query('favorites_by_all_page',game_title_setting=cm.get_setting('game_title_setting'),thumbnail_to_game_art=cm.get_setting('thumbnail_to_game_art'),landscape_to_game_art=cm.get_setting('landscape_to_game_art'),items_per_page=cm.get_setting('games_pagination'),starting_number=starting_number)) if isinstance(list_item,xbmcgui.ListItem)]
		xbmcplugin.addDirectoryItems(plugin.handle,page_result)
		if len(page_result)==cm.get_setting('games_pagination'):
			xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for(view_favorites_paged,choose_id=choose_id,page_id=next_page),cm.get_next_li(),True)])
		for sm in config.listitem.get('sort_methods').get('games'):
			xbmcplugin.addSortMethod(plugin.handle,sm)
	else:
		xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
		xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path('{}/{}/{}/{}'.format('game_list',game_list_id,choose_id,item_path)),list_item,True) for list_item,item_path in db.query_db(db.get_query(choose_id,game_list_id=game_list_id)) if isinstance(list_item,xbmcgui.ListItem)])
		for sm in config.listitem.get('sort_methods').get('game_list_choice_by'):
			xbmcplugin.addSortMethod(plugin.handle,sm)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/view_favorites_group/<group_id>')
def view_favorites_by(group_id):
	xbmc.log(msg='IAGL:  /view_favorites_group',level=xbmc.LOGDEBUG)
	if isinstance(cm.get_setting('games_pagination'),int):
		plugin.redirect('/view_favorites_group_paged/{}/{}'.format(group_id,0))
	else:
		xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
		xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path(item_path),cm.add_context_menu(li=list_item,ip=item_path,type_in='remove_fav_game') if 'play_game' in item_path else cm.add_context_menu(li=list_item,ip=item_path,type_in='remove_fav_link'),False if 'play_game' in item_path else True) for list_item,item_path in db.query_db(db.get_query('favorites_by_group_no_page',group_id=group_id,game_title_setting=cm.get_setting('game_title_setting'),thumbnail_to_game_art=cm.get_setting('thumbnail_to_game_art'),landscape_to_game_art=cm.get_setting('landscape_to_game_art'))) if isinstance(list_item,xbmcgui.ListItem)])
		xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/view_favorites_group_paged/<group_id>/<page_id>')
def view_favorites_group_paged(group_id,page_id):
	xbmc.log(msg='IAGL:  /view_favorites_group_paged',level=xbmc.LOGDEBUG)
	xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
	if page_id == '0':
		starting_number = 0
		next_page = '1'
	else:
		starting_number = int(page_id)*cm.get_setting('games_pagination')
		next_page = str(int(page_id)+1)
	page_result = [(plugin.url_for_path(item_path),cm.add_context_menu(li=list_item,ip=item_path,type_in='remove_fav_game') if 'play_game' in item_path else cm.add_context_menu(li=list_item,ip=item_path,type_in='remove_fav_link'),False if 'play_game' in item_path else True) for list_item,item_path in db.query_db(db.get_query('favorites_by_group_page',group_id=group_id,game_title_setting=cm.get_setting('game_title_setting'),thumbnail_to_game_art=cm.get_setting('thumbnail_to_game_art'),landscape_to_game_art=cm.get_setting('landscape_to_game_art'),items_per_page=cm.get_setting('games_pagination'),starting_number=starting_number)) if isinstance(list_item,xbmcgui.ListItem)]
	xbmcplugin.addDirectoryItems(plugin.handle,page_result)
	if len(page_result)==cm.get_setting('games_pagination'):
		xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for(view_favorites_group_paged,group_id=group_id,page_id=next_page),cm.get_next_li(),True)])
	for sm in config.listitem.get('sort_methods').get('games'):
		xbmcplugin.addSortMethod(plugin.handle,sm)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/history')
def view_history():
	xbmc.log(msg='IAGL:  /history',level=xbmc.LOGDEBUG)
	xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
	xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path(item_path),cm.add_context_menu(li=list_item,ip=item_path,type_in='game'),False) for list_item,item_path in db.query_db(db.get_query('history_no_page',game_title_setting=cm.get_setting('game_title_setting'),filter_to_1g1r=cm.get_setting('filter_to_1g1r'),thumbnail_to_game_art=cm.get_setting('thumbnail_to_game_art'),landscape_to_game_art=cm.get_setting('landscape_to_game_art'))) if isinstance(list_item,xbmcgui.ListItem)])
	for sm in config.listitem.get('sort_methods').get('history'):
		xbmcplugin.addSortMethod(plugin.handle,sm)
	xbmcplugin.endOfDirectory(plugin.handle)

## Search Routes ##
@plugin.route('/search')
def view_search():
	xbmc.log(msg='IAGL:  /search',level=xbmc.LOGDEBUG)
	xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
	current_search = cm.get_search()
	if isinstance(current_search,dict):
		xbmc.log(msg='IAGL:  Current search parameters: {}'.format(current_search),level=xbmc.LOGDEBUG)
	else:
		xbmc.log(msg='IAGL:  Current search parameters are empty',level=xbmc.LOGDEBUG)
	xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path(item_path),cm.update_search_listitem(current_search=current_search,list_item_in=list_item,path_in=item_path),True) for list_item,item_path in db.query_db(db.get_query('search')) if isinstance(list_item,xbmcgui.ListItem)])
	for sm in config.listitem.get('sort_methods').get('search'):
		xbmcplugin.addSortMethod(plugin.handle,sm)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/search_enter_game_lists')
def search_enter_game_lists():
	xbmc.log(msg='IAGL:  /search_enter_game_lists',level=xbmc.LOGDEBUG)
	li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_get_game_lists'))if isinstance(list_item,xbmcgui.ListItem)]
	selected = xbmcgui.Dialog().multiselect(heading=cm.get_loc(30024),options=li,useDetails=True) 
	if isinstance(selected,list):
		xbmc.log(msg='IAGL:  Game lists select in search: {}'.format([x.getLabel() for ii,x in enumerate(li) if ii in selected]),level=xbmc.LOGDEBUG)
		result = cm.update_search(game_lists=[x.getLabel() for ii,x in enumerate(li) if ii in selected])
	else:
		xbmc.log(msg='IAGL:  Game list select cancelled',level=xbmc.LOGDEBUG)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/reset_all_search')
def reset_all_search():
	xbmc.log(msg='IAGL:  /reset_all_search',level=xbmc.LOGDEBUG)
	result = cm.clear_search()
	if result:
		xbmc.sleep(config.defaults.get('sleep'))
		xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/reset_search_enter_game_lists')
def reset_search_enter_game_lists():
	xbmc.log(msg='IAGL:  /reset_search_enter_game_lists',level=xbmc.LOGDEBUG)
	result = cm.update_search(game_lists=None)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/search_enter_game_title')
def search_enter_game_title():
	xbmc.log(msg='IAGL:  /search_enter_game_title',level=xbmc.LOGDEBUG)
	selected = xbmcgui.Dialog().input(heading=cm.get_loc(30226))
	if isinstance(selected,str) and len(selected)>0:
		result = cm.update_search(title=selected)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/reset_search_enter_game_title')
def reset_search_enter_game_title():
	xbmc.log(msg='IAGL:  /reset_search_enter_game_title',level=xbmc.LOGDEBUG)
	result = cm.update_search(title=None)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/search_filter_genre')
def search_filter_genre():
	xbmc.log(msg='IAGL:  /search_filter_genre',level=xbmc.LOGDEBUG)
	if isinstance(cm.get_search(),dict) and isinstance(cm.get_search().get('game_lists'),list):
		game_list_query = 'LIKE '+' OR choose_table.matching_lists LIKE '.join(['"%""{}""%"'.format(x) for x in cm.get_search().get('game_lists') if isinstance(x,str)])
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_matching_lists',table_select='genre',game_list_query=game_list_query))if isinstance(list_item,xbmcgui.ListItem)]
	else:
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_all',table_select='genre'))if isinstance(list_item,xbmcgui.ListItem)]
	selected = xbmcgui.Dialog().multiselect(heading=cm.get_loc(30026),options=li,useDetails=True) 
	if isinstance(selected,list):
		xbmc.log(msg='IAGL:  Game genres select in search: {}'.format([x.getLabel() for ii,x in enumerate(li) if ii in selected]),level=xbmc.LOGDEBUG)
		result = cm.update_search(genres=[x.getLabel() for ii,x in enumerate(li) if ii in selected])
	else:
		xbmc.log(msg='IAGL:  Game genres select cancelled',level=xbmc.LOGDEBUG)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/reset_search_filter_genre')
def reset_search_filter_genre():
	xbmc.log(msg='IAGL:  /reset_search_filter_genre',level=xbmc.LOGDEBUG)
	result = cm.update_search(genres=None)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/search_filter_nplayers')
def search_filter_nplayers():
	xbmc.log(msg='IAGL:  /search_filter_nplayers',level=xbmc.LOGDEBUG)
	if isinstance(cm.get_search(),dict) and isinstance(cm.get_search().get('game_lists'),list):
		game_list_query = 'LIKE '+' OR choose_table.matching_lists LIKE '.join(['"%""{}""%"'.format(x) for x in cm.get_search().get('game_lists') if isinstance(x,str)])
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_matching_lists',table_select='nplayers',game_list_query=game_list_query))if isinstance(list_item,xbmcgui.ListItem)]
	else:
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_all',table_select='nplayers'))if isinstance(list_item,xbmcgui.ListItem)]
	selected = xbmcgui.Dialog().multiselect(heading=cm.get_loc(30027),options=li,useDetails=True) 
	if isinstance(selected,list):
		xbmc.log(msg='IAGL:  Game nplayers select in search: {}'.format([x.getLabel() for ii,x in enumerate(li) if ii in selected]),level=xbmc.LOGDEBUG)
		result = cm.update_search(nplayers=[x.getLabel() for ii,x in enumerate(li) if ii in selected])
	else:
		xbmc.log(msg='IAGL:  Game nplayers select cancelled',level=xbmc.LOGDEBUG)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/reset_search_filter_nplayers')
def reset_search_filter_nplayers():
	xbmc.log(msg='IAGL:  /reset_search_filter_nplayers',level=xbmc.LOGDEBUG)
	result = cm.update_search(nplayers=None)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/search_filter_studio')
def search_filter_studio():
	xbmc.log(msg='IAGL:  /search_filter_studio',level=xbmc.LOGDEBUG)
	if isinstance(cm.get_search(),dict) and isinstance(cm.get_search().get('game_lists'),list):
		game_list_query = 'LIKE '+' OR choose_table.matching_lists LIKE '.join(['"%""{}""%"'.format(x) for x in cm.get_search().get('game_lists') if isinstance(x,str)])
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_matching_lists',table_select='studio',game_list_query=game_list_query))if isinstance(list_item,xbmcgui.ListItem)]
	else:
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_all',table_select='studio'))if isinstance(list_item,xbmcgui.ListItem)]
	selected = xbmcgui.Dialog().multiselect(heading=cm.get_loc(30028),options=li,useDetails=True) 
	if isinstance(selected,list):
		xbmc.log(msg='IAGL:  Game studios select in search: {}'.format([x.getLabel() for ii,x in enumerate(li) if ii in selected]),level=xbmc.LOGDEBUG)
		result = cm.update_search(studios=[x.getLabel() for ii,x in enumerate(li) if ii in selected])
	else:
		xbmc.log(msg='IAGL:  Game studios select cancelled',level=xbmc.LOGDEBUG)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/reset_search_filter_studio')
def reset_search_filter_studio():
	xbmc.log(msg='IAGL:  /reset_search_filter_studio',level=xbmc.LOGDEBUG)
	result = cm.update_search(studios=None)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/search_filter_tag')
def search_filter_tag():
	xbmc.log(msg='IAGL:  /search_filter_tag',level=xbmc.LOGDEBUG)
	if isinstance(cm.get_search(),dict) and isinstance(cm.get_search().get('game_lists'),list):
		game_list_query = 'LIKE '+' OR choose_table.matching_lists LIKE '.join(['"%""{}""%"'.format(x) for x in cm.get_search().get('game_lists') if isinstance(x,str)])
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_matching_lists',table_select='tag',game_list_query=game_list_query))if isinstance(list_item,xbmcgui.ListItem)]
	else:
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_all',table_select='tag'))if isinstance(list_item,xbmcgui.ListItem)]
	selected = xbmcgui.Dialog().multiselect(heading=cm.get_loc(30029),options=li,useDetails=True) 
	if isinstance(selected,list):
		xbmc.log(msg='IAGL:  Game tags select in search: {}'.format([x.getLabel() for ii,x in enumerate(li) if ii in selected]),level=xbmc.LOGDEBUG)
		result = cm.update_search(tags=[x.getLabel() for ii,x in enumerate(li) if ii in selected])
	else:
		xbmc.log(msg='IAGL:  Game tags select cancelled',level=xbmc.LOGDEBUG)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/reset_search_filter_tag')
def reset_search_filter_tag():
	xbmc.log(msg='IAGL:  /reset_search_filter_tag',level=xbmc.LOGDEBUG)
	result = cm.update_search(tags=None)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/search_filter_playlist')
def search_filter_playlist():
	xbmc.log(msg='IAGL:  /search_filter_playlist',level=xbmc.LOGDEBUG)
	if isinstance(cm.get_search(),dict) and isinstance(cm.get_search().get('game_lists'),list):
		game_list_query = 'LIKE '+' OR choose_table.matching_lists LIKE '.join(['"%""{}""%"'.format(x) for x in cm.get_search().get('game_lists') if isinstance(x,str)])
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_matching_lists',table_select='groups',game_list_query=game_list_query))if isinstance(list_item,xbmcgui.ListItem)]
	else:
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_all',table_select='groups'))if isinstance(list_item,xbmcgui.ListItem)]
	selected = xbmcgui.Dialog().multiselect(heading=cm.get_loc(30030),options=li,useDetails=True) 
	if isinstance(selected,list):
		xbmc.log(msg='IAGL:  Game playlists select in search: {}'.format([x.getLabel() for ii,x in enumerate(li) if ii in selected]),level=xbmc.LOGDEBUG)
		result = cm.update_search(playlists=[x.getLabel() for ii,x in enumerate(li) if ii in selected])
	else:
		xbmc.log(msg='IAGL:  Game playlists select cancelled',level=xbmc.LOGDEBUG)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/reset_search_filter_playlist')
def reset_search_filter_playlist():
	xbmc.log(msg='IAGL:  /reset_search_filter_playlist',level=xbmc.LOGDEBUG)
	result = cm.update_search(playlists=None)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/search_filter_region')
def search_filter_region():
	xbmc.log(msg='IAGL:  /search_filter_region',level=xbmc.LOGDEBUG)
	if isinstance(cm.get_search(),dict) and isinstance(cm.get_search().get('game_lists'),list):
		game_list_query = 'LIKE '+' OR choose_table.matching_lists LIKE '.join(['"%""{}""%"'.format(x) for x in cm.get_search().get('game_lists') if isinstance(x,str)])
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_matching_lists',table_select='region',game_list_query=game_list_query))if isinstance(list_item,xbmcgui.ListItem)]
	else:
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_all',table_select='region'))if isinstance(list_item,xbmcgui.ListItem)]
	selected = xbmcgui.Dialog().multiselect(heading=cm.get_loc(30031),options=li,useDetails=True) 
	if isinstance(selected,list):
		xbmc.log(msg='IAGL:  Game regions select in search: {}'.format([x.getLabel() for ii,x in enumerate(li) if ii in selected]),level=xbmc.LOGDEBUG)
		result = cm.update_search(regions=[x.getLabel() for ii,x in enumerate(li) if ii in selected])
	else:
		xbmc.log(msg='IAGL:  Game regions select cancelled',level=xbmc.LOGDEBUG)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/reset_search_filter_region')
def reset_search_filter_region():
	xbmc.log(msg='IAGL:  /reset_search_filter_region',level=xbmc.LOGDEBUG)
	result = cm.update_search(regions=None)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/search_filter_language')
def search_filter_language():
	xbmc.log(msg='IAGL:  /search_filter_language',level=xbmc.LOGDEBUG)
	if isinstance(cm.get_search(),dict) and isinstance(cm.get_search().get('game_lists'),list):
		game_list_query = 'LIKE '+' OR choose_table.matching_lists LIKE '.join(['"%""{}""%"'.format(x) for x in cm.get_search().get('game_lists') if isinstance(x,str)])
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_matching_lists',table_select='language',game_list_query=game_list_query))if isinstance(list_item,xbmcgui.ListItem)]
	else:
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_all',table_select='language'))if isinstance(list_item,xbmcgui.ListItem)]
	selected = xbmcgui.Dialog().multiselect(heading=cm.get_loc(30032),options=li,useDetails=True) 
	if isinstance(selected,list):
		xbmc.log(msg='IAGL:  Game languages select in search: {}'.format([x.getLabel() for ii,x in enumerate(li) if ii in selected]),level=xbmc.LOGDEBUG)
		result = cm.update_search(languages=[x.getLabel() for ii,x in enumerate(li) if ii in selected])
	else:
		xbmc.log(msg='IAGL:  Game languages select cancelled',level=xbmc.LOGDEBUG)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/reset_search_filter_language')
def reset_search_filter_language():
	xbmc.log(msg='IAGL:  /reset_search_filter_language',level=xbmc.LOGDEBUG)
	result = cm.update_search(languages=None)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/search_filter_edition')
def search_filter_edition():
	xbmc.log(msg='IAGL:  /search_filter_edition',level=xbmc.LOGDEBUG)
	if isinstance(cm.get_search(),dict) and isinstance(cm.get_search().get('game_lists'),list):
		game_list_query = 'LIKE '+' OR choose_table.matching_lists LIKE '.join(['"%""{}""%"'.format(x) for x in cm.get_search().get('game_lists') if isinstance(x,str)])
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_matching_lists',table_select='edition',game_list_query=game_list_query))if isinstance(list_item,xbmcgui.ListItem)]
	else:
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_all',table_select='edition'))if isinstance(list_item,xbmcgui.ListItem)]
	selected = xbmcgui.Dialog().multiselect(heading=cm.get_loc(30033),options=li,useDetails=True) 
	if isinstance(selected,list):
		xbmc.log(msg='IAGL:  Game editions select in search: {}'.format([x.getLabel() for ii,x in enumerate(li) if ii in selected]),level=xbmc.LOGDEBUG)
		result = cm.update_search(editions=[x.getLabel() for ii,x in enumerate(li) if ii in selected])
	else:
		xbmc.log(msg='IAGL:  Game editions select cancelled',level=xbmc.LOGDEBUG)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/reset_search_filter_edition')
def reset_search_filter_edition():
	xbmc.log(msg='IAGL:  /reset_search_filter_edition',level=xbmc.LOGDEBUG)
	result = cm.update_search(editions=None)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/search_filter_code')
def search_filter_code():
	xbmc.log(msg='IAGL:  /search_filter_code',level=xbmc.LOGDEBUG)
	if isinstance(cm.get_search(),dict) and isinstance(cm.get_search().get('game_lists'),list):
		game_list_query = 'LIKE '+' OR choose_table.matching_lists LIKE '.join(['"%""{}""%"'.format(x) for x in cm.get_search().get('game_lists') if isinstance(x,str)])
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_matching_lists',table_select='code',game_list_query=game_list_query))if isinstance(list_item,xbmcgui.ListItem)]
	else:
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_all',table_select='code'))if isinstance(list_item,xbmcgui.ListItem)]
	selected = xbmcgui.Dialog().multiselect(heading=cm.get_loc(30034),options=li,useDetails=True) 
	if isinstance(selected,list):
		xbmc.log(msg='IAGL:  Game codes select in search: {}'.format([x.getLabel() for ii,x in enumerate(li) if ii in selected]),level=xbmc.LOGDEBUG)
		result = cm.update_search(codes=[x.getLabel() for ii,x in enumerate(li) if ii in selected])
	else:
		xbmc.log(msg='IAGL:  Game codes select cancelled',level=xbmc.LOGDEBUG)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/reset_search_filter_code')
def reset_search_filter_code():
	xbmc.log(msg='IAGL:  /reset_search_filter_code',level=xbmc.LOGDEBUG)
	result = cm.update_search(codes=None)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/search_filter_rating')
def search_filter_rating():
	xbmc.log(msg='IAGL:  /search_filter_rating',level=xbmc.LOGDEBUG)
	if isinstance(cm.get_search(),dict) and isinstance(cm.get_search().get('game_lists'),list):
		game_list_query = 'LIKE '+' OR choose_table.matching_lists LIKE '.join(['"%""{}""%"'.format(x) for x in cm.get_search().get('game_lists') if isinstance(x,str)])
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_matching_lists',table_select='rating',game_list_query=game_list_query))if isinstance(list_item,xbmcgui.ListItem)]
	else:
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_all',table_select='rating'))if isinstance(list_item,xbmcgui.ListItem)]
	selected = xbmcgui.Dialog().multiselect(heading=cm.get_loc(30035),options=li,useDetails=True) 
	if isinstance(selected,list):
		xbmc.log(msg='IAGL:  Game ratings select in search: {}'.format([x.getLabel() for ii,x in enumerate(li) if ii in selected]),level=xbmc.LOGDEBUG)
		result = cm.update_search(ratings=[x.getLabel() for ii,x in enumerate(li) if ii in selected])
	else:
		xbmc.log(msg='IAGL:  Game ratings select cancelled',level=xbmc.LOGDEBUG)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/reset_search_filter_rating')
def reset_search_filter_rating():
	xbmc.log(msg='IAGL:  /reset_search_filter_rating',level=xbmc.LOGDEBUG)
	result = cm.update_search(ratings=None)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/execute_search')
def execute_search():
	xbmc.log(msg='IAGL:  /execute_search',level=xbmc.LOGDEBUG)
	game_search_query = cm.get_search_query()
	if isinstance(game_search_query,str):
		xbmc.log(msg='IAGL:  Current search parameters: {}'.format(cm.get_search()),level=xbmc.LOGDEBUG)
		xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
		xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path(item_path),cm.add_context_menu(li=list_item,ip=item_path,type_in='game'),False) for list_item,item_path in db.query_db(db.get_query('search_games',game_search_query=game_search_query,game_title_setting=cm.get_setting('append_game_list_to_search_results_combined'))) if isinstance(list_item,xbmcgui.ListItem)])
		for sm in config.listitem.get('sort_methods').get('games'):
			xbmcplugin.addSortMethod(plugin.handle,sm)
		xbmcplugin.endOfDirectory(plugin.handle)
	else:
		xbmc.log(msg='IAGL:  Current search parameters are empty',level=xbmc.LOGDEBUG)
		ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30227),cm.get_loc(30228))
		xbmc.sleep(config.defaults.get('sleep'))
		xbmc.executebuiltin('Container.Refresh')

@plugin.route('/generate_search_link')
def generate_search_link():
	xbmc.log(msg='IAGL:  /generate_search_link',level=xbmc.LOGDEBUG)
	current_search = cm.get_search()
	if isinstance(current_search,dict) and len(list(current_search.keys()))>0:
		selected = xbmcgui.Dialog().input(heading=cm.get_loc(30230))
		if isinstance(selected,str) and len(selected)>0:
			xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
			xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for(search_from_link,query=json.dumps(current_search)),cm.add_context_menu(li=xbmcgui.ListItem(selected,offscreen=True),type_in='search_link',ip=selected),True)])
			xbmcplugin.endOfDirectory(plugin.handle)
		else:
			xbmc.sleep(config.defaults.get('sleep'))
			xbmc.executebuiltin('Container.Refresh')
	else:
		xbmc.log(msg='IAGL:  Current search parameters are empty',level=xbmc.LOGDEBUG)
		ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30227),cm.get_loc(30228))
		xbmc.sleep(config.defaults.get('sleep'))
		xbmc.executebuiltin('Container.Refresh')

@plugin.route('/search_from_link')
def search_from_link():
	xbmc.log(msg='IAGL:  /search_from_link',level=xbmc.LOGDEBUG)
	cc = next(iter(plugin.args.get('query')),None)
	if isinstance(cc,str):
		game_search_query = cm.get_search_query(current_search_in=json.loads(cc))
		xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
		xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path(item_path),cm.add_context_menu(li=list_item,ip=item_path,type_in='game'),False) for list_item,item_path in db.query_db(db.get_query('search_games',game_search_query=game_search_query,game_title_setting=cm.get_setting('append_game_list_to_search_results_combined'))) if isinstance(list_item,xbmcgui.ListItem)])
		for sm in config.listitem.get('sort_methods').get('games'):
			xbmcplugin.addSortMethod(plugin.handle,sm)
		xbmcplugin.endOfDirectory(plugin.handle)
	else:
		if previous_path.startswith('plugin://plugin.program.iagl/search_from_link'): #User came from a favorite, return home after selecting parent path
			xbmc.sleep(config.defaults.get('sleep'))
			xbmc.executebuiltin('Dialog.Close(busydialog)')
			xbmc.executebuiltin('ActivateWindow(home)')
		else:
			xbmc.log(msg='IAGL:  Unknown previous path {}'.format(previous_path), level=xbmc.LOGDEBUG)
			plugin.redirect('/')
## End Search Routes ##

## Random Routes ##
@plugin.route('/random')
def view_random():
	xbmc.log(msg='IAGL:  /random',level=xbmc.LOGDEBUG)
	xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
	current_search = cm.get_random()
	if isinstance(current_search,dict):
		xbmc.log(msg='IAGL:  Current random parameters: {}'.format(current_search),level=xbmc.LOGDEBUG)
	else:
		xbmc.log(msg='IAGL:  Current random parameters are empty',level=xbmc.LOGDEBUG)
	xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path(item_path),cm.update_random_listitem(current_search=current_search,list_item_in=list_item,path_in=item_path),True) for list_item,item_path in db.query_db(db.get_query('random')) if isinstance(list_item,xbmcgui.ListItem)])
	for sm in config.listitem.get('sort_methods').get('search'):
		xbmcplugin.addSortMethod(plugin.handle,sm)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/context_menu/action/reset_all_random')
def reset_all_random():
	xbmc.log(msg='IAGL:  /reset_all_random',level=xbmc.LOGDEBUG)
	result = cm.clear_random()
	if result:
		xbmc.sleep(config.defaults.get('sleep'))
		xbmc.executebuiltin('Container.Refresh')

@plugin.route('/random_enter_game_lists')
def random_enter_game_lists():
	xbmc.log(msg='IAGL:  /random_enter_game_lists',level=xbmc.LOGDEBUG)
	li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_get_game_lists')) if isinstance(list_item,xbmcgui.ListItem)]
	selected = xbmcgui.Dialog().multiselect(heading=cm.get_loc(30024),options=li,useDetails=True) 
	if isinstance(selected,list):
		xbmc.log(msg='IAGL:  Game lists select in random: {}'.format([x.getLabel() for ii,x in enumerate(li) if ii in selected]),level=xbmc.LOGDEBUG)
		result = cm.update_random(game_lists=[x.getLabel() for ii,x in enumerate(li) if ii in selected])
	else:
		xbmc.log(msg='IAGL:  Game list select cancelled',level=xbmc.LOGDEBUG)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/random_enter_num_results')
def random_enter_game_lists():
	xbmc.log(msg='IAGL:  /random_enter_num_results',level=xbmc.LOGDEBUG)
	number_options = [str(x) for x in config.defaults.get('infinite_results_char')+config.defaults.get('random_num_result_options')]
	default_option = number_options.index(config.defaults.get('default_num_results'))
	li = [xbmcgui.ListItem(x,offscreen=True) for x in number_options]
	selected = xbmcgui.Dialog().select(heading=cm.get_loc(30038),list=li,useDetails=False,preselect=default_option)
	if isinstance(selected,int):
		if number_options[selected].isdigit():
			xbmc.log(msg='IAGL:  Number of results selected in random: {}'.format(number_options[selected]),level=xbmc.LOGDEBUG)
			result = cm.update_random(num_results=number_options[selected])
		else:
			xbmc.log(msg='IAGL:  Number of results selected in random: {}'.format('All'),level=xbmc.LOGDEBUG)
			result = cm.update_random(num_results='All')
	else:
		xbmc.log(msg='IAGL:  Game list select cancelled',level=xbmc.LOGDEBUG)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/reset_random_enter_num_results')
def reset_random_enter_num_results():
	xbmc.log(msg='IAGL:  /reset_random_enter_num_results',level=xbmc.LOGDEBUG)
	result = cm.update_random(num_results=None)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/reset_random_enter_game_lists')
def reset_random_enter_game_lists():
	xbmc.log(msg='IAGL:  /reset_random_enter_game_lists',level=xbmc.LOGDEBUG)
	result = cm.update_random(game_lists=None)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/random_enter_game_title')
def random_enter_game_title():
	xbmc.log(msg='IAGL:  /random_enter_game_title',level=xbmc.LOGDEBUG)
	selected = xbmcgui.Dialog().input(heading=cm.get_loc(30226))
	if isinstance(selected,str) and len(selected)>0:
		result = cm.update_random(title=selected)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/reset_random_enter_game_title')
def reset_random_enter_game_title():
	xbmc.log(msg='IAGL:  /reset_random_enter_game_title',level=xbmc.LOGDEBUG)
	result = cm.update_random(title=None)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/random_filter_genre')
def random_filter_genre():
	xbmc.log(msg='IAGL:  /random_filter_genre',level=xbmc.LOGDEBUG)
	if isinstance(cm.get_random(),dict) and isinstance(cm.get_random().get('game_lists'),list):
		game_list_query = 'LIKE '+' OR choose_table.matching_lists LIKE '.join(['"%""{}""%"'.format(x) for x in cm.get_random().get('game_lists') if isinstance(x,str)])
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_matching_lists',table_select='genre',game_list_query=game_list_query))if isinstance(list_item,xbmcgui.ListItem)]
	else:
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_all',table_select='genre'))if isinstance(list_item,xbmcgui.ListItem)]
	selected = xbmcgui.Dialog().multiselect(heading=cm.get_loc(30026),options=li,useDetails=True) 
	if isinstance(selected,list):
		xbmc.log(msg='IAGL:  Game genres select in random: {}'.format([x.getLabel() for ii,x in enumerate(li) if ii in selected]),level=xbmc.LOGDEBUG)
		result = cm.update_random(genres=[x.getLabel() for ii,x in enumerate(li) if ii in selected])
	else:
		xbmc.log(msg='IAGL:  Game genres select cancelled',level=xbmc.LOGDEBUG)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/reset_random_filter_genre')
def reset_random_filter_genre():
	xbmc.log(msg='IAGL:  /reset_random_filter_genre',level=xbmc.LOGDEBUG)
	result = cm.update_random(genres=None)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/random_filter_nplayers')
def random_filter_nplayers():
	xbmc.log(msg='IAGL:  /random_filter_nplayers',level=xbmc.LOGDEBUG)
	if isinstance(cm.get_random(),dict) and isinstance(cm.get_random().get('game_lists'),list):
		game_list_query = 'LIKE '+' OR choose_table.matching_lists LIKE '.join(['"%""{}""%"'.format(x) for x in cm.get_random().get('game_lists') if isinstance(x,str)])
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_matching_lists',table_select='nplayers',game_list_query=game_list_query))if isinstance(list_item,xbmcgui.ListItem)]
	else:
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_all',table_select='nplayers'))if isinstance(list_item,xbmcgui.ListItem)]
	selected = xbmcgui.Dialog().multiselect(heading=cm.get_loc(30027),options=li,useDetails=True) 
	if isinstance(selected,list):
		xbmc.log(msg='IAGL:  Game nplayers select in random: {}'.format([x.getLabel() for ii,x in enumerate(li) if ii in selected]),level=xbmc.LOGDEBUG)
		result = cm.update_random(nplayers=[x.getLabel() for ii,x in enumerate(li) if ii in selected])
	else:
		xbmc.log(msg='IAGL:  Game nplayers select cancelled',level=xbmc.LOGDEBUG)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/reset_random_filter_nplayers')
def reset_random_filter_nplayers():
	xbmc.log(msg='IAGL:  /reset_random_filter_nplayers',level=xbmc.LOGDEBUG)
	result = cm.update_random(nplayers=None)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/random_filter_studio')
def random_filter_studio():
	xbmc.log(msg='IAGL:  /random_filter_studio',level=xbmc.LOGDEBUG)
	if isinstance(cm.get_random(),dict) and isinstance(cm.get_random().get('game_lists'),list):
		game_list_query = 'LIKE '+' OR choose_table.matching_lists LIKE '.join(['"%""{}""%"'.format(x) for x in cm.get_random().get('game_lists') if isinstance(x,str)])
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_matching_lists',table_select='studio',game_list_query=game_list_query))if isinstance(list_item,xbmcgui.ListItem)]
	else:
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_all',table_select='studio'))if isinstance(list_item,xbmcgui.ListItem)]
	selected = xbmcgui.Dialog().multiselect(heading=cm.get_loc(30028),options=li,useDetails=True) 
	if isinstance(selected,list):
		xbmc.log(msg='IAGL:  Game studios select in random: {}'.format([x.getLabel() for ii,x in enumerate(li) if ii in selected]),level=xbmc.LOGDEBUG)
		result = cm.update_random(studios=[x.getLabel() for ii,x in enumerate(li) if ii in selected])
	else:
		xbmc.log(msg='IAGL:  Game studios select cancelled',level=xbmc.LOGDEBUG)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/reset_random_filter_studio')
def reset_random_filter_studio():
	xbmc.log(msg='IAGL:  /reset_random_filter_studio',level=xbmc.LOGDEBUG)
	result = cm.update_random(studios=None)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/random_filter_tag')
def random_filter_tag():
	xbmc.log(msg='IAGL:  /random_filter_tag',level=xbmc.LOGDEBUG)
	if isinstance(cm.get_random(),dict) and isinstance(cm.get_random().get('game_lists'),list):
		game_list_query = 'LIKE '+' OR choose_table.matching_lists LIKE '.join(['"%""{}""%"'.format(x) for x in cm.get_random().get('game_lists') if isinstance(x,str)])
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_matching_lists',table_select='tag',game_list_query=game_list_query))if isinstance(list_item,xbmcgui.ListItem)]
	else:
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_all',table_select='tag'))if isinstance(list_item,xbmcgui.ListItem)]
	selected = xbmcgui.Dialog().multiselect(heading=cm.get_loc(30029),options=li,useDetails=True) 
	if isinstance(selected,list):
		xbmc.log(msg='IAGL:  Game tags select in random: {}'.format([x.getLabel() for ii,x in enumerate(li) if ii in selected]),level=xbmc.LOGDEBUG)
		result = cm.update_random(tags=[x.getLabel() for ii,x in enumerate(li) if ii in selected])
	else:
		xbmc.log(msg='IAGL:  Game tags select cancelled',level=xbmc.LOGDEBUG)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/reset_random_filter_tag')
def reset_random_filter_tag():
	xbmc.log(msg='IAGL:  /reset_random_filter_tag',level=xbmc.LOGDEBUG)
	result = cm.update_random(tags=None)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/random_filter_playlist')
def random_filter_playlist():
	xbmc.log(msg='IAGL:  /random_filter_playlist',level=xbmc.LOGDEBUG)
	if isinstance(cm.get_random(),dict) and isinstance(cm.get_random().get('game_lists'),list):
		game_list_query = 'LIKE '+' OR choose_table.matching_lists LIKE '.join(['"%""{}""%"'.format(x) for x in cm.get_random().get('game_lists') if isinstance(x,str)])
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_matching_lists',table_select='groups',game_list_query=game_list_query))if isinstance(list_item,xbmcgui.ListItem)]
	else:
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_all',table_select='groups'))if isinstance(list_item,xbmcgui.ListItem)]
	selected = xbmcgui.Dialog().multiselect(heading=cm.get_loc(30030),options=li,useDetails=True) 
	if isinstance(selected,list):
		xbmc.log(msg='IAGL:  Game playlists select in random: {}'.format([x.getLabel() for ii,x in enumerate(li) if ii in selected]),level=xbmc.LOGDEBUG)
		result = cm.update_random(playlists=[x.getLabel() for ii,x in enumerate(li) if ii in selected])
	else:
		xbmc.log(msg='IAGL:  Game playlists select cancelled',level=xbmc.LOGDEBUG)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/reset_random_filter_playlist')
def reset_random_filter_playlist():
	xbmc.log(msg='IAGL:  /reset_random_filter_playlist',level=xbmc.LOGDEBUG)
	result = cm.update_random(playlists=None)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/random_filter_region')
def random_filter_region():
	xbmc.log(msg='IAGL:  /random_filter_region',level=xbmc.LOGDEBUG)
	if isinstance(cm.get_random(),dict) and isinstance(cm.get_random().get('game_lists'),list):
		game_list_query = 'LIKE '+' OR choose_table.matching_lists LIKE '.join(['"%""{}""%"'.format(x) for x in cm.get_random().get('game_lists') if isinstance(x,str)])
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_matching_lists',table_select='region',game_list_query=game_list_query))if isinstance(list_item,xbmcgui.ListItem)]
	else:
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_all',table_select='region'))if isinstance(list_item,xbmcgui.ListItem)]
	selected = xbmcgui.Dialog().multiselect(heading=cm.get_loc(30031),options=li,useDetails=True) 
	if isinstance(selected,list):
		xbmc.log(msg='IAGL:  Game regions select in random: {}'.format([x.getLabel() for ii,x in enumerate(li) if ii in selected]),level=xbmc.LOGDEBUG)
		result = cm.update_random(regions=[x.getLabel() for ii,x in enumerate(li) if ii in selected])
	else:
		xbmc.log(msg='IAGL:  Game regions select cancelled',level=xbmc.LOGDEBUG)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/reset_random_filter_region')
def reset_random_filter_region():
	xbmc.log(msg='IAGL:  /reset_random_filter_region',level=xbmc.LOGDEBUG)
	result = cm.update_random(regions=None)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/random_filter_language')
def random_filter_language():
	xbmc.log(msg='IAGL:  /random_filter_language',level=xbmc.LOGDEBUG)
	if isinstance(cm.get_random(),dict) and isinstance(cm.get_random().get('game_lists'),list):
		game_list_query = 'LIKE '+' OR choose_table.matching_lists LIKE '.join(['"%""{}""%"'.format(x) for x in cm.get_random().get('game_lists') if isinstance(x,str)])
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_matching_lists',table_select='language',game_list_query=game_list_query))if isinstance(list_item,xbmcgui.ListItem)]
	else:
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_all',table_select='language'))if isinstance(list_item,xbmcgui.ListItem)]
	selected = xbmcgui.Dialog().multiselect(heading=cm.get_loc(30032),options=li,useDetails=True) 
	if isinstance(selected,list):
		xbmc.log(msg='IAGL:  Game languages select in random: {}'.format([x.getLabel() for ii,x in enumerate(li) if ii in selected]),level=xbmc.LOGDEBUG)
		result = cm.update_random(languages=[x.getLabel() for ii,x in enumerate(li) if ii in selected])
	else:
		xbmc.log(msg='IAGL:  Game languages select cancelled',level=xbmc.LOGDEBUG)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/reset_random_filter_language')
def reset_random_filter_language():
	xbmc.log(msg='IAGL:  /reset_random_filter_language',level=xbmc.LOGDEBUG)
	result = cm.update_random(languages=None)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/random_filter_edition')
def random_filter_edition():
	xbmc.log(msg='IAGL:  /random_filter_edition',level=xbmc.LOGDEBUG)
	if isinstance(cm.get_random(),dict) and isinstance(cm.get_random().get('game_lists'),list):
		game_list_query = 'LIKE '+' OR choose_table.matching_lists LIKE '.join(['"%""{}""%"'.format(x) for x in cm.get_random().get('game_lists') if isinstance(x,str)])
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_matching_lists',table_select='edition',game_list_query=game_list_query))if isinstance(list_item,xbmcgui.ListItem)]
	else:
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_all',table_select='edition'))if isinstance(list_item,xbmcgui.ListItem)]
	selected = xbmcgui.Dialog().multiselect(heading=cm.get_loc(30033),options=li,useDetails=True) 
	if isinstance(selected,list):
		xbmc.log(msg='IAGL:  Game editions select in random: {}'.format([x.getLabel() for ii,x in enumerate(li) if ii in selected]),level=xbmc.LOGDEBUG)
		result = cm.update_random(editions=[x.getLabel() for ii,x in enumerate(li) if ii in selected])
	else:
		xbmc.log(msg='IAGL:  Game editions select cancelled',level=xbmc.LOGDEBUG)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/reset_random_filter_edition')
def reset_random_filter_edition():
	xbmc.log(msg='IAGL:  /reset_random_filter_edition',level=xbmc.LOGDEBUG)
	result = cm.update_random(editions=None)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/random_filter_code')
def random_filter_code():
	xbmc.log(msg='IAGL:  /random_filter_code',level=xbmc.LOGDEBUG)
	if isinstance(cm.get_random(),dict) and isinstance(cm.get_random().get('game_lists'),list):
		game_list_query = 'LIKE '+' OR choose_table.matching_lists LIKE '.join(['"%""{}""%"'.format(x) for x in cm.get_random().get('game_lists') if isinstance(x,str)])
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_matching_lists',table_select='code',game_list_query=game_list_query))if isinstance(list_item,xbmcgui.ListItem)]
	else:
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_all',table_select='code'))if isinstance(list_item,xbmcgui.ListItem)]
	selected = xbmcgui.Dialog().multiselect(heading=cm.get_loc(30034),options=li,useDetails=True) 
	if isinstance(selected,list):
		xbmc.log(msg='IAGL:  Game codes select in random: {}'.format([x.getLabel() for ii,x in enumerate(li) if ii in selected]),level=xbmc.LOGDEBUG)
		result = cm.update_random(codes=[x.getLabel() for ii,x in enumerate(li) if ii in selected])
	else:
		xbmc.log(msg='IAGL:  Game codes select cancelled',level=xbmc.LOGDEBUG)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/reset_random_filter_code')
def reset_random_filter_code():
	xbmc.log(msg='IAGL:  /reset_random_filter_code',level=xbmc.LOGDEBUG)
	result = cm.update_random(codes=None)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/random_filter_rating')
def random_filter_rating():
	xbmc.log(msg='IAGL:  /random_filter_rating',level=xbmc.LOGDEBUG)
	if isinstance(cm.get_random(),dict) and isinstance(cm.get_random().get('game_lists'),list):
		game_list_query = 'LIKE '+' OR choose_table.matching_lists LIKE '.join(['"%""{}""%"'.format(x) for x in cm.get_random().get('game_lists') if isinstance(x,str)])
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_matching_lists',table_select='rating',game_list_query=game_list_query))if isinstance(list_item,xbmcgui.ListItem)]
	else:
		li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_choose_all',table_select='rating'))if isinstance(list_item,xbmcgui.ListItem)]
	selected = xbmcgui.Dialog().multiselect(heading=cm.get_loc(30035),options=li,useDetails=True) 
	if isinstance(selected,list):
		xbmc.log(msg='IAGL:  Game ratings select in random: {}'.format([x.getLabel() for ii,x in enumerate(li) if ii in selected]),level=xbmc.LOGDEBUG)
		result = cm.update_random(ratings=[x.getLabel() for ii,x in enumerate(li) if ii in selected])
	else:
		xbmc.log(msg='IAGL:  Game ratings select cancelled',level=xbmc.LOGDEBUG)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/reset_random_filter_rating')
def reset_random_filter_rating():
	xbmc.log(msg='IAGL:  /reset_random_filter_rating',level=xbmc.LOGDEBUG)
	result = cm.update_random(ratings=None)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/execute_random')
def execute_random():
	xbmc.log(msg='IAGL:  /execute_random',level=xbmc.LOGDEBUG)
	game_search_query = cm.get_random_query()
	if isinstance(game_search_query,str):
		xbmc.log(msg='IAGL:  Current random parameters: {}'.format(cm.get_random()),level=xbmc.LOGDEBUG)
		xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
		xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path(item_path),cm.add_context_menu(li=list_item,ip=item_path,type_in='game'),False) for list_item,item_path in db.query_db(db.get_query('random_games',game_search_query=game_search_query,num_results=cm.get_random_num_results(),game_title_setting=cm.get_setting('append_game_list_to_search_results_combined'))) if isinstance(list_item,xbmcgui.ListItem)])
		for sm in config.listitem.get('sort_methods').get('games'):
			xbmcplugin.addSortMethod(plugin.handle,sm)
		xbmcplugin.endOfDirectory(plugin.handle)
	else:
		xbmc.log(msg='IAGL:  Current random parameters are empty',level=xbmc.LOGDEBUG)
		ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30227),cm.get_loc(30228))
		xbmc.sleep(config.defaults.get('sleep'))
		xbmc.executebuiltin('Container.Refresh')

@plugin.route('/generate_random_link')
def generate_random_link():
	xbmc.log(msg='IAGL:  /generate_random_link',level=xbmc.LOGDEBUG)
	current_search = cm.get_random()
	if isinstance(current_search,dict) and len(list(current_search.keys()))>0:
		selected = xbmcgui.Dialog().input(heading=cm.get_loc(30230))
		if isinstance(selected,str) and len(selected)>0:
			xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
			xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for(random_from_link,query=json.dumps(current_search)),cm.add_context_menu(li=xbmcgui.ListItem(selected,offscreen=True),type_in='random_link',ip=selected),True)])
			xbmcplugin.endOfDirectory(plugin.handle)
		else:
			xbmc.sleep(config.defaults.get('sleep'))
			xbmc.executebuiltin('Container.Refresh')
	else:
		xbmc.log(msg='IAGL:  Current random parameters are empty',level=xbmc.LOGDEBUG)
		ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30227),cm.get_loc(30228))
		xbmc.sleep(config.defaults.get('sleep'))
		xbmc.executebuiltin('Container.Refresh')

@plugin.route('/random_from_link')
def random_from_link():
	xbmc.log(msg='IAGL:  /random_from_link',level=xbmc.LOGDEBUG)
	cc = next(iter(plugin.args.get('query')),None)
	if isinstance(cc,str):
		game_search_query = cm.get_random_query(current_search_in=json.loads(cc))
		xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
		xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path(item_path),cm.add_context_menu(li=list_item,ip=item_path,type_in='game'),False) for list_item,item_path in db.query_db(db.get_query('random_games',game_search_query=game_search_query,num_results=cm.get_random_num_results(current_search_in=json.loads(cc)),game_title_setting=cm.get_setting('game_title_setting'))) if isinstance(list_item,xbmcgui.ListItem)])
		for sm in config.listitem.get('sort_methods').get('games'):
			xbmcplugin.addSortMethod(plugin.handle,sm)
		xbmcplugin.endOfDirectory(plugin.handle)
	else:
		previous_path = xbmc.getInfoLabel('Container.FolderPath')
		if previous_path.startswith('plugin://plugin.program.iagl/random_from_link'): #User came from a favorite, return home after selecting parent path
			xbmc.sleep(config.defaults.get('sleep'))
			xbmc.executebuiltin('Dialog.Close(busydialog)')
			xbmc.executebuiltin('ActivateWindow(home)')
		else:
			xbmc.log(msg='IAGL:  Unknown previous path {}'.format(previous_path), level=xbmc.LOGDEBUG)
			plugin.redirect('/')
## End Random Routes ##

@plugin.route('/game_list/<game_list_id>/<choose_id>')
def view_game_list(game_list_id,choose_id):
	xbmc.log(msg='IAGL:  /game_list/{}/{}'.format(game_list_id,choose_id),level=xbmc.LOGDEBUG)
	if choose_id == 'choose_from_list':
		xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
		xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path('{}/{}/{}'.format('game_list',game_list_id,item_path)),list_item,True) for list_item,item_path in db.query_db(db.get_query(choose_id,game_list_id=game_list_id)) if isinstance(list_item,xbmcgui.ListItem)])
		for sm in config.listitem.get('sort_methods').get('game_list_choice'):
			xbmcplugin.addSortMethod(plugin.handle,sm)
	elif choose_id == 'by_all':
		if isinstance(cm.get_setting('games_pagination'),int):
			plugin.redirect('/game_list_paged/{}/{}/{}'.format(game_list_id,choose_id,0))
		else:
			xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
			xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path(item_path),cm.add_context_menu(li=list_item,ip=item_path,type_in='game'),False) for list_item,item_path in db.query_db(db.get_query('by_all_no_page',game_list_id=game_list_id,game_title_setting=cm.get_setting('game_title_setting'),filter_to_1g1r=cm.get_setting('filter_to_1g1r'),thumbnail_to_game_art=cm.get_setting('thumbnail_to_game_art'),landscape_to_game_art=cm.get_setting('landscape_to_game_art'))) if isinstance(list_item,xbmcgui.ListItem)])
			for sm in config.listitem.get('sort_methods').get('games'):
				xbmcplugin.addSortMethod(plugin.handle,sm)
	else:
		# Possibly update this if I can understand art types for other media types
		# if choose_id in config.settings.get('media_types').keys():
		# 	print(config.settings.get('media_types').get(choose_id))
		# 	xbmcplugin.setContent(plugin.handle,config.settings.get('media_types').get(choose_id))
		# else:
		xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
		xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path('{}/{}/{}/{}'.format('game_list',game_list_id,choose_id,item_path)),list_item,True) for list_item,item_path in db.query_db(db.get_query(choose_id,game_list_id=game_list_id)) if isinstance(list_item,xbmcgui.ListItem)])
		for sm in config.listitem.get('sort_methods').get('game_list_choice_by'):
			xbmcplugin.addSortMethod(plugin.handle,sm)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/game_list_paged/<game_list_id>/<choose_id>/<page_id>')
def view_game_list_paged(game_list_id,choose_id,page_id):
	xbmc.log(msg='IAGL:  /game_list_paged/{}/{}/{}'.format(game_list_id,choose_id,page_id),level=xbmc.LOGDEBUG)
	if choose_id == 'by_all':
		xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
		if page_id == '0':
			starting_number = 0
			next_page = '1'
		else:
			starting_number = int(page_id)*cm.get_setting('games_pagination')
			next_page = str(int(page_id)+1)
		page_result = [(plugin.url_for_path(item_path),cm.add_context_menu(li=list_item,ip=item_path,type_in='game'),False) for list_item,item_path in db.query_db(db.get_query('by_all_page',game_list_id=game_list_id,game_title_setting=cm.get_setting('game_title_setting'),filter_to_1g1r=cm.get_setting('filter_to_1g1r'),items_per_page=cm.get_setting('games_pagination'),starting_number=starting_number)) if isinstance(list_item,xbmcgui.ListItem)]
		xbmcplugin.addDirectoryItems(plugin.handle,page_result)
		if len(page_result)==cm.get_setting('games_pagination'):
			xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for(view_game_list_paged,game_list_id=game_list_id,choose_id=choose_id,page_id=next_page),cm.get_next_li(),True)])
		for sm in config.listitem.get('sort_methods').get('games'):
			xbmcplugin.addSortMethod(plugin.handle,sm)
	else:
		xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
		xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path('{}/{}/{}/{}'.format('game_list',game_list_id,choose_id,item_path)),list_item,True) for list_item,item_path in db.query_db(db.get_query(choose_id,game_list_id=game_list_id)) if isinstance(list_item,xbmcgui.ListItem)])
		for sm in config.listitem.get('sort_methods').get('game_list_choice_by'):
			xbmcplugin.addSortMethod(plugin.handle,sm)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/game_list/<game_list_id>/<choose_id>/<choose_value>')
def view_games_list_from_choice(game_list_id,choose_id,choose_value):
	if isinstance(cm.get_setting('games_pagination'),int):
		plugin.redirect('/game_list_paged/{}/{}/{}/{}'.format(game_list_id,choose_id,choose_value,0))
	else:
		xbmc.log(msg='IAGL:  /game_list/{}/{}/{}'.format(game_list_id,choose_id,choose_value),level=xbmc.LOGDEBUG)
		xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
		xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path(item_path),cm.add_context_menu(li=list_item,ip=item_path,type_in='game'),False) for list_item,item_path in db.query_db(db.get_query('get_games_from_choice_no_page',game_list_id=game_list_id,choice_query=db.get_game_table_filter_from_choice(choose_id=choose_id,choose_value=choose_value),game_title_setting=cm.get_setting('game_title_setting'),filter_to_1g1r=cm.get_setting('filter_to_1g1r'))) if isinstance(list_item,xbmcgui.ListItem)])
		for sm in config.listitem.get('sort_methods').get('games'):
			xbmcplugin.addSortMethod(plugin.handle,sm)
		xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/game_list_paged/<game_list_id>/<choose_id>/<choose_value>/<page_id>')
def view_games_list_from_choice_paged(game_list_id,choose_id,choose_value,page_id):
	xbmc.log(msg='IAGL:  /game_list_paged/{}/{}/{}/{}'.format(game_list_id,choose_id,choose_value,page_id),level=xbmc.LOGDEBUG)
	if page_id == '0':
		starting_number = 0
		next_page = '1'
	else:
		starting_number = int(page_id)*cm.get_setting('games_pagination')
		next_page = str(int(page_id)+1)
	xbmcplugin.setContent(plugin.handle,cm.get_setting('media_type_game'))
	page_result = [(plugin.url_for_path(item_path),cm.add_context_menu(li=list_item,ip=item_path,type_in='game'),False) for list_item,item_path in db.query_db(db.get_query('get_games_from_choice_page',game_list_id=game_list_id,choice_query=db.get_game_table_filter_from_choice(choose_id=choose_id,choose_value=choose_value),game_title_setting=cm.get_setting('game_title_setting'),filter_to_1g1r=cm.get_setting('filter_to_1g1r'),items_per_page=cm.get_setting('games_pagination'),starting_number=starting_number)) if isinstance(list_item,xbmcgui.ListItem)]
	xbmcplugin.addDirectoryItems(plugin.handle,page_result)
	if len(page_result)==cm.get_setting('games_pagination'):
		xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for(view_games_list_from_choice_paged,game_list_id=game_list_id,choose_id=choose_id,choose_value=choose_value,page_id=next_page),cm.get_next_li(),True)])
	for sm in config.listitem.get('sort_methods').get('games'):
		xbmcplugin.addSortMethod(plugin.handle,sm)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/play_game/<game_id>')
def play_game(game_id):
	xbmc.log(msg='IAGL:  /play_game/{}'.format(game_id),level=xbmc.LOGDEBUG)
	current_game_data = next(iter(db.get_game_launch_info_from_id(game_id=game_id)),None)
	selected_game_parameters = dict()
	if isinstance(current_game_data,dict):
		selected_game_parameters['launcher'] = next(iter([x for x in [current_game_data.get('user_game_launcher'),current_game_data.get('user_global_launcher'),current_game_data.get('default_global_launcher')] if isinstance(x,str)]),'retroplayer') #Get launcher (retroplayer/external)
		selected_game_parameters['game_addon'] = next(iter([x for x in [current_game_data.get('user_game_launch_addon'),current_game_data.get('user_global_launch_addon'),current_game_data.get('default_global_launch_addon')] if isinstance(x,str)]),None) #Get launch addon
		selected_game_parameters['external_launch_command'] = next(iter([x for x in [current_game_data.get('user_game_external_launch_command'),current_game_data.get('user_global_external_launch_command'),current_game_data.get('default_global_external_launch_command')] if isinstance(x,str)]),None) #Get external launch command
		selected_game_parameters['post_download_process'] = next(iter([x for x in [current_game_data.get('user_game_post_download_process'),current_game_data.get('user_post_download_process'),current_game_data.get('default_global_post_download_process')] if isinstance(x,str)]),None) #Get external launch command
		xbmc.log(msg='IAGL:  Selected game parameters: {}'.format(selected_game_parameters),level=xbmc.LOGDEBUG)
		if selected_game_parameters.get('launcher') == 'retroplayer':
			xbmc.log(msg='IAGL:  Launcher set as retroplayer',level=xbmc.LOGDEBUG)
			plugin.redirect('/play_game_retroplayer/{}'.format(game_id))
		elif selected_game_parameters.get('launcher') == 'external':
			xbmc.log(msg='IAGL:  Launcher set as external',level=xbmc.LOGDEBUG)
			plugin.redirect('/play_game_external/{}'.format(game_id))
		else:
			xbmc.log(msg='IAGL:  Launcher set as uknown ({}), defaulting to retroplayer'.format(next_path),level=xbmc.LOGDEBUG)
			plugin.redirect('/play_game_retroplayer/{}'.format(game_id))
	else:
		xbmc.log(msg='IAGL:  Database returned null results for game id {}'.format(game_id),level=xbmc.LOGERROR)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/play_game_retroplayer/<game_id>')
def play_game_retroplayer(game_id):
	xbmc.log(msg='IAGL:  /play_game_retroplayer/{}'.format(game_id),level=xbmc.LOGDEBUG)
	current_game_data = db.get_game_from_id(game_id=game_id,game_title_setting=cm.get_setting('append_game_list_to_playlist_results_combined'))
	continue_launching = True
	if cm.get_setting('no_user_command_present') == '0':
		game_addon = next(iter([x for x in [current_game_data.get('user_game_launch_addon'),current_game_data.get('user_global_launch_addon')] if isinstance(x,str)]),None) #Use the kodi prompt to choose the addon if user hasn't set anything
	elif cm.get_setting('no_user_command_present') == '1':
		game_addon = next(iter([x for x in [current_game_data.get('user_game_launch_addon'),current_game_data.get('user_global_launch_addon'),current_game_data.get('default_global_launch_addon')] if isinstance(x,str)]),None) #Get launch addon, default to the IAGL default if user hasn't set anything
	else:
		game_addon = next(iter([x for x in [current_game_data.get('user_game_launch_addon'),current_game_data.get('user_global_launch_addon')] if isinstance(x,str)]),None) #Use what the user has set, if nothing then stop
		if not isinstance(game_addon,str):
			xbmcgui.Dialog().notification(cm.get_loc(30270),cm.get_loc(30351),xbmcgui.NOTIFICATION_WARNING)
			xbmc.log(msg='IAGL:  Launch addon is not set, and user has no_user_command_preset set to STOP',level=xbmc.LOGDEBUG)
			continue_launching = False

	if continue_launching:
		game_dl_path = current_game_data.get('user_global_download_path') or cm.get_game_dl_path(path_in=cm.get_setting('default_dl_path'),game_list_id=current_game_data.get('game_list_id'),organize_path=cm.get_setting('organize_temp_dl'))
		game_pp = next(iter([x for x in [current_game_data.get('user_game_post_download_process'),current_game_data.get('user_post_download_process'),current_game_data.get('default_global_post_download_process')] if isinstance(x,str)]),None)
		if isinstance(game_pp,str) and game_pp.startswith('move_to_folder_'):  #Special case where folder needs to be named exactly
			game_dl_path = cm.update_game_dl_path(path_in=game_dl_path,new_folder=game_pp.replace('move_to_folder_',''))
		game_lp = next(iter([x for x in [current_game_data.get('launch_parameters')] if isinstance(x,dict)]),None)
		current_game_name=current_game_data.get('label')
		game_list_item = cm.create_game_li(game_data=current_game_data,game_addon=game_addon)
		dl.set_game_name(game_name=current_game_name)
		dl.set_rom(rom=current_game_data.get('rom'))
		dl.set_launch_parameters(launch_parameters=game_lp)
		dl.set_dl_path(path_in=game_dl_path)
		current_game_data = dl.downloader.download() #Returns a list of all files downloaded and their result
		if all([x.get('download_success') for x in current_game_data]):
			xbmc.log(msg='IAGL:  Download of {} completed'.format(current_game_name),level=xbmc.LOGDEBUG)
			pp.set_process(process=game_pp)
			pp.set_game_name(game_name=current_game_name)
			pp.set_rom(rom=current_game_data)
			pp.set_launch_parameters(launch_parameters=game_lp)
			current_game_data = pp.process_games() #Returns a dict containing process results
			if current_game_data.get('process_success'):
				ln.set_launcher(launcher='retroplayer')
				xbmc.log(msg='IAGL:  Post processing of {} completed'.format(current_game_name),level=xbmc.LOGDEBUG)
				if isinstance(game_list_item,xbmcgui.ListItem) and isinstance(current_game_data.get('launch_file'),str):
					game_list_item.setPath(current_game_data.get('launch_file'))
				ln.set_game_name(game_name=current_game_name)
				ln.set_list_item(list_item=game_list_item)
				ln.set_rom(rom=current_game_data)
				current_game_data = ln.launcher.launch()
				if current_game_data.get('launch_success'):
					xbmc.log(msg='IAGL:  Updating play history and play count for game: {}'.format(current_game_name),level=xbmc.LOGDEBUG)
					playcount_and_last_played_update = db.update_pc_and_cp(game_id=game_id)
					history_update = db.add_history(game_id=game_id)
					history_limit_update = db.limit_history(history_limit=cm.get_setting('play_history'))
			else:
				ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30270),cm.get_loc(30334))
		else:
			ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30270),next(iter([x.get('download_message') for x in current_game_data if isinstance(x.get('download_message'),str)]),cm.get_loc(30272)))
	xbmcplugin.endOfDirectory(plugin.handle)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/play_game_external/<game_id>')
def play_game_external(game_id):
	xbmc.log(msg='IAGL:  /play_game_external/{}'.format(game_id),level=xbmc.LOGDEBUG)
	current_game_data = db.get_game_from_id(game_id=game_id,game_title_setting=cm.get_setting('append_game_list_to_playlist_results_combined'))
	launch_process = next(iter([x for x in [current_game_data.get('user_game_external_launch_command'),current_game_data.get('user_global_external_launch_command')] if isinstance(x,str)]),None) #Get external launch command
	if not isinstance(launch_process,str) and isinstance(current_game_data.get('game_list_id'),str):  #No user command is set, and a default exists
		if cm.get_setting('no_user_command_present') == '0':
			if xbmcgui.Dialog().yesno(cm.get_loc(30349),cm.get_loc(30350)):
				plugin.redirect('/context_menu/action/update_launch_command/{}'.format(current_game_data.get('game_list_id')))
				launch_process = next(iter([x for x in [current_game_data.get('user_game_external_launch_command'),current_game_data.get('user_global_external_launch_command')] if isinstance(x,str)]),None) #Get external launch command again
		elif cm.get_setting('no_user_command_present') == '1':
			if isinstance(current_game_data.get('default_global_external_launch_command'),str):
				xbmc.log(msg='IAGL:  Attempting to use the default',level=xbmc.LOGDEBUG)
				if isinstance(cm.get_setting('user_launch_os'),str):
					if cm.get_setting('user_launch_os') in config.defaults.get('config_available_systems'):
						installed_cores = cm.get_installed_ra_cores(ra_default_command=next(iter(db.query_db(db.get_query('get_retroarch_default_commands',user_launch_os=cm.get_setting('user_launch_os'),applaunch='0',appause='0'),return_as='dict')),None))
						if isinstance(installed_cores,list) and isinstance(next(iter([x for x in installed_cores if isinstance(x,dict) and x.get('core_stem')==current_game_data.get('default_global_external_launch_command')]),None),dict) and isinstance(next(iter([x for x in installed_cores if isinstance(x,dict) and x.get('core_stem')==current_game_data.get('default_global_external_launch_command')]),None).get('command'),str):
							launch_process = next(iter([x for x in installed_cores if isinstance(x,dict) and x.get('core_stem')==current_game_data.get('default_global_external_launch_command')]),None).get('command')
							xbmc.log(msg='IAGL:  Default command set to {}'.format(launch_process),level=xbmc.LOGDEBUG)
						else:
							xbmcgui.Dialog().notification(cm.get_loc(30270),cm.get_loc(30352).format(current_game_data.get('default_global_external_launch_command')),xbmcgui.NOTIFICATION_WARNING)
					else: #Android
						possible_cores = db.query_db(query=config.database.get('query').get('get_retroarch_android').get(cm.get_setting('kodi_saa')).format(cm.get_setting('user_launch_os'),cm.get_setting('ra_cfg_path') or cm.get_setting('ra_cfg_path_android'),cm.get_android_libretro_directory()),return_as='dict')					
						if isinstance(possible_cores,list) and isinstance(next(iter([x for x in possible_cores if isinstance(x,dict) and isinstance(x.get('command'),str) and current_game_data.get('default_global_external_launch_command') in x.get('command')]),None),dict) and isinstance(next(iter([x for x in possible_cores if isinstance(x,dict) and isinstance(x.get('command'),str) and current_game_data.get('default_global_external_launch_command') in x.get('command')]),None).get('command'),str):
							launch_process = next(iter([x for x in possible_cores if isinstance(x,dict) and isinstance(x.get('command'),str) and current_game_data.get('default_global_external_launch_command') in x.get('command')]),None).get('command')
						else:
							xbmcgui.Dialog().notification(cm.get_loc(30270),cm.get_loc(30352).format(current_game_data.get('default_global_external_launch_command')),xbmcgui.NOTIFICATION_WARNING)
				else:
					ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30270),cm.get_loc(30296))
			else:
				ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30270),cm.get_loc(30351))
		else:
			xbmcgui.Dialog().notification(cm.get_loc(30270),cm.get_loc(30351),xbmcgui.NOTIFICATION_WARNING)
			xbmc.log(msg='IAGL:  Launch process is not set, and user has no_user_command_preset set to STOP',level=xbmc.LOGDEBUG)
	if isinstance(launch_process,str):
		if isinstance(cm.get_setting('enable_elec_prepend_command'),tuple): #Prepend systemd run or flatpak run to the launch command if set in settings
			xbmc.log(msg='IAGL:  User prepend launch commmmand set to: {}'.format(cm.get_setting('enable_elec_prepend_command')),level=xbmc.LOGDEBUG)
			if 'retroarch' in launch_process.lower() and cm.get_setting('enable_elec_prepend_command')[0] in ['retroarch','all']:
				launch_process = '{}{}'.format(cm.get_setting('enable_elec_prepend_command')[-1],launch_process)
			elif 'retroarch' not in launch_process.lower() and cm.get_setting('enable_elec_prepend_command')[0] in ['all']:
				launch_process = '{}{}'.format(cm.get_setting('enable_elec_prepend_command')[-1],launch_process)
			else:
				xbmc.log(msg='IAGL:  User prepend commmand did not match rules',level=xbmc.LOGDEBUG)
		xbmc.log(msg='IAGL:  Launch process set to:\n{}'.format(launch_process),level=xbmc.LOGDEBUG)
		current_dl_path = current_game_data.get('user_global_download_path') or cm.get_game_dl_path(path_in=cm.get_setting('default_dl_path'),game_list_id=current_game_data.get('game_list_id'),organize_path=cm.get_setting('organize_temp_dl'))
		current_pp = next(iter([x for x in [current_game_data.get('user_game_post_download_process'),current_game_data.get('user_post_download_process'),current_game_data.get('default_global_post_download_process')] if isinstance(x,str)]),None)
		if isinstance(current_pp,str) and current_pp.startswith('move_to_folder_'):  #Special case where folder needs to be named exactly
			current_dl_path = cm.update_game_dl_path(path_in=current_dl_path,new_folder=current_pp.replace('move_to_folder_',''))
		current_lp = next(iter([x for x in [current_game_data.get('launch_parameters')] if isinstance(x,dict)]),None)
		current_applaunch = next(iter([x for x in [current_game_data.get('user_global_uses_applaunch')] if isinstance(x,int)]),0) #Default to not using applaunch if the value is not present
		current_apppause = next(iter([x for x in [current_game_data.get('user_global_uses_apppause')] if isinstance(x,int)]),0) #Default to not using apppause if the value is not present
		current_game_name = current_game_data.get('label')
		dl.set_game_name(game_name=current_game_name)
		dl.set_rom(rom=current_game_data.get('rom'))
		dl.set_launch_parameters(launch_parameters=current_lp)
		dl.set_dl_path(path_in=current_dl_path)
		current_game_data = dl.downloader.download() #Returns a list of all files downloaded and their result
		if all([x.get('download_success') for x in current_game_data]):
			xbmc.log(msg='IAGL:  Download of {} completed'.format(current_game_name),level=xbmc.LOGDEBUG)
			pp.set_process(process=current_pp)
			pp.set_game_name(game_name=current_game_name)
			pp.set_rom(rom=current_game_data)
			pp.set_launch_parameters(launch_parameters=current_lp)
			current_game_data = pp.process_games() #Returns a dict containing process results
			if current_game_data.get('process_success'):
				xbmc.log(msg='IAGL:  Post processing of {} completed'.format(current_game_name),level=xbmc.LOGDEBUG)
				ln.set_launcher(launcher='external')
				ln.set_game_name(game_name=current_game_name)
				ln.set_appause(appause=current_apppause)
				ln.set_applaunch(applaunch=current_applaunch)
				ln.set_rom(rom=current_game_data)
				ln.set_launch_parameters(launch_parameters={'launch_process':launch_process,'netplay':cm.get_home_property('iagl_netplay_parameters')}) #Grab any netplay settings user has set
				#Insert history here for games that will be launched with applaunch or apppause
				current_game_data = ln.launcher.launch()
				if current_game_data.get('launch_success'):
					playcount_and_last_played_update = db.update_pc_and_cp(game_id=game_id)
					history_update = db.add_history(game_id=game_id)
					history_limit_update = db.limit_history(history_limit=cm.get_setting('play_history'))
		else:
			ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30270),next(iter([x.get('download_message') for x in current_game_data if isinstance(x.get('download_message'),str)]),cm.get_loc(30272)))
	else:
		xbmc.log(msg='IAGL:  Launch process is not set, unable to launch game',level=xbmc.LOGDEBUG)
	xbmcplugin.endOfDirectory(plugin.handle)
	xbmc.sleep(config.defaults.get('sleep'))
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/download_game_to/<game_id>')
def download_game_to(game_id):
	xbmc.log(msg='IAGL:  /download_game_to/{}'.format(game_id),level=xbmc.LOGDEBUG)
	current_game_data = db.get_game_from_id(game_id=game_id,game_title_setting=cm.get_setting('game_title_setting'))
	game_pp = next(iter([x for x in [current_game_data.get('user_game_post_download_process'),current_game_data.get('user_post_download_process'),current_game_data.get('default_global_post_download_process')] if isinstance(x,str)]),None)
	game_lp = next(iter([x for x in [current_game_data.get('launch_parameters')] if isinstance(x,dict)]),None)
	current_game_name=current_game_data.get('label')
	if isinstance(current_game_data,dict) and isinstance(current_game_data.get('rom'),dict) or isinstance(current_game_data.get('rom'),list):
		selected = xbmcgui.Dialog().browseSingle(0,heading=cm.get_loc(30267),shares="")
		if isinstance(selected,str) and xbmcvfs.exists(selected):
			dl.set_rom(rom=current_game_data.get('rom'))
			dl.set_dl_path(path_in=selected)
			current_game_data = dl.downloader.download()
			if all([x.get('download_success') for x in current_game_data]):
				xbmc.log(msg='IAGL:  Download to... of {} completed'.format(current_game_name),level=xbmc.LOGDEBUG)
				if xbmcgui.Dialog().yesno(cm.get_loc(30233),cm.get_loc(30446)):
					pp.set_process(process=game_pp)
					pp.set_game_name(game_name=current_game_name)
					pp.set_rom(rom=current_game_data)
					pp.set_launch_parameters(launch_parameters=game_lp)
					current_game_data = pp.process_games() #Returns a dict containing process results
					if current_game_data.get('process_success'):
						ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30233),cm.get_loc(30447))

@plugin.route('/context_menu/action/view_launch_parameters/<game_id>')
def download_game_to(game_id):
	xbmc.log(msg='IAGL:  /view_launch_parameters/{}'.format(game_id),level=xbmc.LOGDEBUG)
	current_game_data = db.get_game_from_id(game_id=game_id,game_title_setting=cm.get_setting('game_title_setting'))
	game_item_info = next(iter(db.query_db(db.get_query('get_game_list_info_from_game_id',game_id=game_id,game_title_setting=cm.get_setting('game_title_setting')),return_as='dict')),None)
	if isinstance(game_item_info,dict):
		info_key_to_label = {'label': cm.get_loc(30304),
							 'system': cm.get_loc(30305),
							 'default_global_external_launch_command': cm.get_loc(30309),
							 'default_global_external_launch_core_name':cm.get_loc(30309),
							 'default_global_launch_addon': cm.get_loc(30310),
							 'default_global_launcher': None,
							 'default_global_post_download_process': cm.get_loc(30311),
							 'user_global_download_path': cm.get_loc(30312),
							 'user_global_external_launch_command': cm.get_loc(30313),
							 'user_global_uses_applaunch':None,
							 'user_global_uses_apppause':None,
							 'user_global_launch_addon': cm.get_loc(30314),
							 'user_global_launcher': None,
							 'user_global_visibility': None,
							 'user_post_download_process': cm.get_loc(30315),
							 'launch_parameters':cm.get_loc(30344),
							# 'user_game_launch_addon':None, #not yet editable by the user, to be added later
							# 'user_game_external_launch_command':None, #not yet editable by the user, to be added later
							# 'user_game_post_download_process':None #not yet editable by the user, to be added later
							 }
		game_list_launcher = next(iter([x for x in [game_item_info.get('user_global_launcher'),game_item_info.get('default_global_launcher')] if isinstance(x,str)]),'retroplayer') 
		if game_list_launcher == 'external':
			launch_command_key = next(iter([k for k in ['user_global_external_launch_command','default_global_external_launch_core_name'] if isinstance(game_item_info.get(k),str)]),None)
			pp_command_key = next(iter([k for k in ['user_post_download_process','default_global_post_download_process'] if isinstance(game_item_info.get(k),str)]),None)
			info_keys_to_display = ['label','system',launch_command_key,'user_global_download_path',pp_command_key,'launch_parameters']
			if isinstance(game_item_info.get('user_global_external_launch_command'),str):
				if game_item_info.get('user_global_uses_applaunch') == 1:
					pre_command_value = cm.get_loc(30337)
				elif game_item_info.get('user_global_uses_apppause') == 1:
					pre_command_value = cm.get_loc(30338)
				else:
					pre_command_value = cm.get_loc(30336)
				li1 = xbmcgui.ListItem(label=cm.get_loc(30318),label2='{}[CR]{}'.format(cm.get_loc(30319),pre_command_value))
			else:
				li1 = xbmcgui.ListItem(label=cm.get_loc(30318),label2=cm.get_loc(30320))
			lis = [li1]+[xbmcgui.ListItem(label=info_key_to_label.get(x),label2=next(iter([str(z) for z in [game_item_info.get(x)] if z is not None]),cm.get_loc(30317))) for x in info_keys_to_display if isinstance(info_key_to_label.get(x),str)]
			selected = xbmcgui.Dialog().select(heading=cm.get_loc(30343),list=lis,useDetails=True)
			if lis[selected].getLabel() in [info_key_to_label.get('user_global_external_launch_command'),info_key_to_label.get('user_global_download_path'),info_key_to_label.get('launch_parameters')] and isinstance(lis[selected].getLabel2(),str) and len(lis[selected].getLabel2())>0 and lis[selected].getLabel2()!=cm.get_loc(30317):
				if 'XX' in lis[selected].getLabel2():
					xbmcgui.Dialog().textviewer(lis[selected].getLabel(),lis[selected].getLabel2()+'[CR][CR]'+cm.get_loc(30333))
				elif lis[selected].getLabel() == info_key_to_label.get('launch_parameters'):
					xbmcgui.Dialog().textviewer(lis[selected].getLabel(),'[CR]'.join([x.replace('\\n','[CR]').replace('\n','[CR]').replace('\\r','[CR]').replace('\r','[CR]').replace('{','[CR]{').replace('}','[CR]}').replace('[CR][CR]','[CR]').strip() for x in lis[selected].getLabel2().split(',')]))
				else:
					xbmcgui.Dialog().textviewer(lis[selected].getLabel(),lis[selected].getLabel2())
		else:
			launch_command_key = next(iter([k for k in ['user_global_launch_addon','default_global_launch_addon'] if isinstance(game_item_info.get(k),str)]),None)
			pp_command_key = next(iter([k for k in ['user_post_download_process','default_global_post_download_process'] if isinstance(game_item_info.get(k),str)]),None)
			info_keys_to_display = ['label','system',launch_command_key,'user_global_download_path',pp_command_key,'launch_parameters']
			li1 = xbmcgui.ListItem(label=cm.get_loc(30318),label2=cm.get_loc(30321))
			lis = [li1]+[xbmcgui.ListItem(label=info_key_to_label.get(x),label2=next(iter([str(z) for z in [game_item_info.get(x)] if z is not None]),cm.get_loc(30317))) for x in info_keys_to_display if isinstance(info_key_to_label.get(x),str)]
			selected = xbmcgui.Dialog().select(heading=cm.get_loc(30343),list=lis,useDetails=True)
			if lis[selected].getLabel() in [info_key_to_label.get('launch_parameters')] and isinstance(lis[selected].getLabel2(),str) and len(lis[selected].getLabel2())>0 and lis[selected].getLabel2()!=cm.get_loc(30317):
				xbmcgui.Dialog().textviewer(lis[selected].getLabel(),'[CR]'.join([x.replace('\\n','[CR]').replace('\n','[CR]').replace('\\r','[CR]').replace('\r','[CR]').replace('{','[CR]{').replace('}','[CR]}').replace('[CR][CR]','[CR]').strip() for x in lis[selected].getLabel2().split(',')]))
	else:
		xbmc.log(msg='IAGL:  Game item info is malformed for: {}'.format(game_list_id),level=xbmc.LOGERROR)

@plugin.route('/context_menu/action/add_to_favorites/<game_id>')
def add_to_iagl_favorites(game_id):
	xbmc.log(msg='IAGL:  /add_to_iagl_favorites',level=xbmc.LOGDEBUG)
	fav_groups = db.get_favorite_group_names()
	if isinstance(fav_groups,list) and len(fav_groups)>0:  #Ask about current lists or new list
		li = [xbmcgui.ListItem(x.get('label'),offscreen=True) for x in fav_groups]+[xbmcgui.ListItem(cm.get_loc(30234),offscreen=True)]
		selected = xbmcgui.Dialog().select(heading=cm.get_loc(30235),list=li,useDetails=False)
		if isinstance(selected,int):
			if selected==len(li)-1:
				new_name = xbmcgui.Dialog().input(heading=cm.get_loc(30089))
				if isinstance(new_name,str) and len(new_name)>0:
					result1 = db.add_favorite(fav_group=new_name,game_id=game_id)
					result2 = db.mark_game_as_favorite(game_id=game_id)
					if isinstance(result1,int) and isinstance(result2,int):
						ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30233),'{}[CR]{}'.format(cm.get_loc(30090),new_name))
			else:
				fav_name = [x.get('label') for x in fav_groups][selected]
				result1 = db.add_favorite(fav_group=fav_name,game_id=game_id)
				result2 = db.mark_game_as_favorite(game_id=game_id)
				if isinstance(result1,int) and isinstance(result2,int):
					ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30233),'{}[CR]{}'.format(cm.get_loc(30090),fav_name))			
	else: #No groups defined yet
		new_name = xbmcgui.Dialog().input(heading=cm.get_loc(30089))
		if isinstance(new_name,str) and len(new_name)>0:
			result1 = db.add_favorite(fav_group=new_name,game_id=game_id)
			result2 = db.mark_game_as_favorite(game_id=game_id)
			if isinstance(result1,int) and isinstance(result2,int):
				ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30233),'{}[CR]{}'.format(cm.get_loc(30090),new_name))

@plugin.route('/context_menu/action/remove_game_from_favorites/<game_id>')
def remove_game_from_favorites(game_id):
	xbmc.log(msg='IAGL:  /remove_game_from_favorites',level=xbmc.LOGDEBUG)
	if xbmcgui.Dialog().yesno(cm.get_loc(30237),cm.get_loc(30238)):
		result1 = db.delete_favorite_from_uid(game_id=game_id)
		result2 = db.unmark_game_as_favorite(game_id=game_id)
		if isinstance(result1,int) and isinstance(result2,int):
			ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30237),cm.get_loc(30239))
			xbmc.sleep(config.defaults.get('sleep'))
			xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/add_to_favorites_search/<link_name>')
def add_to_favorites_search(link_name):
	xbmc.log(msg='IAGL:  /add_to_favorites_search',level=xbmc.LOGDEBUG)
	current_search = cm.get_search()
	if isinstance(current_search,dict):
		fav_groups = db.get_favorite_group_names()
		if isinstance(fav_groups,list) and len(fav_groups)>0:  #Ask about current lists or new list
			li = [xbmcgui.ListItem(x.get('label'),offscreen=True) for x in fav_groups]+[xbmcgui.ListItem(cm.get_loc(30234),offscreen=True)]
			selected = xbmcgui.Dialog().select(heading=cm.get_loc(30235),list=li,useDetails=False)
			if isinstance(selected,int):
				if selected==len(li)-1:
					new_name = xbmcgui.Dialog().input(heading=cm.get_loc(30089))
					if isinstance(new_name,str) and len(new_name)>0:
						result = db.add_favorite(fav_group=new_name,is_search_link=1,link_query=json.dumps(current_search))
						if isinstance(result,int):
							ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30233),'{}[CR]{}'.format(cm.get_loc(30090),new_name))
				else:
					fav_name = [x.get('label') for x in fav_groups][selected]
					result = db.add_favorite(fav_group=fav_name,is_search_link=1,link_query=json.dumps(current_search))
					if isinstance(result,int):
						ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30233),'{}[CR]{}'.format(cm.get_loc(30090),fav_name))			
		else: #No groups defined yet
			new_name = xbmcgui.Dialog().input(heading=cm.get_loc(30089))
			if isinstance(new_name,str) and len(new_name)>0:
				result = db.add_favorite(fav_group=new_name,is_search_link=1,link_query=json.dumps(current_search))
				if isinstance(result,int):
					ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30233),'{}[CR]{}'.format(cm.get_loc(30090),new_name))
	else:
		xbmc.log(msg='IAGL:  /add_to_favorites_search query was malformed: {}'.format(current_search),level=xbmc.LOGERROR)

@plugin.route('/context_menu/action/add_to_favorites_random/<link_name>')
def add_to_favorites_random(link_name):
	xbmc.log(msg='IAGL:  /add_to_favorites_random',level=xbmc.LOGDEBUG)
	current_search = cm.get_random()
	if isinstance(current_search,dict):
		fav_groups = db.get_favorite_group_names()
		if isinstance(fav_groups,list) and len(fav_groups)>0:  #Ask about current lists or new list
			li = [xbmcgui.ListItem(x.get('label'),offscreen=True) for x in fav_groups]+[xbmcgui.ListItem(cm.get_loc(30234),offscreen=True)]
			selected = xbmcgui.Dialog().select(heading=cm.get_loc(30235),list=li,useDetails=False)
			if isinstance(selected,int):
				if selected==len(li)-1:
					new_name = xbmcgui.Dialog().input(heading=cm.get_loc(30089))
					if isinstance(new_name,str) and len(new_name)>0:
						result = db.add_favorite(fav_group=new_name,is_random_link=1,link_query=json.dumps(current_search))
						if isinstance(result,int):
							ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30233),'{}[CR]{}'.format(cm.get_loc(30090),new_name))
				else:
					fav_name = [x.get('label') for x in fav_groups][selected]
					result = db.add_favorite(fav_group=fav_name,is_random_link=1,link_query=json.dumps(current_search))
					if isinstance(result,int):
						ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30233),'{}[CR]{}'.format(cm.get_loc(30090),fav_name))			
		else: #No groups defined yet
			new_name = xbmcgui.Dialog().input(heading=cm.get_loc(30089))
			if isinstance(new_name,str) and len(new_name)>0:
				result = db.add_favorite(fav_group=new_name,is_random_link=1,link_query=json.dumps(current_search))
				if isinstance(result,int):
					ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30233),'{}[CR]{}'.format(cm.get_loc(30090),new_name))
	else:
		xbmc.log(msg='IAGL:  /add_to_favorites_random query was malformed: {}'.format(current_search),level=xbmc.LOGERROR)

@plugin.route('/context_menu/action/remove_link_from_favorites')
def remove_link_from_favorites():
	xbmc.log(msg='IAGL:  /remove_link_from_favorites',level=xbmc.LOGDEBUG)
	if isinstance(xbmc.getInfoLabel('ListItem.FileNameAndPath'),str) and isinstance(xbmc.getInfoLabel('ListItem.FileNameAndPath').split('query=')[-1],str) and len(xbmc.getInfoLabel('ListItem.FileNameAndPath').split('query=')[-1])>0:
		query_in = unquote(xbmc.getInfoLabel('ListItem.FileNameAndPath').split('query=')[-1]).replace('"','""')
		if xbmcgui.Dialog().yesno(cm.get_loc(30237),cm.get_loc(30238)):
			result = db.delete_favorite_from_link(query_in=query_in)
			if isinstance(result,int) and result>0:
				ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30237),cm.get_loc(30239))
				xbmc.sleep(config.defaults.get('sleep'))
				xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/update_launcher/<game_list_id>')
def update_game_list_launcher(game_list_id):
	xbmc.log(msg='IAGL:  /update_game_list_launcher',level=xbmc.LOGDEBUG)
	current_launcher = db.get_game_list_launcher(game_list_id=game_list_id)
	if current_launcher == 'retroplayer':
		if xbmcgui.Dialog().yesno(cm.get_loc(30259),cm.get_loc(30260)):
			result = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_launcher',new_value='external')
			if isinstance(result,int) and result>0:
				ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30233),cm.get_loc(30262))
				#add step to update command here
	elif current_launcher == 'external':
		if xbmcgui.Dialog().yesno(cm.get_loc(30259),cm.get_loc(30261)):
			result = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_launcher',new_value='retroplayer')
			if isinstance(result,int) and result>0:
				ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30233),cm.get_loc(30263))
				#add step to update command here
	else:
		xbmc.log(msg='IAGL:  Unknown current launcher: {}'.format(current_launcher),level=xbmc.LOGERROR)

@plugin.route('/context_menu/action/update_launcher_from_uid/<game_id>')
def update_game_list_launcher_from_uid(game_id):
	xbmc.log(msg='IAGL:  /update_launcher_from_uid',level=xbmc.LOGDEBUG)
	game_item_info = next(iter(db.query_db(db.get_query('get_game_list_info_from_game_id',game_id=game_id,game_title_setting=cm.get_setting('game_title_setting')),return_as='dict')),None)
	if xbmcgui.Dialog().yesno(cm.get_loc(30259),cm.get_loc(30364).format(game_item_info.get('label'))):
		plugin.redirect('/context_menu/action/update_launcher/{}'.format(game_item_info.get('label')))

@plugin.route('/context_menu/action/get_game_list_info/<game_list_id>')
def get_game_list_info(game_list_id):
	xbmc.log(msg='IAGL:  /get_game_list_info',level=xbmc.LOGDEBUG)
	game_list_info = next(iter(db.query_db(db.get_query('get_game_list_info',game_list_id=game_list_id),return_as='dict')),None)
	if isinstance(game_list_info,dict):
		info_key_to_label = {'label': cm.get_loc(30304),
							 'system': cm.get_loc(30305),
							 'total_games': cm.get_loc(30307),
							 'total_1g1r_games': cm.get_loc(30306),
							 'total_favorited_games': cm.get_loc(30308),
							 'default_global_external_launch_command': cm.get_loc(30309),
							 'default_global_external_launch_core_name':cm.get_loc(30309),
							 'default_global_launch_addon': cm.get_loc(30310),
							 'default_global_launcher': None,
							 'default_global_post_download_process': cm.get_loc(30311),
							 'user_global_download_path': cm.get_loc(30312),
							 'user_global_external_launch_command': cm.get_loc(30313),
							 'user_global_uses_applaunch':None,
							 'user_global_uses_apppause':None,
							 'user_global_launch_addon': cm.get_loc(30314),
							 'user_global_launcher': None,
							 'user_global_visibility': None,
							 'user_post_download_process': cm.get_loc(30315)}
		game_list_launcher = next(iter([x for x in [game_list_info.get('user_global_launcher'),game_list_info.get('default_global_launcher')] if isinstance(x,str)]),'retroplayer') 
		if game_list_launcher == 'external':
			launch_command_key = next(iter([k for k in ['user_global_external_launch_command','default_global_external_launch_core_name'] if isinstance(game_list_info.get(k),str)]),None)
			pp_command_key = next(iter([k for k in ['user_post_download_process','default_global_post_download_process'] if isinstance(game_list_info.get(k),str)]),None)
			info_keys_to_display = ['label','system',launch_command_key,'user_global_download_path',pp_command_key,'total_games','total_1g1r_games','total_favorited_games']
			if isinstance(game_list_info.get('user_global_external_launch_command'),str):
				if game_list_info.get('user_global_uses_applaunch') == 1:
					pre_command_value = cm.get_loc(30337)
				elif game_list_info.get('user_global_uses_apppause') == 1:
					pre_command_value = cm.get_loc(30338)
				else:
					pre_command_value = cm.get_loc(30336)
				li1 = xbmcgui.ListItem(label=cm.get_loc(30318),label2='{}[CR]{}'.format(cm.get_loc(30319),pre_command_value))
			else:
				li1 = xbmcgui.ListItem(label=cm.get_loc(30318),label2=cm.get_loc(30320))
			lis = [li1]+[xbmcgui.ListItem(label=info_key_to_label.get(x),label2=next(iter([str(z) for z in [game_list_info.get(x)] if z is not None]),cm.get_loc(30317))) for x in info_keys_to_display if isinstance(info_key_to_label.get(x),str)]
			selected = xbmcgui.Dialog().select(heading=cm.get_loc(30316),list=lis,useDetails=True)
			if lis[selected].getLabel() in [info_key_to_label.get('user_global_external_launch_command'),info_key_to_label.get('user_global_download_path')] and isinstance(lis[selected].getLabel2(),str) and len(lis[selected].getLabel2())>0 and lis[selected].getLabel2()!=cm.get_loc(30317):
				if 'XX' in lis[selected].getLabel2():
					xbmcgui.Dialog().textviewer(lis[selected].getLabel(),lis[selected].getLabel2()+'[CR][CR]'+cm.get_loc(30333))
				else:
					xbmcgui.Dialog().textviewer(lis[selected].getLabel(),lis[selected].getLabel2())
		else:
			launch_command_key = next(iter([k for k in ['user_global_launch_addon','default_global_launch_addon'] if isinstance(game_list_info.get(k),str)]),None)
			pp_command_key = next(iter([k for k in ['user_post_download_process','default_global_post_download_process'] if isinstance(game_list_info.get(k),str)]),None)
			info_keys_to_display = ['label','system',launch_command_key,'user_global_download_path',pp_command_key,'total_games','total_1g1r_games','total_favorited_games']
			li1 = xbmcgui.ListItem(label=cm.get_loc(30318),label2=cm.get_loc(30321))
			lis = [li1]+[xbmcgui.ListItem(label=info_key_to_label.get(x),label2=next(iter([str(z) for z in [game_list_info.get(x)] if z is not None]),cm.get_loc(30317))) for x in info_keys_to_display if isinstance(info_key_to_label.get(x),str)]
			selected = xbmcgui.Dialog().select(heading=cm.get_loc(30316),list=lis,useDetails=True)
	else:
		xbmc.log(msg='IAGL:  Game list info is malformed for: {}'.format(game_list_id),level=xbmc.LOGERROR)

@plugin.route('/context_menu/action/update_launch_command/<game_list_id>')
def update_game_list_launch_command(game_list_id):
	xbmc.log(msg='IAGL:  /update_game_list_launch_command',level=xbmc.LOGDEBUG)
	current_launcher = db.get_game_list_launcher(game_list_id=game_list_id)
	if current_launcher == 'retroplayer':
		li = cm.get_game_addons()
		if len(li)>0:
			selected = xbmcgui.Dialog().select(heading=cm.get_loc(30264),list=li,useDetails=True)
			if selected>0:
				if selected == len(li)-1:
					if xbmcgui.Dialog().yesno(cm.get_loc(30299),cm.get_loc(30265)):
						result1 = db.reset_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_launch_addon')
						if isinstance(result1,int) and result1>0:
							ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30299),cm.get_loc(30353))
							xbmc.sleep(config.defaults.get('sleep'))
							xbmc.executebuiltin('Container.Refresh')
				else:
					if isinstance(li[selected],xbmcgui.ListItem) and isinstance(li[selected].getProperty('id'),str):
						result1 = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_launch_addon',new_value=li[selected].getProperty('id'))
						if isinstance(result1,int) and result1>0:
							ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30247),cm.get_loc(30355))
							xbmc.sleep(config.defaults.get('sleep'))
							xbmc.executebuiltin('Container.Refresh')
					else:
						xbmc.log(msg='IAGL: Game addon id could not be found for {}'.format(li[selected]),level=xbmc.LOGERROR)
			else:
				xbmc.log(msg='IAGL:  Updating launch command cancelled',level=xbmc.LOGDEBUG)
		else:
			xbmcgui.Dialog().notification(cm.get_loc(30270),cm.get_loc(30354),xbmcgui.NOTIFICATION_WARNING)
			xbmc.log(msg='IAGL:  No game addons were found installed, unable to update user_global_launch_addon',level=xbmc.LOGDEBUG)
	if current_launcher == 'external':
		selected_external_command_types = xbmcgui.Dialog().select(heading=cm.get_loc(30278),list=[cm.get_loc(30275),cm.get_loc(30276),cm.get_loc(30277),cm.get_loc(30299)],useDetails=False)
		if selected_external_command_types == 0:
			if isinstance(cm.get_setting('user_launch_os'),str):
				if cm.get_setting('user_launch_os') in config.defaults.get('config_available_systems'):
					if isinstance(cm.get_setting('ra_app_path'),str) and xbmcvfs.exists(cm.get_setting('ra_app_path')) and isinstance(cm.get_setting('ra_cfg_path'),str) and xbmcvfs.exists(cm.get_setting('ra_cfg_path')):
						if cm.get_setting('kodi_on_launch') == '1':
							applaunch_setting = '0'
							apppause_setting = '0'
						elif cm.get_setting('kodi_on_launch') == '2':
							applaunch_setting = '1'
							apppause_setting = '0'
						elif cm.get_setting('kodi_on_launch') == '3':
							applaunch_setting = '0'
							apppause_setting = '1'
						else: #Prompt user
							pre_launch_options = [cm.get_loc(30336)]
							uses_applaunch = next(iter(db.query_db(db.get_query('uses_applauch',user_launch_os=cm.get_setting('user_launch_os')),return_as='dict')),None)
							uses_apppause = next(iter(db.query_db(db.get_query('uses_apppause',user_launch_os=cm.get_setting('user_launch_os')),return_as='dict')),None)
							if isinstance(uses_applaunch,dict) and isinstance(uses_applaunch.get('total'),int) and uses_applaunch.get('total')>0:
								pre_launch_options = pre_launch_options+[cm.get_loc(30337)]
							if isinstance(uses_apppause,dict) and isinstance(uses_apppause.get('total'),int) and uses_apppause.get('total')>0:  #This assumes appause is only present if applaunch is present (currently true)
								pre_launch_options = pre_launch_options+[cm.get_loc(30338)]
							selected_external_pre_command_types = xbmcgui.Dialog().select(heading=cm.get_loc(30335),list=pre_launch_options,useDetails=False)
							if selected_external_pre_command_types == 1:
								applaunch_setting = '1'
								apppause_setting = '0'
							elif selected_external_pre_command_types == 2:
								applaunch_setting = '0'
								apppause_setting = '1'
							else:
								applaunch_setting = '0'
								apppause_setting = '0'
						installed_cores = cm.get_installed_ra_cores(ra_default_command=next(iter(db.query_db(db.get_query('get_retroarch_default_commands',user_launch_os=cm.get_setting('user_launch_os'),applaunch=applaunch_setting,appause=apppause_setting),return_as='dict')),None))
						if isinstance(installed_cores,list) and len(installed_cores)>0:
							choose_core_by = xbmcgui.Dialog().select(heading=cm.get_loc(30152),list=[cm.get_loc(30153),cm.get_loc(30154),cm.get_loc(30155)],useDetails=False)
							if choose_core_by == 0:
								display_names = sorted([x.get('display_name') for x in installed_cores if isinstance(x,dict) and isinstance(x.get('display_name'),str)])
								xbmc.log(msg='IAGL:  {} Retroarch core options found'.format(len(display_names)),level=xbmc.LOGDEBUG)
								if isinstance(display_names,list) and len(display_names)>0:
									selected = xbmcgui.Dialog().select(heading=cm.get_loc(30156),list=display_names,useDetails=False)
									new_command = next(iter([x.get('command') for x in installed_cores if x.get('display_name')==display_names[selected]]),None)
									if selected>-1 and isinstance(new_command,str):
										if xbmcgui.Dialog().yesno(cm.get_loc(30247),'{}[CR]{}'.format(cm.get_loc(30292),display_names[selected])):
											result1 = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_external_launch_command',new_value=new_command.replace('"','""'))
											result2 = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_uses_apppause',new_value=apppause_setting)
											result3 = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_uses_applaunch',new_value=applaunch_setting)
											if isinstance(result1,int) and isinstance(result2,int) and isinstance(result3,int) and result1>0 and result2>0 and result3>0:
												ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30247),cm.get_loc(30293))
												xbmc.sleep(config.defaults.get('sleep'))
												xbmc.executebuiltin('Container.Refresh')
									else:
										xbmc.log(msg='IAGL:  Retroarch core selection cancelled',level=xbmc.LOGDEBUG)
							elif choose_core_by == 1:
								core_names = sorted([x.get('corename') for x in installed_cores if isinstance(x,dict) and isinstance(x.get('corename'),str)])
								xbmc.log(msg='IAGL:  {} Retroarch core options found'.format(len(core_names)),level=xbmc.LOGDEBUG)
								if isinstance(core_names,list) and len(core_names)>0:
									selected = xbmcgui.Dialog().select(heading=cm.get_loc(30156),list=core_names,useDetails=False)
									new_command = next(iter([x.get('command') for x in installed_cores if x.get('corename')==core_names[selected]]),None)
									if selected>-1 and isinstance(new_command,str):
										if xbmcgui.Dialog().yesno(cm.get_loc(30247),'{}[CR]{}'.format(cm.get_loc(30292),core_names[selected])):
											result1 = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_external_launch_command',new_value=new_command.replace('"','""'))
											result2 = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_uses_apppause',new_value=apppause_setting)
											result3 = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_uses_applaunch',new_value=applaunch_setting)
											if isinstance(result1,int) and isinstance(result2,int) and isinstance(result3,int) and result1>0 and result2>0 and result3>0:
												ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30247),cm.get_loc(30293))
												xbmc.sleep(config.defaults.get('sleep'))
												xbmc.executebuiltin('Container.Refresh')
									else:
										xbmc.log(msg='IAGL:  Retroarch core selection cancelled',level=xbmc.LOGDEBUG)
							elif choose_core_by == 2:
								system_names = sorted(set([x.get('systemname') for x in installed_cores if isinstance(x,dict) and isinstance(x.get('systemname'),str)]))
								xbmc.log(msg='IAGL:  {} Retroarch system options found'.format(len(system_names)),level=xbmc.LOGDEBUG)
								if isinstance(system_names,list) and len(system_names)>0:
									selected_system = xbmcgui.Dialog().select(heading=cm.get_loc(30157),list=system_names,useDetails=False)
									if selected_system>-1:
										display_names = sorted([x.get('display_name') for x in installed_cores if isinstance(x,dict) and isinstance(x.get('display_name'),str) and x.get('systemname')==system_names[selected_system]])
										xbmc.log(msg='IAGL:  {} Retroarch core options found'.format(len(display_names)),level=xbmc.LOGDEBUG)
										if isinstance(display_names,list) and len(display_names)>0:
											selected = xbmcgui.Dialog().select(heading='{}: {}'.format(system_names[selected_system],cm.get_loc(30156)),list=display_names,useDetails=False)
											new_command = next(iter([x.get('command') for x in installed_cores if x.get('display_name')==display_names[selected]]),None)
											if selected>-1 and isinstance(new_command,str):
												if xbmcgui.Dialog().yesno(cm.get_loc(30247),'{}[CR]{}'.format(cm.get_loc(30292),display_names[selected])):
													result1 = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_external_launch_command',new_value=new_command.replace('"','""'))
													result2 = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_uses_apppause',new_value=apppause_setting)
													result3 = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_uses_applaunch',new_value=applaunch_setting)
													if isinstance(result1,int) and isinstance(result2,int) and isinstance(result3,int) and result1>0 and result2>0 and result3>0:
														ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30247),cm.get_loc(30293))
														xbmc.sleep(config.defaults.get('sleep'))
														xbmc.executebuiltin('Container.Refresh')
											else:
												xbmc.log(msg='IAGL:  Retroarch core selection cancelled',level=xbmc.LOGDEBUG)
							else:
								xbmc.log(msg='IAGL:  Retroarch core selection cancelled',level=xbmc.LOGDEBUG)
						else:
							ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30270),cm.get_loc(30339))
							xbmc.log(msg='IAGL:  No commands found matching query',level=xbmc.LOGERROR)
					else:
						ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30270),cm.get_loc(30295))
				else: #Android
					applaunch_setting = '0'
					apppause_setting = '0'
					if isinstance(cm.get_setting('ra_cfg_path') or cm.get_setting('ra_cfg_path_android'),str) and isinstance(cm.get_android_libretro_directory(),str):
						possible_cores = db.query_db(query=config.database.get('query').get('get_retroarch_android').get(cm.get_setting('kodi_saa')).format(cm.get_setting('user_launch_os'),cm.get_setting('ra_cfg_path') or cm.get_setting('ra_cfg_path_android'),cm.get_android_libretro_directory()),return_as='dict')					
						if isinstance(possible_cores,list) and len(possible_cores)>0:
							choose_core_by = xbmcgui.Dialog().select(heading=cm.get_loc(30152),list=[cm.get_loc(30153),cm.get_loc(30154),cm.get_loc(30155)],useDetails=False)
							if choose_core_by == 0:
								display_names = sorted([x.get('display_name') for x in possible_cores if isinstance(x,dict) and isinstance(x.get('display_name'),str)])
								xbmc.log(msg='IAGL:  {} Retroarch core options found'.format(len(display_names)),level=xbmc.LOGDEBUG)
								if isinstance(display_names,list) and len(display_names)>0:
									selected = xbmcgui.Dialog().select(heading=cm.get_loc(30156),list=display_names,useDetails=False)
									new_command = next(iter([x.get('command') for x in possible_cores if x.get('display_name')==display_names[selected]]),None)
									if selected>-1 and isinstance(new_command,str):
										if xbmcgui.Dialog().yesno(cm.get_loc(30247),'{}[CR]{}'.format(cm.get_loc(30292),display_names[selected])):
											result1 = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_external_launch_command',new_value=new_command.replace('"','""'))
											result2 = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_uses_apppause',new_value=apppause_setting)
											result3 = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_uses_applaunch',new_value=applaunch_setting)
											if isinstance(result1,int) and isinstance(result2,int) and isinstance(result3,int) and result1>0 and result2>0 and result3>0:
												ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30247),'{}[CR]{}'.format(cm.get_loc(30293),cm.get_loc(30294)))
												xbmc.sleep(config.defaults.get('sleep'))
												xbmc.executebuiltin('Container.Refresh')
									else:
										xbmc.log(msg='IAGL:  Retroarch core selection cancelled',level=xbmc.LOGDEBUG)
							elif choose_core_by == 1:
								core_names = sorted([x.get('corename') for x in possible_cores if isinstance(x,dict) and isinstance(x.get('corename'),str)])
								xbmc.log(msg='IAGL:  {} Retroarch core options found'.format(len(core_names)),level=xbmc.LOGDEBUG)
								if isinstance(core_names,list) and len(core_names)>0:
									selected = xbmcgui.Dialog().select(heading=cm.get_loc(30156),list=core_names,useDetails=False)
									new_command = next(iter([x.get('command') for x in possible_cores if x.get('corename')==core_names[selected]]),None)
									if selected>-1 and isinstance(new_command,str):
										if xbmcgui.Dialog().yesno(cm.get_loc(30247),'{}[CR]{}'.format(cm.get_loc(30292),core_names[selected])):
											result1 = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_external_launch_command',new_value=new_command.replace('"','""'))
											result2 = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_uses_apppause',new_value=apppause_setting)
											result3 = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_uses_applaunch',new_value=applaunch_setting)
											if isinstance(result1,int) and isinstance(result2,int) and isinstance(result3,int) and result1>0 and result2>0 and result3>0:
												ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30247),'{}[CR]{}'.format(cm.get_loc(30293),cm.get_loc(30294)))
												xbmc.sleep(config.defaults.get('sleep'))
												xbmc.executebuiltin('Container.Refresh')
									else:
										xbmc.log(msg='IAGL:  Retroarch core selection cancelled',level=xbmc.LOGDEBUG)
							elif choose_core_by == 2:
								system_names = sorted(set([x.get('systemname') for x in possible_cores if isinstance(x,dict) and isinstance(x.get('systemname'),str)]))
								xbmc.log(msg='IAGL:  {} Retroarch system options found'.format(len(system_names)),level=xbmc.LOGDEBUG)
								if isinstance(system_names,list) and len(system_names)>0:
									selected_system = xbmcgui.Dialog().select(heading=cm.get_loc(30157),list=system_names,useDetails=False)
									if selected_system>-1:
										display_names = sorted([x.get('display_name') for x in possible_cores if isinstance(x,dict) and isinstance(x.get('display_name'),str) and x.get('systemname')==system_names[selected_system]])
										xbmc.log(msg='IAGL:  {} Retroarch core options found'.format(len(display_names)),level=xbmc.LOGDEBUG)
										if isinstance(display_names,list) and len(display_names)>0:
											selected = xbmcgui.Dialog().select(heading='{}: {}'.format(system_names[selected_system],cm.get_loc(30156)),list=display_names,useDetails=False)
											new_command = next(iter([x.get('command') for x in possible_cores if x.get('display_name')==display_names[selected]]),None)
											if selected>-1 and isinstance(new_command,str):
												if xbmcgui.Dialog().yesno(cm.get_loc(30247),'{}[CR]{}'.format(cm.get_loc(30292),display_names[selected])):
													result1 = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_external_launch_command',new_value=new_command.replace('"','""'))
													result2 = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_uses_apppause',new_value=apppause_setting)
													result3 = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_uses_applaunch',new_value=applaunch_setting)
													if isinstance(result1,int) and isinstance(result2,int) and isinstance(result3,int) and result1>0 and result2>0 and result3>0:
														ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30247),'{}[CR]{}'.format(cm.get_loc(30293),cm.get_loc(30294)))
														xbmc.sleep(config.defaults.get('sleep'))
														xbmc.executebuiltin('Container.Refresh')
											else:
												xbmc.log(msg='IAGL:  Retroarch core selection cancelled',level=xbmc.LOGDEBUG)
							else:
								xbmc.log(msg='IAGL:  Retroarch core selection cancelled',level=xbmc.LOGDEBUG)
					else:
						ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30270),cm.get_loc(30295))
			else:
				ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30270),cm.get_loc(30296))
		elif selected_external_command_types == 1:
			if cm.get_setting('user_launch_os') in config.defaults.get('config_available_systems'):
				if cm.get_setting('kodi_on_launch') == '1':
					applaunch_setting = '0'
					apppause_setting = '0'
				elif cm.get_setting('kodi_on_launch') == '2':
					applaunch_setting = '1'
					apppause_setting = '0'
				elif cm.get_setting('kodi_on_launch') == '3':
					applaunch_setting = '0'
					apppause_setting = '1'
				else: #Prompt user
					selected_external_pre_command_types = xbmcgui.Dialog().select(heading=cm.get_loc(30335),list=[cm.get_loc(30336),cm.get_loc(30337),cm.get_loc(30338)],useDetails=False)
					if selected_external_pre_command_types == 1:
						applaunch_setting = '1'
						apppause_setting = '0'
					elif selected_external_pre_command_types == 2:
						applaunch_setting = '0'
						apppause_setting = '1'
					else:
						applaunch_setting = '0'
						apppause_setting = '0'
				installed_emus = cm.get_other_emus(other_emulator_commands=db.query_db(query=config.database.get('query').get('get_other_emulator_commands').format(cm.get_setting('user_launch_os'),applaunch_setting,apppause_setting),return_as='dict'),other_emulator_settings={x.upper():cm.get_setting(x) for x in config.defaults.get('other_emulator_settings') if isinstance(cm.get_setting(x),str) and len(cm.get_setting(x))>0})
			else: #Android
				installed_emus = db.query_db(query=config.database.get('query').get('get_other_emulator_android').get(cm.get_setting('kodi_saa')).format(cm.get_setting('user_launch_os'),'0','0'),return_as='dict')
				applaunch_setting = '0'
				apppause_setting = '0'
			if isinstance(installed_emus,list) and len(installed_emus)>0:
				xbmc.log(msg='IAGL:  {} external emulator options found'.format(len(installed_emus)),level=xbmc.LOGDEBUG)
				selected = xbmcgui.Dialog().select(heading=cm.get_loc(30158),list=[x.get('display_name') for x in installed_emus],useDetails=False)
				new_command = next(iter([x.get('command') for x in installed_emus if x.get('display_name')==installed_emus[selected].get('display_name')]),None)
				if selected>-1 and isinstance(new_command,str):
					if xbmcgui.Dialog().yesno(cm.get_loc(30247),'{}[CR]{}'.format(cm.get_loc(30292),installed_emus[selected].get('display_name'))):
						result1 = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_external_launch_command',new_value=new_command.replace('"','""'))
						result2 = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_uses_apppause',new_value=apppause_setting)
						result3 = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_uses_applaunch',new_value=applaunch_setting)
						if isinstance(result1,int) and isinstance(result2,int) and isinstance(result3,int) and result1>0 and result2>0 and result3>0:
							if cm.get_setting('user_launch_os') in config.defaults.get('config_available_systems'):
								ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30247),cm.get_loc(30293))
							else:
								ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30247),'{}[CR]{}'.format(cm.get_loc(30293),cm.get_loc(30294)))
							xbmc.sleep(config.defaults.get('sleep'))
							xbmc.executebuiltin('Container.Refresh')
				else:
					xbmc.log(msg='IAGL:  Other emulator core selection cancelled',level=xbmc.LOGDEBUG)
			else:
				ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30270),cm.get_loc(30297))
		elif selected_external_command_types == 2:  #Manual entry
			if cm.get_setting('user_launch_os') not in config.defaults.get('config_available_systems') and cm.get_setting('kodi_saa')=='activities':
				plugin.redirect('/update_android_command/{}/{}'.format(game_list_id,0))
			else:
				current_command = db.get_game_list_user_global_external_launch_command(game_list_id=game_list_id,user_only=True) #Don't utilize the defaults in manual entry, only a user defined entry as the initial entry
				new_command = xbmcgui.Dialog().input(heading=cm.get_loc(30298),defaultt=current_command or '')
				if isinstance(new_command,str) and len(new_command)>0:
					if xbmcgui.Dialog().yesno(cm.get_loc(30247),'{}[CR]{}'.format(cm.get_loc(30292),cm.get_loc(30277))):
						result = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_external_launch_command',new_value=new_command.replace('"','""'))
						if isinstance(result,int) and result>0:
							ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30247),cm.get_loc(30293))
							xbmc.sleep(config.defaults.get('sleep'))
							xbmc.executebuiltin('Container.Refresh')
		elif selected_external_command_types == 3:  #Reset entry
			if xbmcgui.Dialog().yesno(cm.get_loc(30299),cm.get_loc(30300)):
				result1 = db.reset_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_external_launch_command')
				result2 = db.reset_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_uses_apppause')
				result3 = db.reset_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_uses_applaunch')
				if isinstance(result1,int) and isinstance(result2,int) and isinstance(result3,int) and result1>0 and result2>0 and result3>0:
					ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30299),cm.get_loc(30301))
					xbmc.sleep(config.defaults.get('sleep'))
					xbmc.executebuiltin('Container.Refresh')
		else:
			xbmc.log(msg='IAGL:  External command type selection cancelled',level=xbmc.LOGDEBUG)

@plugin.route('/context_menu/action/update_launch_command_from_uid/<game_id>')
def update_game_list_launcher_from_uid(game_id):
	xbmc.log(msg='IAGL:  /update_launch_command_from_uid',level=xbmc.LOGDEBUG)
	game_item_info = next(iter(db.query_db(db.get_query('get_game_list_info_from_game_id',game_id=game_id,game_title_setting=cm.get_setting('game_title_setting')),return_as='dict')),None)
	if xbmcgui.Dialog().yesno(cm.get_loc(30367),cm.get_loc(30365).format(game_item_info.get('label'))):
		plugin.redirect('/context_menu/action/update_launch_command/{}'.format(game_item_info.get('label')))

@plugin.route('/update_android_command/<game_list_id>/<menu_id>')
def update_android_command(game_list_id,menu_id):
	xbmc.log(msg='IAGL:  /update_android_command',level=xbmc.LOGDEBUG)
	if menu_id == '0':
		result = cm.clear_android_activity()
		current_command = db.get_game_list_user_global_external_launch_command(game_list_id=game_list_id,user_only=True) #Don't utilize the defaults in manual entry, only a user defined entry as the initial entry
		try:
			current_command = json.loads(current_command,parse_int=str,parse_float=str)
			if isinstance(current_command,dict):
				for k,v in current_command.items():
					result = cm.update_android_activity(key_in=k,value_in=v)
		except:
			current_command = dict()
	else:
		current_command = cm.get_home_property(type_in='iagl_android_activity')
	if isinstance(current_command,dict) and any([x in config.defaults.get('android_activity_keys') for x in current_command.keys()]):
		lis =  [xbmcgui.ListItem(label=k,label2=cm.convert_android_value(current_command.get(k)),offscreen=True) for k in config.defaults.get('android_activity_keys')]+[xbmcgui.ListItem(label='Submit Command',offscreen=True)]	
	else:
		lis =  [xbmcgui.ListItem(label=k,label2='',offscreen=True) for k in config.defaults.get('android_activity_keys')]+[xbmcgui.ListItem(label='Submit Command',offscreen=True)]
	selected = xbmcgui.Dialog().select(heading='Test',list=lis,useDetails=True)
	if selected>-1 and selected<len(lis)-1:
		new_value = xbmcgui.Dialog().input(heading='{} {}'.format(cm.get_loc(30302),config.defaults.get('android_activity_keys')[selected]),defaultt=cm.convert_android_value(current_command.get(config.defaults.get('android_activity_keys')[selected])))
		result = cm.update_android_activity(key_in=config.defaults.get('android_activity_keys')[selected],value_in=new_value)
		plugin.redirect('/update_android_command/{}/{}'.format(game_list_id,config.defaults.get('android_activity_keys')[selected]))
	else:
		if isinstance(current_command,dict) and isinstance(json.dumps(current_command),str) and len(json.dumps(current_command))>0:
			if xbmcgui.Dialog().yesno(cm.get_loc(30247),'{}[CR]{}'.format(cm.get_loc(30292),cm.get_loc(30277))):
				result = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_external_launch_command',new_value=json.dumps(current_command).replace('"','""')) #Need double quotes to insert into sql
				if isinstance(result,int) and result>0:
					ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30247),cm.get_loc(30293))
					xbmc.sleep(config.defaults.get('sleep'))
					xbmc.executebuiltin('Container.Refresh')
		else:
			xbmc.log(msg='IAGL:  Android external command appears malformed: {}'.format(current_command),level=xbmc.LOGERROR)

@plugin.route('/context_menu/action/hide_game_list/<game_list_id>')
def hide_game_list(game_list_id):
	xbmc.log(msg='IAGL:  /hide_game_list',level=xbmc.LOGDEBUG)
	if xbmcgui.Dialog().yesno(cm.get_loc(30249),'{}[CR]{}'.format(cm.get_loc(30251),game_list_id)):
		result = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_visibility',new_value='hidden')
		if isinstance(result,int) and result>0:
			ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30249),cm.get_loc(30252))
			xbmc.sleep(config.defaults.get('sleep'))
			xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/unhide_game_lists')
def unhide_game_lists():
	xbmc.log(msg='IAGL:  /unhide_game_lists',level=xbmc.LOGDEBUG)
	li = [list_item for list_item,item_path in db.query_db(db.get_query('get_hidden_game_lists')) if isinstance(list_item,xbmcgui.ListItem)]
	if len(li)>0:
		selected = xbmcgui.Dialog().multiselect(heading=cm.get_loc(30024),options=li,useDetails=True) 
		if isinstance(selected,list):
			xbmc.log(msg='IAGL:  Game lists selected to be unhidden: {}'.format([x.getLabel() for ii,x in enumerate(li) if ii in selected]),level=xbmc.LOGDEBUG)
			result = db.unhide_game_lists(lists_in=[x.getLabel() for ii,x in enumerate(li) if ii in selected])
			if isinstance(result,int) and result>0:
				ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30233),cm.get_loc(30255))
		else:
			xbmc.log(msg='IAGL:  Game list unhide cancelled',level=xbmc.LOGDEBUG)
	else:
		ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30253),cm.get_loc(30254))

@plugin.route('/context_menu/action/update_game_dl_path/<game_list_id>')
def update_game_dl_path(game_list_id):
	xbmc.log(msg='IAGL:  /update_game_dl_path',level=xbmc.LOGDEBUG)
	current_dl_path = next(iter(db.query_db(db.get_query('get_game_list_parameter',game_list_id=game_list_id,parameter='user_global_download_path'),return_as='dict')),None)
	if isinstance(current_dl_path,dict) and isinstance(current_dl_path.get('user_global_download_path'),str) and len(current_dl_path.get('user_global_download_path'))>0: #Custom path already set, query about resetting it
		selected = xbmcgui.Dialog().select(heading=cm.get_loc(30160),list=[cm.get_loc(30326),cm.get_loc(30327)],useDetails=False)
		if selected==0:
			result = xbmcgui.Dialog().browse(type=0,heading=cm.get_loc(30160),shares='local')
			if isinstance(result,str) and len(result)>0 and xbmcvfs.exists(result):
				if xbmcgui.Dialog().yesno(cm.get_loc(30248),'{}[CR]{}'.format(cm.get_loc(30322),result[:40]+('...' if len(result)>40 else ''))):
					result2 = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_download_path',new_value=result)
					if isinstance(result2,int) and result2>0:
						ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30233),cm.get_loc(30323))
						xbmc.sleep(config.defaults.get('sleep'))
						xbmc.executebuiltin('Container.Refresh')
			else:
				xbmc.log(msg='IAGL:  Game list download path update cancelled or path invalid',level=xbmc.LOGDEBUG)
		elif selected==1:
			if xbmcgui.Dialog().yesno(cm.get_loc(30327),cm.get_loc(30324)):
				result = db.reset_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_download_path')
				if isinstance(result,int) and result>0:
					ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30299),cm.get_loc(30301))
					xbmc.sleep(config.defaults.get('sleep'))
					xbmc.executebuiltin('Container.Refresh')
		else:
			xbmc.log(msg='IAGL:  Game list download path update cancelled',level=xbmc.LOGDEBUG)
	else:
		result = xbmcgui.Dialog().browse(type=0,heading=cm.get_loc(30160),shares='local')
		if isinstance(result,str) and len(result)>0 and xbmcvfs.exists(result):
			if xbmcgui.Dialog().yesno(cm.get_loc(30248),'{}[CR]{}'.format(cm.get_loc(30322),result[:40]+('...' if len(result)>40 else ''))):
				result2 = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_download_path',new_value=result)
				if isinstance(result2,int) and result2>0:
					ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30233),cm.get_loc(30323))
					xbmc.sleep(config.defaults.get('sleep'))
					xbmc.executebuiltin('Container.Refresh')
		else:
			xbmc.log(msg='IAGL:  Game list download path update cancelled or path invalid',level=xbmc.LOGDEBUG)

@plugin.route('/context_menu/action/update_game_dl_path_from_uid/<game_id>')
def update_game_dl_path_from_uid(game_id):
	xbmc.log(msg='IAGL:  /update_game_dl_path_from_uid',level=xbmc.LOGDEBUG)
	game_item_info = next(iter(db.query_db(db.get_query('get_game_list_info_from_game_id',game_id=game_id,game_title_setting=cm.get_setting('game_title_setting')),return_as='dict')),None)
	if xbmcgui.Dialog().yesno(cm.get_loc(30368),cm.get_loc(30366).format(game_item_info.get('label'))):
		plugin.redirect('/context_menu/action/update_game_dl_path/{}'.format(game_item_info.get('label')))

@plugin.route('/context_menu/action/update_game_list_post_process/<game_list_id>')
def update_game_list_post_process(game_list_id):
	xbmc.log(msg='IAGL:  /update_game_list_post_process',level=xbmc.LOGDEBUG)
	current_default_pp = next(iter(db.query_db(db.get_query('get_game_list_parameter',game_list_id=game_list_id,parameter='default_global_post_download_process'),return_as='dict')),None)
	current_options = cm.get_post_process_options()
	if isinstance(current_default_pp,dict) and isinstance(current_default_pp.get('default_global_post_download_process'),str) and current_default_pp.get('default_global_post_download_process') in current_options.keys():
		preselected = [k for k,v in current_options.items()].index(current_default_pp.get('default_global_post_download_process'))
	else:
		preselected = [k for k,v in current_options.items()].index('no_process')
	selected = xbmcgui.Dialog().select(heading=cm.get_loc(30315),list=[v for k,v in current_options.items()],useDetails=False,preselect=preselected)
	if selected>-1:
		if xbmcgui.Dialog().yesno(cm.get_loc(30315),cm.get_loc(30443)):
			result = [k for k,v in current_options.items()][selected]
			result2 = db.update_game_list_user_parameter(game_list_id=game_list_id,parameter='user_post_download_process',new_value=result)
			if isinstance(result2,int) and result2>0:
				ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30233),cm.get_loc(30444))
				xbmc.sleep(config.defaults.get('sleep'))
				xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/update_game_list_post_process_from_uid/<game_id>')
def update_game_list_post_process_from_uid(game_id):
	xbmc.log(msg='IAGL:  /update_game_list_post_process_from_uid',level=xbmc.LOGDEBUG)
	game_item_info = next(iter(db.query_db(db.get_query('get_game_list_info_from_game_id',game_id=game_id,game_title_setting=cm.get_setting('game_title_setting')),return_as='dict')),None)
	if xbmcgui.Dialog().yesno(cm.get_loc(30315),cm.get_loc(30445).format(game_item_info.get('label'))):
		plugin.redirect('/context_menu/action/update_game_list_post_process/{}'.format(game_item_info.get('label')))

@plugin.route('/context_menu/action/reset_game_list_settings/<game_list_id>')
def reset_game_list_settings(game_list_id):
	xbmc.log(msg='IAGL:  /reset_game_list_settings',level=xbmc.LOGDEBUG)
	if xbmcgui.Dialog().yesno(cm.get_loc(30328),cm.get_loc(30329)):
		results = list()
		results.append(db.reset_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_download_path'))
		results.append(db.reset_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_external_launch_command'))
		results.append(db.reset_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_launcher'))
		results.append(db.reset_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_launch_addon'))
		results.append(db.reset_game_list_user_parameter(game_list_id=game_list_id,parameter='user_post_download_process'))
		results.append(db.reset_game_list_user_parameter(game_list_id=game_list_id,parameter='user_global_visibility'))
		if all([isinstance(x,int) for x in results]) and all([x>0 for x in results]):
			ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30328),cm.get_loc(30330))
			xbmc.sleep(config.defaults.get('sleep'))
			xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/reset_game_list_settings_from_uid/<game_id>')
def reset_game_list_settings_from_uid(game_id):
	xbmc.log(msg='IAGL:  /reset_game_list_settings_from_uid',level=xbmc.LOGDEBUG)
	game_item_info = next(iter(db.query_db(db.get_query('get_game_list_info_from_game_id',game_id=game_id,game_title_setting=cm.get_setting('game_title_setting')),return_as='dict')),None)
	if xbmcgui.Dialog().yesno(cm.get_loc(30328),cm.get_loc(30369).format(game_item_info.get('label'))):
		plugin.redirect('/context_menu/action/reset_game_list_settings/{}'.format(game_item_info.get('label')))

@plugin.route('/context_menu/action/check_ia_login')
def check_ia_login():
	xbmc.log(msg='IAGL:  /check_ia_login',level=xbmc.LOGDEBUG)
	if isinstance(cm.get_setting('ia_u'),str) and isinstance(cm.get_setting('ia_p'),str):
		dp = xbmcgui.DialogProgress()
		dp.create(cm.get_loc(30332),'{}{}'.format(cm.get_loc(30273),'archive.org'))
		dp.update(1)
		dl.downloader.login()
		if dl.downloader.logged_in:
			dp.update(100)
			dp.close()
			ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30233),cm.get_loc(30268))
		else:
			dp.update(100)
			dp.close()
			ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30270),cm.get_loc(30269))
		dp = None
	else:
		ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30065),cm.get_loc(30159))

@plugin.route('/context_menu/action/reset_database')
def reset_database():
	xbmc.log(msg='IAGL:  /reset_database',level=xbmc.LOGDEBUG)
	if xbmcgui.Dialog().yesno(cm.get_loc(30256),cm.get_loc(30257)):
		result = cm.reset_db()
		if result:
			ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30233),cm.get_loc(30258))
			xbmc.sleep(config.defaults.get('sleep'))
			xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/reset_game_lists_to_retroplayer')
def reset_game_lists_to_retroplayer():
	xbmc.log(msg='IAGL:  /reset_game_lists_to_retroplayer',level=xbmc.LOGDEBUG)
	if xbmcgui.Dialog().yesno(cm.get_loc(30393),cm.get_loc(30395)):
		result = db.update_all_game_list_user_parameters(parameter='user_global_launcher',new_value='retroplayer')
		if result:
			ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30233),cm.get_loc(30263))
			xbmc.sleep(config.defaults.get('sleep'))
			xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/reset_game_lists_to_external')
def reset_game_lists_to_external():
	xbmc.log(msg='IAGL:  /reset_game_lists_to_external',level=xbmc.LOGDEBUG)
	if xbmcgui.Dialog().yesno(cm.get_loc(30393),cm.get_loc(30394)):
		result = db.update_all_game_list_user_parameters(parameter='user_global_launcher',new_value='external')
		if result:
			ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30233),cm.get_loc(30262))
			xbmc.sleep(config.defaults.get('sleep'))
			xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/backup_database')
def backup_database():
	xbmc.log(msg='IAGL:  /backup_database',level=xbmc.LOGDEBUG)
	backup_path = xbmcgui.Dialog().browse(type=3,heading=cm.get_loc(30402),shares='')
	if cm.backup_database(backup_path=backup_path):
		ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30233),cm.get_loc(30404))
		xbmc.sleep(config.defaults.get('sleep'))
		xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/restore_database')
def restore_database():
	xbmc.log(msg='IAGL:  /restore_database',level=xbmc.LOGDEBUG)
	backup_file = xbmcgui.Dialog().browse(type=1,heading=cm.get_loc(30403),shares='')
	if cm.restore_database(backup_file=backup_file):
		ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30233),cm.get_loc(30405))
		xbmc.sleep(config.defaults.get('sleep'))
		xbmc.executebuiltin('Container.Refresh')

@plugin.route('/context_menu/action/get_db_stats')
def get_db_stats():
	xbmc.log(msg='IAGL:  /get_db_stats',level=xbmc.LOGDEBUG)
	game_lists = db.query_db(db.get_query('get_db_stats'),return_as='dict')
	meta_lists = db.query_db(db.get_query('get_db_stats2'),return_as='dict')
	default_art = {'clearlogo':config.paths.get('assets_url').format('icon.png'),'thumb':config.paths.get('assets_url').format('icon.png')}
	all_li = xbmcgui.ListItem(label='All Lists',label2='Total Games: {}  - Total 1G1R Games: {}'.format(sum([x.get('total_games') for x in game_lists]),sum([x.get('total_1g1r_games') for x in game_lists if isinstance(x.get('total_1g1r_games'),int)])),offscreen=True)
	all_li.setArt(default_art)
	sys_li = xbmcgui.ListItem(label='Unique Systems',label2='Total: {}'.format(len(set([x.get('system') for x in game_lists]))),offscreen=True)
	sys_li.setArt(default_art)
	meta_lis = [xbmcgui.ListItem(label=x.get('label'),label2='Total: {}'.format(x.get('total_games')),offscreen=True) for x in meta_lists]
	for m in meta_lis:
		m.setArt(default_art)
	li = [all_li]+[sys_li]+meta_lis+[list_item for list_item,item_path in db.query_db(db.get_query('get_db_stats')) if isinstance(list_item,xbmcgui.ListItem)]
	selected = xbmcgui.Dialog().multiselect(heading=cm.get_loc(30341),options=li,useDetails=True) 

@plugin.route('/context_menu/action/get_donate_screen')
def get_donate_screen():
	xbmc.log(msg='IAGL:  /get_donate_screen',level=xbmc.LOGDEBUG)
	donate_dialog = dialogs.get_donate()
	donate_dialog.doModal()
	del donate_dialog

@plugin.route('/wizard_start')
def wizard_start():
	xbmc.log(msg='IAGL:  Wizard script started', level=xbmc.LOGDEBUG)
	xbmc.playSFX(str(config.files.get('sounds').get('wizard_start')),False)
	ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30245),cm.get_loc(30379))
	xbmc.sleep(config.defaults.get('sleep'))
	if xbmcgui.Dialog().yesno(cm.get_loc(30057),cm.get_loc(30380)):
		selected = xbmcgui.Dialog().input(heading=cm.get_loc(30061),defaultt=cm.get_setting('ia_u') or '')
		if isinstance(selected,str) and len(selected)>0 and '@' in selected:
			xbmcaddon.Addon(id=config.addon.get('addon_name')).setSetting(id='ia_u',value=selected)
		else:
			xbmc.log(msg='IAGL: User entered email appears invalid {}'.format(selected),level=xbmc.LOGERROR)
		selected = xbmcgui.Dialog().input(heading=cm.get_loc(30063),option=xbmcgui.ALPHANUM_HIDE_INPUT,defaultt=cm.get_setting('ia_p') or '')
		if isinstance(selected,str) and len(selected)>0:
			xbmcaddon.Addon(id=config.addon.get('addon_name')).setSetting(id='ia_p',value=selected)
		else:
			xbmc.log(msg='IAGL: User entered password appears invalid {}'.format(selected),level=xbmc.LOGERROR)
	if xbmcgui.Dialog().yesno(cm.get_loc(30233),cm.get_loc(30381)):
		xbmcaddon.Addon(id=config.addon.get('addon_name')).setSetting(id='wizard_run',value='true')
		xbmc.playSFX(str(config.files.get('sounds').get('wizard_done')),False)
		plugin.redirect(cm.get_setting('front_page_display'))
	else:
		xbmc.log(msg='IAGL:  Wizard external launching branch selected', level=xbmc.LOGDEBUG)
		if not isinstance(cm.get_setting('user_launch_os'),str):
			detected_platform = cm.check_system_platform()
			selected = xbmcgui.Dialog().select(heading=cm.get_loc(30136),list=[cm.get_loc(30213),cm.get_loc(30137),cm.get_loc(30138),cm.get_loc(30139),cm.get_loc(30144),cm.get_loc(30145),cm.get_loc(30146)],useDetails=False,preselect=detected_platform)
			if selected>0:
				xbmcaddon.Addon(id=config.addon.get('addon_name')).setSetting(id='user_launch_os',value=str(selected))
		if isinstance(cm.get_setting('user_launch_os'),str):
			#Look for app if not on android and not already set
			if cm.get_setting('user_launch_os') not in config.settings.get('user_launch_os').get('android_options') and (isinstance(cm.get_setting('ra_app_path'),str) and len(cm.get_setting('ra_app_path'))==0 or not isinstance(cm.get_setting('ra_app_path'),str)):
				found_app = None
				if isinstance(config.settings.get('user_launch_os').get('possible_app_locations').get(cm.get_setting('user_launch_os')),list):
					for p in config.settings.get('user_launch_os').get('possible_app_locations').get(cm.get_setting('user_launch_os')):
						try:
							if p.exists():
								found_app = p
						except:
							pass
				if found_app is not None:
					xbmc.log(msg='IAGL:  Wizard found retroarch at {}'.format(str(found_app)), level=xbmc.LOGDEBUG)
					xbmcaddon.Addon(id=config.addon.get('addon_name')).setSetting(id='ra_app_path',value=str(found_app))
					if len(str(found_app))>40:
						ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30140),cm.get_loc(30387).format('{}...{}'.format(str(found_app)[0:20],str(found_app)[-14:])))
					else:
						ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30140),cm.get_loc(30387).format(str(found_app)))
				else: #Find app
					if (isinstance(cm.get_setting('ra_app_path'),str) and len(cm.get_setting('ra_app_path'))==0 or not isinstance(cm.get_setting('ra_app_path'),str)):
						xbmc.log(msg='IAGL:  Wizard did not find retroarch, querying user', level=xbmc.LOGDEBUG)
						found_app = xbmcgui.Dialog().browse(type=1,heading=cm.get_loc(30140),shares='')
						if isinstance(found_app,str) and xbmcvfs.exists(found_app):
							xbmcaddon.Addon(id=config.addon.get('addon_name')).setSetting(id='ra_app_path',value=found_app)
			#Look for config if not aleady set
			if (cm.get_setting('user_launch_os') not in config.settings.get('user_launch_os').get('android_options') and (isinstance(cm.get_setting('ra_cfg_path'),str) and len(cm.get_setting('ra_cfg_path'))==0 or not isinstance(cm.get_setting('ra_cfg_path'),str))) or (cm.get_setting('user_launch_os') in config.settings.get('user_launch_os').get('android_options') and (isinstance(cm.get_setting('ra_cfg_path_android'),str) and len(cm.get_setting('ra_cfg_path_android'))==0 or not isinstance(cm.get_setting('ra_cfg_path_android'),str))):
				found_config = None
				if isinstance(config.settings.get('user_launch_os').get('possible_config_locations').get(cm.get_setting('user_launch_os')),list):
					for p in config.settings.get('user_launch_os').get('possible_config_locations').get(cm.get_setting('user_launch_os')):
						try:
							if p.exists():
								found_config = p
						except:
							pass
				if found_config is not None:
					xbmc.log(msg='IAGL:  Wizard found retroarch config at {}'.format(str(found_config)), level=xbmc.LOGDEBUG)
					if len(str(found_config))>40:
						ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30142),cm.get_loc(30388).format('{}...{}'.format(str(found_config)[0:20],str(found_config)[-14:])))
					else:
						ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30142),cm.get_loc(30388).format(str(found_config)))
					if cm.get_setting('user_launch_os') in config.settings.get('user_launch_os').get('android_options'):
						xbmcaddon.Addon(id=config.addon.get('addon_name')).setSetting(id='ra_cfg_path_android',value=str(found_config))
					else:
						xbmcaddon.Addon(id=config.addon.get('addon_name')).setSetting(id='ra_cfg_path',value=str(found_config))
				else: #Find or enter config
					xbmc.log(msg='IAGL:  Wizard did not find retroarch config, querying user', level=xbmc.LOGDEBUG)
					if (cm.get_setting('user_launch_os') not in config.settings.get('user_launch_os').get('android_options') and (isinstance(cm.get_setting('ra_cfg_path'),str) and len(cm.get_setting('ra_cfg_path'))==0 or not isinstance(cm.get_setting('ra_cfg_path'),str))):
						found_config = xbmcgui.Dialog().browse(type=1,heading=cm.get_loc(30142),shares='')
						if isinstance(found_config,str) and xbmcvfs.exists(found_config):
							xbmcaddon.Addon(id=config.addon.get('addon_name')).setSetting(id='ra_cfg_path',value=found_config)
					if (cm.get_setting('user_launch_os') in config.settings.get('user_launch_os').get('android_options') and (isinstance(cm.get_setting('ra_cfg_path_android'),str) and len(cm.get_setting('ra_cfg_path_android'))==0 or not isinstance(cm.get_setting('ra_cfg_path_android'),str))):
						ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30360),cm.get_loc(30396))
						found_config = xbmcgui.Dialog().input(heading=cm.get_loc(30360))
						if isinstance(found_config,str) and len(found_config)>0:
							xbmcaddon.Addon(id=config.addon.get('addon_name')).setSetting(id='ra_cfg_path_android',value=found_config)
		if (cm.get_setting('user_launch_os') in config.settings.get('user_launch_os').get('android_options') and (isinstance(cm.get_setting('ra_cores_path_android'),str) and len(cm.get_setting('ra_cores_path_android'))==0 or not isinstance(cm.get_setting('ra_cores_path_android'),str))):
			ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30362),cm.get_loc(30397))
			found_core_dir = xbmcgui.Dialog().input(heading=cm.get_loc(30362))
			if isinstance(found_core_dir,str) and len(found_core_dir)>0:
				xbmcaddon.Addon(id=config.addon.get('addon_name')).setSetting(id='ra_cores_path_android',value=found_core_dir)
		if cm.get_setting('user_launch_os') in config.settings.get('user_launch_os').get('android_options'):
			ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30201),cm.get_loc(30422))
			result = xbmcgui.Dialog().browse(type=0,heading=cm.get_loc(30356),shares='')
			if isinstance(result,str) and xbmcvfs.exists(result):
				xbmcaddon.Addon(id=config.addon.get('addon_name')).setSetting(id='alt_temp_dl',value=result)
		selected = xbmcgui.Dialog().select(heading=cm.get_loc(30319),list=[cm.get_loc(30382),cm.get_loc(30383),cm.get_loc(30384)],useDetails=False,preselect=0)
		if selected>-1:
			if selected == 0:
				result = db.update_all_game_list_user_parameters(parameter='user_global_launcher',new_value='external')
				if isinstance(result,int) and result>0:
					ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30233),cm.get_loc(30262))
			elif selected == 2:
				result = db.reset_all_game_list_user_parameters(parameter='user_global_launcher')
				if isinstance(result,int) and result>0:
					ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30233),cm.get_loc(30301))
			else:
				li = [list_item for list_item,item_path in db.query_db(db.get_query('search_random_get_game_lists'))if isinstance(list_item,xbmcgui.ListItem)]
				selected = xbmcgui.Dialog().multiselect(heading=cm.get_loc(30024),options=li,useDetails=True)
				if isinstance(selected,list):
					xbmc.log(msg='IAGL:  Game lists selected for external launching: {}'.format([x.getLabel() for ii,x in enumerate(li) if ii in selected]),level=xbmc.LOGDEBUG)
					result = db.update_some_game_list_user_parameters(parameter='user_global_launcher',new_value='external',game_lists=[x.getLabel() for ii,x in enumerate(li) if ii in selected])
					if isinstance(result,int) and result>0:
						ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30233),cm.get_loc(30385).format(len([x.getLabel() for ii,x in enumerate(li) if ii in selected])))
			if xbmcgui.Dialog().ok(cm.get_loc(30233),cm.get_loc(30386)):
				xbmcaddon.Addon(id=config.addon.get('addon_name')).setSetting(id='wizard_run',value='true')
				xbmc.playSFX(str(config.files.get('sounds').get('wizard_done')),False)
				plugin.redirect(cm.get_setting('front_page_display'))
				ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30233),cm.get_loc(30389)) #End
		else:
			xbmc.log(msg='IAGL:  Wizard external launching branch cancelled', level=xbmc.LOGDEBUG)
			ok_ret = xbmcgui.Dialog().ok(cm.get_loc(30233),cm.get_loc(30389)) #End

if __name__ == '__main__':
	plugin.run(sys.argv)
	del plugin
	# del iagl_addon, iagl_download, iagl_post_process, iagl_launch, clear_mem_cache, get_mem_cache, set_mem_cache, get_next_page_listitem, get_setting_as, get_game_listitem, clean_image_entry, clean_trailer_entry, loc_str, check_if_file_exists, check_if_dir_exists, check_and_close_notification, get_history_listitem, get_netplay_listitem, update_listitem_title, get_post_dl_commands, add_game_to_favorites, clean_file_folder_name, generate_discord_announcement, get_uuid, get_blank_favorites_listitem, get_database_listitem, url_quote_query, delete_file_pathlib, remove_game_from_favorites, zachs_debug, ADDON_SPECIAL_PATH #Delete all locally imported stuff to avoid memory leaks
