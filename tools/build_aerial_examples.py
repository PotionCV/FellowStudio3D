"""Rebuild only the public swimming/hovering recipes, never personal projects."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import engine as E

def build():
 game=ROOT/'examples/motions/game';game.mkdir(parents=True,exist_ok=True)
 for name,kind,style in (('SwimBreaststroke','swim','breast'),('SwimFrontCrawl','swim','crawl'),('TreadWater','swim','tread'),('Hover','hover',None)):
  project=E.new_project(kind,name=name);project.update(seconds=1.5,fps=16)
  if style:project['base']['style']=style
  E.save(project,game/(name+'.json'))
 fusions=ROOT/'examples/motions/fusions';fusions.mkdir(parents=True,exist_ok=True)
 project=E.new_project('hover',name='HoverWave');project.update(seconds=2.,fps=16)
 wave=E.entry('wave');wave.update(side='left',scope='armL',blend='posture',retain=.15)
 project['layers']=[wave];E.save(project,fusions/'HoverWave.json')
 project=E.new_project('hover',name='FloatingMage');project.update(seconds=2.,fps=16)
 project['base']['params'].update(open=25,beat=4,fold=65,tilt=-8,bob=.8)
 project['controls']={'arms':{'forward':40,'fold':65},'head':{'nod':-8}}
 project['physics']={'head':{'strength':.25,'bounce':.3}}
 E.save(project,fusions/'FloatingMage.json')
 project=E.new_project('swim',name='SwimLookAround');project.update(seconds=2.,fps=16)
 project['base']['style']='tread';head=E.entry('shake');head.update(scope='head',mix=.6,cycles=1)
 project['layers']=[head];E.save(project,fusions/'SwimLookAround.json')

if __name__=='__main__':build()
