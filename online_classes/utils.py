from django.conf import settings
from subprocess import PIPE, Popen
import datetime, os
import re
import urllib
import math
import filecmp
import sys,os
from urllib.parse import unquote
from django.conf import settings

class ckDict(dict):
    def __init__(self, default=None):
        dict.__init__(self)
        self.default = default
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            return self.default
    def htmlprint(self):
        html = []
        html.append("<table cellpadding=10 cellspacing=0 border=1>")
        for key in self.keys():
            html.append("<tr><td bgcolor=\"lightgreen\"><b>%s</b></td><td>%s</td></tr>" %(key,(self[key])))
        html.append("</table>")
        return html
    def print(self):
        html = []
        for key in self.keys():
            html.append("%s=%s\n" %(key,(self[key])))
        return html

def get_age(dateofbirth):

    f_date = datetime.datetime.strptime(dateofbirth, "%Y-%m-%d").date()
    l_date = datetime.datetime.now().date()
    delta = l_date - f_date
    return int(delta.days/365)

def get_form_data(request):
    data = ckDict()
    for word in request.POST.keys():
        word = unquote(word)
        data[word] = request.POST[word]
    for word in request.GET.keys():
        word = unquote(word)
        data[word] = request.GET[word]
    server_url = request.META['HTTP_HOST']
    data['server_url'] = server_url 
    data['static_url'] = server_url +"/static/autochar"
    data['user'] = request.user
    data['template_url'] = server_url +"/online_classes"
    data['static_path'] = settings.STATIC_ROOT+"/online_classes"
    data['current_url'] = request.META['PATH_INFO']
    data['page'] = request.META['PATH_INFO'].split('/')[1]
    data['current_full_url'] = request.META['PATH_INFO']+"?"+ request.META['QUERY_STRING']
    data['request'] = request
    
    return data

def set_cookie(response, key, value, expire=None):
    if expire is None:
        max_age = 365*24*60*60  #one year
    else:
        max_age = expire
    expires = datetime.datetime.strftime(datetime.datetime.utcnow() + datetime.timedelta(seconds=max_age), "%a, %d-%b-%Y %H:%M:%S GMT")
    response.set_cookie(key, value, max_age=max_age, expires=expires, 
        domain=settings.SESSION_COOKIE_DOMAIN, secure=settings.SESSION_COOKIE_SECURE or None)
    
