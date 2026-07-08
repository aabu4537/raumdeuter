import React, { useMemo } from "react";
import { genHeat } from "../model/heatmap.js";
import { matchModel, raumIndex } from "../model/engine.js";

function MiniPitch({ player, acc }){
  const { blobs, dots } = useMemo(()=>genHeat(player),[player]);
  return (
    <svg viewBox="0 0 100 64" className="pitch" role="img" aria-label={`Pressing heatmap for ${player.n}`}>
      <rect x="0" y="0" width="100" height="64" rx="3" fill="var(--pitch)"/>
      {[...Array(6)].map((_,i)=>(<rect key={i} x={i*16.7} y="0" width="8.3" height="64" fill="rgba(255,255,255,.012)"/>))}
      <g stroke="var(--pitchline)" strokeWidth=".5" fill="none">
        <rect x="1" y="1" width="98" height="62" rx="2"/>
        <line x1="50" y1="1" x2="50" y2="63"/>
        <circle cx="50" cy="32" r="7"/>
        <rect x="1" y="18" width="12" height="28"/><rect x="87" y="18" width="12" height="28"/>
        <rect x="1" y="25.5" width="4.5" height="13"/><rect x="94.5" y="25.5" width="4.5" height="13"/>
      </g>
      <defs><filter id="blur"><feGaussianBlur stdDeviation="4"/></filter></defs>
      <g filter="url(#blur)">
        {blobs.map((b,i)=>(<circle key={i} cx={b.x} cy={b.y*0.64} r={b.r} fill={acc} opacity={b.o}/>))}
      </g>
      {dots.map((d,i)=>(
        <circle key={i} cx={d.x} cy={d.y*0.64} r="1.1"
          fill={d.regain?"var(--amber)":"none"} stroke={d.regain?"none":"rgba(237,239,230,.75)"} strokeWidth=".55"/>
      ))}
      <text x="3" y="61" fontSize="3.2" fill="var(--dim)" fontFamily="JetBrains Mono">◀ own goal</text>
      <text x="97" y="61" fontSize="3.2" fill="var(--dim)" textAnchor="end" fontFamily="JetBrains Mono">attacking ▶</text>
    </svg>
  );
}

function Radar({ player, acc, ghost }){
  const axes=[["FIN",player.fin],["CRE",player.cre],["PRG",player.prg],["PRS",player.prs],["RGN",player.rgn],["MOV",player.mov]];
  const C=60, R=44;
  const pt=(i,v)=>{ const a=-Math.PI/2 + i*Math.PI/3; return [C+Math.cos(a)*R*v/100, C+Math.sin(a)*R*v/100]; };
  const poly=axes.map((ax,i)=>pt(i,ax[1]).join(",")).join(" ");
  const gAxes = ghost && [ghost.fin,ghost.cre,ghost.prg,ghost.prs,ghost.rgn,ghost.mov];
  const gPoly = ghost && gAxes.map((v,i)=>pt(i,v).join(",")).join(" ");
  return (
    <svg viewBox="0 0 120 120" style={{width:"100%",maxWidth:220,display:"block",margin:"0 auto"}}
      role="img" aria-label={`Attribute radar for ${player.n}`}>
      {[25,50,75,100].map(r=>(
        <polygon key={r} points={axes.map((_,i)=>pt(i,r).join(",")).join(" ")}
          fill="none" stroke="var(--line)" strokeWidth="1"/>
      ))}
      {axes.map((_,i)=>{ const [x,y]=pt(i,100); return <line key={i} x1={C} y1={C} x2={x} y2={y} stroke="var(--line)"/>; })}
      <polygon points={poly} fill={acc} opacity=".22"/>
      <polygon points={poly} fill="none" stroke={acc} strokeWidth="1.6"/>
      {gPoly && <polygon points={gPoly} fill="none" stroke="var(--chalk)" strokeWidth="1.1"
        strokeDasharray="3 2.5" opacity=".85"/>}
      {axes.map((ax,i)=>{ const [x,y]=pt(i,124);
        return <text key={i} x={x} y={y+2} textAnchor="middle" fontSize="7.5"
          fill="var(--muted)" fontFamily="JetBrains Mono">{ax[0]}</text>; })}
    </svg>
  );
}

const STAT_DEFS=[
  ["fin","Finishing / xG threat","on"],["cre","Chance creation","on"],["prg","Ball progression","on"],
  ["prs","Pressures P90","off"],["rgn","Pressure regains","off"],["mov","Space interpretation","off"],["cov","Defensive coverage","off"],
];
function StatBars({ player }){
  return STAT_DEFS.map(([k,label,side])=>(
    <div className="sbar" key={k}>
      <span className="l">{label}</span>
      <span className="bar"><i style={{width:`${player[k]}%`,
        background: side==="off" ? `linear-gradient(90deg,var(--amber),var(--hot))` : `var(--cool)`}}/></span>
      <span className="v mono">{player[k]}</span>
    </div>
  ));
}

