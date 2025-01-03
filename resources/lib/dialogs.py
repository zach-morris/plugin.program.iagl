import xbmcgui,xbmc,xbmcaddon

class dialogs(object):
	def __init__(self,config=None):
		self.config=config

	def get_tou(self):
		return self.TOU_dialog('IAGL-TOU.xml',str(self.config.paths.get('addon')),'Default','1080i',config=self.config)

	def get_donate(self):
		return self.donate_dialog('donate.xml',str(self.config.paths.get('addon')),'Default','1080i',config=self.config)

	def get_discord_invite(self):
		return self.invite_dialog('IAGL-invite.xml',str(self.config.paths.get('addon')),'Default','1080i',config=self.config)

	class TOU_dialog(xbmcgui.WindowXMLDialog):
		def __init__(self,*args,**kwargs):
			xbmc.log(msg='IAGL:  TOU Dialog Initialized', level=xbmc.LOGDEBUG)
			self.config = kwargs.get('config')
			self.dialog_config = self.config.dialogs.get('tou')
			self.buttons = dict()

		def onInit(self):
			for kk in self.dialog_config.get('buttons').keys():
				self.buttons[kk] = self.getControl(self.dialog_config.get('buttons').get(kk))

		def onAction(self,action):  #Do not agree
			if action in self.dialog_config.get('actions').get('do_not_agree'): 
				self.close()

		def onClick(self,id_in):  #Agree and close
			if id_in == self.dialog_config.get('buttons').get('do_not_agree'):
				# xbmcaddon.Addon(id=ADDON_NAME).setSetting(id='iagl_hidden_bool_tou',value='true')
				xbmc.log(msg='IAGL:  Terms of Use Do Not Agree', level=xbmc.LOGDEBUG)
				self.close()

			if id_in == self.dialog_config.get('buttons').get('agree'):
				xbmcaddon.Addon(id=self.config.addon.get('addon_name')).setSetting(id='tou',value='true')
				xbmc.log(msg='IAGL:  Terms of Use Agree', level=xbmc.LOGDEBUG)
				self.close()

	class donate_dialog(xbmcgui.WindowXMLDialog):
		def __init__(self,*args,**kwargs):
			xbmc.log(msg='IAGL:  Donate Dialog Initialized', level=xbmc.LOGDEBUG)
			self.config = kwargs.get('config')
			self.dialog_config = self.config.dialogs.get('donate')
			self.buttons = dict()

		def onInit(self):
			for kk in self.dialog_config.get('buttons').keys():
				self.buttons[kk] = self.getControl(self.dialog_config.get('buttons').get(kk))

		def onAction(self,action):  #OK
			if action in self.dialog_config.get('actions').get('ok'): 
				self.close()

		def onClick(self,id_in):  #OK
			if id_in == self.dialog_config.get('buttons').get('ok'):
				self.close()

	class invite_dialog(xbmcgui.WindowXMLDialog):
		def __init__(self,*args,**kwargs):
			xbmc.log(msg='IAGL:  Discord Invite Dialog Initialized', level=xbmc.LOGDEBUG)
			self.config = kwargs.get('config')
			self.dialog_config = self.config.dialogs.get('discord_invite')
			self.buttons = dict()

		def onInit(self):
			for kk in self.dialog_config.get('buttons').keys():
				self.buttons[kk] = self.getControl(self.dialog_config.get('buttons').get(kk))

		def onAction(self,action):  #OK
			if action in self.dialog_config.get('actions').get('ok'): 
				self.close()

		def onClick(self,id_in):  #OK
			if id_in == self.dialog_config.get('buttons').get('ok'):
				self.close()