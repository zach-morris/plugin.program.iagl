#Internet Archive Game Launcher v2.X
#Zach Morris
#https://github.com/zach-morris/plugin.program.iagl
from kodi_six import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs
xbmc.log(msg='IAGL:  Lets Play!', level=xbmc.LOGNOTICE)
xbmc.log(msg='IAGL:  Version %(addon_version)s' % {'addon_version': xbmcaddon.Addon().getAddonInfo('version')}, level=xbmc.LOGDEBUG)
import routing
from resources.lib.main import *

try:
	from urllib.parse import quote_plus as url_quote
	from urllib.parse import unquote_plus as url_unquote
	xbmc.log(msg='IAGL:  Using python 3 urrlib', level=xbmc.LOGDEBUG)
except:
	from urllib import quote_plus as url_quote
	from urllib import unquote_plus as url_unquote
	xbmc.log(msg='IAGL:  Using python 2 urrlib', level=xbmc.LOGDEBUG)

## Plugin Initialization Stuff ##
plugin = routing.Plugin() #Plugin Handle
IAGL = iagl_utils() #IAGL utils Class
IAGL.initialize_IAGL_settings() #Initialize some addon stuff
xbmcplugin.setContent(plugin.handle,IAGL.handle.getSetting(id='iagl_setting_setcontent')) #Define the content type per settings
IAGL.archive_listing_settings_route = IAGL.archive_listing_settings_routes[IAGL.archive_listing_settings.split('|').index(IAGL.handle.getSetting(id='iagl_setting_archive_listings'))]
IAGL.current_game_listing_route = IAGL.game_listing_settings_routes[IAGL.game_listing_settings.split('|').index(IAGL.handle.getSetting(id='iagl_setting_listing'))]

## Plugin Routes ##
@plugin.route('/')
def iagl_main():
	if not IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_hidden_bool_tou')):
		TOU_Dialog = iagl_TOUdialog('script-IAGL-TOU.xml',IAGL.get_addon_install_path(),'Default','1080i')
		TOU_Dialog.doModal()
		if IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_hidden_bool_tou')):
			IAGL.check_for_new_dat_files()
			plugin.redirect('/archives/'+IAGL.archive_listing_settings_route)
		else:
			xbmcplugin.endOfDirectory(plugin.handle)
	else:
		IAGL.check_for_new_dat_files()
		plugin.redirect('/archives/'+IAGL.archive_listing_settings_route)

@plugin.route('/archives/choose_from_list')
def list_archives_browse():
	list_method = 'choose_from_list'
	for list_item in IAGL.get_browse_lists_as_listitems():
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for_path('/archives/'+url_quote(list_item.getLabel2())),list_item, True)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/archives/all')
def list_archives_all():
	IAGL.current_game_listing_route = IAGL.game_listing_settings_routes[IAGL.game_listing_settings.split('|').index(IAGL.handle.getSetting(id='iagl_setting_listing'))]
	# for ii,list_item in enumerate(IAGL.get_game_lists_as_listitems()):
	for list_item in IAGL.get_game_lists_as_listitems():
		if IAGL.current_game_listing_route == 'list_all':
			if list_item.getProperty('emu_visibility') != 'hidden':
				xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for_path('/game_list/'+IAGL.current_game_listing_route+'/'+url_quote(list_item.getProperty('dat_filename'))+'/1'),IAGL.add_list_context_menus(list_item,url_quote(list_item.getProperty('dat_filename'))), True)
		else:
			if list_item.getProperty('emu_visibility') != 'hidden':
				xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for_path('/game_list/'+IAGL.current_game_listing_route+'/'+url_quote(list_item.getProperty('dat_filename'))),IAGL.add_list_context_menus(list_item,url_quote(list_item.getProperty('dat_filename'))), True)
		# xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game_list, game_list_id=url_quote(list_item.getProperty('dat_filename')), page_number=1),list_item, True)
	if IAGL.check_to_show_history():
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for_path('/game_list/'+IAGL.current_game_listing_route+'/game_history/1'),IAGL.get_game_history_listitem(), True)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/archives/categorized')
def list_archives_by_category():
	# for ii,list_item in enumerate(IAGL.get_game_list_categories_as_listitems()):
	for list_item in IAGL.get_game_list_categories_as_listitems():
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game_lists_in_category, category_id=url_quote(list_item.getLabel())),list_item, True)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/archives/categorized/<category_id>')
def get_game_lists_in_category(category_id):
	IAGL.current_game_listing_route = IAGL.game_listing_settings_routes[IAGL.game_listing_settings.split('|').index(IAGL.handle.getSetting(id='iagl_setting_listing'))]
	# for ii,list_item in enumerate(IAGL.get_game_lists_as_listitems(url_unquote(category_id))):
	for list_item in IAGL.get_game_lists_as_listitems(url_unquote(category_id)):
		if IAGL.current_game_listing_route == 'list_all':
			if list_item.getProperty('emu_visibility') != 'hidden':
				xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for_path('/game_list/'+IAGL.current_game_listing_route+'/'+url_quote(list_item.getProperty('dat_filename'))+'/1'),IAGL.add_list_context_menus(list_item,url_quote(list_item.getProperty('dat_filename'))), True)
		else:
			if list_item.getProperty('emu_visibility') != 'hidden':
				xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for_path('/game_list/'+IAGL.current_game_listing_route+'/'+url_quote(list_item.getProperty('dat_filename'))),IAGL.add_list_context_menus(list_item,url_quote(list_item.getProperty('dat_filename'))), True)
		# xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game_list, game_list_id=url_quote(list_item.getProperty('dat_filename')), page_number=1),list_item, True)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/game_list/choose_from_list/game_history/1')
