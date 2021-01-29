#Internet Archive Game Launcher v3.X
#Zach Morris
#https://github.com/zach-morris/plugin.program.iagl
# from kodi_six import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs
import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs
xbmc.log(msg='IAGL:  Lets Play!',level=xbmc.LOGINFO)
xbmc.log(msg='IAGL:  Version %(addon_version)s'%{'addon_version':xbmcaddon.Addon().getAddonInfo('version')},level=xbmc.LOGDEBUG)
import routing, sys, json, re
# from urllib.parse import unquote_plus as url_unquote
from random import sample as random_sample
from resources.lib.main import iagl_addon
from resources.lib import paginate
from resources.lib.utils import clear_mem_cache, get_mem_cache, set_mem_cache, get_next_page_listitem, get_setting_as, get_game_listitem, check_if_file_exists, check_if_dir_exists, clean_image_entry, clean_trailer_entry, loc_str, check_and_close_notification, get_history_listitem, update_listitem_title, zachs_debug

## Plugin Initialization Stuff ##
SLEEP_HACK=50  #https://github.com/xbmc/xbmc/issues/18576
plugin = routing.Plugin()
iagl_addon = iagl_addon()
iagl_download = None
iagl_post_process = None
iagl_launch = None
xbmcplugin.setContent(plugin.handle,iagl_addon.settings.get('views').get('content_type')) #Define the content type per settings

## Plugin Routes ##
@plugin.route('/')
def index_route():
	if iagl_addon.settings.get('tou'):
		plugin.redirect(iagl_addon.settings.get('index_list').get('route'))
	else:
		plugin.redirect('/tou')

@plugin.route('/tou')
def show_tou():
	from resources.lib.main import iagl_dialog_TOU
	TOU_Dialog = iagl_dialog_TOU('IAGL-TOU.xml',iagl_addon.directory.get('addon').get('path'),'Default','1080i')
	TOU_Dialog.doModal()
	del TOU_Dialog
	xbmc.sleep(500) #Small sleep call here to ensure the new setting is written to file
	if get_setting_as(setting_type='bool',setting=xbmcaddon.Addon(id=iagl_addon.name).getSetting(id='iagl_hidden_bool_tou')): #Need to recall setting to get the new value instead of the old
		plugin.redirect(iagl_addon.settings.get('index_list').get('route'))
	else:
		xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/archives/Browse All Lists')
def archives_browse_all_route():
	# xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for_path('/'),xbmcgui.ListItem('Browse All',offscreen=True), True) #Test li
	xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path('/game_list/%(game_list_route)s/%(label2)s'%{'label2':x.getLabel2(),'game_list_route':iagl_addon.settings.get('game_list').get('route')}),x,True) for x in iagl_addon.game_lists.get_game_lists_as_listitems() if x and x.getLabel2()!='history'])
	for sm in iagl_addon.get_sort_methods('Browse All Lists'):
		xbmcplugin.addSortMethod(plugin.handle,sm)
	xbmcplugin.endOfDirectory(plugin.handle)
	if iagl_addon.settings.get('game_list').get('force_viewtypes') and get_setting_as(setting_type='forced_viewtype',setting=iagl_addon.handle.getSetting(id='iagl_enable_forced_views_2')):
		xbmc.sleep(SLEEP_HACK)
		xbmc.executebuiltin('Container.SetViewMode(%(view_type)s)'%{'view_type': get_setting_as(setting_type='forced_viewtype',setting=iagl_addon.handle.getSetting(id='iagl_enable_forced_views_2'))})

@plugin.route('/archives/Choose from List')
def archives_choose_from_list_route():
	clear_mem_cache('iagl_current_query')
	xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path('/archives/%(label2)s'%{'label2':x.getLabel2()}),x,True) for x in iagl_addon.routes.get_route_as_listitems('browse')])
	if check_if_file_exists(iagl_addon.directory.get('userdata').get('list_cache').get('path').joinpath('history.json')): #Add history listitem
		xbmcplugin.addDirectoryItem(plugin.handle,plugin.url_for_path('/game_history/list_all/%(label2)s'%{'label2':'history'}),get_history_listitem(),True)
	xbmcplugin.endOfDirectory(plugin.handle)
	if iagl_addon.settings.get('game_list').get('force_viewtypes') and get_setting_as(setting_type='forced_viewtype',setting=iagl_addon.handle.getSetting(id='iagl_enable_forced_views_1')):
		xbmc.sleep(SLEEP_HACK)
		xbmc.executebuiltin('Container.SetViewMode(%(view_type)s)'%{'view_type': get_setting_as(setting_type='forced_viewtype',setting=iagl_addon.handle.getSetting(id='iagl_enable_forced_views_1'))})

@plugin.route('/archives/Browse by Category')
def archives_browse_by_category_route():
	clear_mem_cache('iagl_current_query')
	xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path('/archives/by_category/%(label2)s'%{'label2':x.getLabel2()}),x,True) for x in iagl_addon.routes.get_route_as_listitems('categories')])
	if check_if_file_exists(iagl_addon.directory.get('userdata').get('list_cache').get('path').joinpath('history.json')): #Add history listitem
		xbmcplugin.addDirectoryItem(plugin.handle,plugin.url_for_path('/game_history/list_all/%(label2)s'%{'label2':'history'}),get_history_listitem(),True)
	for sm in iagl_addon.get_sort_methods('Browse by Category'):
		xbmcplugin.addSortMethod(plugin.handle,sm)
	xbmcplugin.endOfDirectory(plugin.handle)
	if iagl_addon.settings.get('game_list').get('force_viewtypes') and get_setting_as(setting_type='forced_viewtype',setting=iagl_addon.handle.getSetting(id='iagl_enable_forced_views_3')):
		xbmc.sleep(SLEEP_HACK)
		xbmc.executebuiltin('Container.SetViewMode(%(view_type)s)'%{'view_type': get_setting_as(setting_type='forced_viewtype',setting=iagl_addon.handle.getSetting(id='iagl_enable_forced_views_3'))})

