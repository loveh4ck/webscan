#-*- coding=utf-8 -*-
import requests
import re
from threading import Thread, Lock
import time
import sys
import chardet
import netaddr
import struct
import socket
import gc

lock = Lock()

def ip2int(addr):
	return struct.unpack("!I", socket.inet_aton(addr))[0]

def int2ip(addr):
	return socket.inet_ntoa(struct.pack("!I", addr))

def int_dec(pagehtml):
	charset = None
	if pagehtml != '':
		enc = chardet.detect(pagehtml)
		if enc['encoding'] and enc['confidence'] > 0.9:
			charset = enc['encoding']
		if charset == None:
			charset_re = re.compile("((^|;)\s*charset\s*=)([^\"']*)", re.M)
			charset = charset_re.search(pagehtml[:1000])
			charset = charset and charset.group(3) or None
		try:
			if charset:
				unicode('test', charset, errors='replace')
		except Exception, e:
			print 'Exception', e
			charset = None
	# print 'charset=', charset
	return charset


def http_banner(url):
	ip = url
	try:
		url = requests.get(url, timeout=2)
		body = url.content
		charset = None
		if body != '':
			charset = int_dec(body)
		if charset == None or charset == 'ascii':
			charset = 'ISO-8859-1'
		if charset and charset != 'ascii' and charset != 'unicode':
			try:
				body = unicode(body, charset, errors='replace')
			except Exception, e:
				body = ''
		Struts = url.status_code
		Server = url.headers['server'][0:13]
		if Struts == 200 or Struts == 403 or Struts == 401:
			title = re.findall(r"<title>(.*)<\/title>", body)
			if len(title):
				title = title[0].strip().encode("GBK")
			else:
				title = ''
			lock.acquire()
			#print('%s\t%d\t%-10s\t%s' % (ip.lstrip('http://'), Struts, Server, title))
			f=file("result.txt", "a+")
			f.write('%s\t%d\t%-10s\t%s' % (ip.lstrip('http://'), Struts, Server, title)+"\n")
			f.close()
			lock.release()
			gc.collect()
	except (requests.HTTPError, requests.RequestException, AttributeError, KeyError), e:
		pass

if __name__ == '__main__':
	port = '80'
	ip_file = open('china_ip_list.txt')
	for ips in ip_file:
		if '-' in ips:
			start, end = ips.split('-')
			startlong = ip2int(start)
			endlong = ip2int(end)
			ips = netaddr.IPRange(start, end)
			#print ips
			for ip in list(ips):
				url = 'http://%s:%s' % (ip, port)
				print url
				t = Thread(target=http_banner, args=(url,))
				t.daemon = False
				t.start()
		elif '/' in ips:
			ips = netaddr.IPNetwork(ips)
			for ip in list(ips):
				url = 'http://%s:%s' % (ip, port)
				t = Thread(target=http_banner, args=(url,))
				t.daemon = False
				t.start()
