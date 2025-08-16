# Deploy Guide (No local run needed)

## วิธี 1: Render.com (ง่ายสุด)
1) สร้าง Git repo แล้วอัปโหลดโฟลเดอร์นี้ทั้งชุด (มี `Dockerfile`)
2) ที่ Render → New → Blueprint → เลือก `render.yaml`
3) ตั้งค่าตัวแปร (Environment Variables) ได้ทันทีในหน้าบริการ:
   - `AFF_ENABLED` = true/false
   - `AFF_ENDPOINT` = https://open-api.affiliate.shopee.co.th/graphql (ถ้ามี)
   - `AFF_APP_ID` / `AFF_SECRET` (ถ้ามี)
4) Deploy แล้วเปิด URL ที่ได้ (Static frontend + API พร้อมใช้งาน)

## วิธี 2: Railway
อ่านไฟล์ `RAILWAY_DEPLOY.md` (เพิ่ม variables แล้ว Deploy ได้เลย)

## วิธี 3: Fly.io
ติดตั้ง Fly CLI → `fly launch` (ใช้ไฟล์ `fly.toml`) → `fly deploy`

## วิธี 4: Cloud Run (GCP) / App Runner (AWS) / Azure App Service
ใช้ Dockerfile เดิม `gcloud run deploy` หรือบริการที่รองรับ Docker ได้ทันที

### การตั้งค่าสำคัญ
- ถ้าไม่มี API: ปล่อย `AFF_ENABLED=false` แล้วเติมค่าคอมมิชชั่นด้วย CSV ในหน้าเว็บ (เมนู Commission)
- ถ้ามี API: ตั้งค่า `AFF_ENABLED=true` + `AFF_ENDPOINT` + `APP_ID/SECRET` เป็น env var
- ปรับ keyword/หมวดที่ `backend/categories.json` ก่อน push (หรือเปลี่ยนผ่านฝั่ง client โดยพิมพ์ในช่องค้นหา)

> แนะนำเปิด Cloud logs เพื่อดูอัตราการเรียกใช้งานและเผื่อปรับ rate/หน่วงเวลา หากเจอ rate limit
