// Applies fix.json from verify_rebuild.py --fix: [[audioTrackIndex, startTicks, inTicks, outTicks, endTicks], ...]
// Order matters: outPoint (+2 frames) -> inPoint -> outPoint -> end, or the inPoint stays one frame off.
var PROJECT_HINT = '__PROJECT_HINT__', DST_ID = '__DST_ID__', FIX = '__FIX_PATH__', FR = 4237833600;
var p = app.project; if (!p || String(p.path).indexOf(PROJECT_HINT) < 0) { return JSON.stringify({error: 'wrong project'}); }
var D = null; for (var i = 0; i < p.sequences.numSequences; i++) { if (p.sequences[i].sequenceID == DST_ID) D = p.sequences[i]; }
var f = new File(FIX); f.open('r'); var F = JSON.parse(f.read()); f.close(); function T(t) { var x = new Time(); x.ticks = String(t); return x; }
var ok = 0, nf = 0, still = 0;
for (var q = 0; q < F.length; q++) { var a = F[q]; var tr = D.audioTracks[a[0]]; var c = null;
  for (var k = 0; k < tr.clips.numItems; k++) { if (tr.clips[k].start.ticks == a[1]) { c = tr.clips[k]; break; } }
  if (!c) { nf++; continue; }
  c.outPoint = T(Number(a[3]) + 2 * FR); c.inPoint = T(a[2]); c.outPoint = T(a[3]); c.end = T(a[4]);
  if (c.inPoint.ticks == a[2] && c.end.ticks == a[4]) ok++; else still++; }
p.save(); return JSON.stringify({fixed: ok, notFound: nf, stillWrong: still});