@plugin.route('/archives/Favorites')
def archives_browse_by_favorites_route():
	plugin.redirect('/archives/by_category/Favorites')

@plugin.route('/archives/Search')
def archives_search_route():
	for x in iagl_addon.routes.get_search_random_route_as_listitems('search'):
		if x.getLabel2() == 'execute':
			xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for(search_games,query=json.dumps(get_mem_cache('iagl_current_query'))),x,True)])
		else:
			xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path('/archives/Search/%(label2)s'%{'label2':x.getLabel2()}),x,True)])
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/archives/Search/<value_in>')
def archives_search_update_title(value_in):
	iagl_addon.game_lists.update_search_random_query(value_in)
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/Search')
def search_games():
	query = None
	if plugin.args.get('query'):
		query=json.loads(plugin.args['query'][0])
	if query is not None:
		filter_dict = {'info':{},'properties':{}}
		if 'title' in query.keys() and query.get('title'):
			filter_dict['info'].update({'title':re.compile(query.get('title'),re.IGNORECASE)})
		if 'genre' in query.keys() and query.get('genre'):
			filter_dict['info'].update({'genre':query.get('genre')})
		if 'year' in query.keys() and query.get('year'):
			filter_dict['info'].update({'year':query.get('year')})
		if 'studio' in query.keys() and query.get('studio'):
			filter_dict['info'].update({'studio':query.get('studio')})
		if 'tag' in query.keys() and query.get('tag'):
			filter_dict['info'].update({'tag':query.get('tag')})
		if 'groups' in query.keys() and query.get('groups'):
			filter_dict['info'].update({'showlink':query.get('groups')})
		if 'nplayers' in query.keys() and query.get('nplayers'):
			filter_dict['properties'].update({'nplayers':query.get('nplayers')})
		if 'lists' in query.keys() and query.get('lists'):
			game_list_ids = query.get('lists')
		else:
			game_list_ids = iagl_addon.game_lists.list_game_lists()

		game_listitems = list()
		for game_list_id in game_list_ids:
			game_listitems = game_listitems+iagl_addon.game_lists.get_games_as_listitems(game_list_id=game_list_id,filter_in=filter_dict)

		xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path('/game/%(game_list_id)s/%(label2)s'%{'label2':x.getLabel2(),'game_list_id':game_list_id}),update_listitem_title(x,iagl_addon.settings.get('game_list').get('append_emu_name')),True) for x in game_listitems if x])
		for sm in iagl_addon.get_sort_methods('Games'):
			xbmcplugin.addSortMethod(plugin.handle,sm)
	xbmcplugin.endOfDirectory(plugin.handle)
	if iagl_addon.settings.get('game_list').get('force_viewtypes') and get_setting_as(setting_type='forced_viewtype',setting=iagl_addon.handle.getSetting(id='iagl_enable_forced_views_12')):
		xbmc.sleep(SLEEP_HACK)
		xbmc.executebuiltin('Container.SetViewMode(%(view_type)s)'%{'view_type': get_setting_as(setting_type='forced_viewtype',setting=iagl_addon.handle.getSetting(id='iagl_enable_forced_views_12'))})

@plugin.route('/archives/Random Play')
def archives_search_route():
	for x in iagl_addon.routes.get_search_random_route_as_listitems('random'):
		if x.getLabel2() == 'execute':
			xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for(random_games,query=json.dumps(get_mem_cache('iagl_current_query'))),x,True)])
		else:
			xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path('/archives/Random Play/%(label2)s'%{'label2':x.getLabel2()}),x,True)])
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/archives/Random Play/<value_in>')
def archives_search_update_title(value_in):
	iagl_addon.game_lists.update_search_random_query(value_in)
	xbmc.executebuiltin('Container.Refresh')

@plugin.route('/Random Play')
def random_games():
	query = None
	if plugin.args.get('query'):
		query=json.loads(plugin.args['query'][0])
	if query is not None:
		num_of_results = 1
		if 'num_of_results' in query.keys() and query.get('num_of_results'):
			num_of_results = int(query.get('num_of_results'))

		filter_dict = {'info':{},'properties':{}}
		if 'genre' in query.keys() and query.get('genre'):
			filter_dict['info'].update({'genre':query.get('genre')})
		if 'year' in query.keys() and query.get('year'):
			filter_dict['info'].update({'year':query.get('year')})
		if 'studio' in query.keys() and query.get('studio'):
			filter_dict['info'].update({'studio':query.get('studio')})
		if 'tag' in query.keys() and query.get('tag'):
			filter_dict['info'].update({'tag':query.get('tag')})
		if 'groups' in query.keys() and query.get('groups'):
			filter_dict['info'].update({'showlink':query.get('groups')})
		if 'nplayers' in query.keys() and query.get('nplayers'):
			filter_dict['properties'].update({'nplayers':query.get('nplayers')})
		if 'lists' in query.keys() and query.get('lists'):
			game_list_ids = query.get('lists')
		else:
			game_list_ids = iagl_addon.game_lists.list_game_lists()

		game_listitems = list()
		for game_list_id in game_list_ids:
			game_listitems = game_listitems+iagl_addon.game_lists.get_games_as_listitems(game_list_id=game_list_id,filter_in=filter_dict)
		game_listitems = random_sample(game_listitems,num_of_results) #Get random listitems using random sample

		xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path('/game/%(game_list_id)s/%(label2)s'%{'label2':x.getLabel2(),'game_list_id':game_list_id}),update_listitem_title(x,iagl_addon.settings.get('game_list').get('append_emu_name')),True) for x in game_listitems if x])
		for sm in iagl_addon.get_sort_methods('Games'):
			xbmcplugin.addSortMethod(plugin.handle,sm)
	xbmcplugin.endOfDirectory(plugin.handle)
	if iagl_addon.settings.get('game_list').get('force_viewtypes') and get_setting_as(setting_type='forced_viewtype',setting=iagl_addon.handle.getSetting(id='iagl_enable_forced_views_13')):
		xbmc.sleep(SLEEP_HACK)
		xbmc.executebuiltin('Container.SetViewMode(%(view_type)s)'%{'view_type': get_setting_as(setting_type='forced_viewtype',setting=iagl_addon.handle.getSetting(id='iagl_enable_forced_views_13'))})

