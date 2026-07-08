import { useState, useEffect, useRef } from "react";

function useTween(value, ms=550){
  const [v,setV]=useState(value); const ref=useRef(value);
  useEffect(()=>{
    const from=ref.current, to=value, t0=performance.now();
    if(from===to) return;
    let raf;
    const step=t=>{ const k=Math.min(1,(t-t0)/ms), e=1-Math.pow(1-k,3);
      setV(from+(to-from)*e); if(k<1) raf=requestAnimationFrame(step); else ref.current=to; };
    raf=requestAnimationFrame(step);
    return ()=>cancelAnimationFrame(raf);
  },[value,ms]);
  return v;
}
const mix=(c1,c2,t)=>{
  const h=c=>[parseInt(c.slice(1,3),16),parseInt(c.slice(3,5),16),parseInt(c.slice(5,7),16)];
  const a=h(c1),b=h(c2);
  return `rgb(${a.map((v,i)=>Math.round(v+(b[i]-v)*t)).join(",")})`;
};

export { useTween, mix };
