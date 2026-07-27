<template>
  <div class="app">
    <header>
      <h1>COROS Chatbox</h1>
      <p class="subtitle">Ask anything about your running data</p>
      <div class="header-toolbar">
        <button class="export-btn" @click="refreshCorosData" :disabled="refreshing" :title="lastUpdated ? 'Last updated: ' + new Date(lastUpdated).toLocaleString('zh-HK', {timeZone:'Asia/Hong_Kong'}) : 'Check latest update time'">
          {{ refreshing ? '🔄 Refreshing...' : '🔄 Refresh COROS' }}
        </button>
        <button v-if="selectedMessages.length > 0" class="export-btn" @click="showExportDialog = true">
          📄 Export ({{ selectedMessages.length }})
        </button>
        <button v-if="selectedMessages.length > 0" class="export-btn clear-btn" @click="deleteSelected">
          🗑️ Delete
        </button>
        <button v-if="messages.length > 0" class="export-btn new-btn" @click="newConversation">
          🆕 New Conversation
        </button>
      </div>
    </header>

    <div class="chat-container" ref="chatContainer">
      <div v-if="messages.length === 0" class="welcome">
        <div class="welcome-icon">👋</div>
        <h2>Welcome, Gary!</h2>
        <p>Ask about your COROS data, upload GPX/photo, or paste a race URL for analysis.</p>
        <div class="examples">
          <button v-for="ex in examples" :key="ex" @click="sendMessage(ex)" class="example-btn">
            {{ ex }}
          </button>
        </div>
        <button @click="toggleCorosCharts" class="charts-toggle-btn">
          {{ showCorosCharts ? 'Hide Charts' : 'Show Training Charts' }}
        </button>
        <div class="mode-selector">
          <label class="mode-option" :class="{ active: mode === 'auto' }">
            <input type="radio" value="auto" v-model="mode" /> 🤖 Auto
          </label>
          <label class="mode-option" :class="{ active: mode === 'data' }">
            <input type="radio" value="data" v-model="mode" /> 📊 Data Query
          </label>
          <label class="mode-option" :class="{ active: mode === 'coach' }">
            <input type="radio" value="coach" v-model="mode" /> 🏆 Coach Analysis
          </label>
        </div>
        <div v-if="showCorosCharts" class="coros-charts-area">
          <div class="chart-box">
            <h3>Monthly Running Volume</h3>
            <canvas ref="volumeChartCanvas"></canvas>
          </div>
          <div class="chart-box">
            <h3>Heart Rate Trend (90 days)</h3>
            <canvas ref="hrTrendCanvas"></canvas>
          </div>
          <div class="chart-box" v-if="trainingLoadData.length">
            <h3>Training Load (60 days)</h3>
            <canvas ref="trainingLoadCanvas"></canvas>
          </div>
        </div>
      </div>

      <div v-for="(msg, i) in messages" :key="i" :class="['message', msg.role, { selected: selectedMessages.includes(i) }]">
        <div class="msg-checkbox" @click="toggleSelect(i)" :title="selectedMessages.includes(i) ? 'Deselect' : 'Select for export'">
          <div :class="['check-box', { checked: selectedMessages.includes(i) }]">
            <span v-if="selectedMessages.includes(i)">✓</span>
          </div>
        </div>
        <div class="avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
        <div class="bubble">
          <div v-if="msg.mode" class="mode-badge">{{ msg.mode === 'data' ? '📊 Data' : '🏆 Coach' }}</div>
          <div v-if="msg.file" class="file-preview">
            <div v-if="msg.file.type === 'gpx' || msg.file.type === 'tcx' || msg.file.type === 'fit'" class="file-card">
              <span class="file-icon">🗺️</span>
              <div class="file-info">
                <strong>{{ msg.file.filename }}</strong>
                <span>{{ msg.file.summary }}</span>
              </div>
              <div v-if="msg.file.chartReady" class="gpx-charts">
                <div class="chart-box small" v-if="msg.file.hasEle" @click="expandCanvas($event, 'ele-' + msg.file.file_id)">
                  <h4>Elevation Profile <span class="expand-hint">🔍</span></h4>
                  <canvas :data-chart="'ele-' + msg.file.file_id" style="width:100%;height:auto;max-height:500px;pointer-events:none"></canvas>
                </div>
                <div class="chart-box small" v-if="msg.file.hasHr" @click="expandCanvas($event, 'hr-' + msg.file.file_id)">
                  <h4>Heart Rate <span class="expand-hint">🔍</span></h4>
                  <canvas :data-chart="'hr-' + msg.file.file_id" style="width:100%;height:auto;max-height:500px;pointer-events:none"></canvas>
                </div>
                <div class="chart-box small" v-if="msg.file.hasCad" @click="expandCanvas($event, 'cad-' + msg.file.file_id)">
                  <h4>Cadence <span class="expand-hint">🔍</span></h4>
                  <canvas :data-chart="'cad-' + msg.file.file_id" style="width:100%;height:auto;max-height:500px;pointer-events:none"></canvas>
                </div>
              </div>
            </div>
            <div v-else-if="msg.file.type === 'image'" class="file-card">
              <span class="file-icon">📷</span>
              <div class="file-info">
                <strong>{{ msg.file.filename }}</strong>
                <span>{{ msg.file.summary }}</span>
              </div>
              <img :src="'http://localhost:8000/api/uploads/' + msg.file.file_id" class="uploaded-image" @click="openImage($event)" />
            </div>
          </div>
          <div class="content" v-html="renderMarkdown(msg.content)"></div>
        </div>
      </div>

      <div v-if="fetching" class="message assistant">
        <div class="avatar">🌐</div>
        <div class="bubble">
          <div class="fetching-indicator">
            <div class="spinner"></div>
            <span>Fetching URL content...</span>
          </div>
        </div>
      </div>

      <div v-if="uploading" class="message assistant">
        <div class="avatar">📎</div>
        <div class="bubble">
          <div class="uploading-indicator">
            <div class="spinner"></div>
            <span>Uploading file...</span>
          </div>
        </div>
      </div>

      <div v-if="loading" class="message assistant">
        <div class="avatar">🤖</div>
        <div class="bubble">
          <div class="typing"><span></span><span></span><span></span></div>
        </div>
      </div>
    </div>

    <!-- Export Dialog -->
    <div v-if="showExportDialog" class="modal-overlay" @click.self="showExportDialog = false">
      <div class="export-dialog">
        <h3>📄 Export Report</h3>
        <div class="export-options">
          <div class="export-row">
            <label>Title</label>
            <input v-model="exportTitle" class="export-input" />
          </div>
          <div class="export-row">
            <label>Format</label>
            <div class="export-toggles">
              <button :class="['toggle-btn', { active: exportFormat === 'html' }]" @click="exportFormat = 'html'">HTML</button>
              <button :class="['toggle-btn', { active: exportFormat === 'pdf' }]" @click="exportFormat = 'pdf'">PDF (Print)</button>
            </div>
          </div>
          <div class="export-row">
            <label>Theme</label>
            <div class="export-toggles">
              <button :class="['toggle-btn', { active: exportTheme === 'dark' }]" @click="exportTheme = 'dark'">🌙 Dark</button>
              <button :class="['toggle-btn', { active: exportTheme === 'light' }]" @click="exportTheme = 'light'">☀️ Light</button>
              <button :class="['toggle-btn', { active: exportTheme === 'orange' }]" @click="exportTheme = 'orange'">🔥 Orange</button>
            </div>
          </div>
          <div class="export-row">
            <label>Charts</label>
            <label class="checkbox-label">
              <input type="checkbox" v-model="exportIncludeCharts" />
              Include chart images
            </label>
          </div>
        </div>
        <div class="export-actions">
          <button class="modal-btn secondary" @click="showExportDialog = false">Cancel</button>
          <button class="modal-btn primary" @click="doExport">Generate {{ exportFormat.toUpperCase() }}</button>
        </div>
      </div>
    </div>

    <!-- Chart Lightbox -->
    <div v-if="chartLightbox" class="lightbox-overlay" @click.self="chartLightbox = null" @keydown.esc="chartLightbox = null" ref="lightboxOverlay">
      <div class="lightbox-content">
        <button class="lightbox-close" @click="chartLightbox = null">&times;</button>
        <h3>{{ chartLightbox.title }}</h3>
        <div class="lightbox-controls">
          <button @click="lightboxZoomIn" title="Zoom In">➕</button>
          <button @click="lightboxZoomOut" title="Zoom Out">➖</button>
          <button @click="lightboxReset" title="Reset">⟲</button>
        </div>
        <div class="lightbox-img-wrap"
          @mousedown="lightboxDragStart"
          @mousemove="lightboxDragMove"
          @mouseup="lightboxDragEnd"
          @mouseleave="lightboxDragEnd"
          @wheel.prevent="lightboxWheel"
          ref="lightboxWrapper">
          <div v-if="chartLightbox.isSvg" ref="lightboxSvgContainer" style="display:flex;align-items:center;justify-content:center;width:85vw;height:75vh;overflow:hidden;"></div>
          <img v-else :src="chartLightbox.src" ref="lightboxImg" :style="lightboxImgStyle" />
        </div>
      </div>
    </div>

    <div class="input-area">
      <input type="file" ref="fileInput" accept=".gpx,.tcx,.fit,.jpg,.jpeg,.png,.webp" @change="onFileSelect" hidden />
      <button class="upload-btn" @click="$refs.fileInput.click()" :disabled="loading || uploading" title="Upload GPX/TCX/FIT/photo">
        <svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M16.5 6v11.5c0 2.21-1.79 4-4 4s-4-1.79-4-4V5c0-1.38 1.12-2.5 2.5-2.5s2.5 1.12 2.5 2.5v10.5c0 .55-.45 1-1 1s-1-.45-1-1V6H10v9.5c0 1.38 1.12 2.5 2.5 2.5s2.5-1.12 2.5-2.5V5c0-2.21-1.79-4-4-4S7 2.79 7 5v12.5c0 3.04 2.46 5.5 5.5 5.5s5.5-2.46 5.5-5.5V6h-1.5z"/></svg>
      </button>
      <textarea
        v-model="input"
        @keydown.enter.exact="send"
        placeholder="Ask about your runs, training load, fitness trends..."
        rows="2"
        ref="textarea"
        :disabled="loading"
      ></textarea>
      <button @click="send" :disabled="!input.trim() || loading">
        <svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
      </button>
    </div>
  </div>
