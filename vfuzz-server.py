# coding: utf-8 
from subprocess import *
import time
import getopt,sys
import socket
import threading
import struct
import random
import pvscsi_fuzz

def FormatCmd(base,type,addr,data):
  return struct.pack("<B",(base)<<4|type)+struct.pack("<I",addr)+data

Cmds=""
mapped=[-1,-1,-1]
def IoMap(addr,size=4,mapi=0,lock='l'):
  global Cmds
  if mapi>=3:
    print "iomap num too big!"
  if mapped[mapi] == -1:
    mapped[mapi]=mapi
    mapi=mapi+1
    Cmds+= lock+FormatCmd(mapi+0xa,0xa,addr,struct.pack("<I",size))

def WritePort(port,data,size=4,lock='u'):
  global Cmds
  Cmds+= lock+FormatCmd(size,0,port,struct.pack("<I",data))

def WriteMem(offset,data,base=0,size=4,lock='u'):
  global Cmds
  Cmds+= lock+FormatCmd(size,base+3,offset,struct.pack("<I",data))

def WriteCopy(offset,data,base=0,lock='u'):
  global Cmds
  Cmds+= lock+FormatCmd(0,base+6,offset,data)

def Ri(max,min=0):
  return random.randint(min,max)

def bitFlip(isdata=False):
  len_cmd=len(Cmds)
  if isdata:
    pos=Ri(len_cmd)
    bit=1<<(Ri(32))
    flip=ord(Cmds[pos:pos+1])^bit
    Cmds=Cmds[:pos]+flip+Cmd[pos+1:]
  else:
    if len_cmd%10:
      print "Error:wrong cmd align for bitFlip!"
    pos=Ri(len_cmd/10)
    while Cmds[pos*10:pos*10+1]=='l':
      pos=0 if pos-1<0 else pos-1
      print 'lock check:',pos
      pos=Ri(len_cmd/10)

    intval=struct.unpack('<I',Cmds[pos*10+6:pos*10+10])[0]
    bit=1<<(Ri(32))
    flip=intval^bit
    flip=struct.pack('<I',flip)
    Cmds=Cmds[:pos*10+6]+flip+Cmds[pos*10+10:]

def byteCopies(isdata=False):
  len_cmd=len(Cmds)
  if isdata:
    pos=Ri(len_cmd)
    len_copy= Ri(len_cmd)
    copy=Cmds[pos:len_copy+pos]
  else:
    if len_cmd%10:
      print "Error:wrong cmd align for byteCopies!"
    pos=Ri(len_cmd/10)
    print pos
    len_copy=Ri(len_cmd/10-pos)
    copy=Cmds[pos*10:pos*10+len_copy*10]# copy some len
  Cmds+=copy

def byteRemovals(isdata=False):
  len_cmd=len(Cmds)
  if isdata:
    pos=Ri(len_cmd)
    print len_cmd
    len_remove=Ri(int(len_cmd*0.1))# 移除的数据最多占10%
    Cmds=Cmds[:pos]+Cmds[pos+len_remove:]
  else:
    if len_cmd%10:
      print "Error:wrong cmd align for byteRemovals!"
    print len_cmd
    pos=Ri(len_cmd/10)
    len_remove=Ri(int(len_cmd*0.1))# 移除的命令最多占10%
    Cmds=Cmds[:pos*10]+Cmds[pos*10+len_remove*10:]

