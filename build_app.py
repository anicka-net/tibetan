#!/usr/bin/env python3
"""Build the Tibetan learning app from lesson_data.json."""

import json
from pathlib import Path

with open('lesson_data.json', 'r', encoding='utf-8') as f:
    lessons = json.load(f)

# Compact JSON for embedding
lesson_json = json.dumps(lessons, ensure_ascii=False, separators=(',', ':'))

html = f'''<!DOCTYPE html>
<html lang="bo">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>བོད་སྐད་སློབ་ཚན། - Tibetan Lessons</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Tibetan:wght@400;700&display=swap');

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

:root {{
  --green: #58CC02;
  --green-dark: #46a302;
  --red: #FF4B4B;
  --red-light: #FFF0F0;
  --blue: #1CB0F6;
  --gold: #FFC800;
  --gray-light: #E5E5E5;
  --gray: #AFAFAF;
  --gray-dark: #4B4B4B;
  --bg: #FFFFFF;
  --text: #3C3C3C;
}}

body {{
  font-family: 'Noto Sans Tibetan', -apple-system, BlinkMacSystemFont, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  overflow-x: hidden;
  -webkit-tap-highlight-color: transparent;
}}

/* Header */
.header {{
  display: flex;
  align-items: center;
  padding: 12px 16px;
  gap: 12px;
  position: sticky;
  top: 0;
  background: var(--bg);
  z-index: 10;
  border-bottom: 1px solid var(--gray-light);
}}

.back-btn, .close-btn {{
  background: none;
  border: none;
  font-size: 24px;
  color: var(--gray);
  cursor: pointer;
  padding: 4px;
  line-height: 1;
}}

.progress-bar {{
  flex: 1;
  height: 16px;
  background: var(--gray-light);
  border-radius: 8px;
  overflow: hidden;
}}

.progress-fill {{
  height: 100%;
  background: var(--green);
  border-radius: 8px;
  transition: width 0.4s ease;
}}

.hearts {{
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 18px;
  color: var(--red);
  font-family: sans-serif;
}}

.hearts span {{
  font-weight: 700;
  font-size: 16px;
  margin-left: 2px;
}}

/* Main content */
.content {{
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px 20px;
  max-width: 600px;
  width: 100%;
  margin: 0 auto;
}}

/* Screens */
.screen {{ display: none; flex-direction: column; flex: 1; }}
.screen.active {{ display: flex; }}

/* Title bar */
.title-bar {{
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 0 12px;
}}

.title-bar h1 {{
  font-size: 24px;
  flex: 1;
}}

.title-bar .subtitle {{
  font-size: 14px;
  color: var(--gray);
}}

/* Level cards */
.level-card {{
  background: white;
  border: 2px solid var(--gray-light);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  gap: 16px;
}}

.level-card:active {{ transform: scale(0.98); }}
.level-card.completed {{ border-color: var(--green); }}

.level-badge {{
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
  flex-shrink: 0;
  font-family: sans-serif;
  color: white;
}}

.level-badge.a0 {{ background: linear-gradient(135deg, #9B59B6, #8E44AD); }}
.level-badge.a1 {{ background: linear-gradient(135deg, #3498DB, #2980B9); }}
.level-badge.a2 {{ background: linear-gradient(135deg, #E67E22, #D35400); }}
.level-badge.b1 {{ background: linear-gradient(135deg, #27AE60, #229954); }}

.level-info {{ flex: 1; }}
.level-info h3 {{ font-size: 17px; margin-bottom: 4px; }}
.level-info p {{ font-size: 13px; color: var(--gray); font-family: sans-serif; }}

.level-progress {{
  width: 100%;
  height: 6px;
  background: var(--gray-light);
  border-radius: 3px;
  margin-top: 8px;
  overflow: hidden;
}}

.level-progress-fill {{
  height: 100%;
  background: var(--green);
  border-radius: 3px;
  transition: width 0.3s;
}}

/* Lesson cards */
.lesson-card {{
  background: white;
  border: 2px solid var(--gray-light);
  border-radius: 16px;
  padding: 16px 20px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  gap: 14px;
}}

.lesson-card:active {{ transform: scale(0.98); }}
.lesson-card.completed {{ border-color: var(--green); }}
.lesson-card.locked {{ opacity: 0.5; pointer-events: none; }}

.lesson-icon {{
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
  flex-shrink: 0;
  font-family: sans-serif;
}}

.lesson-icon.green {{ background: #E8F8D8; color: var(--green); }}
.lesson-icon.blue {{ background: #DDF4FF; color: var(--blue); }}
.lesson-icon.gold {{ background: #FFF8E0; color: var(--gold); }}
.lesson-icon.locked {{ background: var(--gray-light); color: var(--gray); }}

.lesson-info {{ flex: 1; }}
.lesson-info h3 {{ font-size: 15px; margin-bottom: 2px; }}
.lesson-info p {{ font-size: 12px; color: var(--gray); font-family: sans-serif; }}

/* Streak banner */
.streak-banner {{
  text-align: center;
  padding: 16px;
  margin-bottom: 20px;
  background: linear-gradient(135deg, #FFF8E0, #FFF0D0);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
}}

.streak-number {{
  font-size: 36px;
  font-weight: 700;
  color: var(--gold);
  font-family: sans-serif;
}}

.streak-label {{
  font-size: 14px;
  color: var(--gray-dark);
}}

.xp-badge {{
  font-size: 14px;
  color: var(--gold);
  font-weight: 700;
  font-family: sans-serif;
}}

/* Exercise styles */
.exercise-prompt {{
  font-size: 16px;
  color: var(--gray-dark);
  margin-bottom: 16px;
  font-family: sans-serif;
  font-weight: 600;
}}

.tibetan-large {{
  font-size: 28px;
  font-weight: 700;
  line-height: 1.8;
  margin-bottom: 12px;
}}

.tibetan-medium {{
  font-size: 20px;
  line-height: 1.8;
  margin-bottom: 8px;
}}

.english-text {{
  font-size: 18px;
  font-family: sans-serif;
  color: var(--gray-dark);
  margin-bottom: 8px;
}}

.english-small {{
  font-size: 14px;
  font-family: sans-serif;
  color: var(--gray);
}}

.flashcard {{
  background: white;
  border: 2px solid var(--gray-light);
  border-radius: 16px;
  padding: 32px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 16px;
}}

.flashcard .revealed-content {{ display: none; margin-top: 16px; border-top: 1px solid var(--gray-light); padding-top: 16px; }}
.flashcard.revealed .revealed-content {{ display: block; }}
.flashcard.revealed .reveal-hint {{ display: none; }}

.reveal-hint {{
  font-size: 14px;
  color: var(--gray);
  margin-top: 8px;
  font-family: sans-serif;
}}

.definition-box {{
  background: #F8F8F8;
  border-radius: 12px;
  padding: 12px;
  text-align: left;
}}

/* Options */
.options {{ display: flex; flex-direction: column; gap: 10px; margin-top: 16px; }}

.option-btn {{
  width: 100%;
  padding: 14px 16px;
  border: 2px solid var(--gray-light);
  border-radius: 12px;
  background: white;
  font-size: 20px;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s;
  font-family: 'Noto Sans Tibetan', sans-serif;
  line-height: 1.6;
}}

.option-btn:active {{ transform: scale(0.98); }}
.option-btn.selected {{ border-color: var(--blue); background: #F0F8FF; }}
.option-btn.correct {{ border-color: var(--green); background: #E8F8D8; }}
.option-btn.incorrect {{ border-color: var(--red); background: var(--red-light); animation: shake 0.3s; }}
.option-btn.disabled {{ pointer-events: none; }}

/* Match */
.match-container {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 16px;
}}

.match-btn {{
  padding: 12px 10px;
  border: 2px solid var(--gray-light);
  border-radius: 12px;
  background: white;
  font-size: 18px;
  cursor: pointer;
  transition: all 0.15s;
  text-align: center;
  font-family: 'Noto Sans Tibetan', sans-serif;
  min-height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1.6;
}}

.match-btn.selected {{ border-color: var(--blue); background: #F0F8FF; }}
.match-btn.matched {{ border-color: var(--green); background: #E8F8D8; opacity: 0.7; pointer-events: none; }}
.match-btn.wrong {{ border-color: var(--red); background: var(--red-light); animation: shake 0.3s; }}

/* Fill blank */
.sentence-box {{
  font-size: 20px;
  line-height: 2;
  padding: 20px;
  background: #F8F8F8;
  border-radius: 16px;
  margin: 16px 0;
}}

.blank-slot {{
  display: inline-block;
  min-width: 60px;
  border-bottom: 3px solid var(--blue);
  text-align: center;
  padding: 2px 8px;
  margin: 0 4px;
}}

.blank-slot.filled {{ border-color: var(--green); background: #E8F8D8; border-radius: 6px; }}

.word-bank {{ display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }}

.word-chip {{
  padding: 10px 18px;
  border: 2px solid var(--gray-light);
  border-radius: 20px;
  background: white;
  font-size: 16px;
  cursor: pointer;
  font-family: 'Noto Sans Tibetan', sans-serif;
  transition: all 0.15s;
}}

.word-chip:active {{ transform: scale(0.95); }}
.word-chip.used {{ border-color: var(--green); background: #E8F8D8; }}

/* Grammar box */
.grammar-box {{
  background: #F0F0FF;
  border: 2px solid #E0E0F0;
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 20px;
}}

.grammar-box h3 {{
  font-size: 16px;
  color: #6B6BCC;
  margin-bottom: 12px;
  font-family: sans-serif;
}}

.grammar-pattern {{
  font-size: 24px;
  text-align: center;
  padding: 16px;
  margin-bottom: 12px;
  font-weight: 700;
}}

.grammar-example {{
  padding: 12px;
  background: white;
  border-radius: 8px;
  margin-bottom: 8px;
}}

/* Reading */
.reading-box {{
  background: #FFFBF0;
  border: 2px solid #F0E8D0;
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 20px;
  font-size: 18px;
  line-height: 2;
}}

/* Bottom bar */
.bottom-bar {{
  padding: 16px 20px;
  max-width: 600px;
  width: 100%;
  margin: 0 auto;
}}

.check-btn {{
  width: 100%;
  padding: 16px;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s;
  font-family: sans-serif;
  text-transform: uppercase;
  letter-spacing: 1px;
}}

.check-btn:active {{ transform: scale(0.98); }}

.check-btn.primary {{
  background: var(--green);
  color: white;
  box-shadow: 0 4px 0 var(--green-dark);
}}

.check-btn.primary:active {{
  box-shadow: 0 2px 0 var(--green-dark);
  transform: translateY(2px);
}}

.check-btn.disabled {{
  background: var(--gray-light);
  color: var(--gray);
  box-shadow: 0 4px 0 #D0D0D0;
  pointer-events: none;
}}

.check-btn.next {{
  background: var(--green);
  color: white;
  box-shadow: 0 4px 0 var(--green-dark);
}}

/* Feedback */
.feedback-bar {{
  padding: 16px 20px;
  border-radius: 12px;
  margin-bottom: 12px;
  display: none;
}}

.feedback-bar.correct {{ background: #E8F8D8; color: var(--green-dark); display: block; }}
.feedback-bar.incorrect {{ background: var(--red-light); color: #CC3333; display: block; }}
.feedback-bar h4 {{ font-size: 16px; margin-bottom: 4px; font-family: sans-serif; }}
.feedback-bar p {{ font-size: 14px; }}

/* Complete screen */
.complete-screen {{
  text-align: center;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}}

.complete-icon {{ font-size: 80px; margin-bottom: 16px; font-family: sans-serif; }}
.complete-title {{ font-size: 28px; font-weight: 700; margin-bottom: 8px; font-family: sans-serif; }}
.complete-subtitle {{ font-size: 16px; color: var(--gray); margin-bottom: 32px; font-family: sans-serif; }}

.xp-display {{
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 20px;
  font-weight: 700;
  color: var(--gold);
  margin-bottom: 8px;
  font-family: sans-serif;
}}

.stats-row {{
  display: flex;
  gap: 32px;
  justify-content: center;
  margin-bottom: 32px;
}}

.stat {{ text-align: center; font-family: sans-serif; }}
.stat-value {{ font-size: 24px; font-weight: 700; }}
.stat-label {{ font-size: 12px; color: var(--gray); }}

.proverb-box {{
  background: linear-gradient(135deg, #FFF8E0, #FFF0D0);
  border-radius: 16px;
  padding: 24px;
  text-align: center;
  margin-bottom: 24px;
  max-width: 400px;
}}

/* Dialogue bubble */
.dialogue-bubble {{
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 8px;
}}

.dialogue-bubble.speaker-a {{ background: #E8F5FF; }}
.dialogue-bubble.speaker-b {{ background: #E8F8D8; }}

.dialogue-speaker {{
  font-weight: 700;
  font-size: 13px;
  margin-bottom: 4px;
  font-family: sans-serif;
}}

/* Animations */
@keyframes shake {{
  0%, 100% {{ transform: translateX(0); }}
  25% {{ transform: translateX(-6px); }}
  75% {{ transform: translateX(6px); }}
}}

@keyframes fadeIn {{
  from {{ opacity: 0; transform: translateY(10px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}

.animate-in {{ animation: fadeIn 0.3s ease; }}

@keyframes confetti {{
  0% {{ transform: translateY(0) rotate(0deg); opacity: 1; }}
  100% {{ transform: translateY(-200px) rotate(720deg); opacity: 0; }}
}}

.confetti-piece {{
  position: fixed;
  width: 10px;
  height: 10px;
  border-radius: 2px;
  animation: confetti 1.5s ease-out forwards;
  pointer-events: none;
  z-index: 100;
}}

/* Empty state */
.empty-state {{
  text-align: center;
  padding: 40px 20px;
  color: var(--gray);
}}

.empty-state .icon {{ font-size: 48px; margin-bottom: 16px; font-family: sans-serif; }}
.empty-state p {{ font-size: 14px; font-family: sans-serif; }}
</style>
</head>
<body>

<!-- Header (for exercise mode) -->
<div class="header" id="exHeader" style="display:none;">
  <button class="close-btn" onclick="goBack()">&times;</button>
  <div class="progress-bar">
    <div class="progress-fill" id="progressFill" style="width:0%"></div>
  </div>
  <div class="hearts" id="heartsDisplay">
    <span style="font-family:sans-serif">&#10084;</span>
    <span id="heartsCount">3</span>
  </div>
</div>

<!-- Nav header (for browsing) -->
<div class="header" id="navHeader" style="display:none;">
  <button class="back-btn" onclick="goBack()">&#8592;</button>
  <div style="flex:1;font-weight:700;font-size:17px;" id="navTitle"></div>
  <div class="xp-badge" id="navXp"></div>
</div>

<!-- Content -->
<div class="content" id="content">

  <!-- Home screen -->
  <div class="screen active" id="homeScreen">
    <div style="padding-top:16px">
      <div style="font-size:28px;font-weight:700;text-align:center;margin-bottom:4px;">བོད་སྐད་སློབ་ཚན།</div>
      <div style="font-size:16px;color:var(--gray);text-align:center;margin-bottom:20px;">Tibetan Language Lessons</div>

      <div class="streak-banner">
        <div>
          <div class="streak-number" id="streakNumber">0</div>
          <div class="streak-label">day streak</div>
        </div>
        <div style="border-left:1px solid #E0D8C0;height:40px;"></div>
        <div>
          <div class="streak-number" id="totalXpDisplay" style="color:var(--blue);">0</div>
          <div class="streak-label">total XP</div>
        </div>
      </div>

      <div id="levelCards"></div>
    </div>
  </div>

  <!-- Level screen -->
  <div class="screen" id="levelScreen">
    <div id="lessonCards"></div>
  </div>

  <!-- Exercise screen -->
  <div class="screen" id="exerciseScreen"></div>

  <!-- Complete screen -->
  <div class="screen" id="completeScreen">
    <div class="complete-screen">
      <div class="complete-icon">&#127942;</div>
      <div class="complete-title">Lesson Complete!</div>
      <div class="complete-subtitle" id="completeSubtitle">Great work!</div>
      <div class="xp-display">+<span id="xpEarned">0</span> XP</div>
      <div class="stats-row">
        <div class="stat">
          <div class="stat-value" id="statCorrect">0</div>
          <div class="stat-label">Correct</div>
        </div>
        <div class="stat">
          <div class="stat-value" id="statAccuracy">0%</div>
          <div class="stat-label">Accuracy</div>
        </div>
        <div class="stat">
          <div class="stat-value" id="statStreak">0</div>
          <div class="stat-label">Day Streak</div>
        </div>
      </div>
      <div class="proverb-box" id="proverbBox" style="display:none;">
        <div class="tibetan-medium" id="proverbText"></div>
      </div>
    </div>
  </div>
</div>

<!-- Bottom bar -->
<div class="bottom-bar" id="bottomBar" style="display:none;">
  <div class="feedback-bar" id="feedbackBar"></div>
  <div id="prevLink" style="display:none;text-align:center;margin-bottom:8px;">
    <a href="#" onclick="prevExercise();return false;" style="color:var(--gray);font-family:sans-serif;font-size:14px;text-decoration:none;">&larr; Previous</a>
  </div>
  <button class="check-btn disabled" id="checkBtn" onclick="handleCheck()">Check</button>
</div>

<div class="bottom-bar" id="completeBar" style="display:none;">
  <button class="check-btn primary" onclick="goBack()">Continue</button>
</div>

<script>
// ===== LESSON DATA =====
const ALL_LESSONS = {lesson_json};

// ===== DATA STRUCTURES =====
const LEVELS = [
  {{ id: 'A1', name: 'Beginner', nameBo: 'གནས་ཚད་དང་པོ།', desc: '13 lessons, greetings to colors', css: 'a1' }},
  {{ id: 'A2', name: 'Elementary', nameBo: 'གནས་ཚད་གཉིས་པ།', desc: '13 lessons, daily life to homeland', css: 'a2' }},
  {{ id: 'B1', name: 'Intermediate', nameBo: 'གནས་ཚད་གསུམ་པ།', desc: '13 lessons, culture to destiny', css: 'b1' }},
];

function getLessonsForLevel(levelId) {{
  return ALL_LESSONS.filter(l => l.level === levelId);
}}

function getLessonGroups(levelId) {{
  const lessons = getLessonsForLevel(levelId);
  const groups = {{}};
  for (const l of lessons) {{
    const key = l.lesson;
    if (!groups[key]) groups[key] = {{ lesson: key, topicBo: l.topicBo, topicEn: l.topicEn, subs: [] }};
    groups[key].subs.push(l);
  }}
  return Object.values(groups).sort((a, b) => a.lesson - b.lesson);
}}

// ===== STATE =====
let nav = ['home']; // navigation stack
let currentLevel = null;
let currentLesson = null; // the sub-lesson data object

let state = {{
  exercises: [],
  currentEx: 0,
  hearts: 3,
  correct: 0,
  total: 0,
  xp: 0,
  selectedAnswer: null,
  checked: false,
  matchState: null,
}};

// ===== PROGRESS =====
function loadProgress() {{
  try {{ return JSON.parse(localStorage.getItem('tibetan_progress') || '{{}}'); }}
  catch {{ return {{}}; }}
}}

function saveProgress(key, value) {{
  const data = loadProgress();
  data[key] = value;
  localStorage.setItem('tibetan_progress', JSON.stringify(data));
}}

function getLessonKey(lesson) {{
  return `${{lesson.level}}_${{lesson.lesson}}_${{lesson.sub}}`;
}}

function isLessonCompleted(lesson) {{
  const data = loadProgress();
  return (data[getLessonKey(lesson) + '_best'] || 0) > 0;
}}

function getStreak() {{
  const data = loadProgress();
  const today = new Date().toISOString().slice(0, 10);
  if (data.lastDay === today) return data.streak || 0;
  const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
  if (data.lastDay === yesterday) return data.streak || 0;
  return 0;
}}

function updateStreak() {{
  const data = loadProgress();
  const today = new Date().toISOString().slice(0, 10);
  if (data.lastDay === today) return;
  const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
  data.streak = (data.lastDay === yesterday) ? (data.streak || 0) + 1 : 1;
  data.lastDay = today;
  localStorage.setItem('tibetan_progress', JSON.stringify(data));
}}

// ===== NAVIGATION =====
function showScreen(name) {{
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(name + 'Screen').classList.add('active');
}}

function goBack() {{
  if (nav.length > 1) {{
    nav.pop();
    const dest = nav[nav.length - 1];
    if (dest === 'home') showHome();
    else if (dest === 'level') showLevel(currentLevel);
    else showHome();
  }} else {{
    showHome();
  }}
}}

function showHome() {{
  nav = ['home'];
  currentLevel = null;
  currentLesson = null;
  document.getElementById('exHeader').style.display = 'none';
  document.getElementById('navHeader').style.display = 'none';
  document.getElementById('bottomBar').style.display = 'none';
  document.getElementById('completeBar').style.display = 'none';
  showScreen('home');
  renderHome();
}}

function showLevel(levelId) {{
  currentLevel = levelId;
  if (nav[nav.length - 1] !== 'level') nav.push('level');
  document.getElementById('exHeader').style.display = 'none';
  document.getElementById('navHeader').style.display = 'flex';
  document.getElementById('bottomBar').style.display = 'none';
  document.getElementById('completeBar').style.display = 'none';

  const level = LEVELS.find(l => l.id === levelId);
  document.getElementById('navTitle').textContent = level.nameBo + ' ' + level.name;
  const data = loadProgress();
  document.getElementById('navXp').textContent = (data.totalXp || 0) + ' XP';

  showScreen('level');
  renderLevelScreen(levelId);
}}

function startExercise(lessonData) {{
  currentLesson = lessonData;
  nav.push('exercise');
  state.hearts = 3;
  state.correct = 0;
  state.total = 0;
  state.xp = 0;
  state.currentEx = 0;
  state.checked = false;
  state.selectedAnswer = null;
  state.exercises = generateExercises(lessonData);

  if (state.exercises.length === 0) {{
    // No exercises available
    alert('This lesson has no exercises yet. Content coming soon!');
    nav.pop();
    return;
  }}

  document.getElementById('exHeader').style.display = 'flex';
  document.getElementById('navHeader').style.display = 'none';
  document.getElementById('bottomBar').style.display = 'block';
  document.getElementById('completeBar').style.display = 'none';
  showScreen('exercise');
  renderExercise();
}}

// ===== RENDERING: HOME =====
function renderHome() {{
  const data = loadProgress();
  document.getElementById('streakNumber').textContent = getStreak();
  document.getElementById('totalXpDisplay').textContent = data.totalXp || 0;

  let html = '';
  for (const level of LEVELS) {{
    const lessons = getLessonsForLevel(level.id);
    const completed = lessons.filter(l => isLessonCompleted(l)).length;
    const total = lessons.length;
    const pct = total > 0 ? Math.round((completed / total) * 100) : 0;
    const isDone = pct === 100;

    html += `
      <div class="level-card${{isDone ? ' completed' : ''}}" onclick="showLevel('${{level.id}}')">
        <div class="level-badge ${{level.css}}">${{level.id}}</div>
        <div class="level-info">
          <h3>${{level.nameBo}}</h3>
          <p>${{level.name}} &mdash; ${{level.desc}}</p>
          <div class="level-progress">
            <div class="level-progress-fill" style="width:${{pct}}%"></div>
          </div>
          <p style="margin-top:4px;font-size:11px;">${{completed}}/${{total}} sub-lessons</p>
        </div>
      </div>
    `;
  }}
  document.getElementById('levelCards').innerHTML = html;
}}

// ===== RENDERING: LEVEL =====
function renderLevelScreen(levelId) {{
  const groups = getLessonGroups(levelId);
  let html = '';

  if (groups.length === 0) {{
    html = `
      <div class="empty-state">
        <div class="icon">&#128218;</div>
        <p>No lessons available for this level.</p>
      </div>
    `;
  }} else {{
    const colors = ['green', 'blue', 'gold'];
    let idx = 0;
    for (const group of groups) {{
      // Lesson header
      html += `<div style="padding:12px 0 4px;font-size:13px;color:var(--gray);font-family:sans-serif;font-weight:600;">
        Lesson ${{group.lesson}}: ${{group.topicEn}}</div>`;

      for (const sub of group.subs.sort((a, b) => a.sub - b.sub)) {{
        const color = colors[idx % 3];
        const done = isLessonCompleted(sub);
        const content = getContentSummary(sub);
        const key = getLessonKey(sub);
        const num = `${{group.lesson}}.${{sub.sub}}`;

        html += `
          <div class="lesson-card${{done ? ' completed' : ''}}" onclick='startExercise(ALL_LESSONS[${{ALL_LESSONS.indexOf(sub)}}])'>
            <div class="lesson-icon ${{color}}">${{num}}</div>
            <div class="lesson-info">
              <h3>${{sub.topicBo}}</h3>
              <p>${{content}}</p>
            </div>
          </div>
        `;
        idx++;
      }}
    }}
  }}
  document.getElementById('lessonCards').innerHTML = html;
}}

function getContentSummary(lesson) {{
  const parts = [];
  if (lesson.vocab.length > 0) parts.push(lesson.vocab.length + ' vocab');
  if (lesson.phrases.length > 0) parts.push(lesson.phrases.length + ' phrases');
  if (lesson.fillBlanks.length > 0) parts.push(lesson.fillBlanks.length + ' exercises');
  if (lesson.proverb) parts.push('proverb');
  return parts.join(' \\u00B7 ') || 'Coming soon';
}}


// ===== EXERCISE GENERATION =====
function shuffle(arr) {{
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {{
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }}
  return a;
}}

function pickRandom(arr, n, exclude) {{
  const filtered = arr.filter(x => x !== exclude);
  return shuffle(filtered).slice(0, n);
}}

function generateExercises(lesson) {{
  const exercises = [];
  const vocab = lesson.vocab || [];
  const phrases = lesson.phrases || [];
  const fillBlanks = lesson.fillBlanks || [];
  const dialogue = lesson.dialogue || [];
  const proverb = lesson.proverb;

  // Vocab with English translations
  const vocabWithEn = vocab.filter(v => v.en);
  // Vocab with Tibetan definitions
  const vocabWithDef = vocab.filter(v => v.defBo);

  // 1. Vocab flashcards (max 8)
  const flashcardVocab = shuffle(vocab).slice(0, 8);
  for (const v of flashcardVocab) {{
    exercises.push({{ type: 'flashcard', data: v }});
  }}

  // 2. If enough translated vocab: MC bo->en
  if (vocabWithEn.length >= 4) {{
    const pool = vocabWithEn;
    for (const v of shuffle(pool).slice(0, Math.min(5, pool.length))) {{
      const wrongs = pickRandom(pool, 3, v).map(w => w.en);
      if (wrongs.length >= 3) {{
        exercises.push({{
          type: 'mc_bo_en',
          prompt: v.bo,
          correct: v.en,
          options: shuffle([v.en, ...wrongs])
        }});
      }}
    }}

    // MC en->bo
    for (const v of shuffle(pool).slice(0, Math.min(4, pool.length))) {{
      const wrongs = pickRandom(pool, 3, v).map(w => w.bo);
      if (wrongs.length >= 3) {{
        exercises.push({{
          type: 'mc_en_bo',
          prompt: v.en,
          correct: v.bo,
          options: shuffle([v.bo, ...wrongs])
        }});
      }}
    }}

    // Match pairs (if 5+)
    if (pool.length >= 5) {{
      const matchItems = shuffle(pool).slice(0, 5);
      exercises.push({{
        type: 'match',
        pairs: matchItems.map(v => ({{ bo: v.bo, en: v.en }}))
      }});
    }}
  }}
  // 3. If not enough English but have definitions: MC word->definition
  else if (vocabWithDef.length >= 4) {{
    const pool = vocabWithDef;
    for (const v of shuffle(pool).slice(0, Math.min(5, pool.length))) {{
      const wrongs = pickRandom(pool, 3, v).map(w => w.defBo.slice(0, 50));
      if (wrongs.length >= 3) {{
        exercises.push({{
          type: 'mc_bo_def',
          prompt: v.bo,
          correct: v.defBo.slice(0, 50),
          correctFull: v.defBo,
          options: shuffle([v.defBo.slice(0, 50), ...wrongs])
        }});
      }}
    }}
  }}

  // 4. Phrase flashcards (only include phrases that have English translations)
  const phrasesWithEn = phrases.filter(p => typeof p === 'object' && p.en);
  for (const p of shuffle(phrasesWithEn).slice(0, 6)) {{
    exercises.push({{ type: 'flashcard_phrase', data: p }});
  }}

  // 5. Fill-in-blank from textbook
  const validBlanks = fillBlanks.filter(fb => fb.sentence && fb.sentence.includes('_'));
  // Prioritize exercises with answers (interactive particle exercises)
  const answerable = validBlanks.filter(fb => fb.answer);
  const practiceOnly = validBlanks.filter(fb => !fb.answer);
  const selectedBlanks = [...shuffle(answerable), ...shuffle(practiceOnly).slice(0, Math.max(0, 5 - answerable.length))].slice(0, 5);
  for (const fb of selectedBlanks) {{
    exercises.push({{ type: 'fill_practice', data: fb }});
  }}

  // 6. Dialogue reading (if available)
  if (dialogue.length >= 2) {{
    exercises.push({{ type: 'dialogue_read', data: dialogue }});
  }}

  return exercises;
}}


// ===== EXERCISE RENDERING =====
function updateProgress() {{
  const pct = ((state.currentEx) / state.exercises.length) * 100;
  document.getElementById('progressFill').style.width = pct + '%';
  document.getElementById('heartsCount').textContent = state.hearts;
}}

function renderExercise() {{
  if (state.currentEx >= state.exercises.length || state.hearts <= 0) {{
    showComplete();
    return;
  }}

  updateProgress();
  state.checked = false;
  state.selectedAnswer = null;

  const ex = state.exercises[state.currentEx];
  const container = document.getElementById('exerciseScreen');
  const feedback = document.getElementById('feedbackBar');
  feedback.className = 'feedback-bar';
  feedback.innerHTML = '';

  switch (ex.type) {{
    case 'flashcard': renderFlashcard(container, ex.data); break;
    case 'flashcard_phrase': renderFlashcardPhrase(container, ex.data); break;
    case 'mc_bo_en': renderMC(container, ex, 'bo_en'); break;
    case 'mc_en_bo': renderMC(container, ex, 'en_bo'); break;
    case 'mc_bo_def': renderMC(container, ex, 'bo_def'); break;
    case 'match': renderMatch(container, ex); break;
    case 'fill_practice': renderFillPractice(container, ex.data); break;
    case 'dialogue_read': renderDialogueRead(container, ex.data); break;
  }}
}}

function renderFlashcard(container, data) {{
  const enSection = data.en ? `<div class="english-text" style="margin-bottom:12px">${{data.en}}</div>` : '';
  const defSection = data.defBo ? `<div class="definition-box"><div class="tibetan-medium">${{data.defBo}}</div></div>` : '';

  container.innerHTML = `
    <div class="exercise-prompt animate-in">New word</div>
    <div class="flashcard animate-in" onclick="revealFlashcard(this)">
      <div class="tibetan-large">${{data.bo}}</div>
      <div class="reveal-hint">Tap to reveal</div>
      <div class="revealed-content">
        ${{enSection}}
        ${{defSection}}
      </div>
    </div>
  `;
  setButton('continue');
}}

function renderFlashcardPhrase(container, data) {{
  container.innerHTML = `
    <div class="exercise-prompt animate-in">Common phrase</div>
    <div class="flashcard animate-in" onclick="revealFlashcard(this)">
      <div class="tibetan-large" style="font-size:22px">${{data.bo}}</div>
      <div class="reveal-hint">Tap to reveal meaning</div>
      <div class="revealed-content">
        ${{data.en ? `<div class="english-text">${{data.en}}</div>` : '<div class="english-small">Practice reading this phrase!</div>'}}
      </div>
    </div>
  `;
  setButton('continue');
}}

function revealFlashcard(el) {{
  el.classList.add('revealed');
}}

function renderMC(container, ex, direction) {{
  let promptText, promptClass, optionStyle;
  if (direction === 'bo_en') {{
    promptText = 'What does this mean?';
    promptClass = 'tibetan-large';
    optionStyle = 'font-family:sans-serif;font-size:18px;';
  }} else if (direction === 'en_bo') {{
    promptText = 'Choose the correct Tibetan';
    promptClass = 'english-text';
    optionStyle = '';
  }} else {{
    promptText = 'Which definition matches?';
    promptClass = 'tibetan-large';
    optionStyle = 'font-size:15px;';
  }}

  container.innerHTML = `
    <div class="exercise-prompt animate-in">${{promptText}}</div>
    <div class="${{promptClass}} animate-in" style="margin-bottom:24px;${{direction === 'en_bo' ? 'font-size:24px;font-weight:700;' : ''}}">${{ex.prompt}}</div>
    <div class="options">
      ${{ex.options.map((opt, i) => `
        <button class="option-btn" onclick="selectOption(this, ${{i}})" data-value="${{escapeAttr(opt)}}"
          style="${{optionStyle}}">${{opt}}</button>
      `).join('')}}
    </div>
  `;
  setButton('check', true);
}}

function selectOption(el, idx) {{
  if (state.checked) return;
  document.querySelectorAll('.option-btn').forEach(b => b.classList.remove('selected'));
  el.classList.add('selected');
  state.selectedAnswer = el.getAttribute('data-value');
  setButton('check', false);
}}

function renderMatch(container, ex) {{
  const pairs = ex.pairs;
  const leftItems = shuffle(pairs.map(p => ({{ text: p.bo, id: p.bo, side: 'bo' }})));
  const rightItems = shuffle(pairs.map(p => ({{ text: p.en, id: p.bo, side: 'en' }})));

  state.matchState = {{ pairs, matched: [], selectedBo: null, selectedEn: null }};

  container.innerHTML = `
    <div class="exercise-prompt animate-in">Match the pairs</div>
    <div class="match-container animate-in" id="matchGrid">
      ${{leftItems.map(item => `
        <button class="match-btn" data-side="bo" data-id="${{escapeAttr(item.id)}}" onclick="handleMatch(this)">${{item.text}}</button>
      `).join('')}}
      ${{rightItems.map(item => `
        <button class="match-btn" data-side="en" data-id="${{escapeAttr(item.id)}}" onclick="handleMatch(this)" style="font-family:sans-serif;font-size:16px;">${{item.text}}</button>
      `).join('')}}
    </div>
  `;
  setButton('check', true);
}}

function handleMatch(el) {{
  const ms = state.matchState;
  const side = el.dataset.side;
  const id = el.dataset.id;

  if (el.classList.contains('matched')) return;

  if (side === 'bo') {{
    document.querySelectorAll('.match-btn[data-side="bo"]').forEach(b => b.classList.remove('selected'));
    el.classList.add('selected');
    ms.selectedBo = {{ el, id }};
  }} else {{
    document.querySelectorAll('.match-btn[data-side="en"]').forEach(b => b.classList.remove('selected'));
    el.classList.add('selected');
    ms.selectedEn = {{ el, id }};
  }}

  if (ms.selectedBo && ms.selectedEn) {{
    if (ms.selectedBo.id === ms.selectedEn.id) {{
      ms.selectedBo.el.classList.remove('selected');
      ms.selectedEn.el.classList.remove('selected');
      ms.selectedBo.el.classList.add('matched');
      ms.selectedEn.el.classList.add('matched');
      ms.matched.push(ms.selectedBo.id);
      state.correct++;
      state.total++;
      state.xp += 10;
    }} else {{
      ms.selectedBo.el.classList.add('wrong');
      ms.selectedEn.el.classList.add('wrong');
      state.total++;
      setTimeout(() => {{
        ms.selectedBo.el.classList.remove('wrong', 'selected');
        ms.selectedEn.el.classList.remove('wrong', 'selected');
      }}, 500);
    }}
    ms.selectedBo = null;
    ms.selectedEn = null;

    if (ms.matched.length === ms.pairs.length) {{
      setButton('continue');
    }}
  }}
}}

function renderFillPractice(container, data) {{
  const hasAnswer = !!data.answer;
  const sentence = data.sentence.replace(/_+/g, '<span class="blank-slot" id="fillBlank">___</span>');
  const wordBank = data.word_bank || [];

  const chipHtml = wordBank.length > 0 ? `
    <div style="font-size:13px;color:var(--gray);font-family:sans-serif;margin-bottom:8px;">
      ${{hasAnswer ? 'Tap the correct particle:' : 'Tap a word to fill the blank:'}}
    </div>
    <div class="word-bank animate-in">
      ${{[...new Set(wordBank)].map(w => {{
        const clean = w.replace(/[།་ ]+$/g, '').trim();
        return `<span class="word-chip option-btn" data-value="${{clean}}" onclick="selectFillAnswer(this, '${{clean.replace(/'/g, "\\\\'")}}')">${{clean}}</span>`;
      }}).join('')}}
    </div>
  ` : '';

  container.innerHTML = `
    <div class="exercise-prompt animate-in">${{hasAnswer ? 'Fill in the blank' : 'Fill in the blank (practice)'}}</div>
    <div class="sentence-box animate-in" id="sentenceBox">${{sentence}}</div>
    ${{chipHtml}}
  `;

  state.selectedAnswer = null;
  state.checked = false;

  if (hasAnswer) {{
    // Scored mode: store correct answer for handleCheck
    const ex = state.exercises[state.currentEx];
    ex.correct = data.answer;
    setButton('check', true);
  }} else {{
    // Practice mode: continue button, but word bank is still tappable
    setButton('continue');
  }}
}}

function selectFillAnswer(el, value) {{
  if (state.checked) return;
  document.querySelectorAll('.word-bank .option-btn').forEach(b => b.classList.remove('selected'));
  el.classList.add('selected');
  state.selectedAnswer = value;

  // Fill the blank with the selected word
  const blank = document.getElementById('fillBlank');
  if (blank) {{
    blank.textContent = value;
    blank.style.color = 'var(--green)';
    blank.style.borderBottom = '2px solid var(--green)';
  }}

  setButton('check');
}}

function renderDialogueRead(container, dialogue) {{
  let html = '<div class="exercise-prompt animate-in">Read the dialogue</div><div class="animate-in">';
  const colors = ['speaker-a', 'speaker-b'];
  const labelColors = ['var(--blue)', 'var(--green-dark)'];

  for (let i = 0; i < Math.min(dialogue.length, 8); i++) {{
    const d = dialogue[i];
    const cls = colors[i % 2];
    const lc = labelColors[i % 2];
    html += `
      <div class="dialogue-bubble ${{cls}}">
        <div class="dialogue-speaker" style="color:${{lc}}">${{d.speaker}}</div>
        <div class="tibetan-medium" style="font-size:16px;margin:0;">${{d.text}}</div>
      </div>
    `;
  }}
  html += '</div>';
  container.innerHTML = html;
  setButton('continue');
}}


// ===== CHECK / CONTINUE =====
function setButton(mode, disabled) {{
  const btn = document.getElementById('checkBtn');
  const prevLink = document.getElementById('prevLink');

  // Show "Previous" link during flashcard exercises if not on first exercise
  const ex = state.exercises[state.currentEx];
  const isFlashcard = ex && (ex.type === 'flashcard' || ex.type === 'flashcard_phrase' || ex.type === 'dialogue_read' || ex.type === 'fill_practice');
  if (prevLink) {{
    if (isFlashcard && state.currentEx > 0) {{
      prevLink.style.display = 'block';
    }} else {{
      prevLink.style.display = 'none';
    }}
  }}

  if (mode === 'continue') {{
    btn.className = 'check-btn next';
    btn.textContent = 'Continue';
    btn.onclick = nextExercise;
  }} else if (mode === 'check') {{
    btn.className = disabled ? 'check-btn disabled' : 'check-btn primary';
    btn.textContent = 'Check';
    btn.onclick = handleCheck;
    if (prevLink) prevLink.style.display = 'none';
  }} else if (mode === 'next') {{
    btn.className = 'check-btn next';
    btn.textContent = 'Continue';
    btn.onclick = nextExercise;
    if (prevLink) prevLink.style.display = 'none';
  }}
}}

function prevExercise() {{
  if (state.currentEx > 0) {{
    state.currentEx--;
    renderExercise();
  }}
}}

function handleCheck() {{
  if (state.checked || !state.selectedAnswer) return;
  state.checked = true;

  const ex = state.exercises[state.currentEx];
  let correct = false;

  switch (ex.type) {{
    case 'mc_bo_en':
    case 'mc_en_bo':
    case 'mc_bo_def':
    case 'fill_practice':
      correct = state.selectedAnswer === ex.correct;
      break;
    default:
      correct = true;
  }}

  state.total++;
  const feedback = document.getElementById('feedbackBar');

  if (correct) {{
    state.correct++;
    state.xp += 10;
    feedback.className = 'feedback-bar correct';
    feedback.innerHTML = '<h4>Correct!</h4>';
    const selected = document.querySelector('.option-btn.selected');
    if (selected) selected.classList.add('correct');
  }} else {{
    state.hearts--;
    document.getElementById('heartsCount').textContent = state.hearts;
    feedback.className = 'feedback-bar incorrect';

    let correctAnswer = ex.correct || '';
    feedback.innerHTML = `<h4>Incorrect</h4><p>Correct: ${{correctAnswer}}</p>`;

    const selected = document.querySelector('.option-btn.selected');
    if (selected) selected.classList.add('incorrect');

    document.querySelectorAll('.option-btn').forEach(b => {{
      if (b.getAttribute('data-value') === correctAnswer) b.classList.add('correct');
    }});
  }}

  document.querySelectorAll('.option-btn').forEach(b => b.classList.add('disabled'));
  setButton('next');
}}

function nextExercise() {{
  state.currentEx++;
  renderExercise();
}}

function showComplete() {{
  document.getElementById('exHeader').style.display = 'none';
  document.getElementById('bottomBar').style.display = 'none';
  document.getElementById('completeBar').style.display = 'block';
  showScreen('complete');

  updateStreak();
  const streak = getStreak();
  const accuracy = state.total > 0 ? Math.round((state.correct / state.total) * 100) : 0;

  // Save best score
  if (currentLesson) {{
    const key = getLessonKey(currentLesson) + '_best';
    const currentBest = loadProgress()[key] || 0;
    if (accuracy > currentBest) saveProgress(key, accuracy);
  }}

  // Save XP
  const data = loadProgress();
  data.totalXp = (data.totalXp || 0) + state.xp;
  localStorage.setItem('tibetan_progress', JSON.stringify(data));

  document.getElementById('xpEarned').textContent = state.xp;
  document.getElementById('statCorrect').textContent = state.correct;
  document.getElementById('statAccuracy').textContent = accuracy + '%';
  document.getElementById('statStreak').textContent = streak;
  document.getElementById('completeSubtitle').textContent =
    state.hearts <= 0 ? 'Keep practicing!' : 'Great work!';

  // Show proverb if available
  const proverbBox = document.getElementById('proverbBox');
  if (currentLesson && currentLesson.proverb) {{
    document.getElementById('proverbText').textContent = currentLesson.proverb;
    proverbBox.style.display = 'block';
  }} else {{
    proverbBox.style.display = 'none';
  }}

  if (state.hearts > 0) spawnConfetti();
}}

function spawnConfetti() {{
  const colors = ['#58CC02', '#1CB0F6', '#FFC800', '#FF4B4B', '#CE82FF'];
  for (let i = 0; i < 30; i++) {{
    const el = document.createElement('div');
    el.className = 'confetti-piece';
    el.style.left = Math.random() * 100 + 'vw';
    el.style.top = (60 + Math.random() * 30) + 'vh';
    el.style.background = colors[Math.floor(Math.random() * colors.length)];
    el.style.animationDelay = Math.random() * 0.5 + 's';
    el.style.animationDuration = (1 + Math.random()) + 's';
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 2500);
  }}
}}

function escapeAttr(s) {{
  return String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;');
}}

// Init
showHome();
</script>
</body>
</html>'''

Path('index.html').write_text(html, encoding='utf-8')
size = Path('index.html').stat().st_size
print(f'Written index.html ({size:,} bytes / {size // 1024} KB)')
