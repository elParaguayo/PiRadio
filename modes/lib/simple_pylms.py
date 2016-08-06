"""
Simple python class definitions for interacting with Logitech Media Server.

This code uses the JSON interface.
"""
import urllib2
import json


class LMSPlayer(object):

    def __init__(self, ref, server):
        self.server = server
        self.ref = ref

    def __repr__(self):
        return "SqueezePlayer: {}".format(self.ref)

    def request(self, command):
        return self.server.request(self.ref, command)

    def set_name(self, name):
        self.request("name {}".format(name))

    def get_wifi_signal_strength(self):
        self.wifi_signal_strength = self.request("signalstrength ?")
        return self.wifi_signal_strength.get("_signalstrength")

    def get_track_artist(self):
        self.track_artist = self.request("artist ?")
        return self.track_artist["_artist"]

    def get_track_album(self):
        self.track_album = self.request("album ?")
        return self.track_album["_album"]

    def get_track_title(self):
        self.track_title = self.request("title ?")
        return self.track_title["_title"]

    def get_track_duration(self):
        self.track_duration = float(self.request("duration ?"))
        return self.track_duration["_duration"]

    def play(self):
        self.request("play")

    def stop(self):
        self.request("stop")

    def play_pause(self):
        self.request("pause")

    def next(self):
        self.request("playlist jump +1")

    def previous(self):
        self.request("playlist jump -1")

class LMSServer(object):
    """
    Class for Logitech Media Server.

    Provides access to JSON interface.
    """

    def __init__(self, host="localhost", port=9000):
        self.host = host
        self.port = port
        self.id = 1
        self.url = "http://{h}:{p}/jsonrpc.js".format(h=host, p=port)

    def request(self, player="-", params=None):
        """
        Send JSON request to server.
        """
        req = urllib2.Request(self.url)
        req.add_header('Content-Type', 'application/json')

        if type(params) == str:
            params = params.split()

        cmd = [player, params]

        data = {"id": self.id,
                "method": "slim.request",
                "params": cmd}

        try:
            response = urllib2.urlopen(req, json.dumps(data))
            self.id += 1
            return json.loads(response.read())["result"]

        except:
            return None
