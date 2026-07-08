import React from "react";
import { TEAMS, FORMS } from "../data/teams.js";
import { raumIndex } from "../model/engine.js";

function Pitch({ fixture, lineups, onPick, selected, alpha }){
  const H = TEAMS[fixture.homeTeam], A = TEAMS[fixture.awayTeam];
  const render = (team, xi, mirror)=>{
    const coords = FORMS[team.form] || FORMS["433"];
    return xi.map((p,i)=>{
      const [fx,fy]=coords[i]||[50,50];
      const x = mirror ? 100 - fx*0.5 : fx*0.5;      // home occupies left half, away right
      const y = mirror ? 100 - fy : fy;          // mirror laterally so slots keep their side
      const sel = selected && selected.player.n===p.n;
      const last = p.n.split(" ").pop();
      const ri = raumIndex(p)/100;
      const auraR = 2.6 + 7.5*alpha*Math.pow(ri,3);
      const auraO = Math.min(.85, alpha*Math.pow(ri,2)*1.05);
      return (
        <g key={p.n} className={"pdot"+(sel?" sel":"")} transform={`translate(${x},${y*0.66})`}
          onClick={()=>onPick(team.code,p,true)} role="button" tabIndex={0} aria-label={`${p.n}, ${team.name}`}
          onKeyDown={e=>{ if(e.key==="Enter") onPick(team.code,p,true); }}>
          <title>{`${p.n} · ${p.arch} · Raum ${raumIndex(p)}`}</title>
          {(()=>null)()}
          {p.pos!=="GK" && <circle className="aura" r={auraR} fill="url(#heatAura)" opacity={auraO}/>}
          <circle className="body" r="2.6" fill={team.color} stroke="rgba(0,0,0,.5)" strokeWidth="1"/>
          <text y="-3.8" x={x<9?-3.4:x>91?3.4:0} textAnchor={x<9?"start":x>91?"end":"middle"} fontSize="2.3"
            fill="var(--chalk)" fontFamily="Barlow Condensed" fontWeight="700">{last.toUpperCase()}</text>
          <text y="5.9" textAnchor="middle" fontSize="1.9" fill="var(--muted)"
            fontFamily="JetBrains Mono">{raumIndex(p)}</text>
        </g>
      );
    });
  };
  return (
    <div className="pitch-wrap">
      <div className="stadium">
      <svg viewBox="0 0 100 66" className="pitch" role="img" aria-label="Tactical pitch with both starting elevens">
        <defs>
          <radialGradient id="heatAura">
            <stop offset="0%" stopColor="#FF6A3D" stopOpacity=".85"/>
            <stop offset="55%" stopColor="#FFB454" stopOpacity=".35"/>
            <stop offset="100%" stopColor="#FFB454" stopOpacity="0"/>
          </radialGradient>
        </defs>
        <defs>
          <linearGradient id="grass" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#122015"/><stop offset="1" stopColor="#0A130C"/>
          </linearGradient>
        </defs>
        <rect width="100" height="66" fill="url(#grass)"/>
        {[...Array(8)].map((_,i)=>(<rect key={i} x={i*12.5} width="6.25" height="66" fill="rgba(255,255,255,.02)"/>))}
        <g stroke="var(--pitchline)" strokeWidth=".42" fill="none">
          <rect x="1" y="1" width="98" height="64" rx="1.5"/>
          <line x1="50" y1="1" x2="50" y2="65"/>
          <circle cx="50" cy="33" r="7.5"/><circle cx="50" cy="33" r=".6" fill="var(--pitchline)"/>
          <rect x="1" y="18.5" width="13" height="29"/><rect x="86" y="18.5" width="13" height="29"/>
          <rect x="1" y="26" width="4.8" height="14"/><rect x="94.2" y="26" width="4.8" height="14"/>
        </g>
        {render(H, lineups[fixture.homeTeam], false)}
        {render(A, lineups[fixture.awayTeam], true)}
      </svg>
      </div>
      <div className="pitch-hint">Select any player for scout report + swaps. Heat auras = who the model prices up as α rises. Numbers are Raum Index.</div>
    </div>
  );
}

export default Pitch;
