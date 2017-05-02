from __future__ import division
import os
def getCovScore():
  check_list={}
  score='0'
  with open('check_list','r') as cfp:
    data=cfp.readline()
    check_list[data]=0
    while data:
      # if 'f:' in data:
      #   data=cfp.readline()
        # continue
      data=cfp.readline()
      check_list[data]=0

  try:
    with open('log','rb') as fp:
      data=fp.readline()
      while data:
        # if 'f:' in data:
        #   data=fp.readline()
        #   continue
        if check_list.has_key(data):
          check_list[data]+=1
        data=fp.readline()
  except:
    print 'No log file!'
    exit(0)
  os.remove('log')
  empty_list=[]
  trigger_list=[]
  for i in check_list:
    if check_list[i] == 0:
      empty_list.append(i)
    else:
      trigger_list.append(i)
  empty_list.sort()
  trigger_list.sort()
  pre_efp=0
  try:
    pre_efp=open('empty_list','rb')
  except:
    efp=open('empty_list','wb')
    score=str(len(trigger_list)*100/len(check_list))[:4]+'%\n'
    efp.write(score)
    for i in empty_list:
      efp.write(i)
      # print i,
    efp.close()
  pre_empty_list=[]
  pre_score='0\n'
  if pre_efp:
    data=pre_efp.readline()
    pre_score=data
    while data:
      data=pre_efp.readline()
      pre_empty_list.append(data)
    print 'new nodes:'
    new_node_count=0
    for i in trigger_list:
      if pre_empty_list.count(i):
        print i,
        new_node_count+=1
    print 'new nodes count:%d'%(new_node_count)
    os.remove('empty_list')
    efp=open('empty_list','wb')
    score=str(len(trigger_list)*100/len(check_list))[:4]+'%\n'
    efp.write(score)
    for i in empty_list:
      efp.write(i)
      # print i,
    efp.close()
  return (pre_score,score)
if __name__ == '__main__':
  (pre_score,score)=getCovScore()
  print 'pre score is:%scur score is:%s'%(pre_score,score)
