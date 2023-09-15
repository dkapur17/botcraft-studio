import React, { useState, useEffect, useRef } from 'react';
import HALO from 'vanta/dist/vanta.halo.min.js';
import * as THREE from 'three';

const FeatureCard = ({title, desc}) => {
    return (
        <div className="card mx-5" style={{background: '#0e1117'}}>
            <div className="card-body p-4">
                <h5 className="card-title text-light">{title}</h5>
                <p className="card-text mt-4" style={{color: 'gray'}}>{desc}</p>
            </div>
        </div>
    )
};

const Landing = ({redirectCallback}) => {
  const [vantaEffect, setVantaEffect] = useState(null)
  const myRef = useRef(null)
  useEffect(() => {
    if (!vantaEffect) {
      setVantaEffect(HALO({
        el: myRef.current,
        mouseControls: true,
        touchControls: true,
        gyroControls: true,
        minHeight: 200.00,
        minWidth: 200.00,
        baseColor: 0x4389dc,
        backgroundColor: 0x0,
        THREE
      }))
    }
    return () => {
      if (vantaEffect) vantaEffect.destroy()
    }
  }, [vantaEffect])
  return (
  <div style={{overflow:"hidden", display:"block", position: "absolute", height: "100%", width: "100%"}} ref={myRef}>
    <div className="d-flex flex-column vh-100 justify-content-evenly" style={{background: 'rgba(0,0,0,0.5)'}}>
       <div className='mt-5'>
       <h1 className="main-header">BotCraft Studio</h1>
        <p className="sub-header">Your gateway to simplicity and efficiency - Create custom AI-Bots trained on your documents.</p>
        <p className="desc">Now supports .txt, .pdf, .docx, .mp4, .wav, .mp3, and several more to come...</p>
        <div className="d-flex flex-row justify-content-center my-5">
            <button className="btn btn-primary btn-sm mt-2" onClick={redirectCallback}>Try it Now!</button>
        </div>
       </div>
    </div>
  </div>)
}

export default Landing;