</template>

<script>
import { Chart, registerables } from 'chart.js'
import mermaid from 'mermaid'
Chart.register(...registerables)
mermaid.initialize({ startOnLoad: false, theme: 'dark', securityLevel: 'loose' })

export default {
  data() {
    return {
      input: '',
      messages: [],
      loading: false,
      uploading: false,
      fetching: false,
      pendingFileIds: [],
      sessionId: Math.random().toString(36).substring(2, 14),
      mode: 'auto',
      showCorosCharts: false,
      monthlyVolume: [],
      heartRateData: [],
      trainingLoadData: [],
      chartInstances: {},
      selectedMessages: [],
      refreshing: false,
      lastUpdated: null,
      showExportDialog: false,
      exportFormat: 'html',
      exportTheme: 'dark',
      exportTitle: 'COROS Training Report',
      exportIncludeCharts: true,
      chartLightbox: null,
      lightboxZoom: 1,
      lightboxPanX: 0,
      lightboxPanY: 0,
      lightboxDragging: false,
      lightboxDragStartX: 0,
      lightboxDragStartY: 0,
      lightboxPanStartX: 0,
      lightboxPanStartY: 0,
      examples: [
        'How was my running volume this year?',
        'What is my current VO2max and fitness level?',
        'Show my marathon and half marathon race analysis',
        'How is my training load trending?',
        'What was my best pace run this year?',
        'Compare my monthly running volume',
        'Help me plan training for a race — paste URL below'
      ]
    }
  },
  computed: {
    lightboxImgStyle() {
      return {
        maxWidth: '100%',
        maxHeight: '100%',
        borderRadius: '8px',
        objectFit: 'contain',
        transform: `translate(${this.lightboxPanX}px, ${this.lightboxPanY}px) scale(${this.lightboxZoom})`,
        cursor: this.lightboxDragging ? 'grabbing' : 'grab',
        transition: this.lightboxDragging ? 'none' : 'transform 0.15s ease'
      }
    },
  },
  mounted() {
    const saved = localStorage.getItem('coros_messages')
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        if (Array.isArray(parsed)) this.messages = parsed
      } catch (_) {}
    }
    const sid = localStorage.getItem('coros_session_id')
    if (sid) this.sessionId = sid
    this.fetchLastUpdated()
    this.$nextTick(() => {
      this.renderMermaidDiagrams()
      this.reloadFileCharts()
    })
    document.addEventListener('click', this._chartClickDelegate)
  },
  beforeDestroy() {
    document.removeEventListener('click', this._chartClickDelegate)
  },
  watch: {
    messages: {
      handler(val) { localStorage.setItem('coros_messages', JSON.stringify(val)) },
      deep: true
    },
    sessionId(val) { localStorage.setItem('coros_session_id', val) }
  },
  methods: {
    async fetchLastUpdated() {
      try {
        const res = await fetch('http://localhost:8000/api/health')
        const data = await res.json()
        if (data.last_updated) this.lastUpdated = data.last_updated
      } catch (_) {}
    },
    newConversation() {
      this.messages = []
      this.sessionId = Math.random().toString(36).substring(2, 14)
      this.selectedMessages = []
      localStorage.removeItem('coros_messages')
    },
    deleteSelected() {
      const sorted = [...this.selectedMessages].sort((a, b) => b - a)
      for (const idx of sorted) {
        this.messages.splice(idx, 1)
      }
      this.selectedMessages = []
    },
    async onFileSelect(e) {
      const file = e.target.files[0]
      if (!file) return

      this.uploading = true
      const form = new FormData()
      form.append('file', file)

      try {
        const res = await fetch('http://localhost:8000/api/upload', {
          method: 'POST',
          body: form
        })
        const data = await res.json()
        this.pendingFileIds.push(data.file_id)

        if (data.type === 'image') {
          this.messages.push({
            role: 'user',
            content: '',
            file: { type: 'image', filename: data.data?.filename || file.name, file_id: data.file_id, summary: data.summary }
          })
        } else {
          const msgIdx = this.messages.length
          const fileType = data.type || 'gpx'
          this.messages.push({
            role: 'user',
            content: '',
            file: { type: fileType, filename: data.data?.filename || file.name, file_id: data.file_id, summary: data.summary, chartReady: false }
          })
          this.$nextTick(async () => {
            if (fileType === 'gpx') await this.loadFileCharts('gpx', data.file_id, msgIdx)
            else if (fileType === 'tcx') await this.loadFileCharts('tcx', data.file_id, msgIdx)
            else if (fileType === 'fit') await this.loadFileCharts('fit', data.file_id, msgIdx)
          })
        }

        this.$nextTick(() => this.scrollBottom())
      } catch (err) {
        this.messages.push({
          role: 'assistant',
          content: 'Failed to upload file: ' + err.message
        })
      }

      this.uploading = false
      e.target.value = ''
    },

    async loadFileCharts(fileType, fileId, msgIdx) {
      try {
        const res = await fetch(`http://localhost:8000/api/chart/${fileType}/${fileId}`)
        if (!res.ok) { console.warn('Chart API returned', res.status); return }
        const data = await res.json()
        const hasEle = data.elevations_m && data.elevations_m.some(e => e !== null)
        const hasHr = data.heart_rates && data.heart_rates.some(h => h !== null)
        const hasCad = data.cadences && data.cadences.some(c => c !== null)
        const msg = this.messages[msgIdx]
        msg.file.chartReady = true
        msg.file.hasEle = hasEle
        msg.file.hasHr = hasHr
        msg.file.hasCad = hasCad
        this.$nextTick(() => {
          this.$nextTick(() => {
            this.renderFileCharts(fileId, data, hasEle, hasHr, hasCad)
          })
        })
      } catch (e) {
        console.warn('loadFileCharts error:', e)
      }
    },

    reloadFileCharts() {
      this.messages.forEach((msg, idx) => {
        if (msg.file && msg.file.chartReady && msg.file.file_id && (msg.file.type === 'gpx' || msg.file.type === 'tcx' || msg.file.type === 'fit')) {
          const ft = msg.file.type || 'gpx'
          this.loadFileCharts(ft, msg.file.file_id, idx)
        }
      })
    },

    renderFileCharts(fileId, data, hasEle, hasHr, hasCad) {
      const distKm = data.distances_m ? data.distances_m.map(d => (d / 1000).toFixed(2)) : []
      console.log('renderFileCharts', fileId, 'hasEle:', hasEle, 'hasHr:', hasHr, 'hasCad:', hasCad, 'distKm.length:', distKm.length)

      this.destroyChart(fileId + '-ele')
      this.destroyChart(fileId + '-hr')
      this.destroyChart(fileId + '-cad')

      const cvs = (id) => document.querySelector(`[data-chart="${id}"]`)

      if (hasEle) {
        const canvas = cvs('ele-' + fileId)
        if (!canvas) { console.warn('ele canvas not found'); return }
        const valid = data.elevations_m.map((e, i) => ({ d: distKm[i], e })).filter(p => p.e !== null && p.d !== undefined)
        if (valid.length < 2) { console.warn('ele <2 valid points'); return }
        console.log('ele canvas found, dimensions before Chart:', canvas.offsetWidth, canvas.offsetHeight)
        const ctx = canvas.getContext('2d')
        const chart = new Chart(ctx, {
          type: 'line',
          data: { labels: valid.map(p => p.d), datasets: [{ label: 'Elevation (m)', data: valid.map(p => p.e), borderColor: '#f97316', backgroundColor: 'rgba(249,115,22,0.1)', fill: true, tension: 0.3, pointRadius: 0, borderWidth: 2 }] },
          options: { responsive: true, maintainAspectRatio: true, aspectRatio: 3, resizeDelay: 100, plugins: { legend: { display: false } }, scales: { x: { title: { display: true, text: 'km', color: '#a1a1aa' }, ticks: { color: '#71717a' }, grid: { color: '#27272a' } }, y: { title: { display: true, text: 'm', color: '#a1a1aa' }, ticks: { color: '#71717a' }, grid: { color: '#27272a' } } } }
        })
        this.chartInstances[fileId + '-ele'] = chart
        console.log('ele chart created, dims:', chart.canvas.offsetWidth, chart.canvas.offsetHeight, 'canvas attr:', chart.canvas.width, chart.canvas.height)
      }

      if (hasHr) {
        const canvas = cvs('hr-' + fileId)
        if (!canvas) { console.warn('hr canvas not found'); return }
        const valid = data.heart_rates.map((h, i) => ({ d: distKm[i], h })).filter(p => p.h !== null && p.d !== undefined)
        if (valid.length < 2) return
        const ctx = canvas.getContext('2d')
        this.chartInstances[fileId + '-hr'] = new Chart(ctx, {
          type: 'line',
          data: { labels: valid.map(p => p.d), datasets: [{ label: 'Heart Rate (bpm)', data: valid.map(p => p.h), borderColor: '#ef4444', backgroundColor: 'rgba(239,68,68,0.1)', fill: true, tension: 0.3, pointRadius: 0, borderWidth: 2 }] },
          options: { responsive: true, maintainAspectRatio: true, aspectRatio: 3, resizeDelay: 100, plugins: { legend: { display: false } }, scales: { x: { title: { display: true, text: 'km', color: '#a1a1aa' }, ticks: { color: '#71717a' }, grid: { color: '#27272a' } }, y: { title: { display: true, text: 'bpm', color: '#a1a1aa' }, ticks: { color: '#71717a' }, grid: { color: '#27272a' } } } }
        })
      }

      if (hasCad) {
        const canvas = cvs('cad-' + fileId)
        if (!canvas) { console.warn('cad canvas not found'); return }
        const valid = data.cadences.map((c, i) => ({ d: distKm[i], c })).filter(p => p.c !== null && p.d !== undefined)
        if (valid.length < 2) return
        const ctx = canvas.getContext('2d')
        this.chartInstances[fileId + '-cad'] = new Chart(ctx, {
          type: 'line',
          data: { labels: valid.map(p => p.d), datasets: [{ label: 'Cadence (spm)', data: valid.map(p => p.c), borderColor: '#22c55e', backgroundColor: 'rgba(34,197,94,0.1)', fill: true, tension: 0.3, pointRadius: 0, borderWidth: 2 }] },
          options: { responsive: true, maintainAspectRatio: true, aspectRatio: 3, resizeDelay: 100, plugins: { legend: { display: false } }, scales: { x: { title: { display: true, text: 'km', color: '#a1a1aa' }, ticks: { color: '#71717a' }, grid: { color: '#27272a' } }, y: { title: { display: true, text: 'spm', color: '#a1a1aa' }, ticks: { color: '#71717a' }, grid: { color: '#27272a' } } } }
        })
      }
    },

    destroyChart(key) {
      if (this.chartInstances[key]) {
        this.chartInstances[key].destroy()
        delete this.chartInstances[key]
      }
    },

    async refreshCorosData() {
      this.refreshing = true
      try {
        const res = await fetch('http://localhost:8000/api/refresh', { method: 'POST' })
        const data = await res.json()
        if (data.success) {
          this.messages.push({ role: 'assistant', content: '✅ COROS data refreshed successfully!', mode: 'data' })
          this.showCorosCharts = false
          this.monthlyVolume = []
          this.fetchLastUpdated()
        } else {
          this.messages.push({ role: 'assistant', content: '❌ Refresh failed:\n' + (data.stderr || 'Unknown error'), mode: 'data' })
        }
      } catch (e) {
        this.messages.push({ role: 'assistant', content: '❌ Failed to refresh: ' + e.message, mode: 'data' })
      }
      this.refreshing = false
      this.$nextTick(() => this.scrollBottom())
    },

    async toggleCorosCharts() {
      this.showCorosCharts = !this.showCorosCharts
      if (this.showCorosCharts && this.monthlyVolume.length === 0) {
        try {
          const res = await fetch('http://localhost:8000/api/chart/coros-summary')
          const data = await res.json()
          this.monthlyVolume = data.monthly_volume || []
          this.heartRateData = data.heart_rate || []
          this.trainingLoadData = data.training_load || []
          this.$nextTick(() => this.renderCorosCharts())
        } catch (e) {
          // silently fail
        }
      } else if (this.showCorosCharts) {
        this.$nextTick(() => this.renderCorosCharts())
      }
    },

    renderCorosCharts() {
      this.destroyChart('volume')
      this.destroyChart('hr-trend')
      this.destroyChart('tl')

      if (this.monthlyVolume.length && this.$refs.volumeChartCanvas) {
        const ctx = this.$refs.volumeChartCanvas.getContext('2d')
        this.chartInstances['volume'] = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: this.monthlyVolume.map(d => d.month),
            datasets: [{
              label: 'km',
              data: this.monthlyVolume.map(d => d.km),
              backgroundColor: 'rgba(249,115,22,0.7)',
              borderColor: '#f97316',
              borderWidth: 1,
              borderRadius: 4
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              x: { ticks: { color: '#71717a' }, grid: { color: '#27272a' } },
              y: { title: { display: true, text: 'km', color: '#a1a1aa' }, ticks: { color: '#71717a' }, grid: { color: '#27272a' }, beginAtZero: true }
            }
          }
        })
      }

      if (this.heartRateData.length && this.$refs.hrTrendCanvas) {
        const ctx = this.$refs.hrTrendCanvas.getContext('2d')
        this.chartInstances['hr-trend'] = new Chart(ctx, {
          type: 'line',
          data: {
            labels: this.heartRateData.map(d => d.date.slice(5)),
            datasets: [{
              label: 'Avg HR',
              data: this.heartRateData.map(d => d.avg_hr),
              borderColor: '#ef4444',
              backgroundColor: 'rgba(239,68,68,0.1)',
              fill: true,
              tension: 0.3,
              pointRadius: 2,
              borderWidth: 2
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              x: { ticks: { color: '#71717a', maxTicksLimit: 15 }, grid: { color: '#27272a' } },
              y: { title: { display: true, text: 'bpm', color: '#a1a1aa' }, ticks: { color: '#71717a' }, grid: { color: '#27272a' } }
            }
          }
        })
      }

      if (this.trainingLoadData.length && this.$refs.trainingLoadCanvas) {
        const ctx = this.$refs.trainingLoadCanvas.getContext('2d')
        this.chartInstances['tl'] = new Chart(ctx, {
          type: 'line',
          data: {
            labels: this.trainingLoadData.map(d => d.date.slice(5)),
            datasets: [
              {
                label: 'Short-term',
                data: this.trainingLoadData.map(d => d.st),
                borderColor: '#f97316',
                backgroundColor: 'rgba(249,115,22,0.1)',
                fill: false,
                tension: 0.3,
                pointRadius: 1,
                borderWidth: 2
              },
              {
                label: 'Long-term',
                data: this.trainingLoadData.map(d => d.lt),
                borderColor: '#22c55e',
                backgroundColor: 'rgba(34,197,94,0.1)',
                fill: false,
                tension: 0.3,
                pointRadius: 1,
                borderWidth: 2
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: '#a1a1aa' } } },
            scales: {
              x: { ticks: { color: '#71717a', maxTicksLimit: 15 }, grid: { color: '#27272a' } },
              y: { ticks: { color: '#71717a' }, grid: { color: '#27272a' }, beginAtZero: true }
            }
          }
        })
      }
    },

    async send() {
      const msg = this.input.trim()
      if (!msg && this.pendingFileIds.length === 0) return
      if (this.loading) return

      const fileIds = [...this.pendingFileIds]
      this.pendingFileIds = []

      if (this.messages.length > 0 && this.messages[this.messages.length - 1].role === 'user' && !this.messages[this.messages.length - 1].content) {
        this.messages[this.messages.length - 1].content = msg
      } else if (msg) {
        this.messages.push({ role: 'user', content: msg })
      }

      this.input = ''
      this.fetching = false
      this.loading = true

      const hasUrl = /https?:\/\/[^\s]+/.test(msg)
      if (hasUrl) this.fetching = true

      try {
        const res = await fetch('http://localhost:8000/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: msg || '(see uploaded file)', file_ids: fileIds, session_id: this.sessionId, mode: this.mode })
        })
        const data = await res.json()
        this.fetching = false

        let reply = data.reply
        if (data.fetched_urls && data.fetched_urls.length > 0) {
          reply = 'Fetched: ' + data.fetched_urls.join(', ') + '\n\n' + reply
        }
        this.messages.push({ role: 'assistant', content: reply, mode: data.mode || 'auto' })
        this.renderMermaidDiagrams()
      } catch (e) {
        this.fetching = false
        this.messages.push({ role: 'assistant', content: 'Error connecting to server. Make sure the backend is running.' })
      }

      this.loading = false
      this.$nextTick(() => this.scrollBottom())
    },

    sendMessage(msg) {
      this.input = msg
      this.send()
    },

    scrollBottom() {
      const el = this.$refs.chatContainer
      if (el) el.scrollTop = el.scrollHeight
    },

    openImage(e) {
      window.open(e.target.src, '_blank')
    },

    _chartClickDelegate(e) {
      const mermaidEl = e.target.closest('.mermaid')
      if (mermaidEl) {
        const svg = mermaidEl.querySelector('svg')
        if (svg) { console.log('mermaid click detected'); this.expandChart('mermaid', svg, mermaidEl) }
      }
    },

    expandCanvas(e, chartAttr) {
      const canvas = e.currentTarget.querySelector('canvas')
      if (!canvas) return
      try {
        const dataUrl = canvas.toDataURL('image/png')
        const title = e.currentTarget.querySelector('h4')?.textContent?.replace('🔍','').trim() || 'Chart'
        this.showLightbox(dataUrl, title)
      } catch (ex) {
        console.warn('expandCanvas failed', ex)
      }
    },

    expandChart(type, el, parentEl) {
      if (type === 'mermaid') {
        try {
          const s = new XMLSerializer().serializeToString(el)
          console.log('mermaid svg first 300 chars:', s.substring(0, 300))
          const title = parentEl?.getAttribute('data-title') || 'Mermaid Chart'
          this.showLightbox(s, title, true)
        } catch (e) {
          console.warn('expandChart failed', e)
        }
      }
    },

    showLightbox(src, title, isSvg) {
      this.lightboxZoom = 1
      this.lightboxPanX = 0
      this.lightboxPanY = 0
      this.chartLightbox = { src, title, isSvg: !!isSvg }
      if (isSvg) {
        this.$nextTick(() => this._renderLightboxSvg())
      }
    },

    _renderLightboxSvg() {
      const el = this.$refs.lightboxSvgContainer
      console.log('_renderLightboxSvg el:', !!el, 'src len:', this.chartLightbox?.src?.length)
      if (!el) return
      el.innerHTML = ''
      try {
        const parser = new DOMParser()
        const doc = parser.parseFromString(this.chartLightbox.src, 'image/svg+xml')
        const svgEl = doc.documentElement
        console.log('svgEl parsed:', svgEl?.tagName, 'xmlns:', svgEl?.getAttribute('xmlns'))
        svgEl.dataset.baseStyle = 'max-width:100%;max-height:100%'
        this._lightboxSvgEl = svgEl
        this._updateSvgTransform()
        el.appendChild(svgEl)
        console.log('svg appended, child count:', el.childNodes.length)
      } catch (e) {
        console.warn('lightbox svg parse error', e)
      }
    },

    _updateSvgTransform() {
      if (!this._lightboxSvgEl) return
      const svg = this._lightboxSvgEl
      const baseStyle = svg.dataset.baseStyle || 'max-width:100%;max-height:100%'
      svg.setAttribute('style',
        baseStyle + ';pointer-events:auto;' +
        'transform:translate(' + this.lightboxPanX + 'px,' + this.lightboxPanY + 'px) scale(' + this.lightboxZoom + ');' +
        'transition:transform 0.15s ease;cursor:' + (this.lightboxDragging ? 'grabbing' : 'grab')
      )
    },

    lightboxZoomIn() { this.lightboxZoom = Math.min(this.lightboxZoom + 0.25, 5); this._updateSvgTransform() },
    lightboxZoomOut() { this.lightboxZoom = Math.max(this.lightboxZoom - 0.25, 0.25); this._updateSvgTransform() },
    lightboxReset() { this.lightboxZoom = 1; this.lightboxPanX = 0; this.lightboxPanY = 0; this._updateSvgTransform() },

    lightboxWheel(e) {
      const delta = e.deltaY > 0 ? -0.15 : 0.15
      this.lightboxZoom = Math.max(0.25, Math.min(5, this.lightboxZoom + delta))
      this._updateSvgTransform()
    },

    lightboxDragStart(e) {
      if (e.button !== 0) return
      this.lightboxDragging = true
      this.lightboxDragStartX = e.clientX
      this.lightboxDragStartY = e.clientY
      this.lightboxPanStartX = this.lightboxPanX
      this.lightboxPanStartY = this.lightboxPanY
    },
    lightboxDragMove(e) {
      if (!this.lightboxDragging) return
      this.lightboxPanX = this.lightboxPanStartX + (e.clientX - this.lightboxDragStartX)
      this.lightboxPanY = this.lightboxPanStartY + (e.clientY - this.lightboxDragStartY)
      this._updateSvgTransform()
    },
    lightboxDragEnd() { this.lightboxDragging = false },

    renderMarkdown(text) {
      if (!text) return ''
      const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      // Protect mermaid blocks from \n -> <br> conversion
      const mermaidBlocks = []
      let html = text.replace(/```mermaid\n?([\s\S]*?)```/g, (match, code) => {
        const idx = mermaidBlocks.length
        mermaidBlocks.push(code)
        return `~~~MERMAID${idx}~~~`
      })
      // Convert markdown tables to HTML tables (before escaping)
      const tableBlocks = []
      html = html.replace(/^\|.+\n\|[-:| ]+\|\n(?:\|.+\n?)+/gm, (match) => {
        const idx = tableBlocks.length
        const lines = match.trimEnd().split('\n')
        const headerCells = lines[0].split('|').filter(c => c.trim()).map(c => esc(c.trim()))
        const dataLines = lines.slice(2).filter(l => l.trim().length > 0)
        let table = '<table class="chat-table">'
        table += '<thead><tr>'
        headerCells.forEach(h => { table += `<th>${h}</th>` })
        table += '</tr></thead>'
        if (dataLines.length > 0) {
          table += '<tbody>'
          dataLines.forEach(row => {
            const cells = row.split('|').filter(c => c.trim()).map(c => esc(c.trim()))
            if (cells.length) {
              table += '<tr>'
              cells.forEach(c => { table += `<td>${c}</td>` })
              table += '</tr>'
            }
          })
          table += '</tbody>'
        }
        table += '</table>'
        tableBlocks.push(table)
        return `~~~TABLE${idx}~~~`
      })
      html = html
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/### (.+)/g, '<h3>$1</h3>')
        .replace(/## (.+)/g, '<h2>$1</h2>')
        .replace(/# (.+)/g, '<h1>$1</h1>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/^- (.+)/gm, '<li>$1</li>')
        .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
        .replace(/\n/g, '<br>')
        .replace(/<br><br>/g, '</p><p>')
      // Restore table blocks
      tableBlocks.forEach((table, i) => {
        html = html.replace(`~~~TABLE${i}~~~`, table)
      })
      // Restore mermaid blocks
      mermaidBlocks.forEach((code, i) => {
        html = html.replace(`~~~MERMAID${i}~~~`, `<div class="mermaid" data-title="Mermaid Chart" style="cursor:pointer">${code}</div>`)
      })
      html = '<div>' + html + '</div>'
      return html
    },

    toggleSelect(i) {
      const idx = this.selectedMessages.indexOf(i)
      if (idx >= 0) {
        this.selectedMessages.splice(idx, 1)
      } else {
        this.selectedMessages.push(i)
      }
    },

    async captureChartImages() {
      const images = {}
      const byFileId = {}

      for (const key in this.chartInstances) {
        try {
          const chart = this.chartInstances[key]
          chart.resize()
          chart.draw()
          const fileId = key.replace(/-(ele|hr|cad)$/, '')
          const type = key.includes('-ele') ? 'elevation' : key.includes('-hr') ? 'heartrate' : key.includes('-cad') ? 'cadence' : 'chart'
          const dataUrl = chart.canvas.toDataURL('image/png')
          images[key] = dataUrl
          if (key.includes('-ele') || key.includes('-hr') || key.includes('-cad')) {
            if (!byFileId[fileId]) byFileId[fileId] = []
            byFileId[fileId].push({ type, dataUrl })
          }
        } catch (e) {
          console.warn('captureChartImages: chart instance', key, 'failed', e)
        }
      }

      const mermaidDivs = document.querySelectorAll('.mermaid')
      if (mermaidDivs.length > 0) {
        const esc = s => s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
        await Promise.all(Array.from(mermaidDivs).map(async (el, idx) => {
          try {
            const svgEl = el.querySelector('svg')
            if (svgEl) {
              const s = new XMLSerializer().serializeToString(svgEl)
              images['mermaid-' + idx] = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(s)
            } else {
              const code = el.textContent.trim()
              const { svg } = await mermaid.render('mermaid-export-' + idx, code)
              el.innerHTML = svg
              images['mermaid-' + idx] = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg)
            }
          } catch (e) {
            console.warn('captureChartImages: mermaid ' + idx + ' failed', e)
          }
        }))
      }

      images._byFileId = byFileId
      images._mermaidCount = Object.keys(images).filter(k => k.startsWith('mermaid-')).length
      return images
    },

    getExportMessages() {
      this.selectedMessages.sort((a, b) => a - b)
      return this.selectedMessages.map(i => this.messages[i])
    },

    async doExport() {
      const msgs = this.getExportMessages()
      const theme = this.exportTheme
      const now = new Date().toLocaleString('zh-HK', { timeZone: 'Asia/Hong_Kong' })

      const themeColors = {
        dark: { bg: '#0f0f13', card: '#18181b', border: '#27272a', text: '#e4e4e7', muted: '#71717a', accent: '#f97316', userBubble: '#f97316', userText: '#fff', aiBubble: '#18181b' },
        light: { bg: '#ffffff', card: '#f4f4f5', border: '#d4d4d8', text: '#18181b', muted: '#71717a', accent: '#ea580c', userBubble: '#ea580c', userText: '#fff', aiBubble: '#f4f4f5' },
        orange: { bg: '#0f0f13', card: '#1c1917', border: '#292524', text: '#fde68a', muted: '#a8a29e', accent: '#f97316', userBubble: '#f97316', userText: '#fff', aiBubble: '#1c1917' },
      }
      const c = themeColors[theme] || themeColors.dark

      if (this.exportIncludeCharts) {
        if (this.showCorosCharts) {
          this.$nextTick(() => this.renderCorosCharts())
        }
        await this.$nextTick()
      }

      const charts = this.exportIncludeCharts ? await this.captureChartImages() : {}
      const byFileId = (charts && charts._byFileId) || {}
      if (charts) charts._mermaidNextIdx = 0

      this._exportAccent = c.accent
      let msgHtml = ''
      const sorted = [...this.selectedMessages].sort((a, b) => a - b)
      sorted.forEach((idx) => {
        const msg = this.messages[idx]
        const isUser = msg.role === 'user'
        const bubbleBg = isUser ? c.userBubble : c.aiBubble
        const bubbleColor = isUser ? c.userText : c.text
        const avatar = isUser ? '👤' : '🤖'

        let content = this.renderExportContent(msg.content || '', charts)
        let fileHtml = ''
        if (msg.file) {
          if (msg.file.type === 'image') {
            fileHtml = `<div style="margin:8px 0"><strong>${msg.file.filename}</strong></div>`
          } else {
            let chartImgs = ''
            if (msg.file.chartReady && msg.file.file_id && byFileId[msg.file.file_id]) {
              byFileId[msg.file.file_id].forEach(ch => {
                chartImgs += `<img src="${ch.dataUrl}" style="width:100%;height:auto;border-radius:8px;margin:4px 0" />\n`
              })
            }
            fileHtml = `<div style="background:${c.card};border:1px solid ${c.border};padding:10px 14px;border-radius:10px;margin:8px 0;font-size:13px;color:${c.muted}">
              🗺️ <strong>${msg.file.filename}</strong> — ${msg.file.summary || ''}
              ${chartImgs ? '<div style="margin-top:8px">' + chartImgs + '</div>' : ''}
            </div>`
          }
        }

        msgHtml += `
          <div style="display:flex;gap:10px;margin-bottom:16px;flex-direction:${isUser ? 'row-reverse' : 'row'}">
            <div style="width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:16px;background:${isUser ? c.accent : c.border};flex-shrink:0">${avatar}</div>
            <div style="max-width:85%;padding:12px 16px;border-radius:14px;font-size:14px;line-height:1.6;background:${bubbleBg};color:${bubbleColor};${isUser ? '' : 'border:1px solid ' + c.border}">
              ${fileHtml}
              <div>${content}</div>
            </div>
          </div>`
      })

      try {
        const html = `<!DOCTYPE html>
<html lang="zh-HK">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>${this.exportTitle}</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background:${c.bg}; color:${c.text}; padding:24px; }
h1 { font-size:22px; background:linear-gradient(135deg,${c.accent},#ef4444); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:4px; }
.sub { color:${c.muted}; font-size:13px; margin-bottom:24px; padding-bottom:12px; border-bottom:1px solid ${c.border}; }
@media print { body { padding:16px; } }
</style>
</head>
<body>
<h1>${this.exportTitle}</h1>
<div class="sub">Generated ${now} | ${sorted.length} messages</div>
${msgHtml}
</body>
</html>`

        if (this.exportFormat === 'html') {
          const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
          const url = URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = 'coros-report.html'
          a.click()
          URL.revokeObjectURL(url)
        } else {
          const w = window.open('', '_blank')
          w.document.write(html)
          w.document.close()
          w.focus()
          setTimeout(() => { w.print() }, 500)
        }
      } catch (e) {
        console.error('Export failed:', e)
        alert('Export failed: ' + e.message)
      }

      this.showExportDialog = false
    },

    renderExportContent(text, charts = {}) {
      if (!text) return ''
      const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

      const totalMermaid = charts._mermaidCount || 0
      let mermaidIdx = charts._mermaidNextIdx || 0

      const mermaidBlocks = []
      const tableBlocks = []

      let html = text.replace(/```mermaid\n?([\s\S]*?)```/g, (match, code) => {
        const idx = mermaidBlocks.length
        if (mermaidIdx < totalMermaid) {
          mermaidBlocks.push(`<div style="background:#1a1a2e;border-radius:10px;padding:12px;text-align:center;margin:8px 0">
            <img src="${charts['mermaid-' + mermaidIdx]}" style="width:100%;height:auto" />
          </div>`)
          mermaidIdx++
        } else {
          mermaidBlocks.push(`<pre style="background:#0f0f13;border:1px solid #27272a;border-radius:8px;padding:12px;font-size:12px;color:#e4e4e7;overflow-x:auto">${esc(code)}</pre>`)
        }
        return `~~~MERMAID${idx}~~~`
      })
      charts._mermaidNextIdx = mermaidIdx

      html = html.replace(/^\|.+\n\|[-:| ]+\|\n(?:\|.+\n?)+/gm, (match) => {
        const idx = tableBlocks.length
        const lines = match.trimEnd().split('\n')
        const headerCells = lines[0].split('|').filter(c => c.trim()).map(c => esc(c.trim()))
        const dataLines = lines.slice(2).filter(l => l.trim().length > 0)
        let table = '<table style="border-collapse:collapse;width:100%;margin:8px 0;font-size:13px">'
        table += '<thead><tr>'
        headerCells.forEach(h => { table += `<th style="border:1px solid #27272a;padding:6px 10px;text-align:left;background:#18181b">${h}</th>` })
        table += '</tr></thead>'
        if (dataLines.length > 0) {
          table += '<tbody>'
          dataLines.forEach(row => {
            const cells = row.split('|').filter(c => c.trim()).map(c => esc(c.trim()))
            if (cells.length) {
              table += '<tr>'
              cells.forEach(c => { table += `<td style="border:1px solid #27272a;padding:6px 10px">${c}</td>` })
              table += '</tr>'
            }
          })
          table += '</tbody>'
        }
        table += '</table>'
        tableBlocks.push(table)
        return `~~~TABLE${idx}~~~`
      })

      html = esc(html)
        .replace(/### (.+)/g, '<h3>$1</h3>')
        .replace(/## (.+)/g, '<h2>$1</h2>')
        .replace(/# (.+)/g, '<h1>$1</h1>')
        .replace(/\*\*(.+?)\*\*/g, '<strong style="color:' + this._exportAccent + '">$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code style="background:#27272a;padding:2px 6px;border-radius:4px;font-size:13px">$1</code>')
        .replace(/^- (.+)/gm, '<li>$1</li>')
        .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
        .replace(/\n/g, '<br>')
        .replace(/<br><br>/g, '</p><p>')

      tableBlocks.forEach((table, i) => {
        html = html.replace(`~~~TABLE${i}~~~`, table)
      })
      mermaidBlocks.forEach((block, i) => {
        html = html.replace(`~~~MERMAID${i}~~~`, block)
      })

      html = '<div>' + html + '</div>'
      return html
    },

    renderMermaidDiagrams() {
      this.$nextTick(() => {
        const elements = document.querySelectorAll('.mermaid')
        if (elements.length === 0) return
        const esc = s => s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
        elements.forEach(async (el) => {
          if (el.dataset.rendered) return
          el.dataset.rendered = '1'
          const code = el.textContent.trim()
          if (!code) return
          try {
            const { svg } = await mermaid.render('m-' + Date.now() + '-' + Math.random().toString(36).slice(2, 6), code)
            const clean = svg.replace(/NaN/g, '0')
            el.innerHTML = clean
          } catch (e) {
            el.innerHTML = `<pre style="background:#0f0f13;border:1px solid #27272a;border-radius:8px;padding:12px;font-size:12px;color:#a1a1aa;overflow-x:auto">${esc(code)}</pre>`
          }
        })
      })
    }
  }
}
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #0f0f13;
  color: #e4e4e7;
  height: 100vh;
  overflow: hidden;
}

.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 75%;
  margin: 0 auto;
  padding: 0 16px;
}

