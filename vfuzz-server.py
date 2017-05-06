# coding: utf-8 
from subprocess import *
import time
import getopt,sys
import socket
import threading
import struct
import random
import checkpoint_analyze
import os
def FormatCmd(base,type,addr,data):
  return struct.pack("<B",(base)<<4|type)+struct.pack("<I",addr)+data

# 由调用者负责处理是否重复map
def IoMap(addr,size=4,mapi=0,lock='l'):
  global Cmds
  Cmds+= lock+FormatCmd(mapi+0xa,0xa,addr,struct.pack("<I",size))

def WritePort(port,data,size=4,lock='u'):
  global Cmds
  Cmds+= lock+FormatCmd(size,0,port,struct.pack("<I",data))

def WriteMem(offset,data,base=0,size=4,lock='u'):
  global Cmds
  Cmds+= lock+FormatCmd(size,base+3,offset,struct.pack("<I",data))

def WriteCopy(offset,len,data,base=0,lock='u'):
  global Cmds
  Cmds+= lock+FormatCmd(0,base+6,offset,struct.pack("<I",len)+data)

class Fuzzer(threading.Thread):
  def __init__(self,id,c=None,runtype=0,dbg=None):
    super(Fuzzer, self).__init__()
    self.client=c
    self.stopped=False
    self.client_id=id
    self.loglistener=checkpoint_analyze.LogListener(runtype)
    self.runtype=runtype
    self.dbg=dbg
#TYPE={"RUNFUZZER":0,"RUNEXAMPLE":1}

  def sendCmd(self,data):
    try:
      self.client.sendall(data)
      self.client.recv(1)# recieve \xcc
    except socket.timeout:
      self.loglistener.stop()
      print 'socket error!\nQEMU is in an infinite loop now.\nclose thread %d'%(self.client_id)
      self.dbg.stop()
      self.client.close()
      print 'Fuzzer exit!'
      exit(-1)

  def sendCmds(self):
    global Cmds
    if len(Cmds)%10:
      print "Wrong: cmds not align!"
      print Cmds.encode('hex')
      exit(-1)
    for i in range(len(Cmds)/10):
      cmd=Cmds[i*10+1:i*10+10]
      self.sendCmd(cmd)

  def storeCmds(self):
    fp=open('last_one_cmds','wb')
    fp.write(Cmds)
    fp.close()

  def moduleFuzzer(self):
    import pvscsi_fuzz
    global Cmds
    Cmds=""
    IoMap(0xfebf0000,0x8000)
    IoMap(0xeb000,0x200,mapi=1)
    while not self.stopped:
      Cmds+=pvscsi_fuzz.pvscsiFuzz()
      self.sendCmds()
      self.storeCmds()
      time.sleep(0.1)
      self.loglistener.getScore()
      Cmds=""

  def run(self):
    if self.client==None:
      print "No socket client!"
      exit(-1)
    count=0
    print 'thread %d connect in.'%(self.client_id)  
    self.loglistener.start()
    if self.runtype==0:
      self.moduleFuzzer()
    elif self.runtype==1:
      fp=open('last_one_cmds','rb')
      data=fp.read(1024)
      global Cmds
      IoMap(0xfebf0000,0x8000)
      IoMap(0xeb000,0x200,mapi=1)
      Cmds+=data
      while data:
        data=fp.read(1024)
        Cmds+=data
      self.sendCmds()
      print 'send last_one_cmds done'
    else:
      print 'Fuzzer:unknow type!'
    self.loglistener.stop()
    print "Fuzzer Stopped!"
    # if self.sendCmd(IoMap(0xfeba0000,0x800))==None:
    #   exit(-1)
    # while not self.stopped:
    #   self.sendCmd(WriteMem(0,0x20,0xdeadface))
    #   print 'sent %d'% (count)
    #   count+=1
    #   time.sleep(2)

  def stop(self):
    print 'wanna stop fuzzer'
    self.stopped=True

