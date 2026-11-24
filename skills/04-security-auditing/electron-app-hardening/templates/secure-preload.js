'use strict';
// Starter for a sandboxed preload. Replace the lists with this app's exact
// allowlist and keep them in sync with the main-process allowlist module.
const { contextBridge, ipcRenderer } = require('electron');

const CHANNELS = new Set(['app:getState', 'app:save']);
const EVENTS = new Set(['app:changed']);

contextBridge.exposeInMainWorld('app_api', {
  invoke(channel, payload) {
    if (!CHANNELS.has(channel)) {
      return Promise.reject(new Error('IPC channel not allowed: ' + channel));
    }
    return ipcRenderer.invoke(channel, payload || {});
  },
  on(channel, callback) {
    if (!EVENTS.has(channel) || typeof callback !== 'function') return () => {};
    const listener = (_event, ...args) => callback(...args);
    ipcRenderer.on(channel, listener);
    return () => ipcRenderer.removeListener(channel, listener);
  },
});
