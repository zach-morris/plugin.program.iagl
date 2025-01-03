from infotagger.listitem import ListItemInfoTag
import xbmcgui, xbmc, json

class listitems(object):
	def __init__(self,config=None,media_type=None):
		self.config=config
		liit = ListItemInfoTag(xbmcgui.ListItem())._tag_attr
		self.string_to_list_keys = [k for k in liit if liit.get(k).get('classinfo')==(list, tuple)]  #These keys need to be converted to a list.  Currently ['genre', 'country', 'studio', 'showlink', 'director', 'writer', 'tag', 'credits', 'artist']
		self.json_decode_keys = set([x for x in self.string_to_list_keys if x not in self.config.listitem.get('non_string_to_list_keys')])  #These keys are stored in the db as json serializable
		if isinstance(media_type,str):
			self.media_type = media_type
		else:
			self.media_type = self.config.media.get('default_type')

	def clean_field(self,key_in,value_in):
		value_out = value_in
		if key_in in self.json_decode_keys:
			try:
				value_out = json.loads(value_in)
			except:
				xbmc.log(msg='IAGL: Values for {} were not json serializable, falling back to string split'.format(key_in),level=xbmc.LOGDEBUG)
				value_out = value_in.split(',')
		# elif key_in in self.config.listitem.get('non_string_to_list_keys'):
		# 	value_out = [value_in]
		else:
			pass
		return value_out

	def from_factory(self,row):
		if isinstance(row.get('localization'),int): #If the localized string ID was found, use it
			li = xbmcgui.ListItem(label=self.config.addon.get('addon_handle').getLocalizedString(row.get('localization')),label2=row.get('label2'),offscreen=True)
		else: #Use the default (english) label
			li = xbmcgui.ListItem(label=row.get('label'),label2=row.get('label2'),offscreen=True)
		li.setArt({k:v for k,v in row.items() if k in self.config.listitem.get('art_keys')})
		li.setProperties({k:v for k,v in row.items() if k in self.config.listitem.get('property_keys')})
		li.setInfo(self.media_type,{k:v for k,v in row.items() if k in self.config.listitem.get('info_keys')}) #No infotagger for these keys currently
		info_tag = ListItemInfoTag(li,self.media_type)
		info_tag.set_info({k:self.clean_field(key_in=k,value_in=v) for k,v in row.items() if k in info_tag._tag_attr and isinstance(v,str)})
		if self.config.debug.get('factory_debug'):
			xbmc.log(msg='IAGL: Listitem Factory Dict: {}'.format(row),level=xbmc.LOGDEBUG)
			xbmc.log(msg='Art Tags: {}'.format(','.join([k for k,v in row.items() if k in self.config.listitem.get('art_keys')])),level=xbmc.LOGDEBUG)
			xbmc.log(msg='Property Tags: {}'.format(','.join([k for k,v in row.items() if k in self.config.listitem.get('property_keys')])),level=xbmc.LOGDEBUG)
			xbmc.log(msg='Info Tags: {}'.format(','.join([k for k,v in row.items() if k in info_tag._tag_attr])),level=xbmc.LOGDEBUG)
		return li,row.get('next_path')
