#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from scapy.all import *

class Scanner:
	def __init__(self):
		pass
	
	def getLiveHosts(self,ip,net):
		try:
			alive,dead=srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ip+'/'+net), timeout=2, verbose=0)
			print "MAC - IP"
			for i in range(0,len(alive)):
					print alive[i][1].hwsrc + " - " + alive[i][1].psrc
		except:
			print 'Exception'
			pass

t=Scanner()
t.getLiveHosts('10.100.3.113','24')
