/**
 * SkillSync Smart Logbook & Voice AI Portal Application Logic
 * Dynamic Voice AI Parser, Blank Form Defaults, Separate Form Persistence & WhatsApp Owner Integration
 */

let appState = {
  currentUser: null,
  activeCombo: 'AWS+DEVOPS',
  comboConfigs: {},
  logs: [],
  suggestions: [],
  voiceTargetSection: 'auto',
  lastParsedAiData: null,
  activeEditingLogId: null,
  isListening: false,
  recognition: null
};

// Initialize Application
document.addEventListener('DOMContentLoaded', async () => {
  await fetchConfigs();
  initSpeechRecognition();
  initDateDefaults();

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/sw.js')
      .then(reg => console.log('✅ PWA Service Worker active:', reg.scope))
      .catch(err => console.log('Service Worker registration:', err));
  }

  window.addEventListener('online', syncOfflineData);
  window.addEventListener('popstate', handleInitialUrlRouting);
  syncOfflineData();

  handleInitialUrlRouting();
});

// URL Routing & Page Navigation
function handleInitialUrlRouting() {
  const path = window.location.pathname.toLowerCase().replace(/\/$/, '');
  const hash = window.location.hash.toLowerCase();

  if (path.startsWith('/tracks/')) {
    if (!restoreSavedUser()) return;
    const comboKey = path.replace('/tracks/', '').trim();
    if (comboKey) {
      appState.activeCombo = comboKey;
      handleComboChange(comboKey, false);
    }
    enterMainApp();
    switchAppTab('dashboard', null, false);
    return;
  }

  if (path === '/register' || hash === '#register') {
    showScreen('auth-register', false);
    return;
  }

  if (path === '/login' || hash === '#login') {
    showScreen('auth-login', false);
    return;
  }

  if (path === '/dashboard' || hash === '#dashboard') {
    if (!restoreSavedUser()) return;
    enterMainApp();
    switchAppTab('dashboard', null, false);
    return;
  }

  if (path === '/editor' || hash === '#editor') {
    if (!restoreSavedUser()) return;
    enterMainApp();
    switchAppTab('editor', null, false);
    return;
  }

  if (path === '/voice-ai' || hash === '#voice-ai') {
    if (!restoreSavedUser()) return;
    enterMainApp();
    switchAppTab('voice-ai', null, false);
    return;
  }

  if (path === '/history' || hash === '#history') {
    if (!restoreSavedUser()) return;
    enterMainApp();
    switchAppTab('history', null, false);
    return;
  }

  if (path === '/print-sheet' || hash === '#print-sheet') {
    if (!restoreSavedUser()) return;
    enterMainApp();
    switchAppTab('print-sheet', null, false);
    return;
  }

  if (path === '/suggestions' || hash === '#suggestions') {
    if (!restoreSavedUser()) return;
    enterMainApp();
    switchAppTab('suggestions', null, false);
    return;
  }

  checkSavedUserSession();
}

function checkSavedUserSession() {
  if (restoreSavedUser()) enterMainApp();
  else showScreen('landing', false);
}

function restoreSavedUser() {
  const savedUser = localStorage.getItem('techwing_active_user');
  if (!savedUser) {
    showScreen('auth-login', false);
    return false;
  }
  try {
    appState.currentUser = JSON.parse(savedUser);
    appState.activeCombo = appState.currentUser.combo || 'AWS+DEVOPS';
    return Boolean(appState.currentUser.email);
  } catch (error) {
    localStorage.removeItem('techwing_active_user');
    showScreen('auth-login', false);
    return false;
  }
}

// Navigation between SPA Screens with URL PushState
function showScreen(screenId, updateUrl = true) {
  document.querySelectorAll('.screen-view').forEach(s => s.classList.remove('active'));
  const target = document.getElementById('screen-' + screenId);
  if (target) target.classList.add('active');

  if (updateUrl) {
    let routePath = '/';
    if (screenId === 'auth-register') routePath = '/register';
    else if (screenId === 'auth-login') routePath = '/login';
    else if (screenId === 'app-main') routePath = '/dashboard';

    if (window.location.pathname !== routePath) {
      window.history.pushState({ screenId }, '', routePath);
    }
  }
}

// Authentication Handlers
async function handleRegisterSubmit(e) {
  e.preventDefault();
  const name = document.getElementById('regName').value.trim();
  const email = document.getElementById('regEmail').value.trim().toLowerCase();
  const combo = document.getElementById('regCombo').value;
  const password = document.getElementById('regPassword').value;
  const pin = document.getElementById('regPin').value.trim();

  if (!/^[A-Za-z0-9]{10}$/.test(pin)) {
    alert('College PIN must contain exactly 10 alphanumeric characters.');
    return;
  }

  try {
    const res = await fetch('/api/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, combo, password, pin })
    });
    const data = await res.json();

    if (!res.ok) {
      alert(data.error || 'Registration failed');
      return;
    }

    appState.currentUser = data.user;
    appState.activeCombo = combo;
    localStorage.setItem('techwing_active_user', JSON.stringify(data.user));
    enterMainApp();
  } catch (err) {
    alert('Server connection error. Registration was not completed. Please try again.');
  }
}

async function handleLoginSubmit(e) {
  e.preventDefault();
  const email = document.getElementById('loginEmail').value.trim().toLowerCase();
  const password = document.getElementById('loginPassword').value.trim();

  try {
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();

    if (!res.ok) {
      alert(data.error || 'Login failed. Please check your credentials.');
      return;
    }

    appState.currentUser = data.user;
    appState.activeCombo = data.user.combo || 'genai-aws';
    localStorage.setItem('techwing_active_user', JSON.stringify(data.user));
    enterMainApp();
  } catch (err) {
    alert('Server connection error. Please verify backend server is running.');
  }
}

function handleLogout() {
  if (!window.confirm('Are you sure you want to log out?')) return;
  localStorage.removeItem('techwing_active_user');
  appState.currentUser = null;
  const profileMenu = document.getElementById('profileMenu');
  if (profileMenu) profileMenu.hidden = true;
  showScreen('landing');
}

function toggleProfileMenu(event) {
  event.stopPropagation();
  const profileMenu = document.getElementById('profileMenu');
  const avatar = document.getElementById('userAvatar');
  if (!profileMenu) return;
  profileMenu.hidden = !profileMenu.hidden;
  if (avatar) avatar.setAttribute('aria-expanded', String(!profileMenu.hidden));
}

document.addEventListener('click', (event) => {
  const profileMenu = document.getElementById('profileMenu');
  const profileWrap = document.querySelector('.profile-menu-wrap');
  const avatar = document.getElementById('userAvatar');
  if (profileMenu && profileWrap && !profileWrap.contains(event.target)) {
    profileMenu.hidden = true;
    if (avatar) avatar.setAttribute('aria-expanded', 'false');
  }
});

function enterMainAppDirectly() {
  if (!appState.currentUser) {
    appState.currentUser = {
      name: 'Kishore Kumar',
      email: 'kishore@techwing.com',
      combo: appState.activeCombo || 'genai-aws'
    };
  }
  enterMainApp();
}

