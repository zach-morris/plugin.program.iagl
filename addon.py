#Internet Archive Game Launcher v2.X
#Zach Morris
#https://github.com/zach-morris/plugin.program.iagl
from kodi_six import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs
xbmc.log(msg='IAGL:  Lets Play!', level=xbmc.LOGNOTICE)
xbmc.log(msg='IAGL:  Version %(addon_version)s' % {'addon_version': xbmcaddon.Addon().getAddonInfo('version')}, level=xbmc.LOGDEBUG)
import routing, sys
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
# IAGL.archive_listing_settings_route = IAGL.archive_listing_settings_routes[IAGL.archive_listing_settings.split('|').index(IAGL.handle.getSetting(id='iagl_setting_archive_listings'))] #Old method pre language update
IAGL.archive_listing_settings_route = IAGL.archive_listing_settings_routes[int(IAGL.handle.getSetting(id='iagl_setting_archive_listings'))]
# IAGL.current_game_listing_route = IAGL.game_listing_settings_routes[IAGL.game_listing_settings.split('|').index(IAGL.handle.getSetting(id='iagl_setting_listing'))] #Old method pre language update
IAGL.current_game_listing_route = IAGL.game_listing_settings_routes[int(IAGL.handle.getSetting(id='iagl_setting_listing'))]

## Plugin Routes ##
@plugin.route('/')
def iagl_main():
	if not IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_hidden_bool_tou')):
		TOU_Dialog = iagl_TOUdialog('script-IAGL-TOU.xml',IAGL.get_addon_install_path(),'Default','1080i')
		TOU_Dialog.doModal()
		del TOU_Dialog
		if IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_hidden_bool_tou')):
			IAGL.check_for_new_dat_files()
			plugin.redirect('/archives/'+IAGL.archive_listing_settings_route)
		else:
			xbmcplugin.endOfDirectory(plugin.handle)
	else:
		IAGL.check_for_new_dat_files()
		IAGL.initialize_search_query()
		IAGL.initialize_random_query()
		plugin.redirect('/archives/'+IAGL.archive_listing_settings_route)

