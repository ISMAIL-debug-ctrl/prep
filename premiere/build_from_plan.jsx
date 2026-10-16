// STEP 7 in Premiere - build the Tight sequence from the Rough Cut and plan.json, a batch at a time.
// Run it again and again: it finds where the target ends and continues; it answers {done:true} when finished.
// The bridge gives up after 45 s but Premiere keeps working - wait for it, then run again (N ranges per call).
// On the final call it removes audio pieces that are not on that track in the source (a nested sequence drags an
// empty audio piece along) . Then: dump_sequence.jsx on the target -> verify_rebuild.py -> fix_pieces.jsx -> add_markers.jsx.
var PROJECT_HINT = '__PROJECT_HINT__', SRC_ID = '__SRC_ID__', DST_ID = '__DST_ID__', PLAN = '__PLAN_PATH__', N = 40;
var p = app.project; if (!p || String(p.path).indexOf(PROJECT_HINT) < 0) { return JSON.stringify({error: 'wrong project'}); }
var R = null, D = null; for (var i = 0; i < p.sequences.numSequences; i++) { var s = p.sequences[i]; if (s.sequenceID == SRC_ID) R = s; if (s.sequenceID == DST_ID) D = s; }
var f = new File(PLAN); f.encoding = 'UTF-8'; f.open('r'); var P = JSON.parse(f.read()); f.close();
var FR = Number(P.ticks_per_frame); function T(t) { var x = new Time(); x.ticks = String(t); return x; }
var v1 = D.videoTracks[0]; var cur = v1.clips.numItems ? Number(v1.clips[v1.clips.numItems - 1].end.ticks) : 0;
var pos = 0, A0 = -1; for (var r = 0; r < P.keep.length; r++) { if (pos == cur) { A0 = r; break; } pos += (P.keep[r][1] - P.keep[r][0]) * FR; }
if (A0 < 0 && pos == cur) A0 = P.keep.length;
if (A0 < 0) return JSON.stringify({error: 'end of V1 is not on a range boundary', cur: cur / FR});
if (A0 >= P.keep.length) {                                     // finished: clean stray audio
  var removed = 0;
  for (var t = 0; t < D.audioTracks.numTracks; t++) { var names = {}; var st = R.audioTracks[t];
    if (st) for (var k = 0; k < st.clips.numItems; k++) names[st.clips[k].name] = 1;
    var tr = D.audioTracks[t]; for (var k = tr.clips.numItems - 1; k >= 0; k--) { if (!names[tr.clips[k].name]) { tr.clips[k].remove(false, false); removed++; } } }
  p.save(); return JSON.stringify({done: true, endFrames: cur / FR, strayAudioRemoved: removed});
}
var src = []; function grab(tracks, kind) { for (var t = 0; t < tracks.numTracks; t++) { var tr = tracks[t]; for (var k = 0; k < tr.clips.numItems; k++) { var c = tr.clips[k];
  src.push({kind: kind, t: t, item: c.projectItem, s: Number(c.start.ticks), e: Number(c.end.ticks), inp: Number(c.inPoint.ticks), name: c.name}); } } }
grab(R.videoTracks, 'v'); grab(R.audioTracks, 'a');
var n = 0, log = [], A1 = Math.min(A0 + N, P.keep.length);
for (var r = A0; r < A1; r++) { var ks = P.keep[r][0] * FR, ke = P.keep[r][1] * FR;
  for (var j = 0; j < src.length; j++) { var c = src[j]; var os = Math.max(ks, c.s), oe = Math.min(ke, c.e); if (oe - os < FR) continue;
    var sin = c.inp + (os - c.s), sout = sin + (oe - os), dest = pos + (os - ks); var tr = (c.kind == 'v' ? D.videoTracks[c.t] : D.audioTracks[c.t]);
    try { c.item.setInPoint(String(sin), 4); c.item.setOutPoint(String(sout), 4); tr.overwriteClip(c.item, T(dest)); c.item.clearInPoint(4); c.item.clearOutPoint(4);
      var x = tr.clips[tr.clips.numItems - 1]; x.outPoint = T(sout + 2 * FR); x.inPoint = T(sin); x.outPoint = T(sout); x.end = T(dest + (oe - os)); n++;
    } catch (e) { log.push(r + ' ' + c.name + ' ' + e); } }
  pos += (ke - ks); }
p.save(); return JSON.stringify({from: A0, to: A1, of: P.keep.length, placed: n, log: log.slice(0, 3)});
