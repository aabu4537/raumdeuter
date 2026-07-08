// Procedural, archetype-driven pressing heatmaps (deterministic per player).
/* ---------- procedural heatmap (archetype-driven) ---------- */
function rng(seed){ let s=0; for(const c of seed) s=(s*31+c.charCodeAt(0))>>>0;
  return ()=>{ s=(s*1664525+1013904223)>>>0; return s/4294967296; }; }
function heatParams(p){
  // pitch coords: x 0..100 (own goal→opp goal), y 0..100
  const base = { GK:[12,50,10], DF:[30,50,16], MF:[52,50,22], FW:[74,50,20] }[p.pos];
  let [cx,cy,spread] = base;
  cx += (p.mov-60)*.22;            // movement pushes territory forward
  const press = p.prs/100;
  const wide = /Winger|FB|Wingback|Fullback|Overlap|Wing/i.test(p.arch) ? 30 : 0;
  return { cx:Math.min(88,cx), cy, spread:spread+press*8, wide, press };
}
function genHeat(p){
  const r = rng(p.n), hp = heatParams(p);
  const blobs=[], dots=[];
  const lanes = hp.wide ? [hp.cy-hp.wide, hp.cy+hp.wide*.2] : [hp.cy];
  for(let i=0;i<7;i++){
    const lane = lanes[i%lanes.length];
    blobs.push({ x:hp.cx + (r()-.42)*hp.spread*1.7, y:lane + (r()-.5)*hp.spread*1.6,
      r:7+r()*11, o:.14+r()*.2 });
  }
  const nd = Math.round(24 + hp.press*46);
  for(let i=0;i<nd;i++){
    const lane = lanes[i%lanes.length];
    dots.push({ x:hp.cx + (r()-.4)*hp.spread*2.1, y:lane + (r()-.5)*hp.spread*2.2,
      regain: r() < (p.rgn/300) });
  }
  const clamp=v=>Math.max(3,Math.min(97,v));
  blobs.forEach(b=>{b.x=clamp(b.x);b.y=clamp(b.y);});
  dots.forEach(d=>{d.x=clamp(d.x);d.y=clamp(d.y);});
  return { blobs, dots };
}

/* ---------- formation coordinates (x: 0 own goal → 100 opp goal) ---------- */

export { genHeat, heatParams };