@plugin.route('/archives/by_category/<category_id>')
def archives_game_lists_in_category_route(category_id):
	if category_id == 'Search':
		plugin.redirect('/archives/Search')
	elif category_id == 'Random Play':
		plugin.redirect('/archives/Random Play')
	else:
		xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path('/game_list/%(game_list_route)s/%(label2)s'%{'label2':x.getLabel2(),'game_list_route':iagl_addon.settings.get('game_list').get('route')}),x,True) for x in iagl_addon.game_lists.get_game_lists_as_listitems(filter_in={'info':{'genre':category_id},'properties':{}}) if x])
		for sm in iagl_addon.get_sort_methods('Browse All Lists'):
			xbmcplugin.addSortMethod(plugin.handle,sm)
		xbmcplugin.endOfDirectory(plugin.handle)
	if iagl_addon.settings.get('game_list').get('force_viewtypes') and get_setting_as(setting_type='forced_viewtype',setting=iagl_addon.handle.getSetting(id='iagl_enable_forced_views_3')):
		xbmc.sleep(SLEEP_HACK)
		xbmc.executebuiltin('Container.SetViewMode(%(view_type)s)'%{'view_type': get_setting_as(setting_type='forced_viewtype',setting=iagl_addon.handle.getSetting(id='iagl_enable_forced_views_3'))})

@plugin.route('/game_list/list_all/<game_list_id>/')
def get_all_games_redirect(game_list_id):
	plugin.redirect('/game_list/list_all/'+game_list_id+'/1')

@plugin.route('/game_list/list_all/<game_list_id>/<page_number>')
def game_list_list_all_route(game_list_id,page_number):
	if iagl_addon.settings.get('game_list').get('games_per_page'):
		current_page = paginate.Page([(plugin.url_for_path('/game/%(game_list_id)s/%(label2)s'%{'label2':x.getLabel2(),'game_list_id':game_list_id}),x,True) for x in iagl_addon.game_lists.get_games_as_listitems(game_list_id=game_list_id) if x], page=int(page_number), items_per_page=iagl_addon.settings.get('game_list').get('games_per_page'))
		if current_page.next_page and current_page.page<current_page.next_page:
			current_page.append((plugin.url_for_path('/game_list/list_all/%(game_list_id)s/%(label2)s'%{'label2':current_page.next_page,'game_list_id':game_list_id}),get_next_page_listitem(current_page=current_page.page,page_count=current_page.page_count,next_page=current_page.next_page,total_items=current_page.item_count),True))
		xbmcplugin.addDirectoryItems(plugin.handle,current_page)
	else:
		xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path('/game/%(game_list_id)s/%(label2)s'%{'label2':x.getLabel2(),'game_list_id':game_list_id}),x,True) for x in iagl_addon.game_lists.get_games_as_listitems(game_list_id=game_list_id) if x])
	for sm in iagl_addon.get_sort_methods('Games'):
		xbmcplugin.addSortMethod(plugin.handle,sm)
	xbmcplugin.endOfDirectory(plugin.handle)
	if iagl_addon.settings.get('game_list').get('force_viewtypes') and get_setting_as(setting_type='forced_viewtype',setting=iagl_addon.handle.getSetting(id='iagl_enable_forced_views_4')):
		xbmc.sleep(SLEEP_HACK)
		xbmc.executebuiltin('Container.SetViewMode(%(view_type)s)'%{'view_type': get_setting_as(setting_type='forced_viewtype',setting=iagl_addon.handle.getSetting(id='iagl_enable_forced_views_4'))})

@plugin.route('/game_history/list_all/<game_list_id>/')
def get_all_games_redirect(game_list_id):
	plugin.redirect('/game_history/list_all/'+game_list_id+'/1')

@plugin.route('/game_history/list_all/<game_list_id>/<page_number>')
def game_list_list_all_route(game_list_id,page_number):
	if iagl_addon.settings.get('game_list').get('games_per_page'):
		current_page = paginate.Page([(plugin.url_for_path('/game/%(game_list_id)s/%(label2)s'%{'label2':x.getLabel2(),'game_list_id':x.getProperty('route')}),x,True) for x in iagl_addon.game_lists.get_games_as_listitems(game_list_id=game_list_id) if x], page=int(page_number), items_per_page=iagl_addon.settings.get('game_list').get('games_per_page'))
		if current_page.next_page and current_page.page<current_page.next_page:
			current_page.append((plugin.url_for_path('/game_history/list_all/%(game_list_id)s/%(label2)s'%{'label2':current_page.next_page,'game_list_id':game_list_id}),get_next_page_listitem(current_page=current_page.page,page_count=current_page.page_count,next_page=current_page.next_page,total_items=current_page.item_count),True))
		xbmcplugin.addDirectoryItems(plugin.handle,current_page)
	else:
		xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path('/game/%(game_list_id)s/%(label2)s'%{'label2':x.getLabel2(),'game_list_id':x.getProperty('route')}),x,True) for x in iagl_addon.game_lists.get_games_as_listitems(game_list_id=game_list_id) if x])
	for sm in iagl_addon.get_sort_methods('History'):
		xbmcplugin.addSortMethod(plugin.handle,sm)
	xbmcplugin.endOfDirectory(plugin.handle)
	if iagl_addon.settings.get('game_list').get('force_viewtypes') and get_setting_as(setting_type='forced_viewtype',setting=iagl_addon.handle.getSetting(id='iagl_enable_forced_views_4')):
		xbmc.sleep(SLEEP_HACK)
		xbmc.executebuiltin('Container.SetViewMode(%(view_type)s)'%{'view_type': get_setting_as(setting_type='forced_viewtype',setting=iagl_addon.handle.getSetting(id='iagl_enable_forced_views_4'))})


