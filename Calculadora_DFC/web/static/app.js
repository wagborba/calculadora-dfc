/* =========================================================
   DFC Framework — app.js
   Vanilla JS, no external dependencies.
   ========================================================= */

'use strict';

// -----------------------------------------------------------------------
// State
// -----------------------------------------------------------------------
const state = {
  currentDimIndex: -1,   // -1 = intro, 0–5 = dimensions
  productName: '',
  scores: {},            // { dim_id: { param_id: score_int_or_null } }
  skipped: new Set(),
  results: null,
};

// -----------------------------------------------------------------------
// Utility helpers
// -----------------------------------------------------------------------

/**
 * Returns a color hex for a normalised CF value (0–1).
 * @param {number} value
 * @returns {string}
 */
function cfColor(value) {
  if (value < 0.2) return '#10B981';
  if (value < 0.4) return '#84CC16';
  if (value < 0.6) return '#F59E0B';
  if (value < 0.8) return '#F97316';
  return '#EF4444';
}

/**
 * Returns a verbal classification for a normalised CF value.
 * @param {number} value
 * @returns {string}
 */
function cfLabel(value) {
  if (value < 0.2) return 'Fricção irrisória';
  if (value < 0.4) return 'Fricção baixa';
  if (value < 0.6) return 'Fricção moderada';
  if (value < 0.8) return 'Fricção alta';
  return 'Fricção crítica';
}

/**
 * Escape HTML special characters.
 * @param {string} str
 * @returns {string}
 */
function escHtml(str) {
  const d = document.createElement('div');
  d.textContent = String(str);
  return d.innerHTML;
}

/**
 * Format a date ISO string to pt-BR short form.
 * @param {string} iso
 * @returns {string}
 */
function fmtDate(iso) {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString('pt-BR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
    });
  } catch (_) {
    return iso ? iso.slice(0, 10) : '';
  }
}

// -----------------------------------------------------------------------
// DOM refs (lazy — looked up when needed)
// -----------------------------------------------------------------------
const $ = (id) => document.getElementById(id);

// -----------------------------------------------------------------------
// init
// -----------------------------------------------------------------------
function init() {
  const btnStart   = $('btn-start');
  const btnNext    = $('btn-next');
  const btnPrev    = $('btn-prev');
  const productInp = $('product-name');

  btnStart.addEventListener('click', startEvaluation);
  btnNext.addEventListener('click', nextStep);
  btnPrev.addEventListener('click', prevStep);

  productInp.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') startEvaluation();
  });
}

// -----------------------------------------------------------------------
// startEvaluation
// -----------------------------------------------------------------------
function startEvaluation() {
  const productInp  = $('product-name');
  const introError  = $('intro-error');
  const name        = productInp.value.trim();

  introError.hidden = true;

  if (!name) {
    introError.textContent = 'Por favor, informe o nome do produto para continuar.';
    introError.hidden = false;
    productInp.focus();
    return;
  }

  state.productName = name;
  state.skipped = new Set();

  // Initialise score map for all dimensions
  state.scores = {};
  window.DIMENSIONS.forEach((dim) => {
    state.scores[dim.id] = {};
    dim.parameters.forEach((p) => {
      state.scores[dim.id][p.id] = null;
    });
  });

  $('intro-section').hidden = true;
  $('eval-section').hidden  = false;

  renderDimension(0);
}