def get_choose_list_history_redirect():
	plugin.redirect('/game_list/choose_from_list/game_history')

@plugin.route('/game_list/choose_from_list/<game_list_id>')
def get_choose_list(game_list_id):
	list_method = 'choose_from_list'
	xbmc.log(msg='IAGL:  Getting game list %(game_list_id)s, display method %(list_method)s' % {'game_list_id': game_list_id,'list_method': list_method}, level=xbmc.LOGDEBUG)
	for list_item in IAGL.get_game_list_choose_as_listitems(game_list_id):
		if url_quote(list_item.getLabel2()) == 'list_all':
			xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for_path('/game_list/'+url_quote(list_item.getLabel2())+'/'+game_list_id+'/1'),list_item, True)
		else:
			xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for_path('/game_list/'+url_quote(list_item.getLabel2())+'/'+game_list_id),list_item, True)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/game_list/alphabetical/<game_list_id>')
def get_alphabetical_list(game_list_id):
	list_method = 'alphabetical'
	xbmc.log(msg='IAGL:  Getting game list %(game_list_id)s alphabetically, display method %(list_method)s' % {'game_list_id': game_list_id,'list_method': list_method}, level=xbmc.LOGDEBUG)
	for list_item in IAGL.get_alphabetical_as_listitem(game_list_id):
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_games_with_letter, letter=url_quote(list_item.getLabel2()), game_list_id=game_list_id, page_number=1),list_item, True)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/game_list/alphabetical/<letter>/<game_list_id>/')
def get_alphabetical_redirect(letter,game_list_id):
	plugin.redirect('/game_list/alphabetical/'+letter+'/'+game_list_id+'/1')

