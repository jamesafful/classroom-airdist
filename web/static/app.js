// web/static/app.js
async function submitPredict(e){
  e.preventDefault();

  const useManual = document.getElementById('use_manual').checked;

  let existing_locations = null;
  try {
    existing_locations = JSON.parse(document.getElementById('diffuser_coords').value || "[]");
  } catch(e){ existing_locations = []; }

  let return_locations = null;
  try {
    return_locations = JSON.parse(document.getElementById('return_coords').value || "[]");
  } catch(e){ return_locations = []; }

  const v95TargetField = document.getElementById('v95_target').value.trim();
  const v95Target = v95TargetField === "" ? null : parseFloat(v95TargetField);

  const payload = {
    room: {
      length_m: parseFloat(document.getElementById('length_m').value),
      width_m: parseFloat(document.getElementById('width_m').value),
      height_m: parseFloat(document.getElementById('height_m').value),
      shape: 'rect',
      window_wall: 'north'
    },
    people: {
      students: parseInt(document.getElementById('students').value,10),
      teachers: parseInt(document.getElementById('teachers').value,10),
      seated_fraction: 0.9
    },
    loads: { deltaT_C: parseFloat(document.getElementById('deltaT_C').value), mode: 'cooling' },
    standard: { type: 'ASHRAE_62_1', edition: '2022', eca_target_cfm: null },
    ventilation: { supply_total_cfm: parseFloat(document.getElementById('supply_total_cfm').value), infiltration_cfm: 0 },
    diffusers: {
      selection: [{
        type: 'ceiling_4way',
        model_id: document.getElementById('model_id').value,
        count: parseInt(document.getElementById('diffuser_count').value,10),
        neck_size_in: 8,
        existing_locations: useManual ? existing_locations : null
      }],
      constraints: { min_from_walls_m: 1.2, min_from_board_m: 1.2, face_velocity_fpm_max: 700 }
    },
    returns: { locations: return_locations && return_locations.length ? return_locations : [{x: (parseFloat(document.getElementById('length_m').value)/2), y: (parseFloat(document.getElementById('width_m').value)/2)}] },
    comfort: {
      edt_min_C: parseFloat(document.getElementById('edt_min').value),
      edt_max_C: parseFloat(document.getElementById('edt_max').value),
      v_cap_mps: parseFloat(document.getElementById('v_cap').value),
      v95_target_mps: v95Target,
      v95_blend: parseFloat(document.getElementById('v95_blend').value)
    },
    solver: { optimize_layout: !useManual, grid_spacing_m: parseFloat(document.getElementById('grid_spacing_m').value), time_budget_ms: 2000 }
  };

  const res = await fetch('/predict', {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
  });
  if(!res.ok){
    const msg = await res.text().catch(()=>res.statusText);
    alert('Predict failed: ' + res.status + ' ' + msg);
    return;
  }
  const data = await res.json();
  renderResults(data);
}

function pct(n){ return (n).toFixed(1) + '%'; }

function renderResults(data){
  document.getElementById('results').hidden = false;

  const k = document.getElementById('kpis');
  k.innerHTML = '';
  const items = [
    ['ADPI', (data.adpi*100).toFixed(1) + '%'],
    ['Draft area', data.draft_risk_area_pct.toFixed(1) + '%'],
    ['v95', data.velocity_stats.v95_mps.toFixed(3) + ' m/s'],
    ['62.1 pass', String(data.compliance.pass)]
  ];
  for(const [label,value] of items){
    const div = document.createElement('div'); div.className='kpi';
    div.innerHTML = `<div style="color:#a9b3c7;font-size:12px">${label}</div><div style="font-size:20px;font-weight:700">${value}</div>`;
    k.appendChild(div);
  }

  document.getElementById('img-vel').src = data.artifacts.heatmap_png_url + '?t=' + Date.now();
  document.getElementById('img-edt').src = data.artifacts.edt_hist_png_url + '?t=' + Date.now();
  document.getElementById('csv-link').href = data.artifacts.coordinates_csv_url;
  document.getElementById('raw').textContent = JSON.stringify(data, null, 2);
}

document.getElementById('predict-form').addEventListener('submit', submitPredict);

