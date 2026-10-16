// Writes every clip of one sequence to a text file: 'track|name|start|end|inPoint|mediaPath|enabled' (ticks).
// Used by tight_plan.py (source) and verify_rebuild.py (source and target). Fill in the three values.
var PROJECT_HINT = '__PROJECT_HINT__', SEQ_ID = '__SEQ_ID__', OUT = '__OUT_PATH__';
var p = app.project; if (!p || String(p.path).indexOf(PROJECT_HINT) < 0) { return JSON.stringify({error: 'wrong project'}); }
var S = null; for (var i = 0; i < p.sequences.numSequences; i++) { if (p.sequences[i].sequenceID == SEQ_ID) S = p.sequences[i]; }
if (!S) return JSON.stringify({error: 'sequence not found'});
var o = [];
function add(tracks, k) { for (var t = 0; t < tracks.numTracks; t++) { var tr = tracks[t]; for (var j = 0; j < tr.clips.numItems; j++) { var c = tr.clips[j];
  var mp = ''; try { mp = c.projectItem ? c.projectItem.getMediaPath() : ''; } catch (e) {}
  var en = 'true'; try { en = c.disabled ? 'false' : 'true'; } catch (e) {}
  o.push([k + (t + 1), c.name, c.start.ticks, c.end.ticks, c.inPoint.ticks, mp, en].join('|')); } } }
add(S.videoTracks, 'V'); add(S.audioTracks, 'A');
var f = new File(OUT); f.encoding = 'UTF-8'; f.open('w'); f.write(o.join('\n')); f.close();
return JSON.stringify({clips: o.length});