@plugin.route('/game_list/alphabetical/<letter>/<game_list_id>/<page_number>')
def get_games_with_letter(letter,game_list_id,page_number=1):
	list_method = 'alphabetical'
	xbmc.log(msg='IAGL:  Getting game list %(game_list_id)s alphabetically, display method %(list_method)s, starting with letter %(letter)s, with %(items_pp)s items per page, on page %(page_number)s' % {'game_list_id': game_list_id,'list_method': list_method, 'letter': url_unquote(letter), 'items_pp': str(IAGL.get_items_per_page()), 'page_number': page_number}, level=xbmc.LOGDEBUG)
	current_page, page_info = IAGL.get_games_as_listitems(url_unquote(game_list_id),list_method,letter,page_number)
	for list_item in current_page:
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game, game_list_id=url_quote(game_list_id), game_id=url_quote(list_item.getLabel2())),list_item, True) #Method 1, dont pass json as arg
		# xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game, game_list_id=url_quote(game_list_id), game_id=url_quote(list_item.getLabel2()), json=list_item.getProperty('iagl_json')),list_item, True) #Method 2, pass json as arg, works well for Kodi favs, but is 'messy'
	next_page_li = IAGL.get_next_page_listitem(page_info['page'],page_info['page_count'],page_info['next_page'],page_info['item_count'])
	if next_page_li is not None:
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_games_with_letter, letter=letter, game_list_id=game_list_id, page_number=page_info['next_page']),next_page_li, True)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/game_list/list_by_genre/<game_list_id>')
def get_genre_list(game_list_id):
	list_method = 'list_by_genre'
	xbmc.log(msg='IAGL:  Getting game list %(game_list_id)s by genre, display method %(list_method)s' % {'game_list_id': game_list_id,'list_method': list_method}, level=xbmc.LOGDEBUG)
	for list_item in IAGL.get_game_list_genres_as_listitems(game_list_id):
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_games_with_genre, genre=url_quote(list_item.getLabel2()), game_list_id=game_list_id, page_number=1),list_item, True)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/game_list/list_by_genre/<genre>/<game_list_id>/')
def get_genres_redirect(genre,game_list_id):
	plugin.redirect('/game_list/list_by_genre/'+genre+'/'+game_list_id+'/1')

@plugin.route('/game_list/list_by_genre/<genre>/<game_list_id>/<page_number>')
def get_games_with_genre(genre,game_list_id,page_number=1):
	list_method = 'list_by_genre'
	xbmc.log(msg='IAGL:  Getting game list %(game_list_id)s by genre, display method %(list_method)s, with the genre %(genre)s, with %(items_pp)s items per page, on page %(page_number)s' % {'game_list_id': game_list_id,'list_method': list_method, 'genre': url_unquote(genre), 'items_pp': str(IAGL.get_items_per_page()), 'page_number': page_number}, level=xbmc.LOGDEBUG)
	current_page, page_info = IAGL.get_games_as_listitems(url_unquote(game_list_id),list_method,url_unquote(genre),page_number)
	for list_item in current_page:
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game, game_list_id=url_quote(game_list_id), game_id=url_quote(list_item.getLabel2())),list_item, True) #Method 1, dont pass json as arg
		# xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game, game_list_id=url_quote(game_list_id), game_id=url_quote(list_item.getLabel2()), json=list_item.getProperty('iagl_json')),list_item, True) #Method 2, pass json as arg, works well for Kodi favs, but is 'messy'
	next_page_li = IAGL.get_next_page_listitem(page_info['page'],page_info['page_count'],page_info['next_page'],page_info['item_count'])
	if next_page_li is not None:
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_games_with_genre, genre=genre, game_list_id=game_list_id, page_number=page_info['next_page']),next_page_li, True)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/game_list/list_by_year/<game_list_id>')
def get_years_list(game_list_id):
	list_method = 'list_by_year'
	xbmc.log(msg='IAGL:  Getting game list %(game_list_id)s by year, display method %(list_method)s' % {'game_list_id': game_list_id,'list_method': list_method}, level=xbmc.LOGDEBUG)
	for list_item in IAGL.get_game_list_years_as_listitems(game_list_id):
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_games_with_year, year=url_quote(list_item.getLabel2()), game_list_id=game_list_id, page_number=1),list_item, True)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/game_list/list_by_year/<year>/<game_list_id>/')
def get_years_redirect(year,game_list_id):
	plugin.redirect('/game_list/list_by_year/'+year+'/'+game_list_id+'/1')