@plugin.route('/archives/choose_from_list')
def list_archives_browse():
	list_method = 'choose_from_list'
	for list_item in IAGL.get_browse_lists_as_listitems():
		if (list_item.getLabel2() == 'search_menu' and not IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_setting_show_search'))) or (list_item.getLabel2() == 'random_menu' and not IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_setting_show_randomplay'))):
			xbmc.log(msg='IAGL:  Getting game item %(game_list_item)s is hidden per setting' % {'game_list_item': list_item.getLabel2()}, level=xbmc.LOGDEBUG)
		else:
			xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for_path('/archives/'+url_quote(list_item.getLabel2())),list_item, True)
	if IAGL.check_to_show_history(): #Add history to the main choose menu as well
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for_path('/game_list/'+IAGL.current_game_listing_route+'/game_history/1'),IAGL.get_game_history_listitem(), True)
	xbmcplugin.endOfDirectory(plugin.handle)
	if IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_enable_forced_views')) and int(IAGL.handle.getSetting(id='iagl_enable_forced_views_1')) > 0:
		xbmc.log(msg='IAGL:  Frontpage Viewtype forced to %(view_type)s' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_1'))]}, level=xbmc.LOGDEBUG)
		xbmc.executebuiltin('Container.SetViewMode(%(view_type)s)' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_1'))]})

@plugin.route('/archives/all')
def list_archives_all():
	# IAGL.current_game_listing_route = IAGL.game_listing_settings_routes[IAGL.game_listing_settings.split('|').index(IAGL.handle.getSetting(id='iagl_setting_listing'))] #Old method pre language update
	IAGL.current_game_listing_route = IAGL.game_listing_settings_routes[int(IAGL.handle.getSetting(id='iagl_setting_listing'))]
	# for ii,list_item in enumerate(IAGL.get_game_lists_as_listitems()):
	for list_item in IAGL.get_game_lists_as_listitems():
		if IAGL.current_game_listing_route == 'list_all':
			if list_item.getProperty('emu_visibility') != 'hidden':
				xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for_path('/game_list/'+IAGL.current_game_listing_route+'/'+url_quote(list_item.getProperty('dat_filename'))+'/1'),IAGL.add_list_context_menus(list_item,url_quote(list_item.getProperty('dat_filename'))), True)
		else:
			if list_item.getProperty('emu_visibility') != 'hidden':
				xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for_path('/game_list/'+IAGL.current_game_listing_route+'/'+url_quote(list_item.getProperty('dat_filename'))),IAGL.add_list_context_menus(list_item,url_quote(list_item.getProperty('dat_filename'))), True)
		# xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game_list, game_list_id=url_quote(list_item.getProperty('dat_filename')), page_number=1),list_item, True)
	search_and_browse_list_item = IAGL.get_browse_lists_as_listitems()
	if IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_setting_show_search')): #Add search to the bottom of the all page
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for_path('/archives/search_menu'),[x for x in search_and_browse_list_item if x.getLabel2()=='search_menu'][0], True)
	if IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_setting_show_randomplay')): #Add random play to the bottom of the all page
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for_path('/archives/random_menu'),[x for x in search_and_browse_list_item if x.getLabel2()=='random_menu'][0], True)
	if IAGL.check_to_show_history(): #Add history item to the bottom of the all page
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for_path('/game_list/'+IAGL.current_game_listing_route+'/game_history/1'),IAGL.get_game_history_listitem(), True)

	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_DATE)
	xbmcplugin.endOfDirectory(plugin.handle)
	if IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_enable_forced_views')) and int(IAGL.handle.getSetting(id='iagl_enable_forced_views_2')) > 0:
		xbmc.log(msg='IAGL:  Games Library Viewtype forced to %(view_type)s' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_2'))]}, level=xbmc.LOGDEBUG)
		xbmc.executebuiltin('Container.SetViewMode(%(view_type)s)' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_2'))]})


@plugin.route('/archives/categorized')
def list_archives_by_category():
	# for ii,list_item in enumerate(IAGL.get_game_list_categories_as_listitems()):
	for list_item in IAGL.get_game_list_categories_as_listitems():
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game_lists_in_category, category_id=url_quote(list_item.getLabel())),list_item, True)
	
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
	xbmcplugin.endOfDirectory(plugin.handle)
	if IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_enable_forced_views')) and int(IAGL.handle.getSetting(id='iagl_enable_forced_views_3')) > 0:
		xbmc.log(msg='IAGL:  Games Categories Viewtype forced to %(view_type)s' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_3'))]}, level=xbmc.LOGDEBUG)
		xbmc.executebuiltin('Container.SetViewMode(%(view_type)s)' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_3'))]})

@plugin.route('/archives/categorized/<category_id>')
def get_game_lists_in_category(category_id):
	# IAGL.current_game_listing_route = IAGL.game_listing_settings_routes[IAGL.game_listing_settings.split('|').index(IAGL.handle.getSetting(id='iagl_setting_listing'))] #Old method pre language update
	IAGL.current_game_listing_route = IAGL.game_listing_settings_routes[int(IAGL.handle.getSetting(id='iagl_setting_listing'))]
	# for ii,list_item in enumerate(IAGL.get_game_lists_as_listitems(url_unquote(category_id))):
	for list_item in IAGL.get_game_lists_as_listitems(url_unquote(category_id)):
		if IAGL.current_game_listing_route == 'list_all':
			if list_item.getProperty('emu_visibility') != 'hidden':
				xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for_path('/game_list/'+IAGL.current_game_listing_route+'/'+url_quote(list_item.getProperty('dat_filename'))+'/1'),IAGL.add_list_context_menus(list_item,url_quote(list_item.getProperty('dat_filename'))), True)
		else:
			if list_item.getProperty('emu_visibility') != 'hidden':
				xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for_path('/game_list/'+IAGL.current_game_listing_route+'/'+url_quote(list_item.getProperty('dat_filename'))),IAGL.add_list_context_menus(list_item,url_quote(list_item.getProperty('dat_filename'))), True)
		# xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game_list, game_list_id=url_quote(list_item.getProperty('dat_filename')), page_number=1),list_item, True)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_DATE)
	xbmcplugin.endOfDirectory(plugin.handle)
	if IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_enable_forced_views')) and int(IAGL.handle.getSetting(id='iagl_enable_forced_views_2')) > 0:
		xbmc.log(msg='IAGL:  Games Library (by Category) Viewtype forced to %(view_type)s' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_2'))]}, level=xbmc.LOGDEBUG)
		xbmc.executebuiltin('Container.SetViewMode(%(view_type)s)' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_2'))]})

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
	if IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_enable_forced_views')) and int(IAGL.handle.getSetting(id='iagl_enable_forced_views_3')) > 0:
		xbmc.log(msg='IAGL:  Games Categories (by Game List) Viewtype forced to %(view_type)s' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_3'))]}, level=xbmc.LOGDEBUG)
		xbmc.executebuiltin('Container.SetViewMode(%(view_type)s)' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_3'))]})

@plugin.route('/game_list/alphabetical/<game_list_id>')
def get_alphabetical_list(game_list_id):
	list_method = 'alphabetical'
	xbmc.log(msg='IAGL:  Getting game list %(game_list_id)s alphabetically, display method %(list_method)s' % {'game_list_id': game_list_id,'list_method': list_method}, level=xbmc.LOGDEBUG)
	for list_item in IAGL.get_alphabetical_as_listitem(game_list_id):
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_games_with_letter, letter=url_quote(list_item.getLabel2()), game_list_id=game_list_id, page_number=1),list_item, True)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
	xbmcplugin.endOfDirectory(plugin.handle)
	if IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_enable_forced_views')) and int(IAGL.handle.getSetting(id='iagl_enable_forced_views_5')) > 0:
		xbmc.log(msg='IAGL:  Games Alphabetical Viewtype forced to %(view_type)s' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_5'))]}, level=xbmc.LOGDEBUG)
		xbmc.executebuiltin('Container.SetViewMode(%(view_type)s)' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_5'))]})


@plugin.route('/game_list/alphabetical/<letter>/<game_list_id>/')
def get_alphabetical_redirect(letter,game_list_id):
	plugin.redirect('/game_list/alphabetical/'+letter+'/'+game_list_id+'/1')

@plugin.route('/game_list/alphabetical/<letter>/<game_list_id>/<page_number>')
def get_games_with_letter(letter,game_list_id,page_number=1):
	list_method = 'alphabetical'
	xbmc.log(msg='IAGL:  Getting game list %(game_list_id)s alphabetically, display method %(list_method)s, starting with letter %(letter)s, with %(items_pp)s items per page, on page %(page_number)s' % {'game_list_id': game_list_id,'list_method': list_method, 'letter': url_unquote(letter), 'items_pp': str(IAGL.get_items_per_page()), 'page_number': page_number}, level=xbmc.LOGDEBUG)
	current_page, page_info = IAGL.get_games_as_listitems(url_unquote(game_list_id),list_method,letter,page_number)
	for list_item in current_page:
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game, game_list_id=url_quote(game_list_id), game_id=url_quote(list_item.getLabel2())),IAGL.add_game_context_menus(list_item,game_list_id,url_quote(list_item.getLabel2()),page_info['categories']), True) #Method 1, dont pass json as arg
		# xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game, game_list_id=url_quote(game_list_id), game_id=url_quote(list_item.getLabel2()), json=list_item.getProperty('iagl_json')),list_item, True) #Method 2, pass json as arg, works well for Kodi favs, but is 'messy'
	next_page_li = IAGL.get_next_page_listitem(page_info['page'],page_info['page_count'],page_info['next_page'],page_info['item_count'])
	if next_page_li is not None:
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_games_with_letter, letter=letter, game_list_id=game_list_id, page_number=page_info['next_page']),next_page_li, True)
	
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_DATE)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_GENRE)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_STUDIO_IGNORE_THE)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_SIZE)
	xbmcplugin.endOfDirectory(plugin.handle)
	if IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_enable_forced_views')) and int(IAGL.handle.getSetting(id='iagl_enable_forced_views_4')) > 0:
		xbmc.log(msg='IAGL:  Games List (by Alpha) Viewtype forced to %(view_type)s' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_4'))]}, level=xbmc.LOGDEBUG)
		xbmc.executebuiltin('Container.SetViewMode(%(view_type)s)' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_4'))]})


@plugin.route('/game_list/list_by_genre/<game_list_id>')
def get_genre_list(game_list_id):
	list_method = 'list_by_genre'
	xbmc.log(msg='IAGL:  Getting game list %(game_list_id)s by genre, display method %(list_method)s' % {'game_list_id': game_list_id,'list_method': list_method}, level=xbmc.LOGDEBUG)
	for list_item in IAGL.get_game_list_genres_as_listitems(game_list_id):
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_games_with_genre, genre=url_quote(list_item.getLabel2()), game_list_id=game_list_id, page_number=1),list_item, True)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
	xbmcplugin.endOfDirectory(plugin.handle)
	if IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_enable_forced_views')) and int(IAGL.handle.getSetting(id='iagl_enable_forced_views_6')) > 0:
		xbmc.log(msg='IAGL:  Games Genre Viewtype forced to %(view_type)s' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_6'))]}, level=xbmc.LOGDEBUG)
		xbmc.executebuiltin('Container.SetViewMode(%(view_type)s)' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_6'))]})

@plugin.route('/game_list/list_by_genre/<genre>/<game_list_id>/')
def get_genres_redirect(genre,game_list_id):
	plugin.redirect('/game_list/list_by_genre/'+genre+'/'+game_list_id+'/1')

@plugin.route('/game_list/list_by_genre/<genre>/<game_list_id>/<page_number>')
def get_games_with_genre(genre,game_list_id,page_number=1):
	list_method = 'list_by_genre'
	xbmc.log(msg='IAGL:  Getting game list %(game_list_id)s by genre, display method %(list_method)s, with the genre %(genre)s, with %(items_pp)s items per page, on page %(page_number)s' % {'game_list_id': game_list_id,'list_method': list_method, 'genre': url_unquote(genre), 'items_pp': str(IAGL.get_items_per_page()), 'page_number': page_number}, level=xbmc.LOGDEBUG)
	current_page, page_info = IAGL.get_games_as_listitems(url_unquote(game_list_id),list_method,url_unquote(genre),page_number)
	for list_item in current_page:
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game, game_list_id=url_quote(game_list_id), game_id=url_quote(list_item.getLabel2())),IAGL.add_game_context_menus(list_item,game_list_id,url_quote(list_item.getLabel2()),page_info['categories']), True) #Method 1, dont pass json as arg
		# xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game, game_list_id=url_quote(game_list_id), game_id=url_quote(list_item.getLabel2()), json=list_item.getProperty('iagl_json')),list_item, True) #Method 2, pass json as arg, works well for Kodi favs, but is 'messy'
	next_page_li = IAGL.get_next_page_listitem(page_info['page'],page_info['page_count'],page_info['next_page'],page_info['item_count'])
	if next_page_li is not None:
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_games_with_genre, genre=genre, game_list_id=game_list_id, page_number=page_info['next_page']),next_page_li, True)
	
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_DATE)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_GENRE)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_STUDIO_IGNORE_THE)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_SIZE)
	xbmcplugin.endOfDirectory(plugin.handle)
	if IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_enable_forced_views')) and int(IAGL.handle.getSetting(id='iagl_enable_forced_views_4')) > 0:
		xbmc.log(msg='IAGL:  Games List (by Genre) Viewtype forced to %(view_type)s' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_4'))]}, level=xbmc.LOGDEBUG)
		xbmc.executebuiltin('Container.SetViewMode(%(view_type)s)' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_4'))]})

@plugin.route('/game_list/list_by_year/<game_list_id>')
def get_years_list(game_list_id):
	list_method = 'list_by_year'
	xbmc.log(msg='IAGL:  Getting game list %(game_list_id)s by year, display method %(list_method)s' % {'game_list_id': game_list_id,'list_method': list_method}, level=xbmc.LOGDEBUG)
	for list_item in IAGL.get_game_list_years_as_listitems(game_list_id):
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_games_with_year, year=url_quote(list_item.getLabel2()), game_list_id=game_list_id, page_number=1),list_item, True)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
	xbmcplugin.endOfDirectory(plugin.handle)
	if IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_enable_forced_views')) and int(IAGL.handle.getSetting(id='iagl_enable_forced_views_7')) > 0:
		xbmc.log(msg='IAGL:  Games Year Viewtype forced to %(view_type)s' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_7'))]}, level=xbmc.LOGDEBUG)
		xbmc.executebuiltin('Container.SetViewMode(%(view_type)s)' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_7'))]})

@plugin.route('/game_list/list_by_year/<year>/<game_list_id>/')
def get_years_redirect(year,game_list_id):
	plugin.redirect('/game_list/list_by_year/'+year+'/'+game_list_id+'/1')

@plugin.route('/game_list/list_by_year/<year>/<game_list_id>/<page_number>')
def get_games_with_year(year,game_list_id,page_number=1):
	list_method = 'list_by_year'
	xbmc.log(msg='IAGL:  Getting game list %(game_list_id)s by year, display method %(list_method)s, with the year %(year)s, with %(items_pp)s items per page, on page %(page_number)s' % {'game_list_id': game_list_id,'list_method': list_method, 'year': url_unquote(year), 'items_pp': str(IAGL.get_items_per_page()), 'page_number': page_number}, level=xbmc.LOGDEBUG)
	current_page, page_info = IAGL.get_games_as_listitems(url_unquote(game_list_id),list_method,url_unquote(year),page_number)
	for list_item in current_page:
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game, game_list_id=url_quote(game_list_id), game_id=url_quote(list_item.getLabel2())),IAGL.add_game_context_menus(list_item,game_list_id,url_quote(list_item.getLabel2()),page_info['categories']), True) #Method 1, dont pass json as arg
		# xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game, game_list_id=url_quote(game_list_id), game_id=url_quote(list_item.getLabel2()), json=list_item.getProperty('iagl_json')),list_item, True) #Method 2, pass json as arg, works well for Kodi favs, but is 'messy'
	next_page_li = IAGL.get_next_page_listitem(page_info['page'],page_info['page_count'],page_info['next_page'],page_info['item_count'])
	if next_page_li is not None:
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_games_with_year, year=year, game_list_id=game_list_id, page_number=page_info['next_page']),next_page_li, True)
	
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_DATE)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_GENRE)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_STUDIO_IGNORE_THE)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_SIZE)
	xbmcplugin.endOfDirectory(plugin.handle)
	if IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_enable_forced_views')) and int(IAGL.handle.getSetting(id='iagl_enable_forced_views_4')) > 0:
		xbmc.log(msg='IAGL:  Games List (by Year) Viewtype forced to %(view_type)s' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_4'))]}, level=xbmc.LOGDEBUG)
		xbmc.executebuiltin('Container.SetViewMode(%(view_type)s)' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_4'))]})

@plugin.route('/game_list/list_by_players/<game_list_id>')
def get_players_list(game_list_id):
	list_method = 'list_by_players'
	xbmc.log(msg='IAGL:  Getting game list %(game_list_id)s by num players, display method %(list_method)s' % {'game_list_id': game_list_id,'list_method': list_method}, level=xbmc.LOGDEBUG)
	for list_item in IAGL.get_game_list_players_as_listitems(game_list_id):
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_games_with_players, nplayers=url_quote(list_item.getLabel2()), game_list_id=game_list_id, page_number=1),list_item, True)	
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
	xbmcplugin.endOfDirectory(plugin.handle)
	if IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_enable_forced_views')) and int(IAGL.handle.getSetting(id='iagl_enable_forced_views_8')) > 0:
		xbmc.log(msg='IAGL:  Games Players Viewtype forced to %(view_type)s' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_8'))]}, level=xbmc.LOGDEBUG)
		xbmc.executebuiltin('Container.SetViewMode(%(view_type)s)' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_8'))]})

@plugin.route('/game_list/list_by_players/<nplayers>/<game_list_id>/')
def get_players_redirect(nplayers,game_list_id):
	plugin.redirect('/game_list/list_by_players/'+nplayers+'/'+game_list_id+'/1')

@plugin.route('/game_list/list_by_players/<nplayers>/<game_list_id>/<page_number>')
def get_games_with_players(nplayers,game_list_id,page_number=1):
	list_method = 'list_by_players'
	xbmc.log(msg='IAGL:  Getting game list %(game_list_id)s by num players, display method %(list_method)s, with the num players %(nplayers)s, with %(items_pp)s items per page, on page %(page_number)s' % {'game_list_id': game_list_id,'list_method': list_method, 'nplayers': url_unquote(nplayers), 'items_pp': str(IAGL.get_items_per_page()), 'page_number': page_number}, level=xbmc.LOGDEBUG)
	current_page, page_info = IAGL.get_games_as_listitems(url_unquote(game_list_id),list_method,url_unquote(nplayers),page_number)
	for list_item in current_page:
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game, game_list_id=url_quote(game_list_id), game_id=url_quote(list_item.getLabel2())),IAGL.add_game_context_menus(list_item,game_list_id,url_quote(list_item.getLabel2()),page_info['categories']), True) #Method 1, dont pass json as arg
		# xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game, game_list_id=url_quote(game_list_id), game_id=url_quote(list_item.getLabel2()), json=list_item.getProperty('iagl_json')),list_item, True) #Method 2, pass json as arg, works well for Kodi favs, but is 'messy'
	next_page_li = IAGL.get_next_page_listitem(page_info['page'],page_info['page_count'],page_info['next_page'],page_info['item_count'])
	if next_page_li is not None:
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_games_with_players, nplayers=nplayers, game_list_id=game_list_id, page_number=page_info['next_page']),next_page_li, True)
	
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_DATE)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_GENRE)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_STUDIO_IGNORE_THE)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_SIZE)
	xbmcplugin.endOfDirectory(plugin.handle)
	if IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_enable_forced_views')) and int(IAGL.handle.getSetting(id='iagl_enable_forced_views_4')) > 0:
		xbmc.log(msg='IAGL:  Games List (by Players) Viewtype forced to %(view_type)s' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_4'))]}, level=xbmc.LOGDEBUG)
		xbmc.executebuiltin('Container.SetViewMode(%(view_type)s)' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_4'))]})

@plugin.route('/game_list/list_by_studio/<game_list_id>')
def get_studio_list(game_list_id):
	list_method = 'list_by_studio'
	xbmc.log(msg='IAGL:  Getting game list %(game_list_id)s by studio, display method %(list_method)s' % {'game_list_id': game_list_id,'list_method': list_method}, level=xbmc.LOGDEBUG)
	for list_item in IAGL.get_game_list_studios_as_listitems(game_list_id):
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_games_with_studio, studio=url_quote(list_item.getLabel2()), game_list_id=game_list_id, page_number=1),list_item, True)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
	xbmcplugin.endOfDirectory(plugin.handle)
	if IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_enable_forced_views')) and int(IAGL.handle.getSetting(id='iagl_enable_forced_views_9')) > 0:
		xbmc.log(msg='IAGL:  Games Studios Viewtype forced to %(view_type)s' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_9'))]}, level=xbmc.LOGDEBUG)
		xbmc.executebuiltin('Container.SetViewMode(%(view_type)s)' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_9'))]})

@plugin.route('/game_list/list_by_studio/<studio>/<game_list_id>/<page_number>')
def get_games_with_studio(studio,game_list_id,page_number=1):
	list_method = 'list_by_studio'
	xbmc.log(msg='IAGL:  Getting game list %(game_list_id)s by studio, display method %(list_method)s, with the studio %(studio)s, with %(items_pp)s items per page, on page %(page_number)s' % {'game_list_id': game_list_id,'list_method': list_method, 'studio': url_unquote(studio), 'items_pp': str(IAGL.get_items_per_page()), 'page_number': page_number}, level=xbmc.LOGDEBUG)
	current_page, page_info = IAGL.get_games_as_listitems(url_unquote(game_list_id),list_method,url_unquote(studio),page_number)
	for list_item in current_page:
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game, game_list_id=url_quote(game_list_id), game_id=url_quote(list_item.getLabel2())),IAGL.add_game_context_menus(list_item,game_list_id,url_quote(list_item.getLabel2()),page_info['categories']), True) #Method 1, dont pass json as arg
		# xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game, game_list_id=url_quote(game_list_id), game_id=url_quote(list_item.getLabel2()), json=list_item.getProperty('iagl_json')),list_item, True) #Method 2, pass json as arg, works well for Kodi favs, but is 'messy'
	next_page_li = IAGL.get_next_page_listitem(page_info['page'],page_info['page_count'],page_info['next_page'],page_info['item_count'])
	if next_page_li is not None:
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_games_with_studio, studio=studio, game_list_id=game_list_id, page_number=page_info['next_page']),next_page_li, True)
	
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_DATE)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_GENRE)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_STUDIO_IGNORE_THE)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_SIZE)
	xbmcplugin.endOfDirectory(plugin.handle)
	if IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_enable_forced_views')) and int(IAGL.handle.getSetting(id='iagl_enable_forced_views_4')) > 0:
		xbmc.log(msg='IAGL:  Games List (by Studio) Viewtype forced to %(view_type)s' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_4'))]}, level=xbmc.LOGDEBUG)
		xbmc.executebuiltin('Container.SetViewMode(%(view_type)s)' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_4'))]})

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
	
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_DATE)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_GENRE)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_STUDIO_IGNORE_THE)
	xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_SIZE)
	xbmcplugin.endOfDirectory(plugin.handle)
	if IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_enable_forced_views')) and int(IAGL.handle.getSetting(id='iagl_enable_forced_views_4')) > 0:
		xbmc.log(msg='IAGL:  Games List (by All) Viewtype forced to %(view_type)s' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_4'))]}, level=xbmc.LOGDEBUG)
		xbmc.executebuiltin('Container.SetViewMode(%(view_type)s)' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_4'))]})

@plugin.route('/game/<game_list_id>/<game_id>')
def get_game(game_list_id,game_id):
	# xbmcplugin.endOfDirectory(plugin.handle, succeeded=False) #Seems like this is needed, some race condition on modal
	list_method = 'list_single_game'
	xbmc.log(msg='IAGL:  Getting game ID: %(game_id)s in game category %(game_list_id)s' % {'game_list_id': game_list_id, 'game_id': game_id}, level=xbmc.LOGDEBUG)
	
	if len(sys.argv)>2 and sys.argv[2] is not None and 'reload' not in sys.argv[2]:  #This catch is to avoid loading the game when a skin widget reloads
		current_game_json = xbmc.getInfoLabel('ListItem.Property(iagl_json)') #Method 1, get current game json manifest
	else:
		current_game_json = None
	return_to_home_from_infodialog = False

	#No json is available from listitem, so this must be a link from a favorite
	if current_game_json is None or len(current_game_json)<1:
		current_page, page_info = IAGL.get_games_as_listitems(url_unquote(game_list_id),list_method,url_unquote(game_id),1)
		current_game_json = current_page[0].getProperty('iagl_json')
		return_to_home_from_infodialog = True

	#Check to see if its an IAGL favorite route
	current_route = IAGL.get_route_from_json(current_game_json)
	if current_route is not None and 'plugin://plugin.program.iagl' in current_route[0]:
		if 'plugin.program.iagl/run_random' in current_route[0] or 'plugin.program.iagl/run_search' in current_route[0]:
			plugin.run([current_route[0].split('?')[0], '0', current_route[0].split('?')[-1]])
			return
		else:
			route_parse = current_route[0].replace('plugin://plugin.program.iagl/game','').replace('plugin://plugin.program.iagl','').split('/')
			current_page, page_info = IAGL.get_games_as_listitems(url_unquote(route_parse[1]),list_method,url_unquote(route_parse[2]),1)
			current_game_json = current_page[0].getProperty('iagl_json')
			xbmc.log(msg='IAGL:  Rerouting to %(game_id)s in game category %(game_list_id)s' % {'game_list_id': route_parse[1], 'game_id': route_parse[2]}, level=xbmc.LOGDEBUG)
	
	xbmcplugin.endOfDirectory(plugin.handle, succeeded=False) #Seems like this is needed, some race condition on modal.  Needs to be before modal call but after any redirect to a different game list
	#Info Dialog
	current_game = dict()
	current_game['game_id'], current_game['listitem'], current_game['fanarts'], current_game['boxart_and_snapshots'], current_game['banners'], current_game['trailer'] = IAGL.get_gamelistitem_from_json(current_game_json)
	current_game['return_home'] = return_to_home_from_infodialog
	current_game['autoplay_trailer'] = IAGL.handle.getSetting(id='iagl_setting_autoplay_trailer')
	current_game['json'] = current_game_json
	# if 'Info Page' in IAGL.handle.getSetting(id='iagl_setting_default_action'): #Old method pre language update
	if int(IAGL.handle.getSetting(id='iagl_setting_default_action')) == 2:
		IAGL_Dialog = iagl_infodialog('script-IAGL-infodialog.xml',IAGL.get_addon_install_path(),'Default','1080i',current_game=current_game)
		IAGL_Dialog.doModal()
		del IAGL_Dialog
	# elif IAGL.handle.getSetting(id='iagl_setting_default_action') == 'Download Only': #Old method pre language update
	elif int(IAGL.handle.getSetting(id='iagl_setting_default_action')) == 1:
		IAGL_DL = iagl_download(current_game['json']) #Initialize download object
		download_and_process_success = IAGL_DL.download_and_process_game_files() #Download files
		current_dialog = xbmcgui.Dialog()
		if False in download_and_process_success:  #Bad files found
			if True in download_and_process_success:  #Good and Bad files found
				ok_ret = current_dialog.ok(IAGL.loc_str(30203),IAGL.loc_str(30303) % {'game_title': IAGL_DL.current_game_title, 'fail_reason': IAGL_DL.download_fail_reason})
			else:  #Only bad files found
				ok_ret = current_dialog.ok(IAGL.loc_str(30203),IAGL.loc_str(30304) % {'game_title': IAGL_DL.current_game_title, 'fail_reason': IAGL_DL.download_fail_reason})
		else:  #So far so good, now process the files
			ok_ret = current_dialog.notification(IAGL.loc_str(30202),IAGL.loc_str(30302) % {'game_title': IAGL_DL.current_game_title},xbmcgui.NOTIFICATION_INFO,IAGL.notification_time)
		del current_dialog
	# elif IAGL.handle.getSetting(id='iagl_setting_default_action') == 'Download and Launch': #Old method pre language update
	elif int(IAGL.handle.getSetting(id='iagl_setting_default_action')) == 0:
		IAGL_DL = iagl_download(current_game['json']) #Initialize download object
		download_and_process_success = IAGL_DL.download_and_process_game_files() #Download files
		if False not in download_and_process_success:
			IAGL_LAUNCH = iagl_launch(current_game['json'],IAGL_DL.current_processed_files,current_game['game_id']) #Initialize launch object
			launch_success = IAGL_LAUNCH.launch() #Launch Game
			if launch_success:
				xbmc.log(msg='IAGL:  Game Launched: %(game_title)s' % {'game_title': IAGL_DL.current_game_title}, level=xbmc.LOGDEBUG)
		else:
			current_dialog = xbmcgui.Dialog()
			ok_ret = current_dialog.ok(IAGL.loc_str(30203),IAGL.loc_str(30305) % {'game_title': IAGL_DL.current_game_title, 'fail_reason': IAGL_DL.download_fail_reason})
			del current_dialog
	else:
		xbmc.log(msg='IAGL:  Unkown default action in settings',level=xbmc.LOGERROR)
	# xbmcplugin.endOfDirectory(plugin.handle, succeeded=False)

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
					ok_ret = current_dialog.notification(IAGL.loc_str(30202),IAGL.loc_str(30306) % {'game_list_id': game_list_id},xbmcgui.NOTIFICATION_INFO,IAGL.notification_time)
					IAGL.delete_dat_file_cache()
					del current_dialog
			elif current_key == 'view_list_settings':
				xbmc.log(msg='IAGL:  Show settings for game list %(game_list_id)s' % {'game_list_id': game_list_id}, level=xbmc.LOGDEBUG)
				current_settings_text = IAGL.get_list_settings_text(current_game_list)
				plugin.redirect('/text_viewer')
			else:
				xbmc.log(msg='IAGL:  Update to game list value cancelled',level=xbmc.LOGDEBUG)

@plugin.route('/games_context_menu/<game_list_id>/<game_id>/<setting_id>')
def update_game_item(game_list_id,game_id,setting_id):
	if url_unquote(game_list_id) == 'query':  #Add ability to add search or random play query to IAGL favorites
		current_game_json = xbmc.getInfoLabel('ListItem.Property(iagl_json)')
	else:
		xbmc.log(msg='IAGL:  Game Context menu called for game %(game_id)s in list %(game_list_id)s setting %(setting_id)s' % {'game_id':game_id, 'game_list_id': game_list_id, 'setting_id': setting_id}, level=xbmc.LOGDEBUG)
		current_page, page_info = IAGL.get_games_as_listitems(url_unquote(game_list_id),'list_single_game',url_unquote(game_id),1)
		current_game_json = current_page[0].getProperty('iagl_json')
	if setting_id == 'add':
		IAGL.add_game_to_IAGL_favorites(game_list_id,game_id,current_game_json)
	elif setting_id == 'remove':
		IAGL.remove_game_from_IAGL_favorites(game_list_id,game_id,current_game_json)
		xbmc.executebuiltin('Container.Refresh')
	elif setting_id == 'view_info_page':
		#Info Dialog
		current_game = dict()
		current_game['game_id'], current_game['listitem'], current_game['fanarts'], current_game['boxart_and_snapshots'], current_game['banners'], current_game['trailer'] = IAGL.get_gamelistitem_from_json(current_game_json)
		current_game['return_home'] = False
		current_game['autoplay_trailer'] = IAGL.handle.getSetting(id='iagl_setting_autoplay_trailer')
		current_game['json'] = current_game_json
		IAGL_Dialog = iagl_infodialog('script-IAGL-infodialog.xml',IAGL.get_addon_install_path(),'Default','1080i',current_game=current_game)
		IAGL_Dialog.doModal()
		del IAGL_Dialog
	else:
		xbmc.log(msg='IAGL:  Unknown game context menu setting  %(setting_id)s' % {'setting_id': setting_id}, level=xbmc.LOGERROR)

@plugin.route('/archives/search_menu')
def search_games_menu():
	xbmc.log(msg='IAGL:  Game Search menu called', level=xbmc.LOGDEBUG)
	try:
		current_query = json.loads(xbmcgui.Window(IAGL.windowid).getProperty('iagl_search_query'))
	except:
		xbmc.log(msg='IAGL:  Search query could not be loaded, resetting the query', level=xbmc.LOGDEBUG)
		IAGL.initialize_search_query()
		current_query = json.loads(xbmcgui.Window(IAGL.windowid).getProperty('iagl_search_query'))
	for list_item in IAGL.get_search_menu_items_as_listitems(current_query):
		if list_item.getLabel2() == 'execute_link':
			xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(generate_search_listitem),list_item, True)
		elif list_item.getLabel2() == 'execute':
			xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(update_search_query, search_id=url_quote(list_item.getLabel2())),list_item, True)
		else:
			xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(update_search_query, search_id=url_quote(list_item.getLabel2())),list_item, False)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/search_query/<search_id>')