function handleComboChange(comboKey, updateUrl = true) {
  if (!comboKey) return;
  appState.activeCombo = comboKey;
  if (appState.currentUser) {
    appState.currentUser.combo = comboKey;
  }

  const topSelect = document.getElementById('comboSelect');
  if (topSelect && topSelect.value !== comboKey) {
    topSelect.value = comboKey;
  }

  const regSelect = document.getElementById('regCombo');
  if (regSelect && regSelect.value !== comboKey) {
    regSelect.value = comboKey;
  }

  const config = appState.comboConfigs[comboKey] || { name: comboKey };

  const userComboBadge = document.getElementById('userComboBadge');
  if (userComboBadge) userComboBadge.innerText = config.name || comboKey;

  const dashStatCombo = document.getElementById('dashStatCombo');
  if (dashStatCombo) dashStatCombo.innerText = config.name || comboKey;

  const dashComboName = document.getElementById('dashComboName');
  if (dashComboName) dashComboName.innerText = config.name || comboKey;

  applyComboDefaultsToForm(comboKey);
  fetchUserLogs();

  if (updateUrl) {
    const routePath = `/tracks/${comboKey}`;
    if (window.location.pathname !== routePath) {
      window.history.pushState({ comboKey }, '', routePath);
    }
  }
}

function applyComboDefaultsToForm(comboKey) {
  const config = appState.comboConfigs[comboKey];
  if (!config) return;

  const labEl = document.getElementById('inputLab');
  if (labEl && !labEl.value.trim()) labEl.placeholder = config.defaultLab || '';

  const trainerEl = document.getElementById('inputTrainer');
  if (trainerEl && !trainerEl.value.trim()) trainerEl.placeholder = config.defaultTrainer || '';

  const topicsEl = document.getElementById('inputTopics');
  if (topicsEl && !topicsEl.value.trim()) topicsEl.placeholder = config.topics || '';

  const assignEl = document.getElementById('inputAssignment');
  if (assignEl && !assignEl.value.trim()) assignEl.placeholder = config.assignment || '';

  const doubtsEl = document.getElementById('inputDoubts');
  if (doubtsEl && !doubtsEl.value.trim()) doubtsEl.placeholder = config.doubts || '';

  const importantNotesEl = document.getElementById('inputImportantNotes');
  if (importantNotesEl && !importantNotesEl.value.trim()) importantNotesEl.placeholder = config.importantNotes || '';
}

// Enter Main Application Dashboard
function enterMainApp() {
  showScreen('app-main');
  const user = appState.currentUser || { name: 'Student', email: 'kishore@techwing.com', combo: 'genai-aws' };

  document.getElementById('topbarComboTitle').innerText = user.name;
  
  document.getElementById('userAvatar').innerText = user.name.charAt(0).toUpperCase();
  document.getElementById('profileName').innerText = user.name;
  document.getElementById('profileEmail').innerText = user.email;
  document.getElementById('profileCombo').innerText = (appState.comboConfigs[appState.activeCombo]?.name) || appState.activeCombo;
  document.getElementById('profilePin').innerText = user.pin_masked || (user.pin ? '**********' : 'Not set');

  if (document.getElementById('sugName')) document.getElementById('sugName').value = user.name;
  if (document.getElementById('sugEmail')) document.getElementById('sugEmail').value = user.email;

  fetchUserLogs();
  clearFormFields();
}

// Fetch logs from Python Backend API
async function fetchUserLogs() {
  if (!appState.currentUser) return;
  try {
    const res = await fetch(`/api/logs?email=${encodeURIComponent(appState.currentUser.email)}`);
    if (res.ok) {
      appState.logs = await res.json();
      renderDashboard();
      renderHistoryTable();
      populatePrintLogSelect();
    }
  } catch (e) {
    console.warn("Using offline storage logs");
  }
}

// Tab Switcher inside App
function switchAppTab(tabId, btnEl, updateUrl = true) {
  document.querySelectorAll('.app-nav-link, .mobile-nav-item').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

  if (!btnEl) {
    btnEl = document.querySelector(`.app-nav-link[onclick*="${tabId}"], .mobile-nav-item[onclick*="${tabId}"]`);
  }
  if (btnEl) btnEl.classList.add('active');

  const pane = document.getElementById('tab-' + tabId);
  if (pane) pane.classList.add('active');

  if (updateUrl) {
    const routePath = '/' + tabId;

    if (window.location.pathname !== routePath) {
      window.history.pushState({ tabId }, '', routePath);
    }
  }

  if (tabId === 'dashboard') renderDashboard();
  if (tabId === 'history') renderHistoryTable();
  if (tabId === 'print-sheet') {
    populatePrintLogSelect();
    const select = document.getElementById('printLogSelect');
    if (select && select.value) {
      loadLogToPrintSheet(select.value);
    } else {
      renderBlankPrintSheet();
    }
  }
}

// Form Defaults & Real-Time Sync
function getLocalDateString(date = new Date()) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function initDateDefaults() {
  const today = new Date();
  const dateStr = getLocalDateString(today);
  const dayStr = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][today.getDay()];

  const inputDate = document.getElementById('inputDate');
  const inputDay = document.getElementById('inputDay');
  const dashDate = document.getElementById('dashDateStr');

  if (inputDate) inputDate.value = dateStr;
  if (inputDay) inputDay.value = dayStr;
  if (dashDate) dashDate.innerText = dateStr;
}

function updateLivePaper() {
  const dateVal = document.getElementById('inputDate').value || '';
  const dayVal = document.getElementById('inputDay').value || '';
  const labVal = document.getElementById('inputLab').value || '';
  const checkInVal = formatTime(document.getElementById('inputCheckIn').value) || '';
  const checkOutVal = formatTime(document.getElementById('inputCheckOut').value) || '';
  const trainerVal = document.getElementById('inputTrainer').value || '';
  const topicsVal = document.getElementById('inputTopics').value || '';
  const assignmentVal = document.getElementById('inputAssignment').value || '';
  const doubtsVal = document.getElementById('inputDoubts').value || '';
  const importantNotesVal = document.getElementById('inputImportantNotes').value || '';

  document.getElementById('paperDateVal').innerText = dateVal;
  document.getElementById('paperDayVal').innerText = dayVal;
  document.getElementById('paperLabVal').innerText = labVal;
  document.getElementById('paperCheckInVal').innerText = checkInVal;
  document.getElementById('paperCheckOutVal').innerText = checkOutVal;
  document.getElementById('paperTrainerVal').innerText = trainerVal;

  document.getElementById('paperTopicsVal').innerText = topicsVal;
  document.getElementById('paperAssignmentVal').innerText = assignmentVal;
  document.getElementById('paperDoubtsVal').innerText = doubtsVal;
  document.getElementById('paperImportantNotesVal').innerText = importantNotesVal;

  syncFullPrintSheet();
}

function formatTime(t) {
  if (!t) return '';
  const normalized = normalizeTime(t);
  if (!normalized) return t;
  const [h, m] = normalized.split(':');
  let hour = parseInt(h, 10);
  const ampm = hour >= 12 ? 'PM' : 'AM';
  hour = hour % 12 || 12;
  return `${hour.toString().padStart(2, '0')}:${m} ${ampm}`;
}

