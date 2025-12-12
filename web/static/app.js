async function submitPredict(e){
  e.preventDefault();

  const L = parseFloat(document.getElementById('length_m').value);
  const W = parseFloat(document.getElementById('width_m').value);
  const H = parseFloat(document.getElementById('height_m').value);
  const deltaT = parseFloat(document.getElementById('deltaT_C').value);
  const totalCFM = parseFloat(document.getElementById('supply_total_cfm').value);
  const students = parseInt(document.getElementById('students').value,10);
  const teachers = parseInt(document.getElementById('teachers').value,10);
  const diffuserCount = parseInt(document.getElementById('diffuser_count').value,10);
  const modelId = document.getElementById('model_id').value;
  const gridSpacing = parseFloat(document.getElementById('grid_spacing_m').value);
  const useManual = document.getElementById('use_manual')?.checked === true;

  // helper to parse optional JSON textareas
  const parseJSONField = (elId, fallback) => {
    const el = document.getElementById(elId);
    if (!el) return fallback;
    const raw = (el.value || '').trim();
    if (!raw) return fallback;
    try { return JSON.parse(raw); }
    catch (e) { throw new Error(`${elId} contains invalid JSON`); }
  };

  let diffuserLocs = null;
  if (useManual) {
    diffuserLocs = parseJSONField('diffuser_coords', null);
    if (!Array.isArray(diffuserLocs) || diffuserLocs.length === 0) {
      alert('Provide diffuser coordinates JSON or uncheck "Use my diffuser coordinates".');
      return;
    }
    if (diffuserCount && diffuserLocs.length !== diffuserCount) {
      const ok = confirm(`You set count=${diffuserCount} but provided ${diffuserLocs.length} coordinates. Continue anyway?`);
      if (!ok) return;
    }
  }

  // let returnLocs = parseJSONField('return_coords', [{ x: L/2, y: W/2 }]);
  // if (!Array.isArray(returnLocs) || returnLocs.length === 0) {
  //   returnLocs = [{ x: L/2, y: W/2 }];
  // }

  let returnLocs = [{ x: L/2, y: W/2 }];
  const rawR = (document.getElementById('return_coords')?.value || '').trim();
  if (rawR) {
    try { returnLocs = JSON.parse(rawR); }
    catch { alert('Bad return coordinates JSON'); return; }
  }


  const payload = {
    room: { length_m: L, width_m: W, height_m: H, shape: 'rect', window_wall: 'north' },
    people: { students, teachers, seated_fraction: 0.9 },
    loads: { deltaT_C: deltaT, mode: deltaT >= 0 ? 'heating' : 'cooling' },
    standard: { type: 'ASHRAE_62_1', edition: '2022', eca_target_cfm: null },
    ventilation: { supply_total_cfm: totalCFM, infiltration_cfm: 0 },
    diffusers: {
      selection: [{
        type: 'ceiling_4way',
        model_id: modelId,
        count: diffuserCount,
        neck_size_in: 8,
        ...(useManual ? { existing_locations: diffuserLocs } : {}) // send coordinates only when manual is enabled
      }],
      constraints: { min_from_walls_m: 1.2, min_from_board_m: 1.2, face_velocity_fpm_max: 700 }
    },
    returns: { locations: returnLocs },
    solver: { optimize_layout: !useManual, grid_spacing_m: gridSpacing, time_budget_ms: 2000 }
  };

  try {
    const res = await fetch('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(`Predict failed: ${res.status} ${txt}`);
    }
    const data = await res.json();
    renderResults(data);
  } catch (err) {
    console.error(err);
    alert(err.message || 'Predict failed');
  }
}

function renderResults(data){
  document.getElementById('results').hidden = false;

  const k = document.getElementById('kpis');
  k.innerHTML = '';
  const items = [
    ['ADPI', (data.adpi * 100).toFixed(1) + '%'],
    ['Draft area', data.draft_risk_area_pct.toFixed(1) + '%'],
    ['v95', data.velocity_stats.v95_mps.toFixed(3) + ' m/s'],
    ['62.1 pass', String(data.compliance.pass)]
  ];
  for (const [label, value] of items) {
    const div = document.createElement('div');
    div.className = 'kpi';
    div.innerHTML = `<div class="muted" style="font-size:12px">${label}</div><div style="font-size:20px;font-weight:700">${value}</div>`;
    k.appendChild(div);
  }

  // Images + downloads + raw JSON
  const heat = (data.artifacts?.heatmap_png_url || '/artifacts/adpi_map.png') + '?t=' + Date.now();
  const edt  = (data.artifacts?.edt_hist_png_url || '/artifacts/edt_hist.png') + '?t=' + Date.now();
  document.getElementById('img-vel').src = heat;
  document.getElementById('img-edt').src = edt;
  document.getElementById('csv-link').href = data.artifacts?.coordinates_csv_url || '/artifacts/layout.csv';
  document.getElementById('raw').textContent = JSON.stringify(data, null, 2);
}

document.getElementById('predict-form').addEventListener('submit', submitPredict);
