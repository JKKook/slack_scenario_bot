import React, { useState } from 'react';
import './App.css';
import axios from 'axios';

function App() {
    const [topic, setTopic] = useState('');
    const [outline, setOutline] = useState('');
    const [scenario, setScenario] = useState(null);
    const [audioUrl, setAudioUrl] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const generateScenario = async () => {
        if (!topic.trim() || !outline.trim()) {
            setError('주제와 상세 내용을 모두 입력해주세요.');
            return;
        }

        setLoading(true);
        setError('');
        setScenario(null);
        setAudioUrl(null);

        try {
            // 시나리오 생성 API 호출
            const response = await axios.post('/api/generate-scenario', {
                topic: topic.trim(),
                outline: outline.trim(),
            });

            setScenario(response.data.scenario);
            setAudioUrl(response.data.audioUrl);
        } catch (err) {
            console.error('Error generating scenario:', err);
            setError(
                '시나리오 생성 중 오류가 발생했습니다. 다시 시도해주세요.',
            );
        } finally {
            setLoading(false);
        }
    };

    const downloadAudio = () => {
        if (audioUrl) {
            const link = document.createElement('a');
            link.href = audioUrl;
            link.download = `${topic}_audio.mp3`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    };

    return (
        <div className='App'>
            <div className='container'>
                <header className='header'>
                    <h1>🎥 YouTube Short 시나리오 생성기</h1>
                    <p>
                        주제와 내용을 입력하면 1분짜리 시나리오와 음성 파일을
                        생성합니다
                    </p>
                </header>

                <div className='input-section'>
                    <div className='input-group'>
                        <label htmlFor='topic'>주제 *</label>
                        <input
                            type='text'
                            id='topic'
                            value={topic}
                            onChange={(e) => setTopic(e.target.value)}
                            placeholder='예: AI의 미래, 반도체 시장 전망...'
                            disabled={loading}
                        />
                    </div>

                    <div className='input-group'>
                        <label htmlFor='outline'>상세 내용 *</label>
                        <textarea
                            id='outline'
                            value={outline}
                            onChange={(e) => setOutline(e.target.value)}
                            placeholder='예: AI가 경제생활에 미치는 영향, 현재 국제 정세와 정책 동향...'
                            rows='4'
                            disabled={loading}
                        />
                    </div>

                    <button
                        className='generate-btn'
                        onClick={generateScenario}
                        disabled={loading}
                    >
                        {loading ? '생성 중...' : '🎵 시나리오 생성하기'}
                    </button>
                </div>

                {error && <div className='error-message'>❌ {error}</div>}

                {scenario && (
                    <div className='result-section'>
                        <h2>📝 생성된 시나리오</h2>

                        <div className='scenario-info'>
                            <div className='info-item'>
                                <strong>어조:</strong> {scenario.tone}
                            </div>
                            <div className='info-item'>
                                <strong>선택 이유:</strong> {scenario.reason}
                            </div>
                        </div>

                        <div className='scenario-content'>
                            <div className='section'>
                                <h3>🎬 시작 (0-10초)</h3>
                                <p>{scenario.opening}</p>
                            </div>

                            <div className='section'>
                                <h3>📋 본문 (10-45초)</h3>
                                <ul>
                                    {scenario.main_points.map(
                                        (point, index) => (
                                            <li key={index}>{point}</li>
                                        ),
                                    )}
                                </ul>
                            </div>

                            <div className='section'>
                                <h3>🎯 마무리 (45-60초)</h3>
                                <p>{scenario.closing}</p>
                            </div>
                        </div>

                        {audioUrl && (
                            <div className='audio-section'>
                                <h3>🎵 음성 파일</h3>
                                <div className='audio-controls'>
                                    <audio
                                        controls
                                        src={audioUrl}
                                        className='audio-player'
                                    >
                                        Your browser does not support the audio
                                        element.
                                    </audio>
                                    <button
                                        className='download-btn'
                                        onClick={downloadAudio}
                                    >
                                        📥 음성 파일 다운로드
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

export default App;
