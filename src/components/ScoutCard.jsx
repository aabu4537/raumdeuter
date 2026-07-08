import React, { useState } from "react";
import { MiniPitch, Radar, StatBars } from "./Charts.jsx";
import { raumIndex } from "../model/engine.js";

function ScoutCard({ ctx, onClose, onSwap, onSlotSwap, alpha, acc }){
  const { player, team, isXI, benchOptions } = ctx;
  const [hov, setHov] = useState(null);
  return (<>
    <div className="overlay" onClick={onClose}/>
    <aside className="scout" role="dialog" aria-label={`Scout report: ${player.n}`}>
      <div className="scout-h">
        <div className="arch">◈ {player.arch}</div>
        <h2 className="disp">{player.n}</h2>
        <div className="meta">{team.name} · {player.pos} · {isXI?"Starting XI":"Bench"}</div>
        <div className="raum-badge">
          <div className="n disp">{raumIndex(player)}</div>
          <div className="l">Raum Index</div>
        </div>
        <button className="scout-x" onClick={onClose} aria-label="Close scout report">✕</button>
      </div>
      <div className="scout-sec">
        <div className="st disp">Territory & pressing map
          <span className="s2">○ pressure · ● regain · procedural, archetype-derived</span></div>
        <MiniPitch player={player} acc={acc}/>
      </div>
      <div className="scout-sec">
        <div className="st disp">Attribute profile <span className="s2">
          {hov ? `dashed: ${hov.n}` : "blue = on-ball · heat = off-ball"}</span></div>
        <StatBars player={player}/>
        <Radar player={player} acc={acc} ghost={hov}/>
      </div>
      {isXI && benchOptions.length>0 && (
        <div className="scout-sec">
          <div className="st disp">Replace in XI <span className="s2">hover to compare · projected Δ at α={alpha.toFixed(2)}</span></div>
          {benchOptions.map(opt=>(
            <button key={opt.player.n} className="swap-row" onClick={()=>onSwap(opt.player)}
              onMouseEnter={()=>setHov(opt.player)} onMouseLeave={()=>setHov(null)}
              onFocus={()=>setHov(opt.player)} onBlur={()=>setHov(null)}>
              <div className="nm disp">{opt.player.n}<span>{opt.player.arch} · Raum {raumIndex(opt.player)}</span></div>
              <div className={"dl mono "+(opt.delta>0.001?"up":opt.delta<-0.001?"dn":"nu")}>
                {opt.delta>0?"▲":opt.delta<0?"▼":"◆"}<b>{(Math.abs(opt.delta)*100).toFixed(1)}%</b>
              </div>
            </button>
          ))}
        </div>
      )}
      {isXI && ctx.teammates && ctx.teammates.length>0 && (
        <div className="scout-sec">
          <div className="st disp">Switch pitch position with <span className="s2">visual repositioning · model weights follow role, not slot</span></div>
          {ctx.teammates.map(t=>(
            <button key={t.n} className="swap-row" onClick={()=>onSlotSwap(t)}>
              <div className="nm disp">{t.n}<span>{t.pos} · {t.arch}</span></div>
              <div className="dl mono nu">⇄</div>
            </button>
          ))}
        </div>
      )}
      {!isXI && <div className="scout-sec" style={{fontSize:12,color:"var(--muted)"}}>
        Select a starter on the pitch to open swap options for this position group.</div>}
    </aside>
  </>);
}

export default ScoutCard;