@plugin.route('/game_list/choose_from_list/<game_list_id>')
def game_list_choose_from_list_route(game_list_id):
	xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path('/game_list/%(label2)s/%(game_list_id)s'%{'label2':x.getLabel2(),'game_list_id':game_list_id}),x,True) for x in iagl_addon.routes.get_route_as_listitems('choose',game_list_name=iagl_addon.game_lists.get_game_list(game_list_id).get('emu_name'),game_list_id=game_list_id)])
	for sm in iagl_addon.get_sort_methods('Choose from List'):
		xbmcplugin.addSortMethod(plugin.handle,sm)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/game_list/<category_choice>/<game_list_id>')
def game_list_choose_category_from_list_route(category_choice,game_list_id):
	if category_choice=='One Big List':
		plugin.redirect('/game_list/list_all/'+game_list_id+'/1')
	else:
		xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path('/game_list/category/%(category_choice)s/%(label2)s/%(game_list_id)s/1'%{'label2':x.getLabel2().replace('#','%23'),'category_choice':category_choice,'game_list_id':game_list_id}),x,True) for x in iagl_addon.game_lists.get_game_choose_categories_as_listitems(game_list_id=game_list_id,category_choice=category_choice,game_list_name=iagl_addon.game_lists.get_game_list(game_list_id).get('emu_name')) if x])
		for sm in iagl_addon.get_sort_methods('Choose from List'):
			xbmcplugin.addSortMethod(plugin.handle,sm)
		xbmcplugin.endOfDirectory(plugin.handle)
	if iagl_addon.settings.get('game_list').get('force_viewtypes') and iagl_addon.settings.get('game_list').get('forced_views').get(category_choice) and get_setting_as(setting_type='forced_viewtype',setting=iagl_addon.handle.getSetting(id=iagl_addon.settings.get('game_list').get('forced_views').get(category_choice))):
		xbmc.sleep(SLEEP_HACK)
		xbmc.executebuiltin('Container.SetViewMode(%(view_type)s)'%{'view_type': get_setting_as(setting_type='forced_viewtype',setting=iagl_addon.handle.getSetting(id=iagl_addon.settings.get('game_list').get('forced_views').get(category_choice)))})

@plugin.route('/game_list/category/<category_choice>/<category_value>/<game_list_id>/<page_number>')
def game_list_in_category_route(category_choice,category_value,game_list_id,page_number):
	if category_choice == 'Alphabetical':
		filter_dict = {'info':{},'properties':{'starts_with':category_value.replace('%23','#')}}
	elif category_choice == 'Group by Genres':
		filter_dict = {'info':{'genre':category_value},'properties':{}}
	elif category_choice == 'Group by Years':
		filter_dict = {'info':{'year':category_value},'properties':{}}
	elif category_choice == 'Group by Players':
		filter_dict = {'info':{},'properties':{'nplayers':category_value}}
	elif category_choice == 'Group by Studio':
		filter_dict = {'info':{'studio':category_value},'properties':{}}
	elif category_choice == 'Group by Tag':
		filter_dict = {'info':{'tag':category_value},'properties':{}}
	elif category_choice == 'Group by Custom Groups':
		filter_dict = {'info':{'showlink':category_value},'properties':{}}
	else:
		filter_dict = None
	if iagl_addon.settings.get('game_list').get('games_per_page'):
		current_page = paginate.Page([(plugin.url_for_path('/game/%(game_list_id)s/%(label2)s'%{'label2':x.getLabel2(),'game_list_id':game_list_id}),x,True) for x in iagl_addon.game_lists.get_games_as_listitems(game_list_id=game_list_id,filter_in=filter_dict) if x], page=int(page_number), items_per_page=iagl_addon.settings.get('game_list').get('games_per_page'))
		if current_page.next_page and current_page.page<current_page.next_page:
			current_page.append((plugin.url_for_path('/game_list/category/%(category_choice)s/%(category_value)s/%(game_list_id)s/%(page_number)s'%{'category_choice':category_choice,'category_value':category_value,'game_list_id':game_list_id,'page_number':current_page.next_page}),get_next_page_listitem(current_page=current_page.page,page_count=current_page.page_count,next_page=current_page.next_page,total_items=current_page.item_count),True))
		xbmcplugin.addDirectoryItems(plugin.handle,current_page)
	else:
		xbmcplugin.addDirectoryItems(plugin.handle,[(plugin.url_for_path('/game/%(game_list_id)s/%(label2)s'%{'label2':x.getLabel2(),'game_list_id':game_list_id}),x,True) for x in iagl_addon.game_lists.get_games_as_listitems(game_list_id=game_list_id,filter_in=filter_dict) if x])
	for sm in iagl_addon.get_sort_methods('Games'):
		xbmcplugin.addSortMethod(plugin.handle,sm)
	xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/game/<game_list_id>/<game_id>')
def get_game(game_list_id,game_id):
	if iagl_addon.settings.get('game_action').get('select')==0: #Download and launch
		plugin.redirect('/game_launch/'+game_list_id+'/'+game_id)
	elif iagl_addon.settings.get('game_action').get('select')==1: #Download only 
		plugin.redirect('/game_download_only/'+game_list_id+'/'+game_id)
	else: #Show info page
		plugin.redirect('/game_info_page/'+game_list_id+'/'+game_id)