// -----------------------------------------------------------------------
// renderDimension
// -----------------------------------------------------------------------
function renderDimension(index) {
  state.currentDimIndex = index;

  const dims      = window.DIMENSIONS;
  const total     = dims.length;
  const dim       = dims[index];
  const isSkipped = state.skipped.has(dim.id);

  // Progress bar
  $('progress-bar').style.width = `${((index + 1) / total) * 100}%`;

  // Step label
  $('step-label').textContent = `Dimensão ${index + 1} de ${total}`;

  // Step counter
  $('step-counter').textContent = `${index + 1} / ${total}`;

  // Next button label
  const btnNext = $('btn-next');
  if (index === total - 1) {
    btnNext.textContent = 'Calcular CF ✓';
  } else {
    btnNext.textContent = 'Próximo →';
  }

  // Prev button
  $('btn-prev').disabled = false;

  // Build card HTML
  const paramsHtml = dim.parameters.map((p) => {
    const currentScore = state.scores[dim.id] ? state.scores[dim.id][p.id] : null;

    const btns = [1, 2, 3, 4, 5].map((v) => {
      const active = currentScore === v ? 'active' : '';
      const labels = {
        1: '1 — Sem problema',
        2: '2 — Leve',
        3: '3 — Moderada',
        4: '4 — Grave',
        5: '5 — Crítica',
      };
      return `<button
        class="score-btn ${active}"
        data-val="${v}"
        data-dim="${escHtml(dim.id)}"
        data-param="${escHtml(p.id)}"
        title="${labels[v]}"
        >${v}</button>`;
    }).join('');

    const skipActive = currentScore === null && state.scores[dim.id] && (p.id in state.scores[dim.id]) && state.scores[dim.id][p.id] === null
      ? ''   // null is default (unset), not "skip"
      : '';

    // "Pular" button — value null
    const skipMarked = currentScore === 'skip' ? 'active' : '';
    const skipBtn = `<button
      class="score-btn skip ${skipMarked}"
      data-val="skip"
      data-dim="${escHtml(dim.id)}"
      data-param="${escHtml(p.id)}"
      >Pular</button>`;

    return `
      <div class="param-item">
        <div class="param-name">${escHtml(p.name)}</div>
        <div class="param-desc">${escHtml(p.description)}</div>
        <div class="score-group">
          ${btns}
          ${skipBtn}
        </div>
      </div>`;
  }).join('');

  const weightPct = Math.round(dim.weight * 100);
  const containerClass = isSkipped ? 'params-container is-skipped' : 'params-container';

  const cardHtml = `
    <div class="dimension-card">
      <div class="dim-header">
        <span class="dim-name">${escHtml(dim.name)}</span>
        <span class="weight-badge">${weightPct}%</span>
      </div>
      <div class="scale-legend">1 = Sem problema &nbsp;•&nbsp; 3 = Moderada &nbsp;•&nbsp; 5 = Crítica</div>

      <label class="skip-dim-toggle">
        <span class="toggle-track">
          <input
            type="checkbox"
            id="skip-dim-cb"
            ${isSkipped ? 'checked' : ''}
          >
          <span class="toggle-slider"></span>
        </span>
        Pular esta dimensão inteira
      </label>

      <div class="${containerClass}" id="params-container">
        ${paramsHtml}
      </div>
    </div>`;

  $('step-container').innerHTML = cardHtml;

  // Attach score button listeners
  $('step-container').querySelectorAll('.score-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const dimId   = btn.dataset.dim;
      const paramId = btn.dataset.param;
      const val     = btn.dataset.val === 'skip' ? 'skip' : parseInt(btn.dataset.val, 10);
      selectScore(dimId, paramId, val);
    });
  });

  // Attach skip-dimension listener
  const skipDimCb = $('skip-dim-cb');
  if (skipDimCb) {
    skipDimCb.addEventListener('change', () => {
      toggleSkipDim(dim.id, skipDimCb.checked);
    });
  }
}

// -----------------------------------------------------------------------
// selectScore
// -----------------------------------------------------------------------
function selectScore(dimId, paramId, value) {
  if (!state.scores[dimId]) state.scores[dimId] = {};
  state.scores[dimId][paramId] = value;

  // Update button active states for this param
  const container = $('step-container');
  if (!container) return;

  container.querySelectorAll(`.score-btn[data-dim="${dimId}"][data-param="${paramId}"]`)
    .forEach((btn) => {
      const btnVal = btn.dataset.val === 'skip' ? 'skip' : parseInt(btn.dataset.val, 10);
      btn.classList.toggle('active', btnVal === value);
    });
}

// -----------------------------------------------------------------------
// toggleSkipDim
// -----------------------------------------------------------------------
function toggleSkipDim(dimId, checked) {
  if (checked) {
    state.skipped.add(dimId);
  } else {
    state.skipped.delete(dimId);
  }

  const container = $('params-container');
  if (container) {
    container.classList.toggle('is-skipped', checked);
  }
}

// -----------------------------------------------------------------------
// nextStep
// -----------------------------------------------------------------------
function nextStep() {
  const total = window.DIMENSIONS.length;

  if (state.currentDimIndex < total - 1) {
    renderDimension(state.currentDimIndex + 1);
  } else {
    submitEvaluation();
  }
}

// -----------------------------------------------------------------------
// prevStep
// -----------------------------------------------------------------------
function prevStep() {
  if (state.currentDimIndex > 0) {
    renderDimension(state.currentDimIndex - 1);
  } else {
    // Back to intro
    $('eval-section').hidden  = true;
    $('intro-section').hidden = false;
  }
}

