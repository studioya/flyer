const TAU=Math.PI*2;
function star(n,R,r,bow,rot=-Math.PI/2){const o=[];for(let k=0;k<n;k++){const a=rot+k*TAU/n,b=a+TAU/(2*n);const tip=[R*Math.cos(a),R*Math.sin(a)],w1=[r*Math.cos(a-TAU/(2*n)),r*Math.sin(a-TAU/(2*n))],w2=[r*Math.cos(b),r*Math.sin(b)];
 const seg=(A,B)=>{const L=Math.hypot(B[0]-A[0],B[1]-A[1]),mx=(A[0]+B[0])/2,my=(A[1]+B[1])/2;let nx=-(B[1]-A[1])/L,ny=(B[0]-A[0])/L;if(mx*nx+my*ny<0){nx=-nx;ny=-ny}for(let j=0;j<16;j++){const t=j/16,off=bow*L*4*t*(1-t);o.push([A[0]+(B[0]-A[0])*t+nx*off,A[1]+(B[1]-A[1])*t+ny*off])}};
 seg(w1,tip);seg(tip,w2);}return o}
// radius of a star-shaped polygon along the ray at angle th
function rayR(poly,th){const d=[Math.cos(th),Math.sin(th)];let best=Infinity;for(let i=0;i<poly.length;i++){const a=poly[i],b=poly[(i+1)%poly.length];const e=[b[0]-a[0],b[1]-a[1]];const den=d[0]*e[1]-d[1]*e[0];if(Math.abs(den)<1e-12)continue;const t=(a[0]*e[1]-a[1]*e[0])/den,u=(a[0]*d[1]-a[1]*d[0])/den;if(t>0&&u>=0&&u<=1)best=Math.min(best,t)}return best}
const band=0.08,Rc=0.86,rout=Rc-band/2,h=band/2;
const S=star(6,Rc-0.02,0.25,0.09);
const Sbig=star(6,Rc+0.25,0.25+band*1.6,0.09);
const out=[S];
for(let k=0;k<6;k++){
  const a0=-Math.PI/2+k*TAU/6+0,a1=a0+TAU/6;   // between tip k and tip k+1
  const N=80, inner=[], outer=[];
  for(let j=0;j<=N;j++){const th=a0+(a1-a0)*j/N;const rin=rayR(Sbig,th);
    if(rin<rout-0.02){inner.push([rin*Math.cos(th),rin*Math.sin(th),th]);}}
  if(!inner.length)continue;
  const t0=inner[0][2],t1=inner[inner.length-1][2];
  for(let j=0;j<=40;j++){const th=t1-(t1-t0)*j/40;outer.push([rout*Math.cos(th),rout*Math.sin(th)])}
  out.push(inner.map(p=>[p[0],p[1]]).concat(outer));
}
console.log(JSON.stringify(out.map(a=>a.map(p=>[+p[0].toFixed(3),+p[1].toFixed(3)]))));