function normalizeTime(value) {
  const match = String(value || '').trim().match(/^(\d{1,2}):(\d{2})\s*(AM|PM)?$/i);
  if (!match) return '';
  let hour = Number(match[1]);
  const minute = Number(match[2]);
  const meridiem = match[3]?.toUpperCase();
  if (minute > 59) return '';
  if (meridiem) {
    if (hour < 1 || hour > 12) return '';
    if (meridiem === 'PM' && hour !== 12) hour += 12;
    if (meridiem === 'AM' && hour === 12) hour = 0;
  } else if (hour > 23) {
    return '';
  }
  return `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;
}

function syncFullPrintSheet() {
  const src = document.getElementById('liveSheetContainer');
  const target = document.getElementById('fullSheetTarget');
  if (src && target && (!target.getAttribute('data-custom-log') || target.getAttribute('data-custom-log') === 'active')) {
    target.innerHTML = src.innerHTML;
  }
}

// Clear Form Fields (100% Blank by Default)
function clearFormFields() {
  document.getElementById('inputLab').value = '';
  document.getElementById('inputTrainer').value = '';
  document.getElementById('inputTopics').value = '';
  document.getElementById('inputAssignment').value = '';
  document.getElementById('inputDoubts').value = '';
  document.getElementById('inputImportantNotes').value = '';
  document.getElementById('inputCheckIn').value = '';
  document.getElementById('inputCheckOut').value = '';
  appState.activeEditingLogId = null;
  updateLivePaper();
}

// Load Combo Sample Data (Only when user explicitly clicks button)
function loadSampleData() {
  const config = appState.comboConfigs[appState.activeCombo] || {
    defaultLab: 'Lab 04 - GenAI Hub',
    defaultTrainer: 'Dr. Rajesh Sharma',
    topics: '• Topic 1: GenAI & LLMs\n• Topic 2: Vector Search & Bedrock',
    assignment: '• Build a RAG Q&A bot using LangChain.',
    doubts: '• Discussed dense vs sparse vector search.',
    importantNotes: '• Review the vector search design and ask for queries before deployment.'
  };

  document.getElementById('inputLab').value = config.defaultLab || 'Lab 04';
  document.getElementById('inputTrainer').value = config.defaultTrainer || 'Dr. Rajesh Sharma';
  document.getElementById('inputTopics').value = config.topics || '';
  document.getElementById('inputAssignment').value = config.assignment || '';
  document.getElementById('inputDoubts').value = config.doubts || '';
  document.getElementById('inputImportantNotes').value = config.importantNotes || '';
  document.getElementById('inputCheckIn').value = '09:30 AM';
  document.getElementById('inputCheckOut').value = '04:30 PM';

  updateLivePaper();
  alert("Sample data loaded into form!");
}

// Save Daily Log (Always saves as a SEPARATE new form entry unless editing existing)
async function saveCurrentLog() {
  const dateVal = document.getElementById('inputDate').value;
  const dayVal = document.getElementById('inputDay').value;
  const labVal = document.getElementById('inputLab').value;
  const checkInVal = normalizeTime(document.getElementById('inputCheckIn').value);
  const checkOutVal = normalizeTime(document.getElementById('inputCheckOut').value);
  const trainerVal = document.getElementById('inputTrainer').value;
  const topicsVal = document.getElementById('inputTopics').value.trim();
  const assignmentVal = document.getElementById('inputAssignment').value.trim();
  const doubtsVal = document.getElementById('inputDoubts').value.trim();
  const importantNotesVal = document.getElementById('inputImportantNotes').value.trim();

  const missingFields = [
    ['Date', dateVal], ['Day', dayVal], ['Lab / Room Location', labVal],
    ['Check-In (use hh:mm AM/PM)', checkInVal], ['Check-Out (use hh:mm AM/PM)', checkOutVal], ['Trainer Name', trainerVal],
    ['Topics Covered Today', topicsVal], ['Task / Assignment', assignmentVal]
  ].filter(([, value]) => !value).map(([label]) => label);

  if (missingFields.length) {
    alert(`Please complete the required fields: ${missingFields.join(', ')}.`);
    return;
  }

  const isEditingExisting = !!appState.activeEditingLogId;

  const payload = {
    id: appState.activeEditingLogId,
    is_update: isEditingExisting,
    user_email: appState.currentUser ? appState.currentUser.email : 'kishore@techwing.com',
    combo: appState.activeCombo,
    date: dateVal,
    day: dayVal,
    lab: labVal,
    checkIn: checkInVal,
    checkOut: checkOutVal,
    trainer: trainerVal,
    topics: topicsVal,
    practical: '',
    assignment: assignmentVal,
    doubts: doubtsVal,
    important_notes: importantNotesVal
  };

  try {
    const res = await fetch('/api/logs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (res.ok) {
      alert(`Report saved as a SEPARATE logbook entry for ${dateVal}!`);
      appState.activeEditingLogId = null; // Reset edit mode so next save creates another separate form
      fetchUserLogs();
    } else {
      alert(data.error || 'Failed to save log. Please try again.');
    }
  } catch (e) {
    const offlineLogs = JSON.parse(localStorage.getItem('techwing_offline_logs') || '[]');
    offlineLogs.push(payload);
    localStorage.setItem('techwing_offline_logs', JSON.stringify(offlineLogs));
    
    if (!payload.id) payload.id = `offline_${Date.now()}`;
    appState.logs.unshift(payload);
    renderDashboard();
    renderHistoryTable();

    alert(`📱 Offline Mode: Report saved locally on your phone for ${dateVal}! Will auto-sync when online.`);
    appState.activeEditingLogId = null;
  }
}

/* =========================================================
   VOICE AI TARGET CHIPS & DYNAMIC DEMO PREVIEW LOGIC
   ========================================================= */
function setVoiceTarget(targetKey, btnEl) {
  appState.voiceTargetSection = targetKey;
  document.querySelectorAll('.chip-btn').forEach(b => b.classList.remove('active'));
  if (btnEl) btnEl.classList.add('active');
}

function renderVoiceDemoPreview(data) {
  appState.lastParsedAiData = data;

  const demoBox = document.getElementById('voiceDemoBox');
  const targetBadge = document.getElementById('demoTargetBadge');

  if (targetBadge) {
    targetBadge.innerText = data.target_name || "DYNAMIC VOICE EXTRACTED CONTENT";
  }

  document.getElementById('demoTopicsText').innerText = data.topics || "(Empty)";
  document.getElementById('demoAssignmentText').innerText = data.assignment || "(Empty)";
  document.getElementById('demoDoubtsText').innerText = data.doubts || "(Empty)";
  document.getElementById('demoImportantNotesText').innerText = data.important_notes || data.importantNotes || "(Empty)";

  if (demoBox) {
    demoBox.style.display = 'block';
    demoBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
}

function applyVoiceDemoToForm() {
  if (!appState.lastParsedAiData) return;

  const data = appState.lastParsedAiData;

  // Append or set dynamic fields from voice AI
  if (data.topics) document.getElementById('inputTopics').value = data.topics;
  if (data.assignment) document.getElementById('inputAssignment').value = data.assignment;
  if (data.doubts) document.getElementById('inputDoubts').value = data.doubts;
  if (data.important_notes || data.importantNotes) document.getElementById('inputImportantNotes').value = data.important_notes || data.importantNotes;

  // Ensure active log ID is cleared so saving creates a brand new separate form
  appState.activeEditingLogId = null;

  updateLivePaper();
  alert(`Voice content applied to your form! Click "Save Report" to store as a new separate entry.`);
  closeVoiceDemoBox();
}

function closeVoiceDemoBox() {
  const demoBox = document.getElementById('voiceDemoBox');
  if (demoBox) demoBox.style.display = 'none';
}

// Voice Speech Recognition Engine (Web Speech API)
function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    const status = document.getElementById('voiceStatus');
    if (status) status.innerText = 'Voice input is unavailable in this browser. Use the text box below.';
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.lang = navigator.language || 'en-US';

  recognition.onstart = () => {
    appState.isListening = true;
    document.getElementById('micBtn').classList.add('listening');
    document.getElementById('voiceStatus').innerText = '🎙️ Listening to your voice... Speak now!';
  };

  recognition.onresult = async (event) => {
    const transcript = event.results[0][0].transcript;
    document.getElementById('voiceStatus').innerText = `Recorded: "${transcript}"`;
    appendChatMessage('user', `🎙️ Spoken: "${transcript}"`);

    // Send to Python AI Voice Parser with target section
    try {
      const res = await fetch('/api/ai/parse-voice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: transcript,
          combo: appState.activeCombo,
          target_section: appState.voiceTargetSection
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Voice parsing failed on the server.');

      appendChatMessage('ai', data.reply);
      renderVoiceDemoPreview(data);

      if (data.topics) document.getElementById('inputTopics').value = data.topics;
      if (data.assignment) document.getElementById('inputAssignment').value = data.assignment;
      if (data.doubts) document.getElementById('inputDoubts').value = data.doubts;
      if (data.important_notes || data.importantNotes) document.getElementById('inputImportantNotes').value = data.important_notes || data.importantNotes;

      updateLivePaper();
    } catch (e) {
      const message = `Voice parsing failed: ${e.message}. You can type the same note in the chat box.`;
      document.getElementById('voiceStatus').innerText = message;
      appendChatMessage('ai', message);
      console.error(e);
    }
  };

  recognition.onerror = (e) => {
    console.error('Speech recognition error:', e.error);
    const messages = {
      'not-allowed': 'Microphone permission was blocked. Allow microphone access for this site, then try again.',
      'service-not-allowed': 'Speech recognition is blocked by the browser. Use the text box below.',
      'no-speech': 'No speech detected. Please speak after the microphone starts.',
      'network': 'Speech service connection failed. Check the internet and try again.'
    };
    const status = document.getElementById('voiceStatus');
    if (status) status.innerText = messages[e.error] || 'Voice input failed. Please try again or type below.';
    stopVoiceRecording(false);
  };

  recognition.onend = () => {
    stopVoiceRecording();
  };

  appState.recognition = recognition;
}

function toggleVoiceRecording() {
  const status = document.getElementById('voiceStatus');

  if (!appState.recognition) {
    if (status) status.innerText = 'Voice input is unavailable in this browser. Please type your notes in the chat box below.';
    return;
  }

  if (appState.isListening) {
    appState.recognition.stop();
    stopVoiceRecording();
    return;
  }

  try {
    appState.recognition.start();
  } catch (error) {
    if (status) status.innerText = 'Could not start the microphone. Allow access for this site and try again.';
    console.error('Could not start speech recognition:', error);
  }
}

function stopVoiceRecording(resetStatus = true) {
  appState.isListening = false;
  const btn = document.getElementById('micBtn');
  if (btn) btn.classList.remove('listening');
  const status = document.getElementById('voiceStatus');
  if (status && resetStatus) status.innerText = 'Click Microphone to Start Speaking';
}

// Conversational AI Chat
function submitChatInput() {
  const input = document.getElementById('chatInput');
  const val = input.value.trim();
  if (!val) return;

  appendChatMessage('user', val);
  input.value = '';

  fetch('/api/ai/parse-voice', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text: val,
      combo: appState.activeCombo,
      target_section: appState.voiceTargetSection
    })
  }).then(async res => {
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Voice parsing failed on the server.');
    return data;
  }).then(data => {
    appendChatMessage('ai', data.reply);
    renderVoiceDemoPreview(data);

    if (data.topics) document.getElementById('inputTopics').value = data.topics;
    if (data.assignment) document.getElementById('inputAssignment').value = data.assignment;
    if (data.doubts) document.getElementById('inputDoubts').value = data.doubts;
    if (data.important_notes || data.importantNotes) document.getElementById('inputImportantNotes').value = data.important_notes || data.importantNotes;
    updateLivePaper();
  }).catch(error => {
    const message = `Voice parsing failed: ${error.message}.`;
    appendChatMessage('ai', message);
    console.error(error);
  });
}

function handleChatKeyPress(e) {
  if (e.key === 'Enter') submitChatInput();
}

function appendChatMessage(sender, text) {
  const thread = document.getElementById('chatThread');
  const msgRow = document.createElement('div');
  msgRow.className = `chat-msg-row ${sender}`;
  msgRow.innerHTML = `<div class="msg-text">${escapeHtml(text)}</div>`;
  thread.appendChild(msgRow);
  thread.scrollTop = thread.scrollHeight;
}

function escapeHtml(s) {
  return s ? s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;") : '';
}

/* =========================================================
   DASHBOARD METRICS & RECENT LOGS
   ========================================================= */
function renderDashboard() {
  const todayStr = getLocalDateString(new Date());
  const submittedToday = appState.logs.some(l => l.date === todayStr);

  const badge = document.getElementById('todayStatusBadge');
  if (badge) {
    if (submittedToday) {
      badge.className = 'status-badge completed';
      badge.innerHTML = '<i class="fa-solid fa-circle-check"></i> Report Submitted Today';
    } else {
      badge.className = 'status-badge pending';
      badge.innerHTML = '<i class="fa-solid fa-clock"></i> Report Pending for Today';
    }
  }

  // Forms filled count
  const countEl = document.getElementById('dashStatLogs');
  if (countEl) countEl.innerText = appState.logs.length;

  // Active combo name
  const comboEl = document.getElementById('dashStatCombo');
  if (comboEl) {
    const comboName = appState.comboConfigs[appState.activeCombo]?.name || appState.activeCombo;
    comboEl.innerText = comboName;
  }

  // Calculate Streak
  const streakEl = document.getElementById('dashStatStreak');
  if (streakEl) {
    const streak = Math.max(1, appState.logs.length);
    streakEl.innerText = `${streak} ${streak === 1 ? 'Day' : 'Days'}`;
  }

  // Render recent logs
  const listEl = document.getElementById('recentReportsList');
  if (listEl) {
    if (appState.logs.length === 0) {
      listEl.innerHTML = `<p style="color: var(--text-muted); text-align: center; padding: 1rem;">No daily reports saved yet.</p>`;
    } else {
      listEl.innerHTML = appState.logs.slice(0, 5).map((l, idx) => `
        <div style="background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 0.75rem 1rem; display: flex; align-items: center; justify-content: space-between;">
          <div>
            <div style="font-weight: 600; font-size: 0.9rem;">📅 ${l.date} — ${l.day} <span style="font-size: 0.75rem; color: var(--accent-secondary); font-weight: normal;">(Form #${appState.logs.length - idx})</span></div>
            <div style="font-size: 0.8rem; color: var(--text-secondary);">${l.lab || 'Lab'} | Trainer: ${l.trainer || 'N/A'}</div>
          </div>
          <button class="btn btn-outline" style="padding: 0.25rem 0.6rem; font-size: 0.75rem;" onclick="loadLogToForm('${l.id}')">
            View / Edit
          </button>
        </div>
      `).join('');
    }
  }
}

/* =========================================================
   PRINTABLE SHEETS DATE/LOG SELECTOR LOGIC (BLANK BY DEFAULT)
   ========================================================= */
function populatePrintLogSelect() {
  const select = document.getElementById('printLogSelect');
  if (!select) return;

  if (appState.logs.length === 0) {
    select.innerHTML = `<option value="">-- Select Saved Report Date --</option>`;
    renderBlankPrintSheet();
    return;
  }

  let html = `<option value="">-- Select Saved Report Date --</option>`;
  const dateCounts = {};
  appState.logs.forEach((l, idx) => {
    dateCounts[l.date] = (dateCounts[l.date] || 0) + 1;
    const entryNum = dateCounts[l.date];
    const comboName = appState.comboConfigs[l.combo]?.name || l.combo;
    html += `<option value="${l.id}">📅 ${l.date} (${l.day}) - Entry ${entryNum} [${l.lab || 'Lab'}]</option>`;
  });

  select.innerHTML = html;
}

function renderBlankPrintSheet() {
  const target = document.getElementById('fullSheetTarget');
  if (!target) return;

  target.setAttribute('data-custom-log', 'blank');
  target.innerHTML = `
    <div class="sheet-container">
      <div class="sheet-outer-box">
        <div class="sheet-header-block">
          <div class="sheet-title-text">
            <span class="sheet-title-bar"></span>
            SKILLSYNC — DAILY TRAINING LOGBOOK
          </div>
          <div class="sheet-subtitle-text">Official Classroom Training Record Sheet</div>
        </div>

        <table class="sheet-table-grid">
          <tr>
            <td class="lbl-cell">DATE</td>
            <td class="val-cell" style="color: #999;">____________________</td>
            <td class="lbl-cell">DAY</td>
            <td class="val-cell" style="color: #999;">____________________</td>
          </tr>
          <tr>
            <td class="lbl-cell">LAB</td>
            <td class="val-cell" colspan="3" style="color: #999;">________________________________________</td>
          </tr>
          <tr>
            <td class="lbl-cell">CHECK-IN</td>
            <td class="val-cell" style="color: #999;">___:___ AM/PM</td>
            <td class="lbl-cell">CHECK-OUT</td>
            <td class="val-cell" style="color: #999;">___:___ AM/PM</td>
          </tr>
          <tr>
            <td class="lbl-cell">TRAINER</td>
            <td class="val-cell" style="width: 35%; color: #999;">____________________</td>
            <td class="val-cell" colspan="2" style="text-align: center; color: #555555; font-size: 11px;">
              [ Trainer Approval & Signature ]
            </td>
          </tr>
        </table>

        <div class="sec-banner"><span class="sq-symbol">■</span> TOPICS COVERED TODAY</div>
        <div class="sec-box-content" style="color: #888;">Select a saved report date above to populate topics covered.</div>

        <div class="sec-banner"><span class="sq-symbol">■</span> TASK / ASSIGNMENT</div>
        <div class="sec-box-content" style="color: #888;">Select a saved report date above to populate assignment.</div>

        <div class="sec-banner"><span class="sq-symbol">■</span> DOUBTS</div>
        <div class="sec-box-content" style="color: #888;">Select a saved report date above to populate doubts.</div>

        <div class="sec-banner"><span class="sq-symbol">■</span> IMPORTANT NOTES</div>
        <div class="sec-box-content" style="color: #888;">Select a saved report date above to populate important notes.</div>
      </div>
    </div>
  `;
}

function loadLogToPrintSheet(logId) {
  const target = document.getElementById('fullSheetTarget');
  if (!target) return;

  if (!logId) {
    renderBlankPrintSheet();
    return;
  }

  const log = appState.logs.find(l => l.id === logId);
  if (!log) {
    renderBlankPrintSheet();
    return;
  }

  target.setAttribute('data-custom-log', 'custom');

  const comboName = appState.comboConfigs[log.combo]?.subtitle || `${log.combo} | Daily Class Record`;

  target.innerHTML = `
    <div class="sheet-container">
      <div class="sheet-outer-box">
        <div class="sheet-header-block">
          <div class="sheet-title-text">
            <span class="sheet-title-bar"></span>
            SKILLSYNC — DAILY TRAINING LOGBOOK
          </div>
          <div class="sheet-subtitle-text">${comboName}</div>
        </div>

        <table class="sheet-table-grid">
          <tr>
            <td class="lbl-cell">DATE</td>
            <td class="val-cell">${log.date}</td>
            <td class="lbl-cell">DAY</td>
            <td class="val-cell">${log.day}</td>
          </tr>
          <tr>
            <td class="lbl-cell">LAB</td>
            <td class="val-cell" colspan="3">${log.lab || ''}</td>
          </tr>
          <tr>
            <td class="lbl-cell">CHECK-IN</td>
            <td class="val-cell">${formatTime(log.checkIn) || ''}</td>
            <td class="lbl-cell">CHECK-OUT</td>
            <td class="val-cell">${formatTime(log.checkOut) || ''}</td>
          </tr>
          <tr>
            <td class="lbl-cell">TRAINER</td>
            <td class="val-cell" style="width: 35%;">${log.trainer || ''}</td>
            <td class="val-cell" colspan="2" style="text-align: center; color: #555555; font-size: 11px;">
              [ Trainer Approval & Signature ]
            </td>
          </tr>
        </table>

        <div class="sec-banner"><span class="sq-symbol">■</span> TOPICS COVERED TODAY</div>
        <div class="sec-box-content">${escapeHtml(log.topics || '')}</div>

        <div class="sec-banner"><span class="sq-symbol">■</span> TASK / ASSIGNMENT</div>
        <div class="sec-box-content">${escapeHtml(log.assignment || '')}</div>

        <div class="sec-banner"><span class="sq-symbol">■</span> DOUBTS</div>
        <div class="sec-box-content">${escapeHtml(log.doubts || '')}</div>

        <div class="sec-banner"><span class="sq-symbol">■</span> IMPORTANT NOTES</div>
        <div class="sec-box-content">${escapeHtml(log.important_notes || '')}</div>
      </div>
    </div>
  `;
}

function loadActiveFormToPrintSheet() {
  const target = document.getElementById('fullSheetTarget');
  if (target) {
    target.setAttribute('data-custom-log', 'active');
    syncFullPrintSheet();
  }
}

function renderHistoryTable() {
  const tbody = document.getElementById('historyTableBody');
  if (!tbody) return;

  const query = (document.getElementById('historySearch')?.value || '').toLowerCase().trim();
  const logs = appState.logs.filter(log => !query || [
    log.date, log.day, log.combo, log.lab, log.trainer, log.topics,
    log.practical, log.assignment, log.doubts, log.important_notes
  ].some(value => String(value || '').toLowerCase().includes(query)));

  if (logs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">No logs found.</td></tr>`;
    return;
  }

  tbody.innerHTML = logs.map((l) => `
    <tr style="border-bottom: 1px solid var(--border-color);">
      <td style="padding: 0.75rem;"><strong>${escapeHtml(l.date)}</strong><br><small>${escapeHtml(formatTime(l.checkIn) || '')} - ${escapeHtml(formatTime(l.checkOut) || '')}</small></td>
      <td style="padding: 0.75rem;">${escapeHtml(l.day)}</td>
      <td style="padding: 0.75rem;"><span style="color: var(--accent-secondary); font-weight: 600;">${escapeHtml(l.combo)}</span></td>
      <td style="padding: 0.75rem;">${escapeHtml(l.lab || 'N/A')}</td>
      <td style="padding: 0.75rem;">${escapeHtml(l.trainer || 'N/A')}</td>
      <td style="padding: 0.75rem; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml((l.topics || '').split('\n')[0])}</td>
      <td style="padding: 0.75rem;">
        <button class="btn btn-outline" style="padding: 0.2rem 0.5rem; font-size: 0.75rem;" onclick="loadLogToForm('${l.id}')">Open / Edit</button>
      </td>
    </tr>
  `).join('');
}

