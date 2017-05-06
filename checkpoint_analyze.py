from __future__ import division
import threading
import socket
import os
import sys

class LogListener(threading.Thread):
  def __init__(self,runtype): 
    super(LogListener, self).__init__()
    self.log_addr='./local_socket'
    self.log_list=[]
    self.trigger_list=[]
    self.stopped=False
    self.pre_score='0\n'
    self.score='0\n'
    self.check_list={}
    self.timer=1
    self.runtype=runtype
    self.delaytime=0.5

  def getCovScore(self):
    score='0'
    if self.check_list=={}: 
      with open('check_list','r') as cfp:
        data=cfp.readline()
        self.check_list[data]=0
        while data:
          data=cfp.readline()
          self.check_list[data]=0
    #count checkpoint
    for each in self.log_list:
      if self.check_list.has_key(each):
        self.check_list[each]+=1
    #count empty point,and new point
    new_trigger_list=[]
    empty_list=[]
    for i in self.check_list:
      if self.check_list[i] != 0:
        if not self.trigger_list.count(i):
          self.trigger_list.append(i)
          new_trigger_list.append(i)
      else:
        if not self.trigger_list.count(i):
          empty_list.append(i)
    try:
      pre_efp=open('empty_list','rb')
      pre_efp.close()
      self.pre_score=self.score
    except:
      self.pre_score='0\n'

    # print "new nodes:"
    # for i in new_trigger_list:
    #   print i,
    # print "new count:",len(new_trigger_list)

    efp=open('empty_list','wb')
    self.score=str(len(self.trigger_list)*100/len(self.check_list))[:4]+'%\n'
    efp.write(self.score)
    empty_list.sort()
    for i in empty_list:
      efp.write(i)
      # print i,
    efp.close()

  def run(self):
    try:
      os.unlink(self.log_addr)
    except OSError:
      if os.path.exists(self.log_addr):
        raise
    sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
    sock.bind(self.log_addr)
    sock.listen(1)
    sock.settimeout(0.1)
    threading.Timer(self.delaytime,self.timerPrintSocre).start()
    while not self.stopped:
      try:
        con,client_addr=sock.accept()
      except socket.timeout:
        continue
      while True:
        data=con.recv(10)
        if data:
          self.log_list.append(data)
          if self.runtype:
            print data
          break
      con.close()
    print 'LogListener exit!'

  def stop(self):
    self.timer=0
    self.stopped=True

  def timerPrintSocre(self):
    if self.timer:
      self.timer+=1
      sys.__stdout__.write('\rcur_score:'+self.score[:-1]+\
        ' times:'+str(self.timer)+' ')
      sys.__stdout__.flush()
      threading.Timer(self.delaytime,self.timerPrintSocre).start()

  def getScore(self):
    self.getCovScore()
    self.log_list=[]
    return self.score