class Fuzzer(threading.Thread):
  def __init__(self,id,c=None):
    super(Fuzzer, self).__init__()
    self.client=c
    self.stopped=False
    self.client_id=id

  def sendCmd(self,data):
    try:
      self.client.sendall(data)
      self.client.recv(1)
    except socket.error:
      print 'sendCmd fail!\nclose thread %d'%(self.client_id)
      self.client.close()
      exit(-1)

  def mutator(self):
    bitFlip()
    posb=Ri(100)
    if posb<30:
      byteCopies()
    posb=Ri(100)
    if posb<20:
      byteRemovals()
    
  def sendCmds(self):
    global Cmds
    if len(Cmds)%10:
      print "Wrong: cmds not align!"
      print Cmds.encode('hex')
      exit(-1)
    for i in range(len(Cmds)/10):
      cmd=Cmds[i*10+1:i*10+10]
      self.sendcmd(cmd)

  def initCmd(self):
    global Cmds
    Cmds=''
    ret=IoMap(0xfebf0000,0x800)
    if ret==None:
      pass
    cmd_sizes=(0,0,0,132,0,3,4,6,34)
    for i in range(9):
      WriteMem(0,i,base=0,size=4,lock='l')
      for i in range(cmd_sizes[i]):
        WriteMem(4,randInt());
    while True:
      self.mutator()
      self.sendCmds()

  def pvscsiPoc(self):
    global Cmds
    Cmds=""
    IoMap(0xfebf0000,0x800)
    WriteMem(0,3)
    for i in range(132):
      WriteMem(4,0xffffffff)
    self.sendCmds()

  def run(self):
    if self.client==None:
      print "No socket client!"
      exit(-1)
    count=0
    print 'thread %d:connect in.'%(self.client_id)
    global Cmds
    Cmds=pvscsi_fuzz.pvscsiFuzz()
    self.sendCmds()
    # if self.sendCmd(IoMap(0xfeba0000,0x800))==None:
    #   exit(-1)
    # while not self.stopped:
    #   self.sendCmd(WriteMem(0,0x20,0xdeadface))
    #   print 'sent %d'% (count)
    #   count+=1
    #   time.sleep(2)

  def stop(self):
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
      print 'accept addr %s at port %d'%(addr[0],addr[1])
      thread=Fuzzer(ids,client)
      ids+=1
      self.clients.append(thread)
      thread.start()
    print "Server stopped"

  def stop(self):
    for each in self.clients: 
      each.stop()
    self.stopped=True

pid_in_use={}
def GetQemuPid():
  p=Popen('ps -al|grep "qemu"',stdout=PIPE,shell=True)
  pids=p.communicate()[0].split('\n')
  pid=''
  for i in pids:
    if i=='':
      print "No process"
      break
    t=i.split()[3]
    if not pid_in_use.has_key(t):
      pid=t
      pid_in_use[t]=1
      break
  if(p.poll()==None):
    p.kill()
  return pid

QUIT=False
def Debugger(memsize,imgpath,cmd):
  print "qemu-system-x86_64 --enable-kvm"+" -m "+memsize+" -hda "+imgpath+" "+cmd
  qemu=Popen("qemu-system-x86_64 --enable-kvm"+" -m "+memsize+" -hda "+imgpath+" "+cmd,stdout=PIPE,stderr=STDOUT,shell=True)
  pid=GetQemuPid()
  print "qemu:"+pid
  qemuDbg=Popen("""gdb -q\
    -ex "c" \
    -ex "disass $pc" \
    -ex "i register" \
    -ex "bt" \
    -ex "set confirm off" \
    -ex "kill" \
    -ex "q" \
    --pid """+pid+" 2>&1",stdout=PIPE,stderr=STDOUT,shell=True)
  debuginfo=qemuDbg.communicate()[0]
  pid_in_use.pop(pid)
  print qemu.poll()
  if qemu.poll()==None:
    qemu.kill()
  print qemuDbg.poll()
  if qemuDbg.poll()==None:
    qemuDbg.kill()
  print debuginfo[-30:]
  Quit()
  if debuginfo[-30:]=='The program is not being run.\n':
    return -1
  fp=open("crash-dump_"+time.strftime('%Y-%m-%d-%H:%M:%S',time.localtime(time.time())),'w+')
  fp.write(debuginfo)
  fp.close()

def Quit():
  global QUIT
  QUIT=True

def Usage():  
    print "Usage:vfuzz [-m|-i|-c] args...."
    print "-m memsize,like: -m 2048"
    print '-i imgpath,like: -i "/home/vv/centos.img"'
    print '-c command,like: -c "-device usb-ehci"'
    sys.exit(-1)

if __name__=="__main__":
  memsize=''
  imgpath=''
  cmd=''
  random.seed()
  try:  
    opts, args = getopt.getopt(sys.argv[1:], "m:i:c:")
    for o,a in opts:
      if o=='-m':
        memsize=a 
      elif o=='-i':
        imgpath=a 
      elif o=='-c':
        cmd=a 
      else:
        print "error cmd"
        Usage()
  except getopt.GetoptError: 
    print "args error!"
    Usage()
  if memsize=='' or imgpath=='':
    print "no input!"
    Usage()
  thread=threading.Thread(target=Debugger,args=(memsize, imgpath, cmd))
  thread.start()
  server=SocketServer()
  server.start()
  try:
    while not QUIT:pass
  except KeyboardInterrupt:
    print "keyboard quit!"
  server.stop()
  # print "rs for restart server"
  # cmd=raw_input('>')
  # if cmd=='rs'