function loadLogToForm(logId) {
  const log = appState.logs.find(l => l.id === logId);
  if (!log) return;

  appState.activeEditingLogId = log.id;

  document.getElementById('inputDate').value = log.date;
  document.getElementById('inputDay').value = log.day;
  document.getElementById('inputLab').value = log.lab || '';
  document.getElementById('inputCheckIn').value = formatTime(log.checkIn) || '';
  document.getElementById('inputCheckOut').value = formatTime(log.checkOut) || '';
  document.getElementById('inputTrainer').value = log.trainer || '';
  document.getElementById('inputTopics').value = log.topics || '';
  document.getElementById('inputAssignment').value = log.assignment || '';
  document.getElementById('inputDoubts').value = log.doubts || '';
  document.getElementById('inputImportantNotes').value = log.important_notes || '';

  updateLivePaper();
  switchAppTab('editor', document.querySelectorAll('.app-nav-link')[1]);
}

function printPaperSheet() {
  const select = document.getElementById('printLogSelect');
  if (select && select.value) {
    loadLogToPrintSheet(select.value);
  } else {
    renderBlankPrintSheet();
  }
  window.print();
}

function exportJSON() {
  const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(appState.logs, null, 2));
  const a = document.createElement('a');
  a.href = dataStr;
  a.download = `techwing_logs_${Date.now()}.json`;
  a.click();
}