@plugin.route('/game_list/list_by_year/<year>/<game_list_id>/<page_number>')
def get_games_with_year(year,game_list_id,page_number=1):
	list_method = 'list_by_year'
	xbmc.log(msg='IAGL:  Getting game list %(game_list_id)s by year, display method %(list_method)s, with the year %(year)s, with %(items_pp)s items per page, on page %(page_number)s' % {'game_list_id': game_list_id,'list_method': list_method, 'year': url_unquote(year), 'items_pp': str(IAGL.get_items_per_page()), 'page_number': page_number}, level=xbmc.LOGDEBUG)
	current_page, page_info = IAGL.get_games_as_listitems(url_unquote(game_list_id),list_method,url_unquote(year),page_number)
	for list_item in current_page:
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game, game_list_id=url_quote(game_list_id), game_id=url_quote(list_item.getLabel2())),list_item, True) #Method 1, dont pass json as arg
		# xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game, game_list_id=url_quote(game_list_id), game_id=url_quote(list_item.getLabel2()), json=list_item.getProperty('iagl_json')),list_item, True) #Method 2, pass json as arg, works well for Kodi favs, but is 'messy'
	next_page_li = IAGL.get_next_page_listitem(page_info['page'],page_info['page_count'],page_info['next_page'],page_info['item_count'])
	if next_page_li is not None:
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_games_with_year, year=year, game_list_id=game_list_id, page_number=page_info['next_page']),next_page_li, True)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/game_list/list_by_players/<game_list_id>')
def get_players_list(game_list_id):
	list_method = 'list_by_players'
	xbmc.log(msg='IAGL:  Getting game list %(game_list_id)s by num players, display method %(list_method)s' % {'game_list_id': game_list_id,'list_method': list_method}, level=xbmc.LOGDEBUG)
	for list_item in IAGL.get_game_list_players_as_listitems(game_list_id):
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_games_with_players, nplayers=url_quote(list_item.getLabel2()), game_list_id=game_list_id, page_number=1),list_item, True)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/game_list/list_by_players/<nplayers>/<game_list_id>/')
def get_players_redirect(nplayers,game_list_id):
	plugin.redirect('/game_list/list_by_players/'+nplayers+'/'+game_list_id+'/1')

@plugin.route('/game_list/list_by_players/<nplayers>/<game_list_id>/<page_number>')
def get_games_with_players(nplayers,game_list_id,page_number=1):
	list_method = 'list_by_players'
	xbmc.log(msg='IAGL:  Getting game list %(game_list_id)s by num players, display method %(list_method)s, with the num players %(nplayers)s, with %(items_pp)s items per page, on page %(page_number)s' % {'game_list_id': game_list_id,'list_method': list_method, 'nplayers': url_unquote(nplayers), 'items_pp': str(IAGL.get_items_per_page()), 'page_number': page_number}, level=xbmc.LOGDEBUG)
	current_page, page_info = IAGL.get_games_as_listitems(url_unquote(game_list_id),list_method,url_unquote(nplayers),page_number)
	for list_item in current_page:
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game, game_list_id=url_quote(game_list_id), game_id=url_quote(list_item.getLabel2())),list_item, True) #Method 1, dont pass json as arg
		# xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game, game_list_id=url_quote(game_list_id), game_id=url_quote(list_item.getLabel2()), json=list_item.getProperty('iagl_json')),list_item, True) #Method 2, pass json as arg, works well for Kodi favs, but is 'messy'
	next_page_li = IAGL.get_next_page_listitem(page_info['page'],page_info['page_count'],page_info['next_page'],page_info['item_count'])
	if next_page_li is not None:
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_games_with_players, nplayers=nplayers, game_list_id=game_list_id, page_number=page_info['next_page']),next_page_li, True)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/game_list/list_by_studio/<game_list_id>')
def get_studio_list(game_list_id):
	list_method = 'list_by_studio'
	xbmc.log(msg='IAGL:  Getting game list %(game_list_id)s by studio, display method %(list_method)s' % {'game_list_id': game_list_id,'list_method': list_method}, level=xbmc.LOGDEBUG)
	for list_item in IAGL.get_game_list_studios_as_listitems(game_list_id):
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_games_with_studio, studio=url_quote(list_item.getLabel2()), game_list_id=game_list_id, page_number=1),list_item, True)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/game_list/list_by_studio/<studio>/<game_list_id>/<page_number>')
def get_games_with_studio(studio,game_list_id,page_number=1):
	list_method = 'list_by_studio'
	xbmc.log(msg='IAGL:  Getting game list %(game_list_id)s by studio, display method %(list_method)s, with the studio %(studio)s, with %(items_pp)s items per page, on page %(page_number)s' % {'game_list_id': game_list_id,'list_method': list_method, 'studio': url_unquote(studio), 'items_pp': str(IAGL.get_items_per_page()), 'page_number': page_number}, level=xbmc.LOGDEBUG)
	current_page, page_info = IAGL.get_games_as_listitems(url_unquote(game_list_id),list_method,url_unquote(studio),page_number)
	for list_item in current_page:
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game, game_list_id=url_quote(game_list_id), game_id=url_quote(list_item.getLabel2())),list_item, True) #Method 1, dont pass json as arg
		# xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game, game_list_id=url_quote(game_list_id), game_id=url_quote(list_item.getLabel2()), json=list_item.getProperty('iagl_json')),list_item, True) #Method 2, pass json as arg, works well for Kodi favs, but is 'messy'
	next_page_li = IAGL.get_next_page_listitem(page_info['page'],page_info['page_count'],page_info['next_page'],page_info['item_count'])
	if next_page_li is not None:
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_games_with_studio, studio=studio, game_list_id=game_list_id, page_number=page_info['next_page']),next_page_li, True)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/game_list/list_all/<game_list_id>/')
def get_all_games_redirect(game_list_id):
	plugin.redirect('/game_list/list_all/'+game_list_id+'/1')

