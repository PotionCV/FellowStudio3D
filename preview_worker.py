"""Coalesced, progressive preview. Export continues to use exact engine.poses."""
import engine as E
import rounded_scene as S
VIEWS=((0,0),(90,0),(45,0),(45,30))
_control=None
_progress=None
def init_progress(control,progress):
 global _control,_progress
 _control=control;_progress=progress
 # A closed window may stop consuming partials. Never keep a worker alive just
 # waiting for its progress queue's feeder to flush into that abandoned window.
 _progress.cancel_join_thread()
def current(revision):return _control is None or _control.value==revision
def frame_images(seq,settings,frame):return {(v,frame):E.rgba(seq[frame],settings,cam) for v,cam in enumerate(VIEWS)}
def compile_preview(project):
 seq=E.poses(project)
 return seq,{key:value for i in range(len(seq)) for key,value in frame_images(seq,project.get('render'),i).items()}
def progressive_preview(project,revision,frame=0):
 try:return _progressive_preview(project,revision,frame)
 except E.PreviewCancelled:return None

def _progressive_preview(project,revision,frame):
 if not current(revision):return None
 # Pose controls first; don't make the user wait for the entire spring warm-up.
 cancel=lambda:not current(revision)
 motion={k:v for k,v in project.items() if k not in ('name','render','export_view','auto_name_key','assets3d','camera_y')}
 authored=E.authored(motion,cancel);bundle=S.assets(project)
 def visible(seq):
  return [dict(pose,_assets3d=bundle,**({'_camera_y':project['camera_y']} if project.get('camera_y') else {})) for pose in seq]
 draft=visible(authored)
 frame%=len(draft);settings=project.get('render')
 images=frame_images(draft,settings,frame)
 if not current(revision):return None
 if _progress is not None:_progress.put((revision,draft,dict(images),False))
 physical=E.physical(authored,motion,cancel)
 seq=draft if physical is authored else visible(physical)
 if not current(revision):return None
 if seq is not draft:images=frame_images(seq,settings,frame)
 if _progress is not None:_progress.put((revision,seq,dict(images),True))
 for offset in range(1,len(seq)):
  if not current(revision):return None
  i=(frame+offset)%len(seq)
  chunk=frame_images(seq,settings,i);images.update(chunk)
  if _progress is not None:_progress.put((revision,seq,chunk,True))
 return seq,images
