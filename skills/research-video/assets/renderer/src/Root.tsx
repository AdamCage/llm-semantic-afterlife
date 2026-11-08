import React from 'react';
import {AbsoluteFill, Composition, Html5Audio, Img, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import data from './episode.generated.json';

type Scene = (typeof data.scenes)[number];
const clamp = {extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const};
const p = data.palette;

const Reveal: React.FC<React.PropsWithChildren<{delay: number; style?: React.CSSProperties}>> = ({children,delay,style}) => {
  const f=useCurrentFrame(); const {fps}=useVideoConfig();
  return <div style={{opacity:interpolate(f,[delay*fps,(delay+0.6)*fps],[0,1],clamp),translate:`0 ${interpolate(f,[delay*fps,(delay+0.6)*fps],[20,0],clamp)}px`,...style}}>{children}</div>;
};

const SceneView: React.FC<{scene: Scene}> = ({scene}) => {
  const f=useCurrentFrame(); const {fps}=useVideoConfig();
  const asset=('render_asset' in scene ? scene.render_asset : undefined) as string|undefined;
  const caption=('caption' in scene ? scene.caption : '') as string;
  const limitations=('limitations' in scene ? scene.limitations : '') as string;
  const origin=('asset_origin' in scene ? scene.asset_origin : '') as string;
  const label=scene.visual==='figure'?'ДАННЫЕ ИССЛЕДОВАНИЯ':scene.visual==='image'?(origin==='ai'?'ИИ-ИЛЛЮСТРАЦИЯ · метафора':'ИЛЛЮСТРАЦИЯ'):'ОБЪЯСНЯЮЩАЯ СХЕМА';
  return <AbsoluteFill style={{background:p.background,color:p.text,fontFamily:'Segoe UI, Arial, sans-serif',opacity:interpolate(f,[0,0.5*fps,scene.duration-0.5*fps,scene.duration-1],[0,1,1,0],clamp)}}>
    {scene.visual==='image'&&asset&&<><Img src={staticFile(asset)} style={{position:'absolute',width:'100%',height:'100%',objectFit:'cover',scale:interpolate(f,[0,scene.duration],[1,1.04],clamp)}}/><AbsoluteFill style={{background:'linear-gradient(90deg,rgba(5,14,26,.95),rgba(5,14,26,.6) 55%,rgba(5,14,26,.15))'}}/></>}
    <div style={{position:'absolute',left:110,right:110,top:80}}>
      <Reveal delay={0}><div style={{fontSize:27,color:p.accent,letterSpacing:4,textTransform:'uppercase',marginBottom:30}}>{scene.chapter} / {scene.id}</div><div style={{fontSize:84,lineHeight:1.12,fontWeight:600,maxWidth:1500}}>{scene.title}</div></Reveal>
    </div>
    <div style={{position:'absolute',left:110,right:110,top:330,bottom:160}}>
      {scene.visual==='figure'&&asset?<><Img src={staticFile(asset)} style={{width:'100%',height:430,objectFit:'contain'}}/><div style={{fontSize:28,marginTop:14,color:p.muted}}>{caption}</div><div style={{fontSize:25,marginTop:12,color:p.highlight}}>{limitations}</div></>:
      scene.visual==='quote'?<Reveal delay={1} style={{fontFamily:'Georgia,serif',fontSize:54,lineHeight:1.45,maxWidth:1500}}>«{scene.lines.join(' ')}»</Reveal>:
      <div style={{display:'flex',gap:28,alignItems:'stretch'}}>{scene.lines.map((line,i)=><React.Fragment key={i}><Reveal delay={1+i*3} style={{flex:1,padding:'34px 28px',minHeight:250,borderTop:`3px solid ${i%2?p.highlight:p.accent}`,background:scene.visual==='image'?'rgba(8,19,33,.6)':'#112536',borderRadius:14}}><div style={{fontSize:26,color:p.muted,marginBottom:36}}>0{i+1}</div><div style={{fontSize:43,lineHeight:1.3}}>{line}</div></Reveal>{scene.visual==='process'&&i<scene.lines.length-1&&<span style={{fontSize:46,alignSelf:'center',color:p.muted}}>→</span>}</React.Fragment>)}</div>}
    </div>
    <div style={{position:'absolute',left:110,right:110,bottom:65,fontSize:22,color:p.muted,display:'flex',justifyContent:'space-between'}}><span>{label}</span><span>{scene.claim_ids.join(' · ')}</span></div>
    {scene.voice_ready&&<Sequence from={scene.lead} layout="none"><Html5Audio src={staticFile(`voice/${scene.id}.mp3`)}/></Sequence>}
    {(data.storyboard||data.smoke_test)&&<div style={{position:'absolute',right:90,top:30,color:'#ff8c69',fontSize:30}}>{data.smoke_test?'OFFLINE DEMO · SYNTHETIC TONES':'ЧЕРНОВИК · STORYBOARD'}</div>}
  </AbsoluteFill>;
};

const Video: React.FC=()=> <AbsoluteFill style={{background:p.background}}>{data.scenes.map(scene=><Sequence key={scene.id} name={`${scene.id} ${scene.title}`} from={scene.from} durationInFrames={scene.duration}><SceneView scene={scene}/></Sequence>)}{!data.storyboard&&<Html5Audio src={staticFile('score.mp3')}/>}</AbsoluteFill>;
export const Root: React.FC=()=> <Composition id="ResearchVideo" component={Video} durationInFrames={data.duration} fps={data.fps} width={data.width} height={data.height}/>;