@plugin.route('/game_list/list_all/<game_list_id>/<page_number>')
def get_game_list(game_list_id,page_number=1):
	list_method = 'list_all'
	xbmc.log(msg='IAGL:  Getting game list %(game_list_id)s, display method %(list_method)s with %(items_pp)s items per page, on page %(page_number)s' % {'game_list_id': game_list_id,'list_method': list_method, 'items_pp': str(IAGL.get_items_per_page()), 'page_number': page_number}, level=xbmc.LOGDEBUG)
	current_page, page_info = IAGL.get_games_as_listitems(url_unquote(game_list_id),list_method,None,page_number)
	for list_item in current_page:
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game, game_list_id=url_quote(game_list_id), game_id=url_quote(list_item.getLabel2())),IAGL.add_game_context_menus(list_item,game_list_id,url_quote(list_item.getLabel2()),page_info['categories']), True) #Method 1, dont pass json as arg
		# xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game, game_list_id=url_quote(game_list_id), game_id=url_quote(list_item.getLabel2()), json=list_item.getProperty('iagl_json')),list_item, True) #Method 2, pass json as arg, works well for Kodi favs, but is 'messy'
	next_page_li = IAGL.get_next_page_listitem(page_info['page'],page_info['page_count'],page_info['next_page'],page_info['item_count'])
	if next_page_li is not None:
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game_list, list_method=list_method, game_list_id=game_list_id, page_number=page_info['next_page']),next_page_li, True)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/game/<game_list_id>/<game_id>')
def get_game(game_list_id,game_id):
	list_method = 'list_single_game'
	xbmc.log(msg='IAGL:  Getting game ID: %(game_id)s in game category %(game_list_id)s' % {'game_list_id': game_list_id, 'game_id': game_id}, level=xbmc.LOGDEBUG)
	current_game_json = xbmc.getInfoLabel('ListItem.Property(iagl_json)') #Method 1, get current game json manifest
	return_to_home_from_infodialog = False

	#No json is available from listitem, so this must be a link from a favorite
	if current_game_json is None or len(current_game_json)<1:
		current_page, page_info = IAGL.get_games_as_listitems(url_unquote(game_list_id),list_method,url_unquote(game_id),1)
		current_game_json = current_page[0].getProperty('iagl_json')
		return_to_home_from_infodialog = True

	#Check to see if its an IAGL favorite route
	current_route = IAGL.get_route_from_json(current_game_json)
	if current_route is not None and 'plugin://plugin.program.iagl' in current_route[0]:
		route_parse = current_route[0].replace('plugin://plugin.program.iagl/game','').replace('plugin://plugin.program.iagl','').split('/')
		current_page, page_info = IAGL.get_games_as_listitems(url_unquote(route_parse[1]),list_method,url_unquote(route_parse[2]),1)
		current_game_json = current_page[0].getProperty('iagl_json')
		xbmc.log(msg='IAGL:  Rerouting to %(game_id)s in game category %(game_list_id)s' % {'game_list_id': route_parse[1], 'game_id': route_parse[2]}, level=xbmc.LOGDEBUG)
		
	#Info Dialog
	current_game = dict()
	current_game['game_id'], current_game['listitem'], current_game['fanarts'], current_game['boxart_and_snapshots'], current_game['banners'], current_game['trailer'] = IAGL.get_gamelistitem_from_json(current_game_json)
	current_game['return_home'] = return_to_home_from_infodialog
	current_game['autoplay_trailer'] = IAGL.handle.getSetting(id='iagl_setting_autoplay_trailer')
	current_game['json'] = current_game_json
	if IAGL.handle.getSetting(id='iagl_setting_default_action') == 'ROM Info Page':
		IAGL_Dialog = iagl_infodialog('script-IAGL-infodialog.xml',IAGL.get_addon_install_path(),'Default','1080i',current_game=current_game)
		IAGL_Dialog.doModal()
	elif IAGL.handle.getSetting(id='iagl_setting_default_action') == 'Download Only':
		IAGL_DL = iagl_download(current_game['json']) #Initialize download object
		download_and_process_success = IAGL_DL.download_and_process_game_files() #Download files
		current_dialog = xbmcgui.Dialog()
		if False in download_and_process_success:  #Bad files found
			if True in download_and_process_success:  #Good and Bad files found
				ok_ret = current_dialog.ok('Error','%(game_title)s partial download failed[CR]%(fail_reason)s' % {'game_title': IAGL_DL.current_game_title, 'fail_reason': IAGL_DL.download_fail_reason})
			else:  #Only bad files found
				ok_ret = current_dialog.ok('Error','%(game_title)s download failed[CR]%(fail_reason)s' % {'game_title': IAGL_DL.current_game_title, 'fail_reason': IAGL_DL.download_fail_reason})
		else:  #So far so good, now process the files
			ok_ret = current_dialog.ok('Complete','%(game_title)s was successfully downloaded' % {'game_title': IAGL_DL.current_game_title})
	elif IAGL.handle.getSetting(id='iagl_setting_default_action') == 'Download and Launch':
		IAGL_DL = iagl_download(current_game['json']) #Initialize download object
		download_and_process_success = IAGL_DL.download_and_process_game_files() #Download files
		if False not in download_and_process_success:
			IAGL_LAUNCH = iagl_launch(current_game['json'],IAGL_DL.current_processed_files,current_game['game_id']) #Initialize launch object
			launch_success = IAGL_LAUNCH.launch() #Launch Game
			if launch_success:
				xbmc.log(msg='IAGL:  Game Launched: %(game_title)s' % {'game_title': IAGL_DL.current_game_title}, level=xbmc.LOGDEBUG)
		else:
			current_dialog = xbmcgui.Dialog()
			ok_ret = current_dialog.ok('Error','%(game_title)s failed to launch[CR]%(fail_reason)s' % {'game_title': IAGL_DL.current_game_title, 'fail_reason': IAGL_DL.download_fail_reason})
	else:
		xbmc.log(msg='IAGL:  Unkown default action in settings',level=xbmc.LOGERROR)

