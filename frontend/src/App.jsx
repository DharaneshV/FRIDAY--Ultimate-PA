import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Shield, 
  Cpu, 
  Activity, 
  Globe, 
  Terminal, 
  Bell, 
  Zap, 
  Radio,
  Box
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Components
// ---------------------------------------------------------------------------

const ArcReactor = ({ isActive }) => (
  <div className="relative flex items-center justify-center w-64 h-64">
    {/* Outer Ring */}
    <motion.div 
      animate={{ rotate: 360 }}
      transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
      className="absolute w-full h-full border-2 border-stark-blue/20 rounded-full border-dashed"
    />
    
    {/* Inner Rotating Rings */}
    <motion.div 
      animate={{ rotate: -360 }}
      transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
      className="absolute w-4/5 h-4/5 border border-stark-blue/40 rounded-full"
    >
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-2 h-2 bg-stark-blue rounded-full shadow-[0_0_10px_#00f2ff]" />
    </motion.div>

    {/* The Core */}
    <motion.div 
      animate={{ 
        scale: isActive ? [1, 1.1, 1] : 1,
        opacity: isActive ? 1 : 0.6
      }}
      transition={{ duration: 0.5, repeat: isActive ? Infinity : 0 }}
      className={`w-32 h-32 rounded-full flex items-center justify-center bg-stark-blue/10 border-4 border-stark-blue shadow-[0_0_50px_rgba(0,242,255,0.3)] transition-all duration-500`}
    >
      <div className="w-24 h-24 rounded-full border-2 border-stark-blue/50 flex items-center justify-center">
        <Zap className={`w-12 h-12 ${isActive ? 'text-stark-blue' : 'text-stark-blue/40'} drop-shadow-[0_0_8px_#00f2ff]`} />
      </div>
    </motion.div>

    {/* HUD Elements around core */}
    {[0, 60, 120, 180, 240, 300].map((deg) => (
      <div 
        key={deg}
        className="absolute w-1 h-4 bg-stark-blue/60"
        style={{ transform: `rotate(${deg}deg) translateY(-140px)` }}
      />
    ))}
  </div>
);

const DiagnosticCard = ({ icon: Icon, label, value, color = "text-stark-blue" }) => (
  <div className="glass p-4 rounded-lg flex items-center space-x-4 border-l-4" style={{ borderColor: value?.status === 'warning' ? '#ff003c' : '#00f2ff' }}>
    <div className="p-2 bg-white/5 rounded">
      <Icon className={`w-6 h-6 ${color}`} />
    </div>
    <div>
      <div className="text-xs uppercase tracking-widest text-white/50">{label}</div>
      <div className={`text-xl font-orbitron font-bold ${color}`}>{value || '---'}</div>
    </div>
  </div>
);

// ---------------------------------------------------------------------------
// Main Dashboard
// ---------------------------------------------------------------------------

export default function App() {
  const [socket, setSocket] = useState(null);
  const [telemetry, setTelemetry] = useState({
    cpu: "0%",
    ram: "0%",
    status: "STANDBY",
    uptime: "00:00:00",
    projects: "Scanning...",
    lastAction: "Awaiting Uplink..."
  });
  const [logs, setLogs] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const logContainerRef = useRef(null);

  useEffect(() => {
    // Connect to Friday WebSocket
    const ws = new WebSocket('ws://localhost:8000/ws/friday');
    
    ws.onopen = () => {
      setLogs(prev => [...prev, { time: new Date().toLocaleTimeString(), msg: "SYSTEM: UPLINK ESTABLISHED", type: "system" }]);
      setTelemetry(prev => ({ ...prev, status: "READY" }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleIncomingData(data);
    };

    ws.onclose = () => {
      setLogs(prev => [...prev, { time: new Date().toLocaleTimeString(), msg: "SYSTEM: UPLINK LOST", type: "error" }]);
      setTelemetry(prev => ({ ...prev, status: "OFFLINE" }));
    };

    setSocket(ws);
    return () => ws.close();
  }, []);

  const handleIncomingData = (payload) => {
    if (payload.type === 'telemetry') {
      setTelemetry(prev => ({ ...prev, ...payload.data }));
      setIsListening(true);
      setTimeout(() => setIsListening(false), 2000);
    }
    
    if (payload.type === 'action' || payload.msg) {
      setLogs(prev => [...prev.slice(-49), { 
        time: new Date().toLocaleTimeString(), 
        msg: payload.msg || payload.data.action, 
        type: payload.type || "agent" 
      }]);
    }
  };

  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="h-screen w-screen p-8 text-white font-inter flex flex-col relative overflow-hidden bg-stark-dark">
      <div className="scanline" />
      
      {/* Background Grid */}
      <div className="absolute inset-0 opacity-10" style={{ backgroundImage: 'radial-gradient(circle, #00f2ff 1px, transparent 1px)', backgroundSize: '40px 40px' }} />

      {/* Header */}
      <header className="flex justify-between items-center mb-12 z-20">
        <div className="flex items-center space-x-4">
          <div className="w-10 h-10 bg-stark-blue flex items-center justify-center rounded-sm rotate-45">
            <Shield className="w-6 h-6 text-stark-dark -rotate-45" />
          </div>
          <div>
            <h1 className="text-3xl font-orbitron font-black tracking-tighter text-stark-blue italic">F.R.I.D.A.Y.</h1>
            <p className="text-[10px] tracking-[0.3em] uppercase opacity-50">Command Center HUD v2.0</p>
          </div>
        </div>
        <div className="flex items-center space-x-6 text-xs font-orbitron">
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${telemetry.status === 'READY' ? 'bg-stark-blue shadow-[0_0_8px_#00f2ff]' : 'bg-stark-red'} duration-500`} />
            <span className="opacity-70">{telemetry.status}</span>
          </div>
          <div className="opacity-50">|</div>
          <div className="flex items-center space-x-2">
            <Radio className="w-4 h-4 text-stark-blue" />
            <span>SESSION: {telemetry.uptime}</span>
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <main className="flex-1 grid grid-cols-12 gap-8 z-20 overflow-hidden">
        
        {/* Left Panel: Metrics */}
        <section className="col-span-3 flex flex-col space-y-4">
          <div className="text-[10px] font-orbitron uppercase tracking-widest text-stark-blue/60 mb-2 border-l-2 border-stark-blue pl-2">System Telemetry</div>
          <DiagnosticCard icon={Cpu} label="Neural Load" value={telemetry.cpu} />
          <DiagnosticCard icon={Activity} label="Buffer Usage" value={telemetry.ram} />
          <DiagnosticCard icon={Globe} label="Grid Status" value="Online" />
          <DiagnosticCard icon={Box} label="Lab Inventory" value={telemetry.projects} />
          
          <div className="flex-1 glass mt-4 p-4 overflow-hidden rounded-lg flex flex-col uppercase font-orbitron text-[10px]">
             <div className="text-stark-blue/50 mb-2 border-b border-white/10 pb-1">Sensor Calibration</div>
             <div className="space-y-2 opacity-70">
                <div className="flex justify-between"><span>Vortex Field</span><span className="text-stark-blue">Optimal</span></div>
                <div className="flex justify-between"><span>Stark Link</span><span className="text-stark-blue">Secure</span></div>
                <div className="flex justify-between"><span>IM-9 Status</span><span className="text-stark-blue">Offline</span></div>
                <div className="flex justify-between"><span>Satellite</span><span className="text-stark-blue">Pending</span></div>
             </div>
             <motion.div 
              animate={{ opacity: [0.3, 1, 0.3] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="mt-auto h-1 w-full bg-stark-blue/20 rounded overflow-hidden"
             >
                <div className="h-full w-1/3 bg-stark-blue shadow-[0_0_10px_#00f2ff]" />
             </motion.div>
          </div>
        </section>

        {/* Center: Arc Reactor */}
        <section className="col-span-6 flex flex-col items-center justify-center relative">
          <ArcReactor isActive={isListening} />
          <div className="mt-12 text-center">
            <motion.div 
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 3, repeat: Infinity }}
              className="text-sm font-orbitron tracking-[.5em] text-white/40 uppercase"
            >
              Uplink Active
            </motion.div>
            <div className="mt-2 h-[1px] w-48 bg-gradient-to-r from-transparent via-stark-blue/50 to-transparent" />
          </div>
        </section>

        {/* Right Panel: Logs & Terminal */}
        <section className="col-span-3 flex flex-col overflow-hidden">
          <div className="text-[10px] font-orbitron uppercase tracking-widest text-stark-blue/60 mb-2 border-l-2 border-stark-blue pl-2">Communication Uplink</div>
          <div className="flex-1 glass rounded-lg overflow-hidden flex flex-col">
            <div className="bg-white/5 p-2 flex items-center justify-between">
              <Terminal className="w-4 h-4 text-stark-blue/60" />
              <div className="h-2 w-2 rounded-full bg-stark-blue animate-pulse" />
            </div>
            <div 
              ref={logContainerRef}
              className="flex-1 p-4 font-mono text-[11px] space-y-2 overflow-y-auto"
            >
              {logs.map((log, i) => (
                <div key={i} className={`flex space-x-2 ${log.type === 'error' ? 'text-stark-red' : log.type === 'system' ? 'text-stark-amber' : 'text-stark-blue/80'}`}>
                  <span className="opacity-30">[{log.time}]</span>
                  <span>{log.msg}</span>
                </div>
              ))}
            </div>
          </div>
          
          <div className="mt-4 glass p-4 rounded-lg flex items-center justify-between">
             <div className="flex items-center space-x-3">
                <Bell className="w-4 h-4 text-stark-amber" />
                <span className="text-[10px] font-bold uppercase tracking-widest opacity-60">System Alerts</span>
             </div>
             <span className="text-[10px] font-orbitron text-stark-amber">0 Active</span>
          </div>
        </section>
      </main>
      
      {/* Footer Decoration */}
      <footer className="h-8 mt-4 flex items-center justify-between px-4 border-t border-white/5 z-20">
         <div className="flex items-center space-x-4 opacity-30 text-[9px] font-orbitron tracking-tighter uppercase">
            <span>Protocol: STARK-X</span>
            <span>Auth: Iron-Mon</span>
         </div>
         <div className="flex items-center space-x-4 opacity-30 text-[9px] font-orbitron tracking-tighter uppercase">
            <span>Grid Uplink: 12.0.0.1</span>
            <span>Freq: 44.1 KHZ</span>
         </div>
      </footer>
    </div>
  );
}
