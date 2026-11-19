import zipfile,xml.etree.ElementTree as ET,json,sys,datetime,os
N={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def load(path):
 with zipfile.ZipFile(path) as z:
  ss=[]
  if 'xl/sharedStrings.xml' in z.namelist():
   r=ET.fromstring(z.read('xl/sharedStrings.xml'))
   ss=[''.join(t.text or '' for t in si.findall('.//x:t',N)) for si in r.findall('x:si',N)]
  def sheet(n):
   r=ET.fromstring(z.read(f'xl/worksheets/sheet{n}.xml'));out=[]
   for row in r.findall('.//x:sheetData/x:row',N):
    d={}
    for c in row.findall('x:c',N):
     ref=c.attrib['r'];col=''.join(x for x in ref if x.isalpha());v=c.find('x:v',N)
     if v is None:continue
     val=v.text or ''
     if c.attrib.get('t')=='s':val=ss[int(val)]
     elif c.attrib.get('t') not in ('str','inlineStr','e'):
      try:val=float(val);val=int(val) if val.is_integer() else val
      except:pass
     d[col]=val
    out.append(d)
   return out
  return [sheet(i) for i in range(1,8)]
def main(src,out):
 players,tournaments,matches,finishes,leaderboard,_,_=load(src)
 names={r.get('A'):(' '.join(str(r.get(c,'')) for c in ('B','C'))).strip() for r in players[1:] if str(r.get('A','')).startswith('P')}
 ts={r.get('A'):str(r.get('C','')) for r in tournaments[1:] if str(r.get('A','')).startswith('T')}
 stats={pid:{'id':pid,'name':name,'played':0,'wins':0,'losses':0,'first':0,'second':0,'third':0,'best':None,'finishes':[]} for pid,name in names.items()}
 games=[]
 for r in matches[1:]:
  if r.get('B') not in ts or r.get('O') not in ('A','B') or not str(r.get('S','')).startswith('VALID'):continue
  a=[r.get('E'),r.get('F')];b=[r.get('G'),r.get('H')]
  if any(p not in stats for p in a+b):continue
  win=r['O'];
  for p in a+b:
   stats[p]['played']+=1
   stats[p]['wins' if (p in a)==(win=='A') else 'losses']+=1
  games.append({'tournament':r['B'],'round':r.get('C',''),'format':r.get('D',''),'teamA':[names[p] for p in a],'teamB':[names[p] for p in b],'score':f"{r.get('I','')}-{r.get('J','')}, {r.get('K','')}-{r.get('L','')}"+(f", TB {r['M']}-{r['N']}" if 'M' in r and 'N' in r else ''),'winner':win})
 for r in finishes[1:]:
  tid=r.get('A');pos=r.get('B')
  if tid not in ts or not isinstance(pos,(int,float)) or pos not in range(1,9):continue
  for p in [r.get('D'),r.get('E')]:
   if p not in stats:continue
   s=stats[p];s['finishes'].append({'tournament':tid,'position':pos});s['best']=min(s['best'],pos) if s['best'] else pos
   if pos==1:s['first']+=1
   if pos==2:s['second']+=1
   if pos==3:s['third']+=1
 people=[]
 for s in stats.values():
  if not s['played'] and not s['finishes']:continue
  s['appearances']=len(s['finishes']);s['winPct']=round(100*s['wins']/s['played'],1) if s['played'] else 0
  s['top3']=s['first']+s['second']+s['third'];people.append(s)
 people.sort(key=lambda s:(-s['wins'],-s['winPct'],s['name']))
 data={'updated':datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),'players':people,'tournaments':[{'id':k,'name':v} for k,v in ts.items()],'matches':games}
 os.makedirs(out,exist_ok=True)
 with open(os.path.join(out,'stats.json'),'w') as f:json.dump(data,f,ensure_ascii=False,indent=2)
 print('Exported',len(people),'players',len(games),'validated matches',sum(len(p['finishes']) for p in people),'individual finishes')
if __name__=='__main__':main(sys.argv[1],sys.argv[2])