@plugin.route('/game_info_page/<game_list_id>/<game_id>')
def show_info_game(game_list_id,game_id):
	game = iagl_addon.game_lists.get_game_as_dict(game_list_id=game_list_id,game_id=game_id)
	if isinstance(game,dict):
		from resources.lib.main import iagl_dialog_info_page
		info_page = iagl_dialog_info_page('IAGL-infodialog.xml',iagl_addon.directory.get('addon').get('path'),'Default','1080i',game_list_id=game_list_id,game_id=game_id,game=game,game_listitem=get_game_listitem(dict_in=game,filter_in=None),autoplay_trailer=iagl_addon.settings.get('game_action').get('autoplay_trailer'))
		info_page.doModal()
		action_requested = info_page.action_requested
		del info_page
		if action_requested == 0:  #Download and launch
			plugin.redirect('/game_launch/'+game_list_id+'/'+game_id)
		elif action_requested == 1:  #Download only 
			plugin.redirect('/game_download_only/'+game_list_id+'/'+game_id)
		else:
			if iagl_addon.kodi_user.get('current_folder') != iagl_addon.title: #There has to be a better way to know what the parentpath is
				if xbmcgui.getCurrentWindowId() != 10000:
					xbmc.log(msg='IAGL:  Returning to Home', level=xbmc.LOGDEBUG)
					xbmc.executebuiltin('ActivateWindow(home)')
					xbmc.sleep(100)
	else:
		current_dialog = xbmcgui.Dialog()
		ok_ret = current_dialog.ok(loc_str(30203),loc_str(30359) % {'game_id': game_id, 'game_list_id': game_list_id})
		del current_dialog

@plugin.route('/game_launch/<game_list_id>/<game_id>')
def download_and_launch_game(game_list_id,game_id):
	game = iagl_addon.game_lists.get_game_as_dict(game_list_id=game_list_id,game_id=game_id)
	current_game_list = iagl_addon.game_lists.get_game_list(game_list_id)
	if isinstance(game,dict) and isinstance(current_game_list,dict):
		from resources.lib.download import iagl_download
		from resources.lib.post_process import iagl_post_process
		from resources.lib.launch import iagl_launch

		iagl_download = iagl_download(settings=iagl_addon.settings,directory=iagl_addon.directory,game_list=current_game_list,game=game)
		downloaded_files = iagl_download.download_game()
		iagl_post_process = iagl_post_process(settings=iagl_addon.settings,directory=iagl_addon.directory,game_list=current_game_list,game=game,game_files=downloaded_files)
		post_processed_files = iagl_post_process.post_process_game()
		iagl_launch = iagl_launch(settings=iagl_addon.settings,directory=iagl_addon.directory,game_list=current_game_list,game=game,game_files=post_processed_files)
		launched_files = iagl_launch.launch_game()

		if not iagl_addon.settings.get('ext_launchers').get('close_kodi') and check_and_close_notification():
			current_dialog = xbmcgui.Dialog()
			if all([x.get('download_success') for x in downloaded_files]) and all([x.get('post_process_success') for x in post_processed_files]) and launched_files.get('launch_process_success'):
				current_dialog.notification(loc_str(30202),launched_files.get('launch_process_message'),xbmcgui.NOTIFICATION_INFO,iagl_addon.settings.get('notifications').get('background_notification_time'),sound=False)
			elif all([not x.get('download_success') for x in downloaded_files]):
				current_dialog.notification(loc_str(30203),loc_str(30304) % {'game_title': game.get('info').get('originaltitle'),'fail_reason':[x.get('download_message') for x in downloaded_files if not x.get('download_success')][0]},xbmcgui.NOTIFICATION_ERROR,iagl_addon.settings.get('notifications').get('background_error_notification_time'))
			elif all([not x.get('post_process_success') for x in post_processed_files]):
				current_dialog.notification(loc_str(30203),loc_str(30304) % {'game_title': game.get('info').get('originaltitle'),'fail_reason':[x.get('post_process_message') for x in post_processed_files if not x.get('post_process_success')][0]},xbmcgui.NOTIFICATION_ERROR,iagl_addon.settings.get('notifications').get('background_error_notification_time'))
			elif not launched_files.get('launch_process_success'):
				current_dialog.notification(loc_str(30203),loc_str(30305) % {'game_title': game.get('info').get('originaltitle'),'fail_reason':launched_files.get('launch_process_message')},xbmcgui.NOTIFICATION_ERROR,iagl_addon.settings.get('notifications').get('background_error_notification_time'))
			else:
				current_dialog.notification(loc_str(30203),loc_str(30303) % {'game_title': game.get('info').get('originaltitle'),'fail_reason':launched_files.get('launch_process_message')},xbmcgui.NOTIFICATION_ERROR,iagl_addon.settings.get('notifications').get('background_error_notification_time'))
		
		iagl_post_launch = iagl_launch.post_launch_check(game_launch_status=launched_files)
	else:
		current_dialog = xbmcgui.Dialog()
		ok_ret = current_dialog.ok(loc_str(30203),loc_str(30359) % {'game_id': game_id, 'game_list_id': game_list_id})
		del current_dialog

@plugin.route('/game_download_only/<game_list_id>/<game_id>')
def download_only_game(game_list_id,game_id):
	game = iagl_addon.game_lists.get_game_as_dict(game_list_id=game_list_id,game_id=game_id)
	current_game_list = iagl_addon.game_lists.get_game_list(game_list_id)
	if isinstance(game,dict) and isinstance(current_game_list,dict):
		from resources.lib.download import iagl_download
		from resources.lib.post_process import iagl_post_process

		iagl_download = iagl_download(settings=iagl_addon.settings,directory=iagl_addon.directory,game_list=current_game_list,game=game)
		downloaded_files = iagl_download.download_game()
		check_and_close_notification()
		iagl_post_process = iagl_post_process(settings=iagl_addon.settings,directory=iagl_addon.directory,game_list=current_game_list,game=game,game_files=downloaded_files)
		post_processed_files = iagl_post_process.post_process_game()

		if check_and_close_notification():
			current_dialog = xbmcgui.Dialog()
			if all([x.get('download_success') for x in downloaded_files]) and all([x.get('post_process_success') for x in post_processed_files]):
				current_dialog.notification(loc_str(30202),loc_str(30302) % {'game_title': game.get('info').get('originaltitle')},xbmcgui.NOTIFICATION_INFO,iagl_addon.settings.get('notifications').get('background_notification_time'))
			elif all([not x.get('download_success') for x in downloaded_files]):
				current_dialog.notification(loc_str(30203),loc_str(30304) % {'game_title': game.get('info').get('originaltitle'),'fail_reason':[x.get('download_message') for x in downloaded_files if not x.get('download_success')][0]},xbmcgui.NOTIFICATION_ERROR,iagl_addon.settings.get('notifications').get('background_error_notification_time'))
			elif all([not x.get('post_process_success') for x in post_processed_files]):
				current_dialog.notification(loc_str(30203),loc_str(30304) % {'game_title': game.get('info').get('originaltitle'),'fail_reason':[x.get('post_process_message') for x in post_processed_files if not x.get('post_process_success')][0]},xbmcgui.NOTIFICATION_ERROR,iagl_addon.settings.get('notifications').get('background_error_notification_time'))
			else:
				current_dialog.notification(loc_str(30203),loc_str(30303) % {'game_title': game.get('info').get('originaltitle'),'fail_reason':[x.get('download_message') for x in downloaded_files if not x.get('download_success')][0]},xbmcgui.NOTIFICATION_ERROR,iagl_addon.settings.get('notifications').get('background_error_notification_time'))
	else:
		current_dialog = xbmcgui.Dialog()
		ok_ret = current_dialog.ok(loc_str(30203),loc_str(30359) % {'game_id': game_id, 'game_list_id': game_list_id})
		del current_dialog

