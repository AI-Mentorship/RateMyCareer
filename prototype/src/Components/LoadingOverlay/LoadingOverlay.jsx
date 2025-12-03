import React, { useEffect, useState, useRef } from 'react';
import ReactDOM from 'react-dom';
import './LoadingOverlay.css';

export default function LoadingOverlay(){
  const [visible, setVisible] = useState(false);
  const countRef = useRef(0);
  const timeoutRef = useRef(null);

  useEffect(()=>{
    function onStart(e){
      countRef.current += 1;
      // show overlay immediately when at least one request
      setVisible(true);
      // clear any pending hide timeout
      if(timeoutRef.current){ clearTimeout(timeoutRef.current); timeoutRef.current = null }
    }
    function onEnd(e){
      // decrement and hide when zero
      countRef.current = Math.max(0, countRef.current - 1);
      if(countRef.current === 0){
        // small delay to avoid flicker for very short requests
        timeoutRef.current = setTimeout(()=>{ setVisible(false); timeoutRef.current = null }, 200);
      }
    }
    window.addEventListener('app:loadingStart', onStart);
    window.addEventListener('app:loadingEnd', onEnd);
    return ()=>{
      window.removeEventListener('app:loadingStart', onStart);
      window.removeEventListener('app:loadingEnd', onEnd);
      if(timeoutRef.current) clearTimeout(timeoutRef.current);
    }
  }, []);

  if(!visible) return null;

  return ReactDOM.createPortal(
    <div className="app-loading-overlay" role="status" aria-live="polite">
      <div className="overlay-backdrop" />
      <div className="overlay-content">
        <div className="spinner" />
        <div className="overlay-text">Loading...</div>
      </div>
    </div>,
    document.body
  )
}
