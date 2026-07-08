import React, { useState, useEffect, useRef } from "react";
import { sampleScore } from "../model/engine.js";

function Simulator({ model, H, A }){
  const [sim,setSim]=useState(null);
  const timer=useRef(null);
  useEffect(()=>()=>clearTimeout(timer.current),[]);
  useEffect(()=>{ setSim(null); },[model]);
  const run=()=>{
    clearTimeout(timer.current);
    setSim({ rolling:true, h:0, a:0 });
    const t0=performance.now();
    const spin=()=>{
      if(performance.now()-t0 < 1000){
        setSim({ rolling:true, h:Math.floor(Math.random()*4), a:Math.floor(Math.random()*4) });
        timer.current=setTimeout(spin, 90);
      } else {
        const [h,a]=sampleScore(model);
        let pens=null;
        if(h===a) pens = Math.random() < .5+model.tilt ? "H" : "A";
        setSim({ rolling:false, h, a, pens });
      }
    };
    spin();
  };
  return (
    <div className="simbar">
      <button className="simbtn" onClick={run} disabled={sim&&sim.rolling}>▶ Simulate this match</button>
      {sim && (
        <span className={"sim-score disp mono"+(sim.rolling?" rolling":"")}>
          {H.code} {sim.h}–{sim.a} {A.code}
        </span>
      )}
      {sim && !sim.rolling && (
        <span className="sim-note win disp">
          {sim.pens
            ? `${(sim.pens==="H"?H:A).name} advance on penalties`
            : `${(sim.h>sim.a?H:A).name} advance`}
        </span>
      )}
      {!sim && <span className="sim-note" style={{color:"var(--dim)"}}>one draw from the Dixon-Coles grid</span>}
    </div>
  );
}

export default Simulator;
