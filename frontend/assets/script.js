async function api(path, opts){
  const res = await fetch(path, opts)
  if(!res.ok) throw new Error(await res.text())
  return await res.json()
}

function fmt(n){ if(n==null) return '-'; return n.toLocaleString('th-TH') }
function fmtPrice(n){ if(n==null) return '-'; return n.toLocaleString('th-TH', {style:'currency', currency:'THB'}) }

function renderTable(items){
  const cols = ["image","name","price","historical_sold","rating_star","commission_rate","score","url"]
  const thead = `<thead><tr>
    <th>รูป</th><th>สินค้า</th><th>ราคา</th><th>ยอดขายสะสม</th><th>เรตติ้ง</th><th>คอมฯ (%)</th><th>คะแนน</th><th>ลิงก์</th>
  </tr></thead>`
  const rows = (items||[]).map(it=>{
    const link = it.url ? `<a href="${it.url}" target="_blank" rel="noopener">เปิด</a>` : '-'
    const img = it.image ? `<img class="thumb" src="${it.image}" alt="">` : ''
    return `<tr>
      <td>${img}</td>
      <td>${it.name||'-'}</td>
      <td>${fmtPrice(it.price)}</td>
      <td>${fmt(it.historical_sold)}</td>
      <td>${it.rating_star?.toFixed?.(2) || it.rating_star || '-'}</td>
      <td>${it.commission_rate!=null ? it.commission_rate.toFixed(2) : '-'}</td>
      <td>${it.score!=null ? fmt(it.score) : '-'}</td>
      <td class="links">${link}</td>
    </tr>`
  }).join('')
  return `<table>${thead}<tbody>${rows}</tbody></table>`
}

document.getElementById('btnSearch').addEventListener('click', async()=>{
  const kw = document.getElementById('kw').value.trim()
  const limit = +document.getElementById('limit').value
  const min_rating = +document.getElementById('min_rating').value
  const min_sold = +document.getElementById('min_sold').value
  const sort = document.getElementById('sort').value
  const status = document.getElementById('searchStatus')
  const table = document.getElementById('searchTable')

  table.innerHTML = ''; status.textContent = 'กำลังดึงข้อมูล...'
  try{
    const res = await api('/api/search', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({keyword:kw,limit,min_rating,min_sold,sort})
    })
    status.textContent = `พบ ${res.count} รายการ`
    table.innerHTML = renderTable(res.items)
  }catch(e){
    status.textContent = 'ดึงข้อมูลล้มเหลว: ' + e.message
  }
})

document.getElementById('btnPerCat').addEventListener('click', async()=>{
  const perCat = +document.getElementById('perCat').value
  const min_rating = +document.getElementById('cat_min_rating').value
  const min_sold = +document.getElementById('cat_min_sold').value
  const use_score = document.getElementById('use_score').checked
  const status = document.getElementById('catStatus')
  const out = document.getElementById('catResults')

  out.innerHTML=''; status.textContent='กำลังดึงต่อหมวด...'
  try{
    const res = await api(`/api/top-by-category?limit_per_cat=${perCat}&min_rating=${min_rating}&min_sold=${min_sold}&use_score=${use_score}`, {method:'POST'})
    status.textContent = ''
    out.innerHTML = (res.categories||[]).map(c=>{
      const top = c.top
      const items = c.items||[]
      return `<div class="cat-card">
        <h3>${c.category.label} <span class="badge">${items.length} รายการ</span></h3>
        ${top ? `<p><b>อันดับ 1:</b> ${top.name} — ยอดขาย ${fmt(top.historical_sold)} — คอมฯ ${top.commission_rate!=null? top.commission_rate.toFixed(2)+'%' : '-'} — <a href="${top.url}" target="_blank" rel="noopener">เปิดลิงก์</a></p>` : '<p>ไม่พบสินค้า</p>'}
        <details><summary>ดูทั้งหมด</summary>${renderTable(items)}</details>
      </div>`
    }).join('')
  }catch(e){
    status.textContent = 'ล้มเหลว: ' + e.message
  }
})

document.getElementById('btnUpload').addEventListener('click', async()=>{
  const f = document.getElementById('csvFile').files[0]
  const status = document.getElementById('csvStatus')
  if(!f){ status.textContent='เลือกไฟล์ CSV ก่อน'; return }
  const fd = new FormData(); fd.append('file', f)
  status.textContent='กำลังอัปโหลด...'
  try{
    const res = await api('/api/commission/upload', {method:'POST', body: fd})
    status.textContent = `อัปโหลดสำเร็จ: ${res.ingested} แถว`
  }catch(e){
    status.textContent = 'อัปโหลดล้มเหลว: ' + e.message
  }
})

async function loadConfig(){
  try{
    const cfg = await api('/api/config')
    document.getElementById('endpoint').value = cfg?.affiliate?.endpoint || ''
    document.getElementById('app_id').value = cfg?.affiliate?.app_id || ''
    document.getElementById('secret').value = cfg?.affiliate?.secret || ''
    document.getElementById('enabled').checked = !!cfg?.affiliate?.enabled
  }catch(e){}
}
document.getElementById('btnSaveCfg').addEventListener('click', async()=>{
  const endpoint = document.getElementById('endpoint').value.trim()
  const app_id = document.getElementById('app_id').value.trim()
  const secret = document.getElementById('secret').value.trim()
  const enabled = document.getElementById('enabled').checked
  const model = { affiliate: { endpoint, app_id, secret, enabled }}
  const status = document.getElementById('cfgStatus')
  status.textContent='กำลังบันทึก...'
  try{
    await api('/api/config', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(model)})
    status.textContent='บันทึกแล้ว ✓'
  }catch(e){
    status.textContent='บันทึกล้มเหลว: ' + e.message
  }
})
loadConfig()
