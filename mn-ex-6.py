#!/usr/bin/python

import time
import sys
import argparse
import math
import os

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.util import dumpNodeConnections
from mininet.clean import cleanup
from mininet.node import OVSBridge
from datetime import datetime

class NetTopo(Topo):
        def build(self, **_opts):
                c = self.addHost('c')
                s = self.addHost('s')
                r1 = self.addHost('r1')
                r2 = self.addHost('r2')
                self.addLink(r1, r2, intfName1='r1-eth0', intfName2='r2-eth0', bw = 8, delay = '10ms')
                self.addLink(c, r1, intfName1='c-eth0', intfName2='r1-eth1')
                self.addLink(s, r2, intfName1='s-eth0', intfName2='r2-eth1')

                cb = self.addHost('cb')
                sa = self.addHost('sa')
                ra = self.addHost('ra')
                rb = self.addHost('rb')
		self.addLink(sa, ra, intfName1='sa-eth0', intfName2='ra-eth1')
		self.addLink(cb, rb, intfName1='cb-eth0', intfName2='rb-eth1')

		self.addLink(ra, r1, intfName1='ra-eth0', intfName2='r1-eth3')
		self.addLink(ra, r2, intfName1='ra-eth2', intfName2='r2-eth3')

		self.addLink(rb, r1, intfName1='rb-eth0', intfName2='r1-eth2')
		self.addLink(rb, r2, intfName1='rb-eth2', intfName2='r2-eth2')


def create_ip_net(net):
        print "create_ip_net"
        net['c' ].cmdPrint("ifconfig c-eth0 192.168.1.2/24")
        net['s' ].cmdPrint("ifconfig s-eth0 192.168.2.2/24")
        net['r1'].cmdPrint("ifconfig r1-eth1 192.168.1.1/24")
        net['r1'].cmdPrint("ifconfig r1-eth0 10.0.0.1/30")
        net['r2'].cmdPrint("ifconfig r2-eth1 192.168.2.1/24")
        net['r2'].cmdPrint("ifconfig r2-eth0 10.0.0.2/30")

	net['sa' ].cmdPrint("ifconfig sa-eth0 192.168.3.2/24")
	net['cb' ].cmdPrint("ifconfig cb-eth0 192.168.4.2/24")

	net['r1'].cmdPrint("ifconfig r1-eth2 10.0.0.17/30")
	net['r1'].cmdPrint("ifconfig r1-eth3 10.0.0.5/30")

	net['r2'].cmdPrint("ifconfig r2-eth2 10.0.0.13/30")
	net['r2'].cmdPrint("ifconfig r2-eth3 10.0.0.10/30")

	net['ra'].cmdPrint("ifconfig ra-eth0 10.0.0.6/30")
	net['ra'].cmdPrint("ifconfig ra-eth1 192.168.3.1/24")
	net['ra'].cmdPrint("ifconfig ra-eth2 10.0.0.9/30")

	net['rb'].cmdPrint("ifconfig rb-eth0 10.0.0.18/30")
	net['rb'].cmdPrint("ifconfig rb-eth1 192.168.4.1/24")
	net['rb'].cmdPrint("ifconfig rb-eth2 10.0.0.14/30")


def config_static_route(net):
        print "setting static routes on client and server nodes"
        net['c' ].cmdPrint('route add default gw 192.168.1.1')
        net['s' ].cmdPrint('route add default gw 192.168.2.1')

        net['cb' ].cmdPrint('route add default gw 192.168.4.1')
        net['sa' ].cmdPrint('route add default gw 192.168.3.1')

def set_log(net, node, fname):
        net[node].cmdPrint('> ./{}.{}'.format(node, fname))
        net[node].cmdPrint('chmod 666 ./{}.{}'.format(node, fname))

def set_ospf_router(net, node):
        net[node].cmdPrint('sysctl -w net.ipv4.ip_forward=1')
        set_log(net, node, 'zebra.log')
        set_log(net, node, 'bgp.log')
        net[node].cmdPrint('zebra -f ./{}.zebra.conf -d -i /tmp/{}.zebra.pid -z /tmp/{}.vty '.format(node, node, node))
        net[node].cmdPrint('chmod 666 /tmp/{}.vty'.format(node))
        net[node].cmdPrint('bgpd -f ./{}.bgp.conf -d -i /tmp/{}.bgp.pid -z /tmp/{}.vty '.format(node, node, node))

def print_routing_tables(net, stimer):
        for i in range(stimer):
                os.system("echo '----------------------'")
                os.system("echo 'PRINTING at {}s'".format(i))
                net['r1'].cmdPrint('route')
                net['r2'].cmdPrint('route')
                net['ra'].cmdPrint('route')
                net['rb'].cmdPrint('route')
                os.system('sleep {}'.format(1))

def net_test(net):
        print "Network connectivity"
        net['c'].cmdPrint('ping -c 20 192.168.2.2')
        net['c'].cmdPrint('traceroute 192.168.2.2')
        net['s'].cmdPrint('iperf3 -s &')
        net['c'].cmdPrint('sleep 3')
        net['c'].cmdPrint('iperf3 -c 192.168.2.2 -R -t 10 -P 2')

def cleanup_quagga():
        os.system('rm *.log')
        os.system('rm /tmp/*.pid')
        os.system('rm /tmp/*.vty')
        os.system('pkill zebra')
        os.system('pkill ospfd')

def run():
        cleanup_quagga()
        topo = NetTopo()
        net = Mininet(topo=topo, link=TCLink, switch=OVSBridge, controller=None) #, host=CPULimitedHost)
        net.start()
        print "Host connections"
        dumpNodeConnections(net.hosts)

        create_ip_net(net)
        config_static_route(net)
        set_ospf_router(net, 'r1')
        set_ospf_router(net, 'r2')
        set_ospf_router(net, 'ra')
        set_ospf_router(net, 'rb')

        print_routing_tables(net, 20)

        #net_test(net)

        CLI(net)
        net.stop()
        cleanup()

if __name__ == '__main__':
        setLogLevel( 'info' )
        run()