def update_search_query(search_id):
	xbmc.log(msg='IAGL:  Query update for %(search_id)s called' % {'search_id':search_id}, level=xbmc.LOGDEBUG)
	try:
		current_query = json.loads(xbmcgui.Window(IAGL.windowid).getProperty('iagl_search_query'))
	except:
		xbmc.log(msg='IAGL:  Search query could not be loaded, resetting the query', level=xbmc.LOGDEBUG)
		IAGL.initialize_search_query()
		current_query = json.loads(xbmcgui.Window(IAGL.windowid).getProperty('iagl_search_query'))

	input_query_types = ['title','tag']
	list_query_types = ['lists']
	filter_query_types = ['year','nplayers','genre','studio']

	if search_id in input_query_types:
		current_dialog = xbmcgui.Dialog()
		new_value = current_dialog.input(xbmc.getInfoLabel('ListItem.Label'))
		if len(new_value)>0:
			current_query[search_id] = new_value
		else:
			current_query[search_id] = None
		del current_dialog
		xbmcgui.Window(IAGL.windowid).setProperty('iagl_search_query',json.dumps(current_query))
		xbmc.executebuiltin('Container.Refresh')
	if search_id in list_query_types:
		current_game_lists = IAGL.get_game_lists()
		try:
			current_select = ['Any']+[x for x in current_game_lists.get('emu_name')]
			current_filenames = [None]+[x for x in current_game_lists.get('dat_filename')]
		except Exception as exc:
			current_select = None
			current_filenames = None
			xbmc.log(msg='IAGL:  The game lists could not be found.  Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
		if current_select is not None:
			if current_query['lists'] is not None:
				currently_selected_lists = [current_filenames.index(x) for x in current_query['lists']]
			else:
				currently_selected_lists = None
			current_dialog = xbmcgui.Dialog()
			if currently_selected_lists is not None:
				ret1 = current_dialog.multiselect(xbmc.getInfoLabel('ListItem.Label'), current_select,0,currently_selected_lists)
			else:
				ret1 = current_dialog.multiselect(xbmc.getInfoLabel('ListItem.Label'), current_select)
			del current_dialog
			if ret1 is not None:
				if 0 in ret1:
					current_query['lists'] = None
				else:
					current_query['lists'] = [x for x in current_filenames if current_filenames.index(x) in ret1]
		else:
			current_query['lists'] = None
		xbmcgui.Window(IAGL.windowid).setProperty('iagl_search_query',json.dumps(current_query))
		xbmc.executebuiltin('Container.Refresh')

	if search_id == 'genre':
		current_genre_lists = None
		if current_query['lists'] is None and not IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_silence_query_warning')):
			current_dialog = xbmcgui.Dialog()
			ret1 = current_dialog.select(IAGL.loc_str(30307), [IAGL.loc_str(30200),IAGL.loc_str(30201)])
			del current_dialog
			if ret1 == 0:
				current_genre_lists = IAGL.get_genres_from_game_lists(current_query['lists'])
			else:
				current_genre_lists = None
				xbmc.log(msg='IAGL:  User cancelled large genre query', level=xbmc.LOGDEBUG)
		else:
			if not IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_silence_query_warning')) and len(current_query['lists'])>10:
				current_dialog = xbmcgui.Dialog()
				ret1 = current_dialog.select(IAGL.loc_str(30308), [IAGL.loc_str(30200),IAGL.loc_str(30201)])
				del current_dialog
				if ret1 == 0:
					current_genre_lists = IAGL.get_genres_from_game_lists(current_query['lists'])
				else:
					current_genre_lists = None
					xbmc.log(msg='IAGL:  User cancelled large genre query', level=xbmc.LOGDEBUG)
			else:
				current_genre_lists = IAGL.get_genres_from_game_lists(current_query['lists'])
		if current_genre_lists is not None:
			current_genre_lists = ['Any']+current_genre_lists
			if current_query['genre'] is not None:
				currently_selected_genres = [current_genre_lists.index(x) for x in current_query['genre']]
			else:
				currently_selected_genres = None
			current_dialog = xbmcgui.Dialog()
			if currently_selected_genres is not None:
				ret1 = current_dialog.multiselect(xbmc.getInfoLabel('ListItem.Label'), current_genre_lists,0,currently_selected_genres)
			else:
				ret1 = current_dialog.multiselect(xbmc.getInfoLabel('ListItem.Label'), current_genre_lists)
			del current_dialog
			if ret1 is not None:
				if 0 in ret1:
					current_query['genre'] = None
				else:
					current_query['genre'] = [x for x in current_genre_lists if current_genre_lists.index(x) in ret1]
		xbmcgui.Window(IAGL.windowid).setProperty('iagl_search_query',json.dumps(current_query))
		xbmc.executebuiltin('Container.Refresh')

	if search_id == 'nplayers':
		current_players_lists = None
		if current_query['lists'] is None and not IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_silence_query_warning')):
			current_dialog = xbmcgui.Dialog()
			ret1 = current_dialog.select(IAGL.loc_str(30309), [IAGL.loc_str(30200),IAGL.loc_str(30201)])
			del current_dialog
			if ret1 == 0:
				current_players_lists = IAGL.get_players_from_game_lists(current_query['lists'])
			else:
				current_players_lists = None
				xbmc.log(msg='IAGL:  User cancelled large nplayers query', level=xbmc.LOGDEBUG)
		else:
			if not IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_silence_query_warning')) and len(current_query['lists'])>10:
				current_dialog = xbmcgui.Dialog()
				ret1 = current_dialog.select(IAGL.loc_str(30310), [IAGL.loc_str(30200),IAGL.loc_str(30201)])
				del current_dialog
				if ret1 == 0:
					current_players_lists = IAGL.get_players_from_game_lists(current_query['lists'])
				else:
					current_players_lists = None
					xbmc.log(msg='IAGL:  User cancelled large nplayers query', level=xbmc.LOGDEBUG)
			else:
				current_players_lists = IAGL.get_players_from_game_lists(current_query['lists'])
		if current_players_lists is not None:
			current_players_lists = ['Any']+current_players_lists
			if current_query['nplayers'] is not None:
				currently_selected_players = [current_players_lists.index(x) for x in current_query['nplayers']]
			else:
				currently_selected_players = None
			current_dialog = xbmcgui.Dialog()
			if currently_selected_players is not None:
				ret1 = current_dialog.multiselect(xbmc.getInfoLabel('ListItem.Label'), current_players_lists,0,currently_selected_players)
			else:
				ret1 = current_dialog.multiselect(xbmc.getInfoLabel('ListItem.Label'), current_players_lists)
			del current_dialog
			if ret1 is not None:
				if 0 in ret1:
					current_query['nplayers'] = None
				else:
					current_query['nplayers'] = [x for x in current_players_lists if current_players_lists.index(x) in ret1]
		xbmcgui.Window(IAGL.windowid).setProperty('iagl_search_query',json.dumps(current_query))
		xbmc.executebuiltin('Container.Refresh')

	if search_id == 'year':
		current_year_lists = None
		if current_query['lists'] is None and not IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_silence_query_warning')):
			current_dialog = xbmcgui.Dialog()
			ret1 = current_dialog.select(IAGL.loc_str(30311), [IAGL.loc_str(30200),IAGL.loc_str(30201)])
			del current_dialog
			if ret1 == 0:
				current_year_lists = IAGL.get_years_from_game_lists(current_query['lists'])
			else:
				current_year_lists = None
				xbmc.log(msg='IAGL:  User cancelled large year query', level=xbmc.LOGDEBUG)
		else:
			if not IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_silence_query_warning')) and len(current_query['lists'])>10:
				current_dialog = xbmcgui.Dialog()
				ret1 = current_dialog.select(IAGL.loc_str(30312), [IAGL.loc_str(30200),IAGL.loc_str(30201)])
				del current_dialog
				if ret1 == 0:
					current_year_lists = IAGL.get_years_from_game_lists(current_query['lists'])
				else:
					current_year_lists = None
					xbmc.log(msg='IAGL:  User cancelled large year query', level=xbmc.LOGDEBUG)
			else:
				current_year_lists = IAGL.get_years_from_game_lists(current_query['lists'])
		if current_year_lists is not None:
			current_year_lists = ['Any']+current_year_lists
			if current_query['year'] is not None:
				currently_selected_years = [current_year_lists.index(x) for x in current_query['year']]
			else:
				currently_selected_years = None
			current_dialog = xbmcgui.Dialog()
			if currently_selected_years is not None:
				ret1 = current_dialog.multiselect(xbmc.getInfoLabel('ListItem.Label'), current_year_lists,0,currently_selected_years)
			else:
				ret1 = current_dialog.multiselect(xbmc.getInfoLabel('ListItem.Label'), current_year_lists)
			del current_dialog
			if ret1 is not None:
				if 0 in ret1:
					current_query['year'] = None
				else:
					current_query['year'] = [x for x in current_year_lists if current_year_lists.index(x) in ret1]
		xbmcgui.Window(IAGL.windowid).setProperty('iagl_search_query',json.dumps(current_query))
		xbmc.executebuiltin('Container.Refresh')
		
	if search_id == 'studio':
		current_studio_lists = None
		if current_query['lists'] is None and not IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_silence_query_warning')):
			current_dialog = xbmcgui.Dialog()
			ret1 = current_dialog.select(IAGL.loc_str(30313), [IAGL.loc_str(30200),IAGL.loc_str(30201)])
			del current_dialog
			if ret1 == 0:
				current_studio_lists = IAGL.get_studios_from_game_lists(current_query['lists'])
			else:
				current_studio_lists = None
				xbmc.log(msg='IAGL:  User cancelled large studio query', level=xbmc.LOGDEBUG)
		else:
			if not IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_silence_query_warning')) and len(current_query['lists'])>10:
				current_dialog = xbmcgui.Dialog()
				ret1 = current_dialog.select(IAGL.loc_str(30314), [IAGL.loc_str(30200),IAGL.loc_str(30201)])
				del current_dialog
				if ret1 == 0:
					current_studio_lists = IAGL.get_studios_from_game_lists(current_query['lists'])
				else:
					current_studio_lists = None
					xbmc.log(msg='IAGL:  User cancelled large studio query', level=xbmc.LOGDEBUG)
			else:
				current_studio_lists = IAGL.get_studios_from_game_lists(current_query['lists'])
		if current_studio_lists is not None:
			current_studio_lists = ['Any']+current_studio_lists
			if current_query['studio'] is not None:
				currently_selected_studios = [current_studio_lists.index(x) for x in current_query['studio']]
			else:
				currently_selected_studios = None
			current_dialog = xbmcgui.Dialog()
			if currently_selected_studios is not None:
				ret1 = current_dialog.multiselect(xbmc.getInfoLabel('ListItem.Label'), current_studio_lists,0,currently_selected_studios)
			else:
				ret1 = current_dialog.multiselect(xbmc.getInfoLabel('ListItem.Label'), current_studio_lists)
			del current_dialog
			if ret1 is not None:
				if 0 in ret1:
					current_query['studio'] = None
				else:
					current_query['studio'] = [x for x in current_studio_lists if current_studio_lists.index(x) in ret1]
		xbmcgui.Window(IAGL.windowid).setProperty('iagl_search_query',json.dumps(current_query))
		xbmc.executebuiltin('Container.Refresh')

	if search_id == 'execute':
		if current_query['title'] is None:
			current_dialog = xbmcgui.Dialog()
			ok_ret = current_dialog.notification(IAGL.loc_str(30203),IAGL.loc_str(30319),xbmcgui.NOTIFICATION_ERROR,IAGL.error_notification_time)
			del current_dialog
		else:
			if current_query['lists'] is None and not IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_silence_query_warning')):
				current_dialog = xbmcgui.Dialog()
				ret1 = current_dialog.select(IAGL.loc_str(30315), [IAGL.loc_str(30200),IAGL.loc_str(30201)])
				del current_dialog
				if ret1 == 0:
					plugin.run(['plugin://plugin.program.iagl/run_search/1/', '0', IAGL.get_query_as_url(current_query)])
				else:
					xbmc.log(msg='IAGL:  User cancelled large query', level=xbmc.LOGDEBUG)
			else:
				if not IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_silence_query_warning')) and len(current_query['lists'])>10:
					current_dialog = xbmcgui.Dialog()
					ret1 = current_dialog.select(IAGL.loc_str(30316), [IAGL.loc_str(30200),IAGL.loc_str(30201)])
					del current_dialog
					if ret1 == 0:
						plugin.run(['plugin://plugin.program.iagl/run_search/1/', '0', IAGL.get_query_as_url(current_query)])
					else:
						xbmc.log(msg='IAGL:  User cancelled large query', level=xbmc.LOGDEBUG)
				else:
					plugin.run(['plugin://plugin.program.iagl/run_search/1/', '0', IAGL.get_query_as_url(current_query)])

@plugin.route('/generate_search_item')
def generate_search_listitem():
	xbmc.log(msg='IAGL:  Generate search listitem called', level=xbmc.LOGDEBUG)
	try:
		current_query = json.loads(xbmcgui.Window(IAGL.windowid).getProperty('iagl_search_query'))
	except:
		xbmc.log(msg='IAGL:  Search query could not be loaded, resetting the query', level=xbmc.LOGDEBUG)
		IAGL.initialize_search_query()
		current_query = json.loads(xbmcgui.Window(IAGL.windowid).getProperty('iagl_search_query'))
	create_listitem = False
	if current_query['title'] is None:
		current_dialog = xbmcgui.Dialog()
		ok_ret = current_dialog.notification(IAGL.loc_str(30203),IAGL.loc_str(30319),xbmcgui.NOTIFICATION_ERROR,IAGL.error_notification_time)
		del current_dialog
	else:
		if current_query['lists'] is None:
			current_dialog = xbmcgui.Dialog()
			ret1 = current_dialog.select(IAGL.loc_str(30317), [IAGL.loc_str(30200),IAGL.loc_str(30201)])
			del current_dialog
			if ret1 == 0:
				create_listitem = True
			else:
				xbmc.log(msg='IAGL:  User cancelled large query', level=xbmc.LOGDEBUG)
		else:
			if len(current_query['lists'])>10:
				current_dialog = xbmcgui.Dialog()
				ret1 = current_dialog.select(IAGL.loc_str(30318), [IAGL.loc_str(30200),IAGL.loc_str(30201)])
				del current_dialog
				if ret1 == 0:
					create_listitem = True
				else:
					xbmc.log(msg='IAGL:  User cancelled large query', level=xbmc.LOGDEBUG)
			else:
				create_listitem = True
	default_label = 'IAGL Search %(query_value)s' % {'query_value':current_query['title']}
	if create_listitem:
		current_dialog = xbmcgui.Dialog()
		new_value = current_dialog.input(IAGL.loc_str(30320),default_label)
		del current_dialog
		if len(new_value)<1:
			new_value = default_label
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for_path('/run_search/1/?'+IAGL.get_query_as_url(current_query)),IAGL.get_search_query_listitem(new_value,current_query), True)
		xbmcplugin.endOfDirectory(plugin.handle)
	else:
		pass