function ScoreMatrix({ model, homeCode, awayCode }){
  const N=6;
  let mx=0; for(let x=0;x<N;x++) for(let y=0;y<N;y++) mx=Math.max(mx,model.grid[x][y]);
  const rows=[];
  rows.push(<div key="c" className="mx-lab"/>);
  for(let y=0;y<N;y++) rows.push(<div key={"h"+y} className="mx-lab mono">{awayCode} {y}</div>);
  for(let x=0;x<N;x++){
    rows.push(<div key={"r"+x} className="mx-lab mono">{homeCode} {x}</div>);
    for(let y=0;y<N;y++){
      const p=model.grid[x][y], t=p/mx;
      rows.push(
        <div key={x+"-"+y} className="mx-cell mono" style={{
          background:`color-mix(in srgb, var(--acc) ${Math.round(t*55)}%, var(--panel2))`,
          color: t>.5?"#0C120D":"var(--muted)", fontWeight:t>.5?700:400 }}>
          {(p*100).toFixed(1)}
        </div>
      );
    }
  }
  return <div className="matrix" style={{gridTemplateColumns:`repeat(${N+1},1fr)`}}>{rows}</div>;
}

function Readout({ model, home, away }){
  const row=(label, S)=>{
    const total=S.atkOn+S.atkOff;
    return (
      <div className="readout-row" key={label}>
        <div className="rr-t"><b className="disp">{label} · attack composition</b>
          <span className="mono" style={{color:"var(--muted)"}}>on {S.atkOn.toFixed(1)} / off {S.atkOff.toFixed(1)}</span></div>
        <div className="stack">
          <i style={{width:`${S.atkOn/total*100}%`, background:"var(--cool)"}}/>
          <i style={{width:`${S.atkOff/total*100}%`, background:"linear-gradient(90deg,var(--amber),var(--hot))"}}/>
        </div>
      </div>
    );
  };
  return (
    <div>
      {row(home, model.H)}{row(away, model.A)}
      <div className="readout-row">
        <div className="rr-t"><b className="disp">Expected goals (λ)</b>
          <span className="mono" style={{color:"var(--muted)"}}>{home} {model.lh.toFixed(2)} · {away} {model.la.toFixed(2)}</span></div>
      </div>
      <div className="legend">
        <span><span className="sw" style={{background:"var(--cool)"}}/>on-ball vector (fin·cre·prg)</span>
        <span><span className="sw" style={{background:"var(--hot)"}}/>off-ball vector (mov·prs·rgn)</span>
      </div>
    </div>
  );
}

function AlphaCurve({ xiH, xiA, alpha, homeCode }){
  const pts = useMemo(()=>{
    const a=[]; for(let i=0;i<=20;i++) a.push(matchModel(xiH,xiA,i/20).advH);
    return a;
  },[xiH,xiA]);
  const W=100,Hh=26;
  const y=v=>Hh-2-(v*(Hh-6));
  const path = pts.map((v,i)=>`${i===0?"M":"L"}${(i/20)*W},${y(v)}`).join(" ");
  const cx=alpha*W, cy=y(pts[Math.round(alpha*20)]);
  return (
    <div className="spark-wrap rise d3">
      <div className="spark-top">
        <span>{homeCode} advance % across full α sweep</span>
        <b className="mono">α {alpha.toFixed(2)} → {(pts[Math.round(alpha*20)]*100).toFixed(1)}%</b>
      </div>
      <svg viewBox={`0 0 ${W} ${Hh}`} style={{width:"100%",display:"block"}} aria-hidden="true">
        <defs>
          <linearGradient id="curveG" x1="0" x2="1">
            <stop offset="0" stopColor="var(--cool)"/><stop offset="1" stopColor="var(--hot)"/>
          </linearGradient>
        </defs>
        <line x1="0" x2={W} y1={y(.5)} y2={y(.5)} stroke="var(--line)" strokeDasharray="2 2" strokeWidth=".5"/>
        <path d={path} fill="none" stroke="url(#curveG)" strokeWidth="1.4" strokeLinecap="round"/>
        <line x1={cx} x2={cx} y1="2" y2={Hh-2} stroke="var(--acc)" strokeWidth=".5" opacity=".5"/>
        <circle cx={cx} cy={cy} r="2.2" fill="var(--acc)" stroke="#0C120D" strokeWidth=".8"/>
        <text x="1" y={Hh-1} fontSize="3.4" fill="var(--dim)" fontFamily="JetBrains Mono">box score</text>
        <text x={W-1} y={Hh-1} fontSize="3.4" fill="var(--dim)" textAnchor="end" fontFamily="JetBrains Mono">raumdeuter</text>
        <text x="1" y="5" fontSize="3.2" fill="var(--dim)" fontFamily="JetBrains Mono">50%</text>
      </svg>
    </div>
  );
}

export { MiniPitch, Radar, StatBars, ScoreMatrix, Readout, AlphaCurve };
