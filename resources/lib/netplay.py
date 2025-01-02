import xbmc,xbmcgui,xbmcaddon,xbmcvfs,json,os
from pathlib import Path
from urllib.parse import urlencode
import requests, time, json
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

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
		self.lobby = None
		self.discord_channel_posts = None
		self.netplay_xx_cmd = ' XXNETPLAY_COMMANDXX'
		self.d_t_f = b'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
		self.d_t_t = b'nopqrstuvwxyzabcdefghijklmNOPQRSTUVWXYZABCDEFGHIJKLM'
		self.session = requests.Session()
		self.retries = requests.adapters.Retry(total=5,backoff_factor=0.1,status_forcelist=[500,502,503,504,499])
		self.session.mount("http://",requests.adapters.HTTPAdapter(max_retries=self.retries))
		self.session.mount("https://",requests.adapters.HTTPAdapter(max_retries=self.retries))

	def t_str(self,string_in=None):
		if isinstance(string_in,str):
			return string_in.translate(bytes.maketrans(self.d_t_f,self.d_t_t))
		else:
			return None

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

	def set_lobby(self,lobby_in=None):
		if isinstance(lobby_in,list):
			self.lobby=lobby_in

	def set_discord_channel_posts(self,channel_in=None):
		if isinstance(channel_in,list):
			self.discord_channel_posts=channel_in

	def query_ra_lobby(self):
		result = None
		try:
			with self.session.get(self.config.netplay.get('lobby_url'),timeout=self.config.netplay.get('netplay_timeout'),allow_redirects=False) as r:
				r.raise_for_status()
				if r.ok and isinstance(r.text,str) and len(r.text)>0:
					result = json.loads(r.text)
					if isinstance(result,list):
						result = [x.get('fields') for x in result]
					self.set_lobby(lobby_in=result)
				xbmc.log(msg='IAGL:  Retroarch netplay lobby returned {} sessions'.format(len(result)),level=xbmc.LOGDEBUG)
		except Exception as exc:
			xbmc.log(msg='IAGL:  Retroarch netplay lobby exception: {}'.format(exc),level=xbmc.LOGERROR)
		return result

	def query_discord_user(self,id_in=None):
		result = None
		if isinstance(id_in,str) and len(id_in)>0 and id_in.isdigit():
			try:
				with self.session.get(self.config.netplay.get('discord_user').format(id_in),timeout=self.config.netplay.get('netplay_timeout'),allow_redirects=False,headers={'Authorization':self.t_str(self.config.netplay.get('header_query')),'content-type':'application/json'}) as r:
					r.raise_for_status()
					if r.ok and isinstance(r.text,str) and len(r.text)>0:
						result = json.loads(r.text)
						self.set_discord_channel_posts(channel_in=result)
					xbmc.log(msg='IAGL:  Discord returned user for id {}'.format(id_in),level=xbmc.LOGDEBUG)
			except Exception as exc:
				xbmc.log(msg='IAGL:  Discord user query exception: {}'.format(exc),level=xbmc.LOGERROR)
		else:
			xbmc.log(msg='IAGL:  Invalid Discord ID provided: {}'.format(id_in),level=xbmc.LOGERROR)
		return result

	def query_discord_channel(self):
		result = None
		try:
			with self.session.get(self.config.netplay.get('discord_channel'),timeout=self.config.netplay.get('netplay_timeout'),allow_redirects=False,headers={'Authorization':self.t_str(self.config.netplay.get('header_query')),'content-type':'application/json'}) as r:
				r.raise_for_status()
				if r.ok and isinstance(r.text,str) and len(r.text)>0:
					result = json.loads(r.text)
					self.set_discord_channel_posts(channel_in=result)
				xbmc.log(msg='IAGL:  Discord returned {} posts'.format(len(result)),level=xbmc.LOGDEBUG)
		except Exception as exc:
			xbmc.log(msg='IAGL:  Discord channel exception: {}'.format(exc),level=xbmc.LOGERROR)
		return result

	def discord_announce(self,game=None,discord_at=None,discord_user_id=None,discord_username=None,timestamp=None):
		result = False
		game['discord_at'] = discord_at
		game['discord_user_id'] = discord_user_id
		game['discord_username'] = discord_username
		game['discord_timestamp'] = timestamp
		game['image_url'] = next(iter([x for x in [game.get('art_box'),game.get('art_title'),game.get('art_snapshot'),game.get('art_logo'),game.get('art_game_list')] if isinstance(x,str)]),self.config.netplay.get('default_art'))  #Choose art for the post
		try:
			announce_json = self.config.netplay.get('discord_announce_json').format(**game)
			with self.session as s:
				p = s.post(self.config.netplay.get('channel_hook').format(self.t_str(self.config.netplay.get('header_post'))),timeout=self.config.netplay.get('netplay_timeout'),json=json.loads(announce_json))
				if p.ok:
					result = True
					xbmc.log(msg='IAGL:  Discord netplay announced for user {}'.format(game.get('discord_username')),level=xbmc.LOGDEBUG)
				else:
					xbmc.log(msg='IAGL:  Discord Announce failure: {}'.format(p),level=xbmc.LOGERROR)
		except Exception as exc:	
			result = False
			xbmc.log(msg='IAGL:  Discord Announce exception: {}'.format(exc),level=xbmc.LOGERROR)
		return result

