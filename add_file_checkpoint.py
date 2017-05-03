#encoding=utf-8
import re
# 使用说明:
#  添加需要修改的文件到当前目录,然后将文件名添加到 FILENAME
#  将第一个函数前的空行位置添加起始标志 //start
#  将需要添加的主要函数名添加到POINT_FUNCS列表中,脚本会自动追溯函数中的被调用函数
#  将不需要打点的函数名或者宏定义添加到KEYWORD列表中

FILENAME='vmw_pvscsi.c'
file_lines={}#index:funcline
full_func_list={}#'funcname':(ifunc,index)
POINT_FUNCS=[
'pvscsi_io_write',
"pvscsi_on_cmd_unknown",
"pvscsi_on_cmd_config",
"pvscsi_on_issue_scsi",
"pvscsi_on_cmd_unplug",
"pvscsi_on_cmd_setup_rings",
"pvscsi_on_cmd_reset_device",
"pvscsi_on_cmd_reset_bus",
"pvscsi_on_cmd_setup_msg_ring",
"pvscsi_on_cmd_abort",
"pvscsi_io_read",
"pvscsi_on_cmd_adapter_reset"
]
KEYWORD={"while":0,"for":0,'fprintf':0,'if':0,'switch':0,'DPRINTF':0,'BADF':0,'sizeof':0,'check_point':0}
check_func="check_point("
check_function=\
'#include <sys/socket.h>\n'\
'#include <sys/un.h>\n'\
'void check_point(const char *buf){\n'\
'  int sockfd=socket(AF_UNIX,SOCK_STREAM,0);\n'\
'  struct sockaddr_un address;\n'\
'  address.sun_family=AF_UNIX;\n'\
'  strcpy(address.sun_path,"./local_socket");\n'\
'  int result=connect(sockfd,(struct sockaddr*)&address,sizeof(address));\n'\
'  write(sockfd,buf,strlen(buf));\n'\
'  close(sockfd);\n'\
'}\n'
check_list=[]

def splitFile(filename):
  with open(filename,'rb') as fp:
    data=fp.readline()
    ifunc=0
    iblock=0
    datas=''
    ibrace=0
    funcname=''
    funcline=''
    while data:
      #print data,'1'
      if '//start' in data:
        datas+='void check_point(const char *buf);\n'
        data=fp.readline()
        break
      else:
        datas+=data
        data=fp.readline()
        continue
    print '***********************start********************'
    while data:
      if '(' in data:
        if ' (' not in data:
          #print data 
          s=re.search('\w+\(',data)
          if not s:
            print data
            datas+=data
            raw_input()
            break
          s=s.span()
          funcname=data[s[0]:s[1]-1]
          # print   funcname
          #check if it's only a decline;
          if '{' not in data:
            if ';' in data:
              datas+=data
              data=fp.readline()
              # print data,'2'
              continue
            funcline=data
            data=fp.readline()
            # print data,'3'
            flag=0
            while ('{' not in data):
              if ';' in data or '}' in data or re.search('\)\s?,',data):
                funcline+=data
                datas+=funcline
                data=fp.readline()
                #print data,'4'
                flag=1
                break
              funcline+=data
              data=fp.readline()
              #print data,'5'
            if flag:
              continue
          ibrace=0
          index=data.index('{')
          check_list.append('f:'+str(ifunc)+"\n")
          # data=data[:index+1]+'check_point("f:'+str(ifunc)+'\\n");'+data[index+1:]
          funcline+=data 
          data=fp.readline()
          # print data,'6'
          while data:
            if '{' in data:
              ibrace+=1
            if '}' in data:
              if ibrace==0:
                funcline+=data
                data=fp.readline()
                #print data,'7'
                break
              else:
                ibrace-=1 
            funcline+=data 
            data=fp.readline()
            #print data,'8',ibrace
            #raw_input()

          full_func_list[funcname]=(ifunc,iblock+1)
          ifunc+=1
          file_lines[iblock]=datas
          iblock+=1
          file_lines[iblock]=funcline
          iblock+=1
          datas=''
          funcline=''
      datas+=data 
      data=fp.readline()
      # print data,data.encode('hex')
      # raw_input('>')

    if datas != '':
      file_lines[iblock]=datas
      iblock+=1
    file_lines[iblock]=check_function

def addFuncPoint(index,ifunc,func_index,start,end):
  funcline=file_lines[index]
  try:
    point=funcline[end:].index(';')+end
  except:
    print funcline[end:]
    raw_input()
    return
  checkline=funcline[end:point]
  if checkline.count(')')>checkline.count('(') or checkline.count('{'):
    return end
  if '#define' in funcline[start-10:start]:
    #print funcline[start-10:start]
    return end
  if ' else ' in funcline[point:point+20]:
    return end
  check_list.append(str(ifunc)+'-'+str(func_index)+'\n')
  tcheck_func=check_func+'"'+str(ifunc)+'-'+str(func_index)+'\\n");'
  new_funcline=funcline[:point+1]+tcheck_func+funcline[point+1:]
  file_lines[index]=new_funcline
  end=point+len(tcheck_func)
  # print point,end,len(tcheck_func)
  # print new_funcline[end:end+10]
  # print new_funcline
  # raw_input()
  return end

