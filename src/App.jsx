import React, { useState, useMemo, useCallback, useEffect } from "react";
import { TEAMS } from "./data/teams.js";
import { matchModel, bracketProbs, resolveFixtures, raumIndex, atkOn, atkOff } from "./model/engine.js";
import { useTween, mix } from "./lib/hooks.js";
import { MiniPitch, Radar, StatBars, ScoreMatrix, Readout, AlphaCurve } from "./components/Charts.jsx";
import ScoutCard from "./components/ScoutCard.jsx";
import Pitch from "./components/Pitch.jsx";
import Simulator from "./components/Simulator.jsx";
import Methodology from "./components/Methodology.jsx";

function App(){
  const [alpha, setAlpha] = useState(0.35);
  const [lineups, setLineups] = useState(()=>{
    const o={}; for(const k in TEAMS) o[k]=TEAMS[k].xi.slice(); return o;
  });
  const [benches, setBenches] = useState(()=>{
    const o={}; for(const k in TEAMS) o[k]=TEAMS[k].bench.slice(); return o;
  });
  const [fxId, setFxId] = useState("QF2");
  const [scout, setScout] = useState(null);
  const [tab, setTab] = useState("matrix");
  const [toast, setToast] = useState(null);
  const [method, setMethod] = useState(false);

  const acc = mix("#6FA8C4","#FF6A3D",alpha);
  const acc2 = mix("#8FBDD4","#FFB454",alpha);

  const fixtures = useMemo(()=>resolveFixtures(lineups,alpha),[lineups,alpha]);
  const fixture = fixtures.find(f=>f.id===fxId);
  const model = useMemo(()=>matchModel(lineups[fixture.homeTeam],lineups[fixture.awayTeam],alpha),
    [lineups,fixture.homeTeam,fixture.awayTeam,alpha]);
  const champs = useMemo(()=>bracketProbs(lineups,alpha),[lineups,alpha]);

  const wT = useTween(model.advH*100), dT = useTween(model.d*100);
  const H = TEAMS[fixture.homeTeam], A = TEAMS[fixture.awayTeam];

  const pick = useCallback((teamCode, player, isXI)=>{
    const xi = lineups[teamCode], bench = benches[teamCode];
    let benchOptions = [];
    if(isXI){
      const group = p => p.pos==="GK" ? "GK" : p.pos;
      benchOptions = bench.filter(b=>group(b)===group(player) ||
        (player.pos!=="GK" && b.pos!=="GK" && Math.abs("DF MF FW".indexOf(b.pos)-"DF MF FW".indexOf(player.pos))<=3))
        .filter(b=>b.pos!=="GK" || player.pos==="GK")
        .map(b=>{
          const newXi = xi.map(p=>p.n===player.n?b:p);
          const inMatch = fixture.homeTeam===teamCode || fixture.awayTeam===teamCode;
          let delta=0;
          if(inMatch){
            const nh = teamCode===fixture.homeTeam ? newXi : lineups[fixture.homeTeam];
            const na = teamCode===fixture.awayTeam ? newXi : lineups[fixture.awayTeam];
            const m2 = matchModel(nh,na,alpha);
            delta = teamCode===fixture.homeTeam ? m2.advH-model.advH : m2.advA-model.advA;
          }
          return { player:b, delta };
        })
        .sort((a,b)=>b.delta-a.delta);
    }
    const teammates = isXI && player.pos!=="GK"
      ? xi.filter(p=>p.n!==player.n && p.pos!=="GK") : [];
    setScout({ player, team:TEAMS[teamCode], teamCode, isXI, benchOptions, teammates });
  },[lineups,benches,fixture,model,alpha]);

  const doSwap = useCallback((incoming)=>{
    const { teamCode, player:out } = scout;
    const before = teamCode===fixture.homeTeam ? model.advH : teamCode===fixture.awayTeam ? model.advA : null;
    setLineups(L=>({ ...L, [teamCode]: L[teamCode].map(p=>p.n===out.n?incoming:p) }));
    setBenches(B=>({ ...B, [teamCode]: [...B[teamCode].filter(p=>p.n!==incoming.n), out] }));
    setScout(null);
    if(before!=null){
      const dOff = atkOff(incoming)-atkOff(out), dOn = atkOn(incoming)-atkOn(out);
      setToast({ inN:incoming.n, outN:out.n, team:TEAMS[teamCode].name, before, dOff, dOn, teamCode });
    }
  },[scout,fixture,model]);

  const doSlotSwap = useCallback((other)=>{
    const { teamCode, player } = scout;
    setLineups(L=>{
      const xi=L[teamCode].slice();
      const i=xi.findIndex(p=>p.n===player.n), j=xi.findIndex(p=>p.n===other.n);
      if(i<0||j<0) return L;
      [xi[i],xi[j]]=[xi[j],xi[i]];
      return { ...L, [teamCode]: xi };
    });
    setScout(null);
  },[scout]);

  // finalize toast after state settles
  useEffect(()=>{
    if(!toast || toast.after!=null) return;
    const side = toast.teamCode===fixture.homeTeam ? model.advH : model.advA;
    setToast(t=>({ ...t, after: side }));
  },[model, toast, fixture]);

  const champList = Object.entries(champs).sort((a,b)=>b[1]-a[1]);
  const maxChamp = champList.length? champList[0][1] : 1;

  const resetXIs = useCallback(()=>{
    const L={},B={}; for(const k in TEAMS){ L[k]=TEAMS[k].xi.slice(); B[k]=TEAMS[k].bench.slice(); }
    setLineups(L); setBenches(B); setToast(null); setScout(null);
  },[]);
  const jumpToTeam = useCallback((code)=>{
    const fx = fixtures.find(f=>f.homeTeam===code||f.awayTeam===code);
    if(fx){ setFxId(fx.id); setToast(null); }
  },[fixtures]);

  return (
    <div className="rd-root" style={{"--acc":acc,"--acc2":acc2}}>
      <div className="rd-wrap">

        <div className="bug rise">
          <span><span className="live-dot"/>World Cup 2026 · Knockout stage · Bracket verified Jul 6</span>
          <span>Model mode: <b>{alpha<.15?"Box score":alpha<.55?"Consensus":alpha<.9?"Raumdeuter":"Pure space"}</b></span>
        </div>

        <header className="rd-head">
          <div className="rd-brand rise">
            <h1 className="disp">Raumdeuter</h1>
            <div className="sub"><span className="live-dot"/>The off-ball engine · <b>FIFA World Cup 2026 · live knockout bracket</b> · Merino 90'+2 sent Portugal home. This is why.</div>
          </div>
          <div className="dial rise d1">
            <div className="dial-top">
              <span className="lab">α · off-ball weighting</span>
              <span className="val mono">{alpha.toFixed(2)}</span>
            </div>
            <input type="range" min="0" max="1" step="0.01" value={alpha}
              aria-label="Off-ball weighting alpha"
              onChange={e=>setAlpha(parseFloat(e.target.value))}/>
            <div className="dial-ends"><span className="l">◄ box score</span><span className="r">raumdeuter ►</span></div>
            <div className="presets" role="group" aria-label="Alpha presets">
              {[["Box score",0],["Consensus",0.35],["Raumdeuter",0.8],["Pure space",1]].map(([lab,v])=>(
                <button key={lab} className={"chip"+(Math.abs(alpha-v)<.005?" on":"")}
                  onClick={()=>setAlpha(v)}>{lab}</button>
              ))}
            </div>
          </div>
        </header>

        <p className="lede rise d1">
          <b style={{color:"var(--chalk)"}}>Raumdeuter</b> is German for "space interpreter". Thomas Müller coined
          it for himself: a player whose value lives in movement the box score never records. This engine asks one
          question about the 2026 World Cup: if you price that invisible work, the pressing, the regains, the runs
          that drag defenders out of shape, who actually wins? The α dial is that price. Turn it and watch.
        </p>

        <div className="rd-grid">
          <div>
            <section className="card rise d2" aria-label="Remaining fixtures">
              <div className="card-h"><span className="t disp">Remaining bracket</span><span className="s mono">verified Jul 6</span></div>
              {fixtures.map(fx=>(
                <button key={fx.id} className={"fx"+(fx.id===fxId?" on":"")} onClick={()=>{setFxId(fx.id); setToast(null);}}>
                  <div className="rnd mono">{fx.round} · {fx.when}{fx.projected?" · projected":""}</div>
                  <div className="tms">
                    <span className={"nm disp"+(fx.projected?" tbd":"")}>{TEAMS[fx.homeTeam].code} v {TEAMS[fx.awayTeam].code}</span>
                    <span className="pc mono">{(matchModel(lineups[fx.homeTeam],lineups[fx.awayTeam],alpha).advH*100).toFixed(0)}–
                      {(matchModel(lineups[fx.homeTeam],lineups[fx.awayTeam],alpha).advA*100).toFixed(0)}</span>
                  </div>
                </button>
              ))}
            </section>

            <section className="card rise d3" style={{marginTop:20}} aria-label="Champion probabilities">
              <div className="card-h"><span className="t disp">Lift the trophy</span><span className="s mono">α = {alpha.toFixed(2)}</span></div>
              <div className="champ-list" style={{height:champList.length*30+16, margin:"8px 0"}}>
                {[...champList].sort((a,b)=>a[0]<b[0]?-1:1).map(([code,p])=>{
                  const rank = champList.findIndex(c=>c[0]===code);
                  return (
                    <div className="champ-row clickable" key={code}
                      style={{transform:`translateY(${rank*30+8}px)`}}
                      onClick={()=>jumpToTeam(code)} role="button" tabIndex={0}
                      onKeyDown={e=>{if(e.key==="Enter")jumpToTeam(code);}}
                      aria-label={`${TEAMS[code].name}: ${(p*100).toFixed(1)}% to win. Jump to their next fixture.`}>
                      <span className="nm disp">{code}{rank===0 && <span className="crown">👑</span>}</span>
                      <span className="bar"><i style={{width:`${p/maxChamp*100}%`}}/></span>
                      <span className="pv mono">{(p*100).toFixed(1)}%</span>
                    </div>
                  );
                })}
              </div>
            </section>
          </div>

          <main className="card rise d2">
            <div className="mh">
              <div className="side">
                <span className="team disp">{H.name}</span>
                <span className="pct disp" style={{color:"var(--acc)"}}>{wT.toFixed(1)}%</span>
                <span className="xg mono">λ {model.lh.toFixed(2)} · to advance</span>
              </div>
              <div className="mid">
                <div className="vs mono">{fixture.round}</div>
                <div className="draw mono">draw {dT.toFixed(1)}%</div>
                <div className="vs mono" style={{marginTop:6}}>{fixture.when}</div>
              </div>
              <div className="side away">
                <span className="team disp">{A.name}</span>
                <span className="pct disp" style={{color:"var(--dim)"}}>{(100-wT).toFixed(1)}%</span>
                <span className="xg mono">λ {model.la.toFixed(2)} · to advance</span>
              </div>
            </div>
            <div className="tri" aria-hidden="true">
              <i className="h" style={{width:`${model.w*100}%`}}/>
              <i className="d" style={{width:`${model.d*100}%`}}/>
              <i className="a" style={{width:`${model.l*100}%`}}/>
            </div>
            <div className="tri-lab"><span>win in 90'</span><span>draw</span><span>lose in 90'</span></div>

            <AlphaCurve xiH={lineups[fixture.homeTeam]} xiA={lineups[fixture.awayTeam]}
              alpha={alpha} homeCode={H.code}/>

            {toast && toast.after!=null && (
              <div className="toast" role="status">
                <span className="big">{toast.inN} ▸ IN · {toast.outN} ▸ OUT</span> · {toast.team} advance:{" "}
                <span className="mono">{(toast.before*100).toFixed(1)}%</span> →{" "}
                <span className={"mono big "+(toast.after>=toast.before?"up":"dn")}>{(toast.after*100).toFixed(1)}%</span>
                <div className="why">
                  Off-ball vector {toast.dOff>=0?"+":""}{toast.dOff.toFixed(1)} · on-ball {toast.dOn>=0?"+":""}{toast.dOn.toFixed(1)}.{" "}
                  {toast.dOff>0 && toast.dOn<0 ? "Trading touches for territory. The Raumdeuter trade." :
                   toast.dOff<0 && toast.dOn>0 ? "More box score, less engine. The α dial decides if that pays." :
                   "A shift in profile more than quality. Watch how α reprices it."}
                </div>
              </div>
            )}

            <Pitch fixture={fixture} lineups={lineups} onPick={pick} selected={scout} alpha={alpha}/>

            <Simulator model={model} H={H} A={A}/>

            <div className="tabs" role="tablist">
              <button className={"tab"+(tab==="matrix"?" on":"")} onClick={()=>setTab("matrix")} role="tab">Score matrix</button>
              <button className={"tab"+(tab==="readout"?" on":"")} onClick={()=>setTab("readout")} role="tab">Model readout</button>
            </div>
            <div className="pane">
              {tab==="matrix"
                ? <ScoreMatrix model={model} homeCode={H.code} awayCode={A.code}/>
                : <Readout model={model} home={H.name} away={A.name}/>}
            </div>
          </main>
        </div>

        <footer className="foot">
          <span>RAUMDEUTER · built mid-tournament, July 2026 · bracket verified vs. live results · ratings are curated analyst estimates</span>
          <span style={{display:"flex",gap:16}}>
            <button className="linkish" onClick={resetXIs}>↺ Reset all XIs</button>
            <button className="linkish" onClick={()=>setMethod(true)}>Methodology & honesty notes</button>
          </span>
        </footer>
      </div>

      {scout && <ScoutCard ctx={scout} onClose={()=>setScout(null)} onSwap={doSwap} onSlotSwap={doSlotSwap} alpha={alpha} acc={acc}/>}
      {method && <Methodology onClose={()=>setMethod(false)}/>}
    </div>
  );
}

export default App;
