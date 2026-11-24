import os
from flask import Flask, request, jsonify, render_template_string
import requests

app = Flask(__name__)

try:
    with open("key.txt", "r") as f:
        API_KEY = f.read().strip()
except FileNotFoundError:
    API_KEY = ""

MODEL = "google/gemma-3-12b-it"
API_URL = "https://api.polza.ai/v1/chat/completions"

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UchiAI — Супер-помощник</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #6366f1; --primary-hover: #4f46e5; --bg: #f8fafc; --card-bg: #ffffff;
            --text: #0f172a; --text-muted: #64748b; --border: #e2e8f0; --success: #10b981;
            --danger: #ef4444; --premium: #f59e0b; --premium-bg: linear-gradient(135deg, #fef3c7, #fde68a);
        }
        body.dark {
            --bg: #0f172a; --card-bg: #1e293b; --text: #f8fafc; --text-muted: #94a3b8;
            --border: #334155; --premium-bg: linear-gradient(135deg, #78350f, #451a03);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; -webkit-tap-highlight-color: transparent; }
        
        .bg-blobs { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; overflow: hidden; pointer-events: none; }
        .blob { position: absolute; background: rgba(99, 102, 241, 0.15); filter: blur(80px); border-radius: 50%; animation: float 10s infinite alternate; }
        .blob-1 { width: 300px; height: 300px; top: -10%; left: -10%; }
        .blob-2 { width: 400px; height: 400px; bottom: -20%; right: -10%; background: rgba(245, 158, 11, 0.1); animation-delay: -5s; }
        .blob-3 { width: 200px; height: 200px; top: 40%; left: 40%; background: rgba(16, 185, 129, 0.1); animation-delay: -2s; }
        @keyframes float { 0% { transform: translate(0, 0) scale(1); } 100% { transform: translate(30px, 50px) scale(1.1); } }

        body { background-color: var(--bg); color: var(--text); display: flex; justify-content: center; padding: 20px 15px; min-height: 100vh; transition: background 0.3s; }
        .app-container { width: 100%; max-width: 650px; z-index: 1; }
        
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; }
        .logo { font-size: 26px; font-weight: 800; color: var(--primary); cursor: pointer; display: flex; gap: 10px; align-items: center;}
        .logo span { font-size: 12px; background: rgba(99,102,241,0.1); color: var(--primary); padding: 4px 8px; border-radius: 6px; font-weight: 800; }
        .header-buttons { display: flex; gap: 8px; }
        .btn-icon { background: var(--card-bg); border: 1px solid var(--border); color: var(--text); padding: 8px 12px; border-radius: 12px; cursor: pointer; font-size: 16px; transition: 0.2s; }
        .btn-icon:active { transform: scale(0.9); }
        .btn-premium { background: linear-gradient(135deg, #f59e0b, #f97316); color: white; padding: 8px 14px; border: none; border-radius: 12px; font-weight: 700; cursor: pointer; font-size: 13px; box-shadow: 0 4px 15px rgba(245,158,11,0.4); transition: 0.3s; }
        .btn-premium:active { transform: scale(0.95); }

        .tabs { display: flex; gap: 10px; margin-bottom: 20px; overflow-x: auto; padding-bottom: 5px; scrollbar-width: none; }
        .tab { padding: 10px 16px; background: var(--card-bg); border-radius: 14px; font-weight: 600; font-size: 13px; cursor: pointer; border: 1px solid var(--border); color: var(--text-muted); white-space: nowrap; }
        .tab.active { background: var(--primary); color: white; border-color: var(--primary); }
        
        .card { background: var(--card-bg); border-radius: 24px; padding: 25px; box-shadow: 0 10px 40px rgba(0,0,0,0.06); margin-bottom: 20px; border: 1px solid var(--border); display: none;}
        .card.active { display: block; animation: slideUp 0.3s ease; }
        @keyframes slideUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        textarea { width: 100%; height: 120px; padding: 18px; border: 2px solid var(--border); border-radius: 16px; resize: none; font-size: 15px; background: var(--bg); color: var(--text); margin-bottom: 15px;}
        textarea:focus { outline: none; border-color: var(--primary); }
        
        .subjects { display: flex; gap: 8px; margin-bottom: 15px; overflow-x: auto; scrollbar-width: none; padding-bottom: 10px; }
        .subject { padding: 8px 14px; background: var(--bg); border: 1px solid var(--border); border-radius: 20px; font-size: 13px; font-weight: 600; cursor: pointer; color: var(--text-muted); white-space: nowrap;}
        .subject.active { background: var(--primary); color: white; border-color: var(--primary); }

        .photo-preview { display: none; position: relative; width: 100%; height: 150px; border-radius: 12px; overflow: hidden; margin-bottom: 15px; background: #000; }
        .photo-preview img { width: 100%; height: 100%; object-fit: cover; opacity: 0.7; }
        .scanner-line { position: absolute; top: 0; left: 0; width: 100%; height: 4px; background: rgba(99, 102, 241, 0.5); box-shadow: 0 0 15px 5px rgba(99, 102, 241, 0.5); animation: scan 2s infinite linear; }
        @keyframes scan { 0% { top: 0; } 100% { top: 100%; } }

        .actions-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 15px; }
        button { border-radius: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s; border: none; display: flex; justify-content: center; align-items: center; gap: 8px; font-size: 15px; }
        button:active { transform: scale(0.97); }
        .btn-photo { background: var(--bg); border: 2px dashed var(--border); color: var(--text-muted); padding: 14px; position: relative; overflow: hidden;}
        .btn-photo input[type="file"] { position: absolute; left: 0; top: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer;}
        .btn-clear { background: rgba(239,68,68,0.1); color: var(--danger); padding: 14px; }
        .btn-solve { background: var(--primary); color: white; padding: 16px; font-size: 16px; box-shadow: 0 8px 20px rgba(99,102,241,0.3); grid-column: span 2; margin-top: 5px;}
        
        .resultBox { display: none; margin-top: 20px; padding: 20px; background: var(--bg); border-left: 4px solid var(--primary); border-radius: 12px; }
        .result-content { font-size: 15px; line-height: 1.6; color: var(--text); }
        .result-actions { display: flex; gap: 10px; margin-top: 15px; flex-wrap: wrap;}
        .btn-result { background: var(--card-bg); border: 1px solid var(--border); padding: 10px; border-radius: 10px; font-size: 13px; flex: 1; color: var(--text); white-space: nowrap;}

        .history-item { background: var(--bg); border: 1px solid var(--border); padding: 15px; border-radius: 12px; margin-bottom: 10px; cursor: pointer; }
        .history-q { font-weight: 700; font-size: 14px; margin-bottom: 5px; color: var(--primary); }
        .history-a { font-size: 13px; color: var(--text-muted); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

        .loader { display: none; text-align: center; margin-top: 15px; color: var(--primary); font-weight: 600;}
        .spinner { display: inline-block; width: 20px; height: 20px; border: 3px solid rgba(99,102,241,0.3); border-radius: 50%; border-top-color: var(--primary); animation: spin 1s infinite linear; vertical-align: middle; margin-right: 8px;}
        @keyframes spin { to { transform: rotate(360deg); } }

        /* Профиль */
        .profile-card { display: none; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 90%; max-width: 420px; background: var(--card-bg); padding: 30px; border-radius: 24px; z-index: 1000; box-shadow: 0 20px 50px rgba(0,0,0,0.2); border: 1px solid var(--border); }
        .profile-header { text-align: center; margin-bottom: 20px; }
        .avatar { width: 90px; height: 90px; background: var(--primary); color: white; font-size: 36px; font-weight: 800; display: flex; justify-content: center; align-items: center; border-radius: 50%; margin: 0 auto 15px; }
        .vip-badge { display: none; background: linear-gradient(135deg, #f59e0b, #f97316); color: white; padding: 6px 16px; border-radius: 20px; font-size: 13px; font-weight: 800; margin-top: 5px;}
        .progress-bar { width: 100%; height: 12px; background: var(--bg); border-radius: 10px; margin: 10px 0; overflow: hidden; }
        .progress-fill { height: 100%; background: var(--success); width: 100%; transition: width 0.3s;}
        .stats-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-top: 20px; text-align: center;}
        .stat-box { background: var(--bg); padding: 15px 5px; border-radius: 12px; }
        .stat-val { font-size: 20px; font-weight: 800; color: var(--primary); }
        .stat-label { font-size: 11px; color: var(--text-muted); margin-top: 5px; }
        .profile-info { background: var(--bg); padding: 15px; border-radius: 12px; margin-top: 20px; font-size: 14px; display: flex; justify-content: space-between; align-items: center;}
        .achievements { display: flex; gap: 10px; margin-top: 15px; justify-content: center;}
        .achieve-icon { width: 40px; height: 40px; background: var(--bg); border-radius: 50%; display: flex; justify-content: center; align-items: center; font-size: 20px; opacity: 0.3; border: 1px solid var(--border); }
        .achieve-icon.unlocked { opacity: 1; background: var(--premium-bg); border-color: var(--premium); }

        /* Окно оплаты */
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 1000; justify-content: center; align-items: flex-end; backdrop-filter: blur(5px);}
        .modal-content { background: var(--card-bg); padding: 25px 20px; border-radius: 24px 24px 0 0; width: 100%; max-width: 650px; max-height: 95vh; overflow-y: auto; }
        .modal-header { text-align: center; margin-bottom: 25px; position: relative;}
        .modal-title { font-size: 24px; font-weight: 800; margin-bottom: 5px; }
        .btn-close-icon { position: absolute; right: 0; top: 0; background: var(--bg); border: none; font-size: 20px; color: var(--text-muted); cursor: pointer; padding: 8px; border-radius: 50%;}

        .plans-container { display: flex; flex-direction: column; gap: 20px; }
        .plan-card { border: 2px solid var(--border); border-radius: 20px; padding: 25px; position: relative; background: var(--bg); }
        .plan-card.popular { border-color: var(--primary); background: var(--card-bg);}
        .plan-badge { position: absolute; top: -14px; right: 20px; background: var(--primary); color: white; font-size: 12px; font-weight: 800; padding: 5px 12px; border-radius: 10px; }
        .plan-title { font-size: 20px; font-weight: 800; margin-bottom: 5px; }
        .plan-price { font-size: 32px; font-weight: 800; color: var(--text); margin-bottom: 20px;}
        .plan-price span { font-size: 14px; color: var(--text-muted); }
        .plan-features { list-style: none; margin-bottom: 25px; }
        .plan-features li { font-size: 14px; color: var(--text); margin-bottom: 10px; display: flex; align-items: flex-start; gap: 10px; }
        .plan-features li::before { content: "✓"; color: var(--success); font-weight: 800; }
        .plan-features li.disabled { color: var(--text-muted); text-decoration: line-through; opacity: 0.5;}
        .plan-features li.disabled::before { content: "✕"; color: var(--danger); }
        .btn-buy { width: 100%; padding: 16px; border-radius: 14px; background: var(--bg); color: var(--text); font-weight: 700; border: 2px solid var(--border); font-size: 16px;}
        .btn-buy.active { background: var(--success); color: white; border-color: var(--success);}
        .plan-card.popular .btn-buy { background: var(--primary); color: white; border-color: var(--primary); }

        /* Экран оплаты */
        .payment-screen { display: none; text-align: center; padding: 20px 0; }
        .card-icon { font-size: 50px; margin-bottom: 15px; animation: pulse 1s infinite alternate; }
        @keyframes pulse { from { transform: scale(1); } to { transform: scale(1.1); } }
        .payment-input { width: 100%; padding: 15px; border-radius: 12px; border: 1px solid var(--border); background: var(--bg); color: var(--text); margin-bottom: 15px; font-size: 16px; text-align: center;}

        /* FAQ (ОГРОМНЫЙ) */
        .faq-section { margin-top: 40px; }
        .faq-title { text-align: center; font-size: 24px; font-weight: 800; margin-bottom: 20px; }
        .faq-item { background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; margin-bottom: 12px; overflow: hidden; }
        .faq-q { padding: 20px; font-weight: 600; cursor: pointer; display: flex; justify-content: space-between; align-items: center; color: var(--text); font-size: 16px;}
        .faq-a { padding: 0 20px 20px; font-size: 14px; color: var(--text-muted); display: none; line-height: 1.7;}
        .faq-item.active .faq-a { display: block; }
        .faq-a h4 { color: var(--text); margin-top: 10px; margin-bottom: 5px;}
        .faq-a ul { margin-left: 20px; margin-bottom: 10px;}

        /* Фичи (15 штук) */
        .features-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 20px; }
        .feature-item { background: var(--card-bg); padding: 20px; border-radius: 16px; border: 1px solid var(--border); text-align: center; }
        .feature-icon { font-size: 28px; margin-bottom: 10px; display: block; }
        .feature-title { font-weight: 700; font-size: 14px; margin-bottom: 5px; }
        .feature-desc { font-size: 12px; color: var(--text-muted); }

        #toast { visibility: hidden; min-width: 250px; background-color: #333; color: #fff; text-align: center; border-radius: 30px; padding: 14px; position: fixed; z-index: 2000; left: 50%; bottom: 30px; transform: translateX(-50%); font-size: 14px; font-weight: 600; opacity: 0; transition: opacity 0.3s;}
        #toast.show { visibility: visible; opacity: 1; }
    </style>
</head>
<body>

<div class="bg-blobs"><div class="blob blob-1"></div><div class="blob blob-2"></div><div class="blob blob-3"></div></div>

<div class="app-container">
    <div class="header">
        <div class="logo" onclick="switchTab('reshatel', document.querySelectorAll('.tab')[0])">UchiAI <span>PRO</span></div>
        <div class="header-buttons">
            <button class="btn-icon" onclick="toggleDarkMode()" id="themeBtn">🌙</button>
            <button class="btn-icon" onclick="openProfile()">👤</button>
            <button class="btn-premium" onclick="openPremium()">Premium 👑</button>
        </div>
    </div>

    <div class="tabs">
        <div class="tab active" onclick="switchTab('reshatel', this)">🤖 Решалка</div>
        <div class="tab" onclick="switchTab('history', this)">📜 История</div>
        <div class="tab" onclick="switchTab('notes', this)">📝 Конспекты</div>
        <div class="tab" onclick="switchTab('check', this)">🔍 Проверка</div>
        <div class="tab" onclick="switchTab('translate', this)">🌍 Переводчик</div>
    </div>

    <!-- ВКЛАДКА 1: РЕШАЛКА -->
    <div id="tab-reshatel" class="card active">
        <div class="subjects">
            <div class="subject active" onclick="setSmart('Алгебра', this)">Алгебра</div>
            <div class="subject" onclick="setSmart('Геометрия', this)">Геометрия</div>
            <div class="subject" onclick="setSmart('Физика', this)">Физика</div>
            <div class="subject" onclick="setSmart('Химия', this)">Химия</div>
            <div class="subject" onclick="setSmart('Биология', this)">Биология</div>
            <div class="subject" onclick="setSmart('Русский язык', this)">Русский</div>
            <div class="subject" onclick="setSmart('Английский язык', this)">Английский</div>
            <div class="subject" onclick="setSmart('История', this)">История</div>
            <div class="subject" onclick="setSmart('Информатика', this)">Информатика</div>
            <div class="subject" onclick="setSmart('Литература', this)">Литература</div>
            <div class="subject" onclick="setSmart('География', this)">География</div>
            <div class="subject" onclick="setSmart('Обществознание', this)">Общество</div>
        </div>
        <textarea id="task" placeholder="Напиши задачу..."></textarea>
        <div class="photo-preview" id="photoPreview">
            <img id="previewImg" src="" alt="Фото">
            <div class="scanner-line"></div>
        </div>
        <div class="actions-grid">
            <button class="btn-photo">📸 <span id="photoText">Фото</span><input type="file" accept="image/*" onchange="handlePhoto(this)"></button>
            <button class="btn-clear" onclick="clearText('task', 'result-reshatel')">🗑️ Очистить</button>
            <button class="btn-solve" id="btn-solve-reshatel" onclick="solve('reshatel')">Решить задачу ✨</button>
        </div>
        <div class="loader" id="loader-reshatel"><span class="spinner"></span> Думаю...</div>
        <div id="result-reshatel" class="resultBox">
            <div id="text-reshatel" class="result-content"></div>
            <div class="result-actions">
                <button class="btn-result" onclick="copyResult('text-reshatel')">📋 Скопировать</button>
                <button class="btn-result" onclick="saveHistory()">💾 В историю</button>
                <button class="btn-result" onclick="shareResult('text-reshatel')">📤 Поделиться</button>
            </div>
        </div>
    </div>

    <div id="tab-history" class="card"><h2 style="font-size: 18px; margin-bottom: 15px;">История</h2><div id="historyList"><p style="color: var(--text-muted); font-size: 14px;">Пусто.</p></div></div>
    
    <div id="tab-notes" class="card"><h2 style="font-size: 18px; margin-bottom: 12px;">Конспекты</h2><textarea id="notes-input" placeholder="Текст..."></textarea><button class="btn-solve" style="width: 100%;" id="btn-solve-notes" onclick="solve('notes')">Сделать 📝</button><div class="loader" id="loader-notes"><span class="spinner"></span> Пишу...</div><div id="result-notes" class="resultBox"><div id="text-notes" class="result-content"></div><div class="result-actions"><button class="btn-result" onclick="copyResult('text-notes')">📋 Скопировать</button></div></div></div>
    
    <div id="tab-check" class="card"><h2 style="font-size: 18px; margin-bottom: 12px;">Проверка</h2><textarea id="check-input" placeholder="Текст..."></textarea><button class="btn-solve" style="width: 100%;" id="btn-solve-check" onclick="solve('check')">Проверить 🔍</button><div class="loader" id="loader-check"><span class="spinner"></span> Проверяю...</div><div id="result-check" class="resultBox"><div id="text-check" class="result-content"></div><div class="result-actions"><button class="btn-result" onclick="copyResult('text-check')">📋 Скопировать</button></div></div></div>
    
    <div id="tab-translate" class="card"><h2 style="font-size: 18px; margin-bottom: 12px;">Перевод</h2><textarea id="translate-input" placeholder="Текст..."></textarea><button class="btn-solve" style="width: 100%;" id="btn-solve-translate" onclick="solve('translate')">Перевести 🌍</button><div class="loader" id="loader-translate"><span class="spinner"></span> Перевожу...</div><div id="result-translate" class="resultBox"><div id="text-translate" class="result-content"></div><div class="result-actions"><button class="btn-result" onclick="copyResult('text-translate')">📋 Скопировать</button></div></div></div>

    <!-- 15 НОВЫХ ФИЧ -->
    <h2 style="text-align: center; font-size: 22px; margin-top: 30px; font-weight: 800;">Возможности UchiAI</h2>
    <div class="features-grid">
        <div class="feature-item"><span class="feature-icon">🧮</span><div class="feature-title">Калькулятор</div><div class="feature-desc">Сложные вычисления</div></div>
        <div class="feature-item"><span class="feature-icon">📖</span><div class="feature-title">Шпаргалки</div><div class="feature-desc">Формулы под рукой</div></div>
        <div class="feature-item"><span class="feature-icon">✂️</span><div class="feature-title">Сокращение</div><div class="feature-desc">Краткий пересказ</div></div>
        <div class="feature-item"><span class="feature-icon">📝</span><div class="feature-title">Тесты</div><div class="feature-desc">Генерация вопросов</div></div>
        <div class="feature-item"><span class="feature-icon">🔠</span><div class="feature-title">Синонимы</div><div class="feature-desc">Расширение словаря</div></div>
        <div class="feature-item"><span class="feature-icon">🌐</span><div class="feature-title">50+ языков</div><div class="feature-desc">Перевод любой сложности</div></div>
        <div class="feature-item"><span class="feature-icon">🎯</span><div class="feature-title">Фокус</div><div class="feature-desc">Режим концентрации</div></div>
        <div class="feature-item"><span class="feature-icon">🗣️</span><div class="feature-title">Озвучка</div><div class="feature-desc">Чтение текста голосом</div></div>
        <div class="feature-item"><span class="feature-icon">📊</span><div class="feature-title">Графики</div><div class="feature-desc">Построение функций</div></div>
        <div class="feature-item"><span class="feature-icon">🧬</span><div class="feature-title">Разбор ДНК</div><div class="feature-desc">Биология (демо)</div></div>
        <div class="feature-item"><span class="feature-icon">🏛️</span><div class="feature-title">Даты</div><div class="feature-desc">Историческая лента</div></div>
        <div class="feature-item"><span class="feature-icon">💡</span><div class="feature-title">Идеи</div><div class="feature-desc">Мозговой штурм</div></div>
        <div class="feature-item"><span class="feature-icon">📱</span><div class="feature-title">Оффлайн</div><div class="feature-desc">Сохранение ответов</div></div>
        <div class="feature-item"><span class="feature-icon">🛡️</span><div class="feature-title">Антиплагиат</div><div class="feature-desc">Проверка уникальности</div></div>
        <div class="feature-item"><span class="feature-icon">📈</span><div class="feature-title">Прогресс</div><div class="feature-desc">График обучения</div></div>
    </div>

    <!-- FAQ (СТАТЬИ) -->
    <div class="faq-section">
        <div class="faq-title">База знаний</div>
        
        <div class="faq-item" onclick="this.classList.toggle('active')">
            <div class="faq-q">📖 Бесплатно? <span>▼</span></div>
            <div class="faq-a">
                <b>Да, базовый функционал бесплатен.</b> Мы даем <b>3 задачи в день</b>, которые обновляются каждые 24 часа.<br>
                <h4>Что входит в бесплатный тариф:</h4>
                <ul><li>Решение базовых задач</li><li>Проверка текста</li><li>История</li></ul>
                <h4>Премиум:</h4> Снимает лимиты и дает приоритет.
            </div>
        </div>

        <div class="faq-item" onclick="this.classList.toggle('active')">
            <div class="faq-q">🧠 Точные ответы? <span>▼</span></div>
            <div class="faq-a">
                <b>Мы используем Google Gemma 3 12B.</b> Это нейросеть уровня отличника.<br><br>
                <b>Как обеспечивается точность:</b> Мы используем промпт, который заставляет ИИ решать по шагам. Но всегда проверяй сложные ответы — ИИ может ошибаться в 2-3% случаев.
            </div>
        </div>

        <div class="faq-item" onclick="this.classList.toggle('active')">
            <div class="faq-q">📸 Работает фото? <span>▼</span></div>
            <div class="faq-a">
                <b>Да, мы внедряем технологию OCR.</b> Ты наводишь камеру на учебник, нажимаешь "Фото", и ИИ распознает текст, вставив его в поле ввода. Тебе останется только проверить и нажать "Решить".
            </div>
        </div>

        <div class="faq-item" onclick="this.classList.toggle('active')">
            <div class="faq-q">💳 Как оплатить? <span>▼</span></div>
            <div class="faq-a">
                <b>Оплата картой РФ или СБП.</b><br>
                Нажми на Premium, выбери тариф и введи данные. Подписка продлевается автоматически, но ты можешь отменить её в любой момент в профиле.
            </div>
        </div>

        <div class="faq-item" onclick="this.classList.toggle('active')">
            <div class="faq-q">📚 Какие предметы? <span>▼</span></div>
            <div class="faq-a">
                Все школьные: Алгебра, Геометрия, Физика, Химия, Биология, История, Русский, Английский, Информатика и другие. Выбирай нужный в меню "Предметы", чтобы ИИ понял контекст.
            </div>
        </div>

        <div class="faq-item" onclick="this.classList.toggle('active')">
            <div class="faq-q">🔒 Безопасно? <span>▼</span></div>
            <div class="faq-a">
                <b>Абсолютно.</b> Мы не собираем личные данные. История хранится только в твоем браузере (LocalStorage). Никто, кроме тебя, её не увидит.
            </div>
        </div>
        
        <div class="faq-item" onclick="this.classList.toggle('active')">
            <div class="faq-q">🚀 Насколько быстро? <span>▼</span></div>
            <div class="faq-a">
                Обычно ответ занимает 3-5 секунд. С Premium-подпиской скорость возрастает до 1-2 секунд за счет приоритета на сервере.
            </div>
        </div>
        
        <div class="faq-item" onclick="this.classList.toggle('active')">
            <div class="faq-q">🎓 Подходит для ЕГЭ? <span>▼</span></div>
            <div class="faq-a">
                Да, отлично подходит. ИИ решает задачи из ОГЭ/ЕГЭ и объясняет их по шагам. Но мы советуем использовать его как помощника для проверки, а не просто для списывания.
            </div>
        </div>
    </div>
</div>

<!-- ПРОФИЛЬ -->
<div class="profile-card" id="profileModal">
    <div class="profile-header">
        <div class="avatar">А</div>
        <h2 style="font-size: 22px; font-weight: 800;">Андрей</h2>
        <div class="vip-badge" id="vipBadge">👑 VIP Аккаунт</div>
        <p style="color: var(--text-muted); font-size: 13px; margin-top: 5px;">В UchiAI с Ноября 2024</p>
    </div>
    
    <div style="background: var(--bg); padding: 15px; border-radius: 16px; margin-bottom: 15px;">
        <div style="display: flex; justify-content: space-between; font-size: 14px; font-weight: 700; margin-bottom: 8px;">
            <span>Лимит задач</span><span id="free-tasks-text">3 / 3</span>
        </div>
        <div class="progress-bar"><div class="progress-fill" id="progress-fill"></div></div>
    </div>

    <div class="stats-grid">
        <div class="stat-box"><div class="stat-val" id="stat-solved">0</div><div class="stat-label">Решено</div></div>
        <div class="stat-box"><div class="stat-val" id="stat-saved">0</div><div class="stat-label">В истории</div></div>
        <div class="stat-box"><div class="stat-val">12</div><div class="stat-label">Дней с нами</div></div>
    </div>

    <div class="profile-info">
        <span>Статус:</span>
        <span id="account-status" style="color: var(--success);">Базовый</span>
    </div>

    <div style="margin-top: 15px;">
        <p style="font-size: 12px; color: var(--text-muted); text-align: center; margin-bottom: 5px;">Достижения</p>
        <div class="achievements">
            <div class="achieve-icon unlocked" title="Первый шаг">🐣</div>
            <div class="achieve-icon" id="ach-solve" title="10 решений">🔥</div>
            <div class="achieve-icon" id="ach-premium" title="Premium">👑</div>
        </div>
    </div>

    <button class="btn-solve" style="width: 100%; margin-top: 20px;" onclick="closeProfile()">Закрыть</button>
    <div style="display: flex; gap: 10px; margin-top: 10px;">
        <button class="btn-close" style="flex: 1; background: transparent; border: 1px solid var(--border);" onclick="openPremium()">Сменить тариф</button>
        <button class="btn-close" style="flex: 1; background: transparent; border: 1px solid var(--danger); color: var(--danger);" onclick="resetAccount()">Сброс</button>
    </div>
</div>

<!-- ТАРИФЫ И ОПЛАТА -->
<div class="modal" id="premiumModal">
    <div class="modal-content" id="plansScreen">
        <div class="modal-header">
            <button class="btn-close-icon" onclick="closePremium()">✕</button>
            <div class="modal-title">Премиум подписка</div>
            <p style="color: var(--text-muted); font-size: 14px;">Выбери план</p>
        </div>
        
        <div class="plans-container">
            <div class="plan-card">
                <div class="plan-title">Старт</div>
                <div class="plan-price">0 ₽ <span>/ навсегда</span></div>
                <ul class="plan-features">
                    <li>3 задачи в день</li>
                    <li>Все школьные предметы</li>
                    <li class="disabled">Приоритетная скорость</li>
                </ul>
                <button class="btn-buy active" disabled>Текущий тариф</button>
            </div>

            <div class="plan-card popular">
                <div class="plan-badge">Рекомендуем</div>
                <div class="plan-title">Профи 🚀</div>
                <div class="plan-price">199 ₽ <span>/ месяц</span></div>
                <ul class="plan-features">
                    <li>Безлимитные задачи</li>
                    <li>Приоритетная скорость</li>
                    <li>Сканер фото</li>
                    <li>История без ограничений</li>
                </ul>
                <button class="btn-buy" id="btn-buy-pro" onclick="startPayment('Профи', 'btn-buy-pro')">Купить</button>
            </div>

            <div class="plan-card">
                <div class="plan-title">Максимум 🔥</div>
                <div class="plan-price">499 ₽ <span>/ 3 месяца</span></div>
                <ul class="plan-features">
                    <li>Всё из тарифа Профи</li>
                    <li>Выгода 30%</li>
                    <li>Доступ к базе конспектов</li>
                </ul>
                <button class="btn-buy" id="btn-buy-max" onclick="startPayment('Максимум', 'btn-buy-max')">Купить</button>
            </div>
        </div>
        <div style="text-align: center; margin-top: 20px;">
            <button class="btn-close" onclick="restorePurchases()" style="background: transparent; color: var(--text-muted); font-size: 13px;">Восстановить покупки</button>
        </div>
    </div>

    <!-- ЭКРАН ОПЛАТЫ -->
    <div class="modal-content" id="paymentScreen" style="display: none;">
        <div class="payment-screen">
            <div class="card-icon">💳</div>
            <h2 style="font-size: 22px; margin-bottom: 10px;">Оплата подписки</h2>
            <p style="color: var(--text-muted); font-size: 14px; margin-bottom: 20px;">Введи данные карты для активации</p>
            
            <input type="text" class="payment-input" placeholder="Номер карты (0000 0000 0000 0000)" maxlength="19">
            <div style="display: flex; gap: 10px;">
                <input type="text" class="payment-input" placeholder="ММ/ГГ" maxlength="5" style="width: 50%;">
                <input type="text" class="payment-input" placeholder="CVC" maxlength="3" style="width: 50%;">
            </div>
            
            <button class="btn-solve" style="width: 100%; margin-top: 20px;" onclick="confirmPayment()">Оплатить</button>
            <button class="btn-close" style="width: 100%; margin-top: 10px;" onclick="cancelPayment()">Отмена</button>
        </div>
    </div>
</div>

<div id="toast">Уведомление</div>

<script>
    let currentPlanToBuy = '';
    let currentBtnToUpdate = '';

    // ОПЛАТА
    function startPayment(plan, btnId) {
        currentPlanToBuy = plan;
        currentBtnToUpdate = btnId;
        document.getElementById('plansScreen').style.display = 'none';
        document.getElementById('paymentScreen').style.display = 'block';
    }

    function cancelPayment() {
        document.getElementById('paymentScreen').style.display = 'none';
        document.getElementById('plansScreen').style.display = 'block';
    }

    function confirmPayment() {
        const btn = document.getElementById(currentBtnToUpdate);
        btn.innerText = "Оплата...";
        btn.disabled = true;
        
        setTimeout(() => {
            localStorage.setItem('uchi_premium', 'true');
            localStorage.setItem('uchi_plan', currentPlanToBuy);
            
            btn.innerText = "Оплачено ✅";
            btn.classList.add('active');
            
            showToast('👑 Тариф ' + currentPlanToBuy + ' активирован!');
            updateStats();
            
            setTimeout(() => {
                closePremium();
                document.getElementById('paymentScreen').style.display = 'none';
                document.getElementById('plansScreen').style.display = 'block';
            }, 1500);
        }, 2000);
    }

    function restorePurchases() {
        let isPremium = localStorage.getItem('uchi_premium') === 'true';
        if(isPremium) {
            showToast('✅ Подписка ' + localStorage.getItem('uchi_plan') + ' восстановлена!');
            updateStats();
        } else {
            showToast('❌ Активных подписок не найдено.');
        }
    }

    function checkPremiumStatus() {
        let isPremium = localStorage.getItem('uchi_premium') === 'true';
        let plan = localStorage.getItem('uchi_plan');
        if(isPremium && plan) {
            if(plan === 'Профи') {
                const btn = document.getElementById('btn-buy-pro');
                if(btn) { btn.innerText = "Оплачено ✅"; btn.classList.add('active'); btn.disabled = true; }
            } else if(plan === 'Максимум') {
                const btn = document.getElementById('btn-buy-max');
                if(btn) { btn.innerText = "Оплачено ✅"; btn.classList.add('active'); btn.disabled = true; }
            }
        }
    }

    function resetAccount() {
        if(confirm('Ты уверен, что хочешь сбросить весь прогресс и подписки?')) {
            localStorage.clear();
            location.reload();
        }
    }

    // УМНЫЙ СТАРТ
    function setSmart(subject, el) {
        const ta = document.getElementById('task');
        ta.value = `Предмет: ${subject}\\nЗадача: ` + ta.value.replace(/Предмет: .*\\nЗадача: /, '');
        document.querySelectorAll('.subject').forEach(s => s.classList.remove('active'));
        el.classList.add('active');
        ta.focus();
    }

    // ФОТО
    function handlePhoto(input) {
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            reader.onload = function(e) {
                document.getElementById('previewImg').src = e.target.result;
                document.getElementById('photoPreview').style.display = 'block';
                document.getElementById('photoText').innerText = "Сканируется...";
                showToast('Распознаю текст...');
                setTimeout(() => {
                    document.getElementById('photoText').innerText = "Готово";
                    document.getElementById('task').value += "\\n[Текст с фото распознан!]";
                }, 2000);
            }
            reader.readAsDataURL(input.files[0]);
        }
    }

    // ВКЛАДКИ
    function switchTab(tabId, element) {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.card').forEach(c => c.classList.remove('active'));
        element.classList.add('active');
        document.getElementById('tab-' + tabId).classList.add('active');
        if(tabId === 'history') renderHistory();
    }

    // СТАТИСТИКА
    function updateStats() {
        let history = JSON.parse(localStorage.getItem('uchi_history') || '[]');
        let solved = parseInt(localStorage.getItem('uchi_solved') || '0');
        let isPremium = localStorage.getItem('uchi_premium') === 'true';
        let plan = localStorage.getItem('uchi_plan') || '';

        document.getElementById('stat-solved').innerText = solved;
        document.getElementById('stat-saved').innerText = history.length;
        
        if(solved >= 10) document.getElementById('ach-solve').classList.add('unlocked');
        if(isPremium) document.getElementById('ach-premium').classList.add('unlocked');

        if(isPremium) {
            document.getElementById('vipBadge').style.display = 'inline-block';
            document.getElementById('vipBadge').innerText = '👑 ' + plan;
            document.getElementById('account-status').innerText = plan;
            document.getElementById('account-status').style.color = 'var(--premium)';
            document.getElementById('free-tasks-text').innerText = "∞ / ∞";
            document.getElementById('progress-fill').style.width = "100%";
            document.getElementById('progress-fill').style.background = "var(--premium)";
        } else {
            document.getElementById('vipBadge').style.display = 'none';
            document.getElementById('account-status').innerText = "Базовый";
            document.getElementById('account-status').style.color = 'var(--success)';
            let freeUsed = parseInt(localStorage.getItem('uchi_free_used') || '0');
            let left = Math.max(0, 3 - freeUsed);
            document.getElementById('free-tasks-text').innerText = left + " / 3";
            document.getElementById('progress-fill').style.width = (left / 3 * 100) + "%";
            document.getElementById('progress-fill').style.background = left === 0 ? 'var(--danger)' : 'var(--success)';
        }
        checkPremiumStatus();
    }

    // МОДАЛКИ
    function openProfile() { updateStats(); document.getElementById('profileModal').style.display = 'block'; }
    function closeProfile() { document.getElementById('profileModal').style.display = 'none'; }
    function openPremium() { checkPremiumStatus(); document.getElementById('premiumModal').style.display = 'flex'; document.getElementById('plansScreen').style.display = 'block'; document.getElementById('paymentScreen').style.display = 'none'; }
    function closePremium() { document.getElementById('premiumModal').style.display = 'none'; }
    
    // ОБЩИЕ ФУНКЦИИ
    function toggleDarkMode() { document.body.classList.toggle('dark'); document.getElementById('themeBtn').innerText = document.body.classList.contains('dark') ? '☀️' : '🌙'; }
    function showToast(msg) { const toast = document.getElementById("toast"); toast.innerText = msg; toast.className = "show"; setTimeout(() => { toast.className = toast.className.replace("show", ""); }, 3000); }
    function clearText(inp, res) { document.getElementById(inp).value = ''; document.getElementById(res).style.display = 'none'; }
    function copyResult(id) { const t = document.getElementById(id).innerText; if(t) navigator.clipboard.writeText(t).then(() => showToast('Скопировано!')); }
    function shareResult(id) {
        const t = document.getElementById(id).innerText;
        if(navigator.share) {
            navigator.share({ title: 'Мое решение от UchiAI', text: t }).catch(() => {});
        } else {
            showToast('Поделиться не поддерживается на этом устройстве');
        }
    }
    
    // ИСТОРИЯ
    function saveHistory() {
        const q = document.getElementById('task').value;
        const a = document.getElementById('text-reshatel').innerText;
        if(!q || !a) return showToast('Сначала реши задачу!');
        let history = JSON.parse(localStorage.getItem('uchi_history') || '[]');
        history.unshift({ q: q, a: a });
        localStorage.setItem('uchi_history', JSON.stringify(history));
        showToast('Сохранено! ✅');
        updateStats();
    }
    function renderHistory() {
        const list = document.getElementById('historyList');
        let history = JSON.parse(localStorage.getItem('uchi_history') || '[]');
        list.innerHTML = history.map(item => `<div class="history-item"><div class="history-q">${item.q}</div><div class="history-a">${item.a}</div></div>`).join('');
    }

    // ДВИЖОК
    async function solve(type) {
        const btn = document.getElementById('btn-solve-' + type);
        let prompt = document.getElementById('task').value;
        if (type === 'notes') prompt = "Сделай конспект: " + document.getElementById('notes-input').value;
        if (type === 'check') prompt = "Найди ошибки: " + document.getElementById('check-input').value;
        if (type === 'translate') prompt = "Переведи: " + document.getElementById('translate-input').value;

        if(!prompt.trim()) return showToast('Введи текст!');
        
        let isPremium = localStorage.getItem('uchi_premium') === 'true';
        if(type === 'reshatel' && !isPremium) {
            let freeUsed = parseInt(localStorage.getItem('uchi_free_used') || '0');
            if(freeUsed >= 3) return showToast('Лимит! Купи Premium.');
            localStorage.setItem('uchi_free_used', freeUsed + 1);
        }
        let solved = parseInt(localStorage.getItem('uchi_solved') || '0');
        localStorage.setItem('uchi_solved', solved + 1);

        const loader = document.getElementById('loader-' + type);
        const resBox = document.getElementById('result-' + type);
        const textBox = document.getElementById('text-' + type);
        
        btn.disabled = true; btn.style.opacity = '0.7';
        loader.style.display = 'block'; resBox.style.display = 'none';
        
        try {
            const response = await fetch('/solve', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({task: prompt})
            });
            const data = await response.json();
            textBox.innerHTML = data.answer.replace(/\\*\\*/g, '').replace(/\\n/g, '<br>');
            resBox.style.display = 'block';
        } catch (e) {
            textBox.innerHTML = 'Ошибка сети';
            resBox.style.display = 'block';
        } finally {
            loader.style.display = 'none';
            btn.disabled = false; btn.style.opacity = '1';
        }
    }
    
    document.addEventListener('DOMContentLoaded', () => {
        updateStats();
    });
</script>

</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/solve', methods=['POST'])
def solve():
    data = request.json
    task = data.get('task')
    if not API_KEY: return jsonify({"answer": "Нет ключа"})
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Ты школьный помощник. Отвечай без ** и с переносами строк."},
            {"role": "user", "content": task}
        ]
    }
    try:
        res = requests.post(API_URL, headers=headers, json=payload).json()
        answer = res['choices'][0]['message']['content'] if 'choices' in res else "Ошибка ИИ"
    except: answer = "Ошибка сети"
    return jsonify({"answer": answer})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