@plugin.route('/run_search/<page_number>/')
def run_search_query(page_number=1):
	current_query = IAGL.get_query_from_args(plugin.args)
	if current_query['title'] is not None:
		xbmc.log(msg='IAGL:  Executing query', level=xbmc.LOGDEBUG)
		xbmc.log(msg='IAGL:  Query Title: %(query_value)s' % {'query_value':current_query['title']}, level=xbmc.LOGDEBUG)
		xbmc.log(msg='IAGL:  Query Tag: %(query_value)s' % {'query_value':current_query['tag']}, level=xbmc.LOGDEBUG)
		xbmc.log(msg='IAGL:  Query Lists: %(query_value)s' % {'query_value':current_query['lists']}, level=xbmc.LOGDEBUG)
		xbmc.log(msg='IAGL:  Query Years: %(query_value)s' % {'query_value':current_query['year']}, level=xbmc.LOGDEBUG)
		xbmc.log(msg='IAGL:  Query Genres: %(query_value)s' % {'query_value':current_query['genre']}, level=xbmc.LOGDEBUG)
		xbmc.log(msg='IAGL:  Query Players: %(query_value)s' % {'query_value':current_query['nplayers']}, level=xbmc.LOGDEBUG)
		xbmc.log(msg='IAGL:  Query Studios: %(query_value)s' % {'query_value':current_query['studio']}, level=xbmc.LOGDEBUG)
		list_method = 'list_all'
		xbmc.log(msg='IAGL:  Getting game list for search, display method %(list_method)s with %(items_pp)s items per page, on page %(page_number)s' % {'list_method': list_method, 'items_pp': str(IAGL.get_items_per_page()), 'page_number': page_number}, level=xbmc.LOGDEBUG)
		current_page, page_info = IAGL.get_games_from_search_query_as_listitems(current_query,list_method,None,page_number)
		for list_item in current_page:
			current_game_list_id = json.loads(list_item.getProperty('iagl_json')).get('emu').get('game_list_id')
			xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game, game_list_id=url_quote(current_game_list_id), game_id=url_quote(list_item.getLabel2())),IAGL.add_game_context_menus(list_item,current_game_list_id,url_quote(list_item.getLabel2()),page_info['categories']), True) #Method 1, dont pass json as arg
		next_page_li = IAGL.get_next_page_listitem(page_info['page'],page_info['page_count'],page_info['next_page'],page_info['item_count'])
		if next_page_li is not None:
			xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game_list, list_method=list_method, game_list_id=game_list_id, page_number=page_info['next_page']),next_page_li, True)
		
		xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
		xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_DATE)
		xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_GENRE)
		xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_STUDIO_IGNORE_THE)
		xbmcplugin.addSortMethod(plugin.handle,xbmcplugin.SORT_METHOD_SIZE)
		xbmcplugin.endOfDirectory(plugin.handle)
		if IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_enable_forced_views')) and int(IAGL.handle.getSetting(id='iagl_enable_forced_views_10')) > 0:
			xbmc.log(msg='IAGL:  Games Search Results Viewtype forced to %(view_type)s' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_10'))]}, level=xbmc.LOGDEBUG)
			xbmc.executebuiltin('Container.SetViewMode(%(view_type)s)' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_10'))]})
	else:
		pass

@plugin.route('/archives/random_menu')
def random_games_menu():
	xbmc.log(msg='IAGL:  Random game menu called', level=xbmc.LOGDEBUG)
	try:
		current_query = json.loads(xbmcgui.Window(IAGL.windowid).getProperty('iagl_random_query'))
	except:
		xbmc.log(msg='IAGL:  Random query could not be loaded, resetting the query', level=xbmc.LOGDEBUG)
		IAGL.initialize_random_query()
		current_query = json.loads(xbmcgui.Window(IAGL.windowid).getProperty('iagl_random_query'))
	for list_item in IAGL.get_random_menu_items_as_listitems(current_query):
		if list_item.getLabel2() == 'execute_link':
			xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(generate_random_listitem),list_item, True)
		elif list_item.getLabel2() == 'execute':
			xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(update_random_query, random_id=url_quote(list_item.getLabel2())),list_item, True)
		else:
			xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(update_random_query, random_id=url_quote(list_item.getLabel2())),list_item, False)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/random_query/<random_id>')