class SocketServer(threading.Thread):
  def __init__(self,port=8088,socket_nums=10): 
    super(SocketServer, self).__init__()
    self.port=port
    self.MAXACCEPT=socket_nums;
    self.timeout = 0.2
    self.server=None
    self.clients=[]
    self.stopped=False

  def run(self):
    dbg=Debugger(memsize, imgpath, cmd)
    dbg.start()
    self.server=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    try:
      self.server.bind(('',self.port))
    except:
      print "Can't bind port %d"%(self.port)
      exit(-1)
    print "Server init."
    self.server.listen(self.MAXACCEPT)
    ids=0
    self.server.settimeout(self.timeout)
    while not self.stopped:
      try:
        (client,addr)=self.server.accept()
      except socket.timeout:
        continue  
      print 'accept a fuzzer at port %d'%(addr[1])
      runtype=client.recv(1)
      client.settimeout(3)
      fuzzer=Fuzzer(ids,client,int(runtype),dbg)
      ids+=1
      self.clients.append(fuzzer)
      fuzzer.start()
    if dbg.isAlive():
      dbg.stop()
    print "Server stopped"

  def stop(self):
    for each in self.clients: 
      if each.isAlive():
        each.stop()
    self.stopped=True

def GetQemuPid():
  p=Popen('ps -al|grep "qemu"',stdout=PIPE,shell=True)
  pids=p.communicate()[0].split('\n')
  pid=''
  for i in pids:
    if i=='':
      print "No process"
      break
    t=i.split()[3]
    if not pid_in_use.count(t):
      pid=t
      pid_in_use.append(pid)
      break
  if(p.poll()==None):
    p.kill()
  return pid

class Debugger(threading.Thread):
  def __init__(self,memsize,imgpath,cmd):
    super(Debugger, self).__init__()
    self.memsize=memsize
    self.imgpath=imgpath 
    self.cmd=cmd 

  def run(self):
    print "qemu-system-x86_64 --enable-kvm"+" -m "+self.memsize+" -hda "+self.imgpath+" "+self.cmd
    qemu=Popen("qemu-system-x86_64 --enable-kvm"+" -m "+self.memsize+" -hda "+\
                self.imgpath+" "+self.cmd,stdout=PIPE,stderr=STDOUT,shell=True)
    pid=GetQemuPid()
    print "qemu:"+pid
    global NOGDB
    if NOGDB:
      exit(0)
    qemuDbg=Popen("""gdb -q\
      -ex "c" \
      -ex "x/10i $pc" \
      -ex "i register" \
      -ex "bt" \
      -ex "set confirm off" \
      -ex "kill" \
      -ex "q" \
      --pid """+pid+" 2>&1",stdout=PIPE,stderr=STDOUT,shell=True)
    debuginfo=qemuDbg.communicate()[0]
    pid_in_use.remove(pid)
    print qemu.poll()
    if qemu.poll()==None:
      qemu.kill()
    print qemuDbg.poll()
    if qemuDbg.poll()==None:
      qemuDbg.kill()
    print debuginfo[-30:]
    Quit()
    if debuginfo[-30:]=='The program is not being run.\n':
      return 0
    timer=time.strftime('%Y-%m-%d-%H:%M:%S',time.localtime(time.time()))
    print "Get a crash-dump_"+timer
    fp=open("crash-dump_"+timer,'w+')
    fp.write(debuginfo)
    fp.close()

  def stop(self):
    for i in pid_in_use:
      print 'killed ',i
      killer=Popen("kill -9 "+i,stdout=PIPE,stderr=STDOUT,shell=True)
      killer.kill()

def Quit():
  global QUIT
  QUIT=True

def Usage():  
    print "Usage:vfuzz [-m|-i|-c] args...."
    print "-m memsize,like: -m 2048"
    print '-i imgpath,like: -i /home/vv/centos.img'
    print '-c command,like: -c "-device usb-ehci"'
    print '-p port,like -p 8088.DEFAULT:8088'
    print '--nogdb   ,disable gdb attach'
    sys.exit(-1)

NOGDB=False
Cmds=""
QUIT=False
pid_in_use=[]
if __name__=="__main__":
  memsize=''
  imgpath=''
  cmd=''
  random.seed()
  NOGDB=False
  port=8088
  try:  
    opts, args = getopt.getopt(sys.argv[1:], "m:i:c:p:",['nogdb'])
    for o,a in opts:
      if o=='-m':
        memsize=a 
      elif o=='-i':
        imgpath=a 
      elif o=='-c':
        cmd=a 
      elif o=='-p':
        port=int(a)
      elif o=='--nogdb':
        NOGDB=True
      else:
        print "error cmd"
        Usage()
  except getopt.GetoptError: 
    print "args error!"
    Usage()
  if memsize=='' or imgpath=='':
    print "no input!"
    Usage()
  server=SocketServer(port)
  server.start()
  try:
    while not QUIT:pass
  except KeyboardInterrupt:
    print "keyboard quit!"
  server.stop()
