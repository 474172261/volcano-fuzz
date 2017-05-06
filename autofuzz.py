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

  def mutator(self):
    bitFlip()
    posb=Ri(100)
    if posb<30:
      byteCopies()
    posb=Ri(100)
    if posb<20:
      byteRemovals()

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