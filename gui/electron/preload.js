'use strict';
// Preload runs in the renderer with Node access.
// The app is fully served by the FastAPI backend, so we only need to
// expose the app version for display in the UI if wanted.
const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  version: process.env.npm_package_version || '1.0.0',
});
