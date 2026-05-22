'use strict';

/**
 * TechnobizTrader — Electron main process
 *
 * Flow:
 *   1. Show a themed splash window immediately (no blank screen).
 *   2. Locate a Python interpreter that has the required packages.
 *   3. Auto-install missing packages from requirements-app.txt via pip.
 *   4. Spawn gui_server.py from the backend resource directory.
 *   5. Poll http://127.0.0.1:PORT/api/status until the server is up.
 *   6. Open the main BrowserWindow and load the trading office.
 *   7. On quit, cleanly terminate the Python process.
 */

const {
  app, BrowserWindow, Menu, shell,
  ipcMain, dialog, nativeTheme,
} = require('electron');
const path   = require('path');
const fs     = require('fs');
const http   = require('http');
const { spawn, execFileSync } = require('child_process');

// ── Constants ────────────────────────────────────────────────────────────────
const BACKEND_PORT  = 8765;
const BACKEND_URL   = `http://127.0.0.1:${BACKEND_PORT}`;
const POLL_INTERVAL = 500;   // ms between readiness checks
const POLL_TIMEOUT  = 90000; // give Python 90 s to start (longer for slow machines)
const IS_DEV        = !app.isPackaged;

// ── State ────────────────────────────────────────────────────────────────────
let mainWindow    = null;
let splashWindow  = null;
let pythonProcess = null;
let pollTimer     = null;
let pollDeadline  = null;

// ── Python discovery ─────────────────────────────────────────────────────────
function findPython () {
  if (process.platform === 'win32') {
    try {
      const raw   = execFileSync('where.exe', ['python'], { timeout: 5000, stdio: 'pipe' });
      const paths = raw.toString().trim().split(/\r?\n/)
        .map(p => p.trim())
        .filter(p => p && !p.toLowerCase().includes('windowsapps'));

      for (const py of paths) {
        try {
          execFileSync(py, ['-c', 'import sys; sys.exit(0)'], { timeout: 6000, stdio: 'pipe' });
          return py;
        } catch { /* try next */ }
      }
    } catch { /* where.exe failed */ }
  }
  // Non-Windows / fallback
  for (const exe of ['python3', 'python', 'py']) {
    try {
      execFileSync(exe, ['-c', 'import sys; sys.exit(0)'], { timeout: 5000, stdio: 'pipe' });
      return exe;
    } catch { /* try next */ }
  }
  return 'python'; // last resort
}

// ── Backend directory ─────────────────────────────────────────────────────────
function backendDir () {
  return IS_DEV
    ? path.join(__dirname, '..', '..') // repo root in dev
    : path.join(process.resourcesPath, 'backend');
}

// ── User-data .env path (writable even in packaged builds) ───────────────────
function userEnvPath () {
  return path.join(app.getPath('userData'), '.env');
}

// ── Ensure a writable .env exists in userData ─────────────────────────────────
function ensureUserEnv () {
  const dest = userEnvPath();
  if (!fs.existsSync(dest)) {
    const tmpl  = path.join(backendDir(), '.env.template');
    const blank = path.join(backendDir(), '.env');
    const src   = fs.existsSync(tmpl) ? tmpl : fs.existsSync(blank) ? blank : null;
    if (src) {
      try { fs.copyFileSync(src, dest); } catch { /* non-fatal */ }
    } else {
      fs.writeFileSync(dest, '# TechnobizTrader configuration\n');
    }
  }
}

// ── Splash status helper ──────────────────────────────────────────────────────
function setSplashStatus (msg) {
  if (splashWindow && !splashWindow.isDestroyed()) {
    const safe = msg.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
    splashWindow.webContents.executeJavaScript(
      `document.getElementById('status').textContent = '${safe}';`
    ).catch(() => {});
  }
}

// ── Dependency check & auto-install ──────────────────────────────────────────
function ensureRequirements (python) {
  return new Promise((resolve, reject) => {
    // Quick probe: if all key packages importable, skip install
    try {
      execFileSync(
        python,
        ['-c', 'import fastapi, uvicorn, sse_starlette, anthropic, pandas'],
        { timeout: 10000, stdio: 'pipe' }
      );
      return resolve(); // all good
    } catch { /* need to install */ }

    const reqFile = path.join(backendDir(), 'requirements-app.txt');
    if (!fs.existsSync(reqFile)) {
      // No requirements file — nothing we can do, proceed anyway
      return resolve();
    }

    setSplashStatus('Installing dependencies (first launch)…');

    const pip = spawn(
      python,
      ['-m', 'pip', 'install', '--quiet', '--no-warn-script-location',
       '-r', reqFile],
      { stdio: ['ignore', 'pipe', 'pipe'], windowsHide: true }
    );

    let dotCount = 0;
    const dotTimer = setInterval(() => {
      dotCount++;
      setSplashStatus(`Installing dependencies${''.padEnd(dotCount % 4, '.')}  (this may take a minute)`);
    }, 800);

    const logPath = path.join(app.getPath('userData'), 'pip-install.log');
    const logStream = fs.createWriteStream(logPath, { flags: 'a' });

    pip.stdout.pipe(logStream);
    pip.stderr.pipe(logStream);

    pip.on('close', (code) => {
      clearInterval(dotTimer);
      logStream.end();
      if (code === 0) {
        setSplashStatus('Dependencies ready.');
        resolve();
      } else {
        reject(new Error(
          `pip install failed (exit code ${code}).\nSee ${logPath} for details.`
        ));
      }
    });

    pip.on('error', (err) => {
      clearInterval(dotTimer);
      logStream.end();
      reject(err);
    });
  });
}

