'use client';

import { useState, useEffect } from 'react';

export default function TestLeadsPage() {
  const [logs, setLogs] = useState<string[]>([]);
  const [token, setToken] = useState<string | null>(null);
  const [apiResult, setApiResult] = useState<any>(null);

  const log = (message: string) => {
    console.log(message);
    setLogs(prev => [...prev, `${new Date().toLocaleTimeString()}: ${message}`]);
  };

  useEffect(() => {
    log('Page mounted');
    const storedToken = localStorage.getItem('access_token');
    setToken(storedToken);
    log(`Token found: ${storedToken ? 'YES' : 'NO'}`);
    if (storedToken) {
      log(`Token preview: ${storedToken.substring(0, 30)}...`);
    }
  }, []);

  const testApiCall = async () => {
    log('--- Starting API Test ---');

    const currentToken = localStorage.getItem('access_token');
    if (!currentToken) {
      log('ERROR: No token in localStorage!');
      return;
    }

    log(`Using token: ${currentToken.substring(0, 30)}...`);

    try {
      log('Calling: http://localhost:8000/api/v1/leads');

      const response = await fetch('http://localhost:8000/api/v1/leads?limit=2', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${currentToken}`,
          'Content-Type': 'application/json',
        },
      });

      log(`Response status: ${response.status} ${response.statusText}`);
      log(`Response headers: ${JSON.stringify([...response.headers.entries()])}`);

      const responseText = await response.text();
      log(`Response body length: ${responseText.length} characters`);

      if (!response.ok) {
        log(`ERROR: API returned ${response.status}`);
        log(`Error body: ${responseText}`);
        setApiResult({ error: true, status: response.status, body: responseText });
        return;
      }

      const data = JSON.parse(responseText);
      log(`SUCCESS: Parsed ${data.length} leads`);
      setApiResult({ error: false, data });

      if (data.length > 0) {
        log(`First lead: ${JSON.stringify(data[0], null, 2)}`);
      }
    } catch (error: any) {
      log(`EXCEPTION: ${error.message}`);
      log(`Error stack: ${error.stack}`);
      setApiResult({ error: true, exception: error.message });
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Leads API Diagnostic</h1>

      <div className="mb-4 p-4 bg-gray-100 rounded">
        <h2 className="font-bold mb-2">Status</h2>
        <p>Token: {token ? '✓ Found' : '✗ Not Found'}</p>
        {token && <p className="text-xs text-gray-600 break-all">{token.substring(0, 100)}...</p>}
      </div>

      <button
        onClick={testApiCall}
        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 mb-4"
      >
        Test API Call
      </button>

      {apiResult && (
        <div className={`p-4 rounded mb-4 ${apiResult.error ? 'bg-red-100' : 'bg-green-100'}`}>
          <h3 className="font-bold mb-2">API Result:</h3>
          <pre className="text-xs overflow-auto">{JSON.stringify(apiResult, null, 2)}</pre>
        </div>
      )}

      <div className="bg-black text-green-400 p-4 rounded font-mono text-xs">
        <h2 className="font-bold mb-2 text-white">Console Logs:</h2>
        {logs.map((log, i) => (
          <div key={i}>{log}</div>
        ))}
      </div>
    </div>
  );
}