@plugin.route('/context_menu/edit/<game_list_id>/<edit_id>')
def context_menu_edit(game_list_id,edit_id):
	current_dialog = xbmcgui.Dialog()
	current_crc = iagl_addon.game_lists.get_crc(game_list_id)
	addons_available = []
	# ,'emu_postdlaction','emu_default_addon'
	if edit_id in ['emu_launcher','emu_visibility','emu_default_addon']:
		if edit_id == 'emu_default_addon':
			try:
				json_query = json.loads(xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Addons.GetAddons","params":{"type":"kodi.gameclient"}, "id": "1"}'))
			except Exception as exc:
				xbmc.log(msg='IAGL:  Error executing JSONRPC command.  Exception %(exc)s' % {'exc': exc}, level=xbmc.LOGERROR)
				json_query = None
			if json_query and json_query.get('result') and json_query.get('result').get('addons'):
				addons_available = sorted([x.get('addonid') for x in json_query.get('result').get('addons') if x.get('addonid')!='game.libretro'])
			# {"id":"1","jsonrpc":"2.0","result":{"addons":[{"addonid":"game.libretro","type":"kodi.gameclient"},{"addonid":"game.libretro.cannonball","type":"kodi.gameclient"},{"addonid":"game.libretro.fbneo","type":"kodi.gameclient"},{"addonid":"game.libretro.mame2003","type":"kodi.gameclient"},{"addonid":"game.libretro.mame2003_plus","type":"kodi.gameclient"},{"addonid":"game.libretro.mame2015","type":"kodi.gameclient"}],"limits":{"end":6,"start":0,"total":6}}}
		current_choices = dict(zip(['emu_launcher','emu_visibility','emu_default_addon'],[dict(zip(['query','query_values','header_values','current_choice'],[loc_str(30333),[loc_str(30363),loc_str(30364)],['external','retroplayer'],loc_str(30045)])),
																	dict(zip(['query','query_values','header_values','current_choice'],[loc_str(30334),[loc_str(30200),loc_str(30201)],['hidden','visible'],loc_str(30403)])),
																	dict(zip(['query','query_values','header_values','current_choice'],[loc_str(30339),[loc_str(30338)]+[xbmcaddon.Addon(id='%(addon_name)s' % {'addon_name':x}).getAddonInfo('name') for x in addons_available],['none']+addons_available,loc_str(30409)])),
																	]))
		choices = current_choices.get(edit_id)
		new_value = current_dialog.select(choices.get('query'),choices.get('query_values'))
		if new_value in [ii for ii,x in enumerate(choices.get('query_values'))] and choices.get('query_values')[new_value] != loc_str(30201): #Make sure the new value is indexable and is not 'Cancel'
			success = iagl_addon.game_lists.update_game_list_header(game_list_id,header_key=edit_id,header_value=choices.get('header_values')[new_value],current_choice=choices.get('current_choice'))
			if success:
				if iagl_addon.refresh_list(current_crc):
					ok_ret = current_dialog.ok(loc_str(30202),loc_str(30345)%{'current_filename':game_list_id})
				else:
					ok_ret = current_dialog.ok(loc_str(30202),loc_str(30346)%{'current_filename':game_list_id})
			xbmc.executebuiltin('Container.Refresh')
	if edit_id in ['emu_launcher']: #Redirect to update the launch command if they updated the launch type
		if choices.get('header_values')[new_value] == 'external':
			plugin.redirect('/context_menu/select/'+game_list_id+'/emu_ext_launch_cmd')
		elif choices.get('header_values')[new_value] == 'retroplayer':
			plugin.redirect('/context_menu/edit/'+game_list_id+'/emu_default_addon')
	else:
		xbmc.log(msg='IAGL:  Unknown context edit selection %(edit_id)s'%{'edit_id':edit_id},level=xbmc.LOGERROR)
	del current_dialog

@plugin.route('/context_menu/select/<game_list_id>/<select_id>')
def context_menu_select(game_list_id,select_id):
	current_dialog = xbmcgui.Dialog()
	current_crc = iagl_addon.game_lists.get_crc(game_list_id)
	if select_id == 'emu_downloadpath':
		current_choices = dict(zip(['emu_downloadpath'],[dict(zip(['query','query_values','header_values','current_choice'],[loc_str(30336),[loc_str(30207),loc_str(30208),loc_str(30201)],[0,1,2],''])),]))
		choices = current_choices.get(select_id)
		new_value = current_dialog.select(choices.get('query'),choices.get('query_values'))
		if new_value in [0,1]: #Make sure the new value is indexable and is not 'Cancel'
			if new_value == 0: #Default Dir
				success = iagl_addon.game_lists.update_game_list_header(game_list_id,header_key=select_id,header_value='default',current_choice=loc_str(30513))
				if success:
					if iagl_addon.refresh_list(current_crc):
						ok_ret = current_dialog.ok(loc_str(30202),loc_str(30345)%{'current_filename':game_list_id})
					else:
						ok_ret = current_dialog.ok(loc_str(30202),loc_str(30346)%{'current_filename':game_list_id})
				xbmc.executebuiltin('Container.Refresh')
			else: #Custom Dir
				new_value = current_dialog.browse(0,loc_str(30337),'')
				if check_if_dir_exists(new_value):
					success = iagl_addon.game_lists.update_game_list_header(game_list_id,header_key=select_id,header_value=new_value,current_choice=loc_str(30513))
					if success:
						if iagl_addon.refresh_list(current_crc):
							ok_ret = current_dialog.ok(loc_str(30202),loc_str(30345)%{'current_filename':game_list_id})
						else:
							ok_ret = current_dialog.ok(loc_str(30202),loc_str(30346)%{'current_filename':game_list_id})
					xbmc.executebuiltin('Container.Refresh')
	elif select_id == 'metadata':
		current_choices = dict(zip(['metadata'],[dict(zip(['query','query_values','header_values','current_choice'],[loc_str(30331),[loc_str(30414),loc_str(30415),loc_str(30416),loc_str(30417),loc_str(30418),loc_str(30419),loc_str(30420)],['emu_name','emu_category','emu_description', 'emu_comment', 'emu_trailer', 'emu_author', 'emu_date'],''])),]))
		choices = current_choices.get(select_id)
		new_value = current_dialog.select(choices.get('query'),choices.get('query_values'))
		if new_value in [ii for ii,x in enumerate(choices.get('query_values'))] and choices.get('query_values')[new_value] != loc_str(30201):
			current_game_list = iagl_addon.game_lists.get_game_list(game_list_id)
			new_value2 = current_dialog.input(loc_str(30343)%{'current_choice':choices.get('query_values')[new_value]},current_game_list.get(choices.get('header_values')[new_value]))
			if choices.get('header_values')[new_value] == 'emu_trailer':
				new_value2 = clean_trailer_entry(new_value2)
			if new_value2:
				success = iagl_addon.game_lists.update_game_list_header(game_list_id,header_key=choices.get('header_values')[new_value],header_value=new_value2,current_choice=choices.get('query_values')[new_value])
				if success:
					if iagl_addon.refresh_list(current_crc):
						ok_ret = current_dialog.ok(loc_str(30202),loc_str(30345)%{'current_filename':game_list_id})
					else:
						ok_ret = current_dialog.ok(loc_str(30202),loc_str(30346)%{'current_filename':game_list_id})
					xbmc.executebuiltin('Container.Refresh')
			else:
				if choices.get('header_values')[new_value] == 'emu_trailer':
					ok_ret = current_dialog.ok(loc_str(30203),loc_str(30374))
	elif select_id == 'art':
		current_choices = dict(zip(['art'],[dict(zip(['query','query_values','header_values','current_choice'],[loc_str(30332),[loc_str(30421),loc_str(30422),loc_str(30423),loc_str(30424)],['emu_thumb', 'emu_logo', 'emu_banner', 'emu_fanart'],''])),]))
		choices = current_choices.get(select_id)
		new_value = current_dialog.select(choices.get('query'),choices.get('query_values'))
		if new_value in [ii for ii,x in enumerate(choices.get('query_values'))] and choices.get('query_values')[new_value] != loc_str(30201):
			current_game_list = iagl_addon.game_lists.get_game_list(game_list_id)
			new_value2 = clean_image_entry(current_dialog.input(loc_str(30343)%{'current_choice':choices.get('query_values')[new_value]},current_game_list.get(choices.get('header_values')[new_value])))
			if new_value2:
				success = iagl_addon.game_lists.update_game_list_header(game_list_id,header_key=choices.get('header_values')[new_value],header_value=new_value2,current_choice=choices.get('query_values')[new_value])
				if success:
					if iagl_addon.refresh_list(current_crc):
						ok_ret = current_dialog.ok(loc_str(30202),loc_str(30345)%{'current_filename':game_list_id})
					else:
						ok_ret = current_dialog.ok(loc_str(30202),loc_str(30346)%{'current_filename':game_list_id})
					xbmc.executebuiltin('Container.Refresh')
			else:
				ok_ret = current_dialog.ok(loc_str(30203),loc_str(30373))
	elif select_id == 'emu_ext_launch_cmd':
		current_choices = iagl_addon.get_ext_launch_cmds() #Generate list of commands to use based on RA and other EXT launch settings
		if current_choices:
			new_value = current_dialog.select(loc_str(30363),[x.get('@name') for x in current_choices]+[loc_str(30583)])
			if new_value in [ii for ii,x in enumerate(current_choices)]:
				success = iagl_addon.game_lists.update_game_list_header(game_list_id,header_key='emu_ext_launch_cmd',header_value=current_choices[new_value].get('command'),current_choice=loc_str(30363))
				if success:
					if iagl_addon.refresh_list(current_crc):
						ok_ret = current_dialog.ok(loc_str(30202),loc_str(30345)%{'current_filename':game_list_id})
					else:
						ok_ret = current_dialog.ok(loc_str(30202),loc_str(30346)%{'current_filename':game_list_id})
					xbmc.executebuiltin('Container.Refresh')
			elif new_value == len(current_choices): #Manual Entry
				current_game_list = iagl_addon.game_lists.get_game_list(game_list_id)
				new_value2 = current_dialog.input(loc_str(30342),current_game_list.get('emu_ext_launch_cmd'))
				if new_value2:
					success = iagl_addon.game_lists.update_game_list_header(game_list_id,header_key='emu_ext_launch_cmd',header_value=new_value2,current_choice=loc_str(30363))
					if success:
						if iagl_addon.refresh_list(current_crc):
							ok_ret = current_dialog.ok(loc_str(30202),loc_str(30345)%{'current_filename':game_list_id})
						else:
							ok_ret = current_dialog.ok(loc_str(30202),loc_str(30346)%{'current_filename':game_list_id})
					xbmc.executebuiltin('Container.Refresh')
	else:
		xbmc.log(msg='IAGL:  Unknown context edit selection %(select_id)s'%{'select_id':select_id},level=xbmc.LOGERROR)
	del current_dialog

@plugin.route('/context_menu/action/<game_list_id>/<action_id>')
def context_menu_action(game_list_id,action_id):
	if action_id == 'view_list_settings':
		current_game_list = iagl_addon.game_lists.get_game_list(game_list_id)
		current_emu_postdlaction = dict(zip(['none','unzip_rom','unzip_and_launch_file','unzip_to_folder_and_launch_file'],['None (Direct File Launch)','UnArchive Game','UnArchive Game, Launch File','UnArchive Game to Folder, Launch File'])).get(current_game_list.get('emu_postdlaction'))
		if not current_emu_postdlaction:
			current_emu_postdlaction = current_game_list.get('emu_postdlaction')
		launch_command_string = ''
		download_path_string = loc_str(30361)
		current_header = loc_str(30362)%{'game_list_id':game_list_id}
		if current_game_list.get('emu_launcher') == 'external':
			if current_game_list.get('emu_ext_launch_cmd') == 'none':
				launch_command_string = '[COLOR FF12A0C7]%(elc)s:  [/COLOR]Not Set!'%{'elc':loc_str(30363)}
			else:
				launch_command_string = '[COLOR FF12A0C7]%(elc)s:  [/COLOR]%(lc)s'%{'elc':loc_str(30363),'lc':current_game_list.get('emu_ext_launch_cmd')}
		if current_game_list.get('emu_launcher') == 'retroplayer':
			if current_game_list.get('emu_default_addon') == 'none':
				launch_command_string = '[COLOR FF12A0C7]%(rp)s:  [/COLOR]%(auto)s'%{'rp':loc_str(30364),'auto':loc_str(30338)}
			else:
				launch_command_string = '[COLOR FF12A0C7]%(rp)s:  [/COLOR]%(lc)s'%{'rp':loc_str(30364),'lc':current_game_list.get('emu_default_addon')}
		if current_game_list.get('emu_downloadpath') != 'default':
			download_path_string = current_game_list.get('emu_downloadpath_resolved')
		current_text = '[B]%(md)s[/B][CR][COLOR FF12A0C7]%(gln)s:  [/COLOR]%(emu_name)s[CR][COLOR FF12A0C7]%(cat)s:  [/COLOR]%(emu_category)s[CR][COLOR FF12A0C7]%(platform_string)s:  [/COLOR]%(emu_description)s[CR][COLOR FF12A0C7]%(author_string)s:  [/COLOR]%(emu_author)s[CR][CR][B]%(dp)s[/B][CR][COLOR FF12A0C7]%(source)s:  [/COLOR]%(download_source)s[CR][COLOR FF12A0C7]%(dl)s:  [/COLOR]%(download_path_string)s[CR][COLOR FF12A0C7]%(pdlc)s:  [/COLOR]%(emu_postdlaction)s[CR][CR][B]%(lp)s[/B][CR][COLOR FF12A0C7]%(lw)s:  [/COLOR]%(emu_launcher)s[CR]%(launch_command_string)s'%{'emu_name':current_game_list.get('emu_name'),'emu_category':current_game_list.get('emu_category'),'emu_description':current_game_list.get('emu_description'),'emu_author':current_game_list.get('emu_author'),'download_source':current_game_list.get('download_source'),'emu_postdlaction':current_emu_postdlaction,'emu_launcher':{'retroplayer':loc_str(30128),'external':loc_str(30003)}.get(current_game_list.get('emu_launcher')),'launch_command_string':launch_command_string,'download_path_string':download_path_string,'platform_string':loc_str(30416),'author_string':loc_str(30419),'gln':loc_str(30365),'cat':loc_str(30415),'dp':loc_str(30366),'source':loc_str(30368),'dl':loc_str(30367),'pdlc':loc_str(30369),'lp':loc_str(30370),'lw':loc_str(30371),'md':loc_str(30372)}
		set_mem_cache('TextViewer_Header',current_header)
		set_mem_cache('TextViewer_Text',current_text)
		plugin.redirect('/text_viewer')
	elif action_id == 'refresh_list':
		if iagl_addon.refresh_list(iagl_addon.game_lists.get_crc(game_list_id)):
			current_dialog = xbmcgui.Dialog()
			ok_ret = current_dialog.ok(loc_str(30202),loc_str(30306)%{'game_list_id': game_list_id})
			del current_dialog
			xbmc.executebuiltin('Container.Refresh')
	else:
		xbmc.log(msg='IAGL:  Unknown context action %(action_id)s'%{'action_id':action_id},level=xbmc.LOGERROR)

@plugin.route('/category_context_menu/action/<category_choice>/<game_list_id>/<action_id>')
def category_context_menu_action(category_choice,game_list_id,action_id):
	if action_id == 'add_to_favs':
		zachs_debug('ztest')
		zachs_debug(category_choice)
		zachs_debug(game_list_id)
		zachs_debug(action_id)
	else:
		xbmc.log(msg='IAGL:  Unknown category context action %(action_id)s'%{'action_id':action_id},level=xbmc.LOGERROR)

@plugin.route('/text_viewer')
def iagl_text_viewer():
	from resources.lib.main import iagl_dialog_text_viewer
	IAGL_text_Dialog = iagl_dialog_text_viewer('IAGL-textviewer.xml',iagl_addon.directory.get('addon').get('path'),'Default','1080i')
	IAGL_text_Dialog.doModal()
	del IAGL_text_Dialog

if __name__ == '__main__':
	plugin.run(sys.argv)
	del iagl_addon, iagl_download, iagl_post_process, iagl_launch, clear_mem_cache, get_mem_cache, set_mem_cache, get_next_page_listitem, get_setting_as, get_game_listitem, clean_image_entry, clean_trailer_entry, loc_str, check_if_file_exists, check_if_dir_exists, check_and_close_notification, get_history_listitem, update_listitem_title, zachs_debug #Delete all locally imported stuff to avoid memory leaks