// ── Splash screen ─────────────────────────────────────────────────────────────
function createSplash () {
  splashWindow = new BrowserWindow({
    width: 520, height: 340,
    frame: false, resizable: false, center: true,
    alwaysOnTop: true, transparent: true,
    webPreferences: { nodeIntegration: false, contextIsolation: true },
    icon: path.join(__dirname, '..', 'assets', 'icon.ico'),
    show: false,
  });

  const html = `<!DOCTYPE html><html>
<head><meta charset="utf-8">
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    font-family: -apple-system, 'Segoe UI', sans-serif;
    background: #0A1628;
    border: 2px solid #F0B428;
    border-radius: 14px;
    overflow: hidden;
    width: 520px; height: 340px;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    color: #fff;
    -webkit-app-region: drag;
  }
  .ring {
    width: 90px; height: 90px;
    border: 5px solid #1A2E50;
    border-top-color: #F0B428;
    border-right-color: #22C55E;
    border-radius: 50%;
    animation: spin 1.1s linear infinite;
    margin-bottom: 24px;
    position: relative;
  }
  .ring::after {
    content: 'T';
    position: absolute; inset:0;
    display:flex; align-items:center; justify-content:center;
    font-size: 32px; font-weight: 900;
    color: #F0B428;
    animation: spin-reverse 1.1s linear infinite;
  }
  @keyframes spin         { to { transform: rotate(360deg);  } }
  @keyframes spin-reverse { to { transform: rotate(-360deg); } }
  h1 { font-size: 26px; font-weight: 800; letter-spacing: 1px; color: #F0B428; }
  h2 { font-size: 13px; font-weight: 400; color: #7A9CC0; margin-top: 6px; }
  #status {
    margin-top: 28px; font-size: 12px; color: #4A7FA5;
    height: 18px; letter-spacing: 0.5px;
    max-width: 400px; text-align: center;
  }
  .bar-track {
    margin-top: 16px; width: 280px; height: 3px;
    background: #1A2E50; border-radius: 3px; overflow: hidden;
  }
  .bar-fill {
    height: 100%; width: 0%;
    background: linear-gradient(90deg, #22C55E, #F0B428);
    border-radius: 3px;
    animation: progress 60s ease-in forwards;
  }
  @keyframes progress { to { width: 90%; } }
</style></head>
<body>
  <div class="ring"></div>
  <h1>TechnobizTrader</h1>
  <h2>7-Agent ICT Trading System</h2>
  <div id="status">Checking Python environment…</div>
  <div class="bar-track"><div class="bar-fill"></div></div>
</body></html>`;

  splashWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(html)}`);
  splashWindow.once('ready-to-show', () => splashWindow.show());
}

// ── Main window ───────────────────────────────────────────────────────────────
function createMain () {
  mainWindow = new BrowserWindow({
    width: 1440, height: 900,
    minWidth: 1100, minHeight: 700,
    title: 'TechnobizTrader',
    icon: path.join(__dirname, '..', 'assets', 'icon.ico'),
    backgroundColor: '#0A1628',
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: true,
    },
  });

  const menu = Menu.buildFromTemplate([
    {
      label: 'File',
      submenu: [
        {
          label: 'Open User Data Folder',
          click: () => shell.openPath(app.getPath('userData')),
        },
        { type: 'separator' },
        { role: 'quit', label: 'Exit TechnobizTrader' },
      ],
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' },
        ...(IS_DEV ? [{ type: 'separator' }, { role: 'toggleDevTools' }] : []),
      ],
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'User Manual',
          click: () => {
            const manualPath = path.join(backendDir(), 'docs', 'USER_MANUAL.md');
            if (fs.existsSync(manualPath)) shell.openPath(manualPath);
          },
        },
        {
          label: 'Support',
          click: () => shell.openExternal('mailto:erickomari243@gmail.com'),
        },
        { type: 'separator' },
        {
          label: 'About TechnobizTrader',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'none',
              icon: path.join(__dirname, '..', 'assets', 'icon.ico'),
              title: 'About TechnobizTrader',
              message: 'TechnobizTrader v1.0.0',
              detail:
                '7-Agent ICT Trading System\n' +
                'By My Digital Solutions\n' +
                'erickomari243@gmail.com\n\n' +
                'Copyright © 2026 My Digital Solutions.\nAll rights reserved.',
            });
          },
        },
      ],
    },
  ]);
  Menu.setApplicationMenu(menu);

  mainWindow.loadURL(BACKEND_URL);

  mainWindow.once('ready-to-show', () => {
    if (splashWindow && !splashWindow.isDestroyed()) splashWindow.destroy();
    mainWindow.show();
    if (IS_DEV) mainWindow.webContents.openDevTools({ mode: 'detach' });
  });

  mainWindow.on('closed', () => { mainWindow = null; });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

// ── Backend readiness polling ─────────────────────────────────────────────────
function pollBackend () {
  if (Date.now() > pollDeadline) {
    clearInterval(pollTimer);
    const logPath = path.join(app.getPath('userData'), 'backend.log');
    dialog.showErrorBox(
      'TechnobizTrader — Startup Failed',
      'The Python backend did not start within 90 seconds.\n\n' +
      'Please ensure Python 3.11+ is installed and on your PATH.\n\n' +
      `Log file: ${logPath}`
    );
    app.quit();
    return;
  }

  const req = http.get(`${BACKEND_URL}/api/status`, { timeout: 2000 }, (res) => {
    if (res.statusCode === 200 || res.statusCode === 401) {
      clearInterval(pollTimer);
      createMain();
    }
  });
  req.on('error', () => { /* backend not yet ready */ });
  req.end();
}

// ── Python process spawner ────────────────────────────────────────────────────
function startBackend (python) {
  const bDir   = backendDir();
  const script = path.join(bDir, 'gui_server.py');

  if (!fs.existsSync(script)) {
    dialog.showErrorBox(
      'Missing Backend',
      `gui_server.py not found at:\n${script}\n\nReinstall TechnobizTrader.`
    );
    app.quit();
    return;
  }

  setSplashStatus('Starting Python backend…');

  const env = {
    ...process.env,
    TECHNOBIZ_USERDATA: app.getPath('userData'),
    GUI_HOST: '127.0.0.1',
    GUI_PORT: String(BACKEND_PORT),
    PYTHONUNBUFFERED: '1',
  };

  const logPath = path.join(app.getPath('userData'), 'backend.log');
  const logFile = fs.openSync(logPath, 'a');

  pythonProcess = spawn(python, [script], {
    cwd: bDir,
    env,
    stdio: ['ignore', logFile, logFile],
    detached: false,
    windowsHide: true,
  });

  pythonProcess.on('error', (err) => {
    dialog.showErrorBox(
      'Python Error',
      `Failed to start Python:\n${err.message}\n\n` +
      'Ensure Python 3.11+ is installed and on your PATH.'
    );
    app.quit();
  });

  pythonProcess.on('exit', (code, signal) => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      const logPath2 = path.join(app.getPath('userData'), 'backend.log');
      dialog.showErrorBox(
        'Backend Stopped',
        `The Python backend exited unexpectedly (code ${code}, signal ${signal}).\n\n` +
        `See ${logPath2} for details.`
      );
      app.quit();
    }
  });

  pollDeadline = Date.now() + POLL_TIMEOUT;
  pollTimer    = setInterval(pollBackend, POLL_INTERVAL);
}

// ── App lifecycle ─────────────────────────────────────────────────────────────
nativeTheme.themeSource = 'dark';

app.whenReady().then(async () => {
  ensureUserEnv();
  createSplash();

  // Wait for splash to render before heavy work
  await new Promise(r => setTimeout(r, 300));

  const python = findPython();

  try {
    await ensureRequirements(python);
  } catch (err) {
    dialog.showErrorBox(
      'Dependency Installation Failed',
      `Could not install required Python packages.\n\n${err.message}\n\n` +
      'Please run manually:\n  pip install -r requirements-app.txt\n\n' +
      `Log: ${path.join(app.getPath('userData'), 'pip-install.log')}`
    );
    app.quit();
    return;
  }

  startBackend(python);

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createMain();
  });
});

app.on('window-all-closed', () => {
  killBackend();
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => killBackend());

function killBackend () {
  if (pollTimer) clearInterval(pollTimer);
  if (pythonProcess && !pythonProcess.killed) {
    try {
      if (process.platform === 'win32') {
        execFileSync('taskkill', ['/PID', String(pythonProcess.pid), '/T', '/F'], {
          stdio: 'ignore',
        });
      } else {
        pythonProcess.kill('SIGTERM');
      }
    } catch { /* process may have already exited */ }
    pythonProcess = null;
  }
}

// ── IPC ───────────────────────────────────────────────────────────────────────
ipcMain.handle('open-userdata', () => shell.openPath(app.getPath('userData')));