@plugin.route('/context_menu/<game_list_id>/<setting_id>')
def update_game_list(game_list_id,setting_id):
	xbmc.log(msg='IAGL:  Context menu called for %(game_list_id)s setting  %(setting_id)s' % {'game_list_id': game_list_id, 'setting_id': setting_id}, level=xbmc.LOGDEBUG)
	current_game_list = dict()

	# url_quote(game_list_id)
	current_game_lists = IAGL.get_game_lists()
	try:
		current_index = [x for x in current_game_lists.get('dat_filename')].index(url_quote(game_list_id))
	except Exception as exc:
		current_index = None
		xbmc.log(msg='IAGL:  The settings for %(game_list_id)s could not be found.  Exception %(exc)s' % {'game_list_id': game_list_id, 'exc': exc}, level=xbmc.LOGERROR)

	if current_index is not None:
		current_game_list['game_list_id'] = game_list_id
		current_game_list['fullpath'] = [x for x in current_game_lists.get('fullpath')][current_index]
		#Metadata
		current_game_list['emu_name'] = [x for x in current_game_lists.get('emu_name')][current_index]
		current_game_list['emu_category'] = [x for x in current_game_lists.get('emu_category')][current_index]
		current_game_list['emu_description'] = [x for x in current_game_lists.get('emu_description')][current_index]
		current_game_list['emu_comment'] = [x for x in current_game_lists.get('emu_comment')][current_index]
		current_game_list['emu_author'] = [x for x in current_game_lists.get('emu_author')][current_index]
		current_game_list['emu_trailer'] = [x for x in current_game_lists.get('emu_trailer')][current_index]
		current_game_list['emu_date'] = [x for x in current_game_lists.get('emu_date')][current_index]
		#Art
		current_game_list['emu_thumb'] = [x for x in current_game_lists.get('emu_thumb')][current_index]
		current_game_list['emu_logo'] = [x for x in current_game_lists.get('emu_logo')][current_index]
		current_game_list['emu_banner'] = [x for x in current_game_lists.get('emu_banner')][current_index]
		current_game_list['emu_fanart'] = [x for x in current_game_lists.get('emu_fanart')][current_index]
		#Visibility
		current_game_list['emu_visibility'] = [x for x in current_game_lists.get('emu_visibility')][current_index]
		#Download Path
		current_game_list['emu_downloadpath'] = [x for x in current_game_lists.get('emu_downloadpath')][current_index]
		#Launcher
		current_game_list['emu_launcher'] = [x for x in current_game_lists.get('emu_launcher')][current_index]
		#Launch Command
		current_game_list['emu_default_addon'] = [x for x in current_game_lists.get('emu_default_addon')][current_index]
		current_game_list['emu_ext_launch_cmd'] = [x for x in current_game_lists.get('emu_ext_launch_cmd')][current_index]
		#Post DL Command
		current_game_list['emu_postdlaction'] = [x for x in current_game_lists.get('emu_postdlaction')][current_index]

		current_choice, current_key = IAGL.get_user_context_choice(setting_id)
		if current_choice is not None:
			new_value = IAGL.get_user_context_entry(current_key,current_game_list[current_key],current_choice)
			if new_value is not None:
				IAGL.update_xml_header(current_game_list['fullpath'],current_key,new_value,False)
				xbmc.executebuiltin('Container.Refresh')
			else:
				xbmc.log(msg='IAGL:  Update to game list value cancelled',level=xbmc.LOGDEBUG)
		else:
			if current_key == 'refresh_list':
				xbmc.log(msg='IAGL:  Refreshing cache for game list %(game_list_id)s' % {'game_list_id': game_list_id}, level=xbmc.LOGDEBUG)
				if IAGL.delete_list_cache(game_list_id):
					current_dialog = xbmcgui.Dialog()
					ok_ret = current_dialog.ok('Complete','Cache cleared for %(game_list_id)s' % {'game_list_id': game_list_id})
					IAGL.delete_dat_file_cache()
			elif current_key == 'view_list_settings':
				xbmc.log(msg='IAGL:  Show settings for game list %(game_list_id)s' % {'game_list_id': game_list_id}, level=xbmc.LOGDEBUG)
				current_settings_text = IAGL.get_list_settings_text(current_game_list)
				plugin.redirect('/text_viewer')
			else:
				xbmc.log(msg='IAGL:  Update to game list value cancelled',level=xbmc.LOGDEBUG)

