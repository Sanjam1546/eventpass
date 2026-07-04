function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

let lastScanned = null;
let lastScanTime = 0;
let isProcessing = false;

function showResult(cls, html) {
  const el = document.getElementById('scan-result');
  el.className = cls;
  el.innerHTML = html;
}

async function onScanSuccess(decodedText) {
  const now = Date.now();
  // Debounce: ignore identical scans within 4 seconds so one QR isn't sent repeatedly
  if (isProcessing || (decodedText === lastScanned && now - lastScanTime < 4000)) return;
  lastScanned = decodedText;
  lastScanTime = now;
  isProcessing = true;

  showResult('idle', 'Checking pass...');

  try {
    const response = await fetch(SCAN_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: JSON.stringify({ pass_code: decodedText }),
    });
    const data = await response.json();

    const details = data.event_title
      ? `<div style="font-size:13px;font-weight:400;color:var(--text-dim);margin-top:6px;">
           ${data.holder_name} &middot; ${data.event_title} &middot; ${data.date} ${data.time}
         </div>`
      : '';
    const vipTag = data.is_vip
      ? `<div style="display:inline-block;margin-top:8px;padding:4px 12px;border-radius:999px;font-size:12px;font-weight:700;background:linear-gradient(135deg,#f4d675,#c9971f);color:#241a00;">✨ VIP GUEST</div>`
      : '';

    if (data.ok) {
      showResult('allowed', `✅ ${data.message}${details}${vipTag}`);
      if (navigator.vibrate) navigator.vibrate(data.is_vip ? [80, 60, 80] : 120);
    } else {
      showResult('denied', `⛔ ${data.message}${details}${vipTag}`);
    }
  } catch (err) {
    showResult('denied', '⚠️ Network error while verifying pass. Try again.');
  } finally {
    setTimeout(() => { isProcessing = false; }, 800);
  }
}

function onScanFailure() {
  // Called continuously while no QR is in frame — intentionally silent.
}

document.addEventListener('DOMContentLoaded', () => {
  const html5QrCode = new Html5Qrcode("qr-reader");
  const config = { fps: 10, qrbox: 250 };

  Html5Qrcode.getCameras().then(cameras => {
    if (cameras && cameras.length) {
      const cameraId = cameras[cameras.length - 1].id; // prefer back camera on mobile
      html5QrCode.start(cameraId, config, onScanSuccess, onScanFailure)
        .catch(() => {
          html5QrCode.start({ facingMode: "environment" }, config, onScanSuccess, onScanFailure);
        });
    } else {
      showResult('denied', 'No camera found on this device.');
    }
  }).catch(() => {
    showResult('denied', 'Camera permission denied. Please allow camera access.');
  });
});
