# -*- coding: utf-8 -*-

from __future__ import print_function
import json
import re
import requests
import time
import threading
import os


import sys

from requests.api import delete
import bencode
import hashlib
import base64
import urllib
import tools
try:
    from urllib.parse import unquote, urlparse
except ImportError:
    from urllib2 import unquote
    from urlparse import urlparse

#from resources.lib.common import tools


class RealDebrid:
    def __init__(self):
        self.ClientID = tools.getSetting('rd.client_id')
        if self.ClientID == '':
            self.ClientID = 'X245A4XAIBGVM'
        self.OauthUrl = 'https://api.real-debrid.com/oauth/v2/'
        self.DeviceCodeUrl = "device/code?%s"
        self.DeviceCredUrl = "device/credentials?%s"
        self.TokenUrl = "token"
        self.token = tools.getSetting('rd.auth')
        self.refresh = tools.getSetting('rd.refresh')
        self.DeviceCode = ''
        self.ClientSecret = tools.getSetting('rd.secret')
        self.OauthTimeout = 0
        self.OauthTimeStep = 0
        self.BaseUrl = "https://api.real-debrid.com/rest/1.0/"
        self.cache_check_results = {}
        self._asked = tools.getSetting("rd.asked")

    @property
    def asked(self):
        return self._asked

    @asked.setter
    def asked(self, var):
        self._asked = var
        tools.setSetting("rd.asked", var)

    def auth_loop(self):
        if tools.progressDialog.iscanceled():
            tools.progressDialog.close()
            return
        time.sleep(self.OauthTimeStep)
        url = "client_id=%s&code=%s" % (self.ClientID, self.DeviceCode)
        url = self.OauthUrl + self.DeviceCredUrl % url
        response = json.loads(requests.get(url).text)
        if 'error' in response:
            return
        else:
            try:
                tools.progressDialog.close()
                tools.setSetting('rd.client_id', response['client_id'])
                tools.setSetting('rd.secret', response['client_secret'])
                self.ClientSecret = response['client_secret']
                self.ClientID = response['client_id']
            except Exception as e:
                tools.showDialog.ok(tools.addonName, "Authorisation cancelled")
            return

    def auth(self):
        self.ClientSecret = ''
        self.ClientID = 'X245A4XAIBGVM'
        url = ("client_id=%s&new_credentials=yes" % self.ClientID)
        url = self.OauthUrl + self.DeviceCodeUrl % url
        response = json.loads(requests.get(url).text)
        tools.copy2clip(response['user_code'])
        tools.progressDialog.create("Authorise with Real Debrid")
        tools.progressDialog.update(-1, "Open {} in your browser".format(tools.colorString(
            'https://real-debrid.com/device')),
                                    "enter the code {}".format(tools.colorString(
                                        response['user_code'])),
                                    'This code has been copied to your clipboard')
        self.OauthTimeout = int(response['expires_in'])
        self.OauthTimeStep = int(response['interval'])
        self.DeviceCode = response['device_code']

        while self.ClientSecret == '':
            self.auth_loop()

        self.token_request()

        user_information = self.get_url('user')
        if user_information['type'] != 'premium':
            tools.showDialog.ok(tools.addonName, "You don't have a premium account")

    def token_request(self):
        import time
        if self.ClientSecret is '':
            return

        postData = {'client_id': self.ClientID,
                    'client_secret': self.ClientSecret,
                    'code': self.DeviceCode,
                    'grant_type': 'http://oauth.net/grant_type/device/1.0'}

        url = self.OauthUrl + self.TokenUrl
        response = requests.post(url, data=postData).text
        response = json.loads(response)
        tools.setSetting('rd.auth', response['access_token'])
        tools.setSetting('rd.refresh', response['refresh_token'])
        self.token = response['access_token']
        self.refresh = response['refresh_token']
        tools.setSetting('rd.expiry', str(time.time() + int(response['expires_in'])))
        username = self.get_url('user')['username']
        tools.setSetting('rd.username', username)
        tools.showDialog.ok(tools.addonName, 'Real Debrid Authorised')
        tools.log('Authorised Real Debrid successfully', 'info')

    def refreshToken(self):
        import time
        postData = {'grant_type': 'http://oauth.net/grant_type/device/1.0',
                    'code': self.refresh,
                    'client_secret': self.ClientSecret,
                    'client_id': self.ClientID
                    }
        url = self.OauthUrl + 'token'
        response = requests.post(url, data=postData)
        response = json.loads(response.text)
        if 'access_token' in response:
            self.token = response['access_token']
        else:
            pass
        if 'refresh_token' in response:
            self.refresh = response['refresh_token']
        tools.setSetting('rd.auth', self.token)
        tools.setSetting('rd.refresh', self.refresh)
        tools.setSetting('rd.expiry', str(time.time() + int(response['expires_in'])))
        tools.log('Real Debrid Token Refreshed')
        ###############################################
        # To be FINISHED FINISH ME
        ###############################################

    def post_url(self, url, postData, fail_check=False):
        original_url = url
        url = self.BaseUrl + url
        if self.token == '':
            return None
        if not fail_check:
            if '?' not in url:
                url += "?auth_token=%s" % self.token
            else:
                url += "&auth_token=%s" % self.token

        response = requests.post(url, data=postData, timeout=5).text
        if 'bad_token' in response or 'Bad Request' in response:
            if not fail_check:
                self.refreshToken()
                response = self.post_url(original_url, postData, fail_check=True)
        try:
            return json.loads(response)
        except:
            return response

    def get_url(self, url, fail_check=False):
        original_url = url
        url = self.BaseUrl + url
        if self.token == '':
            tools.log('No Real Debrid Token Found')
            return None
        if '?' not in url:
            url += "?auth_token=%s" % self.token
        else:
            url += "&auth_token=%s" % self.token

        response = requests.get(url, timeout=5).text

        if 'bad_token' in response or 'Bad Request' in response:
            tools.log('Refreshing RD Token')
            if not fail_check:
                self.refreshToken()
                response = self.get_url(original_url, fail_check=True)
        try:
            return json.loads(response)
        except:
            return response # TODO: this just creates other exceptions later on. should be better

    def checkHash(self, hashList):

        if isinstance(hashList, list):
            cache_result = {}
            hashList = [hashList[x:x+100] for x in range(0, len(hashList), 100)]
            threads = []
            for section in hashList:
                threads.append(threading.Thread(target=self._check_hash_thread, args=(section,)))
            for i in threads:
                i.start()
            for i in threads:
                i.join()
            return self.cache_check_results
        else:
            hashString = "/" + hashList
            response = self.get_url("torrents/instantAvailability" + hashString)
            if response.get('error_code') == 3:
                #torrent has never been uploaded
                return {}
            else:
                return response


    def _check_hash_thread(self, hashes):
        hashString = '/' + '/'.join(hashes)
        response = self.get_url("torrents/instantAvailability" + hashString)
        self.cache_check_results.update(response)

    def addMagnet(self, magnet):
        postData = {'magnet': magnet}
        url = 'torrents/addMagnet'
        response = self.post_url(url, postData)
        return response

    def list_torrents(self):
        url = "torrents"
        response = self.get_url(url)
        return response

    def torrentInfo(self, id):
        url = "torrents/info/%s" % id
        return self.get_url(url)

    def torrentSelect(self, torrentID, fileID):
        url = "torrents/selectFiles/%s" % torrentID
        postData = {'files': fileID}
        return self.post_url(url, postData)

    def resolve_hoster(self, link):
        url = 'unrestrict/link'
        postData = {'link': link}
        response = self.post_url(url, postData)
        try:
            return response['download']
        except:
            return None

    def deleteTorrent(self, id):
        if self.token == '':
            return None
        url = "torrents/delete/%s&auth_token=%s" % (id, self.token)
        requests.delete(self.BaseUrl + url, timeout=5)


    def make_magnet_from_torrent(self, torrent) :
        try:
            metadata = bencode.bdecode(torrent)
        except bencode.BTFailure:
            # TODO: log error
            return None, None
        subj = metadata[b'info']
        hashcontents = bencode.bencode(subj)
        digest = hashlib.sha1(hashcontents).digest()
        b32hash = base64.b32encode(digest).decode() # can also use this hash.
        hash = hashlib.sha1(hashcontents).hexdigest()
        link = 'magnet:?'\
                + 'xt=urn:btih:' + hash\
                + '&dn=' + metadata[b'info'][b'name'].decode()\
                + '&tr=' + metadata[b'announce'].decode()
        if b'length' in metadata[b'info']:
            link+= '&xl=' + str(metadata[b'info'][b'length'])

        files = {}
        for i, file in enumerate(metadata[b'info'][b'files'], start=1):
            file_name = file[b'path'][-1].decode('utf-8')
            files[file_name] = dict(id=i)
        return link,files


    def instantAvailabilityFiles(self, hash):
        hashCheck = self.checkHash(hash)
        # go through contents and find our file 
        files = {}
        for storage_variant in hashCheck.get(hash,{}).get('rd',[]):
            for key, value in storage_variant.items():
                file_name = storage_variant[key]['filename']
                files[file_name] = key
        return files

    def torrentInfoFiles(self, id):
        link = self.torrentInfo(id)
        files = {}
        links = link['links']

        # TODO: IA torrents have a bug they are truncacted - https://github.com/internetarchive/heritrix3/issues/321

        file_index = 0
        for i in link['files']:
            if i['selected'] == 1:
                # we need to keep track of the index of selected files to get the right url
                if links:
                    i['link'] = links[file_index] if len(links) else None
                file_index += 1
            file_name = i['path'].split('/')[-1]
            files[file_name] = i
        
        return files

    def downloadingFiles(self, hash, file_name):
        # find the one closest to finishing with file_name selected
        for torrent in sorted(self.list_torrents(), key=lambda t: int(t['progress']), reverse=True):
            if torrent['hash'] == hash and torrent['status'] != 'error':
                if torrent['filename'] == file_name: #RD does this when its a single file from the torrent
                    # We will assume it was the only one selected and it will be the first link
                    return torrent, {file_name:dict(link=torrent['links'][0] if torrent['links'] else None)}
                else:
                    # Need to look up and see if this file was selected                   

                    files = self.torrentInfoFiles(torrent['id'])
                    if file_name not in files:
                        continue
                    file = files[file_name]
                    if not file['selected']:
                        continue
                    return torrent, files
        return None, None

    def resolve_torrent(self, torrent_file, file_name, ask_auth=True):
        if ask_auth and not self.token and not self.asked:
            if tools.showDialog.yesno("Real Debrid", 
                    "Do you have a Real Debrid premium account and would like to authorise it now?"):
                self.auth()
            else:
                tools.showDialog.ok("Real Debrid", "You can add Debrid support later in the settings")
                self.asked = True
        if not self.token:
            return None

        #tools.progressDialog.create("Read Debrid")
        file_name = unquote(file_name)
        # first we need to the hash to check instant availability
        magnet, files = self.make_magnet_from_torrent(torrent_file)
        if not files or file_name not in files:
            #tools.progressDialog.update(-1, 'File "{}" no in IA torrent'.format(file_name), file_name)
            tools.log("""couldn't find "{}" in torrent""".format(file_name),'error')
            return None
        file = files[file_name]
        key_list = ','.join([str(file['id'])])
        hash = str(re.findall(r'btih:(.*?)(?:&|$)', magnet)[0].lower())

        def start_caching(reuse_existing=True, delete_after=True):
            # ensure we aren't already trying to cache it. if instant we don't need to bother
            torrent, files = self.downloadingFiles(hash, file_name) if reuse_existing else (None,dict())
            if torrent is None:
                #tools.progressDialog.update(-1, "Initilising", file_name)
                if reuse_existing:
                    tools.log('Torrent for "{}" not uploaded to RD'.format(file_name), 'notice')
                torrent = self.addMagnet(magnet)
                self.torrentSelect(torrent['id'], key_list)

                # if its instantly available we will now have a link. Refresh our info to see
                # it its still resolving the magnet link (hasn't seen this torrent before), we won't get the file
                file = self.torrentInfoFiles(torrent['id']).get(file_name, dict(link=None))
            else:
                # we have already started downloading it. See if its ready yet
                file = files[file_name]
            link = file.get('link')
            if link:
                #tools.progressDialog.update(-1, "Found!", file_name)
                tools.log('"{}" cached on RD'.format(file_name), 'notice')
                link = self.resolve_hoster(link)
                if delete_after:
                    self.deleteTorrent(torrent['id']) #TODO: do we only do this for a single select torrent?
            else:
                #tools.progressDialog.update(-1, "Uncached. Using IA instead.", file_name)
                tools.log('"{}" caching in progress. Reverting to normal download'.format(file_name), 'notice')
            return link

        #tools.progressDialog.update(-1, "Checking if available", file_name)
        # do an instant check to see if we have this torrent. already.
        instant = self.instantAvailabilityFiles(hash)
        if file_name not in instant:
            # setup the cache in the background so its faster next time or us or others
            threading.Thread(target=start_caching, kwargs=dict(reuse_existing=True)).start()
            return None
        else:
            return start_caching(reuse_existing=False)

    def ia_torrent_url(self, dl_url):
        "Get the torrent url for a file point into a IA collection"
        parsed = urlparse(dl_url)
        _,download,collection,rest = parsed.path.split('/',3)
        # if there is another / it could be inside a zip so skip it
        # TODO: determine if its a zip or folder
        if parsed.hostname == "archive.org" and download == 'download' and '/' not in rest:
            torrent = "https://archive.org/download/{}/{}_archive.torrent".format(collection,collection)
            file = rest
            return (torrent,file)
        else:
            return (None,rest)

    