header {
  text-align: center;
  padding: 20px 0 12px;
  border-bottom: 1px solid #27272a;
  flex-shrink: 0;
}

header h1 {
  font-size: 22px;
  font-weight: 700;
  background: linear-gradient(135deg, #f97316, #ef4444);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  font-size: 13px;
  color: #71717a;
  margin-top: 2px;
}

.chat-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px 0;
  scroll-behavior: smooth;
}

.chat-container::-webkit-scrollbar { width: 6px; }
.chat-container::-webkit-scrollbar-thumb { background: #27272a; border-radius: 3px; }

.welcome {
  text-align: center;
  padding: 20px 16px;
}

.welcome-icon { font-size: 48px; margin-bottom: 12px; }
.welcome h2 { font-size: 20px; margin-bottom: 8px; }
.welcome p { color: #71717a; font-size: 14px; margin-bottom: 20px; }

.examples {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 400px;
  margin: 0 auto 20px;
}

.example-btn {
  background: #18181b;
  border: 1px solid #27272a;
  color: #a1a1aa;
  padding: 10px 16px;
  border-radius: 10px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.example-btn:hover {
  background: #27272a;
  color: #e4e4e7;
  border-color: #f97316;
}

.charts-toggle-btn {
  background: #18181b;
  border: 1px solid #f97316;
  color: #f97316;
  padding: 10px 20px;
  border-radius: 10px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
  margin-bottom: 16px;
}

.charts-toggle-btn:hover {
  background: #27272a;
}

.header-toolbar {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-top: 8px;
}

.export-btn {
  background: #18181b;
  border: 1px solid #f97316;
  color: #f97316;
  padding: 6px 14px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.export-btn:hover {
  background: #f97316;
  color: white;
}

.clear-btn {
  border-color: #3f3f46;
  color: #a1a1aa;
}

.clear-btn:hover {
  background: #27272a;
  border-color: #ef4444;
  color: #ef4444;
}

.new-btn {
  border-color: #3f3f46;
  color: #a1a1aa;
}

.new-btn:hover {
  background: #27272a;
  border-color: #22c55e;
  color: #22c55e;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.export-dialog {
  background: #18181b;
  border: 1px solid #27272a;
  border-radius: 16px;
  padding: 24px;
  width: 90%;
  max-width: 440px;
}

.export-dialog h3 {
  font-size: 18px;
  margin-bottom: 20px;
}

.export-options {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 20px;
}

.export-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.export-row label {
  font-size: 13px;
  color: #a1a1aa;
}

.export-input {
  background: #0f0f13;
  border: 1px solid #27272a;
  border-radius: 8px;
  padding: 10px 12px;
  color: #e4e4e7;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.export-input:focus {
  border-color: #f97316;
}

.export-toggles {
  display: flex;
  gap: 6px;
}

.toggle-btn {
  flex: 1;
  padding: 8px;
  border-radius: 8px;
  border: 1px solid #27272a;
  background: transparent;
  color: #a1a1aa;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-btn.active {
  background: #f97316;
  color: white;
  border-color: #f97316;
}

.toggle-btn:hover:not(.active) {
  border-color: #52525b;
  color: #e4e4e7;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #a1a1aa;
  cursor: pointer;
}

.checkbox-label input {
  accent-color: #f97316;
}

.export-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.modal-btn {
  padding: 10px 20px;
  border-radius: 10px;
  border: none;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.modal-btn.primary {
  background: #f97316;
  color: white;
}

.modal-btn.primary:hover {
  background: #ea580c;
}

.modal-btn.secondary {
  background: #27272a;
  color: #a1a1aa;
}

.modal-btn.secondary:hover {
  background: #3f3f46;
  color: #e4e4e7;
}

.coros-charts-area {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 8px;
}

.chart-box {
  background: #18181b;
  border: 1px solid #27272a;
  border-radius: 10px;
  padding: 12px;
  overflow: hidden;
}

.chart-box h3, .chart-box h4 {
  font-size: 13px;
  color: #a1a1aa;
  margin-bottom: 8px;
  text-align: left;
}

.chart-box.small {
  padding: 4px;
  margin-top: 4px;
}

.chart-box canvas {
  display: block;
  width: 100%;
  max-height: 500px;
}

.gpx-charts {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.message {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
  animation: fadeIn 0.3s ease;
  transition: all 0.2s;
}

.message.selected {
  background: rgba(249,115,22,0.08);
  border-radius: 12px;
  padding: 4px 8px;
  margin-left: -8px;
  margin-right: -8px;
  border: 1px solid rgba(249,115,22,0.3);
}

.msg-checkbox {
  display: flex;
  align-items: flex-start;
  padding-top: 6px;
  cursor: pointer;
  flex-shrink: 0;
}

.check-box {
  width: 18px;
  height: 18px;
  border-radius: 4px;
  border: 2px solid #3f3f46;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  color: white;
  transition: all 0.2s;
}

.check-box.checked {
  background: #f97316;
  border-color: #f97316;
}

.check-box:hover {
  border-color: #f97316;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
  margin-top: 4px;
}

.user .avatar { background: #f97316; }
.assistant .avatar { background: #27272a; }

.bubble {
  max-width: 85%;
  padding: 12px 16px;
  border-radius: 14px;
  font-size: 14px;
  line-height: 1.6;
}

.user .bubble {
  background: #f97316;
  color: white;
  border-bottom-right-radius: 4px;
  margin-left: auto;
}

.assistant .bubble {
  background: #18181b;
  border: 1px solid #27272a;
  border-bottom-left-radius: 4px;
}

.bubble .content p { margin-bottom: 8px; }
.bubble .content p:last-child { margin-bottom: 0; }
.bubble .content h1 { font-size: 18px; margin: 12px 0 6px; }
.bubble .content h2 { font-size: 16px; margin: 10px 0 6px; }
.bubble .content h3 { font-size: 14px; margin: 8px 0 4px; }
.bubble .content strong { color: #f97316; }
.bubble .content code {
  background: #27272a;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}
.bubble .content ul { margin: 4px 0; padding-left: 20px; }
.bubble .content li { margin-bottom: 2px; }
.bubble .content .chat-table {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
  font-size: 13px;
}
.bubble .content .chat-table th {
  background: #27272a;
  color: #f97316;
  padding: 6px 10px;
  text-align: left;
  font-weight: 600;
  border: 1px solid #3f3f46;
}
.bubble .content .chat-table td {
  padding: 5px 10px;
  border: 1px solid #3f3f46;
  color: #e4e4e7;
}
.bubble .content .chat-table tr:nth-child(even) td {
  background: #1f1f23;
}
.bubble .content .chat-table tr:hover td {
  background: #27272a;
}

.file-preview {
  margin-bottom: 8px;
  width: 100%;
}

.file-card {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  background: #27272a;
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px solid #3f3f46;
  flex-wrap: wrap;
}

.file-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.file-info {
  display: flex;
  flex-direction: column;
  font-size: 13px;
  gap: 2px;
  overflow: hidden;
  flex: 1;
}

.file-info strong {
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-info span {
  color: #a1a1aa;
  font-size: 12px;
  white-space: pre-line;
}

.uploaded-image {
  max-width: 200px;
  max-height: 200px;
  border-radius: 8px;
  cursor: pointer;
  margin-left: 8px;
  border: 1px solid #3f3f46;
  transition: transform 0.2s;
}

.uploaded-image:hover {
  transform: scale(1.02);
}

.uploading-indicator, .fetching-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #a1a1aa;
  font-size: 13px;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #3f3f46;
  border-top-color: #f97316;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.typing {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.typing span {
  width: 6px;
  height: 6px;
  background: #71717a;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out;
}

.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.6); }
  40% { transform: scale(1); }
}

.input-area {
  display: flex;
  gap: 8px;
  padding: 12px 0 20px;
  border-top: 1px solid #27272a;
  flex-shrink: 0;
  align-items: center;
}

.input-area textarea {
  flex: 1;
  background: #18181b;
  border: 1px solid #27272a;
  border-radius: 12px;
  padding: 12px 16px;
  color: #e4e4e7;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  outline: none;
  transition: border-color 0.2s;
  min-height: 44px;
  max-height: 300px;
}

.input-area textarea:focus {
  border-color: #f97316;
}

.input-area textarea::placeholder {
  color: #52525b;
}

.input-area button, .upload-btn {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;
}

.input-area button {
  background: #f97316;
  color: white;
}

.input-area button:hover:not(:disabled) { background: #ea580c; }
.input-area button:disabled { opacity: 0.4; cursor: not-allowed; }

.upload-btn {
  background: transparent;
  color: #71717a;
  border: 1px solid #27272a;
}

.upload-btn:hover:not(:disabled) {
  background: #18181b;
  color: #e4e4e7;
  border-color: #f97316;
}

.upload-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.mermaid {
  background: #1a1a2e;
  border-radius: 10px;
  padding: 12px;
  margin: 8px 0;
  overflow-x: auto;
  text-align: center;
}

.mermaid svg {
  max-width: 100%;
  max-height: 150px;
  height: auto;
}
.mermaid svg * { pointer-events: bounding-box; }

.mode-selector {
  display: flex;
  gap: 8px;
  padding: 8px 0 12px;
  flex-wrap: wrap;
}

.mode-option {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  border-radius: 20px;
  background: #18181b;
  border: 1px solid #27272a;
  color: #a1a1aa;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}

.mode-option input { display: none; }

.mode-option.active {
  background: #f97316;
  color: white;
  border-color: #f97316;
}

.mode-option:hover:not(.active) {
  border-color: #52525b;
  color: #e4e4e7;
}

.mode-badge {
  display: inline-block;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: #27272a;
  color: #a1a1aa;
  margin-bottom: 6px;
}

.lightbox-overlay {
  position: fixed;
  inset: 0;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 24px;
}
.lightbox-content {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.lightbox-content h3 {
  color: #e4e4e7;
  font-size: 16px;
}
.lightbox-close {
  position: absolute;
  top: -36px;
  right: 0;
  background: none;
  border: none;
  color: #a1a1aa;
  font-size: 28px;
  cursor: pointer;
  padding: 4px 8px;
  line-height: 1;
}
.lightbox-close:hover { color: #e4e4e7; }
.lightbox-controls {
  display: flex;
  gap: 8px;
}
.lightbox-controls button {
  background: #27272a;
  border: 1px solid #52525b;
  color: #e4e4e7;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.lightbox-controls button:hover { background: #3f3f46; }
.lightbox-img-wrap {
  overflow: auto;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  max-width: 90vw;
  max-height: 80vh;
}
.lightbox-img-wrap svg {
  max-width: 100%;
  max-height: 100%;
  pointer-events: auto;
}
.expand-hint {
  font-size: 11px;
  opacity: 0.6;
}
.chart-box.small { cursor: pointer; }
.chart-box.small canvas { pointer-events: none; }
</style>