def pointFunc():
  #print full_func_list
  pointfuncname=POINT_FUNCS[0]
  ipoint=1
  while pointfuncname:
    if POINT_FUNCS==[]:
      print 'No func select!'
      return
    # print pointfuncname,'<pointfuncname'
    if full_func_list.has_key(pointfuncname):
      index=full_func_list[pointfuncname][1]
      ifunc=full_func_list[pointfuncname][0]
      func_index=0
      funcline=file_lines[index]
      #print funcline
      r=re.search('\w+\(',funcline)# ()
      if r:
        end=r.span()[1]
        # print r.span()
        r=re.search('\w+\(',funcline[end:])
        while r:
          start=r.span()[0]+end
          end=r.span()[1]-1+end
          funcname=funcline[start:end]
          # print funcname,'<funcname\n'
          # raw_input()
          if KEYWORD.has_key(funcname):
            # print funcname,'pass'
            pass
          else:
            end=addFuncPoint(index,ifunc,func_index,start,end)
            func_index+=1
            funcline=file_lines[index]
            if funcname not in POINT_FUNCS and full_func_list.has_key(funcname):
              POINT_FUNCS.append(funcname)
          r=re.search('\w+\(',funcline[end:])
      # only add need func for point
      r=re.search('{',funcline)
      end=r.span()[1]
      newfuncline=funcline[:end]+'check_point("f:'+str(ifunc)+'\\n");'+funcline[end:]
      file_lines[index]=newfuncline
      # print newfuncline
      # raw_input()
      # exit(0)
    else:
      print 'Error pointfuncname:',pointfuncname,'!\n'
      break
    try:
      pointfuncname=POINT_FUNCS[ipoint]
      ipoint+=1
    except:
      break
    #raw_input('?')

def readchar(line,end):
  try:
    return line[end:end+1]
  except:
    return ''

def addBranchPoint():
  for i in POINT_FUNCS:
    funcline=file_lines[full_func_list[i][1]]
    ifunc=full_func_list[i][0]
    r=re.search('\sif\s*\(',funcline)
    end=0
    iif=0
    while r:
      end=r.span()[1]+end
      c=readchar(funcline,end)
      end+=1
      ipar=0
      while c!=';' and c!='':
        # print c,ipar,'reading',
        # raw_input('?')
        if c=='(':
          ipar+=1
        if c==')' and ipar==0:
          if '{' in funcline[end:end+10]:
            point=funcline[end:].index('{')+end
            check_list.append(str(ifunc)+'*'+str(iif)+'\n')
            tcheck_func=check_func+'"'+str(ifunc)+'*'+str(iif)+'\\n");'
            iif+=1
            funcline=funcline[:point+1]+tcheck_func+funcline[point+1:]
            end+=len(tcheck_func)
            break
          else:
            point=end
            end=funcline[point:].index(';')+point+1
            check_list.append(str(ifunc)+'*'+str(iif)+'\n')
            tcheck_func=check_func+'"'+str(ifunc)+'*'+str(iif)+'\\n");'
            iif+=1
            funcline=funcline[:point]+'{'+tcheck_func+funcline[point:end]+'}'+funcline[end:]
            break
        elif c==')':
            ipar-=1
        c=readchar(funcline,end)
        end+=1
        
      r=re.search('\sif\s*\(',funcline[end:])
      #raw_input('>>>>>>>>')
    r=re.search('(\s\w+\s\w+:)|(\s\w+:)',funcline)
    end=0
    icase=0
    while r:
      start=r.span()[0]+end
      end=r.span()[1]+end
      #print funcline[start:end]
      if '?' in funcline[start-10:end]:
        r=re.search('(\s\w+\s\w+:)|(\s\w+:)',funcline[end:])
        continue
      check_list.append(str(ifunc)+'+'+str(icase)+'\n')
      tcheck_func=check_func+'"'+str(ifunc)+'+'+str(icase)+'\\n");'
      funcline=funcline[:end]+tcheck_func+funcline[end:]
      icase+=1
      end+=len(tcheck_func)
      r=re.search('(\s\w+\s\w+:)|(\s\w+:)',funcline[end:])
    file_lines[full_func_list[i][1]]=funcline
    #print funcline

def storeFile(filename):
  with open(filename,'wb') as fp:
    for i in range(0,len(file_lines)):
      fp.write(file_lines[i])

if __name__=="__main__":
  splitFile(FILENAME)
  if not len(full_func_list):
    print 'No start sign!'
    exit(0)
  pointFunc()
  addBranchPoint()
  storeFile(FILENAME+'.c')
  with open('check_list','wb') as fp:
    for i in check_list:
      fp.write(i)
  flag=0
  print full_func_list
  print POINT_FUNCS
  for i in full_func_list:
    for pfunc in POINT_FUNCS:
      if pfunc==i:
        flag=1
        break
    if not flag:
      print i
    flag=0
  print 'Finish!'
