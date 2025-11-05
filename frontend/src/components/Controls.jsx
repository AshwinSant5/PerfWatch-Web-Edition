import React, { useState, useRef, useEffect } from 'react';

const Controls = ({ isProfiling, onStart, onStop, status }) => {
  const [mode, setMode] = useState('exe'); // 'exe' or 'cpp'
  const [programPath, setProgramPath] = useState('');
  const [cppCode, setCppCode] = useState('');
  const [cppFileName, setCppFileName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [showMessageModal, setShowMessageModal] = useState(false);
  const [messageOverflows, setMessageOverflows] = useState(false);
  const fileInputRef = useRef(null);
  const cppFileInputRef = useRef(null);
  const messageRef = useRef(null);

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      // For security, we can't directly access file paths in browser
      // So we'll use the file name and let user provide full path
      setProgramPath(file.name);
      setMessage('Note: Please provide the full path to the executable');
    }
  };

  const handleCppFileSelect = async (file) => {
    if (!file) return;
    
    // Check if it's a C++ file
    const validExtensions = ['.cpp', '.cxx', '.cc', '.c++', '.hpp', '.hxx', '.h++', '.c', '.h'];
    const fileName = file.name.toLowerCase();
    const hasValidExtension = validExtensions.some(ext => fileName.endsWith(ext));
    
    if (!hasValidExtension) {
      setMessage('Error: Please select a C++ source file (.cpp, .cxx, .hpp, etc.)');
      return;
    }
    
    try {
      const text = await file.text();
      setCppCode(text);
      setCppFileName(file.name);
      setMessage(`Loaded: ${file.name}`);
    } catch (error) {
      setMessage(`Error reading file: ${error.message}`);
    }
  };

  const handleCppFileInput = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleCppFileSelect(file);
    }
    // Reset input so same file can be selected again
    e.target.value = '';
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    if (isProfiling) return;
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleCppFileSelect(files[0]);
    }
  };

  const handleDropZoneClick = () => {
    if (!isProfiling && cppFileInputRef.current) {
      cppFileInputRef.current.click();
    }
  };

  const handleStart = async () => {
    if (mode === 'exe') {
      if (!programPath.trim()) {
        setMessage('Please enter a program path');
        return;
      }
    } else {
      if (!cppCode.trim()) {
        setMessage('Please paste C++ source code');
        return;
      }
    }

    setIsLoading(true);
    setMessage('');

    try {
      let response;
      if (mode === 'exe') {
        response = await fetch('http://localhost:8000/run', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ program: programPath }),
        });
      } else {
        // Compile and run C++ code
        response = await fetch('http://localhost:8000/compile-and-run', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ source_code: cppCode }),
        });
      }

      const data = await response.json();

      if (response.ok) {
        setMessage(`Started: ${data.message}`);
        onStart();
      } else {
        setMessage(`Error: ${data.detail || 'Failed to start'}`);
      }
    } catch (error) {
      setMessage(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStop = async () => {
    setIsLoading(true);
    setMessage('');

    try {
      const response = await fetch('http://localhost:8000/stop', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ kill_process: true }),
      });

      const data = await response.json();

      if (response.ok) {
        setMessage(data.message || 'Stopped profiling');
        onStop();
      } else {
        setMessage(`Error: ${data.detail || 'Failed to stop'}`);
      }
    } catch (error) {
      setMessage(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const response = await fetch('http://localhost:8000/export?format=csv');
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `metrics_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        setMessage('Metrics exported successfully');
      } else {
        setMessage('No metrics to export');
      }
    } catch (error) {
      setMessage(`Export error: ${error.message}`);
    }
  };

  // Check if message overflows its container
  useEffect(() => {
    if (message && messageRef.current) {
      const element = messageRef.current;
      const isOverflowing = element.scrollHeight > element.clientHeight || 
                           element.scrollWidth > element.clientWidth;
      setMessageOverflows(isOverflowing);
    } else {
      setMessageOverflows(false);
    }
  }, [message]);

  const defaultCppCode = `#include <iostream>
#include <thread>
#include <chrono>

int main() {
    std::cout << "Hello from compiled C++!" << std::endl;
    
    // Simulate some work
    for (int i = 0; i < 100; i++) {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        std::cout << "Iteration: " << i << std::endl;
    }
    
    return 0;
}`;

  return (
    <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
      <h2 className="text-2xl font-semibold mb-4">Controls</h2>

      {/* Mode Toggle */}
      <div className="mb-4">
        <div className="flex bg-gray-700 rounded-lg p-1">
          <button
            onClick={() => setMode('exe')}
            disabled={isProfiling}
            className={`flex-1 px-4 py-2 rounded text-sm font-medium transition-colors ${
              mode === 'exe'
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:bg-gray-600'
            } disabled:opacity-50`}
          >
            📁 Run Executable
          </button>
          <button
            onClick={() => setMode('cpp')}
            disabled={isProfiling}
            className={`flex-1 px-4 py-2 rounded text-sm font-medium transition-colors ${
              mode === 'cpp'
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:bg-gray-600'
            } disabled:opacity-50`}
          >
            💻 Compile C++
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {mode === 'exe' ? (
          <div>
            <label className="block text-sm font-medium mb-2">
              Executable Path
            </label>
            <input
              type="text"
              value={programPath}
              onChange={(e) => setProgramPath(e.target.value)}
              placeholder="C:\\path\\to\\program.exe"
              disabled={isProfiling}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            />
            <p className="text-xs text-gray-400 mt-1">
              Example: notepad.exe or C:\\Windows\\System32\\notepad.exe
            </p>
          </div>
        ) : (
          <div>
            <label className="block text-sm font-medium mb-2">
              C++ Source File
            </label>
            
            {/* Drag and Drop Zone */}
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={handleDropZoneClick}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                isDragging
                  ? 'border-blue-500 bg-blue-900/20'
                  : 'border-gray-600 bg-gray-700/50 hover:border-gray-500 hover:bg-gray-700'
              } ${isProfiling ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <input
                ref={cppFileInputRef}
                type="file"
                accept=".cpp,.cxx,.cc,.c++,.hpp,.hxx,.h++,.c,.h"
                onChange={handleCppFileInput}
                className="hidden"
                disabled={isProfiling}
              />
              
              {cppCode ? (
                <div className="space-y-2">
                  <div className="text-green-400 text-lg">✓</div>
                  <div className="text-gray-200 font-medium">{cppFileName || 'File loaded'}</div>
                  <div className="text-xs text-gray-400">Click to select a different file</div>
                  <div className="text-xs text-gray-400">or drag and drop a new file here</div>
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="text-4xl mb-2">📄</div>
                  <div className="text-gray-200 font-medium">Drag & Drop C++ File</div>
                  <div className="text-xs text-gray-400">or click to browse</div>
                  <div className="text-xs text-gray-400 mt-1">
                    Supports: .cpp, .cxx, .hpp, .h, .c
                  </div>
                </div>
              )}
            </div>

            {/* Code Preview (read-only) */}
            {cppCode && (
              <div className="mt-4">
                <div className="flex justify-between items-center mb-2">
                  <label className="block text-sm font-medium text-gray-300">
                    Code Preview
                  </label>
                  <button
                    onClick={() => {
                      setCppCode('');
                      setCppFileName('');
                      setMessage('');
                    }}
                    disabled={isProfiling}
                    className="text-xs text-red-400 hover:text-red-300 disabled:opacity-50"
                  >
                    Clear
                  </button>
                </div>
                <textarea
                  value={cppCode}
                  onChange={(e) => setCppCode(e.target.value)}
                  placeholder="C++ code will appear here..."
                  disabled={isProfiling}
                  rows={8}
                  className="w-full px-3 py-2 bg-gray-900 border border-gray-600 rounded text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 font-mono text-xs"
                />
              </div>
            )}

            <p className="text-xs text-gray-400 mt-2">
              Requires MinGW-w64 (g++) or MSVC compiler. File will be compiled and executed automatically.
            </p>
          </div>
        )}

        <div className="flex flex-col space-y-2">
          <button
            onClick={handleStart}
            disabled={isProfiling || isLoading || (mode === 'exe' ? !programPath.trim() : !cppCode.trim())}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded font-medium transition-colors"
          >
            {isLoading 
              ? (mode === 'cpp' ? 'Compiling...' : 'Starting...') 
              : (mode === 'cpp' ? '🔨 Compile & Profile' : '▶ Start Profiling')}
          </button>

          <button
            onClick={handleStop}
            disabled={!isProfiling || isLoading}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded font-medium transition-colors"
          >
            {isLoading ? 'Stopping...' : '⏹ Stop Profiling'}
          </button>

          <button
            onClick={handleExport}
            disabled={isLoading || !status || status.metrics_count === 0}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded font-medium transition-colors"
          >
            📥 Export CSV
          </button>
        </div>

        {message && (
          <div className={`p-3 rounded text-sm relative ${
            message.includes('Error') 
              ? 'bg-red-900 text-red-200' 
              : 'bg-blue-900 text-blue-200'
          }`}>
            <div 
              ref={messageRef}
              className="pr-8 break-words overflow-hidden"
              style={{
                maxHeight: '100px',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                display: '-webkit-box',
                WebkitLineClamp: 4,
                WebkitBoxOrient: 'vertical',
                wordBreak: 'break-word'
              }}
            >
              {message}
            </div>
            {(message.length > 150 || messageOverflows) && (
              <button
                onClick={() => setShowMessageModal(true)}
                className="absolute top-2 right-2 p-1 rounded hover:bg-black/20 transition-colors"
                title="View full message"
              >
                <svg 
                  className="w-4 h-4" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" 
                  />
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" 
                  />
                </svg>
              </button>
            )}
          </div>
        )}

        {/* Message Modal */}
        {showMessageModal && (
          <div 
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setShowMessageModal(false)}
          >
            <div 
              className={`bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] flex flex-col ${
                message.includes('Error') 
                  ? 'border-2 border-red-600' 
                  : 'border-2 border-blue-600'
              }`}
              onClick={(e) => e.stopPropagation()}
            >
              <div className={`p-4 border-b ${
                message.includes('Error') 
                  ? 'bg-red-900/30 border-red-600' 
                  : 'bg-blue-900/30 border-blue-600'
              } flex justify-between items-center`}>
                <h3 className={`text-lg font-semibold ${
                  message.includes('Error') 
                    ? 'text-red-200' 
                    : 'text-blue-200'
                }`}>
                  {message.includes('Error') ? '⚠️ Error' : 'ℹ️ Message'}
                </h3>
                <button
                  onClick={() => setShowMessageModal(false)}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  <svg 
                    className="w-6 h-6" 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path 
                      strokeLinecap="round" 
                      strokeLinejoin="round" 
                      strokeWidth={2} 
                      d="M6 18L18 6M6 6l12 12" 
                    />
                  </svg>
                </button>
              </div>
              <div className="p-4 overflow-y-auto flex-1">
                <pre className={`whitespace-pre-wrap break-words text-sm font-mono ${
                  message.includes('Error') 
                    ? 'text-red-200' 
                    : 'text-blue-200'
                }`}>
                  {message}
                </pre>
              </div>
              <div className="p-4 border-t border-gray-700 flex justify-end">
                <button
                  onClick={() => setShowMessageModal(false)}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {status && (
          <div className="mt-4 pt-4 border-t border-gray-700">
            <div className="text-sm space-y-1">
              <div className="flex justify-between">
                <span className="text-gray-400">Status:</span>
                <span className={status.is_profiling ? 'text-green-400' : 'text-gray-500'}>
                  {status.is_profiling ? 'Profiling' : 'Idle'}
                </span>
              </div>
              {status.pid && (
                <div className="flex justify-between">
                  <span className="text-gray-400">PID:</span>
                  <span className="text-gray-300">{status.pid}</span>
                </div>
              )}
              {status.metrics_count > 0 && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Metrics:</span>
                  <span className="text-gray-300">{status.metrics_count}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Controls;