@plugin.route('/games_context_menu/<game_list_id>/<game_id>/<setting_id>')
def update_game_item(game_list_id,game_id,setting_id):
	xbmc.log(msg='IAGL:  Game Context menu called for game %(game_id)s in list %(game_list_id)s setting %(setting_id)s' % {'game_id':game_id, 'game_list_id': game_list_id, 'setting_id': setting_id}, level=xbmc.LOGDEBUG)
	current_page, page_info = IAGL.get_games_as_listitems(url_unquote(game_list_id),'list_single_game',url_unquote(game_id),1)
	current_game_json = current_page[0].getProperty('iagl_json')
	if setting_id == 'add':
		IAGL.add_game_to_IAGL_favorites(game_list_id,game_id,current_game_json)
	elif setting_id == 'remove':
		IAGL.remove_game_from_IAGL_favorites(game_list_id,game_id,current_game_json)
		xbmc.executebuiltin('Container.Refresh')
	else:
		xbmc.log(msg='IAGL:  Unknown game context menu setting  %(setting_id)s' % {'setting_id': setting_id}, level=xbmc.LOGERROR)

@plugin.route('/text_viewer')
def iagl_text_viewer():
	IAGL_Dialog = iagl_textviewer_dialog('script-IAGL-textviewer.xml',IAGL.get_addon_install_path(),'Default','1080i')
	IAGL_Dialog.doModal()

if __name__ == '__main__':
	plugin.run()