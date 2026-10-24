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
 if not current(revision):return None
 # Pose controls first; don't make the user wait for the entire spring warm-up.
 draft=E.authored(project);bundle=S.assets(project)
 for pose in draft:pose['_assets3d']=bundle
 frame%=len(draft);settings=project.get('render')
 images=frame_images(draft,settings,frame)
 if not current(revision):return None
 if _progress is not None:_progress.put((revision,draft,dict(images),False))
 seq=E.poses(project)
 if not current(revision):return None
 images=frame_images(seq,settings,frame)
 if _progress is not None:_progress.put((revision,seq,dict(images),True))
 for i in range(len(seq)):
  if not current(revision):return None
  if i!=frame:
   chunk=frame_images(seq,settings,i);images.update(chunk)
   if _progress is not None:_progress.put((revision,seq,chunk,True))
 return seq,images
