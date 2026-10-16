// Drops a marker named MARKER_NAME (default 'DECIDE') on every judgement moment of plan.json (marks[].frame in the new sequence, marks[].why as the comment).
var MARKER_NAME = 'DECIDE';   // the label every judgement marker gets - change it to your own
var PROJECT_HINT = '__PROJECT_HINT__', DST_ID = '__DST_ID__', PLAN = '__PLAN_PATH__';
var p = app.project; if (!p || String(p.path).indexOf(PROJECT_HINT) < 0) { return JSON.stringify({error: 'wrong project'}); }
var D = null; for (var i = 0; i < p.sequences.numSequences; i++) { if (p.sequences[i].sequenceID == DST_ID) D = p.sequences[i]; }
var f = new File(PLAN); f.encoding = 'UTF-8'; f.open('r'); var P = JSON.parse(f.read()); f.close();
var FR = Number(P.ticks_per_frame), name = MARKER_NAME, n = 0;
for (var q = 0; q < P.marks.length; q++) { var m = D.markers.createMarker(P.marks[q].frame * FR / 254016000000); m.name = name; m.comments = P.marks[q].why; try { m.setColorByIndex(1); } catch (e) {} n++; }
p.save(); return JSON.stringify({markers: n});
