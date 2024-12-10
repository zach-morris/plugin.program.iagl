import xbmc,xbmcgui,xbmcaddon,xbmcvfs,json,os
from pathlib import Path
from urllib.parse import urlencode

class netplay(object):
	def __init__(self,config=None,netplay_type=None,nickname=None,discord_id=None,ip_address=None,port=None,use_relay=None,num_frames=None):
		self.config=config
		self.netplay_type = netplay_type
		self.nickname = nickname
		self.discord_id = discord_id
		self.ip_address = ip_address
		self.port = port
		self.use_relay = use_relay
		self.num_frames = num_frames
		self.netplay_xx_cmd = ' XXNETPLAY_COMMANDXX'

	def set_netplay_type(self,type_in=None):
		self.netplay_type = type_in

	def set_nickname(self,nickname_in=None):
		if isinstance(nickname_in,str):
			self.nickname=nickname_in

	def set_discord_id(self,discord_id_in=None):
		if isinstance(discord_id_in,str):
			self.discord_id=discord_id_in

	def set_ip_address(self,ip_address_in=None):
		if isinstance(ip_address_in,str):
			self.ip_address=ip_address_in

	def set_port(self,port_in=None):
		if isinstance(port_in,str):
			self.port=port_in

	def set_use_relay(self,use_relay_in=None):
		if isinstance(use_relay_in,bool):
			self.use_relay=use_relay_in

	def set_num_frames(self,num_frames_in=None):
		if isinstance(num_frames_in,int):
			self.num_frames=num_frames_in

	def insert_netplay_command(self,command_in=None):
		current_command = command_in
		if isinstance(current_command,str):
			current_command = current_command.replace(self.netplay_xx_cmd,'')  #Stubbing out netplay for now
			xbmc.log(msg='IAGL:  Netplay command set to NONE',level=xbmc.LOGDEBUG)
		return current_command

		return current_command

