import React, { useState } from 'react';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    try {
      const resp = await fetch('http://localhost:7070/upload', {
        method: 'POST',
        body: formData,
      });
      const text = await resp.text();
      // Simple parsing: extract masked text and image URL
      const parser = new DOMParser();
      const doc = parser.parseFromString(text, 'text/html');
      const maskedText = doc.querySelector('pre')?.innerText || '';
      const imgSrc = doc.querySelector('img')?.src || '';
      setResult({ maskedText, imgSrc });
    } catch (err) {
      setError('Upload failed');
    }
  };

  return (
    <div className="container">
      <h1>OCR Sécurisé – React Frontend</h1>
      <form onSubmit={handleSubmit}>
        <input type="file" accept="image/*" onChange={handleFileChange} required />
        <button type="submit">Analyser et anonymiser</button>
      </form>
      {error && <div className="error">{error}</div>}
      {result && (
        <div className="result">
          <h2>Texte masqué</h2>
          <pre>{result.maskedText}</pre>
          {result.imgSrc && <img src={result.imgSrc} alt="Masqué" style={{ maxWidth: '100%' }} />}
        </div>
      )}
    </div>
  );
}

export default App;