function exportCSV() {
  let csv = "ID,Date,Day,Combo,Lab,Trainer\n";
  appState.logs.forEach(l => {
    csv += `"${l.id}","${l.date}","${l.day}","${l.combo}","${l.lab || ''}","${l.trainer || ''}"\n`;
  });
  const a = document.createElement('a');
  a.href = "data:text/csv;charset=utf-8," + encodeURIComponent(csv);
  a.download = `techwing_logs_${Date.now()}.csv`;
  a.click();
}

/* =========================================================
   SUGGESTIONS & WHATSAPP INTEGRATION (+91 8074404321)
   ========================================================= */
async function fetchSuggestions() {
  try {
    const res = await fetch('/api/suggestions');
    if (res.ok) {
      appState.suggestions = await res.json();
      renderSuggestions();
    }
  } catch (e) {
    console.warn("Could not fetch suggestions");
  }
}

function renderSuggestions() {
  const list = document.getElementById('suggestionsList');
  const countBadge = document.getElementById('sugCountBadge');

  if (countBadge) {
    countBadge.innerText = `${appState.suggestions.length} Received`;
  }

  if (!list) return;

  if (appState.suggestions.length === 0) {
    list.innerHTML = `<p style="color: var(--text-muted); text-align: center; padding: 2rem;">No suggestions submitted yet.</p>`;
    return;
  }

  list.innerHTML = appState.suggestions.map(s => `
    <div class="suggestion-card">
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <span class="sug-cat-tag">${escapeHtml(s.category)}</span>
        <span style="font-size: 0.75rem; color: var(--text-muted);">${s.date}</span>
      </div>
      <h4 style="font-size: 0.95rem; font-family: var(--font-display); color: var(--text-primary); margin-top: 0.2rem;">
        ${escapeHtml(s.subject)}
      </h4>
      <p style="font-size: 0.85rem; color: var(--text-secondary); line-height: 1.5; white-space: pre-wrap;">
        ${escapeHtml(s.message)}
      </p>
      <div style="font-size: 0.78rem; color: var(--accent-primary); font-weight: 500; margin-top: 0.3rem;">
        <i class="fa-solid fa-user-graduate"></i> Submitted by: ${escapeHtml(s.name)} (${escapeHtml(s.email)})
      </div>
    </div>
  `).join('');
}