def update_random_query(random_id):
	xbmc.log(msg='IAGL:  Query update for %(random_id)s called' % {'random_id':random_id}, level=xbmc.LOGDEBUG)
	try:
		current_query = json.loads(xbmcgui.Window(IAGL.windowid).getProperty('iagl_random_query'))
	except:
		xbmc.log(msg='IAGL:  Random query could not be loaded, resetting the query', level=xbmc.LOGDEBUG)
		IAGL.initialize_random_query()
		current_query = json.loads(xbmcgui.Window(IAGL.windowid).getProperty('iagl_random_query'))

	choose_query_types = ['title']
	input_query_types = ['tag']
	list_query_types = ['lists']
	filter_query_types = ['year','nplayers','genre','studio']

	if random_id in choose_query_types:
		current_dialog = xbmcgui.Dialog()
		ret1 = current_dialog.select(IAGL.loc_str(30321),['1','2','5','10','25','100'],0,0)
		del current_dialog
		if ret1>0:
			new_value = ['1','2','5','10','25','100'][ret1]
		else:
			new_value = '1'
		if len(new_value)>0:
			current_query[random_id] = new_value
		else:
			current_query[random_id] = '1'
		xbmcgui.Window(IAGL.windowid).setProperty('iagl_random_query',json.dumps(current_query))
		xbmc.executebuiltin('Container.Refresh')		
	if random_id in input_query_types:
		current_dialog = xbmcgui.Dialog()
		new_value = current_dialog.input(xbmc.getInfoLabel('ListItem.Label'))
		if len(new_value)>0:
			current_query[random_id] = new_value
		else:
			current_query[random_id] = None
		del current_dialog
		xbmcgui.Window(IAGL.windowid).setProperty('iagl_random_query',json.dumps(current_query))
		xbmc.executebuiltin('Container.Refresh')
	if random_id in list_query_types:
		current_game_lists = IAGL.get_game_lists()
		try:
			current_select = ['Any']+[x for x in current_game_lists.get('emu_name')]
			current_filenames = [None]+[x for x in current_game_lists.get('dat_filename')]
		except Exception as exc:
			current_select = None
			current_filenames = None
			xbmc.log(msg='IAGL:  The game lists could not be found.  Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
		if current_select is not None:
			if current_query['lists'] is not None:
				currently_selected_lists = [current_filenames.index(x) for x in current_query['lists']]
			else:
				currently_selected_lists = None
			current_dialog = xbmcgui.Dialog()
			if currently_selected_lists is not None:
				ret1 = current_dialog.multiselect(xbmc.getInfoLabel('ListItem.Label'), current_select,0,currently_selected_lists)
			else:
				ret1 = current_dialog.multiselect(xbmc.getInfoLabel('ListItem.Label'), current_select)
			del current_dialog
			if ret1 is not None:
				if 0 in ret1:
					current_query['lists'] = None
				else:
					current_query['lists'] = [x for x in current_filenames if current_filenames.index(x) in ret1]
		else:
			current_query['lists'] = None
		xbmcgui.Window(IAGL.windowid).setProperty('iagl_random_query',json.dumps(current_query))
		xbmc.executebuiltin('Container.Refresh')

	if random_id == 'genre':
		current_genre_lists = None
		if current_query['lists'] is None and not IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_silence_query_warning')):
			current_dialog = xbmcgui.Dialog()
			ret1 = current_dialog.select(IAGL.loc_str(30307), [IAGL.loc_str(30200),IAGL.loc_str(30201)])
			del current_dialog
			if ret1 == 0:
				current_genre_lists = IAGL.get_genres_from_game_lists(current_query['lists'])
			else:
				current_genre_lists = None
				xbmc.log(msg='IAGL:  User cancelled large genre query', level=xbmc.LOGDEBUG)
		else:
			if not IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_silence_query_warning')) and len(current_query['lists'])>10:
				current_dialog = xbmcgui.Dialog()
				ret1 = current_dialog.select(IAGL.loc_str(30308), [IAGL.loc_str(30200),IAGL.loc_str(30201)])
				del current_dialog
				if ret1 == 0:
					current_genre_lists = IAGL.get_genres_from_game_lists(current_query['lists'])
				else:
					current_genre_lists = None
					xbmc.log(msg='IAGL:  User cancelled large genre query', level=xbmc.LOGDEBUG)
			else:
				current_genre_lists = IAGL.get_genres_from_game_lists(current_query['lists'])
		if current_genre_lists is not None:
			current_genre_lists = ['Any']+current_genre_lists
			if current_query['genre'] is not None:
				currently_selected_genres = [current_genre_lists.index(x) for x in current_query['genre']]
			else:
				currently_selected_genres = None
			current_dialog = xbmcgui.Dialog()
			if currently_selected_genres is not None:
				ret1 = current_dialog.multiselect(xbmc.getInfoLabel('ListItem.Label'), current_genre_lists,0,currently_selected_genres)
			else:
				ret1 = current_dialog.multiselect(xbmc.getInfoLabel('ListItem.Label'), current_genre_lists)
			del current_dialog
			if ret1 is not None:
				if 0 in ret1:
					current_query['genre'] = None
				else:
					current_query['genre'] = [x for x in current_genre_lists if current_genre_lists.index(x) in ret1]
		xbmcgui.Window(IAGL.windowid).setProperty('iagl_random_query',json.dumps(current_query))
		xbmc.executebuiltin('Container.Refresh')

	if random_id == 'nplayers':
		current_players_lists = None
		if current_query['lists'] is None and not IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_silence_query_warning')):
			current_dialog = xbmcgui.Dialog()
			ret1 = current_dialog.select(IAGL.loc_str(30309), [IAGL.loc_str(30200),IAGL.loc_str(30201)])
			del current_dialog
			if ret1 == 0:
				current_players_lists = IAGL.get_players_from_game_lists(current_query['lists'])
			else:
				current_players_lists = None
				xbmc.log(msg='IAGL:  User cancelled large nplayers query', level=xbmc.LOGDEBUG)
		else:
			if not IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_silence_query_warning')) and len(current_query['lists'])>10:
				current_dialog = xbmcgui.Dialog()
				ret1 = current_dialog.select(IAGL.loc_str(30310), [IAGL.loc_str(30200),IAGL.loc_str(30201)])
				del current_dialog
				if ret1 == 0:
					current_players_lists = IAGL.get_players_from_game_lists(current_query['lists'])
				else:
					current_players_lists = None
					xbmc.log(msg='IAGL:  User cancelled large nplayers query', level=xbmc.LOGDEBUG)
			else:
				current_players_lists = IAGL.get_players_from_game_lists(current_query['lists'])
		if current_players_lists is not None:
			current_players_lists = ['Any']+current_players_lists
			if current_query['nplayers'] is not None:
				currently_selected_players = [current_players_lists.index(x) for x in current_query['nplayers']]
			else:
				currently_selected_players = None
			current_dialog = xbmcgui.Dialog()
			if currently_selected_players is not None:
				ret1 = current_dialog.multiselect(xbmc.getInfoLabel('ListItem.Label'), current_players_lists,0,currently_selected_players)
			else:
				ret1 = current_dialog.multiselect(xbmc.getInfoLabel('ListItem.Label'), current_players_lists)
			del current_dialog
			if ret1 is not None:
				if 0 in ret1:
					current_query['nplayers'] = None
				else:
					current_query['nplayers'] = [x for x in current_players_lists if current_players_lists.index(x) in ret1]
		xbmcgui.Window(IAGL.windowid).setProperty('iagl_random_query',json.dumps(current_query))
		xbmc.executebuiltin('Container.Refresh')

	if random_id == 'year':
		current_year_lists = None
		if current_query['lists'] is None and not IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_silence_query_warning')):
			current_dialog = xbmcgui.Dialog()
			ret1 = current_dialog.select(IAGL.loc_str(30311), [IAGL.loc_str(30200),IAGL.loc_str(30201)])
			del current_dialog
			if ret1 == 0:
				current_year_lists = IAGL.get_years_from_game_lists(current_query['lists'])
			else:
				current_year_lists = None
				xbmc.log(msg='IAGL:  User cancelled large year query', level=xbmc.LOGDEBUG)
		else:
			if not IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_silence_query_warning')) and len(current_query['lists'])>10:
				current_dialog = xbmcgui.Dialog()
				ret1 = current_dialog.select(IAGL.loc_str(30312), [IAGL.loc_str(30200),IAGL.loc_str(30201)])
				del current_dialog
				if ret1 == 0:
					current_year_lists = IAGL.get_years_from_game_lists(current_query['lists'])
				else:
					current_year_lists = None
					xbmc.log(msg='IAGL:  User cancelled large year query', level=xbmc.LOGDEBUG)
			else:
				current_year_lists = IAGL.get_years_from_game_lists(current_query['lists'])
		if current_year_lists is not None:
			current_year_lists = ['Any']+current_year_lists
			if current_query['year'] is not None:
				currently_selected_years = [current_year_lists.index(x) for x in current_query['year']]
			else:
				currently_selected_years = None
			current_dialog = xbmcgui.Dialog()
			if currently_selected_years is not None:
				ret1 = current_dialog.multiselect(xbmc.getInfoLabel('ListItem.Label'), current_year_lists,0,currently_selected_years)
			else:
				ret1 = current_dialog.multiselect(xbmc.getInfoLabel('ListItem.Label'), current_year_lists)
			del current_dialog
			if ret1 is not None:
				if 0 in ret1:
					current_query['year'] = None
				else:
					current_query['year'] = [x for x in current_year_lists if current_year_lists.index(x) in ret1]
		xbmcgui.Window(IAGL.windowid).setProperty('iagl_random_query',json.dumps(current_query))
		xbmc.executebuiltin('Container.Refresh')
		
	if random_id == 'studio':
		current_studio_lists = None
		if current_query['lists'] is None and not IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_silence_query_warning')):
			current_dialog = xbmcgui.Dialog()
			ret1 = current_dialog.select(IAGL.loc_str(30313), [IAGL.loc_str(30200),IAGL.loc_str(30201)])
			del current_dialog
			if ret1 == 0:
				current_studio_lists = IAGL.get_studios_from_game_lists(current_query['lists'])
			else:
				current_studio_lists = None
				xbmc.log(msg='IAGL:  User cancelled large studio query', level=xbmc.LOGDEBUG)
		else:
			if not IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_silence_query_warning')) and len(current_query['lists'])>10:
				current_dialog = xbmcgui.Dialog()
				ret1 = current_dialog.select(IAGL.loc_str(30314), [IAGL.loc_str(30200),IAGL.loc_str(30201)])
				del current_dialog
				if ret1 == 0:
					current_studio_lists = IAGL.get_studios_from_game_lists(current_query['lists'])
				else:
					current_studio_lists = None
					xbmc.log(msg='IAGL:  User cancelled large studio query', level=xbmc.LOGDEBUG)
			else:
				current_studio_lists = IAGL.get_studios_from_game_lists(current_query['lists'])
		if current_studio_lists is not None:
			current_studio_lists = ['Any']+current_studio_lists
			if current_query['studio'] is not None:
				currently_selected_studios = [current_studio_lists.index(x) for x in current_query['studio']]
			else:
				currently_selected_studios = None
			current_dialog = xbmcgui.Dialog()
			if currently_selected_studios is not None:
				ret1 = current_dialog.multiselect(xbmc.getInfoLabel('ListItem.Label'), current_studio_lists,0,currently_selected_studios)
			else:
				ret1 = current_dialog.multiselect(xbmc.getInfoLabel('ListItem.Label'), current_studio_lists)
			del current_dialog
			if ret1 is not None:
				if 0 in ret1:
					current_query['studio'] = None
				else:
					current_query['studio'] = [x for x in current_studio_lists if current_studio_lists.index(x) in ret1]
		xbmcgui.Window(IAGL.windowid).setProperty('iagl_random_query',json.dumps(current_query))
		xbmc.executebuiltin('Container.Refresh')

	if random_id == 'execute':
		if current_query['title'] is None:
			current_query['title'] = 1
		if current_query['lists'] is None and not IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_silence_query_warning')):
			current_dialog = xbmcgui.Dialog()
			ret1 = current_dialog.select(IAGL.loc_str(30315), [IAGL.loc_str(30200),IAGL.loc_str(30201)])
			del current_dialog
			if ret1 == 0:
				plugin.run(['plugin://plugin.program.iagl/run_random/1/', '0', IAGL.get_query_as_url(current_query)])
			else:
				xbmc.log(msg='IAGL:  User cancelled large query', level=xbmc.LOGDEBUG)
		else:
			if not IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_silence_query_warning')) and len(current_query['lists'])>10:
				current_dialog = xbmcgui.Dialog()
				ret1 = current_dialog.select(IAGL.loc_str(30316), [IAGL.loc_str(30200),IAGL.loc_str(30201)])
				del current_dialog
				if ret1 == 0:
					plugin.run(['plugin://plugin.program.iagl/run_random/1/', '0', IAGL.get_query_as_url(current_query)])
				else:
					xbmc.log(msg='IAGL:  User cancelled large query', level=xbmc.LOGDEBUG)
			else:
				plugin.run(['plugin://plugin.program.iagl/run_random/1/', '0', IAGL.get_query_as_url(current_query)])

@plugin.route('/generate_random_item')
def generate_random_listitem():
	xbmc.log(msg='IAGL:  Generate random listitem called', level=xbmc.LOGDEBUG)
	try:
		current_query = json.loads(xbmcgui.Window(IAGL.windowid).getProperty('iagl_random_query'))
	except:
		xbmc.log(msg='IAGL:  Random query could not be loaded, resetting the query', level=xbmc.LOGDEBUG)
		IAGL.initialize_search_query()
		current_query = json.loads(xbmcgui.Window(IAGL.windowid).getProperty('iagl_random_query'))
	create_listitem = False
	if current_query['title'] is None:
		current_query['title'] = 1
	if current_query['lists'] is None:
		current_dialog = xbmcgui.Dialog()
		ret1 = current_dialog.select(IAGL.loc_str(30317), [IAGL.loc_str(30200),IAGL.loc_str(30201)])
		del current_dialog
		if ret1 == 0:
			create_listitem = True
		else:
			xbmc.log(msg='IAGL:  User cancelled large query', level=xbmc.LOGDEBUG)
	else:
		if len(current_query['lists'])>10:
			current_dialog = xbmcgui.Dialog()
			ret1 = current_dialog.select(IAGL.loc_str(30318), [IAGL.loc_str(30200),IAGL.loc_str(30201)])
			del current_dialog
			if ret1 == 0:
				create_listitem = True
			else:
				xbmc.log(msg='IAGL:  User cancelled large query', level=xbmc.LOGDEBUG)
		else:
			create_listitem = True
	default_label = 'IAGL Random Play %(query_value)s' % {'query_value':IAGL.get_random_time()}
	if create_listitem:
		current_dialog = xbmcgui.Dialog()
		new_value = current_dialog.input(IAGL.loc_str(30320),default_label)
		del current_dialog
		if len(new_value)<1:
			new_value = default_label
		xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for_path('/run_random/1/?'+IAGL.get_query_as_url(current_query)),IAGL.get_random_query_listitem(new_value,current_query), True)
		xbmcplugin.endOfDirectory(plugin.handle)
	else:
		pass