// -----------------------------------------------------------------------
// submitEvaluation
// -----------------------------------------------------------------------
async function submitEvaluation() {
  const btnNext = $('btn-next');
  const origText = btnNext.textContent;
  btnNext.textContent = 'Calculando…';
  btnNext.disabled = true;

  // Build clean scores payload (only numeric scores, omit nulls and 'skip')
  const cleanScores = {};
  for (const [dimId, params] of Object.entries(state.scores)) {
    cleanScores[dimId] = {};
    for (const [paramId, score] of Object.entries(params)) {
      if (typeof score === 'number') {
        cleanScores[dimId][paramId] = score;
      }
      // null or 'skip' → omit (treated as unanswered)
    }
  }

  const payload = {
    product_name: state.productName,
    scores: cleanScores,
    skipped_dimensions: Array.from(state.skipped),
  };

  try {
    const res = await fetch('/api/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const data = await res.json();

    if (!res.ok) {
      alert(`Erro: ${data.error || 'Não foi possível calcular o CF.'}`);
      return;
    }

    state.results = data;
    renderResults(data);
  } catch (err) {
    alert('Não foi possível conectar ao servidor. Verifique se o app está em execução.');
  } finally {
    btnNext.textContent = origText;
    btnNext.disabled = false;
  }
}

// -----------------------------------------------------------------------
// renderResults
// -----------------------------------------------------------------------
function renderResults(data) {
  $('eval-section').hidden    = true;
  $('results-section').hidden = false;

  const cf             = data.cf;
  const color          = cfColor(cf);
  const label          = cfLabel(cf);
  const cfPct          = Math.min(cf * 100, 100).toFixed(0);

  const breakdownRows = data.dimensions.map((dr) => {
    if (dr.skipped) {
      return `
        <tr>
          <td>${escHtml(dr.dimension_name)}</td>
          <td class="num"><span class="skip-pill">SKIP</span></td>
          <td class="num">${Math.round(dr.weight * 100)}%</td>
          <td class="num">—</td>
        </tr>`;
    }
    const normScore  = dr.score_normalized;
    const scoreColor = cfColor(normScore);
    const answered   = Object.keys(dr.scores || {}).length;
    return `
      <tr>
        <td>${escHtml(dr.dimension_name)}</td>
        <td class="num">
          <span class="score-pill" style="background:${scoreColor}">
            ${normScore.toFixed(2)}
          </span>
        </td>
        <td class="num">${Math.round(dr.weight * 100)}%</td>
        <td class="num">${answered}</td>
      </tr>`;
  }).join('');

  const html = `
    <div class="result-header">
      <div class="result-product-name">${escHtml(data.product_name)}</div>
      <div class="result-date">${fmtDate(data.evaluated_at)}</div>
    </div>

    <div class="cf-display">
      <div class="cf-number" style="color:${color}">${cf.toFixed(2)}</div>
      <div class="cf-classification">${escHtml(label)}</div>
      <div class="cf-bar-track">
        <div class="cf-bar-fill" style="width:${cfPct}%;background:${color}"></div>
      </div>
    </div>

    <div class="breakdown-card">
      <div class="breakdown-title">Breakdown por Dimensão</div>
      <table class="breakdown-table">
        <thead>
          <tr>
            <th>Dimensão</th>
            <th class="num">Score</th>
            <th class="num">Peso</th>
            <th class="num">Parâmetros avaliados</th>
          </tr>
        </thead>
        <tbody>
          ${breakdownRows}
        </tbody>
      </table>
    </div>

    <div class="export-buttons">
      <button class="btn-primary" onclick="exportResult('json')">⬇ Baixar JSON</button>
      <button class="btn-secondary" onclick="exportResult('txt')">⬇ Baixar Relatório TXT</button>
    </div>

    <div class="restart-wrap">
      <button class="restart-btn" onclick="restartEvaluation()">↩ Nova Avaliação</button>
    </div>
  `;

  $('results-content').innerHTML = html;

  // Scroll to top
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// -----------------------------------------------------------------------
// exportResult
// -----------------------------------------------------------------------
async function exportResult(format) {
  if (!state.results) return;

  const endpoint = format === 'json' ? '/api/export/json' : '/api/export/txt';

  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(state.results),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      alert(`Erro ao exportar: ${err.error || res.statusText}`);
      return;
    }

    // Determine filename from Content-Disposition header or fallback
    let filename = format === 'json' ? 'dfc_resultado.json' : 'dfc_resultado.txt';
    const cd = res.headers.get('Content-Disposition');
    if (cd) {
      const match = cd.match(/filename="?([^";\n]+)"?/i);
      if (match) filename = match[1];
    }

    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 200);
  } catch (err) {
    alert('Não foi possível conectar ao servidor para exportar.');
  }
}

// -----------------------------------------------------------------------
// restartEvaluation
// -----------------------------------------------------------------------
function restartEvaluation() {
  state.currentDimIndex = -1;
  state.productName     = '';
  state.scores          = {};
  state.skipped         = new Set();
  state.results         = null;

  $('results-section').hidden = true;
  $('eval-section').hidden    = true;
  $('intro-section').hidden   = false;

  const productInp = $('product-name');
  productInp.value = '';
  productInp.focus();

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// -----------------------------------------------------------------------
// Bootstrap
// -----------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', init);