async function handleSuggestionSubmit(e) {
  e.preventDefault();
  const name = document.getElementById('sugName').value.trim();
  const email = document.getElementById('sugEmail').value.trim();
  const category = document.getElementById('sugCategory').value;
  const subject = document.getElementById('sugSubject').value.trim();
  const message = document.getElementById('sugMessage').value.trim();

  if (!message || !subject) {
    alert("Please enter a subject and suggestion message before submitting.");
    return;
  }

  try {
    const res = await fetch('/api/suggestions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, category, subject, message })
    });

    const data = await res.json();

    if (res.ok) {
      alert(data.message || "Suggestion has been successfully submitted!");
      document.getElementById('sugSubject').value = '';
      document.getElementById('sugMessage').value = '';
      fetchSuggestions();
    } else {
      alert(data.error || "Failed to submit suggestion. Please try again.");
    }
  } catch (err) {
    // Offline fallback for suggestions
    const offlineSuggestions = JSON.parse(localStorage.getItem('techwing_offline_suggestions') || '[]');
    offlineSuggestions.push({ name, email, category, subject, message, date: new Date().toISOString() });
    localStorage.setItem('techwing_offline_suggestions', JSON.stringify(offlineSuggestions));
    alert("📱 Offline Mode: Suggestion saved locally on your phone! It will auto-sync when connection restores.");
    document.getElementById('sugSubject').value = '';
    document.getElementById('sugMessage').value = '';
  }
}

// Offline Data Synchronizer
async function syncOfflineData() {
  const offlineLogs = JSON.parse(localStorage.getItem('techwing_offline_logs') || '[]');
  if (offlineLogs.length > 0) {
    let allLogsSynced = true;
    for (const log of offlineLogs) {
      try {
        const response = await fetch('/api/logs', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(log)
        });
        if (!response.ok) allLogsSynced = false;
      } catch (e) {
        allLogsSynced = false;
        console.warn('Could not sync log entry:', e);
      }
    }
    if (allLogsSynced) {
      localStorage.removeItem('techwing_offline_logs');
      console.log('Synced offline log reports to Python server.');
      if (appState.currentUser) fetchUserLogs();
    }
  }

  const offlineSuggestions = JSON.parse(localStorage.getItem('techwing_offline_suggestions') || '[]');
  if (offlineSuggestions.length > 0) {
    for (const sug of offlineSuggestions) {
      try {
        await fetch('/api/suggestions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(sug)
        });
      } catch (e) {
        console.warn('Could not sync suggestion entry:', e);
      }
    }
    localStorage.removeItem('techwing_offline_suggestions');
    console.log('✅ Synced offline suggestions to Python server!');
    fetchSuggestions();
  }
}

