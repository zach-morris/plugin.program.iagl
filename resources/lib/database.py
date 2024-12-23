import sqlite3, json
from datetime import datetime as dt
from contextlib import closing
from collections import namedtuple
from infotagger.listitem import ListItemInfoTag
from resources.lib import listitems
import xbmc

class database(object):
	def __init__(self,config=None,media_type=None):
		self.config=config
		self.listitems = listitems.listitems(config=self.config,media_type=media_type)
		self.factory_map = {'listitems':self.listitem_factory,'rows':sqlite3.Row,'dict':self.dict_factory,'namedtuple':self.namedtuple_factory}

	def get_query(self,query_type=None,**kwargs):
		query_out = None
		#To add:  kwarg args
		if isinstance(query_type,str) and query_type in self.config.database.get('query').keys():
			xbmc.log(msg='IAGL:  DB Query: {}'.format(query_type),level=xbmc.LOGDEBUG)
			xbmc.log(msg='IAGL:  DB Query kwargs: {}'.format(kwargs),level=xbmc.LOGDEBUG)
			query_out = self.config.database.get('query').get(query_type).format(**kwargs)
		else:
			xbmc.log(msg='IAGL:  Error in query requested: {} with kwargs: {}'.format(query_type,kwargs),level=xbmc.LOGERROR)
		return query_out

	def query_db(self,query=None,return_as='listitems',fetch_one=False):
		result = None
		if isinstance(query,str):
			if self.config.debug.get('print_query'):
				xbmc.log(msg='IAGL: SQL QUERY: {}'.format(query),level=xbmc.LOGDEBUG)
			try:
				with closing(sqlite3.connect(self.config.files.get('db'))) as conn:
					conn.row_factory = self.factory_map.get(return_as) or self.listitem_factory
					if fetch_one:
						result = conn.execute(query).fetchone()
					else:
						result = conn.execute(query).fetchall()
			except Exception as exc:
				xbmc.log(msg='IAGL:  Error in query: {}'.format(query),level=xbmc.LOGERROR)
				xbmc.log(msg='IAGL:  SQL Error: {}'.format(exc),level=xbmc.LOGERROR)
		return result

	def insert_row_db(self,statement=None,return_as='dict'):
		result = None
		if isinstance(statement,str):
			if self.config.debug.get('print_query'):
				xbmc.log(msg='IAGL: SQL Statement: {}'.format(statement),level=xbmc.LOGDEBUG)
			try:
				with closing(sqlite3.connect(self.config.files.get('db'))) as conn:
					with closing(conn.cursor()) as cursor:
						result = cursor.execute(statement)
			except Exception as exc:
				xbmc.log(msg='IAGL:  Error in statement: {}'.format(query),level=xbmc.LOGERROR)
				xbmc.log(msg='IAGL:  SQL Error: {}'.format(exc),level=xbmc.LOGERROR)
		return result

	def dict_factory(self,cursor,row):
		return dict(zip([column[0] for column in cursor.description],row))

	def namedtuple_factory(self,cursor,row):
		return namedtuple('Row',[column[0] for column in cursor.description])._make(row)

	def listitem_factory(self,cursor,row):
		return self.listitems.from_factory(dict(zip([column[0] for column in cursor.description],row)))

	def get_table_filter(self,game_list_id):
		filter_out = None
		if isinstance(game_list_id,str):
			result = self.query_db(query=self.config.database.get('query').get('get_game_table_filter').format(game_list_id),return_as='dict')
			if isinstance(result,list):
				filter_out = next(iter(result)).get('table_filter')
			else:
				xbmc.log(msg='IAGL:  Error in table filter for game_list_id {}: {}'.format(game_list_id,result),level=xbmc.LOGERROR)
		return filter_out

	def get_game_table_filter_from_choice(self,**kwargs):
		filter_out = None
		result = self.query_db(query=self.config.database.get('query').get('get_game_table_filter_from_choice').format(**kwargs),return_as='dict')
		if isinstance(result,list):
			filter_out = next(iter(result)).get('table_filter')
		else:
			xbmc.log(msg='IAGL:  Error in game table filter from choice: {}'.format(kwargs),level=xbmc.LOGERROR)
		return filter_out

	def clean_game_result(self,result_in):
		result_out = result_in
		if isinstance(result_out,dict):
			for process,keys in self.config.database.get('process').get('game').items():
				if process == 'from_json':
					for key in keys:
						if isinstance(result_out.get(key),str):
							result_out[key] = json.loads(result_out.get(key))
		return result_out

	def get_game_from_id(self,**kwargs):
		result = next(iter(self.query_db(query=self.config.database.get('query').get('get_game_from_id').format(**kwargs),return_as='dict')),None)
		if isinstance(result,dict):
			result = self.clean_game_result(result)
		return result

	def get_game_launch_info_from_id(self,**kwargs):
		result = self.query_db(query=self.config.database.get('query').get('game_launch_info_from_id').format(**kwargs),return_as='dict')
		if isinstance(result,list):
			result = [self.clean_game_result(r) for r in result]
		return result

	def get_game_list_launcher(self,**kwargs):
		l =  next(iter(self.query_db(query=self.config.database.get('query').get('get_game_list_launcher').format(**kwargs),return_as='dict')),None)
		if kwargs.get('user_only'):
			result = l.get('user_global_launcher')
		elif kwargs.get('default_only'):
			result = l.get('default_global_launcher')
		else:
			result = l.get('user_global_launcher') or l.get('default_global_launcher')
		return result

	def get_game_list_user_global_external_launch_command(self,**kwargs):
		l =  next(iter([x for x in self.query_db(query=self.config.database.get('query').get('get_game_list_user_global_external_launch_command').format(**kwargs),return_as='dict') if isinstance(x,dict)]),None)
		if kwargs.get('user_only'):
			result = l.get('user_global_external_launch_command')
		elif kwargs.get('default_only'):
			result = l.get('default_global_external_launch_command')
		else:
			result = l.get('user_global_external_launch_command') or l.get('default_global_external_launch_command')
		return result

	def get_favorite_group_names(self,**kwargs):
		return self.query_db(query=self.config.database.get('query').get('get_favorite_group_names').format(**kwargs),return_as='dict')

	def get_total_history(self):
		result = next(iter(self.query_db(query=self.config.database.get('query').get('get_total_history'),return_as='dict')),None)
		if isinstance(result,dict) and isinstance(result.get('total_history'),int):
			return result.get('total_history')
		else:
			return 0

	def add_favorite(self,game_id=None,fav_group=None,is_search_link=0,is_random_link=0,link_query=None):
		result = None
		try:
			with closing(sqlite3.connect(self.config.files.get('db'))) as conn:
				with closing(conn.cursor()) as cursor:
					# (uid,fav_group,is_search_link,is_random_link,link_name)
					cursor.execute(self.config.database.get('query').get('insert_favorite'),(game_id,fav_group,is_search_link,is_random_link,link_query))
					conn.commit()
					result = cursor.lastrowid
		except Exception as exc:
			xbmc.log(msg='IAGL:  SQL Error: {}'.format(exc),level=xbmc.LOGERROR)
		
		return result

	def transfer_game_list_user_settings(self,old_settings=None):
		result = None
		if isinstance(old_settings,dict):
			if self.config.debug.get('print_query'):
				xbmc.log(msg='IAGL: SQL STATEMENT: {}'.format(self.config.database.get('query').get('transfer_game_list_user_settings').format(**old_settings)),level=xbmc.LOGDEBUG)
			try:
				with closing(sqlite3.connect(self.config.files.get('db'))) as conn:
					with closing(conn.cursor()) as cursor:
						cursor.execute(self.config.database.get('query').get('transfer_game_list_user_settings').format(**old_settings))
						conn.commit()
						result = cursor.rowcount
			except Exception as exc:
				xbmc.log(msg='IAGL:  SQL Error: {}'.format(exc),level=xbmc.LOGERROR)
		return result

	def transfer_game_values(self,old_values=None):
		result = None
		if isinstance(old_values,dict):
			if self.config.debug.get('print_query'):
				xbmc.log(msg='IAGL: SQL STATEMENT: {}'.format(self.config.database.get('query').get('transfer_game_values').format(**old_values)),level=xbmc.LOGDEBUG)
			try:
				with closing(sqlite3.connect(self.config.files.get('db'))) as conn:
					with closing(conn.cursor()) as cursor:
						cursor.execute(self.config.database.get('query').get('transfer_game_values').format(**old_values))
						conn.commit()
						result = cursor.rowcount
			except Exception as exc:
				xbmc.log(msg='IAGL:  SQL Error: {}'.format(exc),level=xbmc.LOGERROR)
		return result

	def mark_game_as_favorite(self,game_id=None):
		result = None
		if isinstance(game_id,str):
			if self.config.debug.get('print_query'):
				xbmc.log(msg='IAGL: SQL STATEMENT: {}'.format(self.config.database.get('query').get('mark_game_as_favorite').format(game_id)),level=xbmc.LOGDEBUG)
			try:
				with closing(sqlite3.connect(self.config.files.get('db'))) as conn:
					with closing(conn.cursor()) as cursor:
						cursor.execute(self.config.database.get('query').get('mark_game_as_favorite').format(game_id))
						conn.commit()
						result = cursor.rowcount
			except Exception as exc:
				xbmc.log(msg='IAGL:  SQL Error: {}'.format(exc),level=xbmc.LOGERROR)
		return result

	def add_history(self,game_id=None,insert_time=None):
		result = None
		delete_first_result = self.delete_history_from_uid(game_id=game_id) #Remove the last time the game was played from history first
		if insert_time is None:
			insert_time = dt.now().timestamp()
		if self.config.debug.get('print_query'):
			xbmc.log(msg='IAGL: SQL STATEMENT: {}, ({}, {})'.format(self.config.database.get('query').get('insert_history'),game_id,insert_time),level=xbmc.LOGDEBUG)
		try:
			with closing(sqlite3.connect(self.config.files.get('db'))) as conn:
				with closing(conn.cursor()) as cursor:
					cursor.execute(self.config.database.get('query').get('insert_history'),(game_id,insert_time,))
					conn.commit()
					result = cursor.lastrowid
		except Exception as exc:
			xbmc.log(msg='IAGL:  SQL Error: {}'.format(exc),level=xbmc.LOGERROR)
		return result

	def delete_history_from_uid(self,game_id=None):
		result = None
		if self.config.debug.get('print_query'):
			xbmc.log(msg='IAGL: SQL STATEMENT: {}'.format(self.config.database.get('query').get('delete_history_from_uid').format(game_id)),level=xbmc.LOGDEBUG)
		try:
			with closing(sqlite3.connect(self.config.files.get('db'))) as conn:
				with closing(conn.cursor()) as cursor:
					cursor.execute(self.config.database.get('query').get('delete_history_from_uid').format(game_id))
					conn.commit()
					result = cursor.rowcount
		except Exception as exc:
			xbmc.log(msg='IAGL:  SQL Error: {}'.format(exc),level=xbmc.LOGERROR)
		return result

	def delete_favorite_from_uid(self,game_id=None):
		result = None
		if self.config.debug.get('print_query'):
			xbmc.log(msg='IAGL: SQL STATEMENT: {}'.format(self.config.database.get('query').get('delete_favorite_from_uid').format(game_id)),level=xbmc.LOGDEBUG)
		try:
			with closing(sqlite3.connect(self.config.files.get('db'))) as conn:
				with closing(conn.cursor()) as cursor:
					cursor.execute(self.config.database.get('query').get('delete_favorite_from_uid').format(game_id))
					conn.commit()
					result = cursor.rowcount
		except Exception as exc:
			xbmc.log(msg='IAGL:  SQL Error: {}'.format(exc),level=xbmc.LOGERROR)
		return result

	def unmark_game_as_favorite(self,game_id=None):
		result = None
		if isinstance(game_id,str):
			if self.config.debug.get('print_query'):
				xbmc.log(msg='IAGL: SQL STATEMENT: {}'.format(self.config.database.get('query').get('unmark_game_as_favorite').format(game_id)),level=xbmc.LOGDEBUG)
			try:
				with closing(sqlite3.connect(self.config.files.get('db'))) as conn:
					with closing(conn.cursor()) as cursor:
						cursor.execute(self.config.database.get('query').get('unmark_game_as_favorite').format(game_id))
						conn.commit()
						result = cursor.rowcount
			except Exception as exc:
				xbmc.log(msg='IAGL:  SQL Error: {}'.format(exc),level=xbmc.LOGERROR)
		return result

	def delete_favorite_from_link(self,query_in=None):
		result = None
		if self.config.debug.get('print_query'):
			xbmc.log(msg='IAGL: SQL STATEMENT: {}'.format(self.config.database.get('query').get('delete_favorite_from_link').format(query_in)),level=xbmc.LOGDEBUG)
		try:
			with closing(sqlite3.connect(self.config.files.get('db'))) as conn:
				with closing(conn.cursor()) as cursor:
					cursor.execute(self.config.database.get('query').get('delete_favorite_from_link').format(query_in))
					conn.commit()
					result = cursor.rowcount
		except Exception as exc:
			xbmc.log(msg='IAGL:  SQL Error: {}'.format(exc),level=xbmc.LOGERROR)
		return result

	def limit_history(self,**kwargs):
		result = None
		if self.config.debug.get('print_query'):
			xbmc.log(msg='IAGL: SQL STATEMENT: {}'.format(self.config.database.get('query').get('limit_history').format(**kwargs)),level=xbmc.LOGDEBUG)
		try:
			with closing(sqlite3.connect(self.config.files.get('db'))) as conn:
				with closing(conn.cursor()) as cursor:
					cursor.execute(self.config.database.get('query').get('limit_history').format(**kwargs))
					conn.commit()
			result = True
		except Exception as exc:
			result = False
			xbmc.log(msg='IAGL:  SQL Error: {}'.format(exc),level=xbmc.LOGERROR)
		return result

	def update_pc_and_cp(self,game_id=None,time_format='%Y-%m-%d %H:%M:%S'):
		result = None
		if isinstance(game_id,str):
			current_pc_lp = next(iter(self.query_db(query=self.get_query('get_playcount_and_lastplayed',game_id=game_id),return_as='dict')),None)
			next_pc = 1
			if isinstance(current_pc_lp,dict):
				if isinstance(current_pc_lp.get('playcount'),int):
					next_pc = current_pc_lp.get('playcount')+1
			if self.config.debug.get('print_query'):
				xbmc.log(msg='IAGL: SQL STATEMENT: {}'.format(self.config.database.get('query').get('update_playcount_and_lastplayed').format(next_pc,dt.now().strftime(time_format),game_id)),level=xbmc.LOGDEBUG)
			try:
				with closing(sqlite3.connect(self.config.files.get('db'))) as conn:
					with closing(conn.cursor()) as cursor:
						cursor.execute(self.config.database.get('query').get('update_playcount_and_lastplayed').format(next_pc,dt.now().strftime(time_format),game_id))
						conn.commit()
						result = cursor.rowcount
			except Exception as exc:
				xbmc.log(msg='IAGL:  SQL Error: {}'.format(exc),level=xbmc.LOGERROR)
		return result

	def update_game_list_user_parameter(self,**kwargs):
		result = None
		if self.config.debug.get('print_query'):
			xbmc.log(msg='IAGL: SQL STATEMENT: {}'.format(self.config.database.get('query').get('update_game_list_user_parameter').format(**kwargs)),level=xbmc.LOGDEBUG)
		try:
			with closing(sqlite3.connect(self.config.files.get('db'))) as conn:
				with closing(conn.cursor()) as cursor:
					cursor.execute(self.config.database.get('query').get('update_game_list_user_parameter').format(**kwargs))
					conn.commit()
					result = cursor.rowcount
		except Exception as exc:
			xbmc.log(msg='IAGL:  SQL Error: {}'.format(exc),level=xbmc.LOGERROR)
		return result

	def update_all_game_list_user_parameters(self,**kwargs):
		result = None
		if self.config.debug.get('print_query'):
			xbmc.log(msg='IAGL: SQL STATEMENT: {}'.format(self.config.database.get('query').get('update_all_game_list_user_parameters').format(**kwargs)),level=xbmc.LOGDEBUG)
		try:
			with closing(sqlite3.connect(self.config.files.get('db'))) as conn:
				with closing(conn.cursor()) as cursor:
					cursor.execute(self.config.database.get('query').get('update_all_game_list_user_parameters').format(**kwargs))
					conn.commit()
					result = cursor.rowcount
		except Exception as exc:
			xbmc.log(msg='IAGL:  SQL Error: {}'.format(exc),level=xbmc.LOGERROR)
		return result

	def update_some_game_list_user_parameters(self,**kwargs):
		result = None
		if isinstance(kwargs.get('game_lists'),list):
			kwargs['game_lists'] = ','.join(['"{}"'.format(x) for x in kwargs.get('game_lists')])  #Format game_lists for sql
		if self.config.debug.get('print_query'):
			xbmc.log(msg='IAGL: SQL STATEMENT: {}'.format(self.config.database.get('query').get('update_some_game_list_user_parameters').format(**kwargs)),level=xbmc.LOGDEBUG)
		try:
			with closing(sqlite3.connect(self.config.files.get('db'))) as conn:
				with closing(conn.cursor()) as cursor:
					cursor.execute(self.config.database.get('query').get('update_some_game_list_user_parameters').format(**kwargs))
					conn.commit()
					result = cursor.rowcount
		except Exception as exc:
			xbmc.log(msg='IAGL:  SQL Error: {}'.format(exc),level=xbmc.LOGERROR)
		return result

	def reset_game_list_user_parameter(self,**kwargs):
		result = None
		if self.config.debug.get('print_query'):
			xbmc.log(msg='IAGL: SQL STATEMENT: {}'.format(self.config.database.get('query').get('reset_game_list_user_parameter').format(**kwargs)),level=xbmc.LOGDEBUG)
		try:
			with closing(sqlite3.connect(self.config.files.get('db'))) as conn:
				with closing(conn.cursor()) as cursor:
					cursor.execute(self.config.database.get('query').get('reset_game_list_user_parameter').format(**kwargs))
					conn.commit()
					result = cursor.rowcount
		except Exception as exc:
			xbmc.log(msg='IAGL:  SQL Error: {}'.format(exc),level=xbmc.LOGERROR)
		return result

	def reset_all_game_list_user_parameters(self,**kwargs):
		result = None
		if self.config.debug.get('print_query'):
			xbmc.log(msg='IAGL: SQL STATEMENT: {}'.format(self.config.database.get('query').get('reset_all_game_list_user_parameters').format(**kwargs)),level=xbmc.LOGDEBUG)
		try:
			with closing(sqlite3.connect(self.config.files.get('db'))) as conn:
				with closing(conn.cursor()) as cursor:
					cursor.execute(self.config.database.get('query').get('reset_all_game_list_user_parameters').format(**kwargs))
					conn.commit()
					result = cursor.rowcount
		except Exception as exc:
			xbmc.log(msg='IAGL:  SQL Error: {}'.format(exc),level=xbmc.LOGERROR)
		return result

	def unhide_game_lists(self,lists_in=None):
		result = None
		if isinstance(lists_in,list):
			q = 'label IN ({})'.format(','.join(['"{}"'.format(x) for x in lists_in if isinstance(x,str)]))
			if self.config.debug.get('print_query'):
				xbmc.log(msg='IAGL: SQL STATEMENT: {}'.format(self.config.database.get('query').get('unhide_game_lists').format(q)),level=xbmc.LOGDEBUG)
			try:
				with closing(sqlite3.connect(self.config.files.get('db'))) as conn:
					with closing(conn.cursor()) as cursor:
						cursor.execute(self.config.database.get('query').get('unhide_game_lists').format(q))
						conn.commit()
						result = cursor.rowcount
			except Exception as exc:
				xbmc.log(msg='IAGL:  SQL Error: {}'.format(exc),level=xbmc.LOGERROR)
		return result
