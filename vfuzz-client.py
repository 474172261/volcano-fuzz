import struct
import sys
import getopt
import socket
import threading
def Translate(data):
  # print data.encode('hex')
  fp=open("/proc/vfuzz","w+")
  fp.write(data)
  fp.close()

class Accepter(threading.Thread):
  def __init__(self,client): 
    super(Accepter, self).__init__()
    self.stopped=False 
    self.client=client

  def run(self):
    if self.client==None:
      print 'No Client!'
      exit(-1)
    while not self.stopped:
      try:
        data=self.client.recv(1024)
        if not data:
          continue
        self.client.send('\xff')
      except socket.timeout:
        continue 
      except:
        print 'send or get fail!'
        exit(-1)
      # print len(data)
      # print data.encode('hex')
      Translate(data)
    print '\nClient exit!'

  def stop(self):
    self.stopped=True

def SocketClient(ipaddr,runtype,port):
  c=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
  try:
    c.connect_ex((ipaddr,port))
  except socket.error as e:
    print e
    print 'Fail to connect %s!'%(ipaddr)
    c.close()
    exit(-1)
  c.settimeout(0.2)
  c.send(runtype)
  thread=Accepter(c)
  thread.start()
  try:
    while 1:pass
  except KeyboardInterrupt:
    thread.stop()

def Usage():
  print """Usage: -i 192.168.1.1 """
  print "-p port"
  print "-t type.type 0: run fuzzer; type 1: run last one cmds. Default 0."
  sys.exit(-1)

if __name__=="__main__":
  port=8088
  ip=None
  runtype=0
  try: 
    opts,args=getopt.getopt(sys.argv[1:],"i:p:t:")
    for o,a in opts:
      if o=='-i':
        ip=a
      elif o=='-p':
        port=a
      elif o=='-t':
        runtype=a
        if runtype not in ['0','1']:
          Usage()
      else:
        Usage()
  except getopt.GetoptError:
    Usage()
  if ip==None:
    print "no ipaddr!"
    Usage()
    exit(-1)
  SocketClient(ip,runtype,port)