// Toggle Owner Inbox View (Protected Access)
function toggleOwnerInbox() {
  const card = document.getElementById('ownerInboxCard');
  if (!card) return;

  if (card.style.display === 'block') {
    card.style.display = 'none';
    return;
  }

  const user = appState.currentUser;
  const isOwnerEmail = user && (user.email.toLowerCase() === 'kishore@techwing.com' || user.email.includes('admin') || user.email.includes('owner'));

  if (isOwnerEmail) {
    card.style.display = 'block';
    fetchSuggestions();
    return;
  }

  const code = prompt("🔒 Owner Access Required:\nEnter Owner Passcode to access Suggestions Inbox:");
  if (code === 'admin123' || code === 'techwing123' || code === '8074404321' || code === 'password123') {
    card.style.display = 'block';
    fetchSuggestions();
  } else if (code !== null) {
    alert("❌ Incorrect Owner Passcode. Suggestions inbox is private to the app owner only.");
  }
}

function hideOwnerInbox() {
  const card = document.getElementById('ownerInboxCard');
  if (card) card.style.display = 'none';
}


/* =========================================================
   OWNER MONITORING PORTAL DASHBOARD LOGIC
   ========================================================= */
let ownerState = {
  unlocked: false,
  passcode: 'admin123',
  masterLogs: [],
  users: [],
  suggestions: []
};

function unlockOwnerPortal() {
  const promptInput = document.getElementById('ownerPasscodePrompt');
  const promptVal = promptInput ? promptInput.value.trim() : '';
  const user = appState.currentUser;
  const isOwnerEmail = user && user.email.toLowerCase() === 'kishore@techwing.com';

  if (isOwnerEmail || ['admin123', 'techwing123', '8074404321', 'password123'].includes(promptVal)) {
    ownerState.unlocked = true;
    ownerState.passcode = promptVal || 'admin123';
    
    const gateCard = document.getElementById('ownerGateCard');
    const dashView = document.getElementById('ownerDashboardView');
    
    if (gateCard) gateCard.style.display = 'none';
    if (dashView) dashView.style.display = 'block';

    loadOwnerMasterData();
  } else {
    alert("❌ Invalid Owner Passcode. Access is restricted strictly to the App Owner.");
  }
}

async function loadOwnerMasterData() {
  const user = appState.currentUser;
  const passcode = ownerState.passcode || 'admin123';
  const email = user ? user.email : '';

  try {
    const res = await fetch(`/api/owner/master?passcode=${encodeURIComponent(passcode)}&email=${encodeURIComponent(email)}`);
    if (res.ok) {
      const data = await res.json();
      ownerState.masterLogs = data.logs || [];
      ownerState.users = data.users || [];
      ownerState.suggestions = data.suggestions || [];
      renderOwnerPortal();
    }
  } catch (e) {
    console.warn("Could not fetch owner master data offline", e);
  }
}

function renderOwnerPortal() {
  const elStudents = document.getElementById('ownerTotalStudents');
  const elLogs = document.getElementById('ownerTotalLogs');
  const elSug = document.getElementById('ownerTotalSuggestions');

  if (elStudents) elStudents.innerText = ownerState.users.length || 1;
  if (elLogs) elLogs.innerText = ownerState.masterLogs.length || 0;
  if (elSug) elSug.innerText = ownerState.suggestions.length || 0;

  renderOwnerMasterLogsTable(ownerState.masterLogs);
  renderOwnerStudentRoster(ownerState.users);
  renderOwnerSuggestionsInbox(ownerState.suggestions);
}

function renderOwnerMasterLogsTable(logsList) {
  const tbody = document.getElementById('ownerMasterLogsTbody');
  if (!tbody) return;

  if (logsList.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 1.5rem; color: var(--text-muted);">No student logs found.</td></tr>`;
    return;
  }

  tbody.innerHTML = logsList.map(l => `
    <tr style="border-bottom: 1px solid var(--border-color);">
      <td style="padding: 0.75rem;"><strong>${l.date}</strong><br><small style="color: var(--text-muted);">${l.day}</small></td>
      <td style="padding: 0.75rem;"><span style="color: var(--accent-primary); font-weight: 500;">${escapeHtml(l.user_email || 'kishore@techwing.com')}</span></td>
      <td style="padding: 0.75rem;"><span style="color: var(--accent-secondary); font-weight: 600;">${l.combo}</span></td>
      <td style="padding: 0.75rem;">${escapeHtml(l.lab || 'N/A')}<br><small style="color: var(--text-secondary);">${escapeHtml(l.trainer || 'N/A')}</small></td>
      <td style="padding: 0.75rem; max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml((l.topics || l.practical || '').split('\n')[0])}</td>
      <td style="padding: 0.75rem;">
        <button class="btn btn-outline" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" onclick="loadLogToForm('${l.id}')">View / Edit</button>
      </td>
    </tr>
  `).join('');
}

function renderOwnerStudentRoster(usersList) {
  const tbody = document.getElementById('ownerStudentRosterTbody');
  if (!tbody) return;

  if (usersList.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; padding: 1.5rem; color: var(--text-muted);">No registered student accounts found.</td></tr>`;
    return;
  }

  tbody.innerHTML = usersList.map(u => `
    <tr style="border-bottom: 1px solid var(--border-color);">
      <td style="padding: 0.75rem; font-weight: 600;"><i class="fa-solid fa-user-graduate" style="color: var(--accent-primary); margin-right: 0.4rem;"></i>${escapeHtml(u.name)}</td>
      <td style="padding: 0.75rem;">${escapeHtml(u.email)}</td>
      <td style="padding: 0.75rem;"><span class="user-combo-tag">${u.combo}</span></td>
      <td style="padding: 0.75rem;"><strong>${u.log_count || 0} Logs Submitted</strong></td>
    </tr>
  `).join('');
}

function renderOwnerSuggestionsInbox(sugList) {
  const list = document.getElementById('ownerPortalSuggestionsList');
  if (!list) return;

  if (sugList.length === 0) {
    list.innerHTML = `<p style="color: var(--text-muted); text-align: center; padding: 1.5rem;">No student suggestions submitted yet.</p>`;
    return;
  }

  list.innerHTML = sugList.map(s => `
    <div class="suggestion-card" style="border: 1px solid var(--border-color);">
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <span class="sug-cat-tag">${escapeHtml(s.category)}</span>
        <span style="font-size: 0.75rem; color: var(--text-muted);">${s.date}</span>
      </div>
      <h4 style="font-size: 1rem; font-family: var(--font-display); color: var(--text-primary); margin-top: 0.3rem;">
        ${escapeHtml(s.subject)}
      </h4>
      <p style="font-size: 0.88rem; color: var(--text-secondary); line-height: 1.5; white-space: pre-wrap; margin: 0.5rem 0;">
        ${escapeHtml(s.message)}
      </p>
      <div style="font-size: 0.8rem; color: var(--accent-primary); font-weight: 500; display: flex; justify-content: space-between; align-items: center;">
        <span><i class="fa-solid fa-user-graduate"></i> From: ${escapeHtml(s.name)} (${escapeHtml(s.email)})</span>
        <span class="status-badge completed" style="font-size: 0.7rem;">Status: Received</span>
      </div>
    </div>
  `).join('');
}

