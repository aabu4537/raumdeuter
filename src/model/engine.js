// Pure prediction engine: no React, no DOM. Fully unit-testable.
import { FIXTURES } from "../data/teams.js";

const POSW = { GK:{a:0,d:1.1}, DF:{a:.35,d:1}, MF:{a:.75,d:.75}, FW:{a:1,d:.3} };
const atkOn  = p => .45*p.fin + .40*p.cre + .15*p.prg;
const atkOff = p => .50*p.mov + .30*p.prs + .20*p.rgn;
const defOff = p => .45*p.cov + .35*p.prs + .20*p.rgn;
const blend = (a,b,al) => (1-al)*a + al*b;
const raumIndex = p => Math.round(.34*p.mov + .28*p.prs + .22*p.rgn + .16*p.cov);

function teamStrength(xi, alpha){
  let aSum=0,aW=0,dSum=0,dW=0, aOn=0, aOf=0, dBase=0, dOf=0;
  for(const p of xi){
    const w = POSW[p.pos];
    if(p.pos==="GK"){ dSum += w.d*p.fin; dW += w.d; dBase += w.d*p.fin; dOf += w.d*p.fin; continue; }
    const ao=atkOn(p), af=atkOff(p), db=p.cov, dfo=defOff(p);
    aSum += w.a*blend(ao,af,alpha); aW += w.a;
    dSum += w.d*blend(db,dfo,alpha); dW += w.d;
    aOn += w.a*ao; aOf += w.a*af; dBase += w.d*db; dOf += w.d*dfo;
  }
  return { atk:aSum/aW, def:dSum/dW, atkOn:aOn/aW, atkOff:aOf/aW, defOn:dBase/dW, defOff:dOf/dW };
}

const fact = n => { let f=1; for(let i=2;i<=n;i++) f*=i; return f; };
const pois = (l,k) => Math.exp(-l)*Math.pow(l,k)/fact(k);
const RHO = -0.10;
function dcTau(x,y,lh,la){
  if(x===0&&y===0) return 1 - lh*la*RHO;
  if(x===0&&y===1) return 1 + lh*RHO;
  if(x===1&&y===0) return 1 + la*RHO;
  if(x===1&&y===1) return 1 - RHO;
  return 1;
}
function matchModel(xiH, xiA, alpha){
  const H = teamStrength(xiH, alpha), A = teamStrength(xiA, alpha);
  const lh = Math.exp(Math.log(1.35) + (H.atk - A.def)/12);
  const la = Math.exp(Math.log(1.35) + (A.atk - H.def)/12);
  const N=9; const grid=[]; let z=0;
  for(let x=0;x<N;x++){ grid[x]=[]; for(let y=0;y<N;y++){
    const p = pois(lh,x)*pois(la,y)*dcTau(x,y,lh,la);
    grid[x][y]=Math.max(p,0); z+=grid[x][y];
  }}
  let w=0,d=0,l=0;
  for(let x=0;x<N;x++) for(let y=0;y<N;y++){
    grid[x][y]/=z;
    if(x>y) w+=grid[x][y]; else if(x===y) d+=grid[x][y]; else l+=grid[x][y];
  }
  const tilt = Math.max(-.08, Math.min(.08, ((H.atk+H.def)-(A.atk+A.def))/200));
  const advH = w + d*(.5+tilt);
  return { H, A, lh, la, grid, w, d, l, advH, advA:1-advH, tilt };
}

function sampleScore(model){
  let r=Math.random(), acc=0;
  for(let x=0;x<9;x++) for(let y=0;y<9;y++){ acc+=model.grid[x][y]; if(r<=acc) return [x,y]; }
  return [1,1];
}

/* analytic bracket propagation → champion probabilities */
function bracketProbs(lineups, alpha){
  const win2 = {}; // memo pairwise advance prob
  const adv = (a,b)=>{
    const k=a+"|"+b;
    if(!(k in win2)) win2[k] = matchModel(lineups[a], lineups[b], alpha).advH;
    return win2[k];
  };
  const dist = {}; // fixtureId -> {team: pWin&Reach}
  const entrants = (spec)=>{
    if(typeof spec==="string") return {[spec]:1};
    return dist[spec[0]] || {};
  };
  for(const fx of FIXTURES){
    const Hs=entrants(fx.home), As=entrants(fx.away), out={};
    for(const h in Hs) for(const a in As){
      const p = Hs[h]*As[a];
      out[h]=(out[h]||0)+p*adv(h,a);
      out[a]=(out[a]||0)+p*(1-adv(h,a));
    }
    dist[fx.id]=out;
  }
  return dist["FIN"]; // champion probability by team
}

/* ---------- resolve fixture participants (most likely path for TBD slots) ---------- */
function resolveFixtures(lineups, alpha){
  const winner = {}; // fixtureId -> most likely team code
  const resolved = FIXTURES.map(fx=>{
    const h = typeof fx.home==="string" ? fx.home : winner[fx.home[0]];
    const a = typeof fx.away==="string" ? fx.away : winner[fx.away[0]];
    const m = matchModel(lineups[h], lineups[a], alpha);
    winner[fx.id] = m.advH>=.5 ? h : a;
    return { ...fx, homeTeam:h, awayTeam:a, projected: typeof fx.home!=="string" || typeof fx.away!=="string" };
  });
  return resolved;
}

export { POSW, atkOn, atkOff, defOff, blend, raumIndex, teamStrength,
  dcTau, matchModel, sampleScore, bracketProbs, resolveFixtures, RHO };
