from infotagger.listitem import ListItemInfoTag
import xbmcgui, xbmc, json

class listitems(object):
	def __init__(self,config=None,media_type=None):
		self.config=config
		liit = ListItemInfoTag(xbmcgui.ListItem())._tag_attr
		self.string_to_list_keys = [k for k in liit.keys() if liit.get(k).get('classinfo')==(list, tuple)]  #Currently ['genre', 'country', 'studio', 'showlink', 'director', 'writer', 'tag', 'credits', 'artist']
		if isinstance(media_type,str):
			self.media_type = media_type
		else:
			self.media_type = self.config.media.get('default_type')

	def clean_field(self,value_in,key_in):
		value_out = value_in
		if isinstance(value_in,str) and key_in in self.string_to_list_keys:
			if key_in not in self.config.listitem.get('non_string_to_list_keys'): #Removed 'studio' via config
				try:
					value_out = json.loads(value_in)
				except:
					xbmc.log(msg='IAGL: Values for {} were not json serializable, falling back to string split'.format(key_in),level=xbmc.LOGDEBUG)
					value_out = [x.strip() for x in value_in.split(',') if isinstance(x,str)]
			else:
				value_out = [x.strip() for x in value_in.split(',') if isinstance(x,str)]
		return value_out

	def from_factory(self,fields,row):
		if fields.get('localization') and isinstance(row[fields.get('localization')],int): #If the localized string was found, use it
			li = xbmcgui.ListItem(label=self.config.addon.get('addon_handle').getLocalizedString(row[fields.get('localization')]),offscreen=True)
		else: #Use the default (english) label
			li = xbmcgui.ListItem(label=row[fields.get('label')],offscreen=True)
		li.setArt({k:row[fields.get(k)] for k in fields.keys() if k in self.config.listitem.get('art_keys')})
		li.setProperties({k:row[fields.get(k)] for k in fields.keys() if k in self.config.listitem.get('property_keys')})
		info_tag = ListItemInfoTag(li,self.media_type)
		info_tag.set_info({k:self.clean_field(value_in=row[fields.get(k)],key_in=k) for k in fields.keys() if k in info_tag._tag_attr.keys()})
		li.setInfo(self.media_type,{k:row[fields.get(k)] for k in fields.keys() if k in self.config.listitem.get('info_keys')}) #No infotagger for these keys currently
		if self.config.debug.get('factory_debug'):
			xbmc.log(msg='IAGL: Listitem Factory Dict: {}'.format({k:row[fields.get(k)] for k in fields.keys()}),level=xbmc.LOGDEBUG)
			xbmc.log(msg='Art Tags: {}'.format(','.join([k for k in fields.keys() if k in self.config.listitem.get('art_keys')])),level=xbmc.LOGDEBUG)
			xbmc.log(msg='Property Tags: {}'.format(','.join([k for k in fields.keys() if k in self.config.listitem.get('property_keys')])),level=xbmc.LOGDEBUG)
			xbmc.log(msg='Info Tags: {}'.format(','.join([k for k in fields.keys() if k in info_tag._tag_attr.keys()])),level=xbmc.LOGDEBUG)
		return li,row[fields.get('next_path')]