function switchOwnerSubTab(subTabName) {
  const logsEl = document.getElementById('ownerSub-master-logs');
  const rosterEl = document.getElementById('ownerSub-student-roster');
  const inboxEl = document.getElementById('ownerSub-suggestions-inbox');
  const dbEl = document.getElementById('ownerSub-db-inspector');

  if (logsEl) logsEl.style.display = subTabName === 'master-logs' ? 'block' : 'none';
  if (rosterEl) rosterEl.style.display = subTabName === 'student-roster' ? 'block' : 'none';
  if (inboxEl) inboxEl.style.display = subTabName === 'suggestions-inbox' ? 'block' : 'none';
  if (dbEl) dbEl.style.display = subTabName === 'db-inspector' ? 'block' : 'none';

  const btnL = document.getElementById('btnOwnerSubLogs');
  const btnR = document.getElementById('btnOwnerSubRoster');
  const btnI = document.getElementById('btnOwnerSubInbox');
  const btnD = document.getElementById('btnOwnerSubDb');

  if (btnL) btnL.className = subTabName === 'master-logs' ? 'btn btn-primary' : 'btn btn-outline';
  if (btnR) btnR.className = subTabName === 'student-roster' ? 'btn btn-primary' : 'btn btn-outline';
  if (btnI) btnI.className = subTabName === 'suggestions-inbox' ? 'btn btn-primary' : 'btn btn-outline';
  if (btnD) btnD.className = subTabName === 'db-inspector' ? 'btn btn-primary' : 'btn btn-outline';

  if (subTabName === 'db-inspector') {
    inspectServerDatabase();
  }
}

function exportMasterDataJSON() {
  const masterData = {
    exportDate: new Date().toISOString(),
    users: ownerState.users,
    logs: ownerState.masterLogs,
    suggestions: ownerState.suggestions
  };
  const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(masterData, null, 2));
  const a = document.createElement('a');
  a.href = dataStr;
  a.download = `techwing_master_system_export_${Date.now()}.json`;
  a.click();
}

function exportMasterLogsCSV() {
  let csv = "ID,Date,Day,Student_Email,Combo_Track,Lab,Trainer\n";
  ownerState.masterLogs.forEach(l => {
    csv += `"${l.id}","${l.date}","${l.day}","${l.user_email || ''}","${l.combo}","${l.lab || ''}","${l.trainer || ''}"\n`;
  });
  const a = document.createElement('a');
  a.href = "data:text/csv;charset=utf-8," + encodeURIComponent(csv);
  a.download = `techwing_master_student_logs_${Date.now()}.csv`;
  a.click();
}

async function inspectServerDatabase() {
  const passcode = ownerState.passcode || 'admin123';
  const email = appState.currentUser ? appState.currentUser.email : '';
  const container = document.getElementById('dbInspectorContent');
  if (!container) return;

  container.innerHTML = `<div style="text-align: center; padding: 2rem; color: var(--text-muted);"><i class="fa-solid fa-spinner fa-spin"></i> Inspecting database schema and health on server...</div>`;

  try {
    const res = await fetch(`/api/owner/inspect-db?passcode=${encodeURIComponent(passcode)}&email=${encodeURIComponent(email)}`);
    if (res.ok) {
      const dbInfo = await res.json();
      renderDbInspectorView(dbInfo);
    } else {
      container.innerHTML = `<div class="alert alert-danger" style="color: var(--accent-red); padding: 1rem;">❌ Failed to inspect database: Unauthorized access.</div>`;
    }
  } catch (err) {
    container.innerHTML = `<div class="alert alert-danger" style="color: var(--accent-red); padding: 1rem;">⚠️ Connection error inspecting database: ${err.message}</div>`;
  }
}

function renderDbInspectorView(info) {
  const container = document.getElementById('dbInspectorContent');
  if (!container) return;

  let tablesHtml = Object.keys(info.tables).map(tbl => `
    <div style="background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 8px; padding: 1rem;">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <h4 style="margin: 0; color: var(--accent-secondary); font-family: var(--font-display);">
          <i class="fa-solid fa-table"></i> ${tbl}
        </h4>
        <span class="status-badge completed">${info.tables[tbl].count} Records</span>
      </div>
      <p style="font-size: 0.78rem; color: var(--text-muted); margin: 0.5rem 0 0 0;">
        <strong>Columns:</strong> ${info.tables[tbl].columns.join(', ')}
      </p>
    </div>
  `).join('');

  let auditsHtml = (info.recent_audits || []).map(a => `
    <tr style="border-bottom: 1px solid var(--border-color); font-size: 0.8rem;">
      <td style="padding: 0.5rem; color: var(--text-muted);">${a.created_at}</td>
      <td style="padding: 0.5rem;"><span class="user-combo-tag">${a.action}</span></td>
      <td style="padding: 0.5rem; color: var(--accent-primary);">${escapeHtml(a.user_email || 'system')}</td>
      <td style="padding: 0.5rem;">${escapeHtml(a.ip_address || '127.0.0.1')}</td>
    </tr>
  `).join('');

  container.innerHTML = `
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin-bottom: 1rem;">
      <div class="dash-stat-card" style="padding: 1rem;">
        <div>
          <h4 style="font-size: 1.1rem; color: var(--accent-green);">${info.status}</h4>
          <p>DB Engine Status</p>
        </div>
      </div>
      <div class="dash-stat-card" style="padding: 1rem;">
        <div>
          <h4 style="font-size: 1.1rem;">${info.database_size_human}</h4>
          <p>Database File Size</p>
        </div>
      </div>
      <div class="dash-stat-card" style="padding: 1rem; grid-column: span 2;">
        <div>
          <h4 style="font-size: 0.85rem; word-break: break-all; color: var(--accent-primary);">${escapeHtml(info.database_file_path)}</h4>
          <p>Server Database File Location</p>
        </div>
      </div>
    </div>

    <h4 style="font-family: var(--font-display); margin-top: 1rem; margin-bottom: 0.5rem;">Database Tables & Schemas</h4>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 0.88rem;">
      ${tablesHtml}
    </div>

    <h4 style="font-family: var(--font-display); margin-top: 1.5rem; margin-bottom: 0.5rem;">Real-Time Activity & Security Audit Logs</h4>
    <div style="overflow-x: auto; background: var(--bg-secondary); border-radius: 8px; padding: 0.5rem;">
      <table style="width: 100%; border-collapse: collapse;">
        <thead>
          <tr style="border-bottom: 2px solid var(--border-color); text-align: left; font-size: 0.8rem; color: var(--text-secondary);">
            <th style="padding: 0.5rem;">Timestamp</th>
            <th style="padding: 0.5rem;">Action</th>
            <th style="padding: 0.5rem;">User Email</th>
            <th style="padding: 0.5rem;">IP Address</th>
          </tr>
        </thead>
        <tbody>
          ${auditsHtml || '<tr><td colspan="4" style="padding: 1rem; text-align: center;">No recent audit logs.</td></tr>'}
        </tbody>
      </table>
    </div>
  `;
}

function downloadDatabaseFile() {
  const passcode = ownerState.passcode || 'admin123';
  const email = appState.currentUser ? appState.currentUser.email : '';
  window.open(`/api/owner/download-db?passcode=${encodeURIComponent(passcode)}&email=${encodeURIComponent(email)}`, '_blank');
}


