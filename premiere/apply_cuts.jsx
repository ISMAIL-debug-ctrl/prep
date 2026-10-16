// STEP 6 in Premiere - build the Rough Cut from the Assembly (run through execute_extendscript).
// Fill in PROJECT_HINT (a piece of the project's path), ASSEMBLY_ID, ROUGH_ID (sequence ids) and KEEP
// (kept ranges in whole sequence frames: everything between the cuts of cuts.json), FR = ticks per frame.
// Proven on 2026-10-14 (3 cameras + 3 recorders, 45 pieces, zero mismatches). For hundreds of ranges (tight cut) see
// scripts/tight.py: the bridge times out after 45 s (Premiere keeps working - wait, then resume from the end of V1),
// a nested sequence placed on a video track drags an empty audio piece onto A1 (remove non-.wav audio afterwards),
// and a track item's points must be set in the order outPoint(+2 frames), inPoint, outPoint, end. Prove with verify_rebuild.py.
//
// Method: the Rough Cut (a duplicate of the Assembly, so it keeps track names and mutes) is emptied and every kept
// range is laid down again from the Assembly's own clips. Razor + ripple is avoided: there is no ripple across all
// tracks. After each placement the new track item's inPoint, outPoint and end are set in ticks, because
// projectItem.setInPoint() on an audio-only file lands up to 2 frames off. Camera audio goes to the track 3 below
// its video track (V1->A4 ...); adjust `a:v+3` and the mic track count for another layout.
var PROJECT_HINT = '__PROJECT_HINT__', ASSEMBLY_ID = '__ASSEMBLY_ID__', ROUGH_ID = '__ROUGH_ID__';
var FR = 4237833600, MIC_TRACKS = 3, KEEP = [/* [startFrame, endFrame], ... */];
var p = app.project; if (!p || String(p.path).indexOf(PROJECT_HINT) < 0) { return JSON.stringify({error: 'wrong project'}); }
var A = null, R = null;
for (var i = 0; i < p.sequences.numSequences; i++) { var s = p.sequences[i]; if (s.sequenceID == ASSEMBLY_ID) A = s; if (s.sequenceID == ROUGH_ID) R = s; }
if (!A || !R) return JSON.stringify({error: 'sequences not found'});
function T(ticks) { var t = new Time(); t.ticks = String(ticks); return t; }
function clear(tr) { for (var k = tr.clips.numItems - 1; k >= 0; k--) tr.clips[k].remove(false, false); }
for (var v = 0; v < R.videoTracks.numTracks; v++) clear(R.videoTracks[v]);
for (var a = 0; a < R.audioTracks.numTracks; a++) clear(R.audioTracks[a]);
var src = [];
for (var v = 0; v < A.videoTracks.numTracks; v++) { var tr = A.videoTracks[v]; for (var k = 0; k < tr.clips.numItems; k++) { var c = tr.clips[k];
  src.push({kind: 'cam', v: v, a: v + MIC_TRACKS, item: c.projectItem, s: Number(c.start.ticks), e: Number(c.end.ticks), inp: Number(c.inPoint.ticks), name: c.name}); } }
for (var a = 0; a < MIC_TRACKS; a++) { var tr = A.audioTracks[a]; for (var k = 0; k < tr.clips.numItems; k++) { var c = tr.clips[k];
  src.push({kind: 'mic', a: a, item: c.projectItem, s: Number(c.start.ticks), e: Number(c.end.ticks), inp: Number(c.inPoint.ticks), name: c.name}); } }
var pos = 0, log = [], want = [];
function fix(tr, dest, sin, sout, label) { var c = tr.clips[tr.clips.numItems - 1]; c.inPoint = T(sin); c.outPoint = T(sout); c.end = T(dest + (sout - sin));
  want.push({tr: tr, idx: tr.clips.numItems - 1, s: dest, e: dest + (sout - sin), i: sin, label: label}); }
for (var r = 0; r < KEEP.length; r++) { var ks = KEEP[r][0] * FR, ke = KEEP[r][1] * FR;
  for (var j = 0; j < src.length; j++) { var c = src[j]; var os = Math.max(ks, c.s), oe = Math.min(ke, c.e); if (oe - os < FR) continue;
    var sin = c.inp + (os - c.s), sout = sin + (oe - os), dest = pos + (os - ks);
    try { c.item.setInPoint(String(sin), 4); c.item.setOutPoint(String(sout), 4);
      if (c.kind == 'cam') { R.overwriteClip(c.item, T(dest), c.v, c.a); fix(R.videoTracks[c.v], dest, sin, sout, 'V' + (c.v + 1) + ' ' + c.name + ' r' + r); fix(R.audioTracks[c.a], dest, sin, sout, 'A' + (c.a + 1) + ' ' + c.name + ' r' + r); }
      else { R.audioTracks[c.a].overwriteClip(c.item, T(dest)); fix(R.audioTracks[c.a], dest, sin, sout, 'A' + (c.a + 1) + ' ' + c.name + ' r' + r); }
      c.item.clearInPoint(4); c.item.clearOutPoint(4); } catch (e) { log.push(c.name + ' r' + r + ' ERR ' + e); } }
  pos += (ke - ks); }
// proof: every piece read back in ticks against where it was meant to be
var bad = []; for (var w = 0; w < want.length; w++) { var x = want[w]; var c = x.tr.clips[x.idx];
  if (Number(c.start.ticks) != x.s || Number(c.end.ticks) != x.e || Number(c.inPoint.ticks) != x.i) bad.push([x.label, Number(c.start.ticks) - x.s, Number(c.end.ticks) - x.e, Number(c.inPoint.ticks) - x.i]); }
p.save();
return JSON.stringify({log: log, placed: want.length, mismatches: bad, totalFrames: pos / FR});