@plugin.route('/run_random/<page_number>/')
def run_random_query(page_number=1):
	current_query = IAGL.get_query_from_args(plugin.args)
	if current_query['title'] is not None:
		xbmc.log(msg='IAGL:  Executing random query', level=xbmc.LOGDEBUG)
		xbmc.log(msg='IAGL:  Query Number of Results: %(query_value)s' % {'query_value':current_query['title']}, level=xbmc.LOGDEBUG)
		xbmc.log(msg='IAGL:  Query Tag: %(query_value)s' % {'query_value':current_query['tag']}, level=xbmc.LOGDEBUG)
		xbmc.log(msg='IAGL:  Query Lists: %(query_value)s' % {'query_value':current_query['lists']}, level=xbmc.LOGDEBUG)
		xbmc.log(msg='IAGL:  Query Years: %(query_value)s' % {'query_value':current_query['year']}, level=xbmc.LOGDEBUG)
		xbmc.log(msg='IAGL:  Query Genres: %(query_value)s' % {'query_value':current_query['genre']}, level=xbmc.LOGDEBUG)
		xbmc.log(msg='IAGL:  Query Players: %(query_value)s' % {'query_value':current_query['nplayers']}, level=xbmc.LOGDEBUG)
		xbmc.log(msg='IAGL:  Query Studios: %(query_value)s' % {'query_value':current_query['studio']}, level=xbmc.LOGDEBUG)
		list_method = 'list_all'
		xbmc.log(msg='IAGL:  Getting game list for random play, display method %(list_method)s with %(items_pp)s items per page, on page %(page_number)s' % {'list_method': list_method, 'items_pp': str(IAGL.get_items_per_page()), 'page_number': page_number}, level=xbmc.LOGDEBUG)
		current_page, page_info = IAGL.get_games_from_random_query_as_listitems(current_query,list_method,None,page_number)
		for list_item in current_page:
			current_game_list_id = json.loads(list_item.getProperty('iagl_json')).get('emu').get('game_list_id')
			xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game, game_list_id=url_quote(current_game_list_id), game_id=url_quote(list_item.getLabel2())),IAGL.add_game_context_menus(list_item,current_game_list_id,url_quote(list_item.getLabel2()),page_info['categories']), True) #Method 1, dont pass json as arg
		next_page_li = IAGL.get_next_page_listitem(page_info['page'],page_info['page_count'],page_info['next_page'],page_info['item_count'])
		if next_page_li is not None:
			xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(get_game_list, list_method=list_method, game_list_id=game_list_id, page_number=page_info['next_page']),next_page_li, True)
		xbmcplugin.endOfDirectory(plugin.handle)
		if IAGL.get_setting_as_bool(IAGL.handle.getSetting(id='iagl_enable_forced_views')) and int(IAGL.handle.getSetting(id='iagl_enable_forced_views_11')) > 0:
			xbmc.log(msg='IAGL:  Games Random Results Viewtype forced to %(view_type)s' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_11'))]}, level=xbmc.LOGDEBUG)
			xbmc.executebuiltin('Container.SetViewMode(%(view_type)s)' % {'view_type': IAGL.force_viewtype_options[int(IAGL.handle.getSetting(id='iagl_enable_forced_views_11'))]})
	else:
		pass

@plugin.route('/text_viewer')
def iagl_text_viewer():
	IAGL_text_Dialog = iagl_textviewer_dialog('script-IAGL-textviewer.xml',IAGL.get_addon_install_path(),'Default','1080i')
	IAGL_text_Dialog.doModal()
	del IAGL_text_Dialog

if __name__ == '__main__':
	plugin.run(sys.argv)