if __name__ == "__main__":
    dl_url = "https://archive.org/download/PSP_EU_Arquivista/7%20Wonders%20of%20the%20Ancient%20World%20%28EU%29.iso"
    dl_url = "https://archive.org/download/PSP_EU_Arquivista/PaRappa%20the%20Rapper%20%28EU%20-%20AU%29.iso"
    dl_url = "https://archive.org/download/PSP_EU_Arquivista/Driver%2076%20%28EU%29.iso"
    #dl_url = "https://archive.org/download/PSP_EU_Arquivista/Disney%20TRON%20-%20Evolution%20%28EU%29.iso"
    #dl_url = "https://archive.org/download/RedumpSonyPlayStationAmerica20160617/Tony%20Hawk%27s%20Pro%20Skater%202%20%28USA%29.zip"
    #dl_url = "https://archive.org/download/PSP_EU_Arquivista/Aces%20of%20War%20%28EU%29.iso"
    dl_url = "http://archive.org/download/amigaromset/CommodoreAmigaRomset1.zip/3DGalax_v1.0.hdf"
    magnet = "magnet:?xt=urn:btih:b76aef3af2d6f8d754221b8feb62be9da4da6bc1&dn=PSP_EU_Arquivista"
    magnet = "magnet:?xt=urn:btih:W5VO6OXS234NOVBCDOH6WYV6TWSNU26B&dn=PSP_EU_Arquivista&tr=http://bt1.archive.org:6969/announce"
    progress = lambda size, total, msg, *_: print(int(size/total*100), msg)
    rd = RealDebrid()
    torrent_url, file_name = rd.ia_torrent_url(dl_url)
    if torrent_url:            
        torrent = tools.get_cached_url(torrent_url)
        link = rd.resolve_torrent(torrent, file_name)
        print(link)
        if link:
            tools.download_file(link, progress=progress)
    else:
        tools.download_file(dl_url, progress=progress, number_of_threads=20)