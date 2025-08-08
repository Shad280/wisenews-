const { app, BrowserWindow } = require('electron')
const path = require('path')
const { spawn } = require('child_process')

let mainWindow
let flaskProcess

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: true
    },
    icon: path.join(__dirname, 'static/icon-192.png')
  })

  // Start Flask server
  startFlaskServer()

  // Load the app after a short delay
  setTimeout(() => {
    mainWindow.loadURL('http://localhost:5000')
  }, 3000)

  // Open DevTools in development
  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools()
  }
}

function startFlaskServer() {
  flaskProcess = spawn('python', ['app.py'], {
    cwd: __dirname,
    stdio: 'inherit'
  })

  flaskProcess.on('error', (err) => {
    console.error('Failed to start Flask server:', err)
  })
}

// This method will be called when Electron has finished initialization
app.whenReady().then(createWindow)

// Quit when all windows are closed
app.on('window-all-closed', () => {
  if (flaskProcess) {
    flaskProcess.kill()
  }
  
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})

// Cleanup on app quit
app.on('before-quit', () => {
  if (flaskProcess) {
    flaskProcess.kill()
  }
})
