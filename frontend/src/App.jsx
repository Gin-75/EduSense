import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Activity, CheckCircle2, ChevronRight, XCircle, Beaker, 
  BookOpen, Target, Send, Plus, Award, Briefcase, GraduationCap,
  Sparkles, Zap
} from 'lucide-react';
import { InlineMath, BlockMath } from 'react-katex';
import 'katex/dist/katex.min.css';
import 'mathlive';

const API_BASE_URL = 'http://localhost:8000';

const LatexText = ({ content }) => {
  if (!content) return null;
  
  const parts = content.split(/(\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\))/g);
  
  return (
    <span className="latex-container whitespace-pre-wrap">
      {parts.map((part, index) => {
        if (!part) return null;
        if (part.startsWith('\\[') && part.endsWith('\\]')) {
          const math = part.substring(2, part.length - 2).trim();
          return <div key={index} className="my-2"><BlockMath math={math} /></div>;
        } else if (part.startsWith('\\(') && part.endsWith('\\)')) {
          const math = part.substring(2, part.length - 2).trim();
          return <InlineMath key={index} math={math} />;
        } else {
          return <span key={index}>{part}</span>;
        }
      })}
    </span>
  );
};

function App() {
  const [view, setView] = useState('landing');
  const [session, setSession] = useState(null);
  const [question, setQuestion] = useState(null);
  const [trace, setTrace] = useState([]);
  const [currentStep, setCurrentStep] = useState('');
  const [diagnosis, setDiagnosis] = useState(null);
  const [status, setStatus] = useState('idle');
  const [message, setMessage] = useState('');
  const [studentId, setStudentId] = useState(() => Math.floor(Math.random() * 10000));
  const [pendingNextQuestion, setPendingNextQuestion] = useState(null);
  
  // Curriculum state
  const [subjects, setSubjects] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState('all');

  useEffect(() => {
    const fetchSubjects = async () => {
      try {
        const res = await axios.get(`${API_BASE_URL}/subjects`);
        setSubjects(res.data);
      } catch (err) {
        console.error("Failed to fetch subjects", err);
      }
    };
    fetchSubjects();
  }, []);

  const startSession = async () => {
    // Generate a fresh student ID for each session to prevent mixing history
    const newStudentId = Math.floor(Math.random() * 10000);
    setStudentId(newStudentId);
    
    setStatus('loading');
    setView('workspace');
    setTrace([]);
    setDiagnosis(null);
    try {
      const res = await axios.get(`${API_BASE_URL}/start_session?subject=${selectedSubject}`);
      setQuestion(res.data);
      setStatus('active');
    } catch (err) {
      setStatus('error');
      setMessage('Failed to load assessment. Is the backend running?');
    }
  };

  const addStep = () => {
    if (currentStep.trim()) {
      setTrace([...trace, currentStep.trim()]);
      setCurrentStep('');
    }
  };

  const submitProcess = async (overrideTrace = null) => {
    let finalTrace = overrideTrace;
    
    if (!finalTrace) {
      finalTrace = [...trace];
      if (currentStep.trim()) {
        finalTrace.push(currentStep.trim());
        setCurrentStep('');
      }
    }
    
    if (finalTrace.length === 0) return;
    
    setStatus('loading');
    try {
      const res = await axios.post(`${API_BASE_URL}/submit_process`, {
        student_id: studentId,
        question_id: question.id,
        trace: finalTrace,
        grade_level: "all"
      });

      setDiagnosis(res.data.diagnosis);
      
      if (res.data.status === 'completed') {
        setStatus('completed');
        setMessage(res.data.message);
      } else {
        setStatus('feedback');
        setPendingNextQuestion(res.data.next_question);
      }
    } catch (err) {
      setStatus('error');
      setMessage('Analysis failed. Please try again.');
    }
  };

  const continueToNextQuestion = () => {
    setQuestion(pendingNextQuestion);
    setPendingNextQuestion(null);
    setTrace([]);
    setDiagnosis(null);
    setStatus('active');
  };

  // Katex parser helper
  const getQuestionContent = (text) => {
    if (!text) return '';
    const parts = text.split(':');
    if (parts.length > 1) {
      return parts[1].trim().replace(/\*\*/g, '^').replace(/\*/g, ' ');
    }
    return text.replace(/\*\*/g, '^').replace(/\*/g, ' ');
  };

  // --- UI Components ---

  const Sidebar = () => (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col h-screen fixed top-0 left-0">
      <div className="p-6 flex items-center gap-3 text-white font-bold text-xl border-b border-slate-800">
        <Sparkles className="text-blue-500 h-6 w-6" />
        DiagMath.AI
      </div>
      <div className="flex-1 overflow-y-auto py-6 px-4 space-y-6">
        <div>
          <h4 className="text-xs uppercase tracking-widest text-slate-500 mb-3 font-semibold px-2">Profile</h4>
          <div className="bg-slate-800 rounded-xl p-4 flex items-center gap-3">
            <div className="h-10 w-10 bg-blue-500/20 text-blue-400 rounded-full flex items-center justify-center font-bold">
              ID
            </div>
            <div>
              <div className="text-sm text-white font-semibold">Student #{studentId}</div>
              <div className="text-xs text-slate-400">Egypt Curriculum</div>
            </div>
          </div>
        </div>
        
        <div>
          <h4 className="text-xs uppercase tracking-widest text-slate-500 mb-3 font-semibold px-2">Navigation</h4>
          <nav className="space-y-1">
            <button onClick={() => setView('landing')} className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${view === 'landing' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 hover:text-white'}`}>
              <BookOpen size={18} /> Curriculum
            </button>
            <button className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${view === 'workspace' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800 hover:text-white'}`}>
              <Target size={18} /> Active Session
            </button>
          </nav>
        </div>
      </div>
      <div className="p-6 border-t border-slate-800 text-xs text-slate-500 text-center">
        Powered by EduCDM Neural Networks
      </div>
    </aside>
  );

  const CognitiveProfile = () => {
    
    return (
      <div className="w-80 bg-white border-l border-slate-200 h-screen fixed top-0 right-0 overflow-y-auto flex flex-col shadow-[-10px_0_30px_-15px_rgba(0,0,0,0.05)]">
        <div className="p-6 border-b border-slate-100 bg-slate-50/50">
          <h3 className="text-sm font-bold text-slate-800 uppercase tracking-widest flex items-center gap-2">
            <Activity className="h-4 w-4 text-indigo-600" />
            Neural Mastery
          </h3>
          <p className="text-xs text-slate-500 mt-1 font-medium">Real-time KST Inference</p>
        </div>
        
        <div className="p-6 flex-1">
          {diagnosis?.ncdm_mastery ? (
            <div className="space-y-6">
              {Object.entries(diagnosis.ncdm_mastery.mastery_profile || diagnosis.ncdm_mastery).map(([skill, mastery]) => (
                <div key={skill} className={diagnosis.ncdm_mastery.latest_skills?.includes(skill) ? "bg-indigo-50/50 p-2 -mx-2 rounded-lg border border-indigo-100" : "p-2 -mx-2"}>
                  <div className="flex justify-between text-xs font-bold text-slate-700 mb-2">
                    <span className="flex items-center gap-2">
                      {skill} 
                      {diagnosis.ncdm_mastery.latest_skills?.includes(skill) && <span className="w-2 h-2 rounded-full bg-indigo-500 inline-block animate-pulse"></span>}
                    </span>
                    <span className="text-indigo-600">{Math.round(mastery * 100)}%</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                    <div 
                      className={`h-full rounded-full transition-all duration-1000 ease-out ${
                        mastery > 0.8 ? 'bg-gradient-to-r from-emerald-400 to-emerald-500' : 
                        mastery > 0.4 ? 'bg-gradient-to-r from-indigo-400 to-indigo-500' : 
                        'bg-gradient-to-r from-rose-400 to-rose-500'
                      }`}
                      style={{ width: `${mastery * 100}%` }}
                    ></div>
                  </div>
                </div>
              ))}
              
              {diagnosis.primary_cause && diagnosis.primary_cause !== "No Significant Weakness" && (
                <div className="mt-8 p-5 bg-rose-50 rounded-xl border border-rose-100 shadow-sm relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-1 h-full bg-rose-500"></div>
                  <h4 className="text-[10px] font-bold text-rose-800 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <Zap className="h-3 w-3" />
                    AI Cognitive Bottleneck
                  </h4>
                  <p className="text-sm text-slate-800 font-bold mb-1">{diagnosis.primary_cause}</p>
                  {diagnosis.report && (
                    <p className="text-xs text-slate-600 leading-relaxed font-medium mt-2 p-3 bg-white/60 rounded-lg border border-rose-100/50">
                      {diagnosis.report}
                    </p>
                  )}
                </div>
              )}
              
              {diagnosis.primary_cause === "No Significant Weakness" && (
                <div className="mt-8 p-5 bg-emerald-50 rounded-xl border border-emerald-100 shadow-sm relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-1 h-full bg-emerald-500"></div>
                  <h4 className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider mb-2">Excellent Work</h4>
                  <p className="text-sm text-emerald-700 font-medium">{diagnosis.report || "No cognitive gaps detected in this step."}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center opacity-60">
              <Zap className="h-12 w-12 text-slate-300 mb-4" />
              <p className="text-sm font-medium text-slate-500">Submit an answer to generate your dynamic cognitive profile.</p>
            </div>
          )}
        </div>
      </div>
    );
  };

  // --- Main Layout ---

  return (
    <div className="min-h-screen bg-slate-50 font-sans">
      <Sidebar />
      
      <div className="ml-64 mr-80 min-h-screen flex flex-col">
        {view === 'landing' && (
          <div className="p-12 max-w-4xl mx-auto w-full animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="mb-12">
              <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight mb-3">Diagnostic Placement</h1>
              <p className="text-lg text-slate-500 font-medium">Select your curriculum to initialize the cognitive knowledge space.</p>
            </div>

            <div className="bg-white rounded-3xl p-8 shadow-sm border border-slate-200 mb-10">
              <div className="space-y-3">
                <label className="block text-sm font-bold text-slate-700 uppercase tracking-wider">Select Mathematics Topic</label>
                <select 
                  value={selectedSubject} 
                  onChange={(e) => setSelectedSubject(e.target.value)}
                  className="w-full bg-slate-50 border-2 border-slate-100 rounded-xl px-4 py-4 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 outline-none transition-all font-medium text-slate-700"
                >
                  <option value="all">All Topics (Full Diagnostic)</option>
                  {subjects.map(s => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
                <p className="text-xs text-slate-400 mt-2">Questions are drawn from a real-world diagnostic dataset.</p>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div onClick={startSession} className="group bg-white rounded-3xl p-8 shadow-sm border border-slate-200 hover:shadow-xl hover:border-indigo-300 transition-all cursor-pointer transform hover:-translate-y-1">
                <div className="h-14 w-14 bg-indigo-50 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <Beaker className="h-7 w-7 text-indigo-600" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 mb-2">Adaptive Assessment</h3>
                <p className="text-slate-500 font-medium">Begin an AI-driven session that dynamically probes your weaknesses across the curriculum.</p>
              </div>
              
              <div className="group bg-slate-100 rounded-3xl p-8 border border-slate-200 opacity-60 cursor-not-allowed">
                <div className="h-14 w-14 bg-slate-200 rounded-2xl flex items-center justify-center mb-6">
                  <Briefcase className="h-7 w-7 text-slate-500" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 mb-2">Targeted Revision</h3>
                <p className="text-slate-500 font-medium">Locked. Complete a diagnostic placement test first to unlock targeted practice.</p>
              </div>
            </div>
          </div>
        )}

        {view === 'workspace' && (
          <div className="flex-1 p-8 md:p-12">
            {status === 'loading' ? (
              <div className="flex justify-center items-center h-full min-h-[400px]">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
              </div>
            ) : status === 'error' ? (
              <div className="bg-rose-50 p-6 rounded-2xl border border-rose-200 text-center max-w-md mx-auto mt-20">
                <XCircle className="mx-auto h-12 w-12 text-rose-500 mb-4" />
                <p className="text-rose-800 font-bold text-lg mb-1">Connection Error</p>
                <p className="text-rose-600 font-medium">{message}</p>
              </div>
            ) : (
              <div className="max-w-3xl mx-auto animate-in fade-in zoom-in-95 duration-300">
                <div className="bg-white rounded-[2rem] shadow-sm border border-slate-200 overflow-hidden">
                  
                  {/* Header */}
                  <div className="bg-slate-900 px-10 py-10 text-center relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-b from-white/5 to-transparent"></div>
                    <h3 className="text-xs font-bold text-indigo-400 uppercase tracking-[0.2em] mb-4 relative z-10">Step-by-Step Solver</h3>
                    <div className="text-white text-xl relative z-10 font-medium leading-relaxed max-w-3xl mx-auto">
                      <LatexText content={question?.content} />
                    </div>
                  </div>

                  {/* Workspace */}
                  <div className="p-10 bg-white">
                    <div className="space-y-5 mb-10">
                      {trace.map((step, index) => (
                        <div key={index} className="flex items-center group">
                          <div className="w-10 h-10 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center font-bold text-sm mr-4 group-hover:bg-indigo-50 group-hover:text-indigo-600 transition-colors">
                            {index + 1}
                          </div>
                          <div className="flex-1 bg-slate-50 px-6 py-4 rounded-2xl border border-slate-100 group-hover:border-indigo-100 transition-colors">
                            <span className="text-lg text-slate-800"><LatexText content={step} /></span>
                          </div>
                        </div>
                      ))}
                      
                      {/* Input row / Multiple Choice */}
                      {status === 'feedback' ? (
                        <div className="mt-8 flex flex-col items-center justify-center p-8 bg-indigo-50/50 rounded-3xl border border-indigo-100">
                          <p className="text-lg text-slate-700 font-medium mb-6 text-center">
                            {diagnosis?.primary_cause === "No Significant Weakness" 
                              ? "Excellent! You got it right. Review the cognitive update in the sidebar."
                              : "Review your cognitive feedback in the sidebar before continuing."}
                          </p>
                          <button
                            onClick={continueToNextQuestion}
                            className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-4 px-10 rounded-xl transition-all shadow-lg shadow-indigo-200"
                          >
                            Continue to Next Question
                          </button>
                        </div>
                      ) : status === 'active' && question?.options && question.options.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8">
                          {question.options.map((opt) => (
                            <button
                              key={opt.id}
                              onClick={() => {
                                const newTrace = [opt.math];
                                setTrace(newTrace);
                                submitProcess(newTrace);
                              }}
                              className={`p-5 rounded-2xl border-2 text-left transition-all duration-200 flex items-center gap-4
                                ${opt.math === "I don't know" 
                                  ? "bg-slate-50 border-slate-200 hover:bg-slate-100 hover:border-slate-300 text-slate-600"
                                  : "bg-white border-slate-200 hover:border-indigo-500 hover:shadow-md hover:shadow-indigo-100"
                                }`}
                            >
                              <span className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center font-bold text-sm">
                                {opt.id}
                              </span>
                              <div className="flex-1 text-lg font-medium text-slate-800">
                                {opt.math === "I don't know" ? (
                                  <span>I don't know</span>
                                ) : (
                                  <span className="pointer-events-none"><LatexText content={opt.math} /></span>
                                )}
                              </div>
                            </button>
                          ))}
                        </div>
                      ) : status === 'active' ? (
                        <div className="flex items-center">
                          <div className="w-10 h-10 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold text-sm mr-4 shadow-sm border border-indigo-200">
                            {trace.length + 1}
                          </div>
                          <div className="flex-1 bg-white border-2 border-indigo-100 rounded-2xl px-5 py-3 focus-within:border-indigo-500 focus-within:ring-4 focus-within:ring-indigo-500/10 transition-all shadow-sm">
                            <math-field
                              style={{ width: '100%', fontSize: '1.25rem', outline: 'none', background: 'transparent' }}
                              value={currentStep}
                              onInput={(e) => setCurrentStep(e.target.value)}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') addStep();
                              }}
                            >
                            </math-field>
                          </div>
                          <button
                            onClick={addStep}
                            disabled={!currentStep.trim()}
                            className="ml-4 h-12 w-12 flex items-center justify-center bg-slate-100 text-slate-600 hover:bg-indigo-600 hover:text-white rounded-2xl disabled:opacity-50 disabled:hover:bg-slate-100 transition-all"
                          >
                            <Plus size={20} strokeWidth={3} />
                          </button>
                        </div>
                      ) : null}
                    </div>

                    {/* Actions */}
                    {status === 'active' && (
                      <div className="pt-6 border-t border-slate-100 flex justify-end">
                        <button
                          onClick={submitProcess}
                          disabled={trace.length <= 0 && !currentStep.trim()}
                          className="flex items-center bg-indigo-600 text-white px-8 py-4 rounded-2xl font-bold text-sm tracking-wide hover:bg-indigo-700 focus:ring-4 focus:ring-indigo-600/20 disabled:opacity-50 transition-all shadow-md shadow-indigo-600/20"
                        >
                          Submit Verification
                          <ChevronRight size={18} className="ml-2" />
                        </button>
                      </div>
                    )}
                    
                    {status === 'completed' && (
                      <div className="p-8 bg-emerald-50 rounded-2xl border border-emerald-200 text-center animate-in fade-in slide-in-from-bottom-4">
                        <CheckCircle2 className="mx-auto h-12 w-12 text-emerald-500 mb-4" />
                        <h4 className="text-xl font-bold text-emerald-900 mb-2">Assessment Complete</h4>
                        <p className="text-emerald-700 font-medium">Your cognitive profile has been fully mapped.</p>
                        <button 
                          onClick={() => setView('landing')}
                          className="mt-6 bg-emerald-600 text-white px-6 py-3 rounded-xl font-bold text-sm hover:bg-emerald-700 transition-colors"
                        >
                          Return to Dashboard
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
      
      <CognitiveProfile />
    </div>
  );
}

export default App;
