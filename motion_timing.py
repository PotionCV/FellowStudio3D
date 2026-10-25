"""Shared timing for sampling, layer masks and all preview windows."""
import math
MODES=('loop','once','hold')
def mode(project):return project.get('playback','loop') if project.get('playback','loop') in MODES else 'loop'

def interval(entry):
    start=max(0.,min(.99,float(entry.get('start',0.))))
    span=max(.01,min(1.,float(entry['end'])-start)) if 'end' in entry else max(.01,min(1.,float(entry.get('span',1.))))
    return start,span
def sample_time(entry,index,count,project=None):
    kind=entry.get('mode',mode(project or {}))
    progress=index/max(1,count if kind=='loop' else count-1)
    start,span=interval(entry)
    local=(progress-start)/span
    return (local*entry.get('cycles',1)+entry.get('phase',0))%1 if kind=='loop' else max(0.,min(1.,local))
def layer_weight(entry,index,count,project=None):
    progress=index/max(1,count-1);start,span=interval(entry)
    if progress<start:return 0.
    kind=entry.get('mode',mode(project or {}))
    if progress>start+span:return 1. if kind=='hold' else 0.
    fade=max(0.,min(.45,float(entry.get('fade',0.))))
    if not fade:return 1.
    t=(progress-start)/span;ramp=max(0.,min(1.,t/fade,(1-t)/fade if kind!='hold' else 1.))
    return ramp*ramp*(3-2*ramp)
def preview_frame(elapsed,fps,count,project):
    raw=max(0,math.floor(elapsed*fps))
    if mode(project)=='loop':return raw%max(1,count),False
    return min(max(0,count-1),raw),raw>=count
