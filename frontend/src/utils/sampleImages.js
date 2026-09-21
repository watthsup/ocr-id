/**
 * Utility to generate realistic mock canvas images for testing OCR
 */

export function generateSampleFrontCard() {
  const canvas = document.createElement('canvas');
  canvas.width = 1000;
  canvas.height = 630;
  const ctx = canvas.getContext('2d');

  // Card Background: light blue / silver gradient
  const bgGrad = ctx.createLinearGradient(0, 0, 1000, 630);
  bgGrad.addColorStop(0, '#EAF4FC');
  bgGrad.addColorStop(0.5, '#F5F9FD');
  bgGrad.addColorStop(1, '#DDEEFA');
  ctx.fillStyle = bgGrad;
  ctx.fillRect(0, 0, 1000, 630);

  // Border
  ctx.strokeStyle = '#B5D3ED';
  ctx.lineWidth = 4;
  ctx.strokeRect(10, 10, 980, 610);

  // Top Thai Header
  ctx.fillStyle = '#114B80';
  ctx.font = 'bold 26px sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('บัตรประจำตัวประชาชน Thai National ID Card', 500, 50);

  // Identification Number (Valid Checksum: 1100701234567)
  ctx.fillStyle = '#0B3357';
  ctx.font = 'bold 36px monospace';
  ctx.textAlign = 'left';
  ctx.fillText('เลขประจำตัวประชาชน 1 1007 01234 56 7', 80, 110);

  // Thai Name
  ctx.fillStyle = '#1A1D20';
  ctx.font = '24px sans-serif';
  ctx.fillText('ชื่อตัวและชื่อสกุล นาย สมชาย ใจดี', 260, 180);

  // English Name
  ctx.font = '22px sans-serif';
  ctx.fillText('Name Mr. Somchai Jaidee', 260, 220);

  // Date of Birth
  ctx.font = '20px sans-serif';
  ctx.fillText('เกิดวันที่ 15 ม.ค. 2533', 260, 270);
  ctx.fillText('Date of Birth 15 Jan. 1990', 260, 305);

  // Religion
  ctx.fillText('ศาสนา พุทธ', 260, 350);

  // Address
  ctx.font = '19px sans-serif';
  ctx.fillText('ที่อยู่ 99/1 หมู่ที่ 2 ต.บางตลาด', 260, 395);
  ctx.fillText('อ.ปากเกร็ด จ.นนทบุรี 11120', 260, 430);

  // Date of Issue & Expiry
  ctx.font = '18px sans-serif';
  ctx.fillText('วันออกบัตร 20 ก.พ. 2564', 80, 530);
  ctx.fillText('Date of Issue 20 Feb. 2021', 80, 560);

  ctx.fillText('วันบัตรหมดอายุ 14 ม.ค. 2572', 600, 530);
  ctx.fillText('Date of Expiry 14 Jan. 2029', 600, 560);

  // Simulated Photo Box
  ctx.fillStyle = '#CBD5E1';
  ctx.fillRect(720, 150, 220, 280);
  ctx.strokeStyle = '#94A3B8';
  ctx.strokeRect(720, 150, 220, 280);
  ctx.fillStyle = '#475569';
  ctx.font = 'bold 20px sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('PHOTO', 830, 300);

  // Simulated Chip Box
  ctx.fillStyle = '#F59E0B';
  ctx.fillRect(80, 150, 120, 90);
  ctx.strokeStyle = '#D97706';
  ctx.strokeRect(80, 150, 120, 90);

  return new Promise((resolve) => {
    canvas.toBlob((blob) => {
      resolve(new File([blob], 'sample_thai_id_front.jpg', { type: 'image/jpeg' }));
    }, 'image/jpeg', 0.95);
  });
}

export function generateSampleLaserCard() {
  const canvas = document.createElement('canvas');
  canvas.width = 900;
  canvas.height = 500;
  const ctx = canvas.getContext('2d');

  // Back of card background: soft cream / warm gray
  ctx.fillStyle = '#F4F4F6';
  ctx.fillRect(0, 0, 900, 500);

  // Magnetic strip
  ctx.fillStyle = '#262626';
  ctx.fillRect(0, 60, 900, 90);

  // Barcode / text section
  ctx.fillStyle = '#333333';
  ctx.font = '16px sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('BOPA / Department of Provincial Administration Thailand', 450, 210);

  // Laser ID Box in lower left or center
  ctx.strokeStyle = '#CBD5E1';
  ctx.lineWidth = 2;
  ctx.strokeRect(180, 280, 540, 120);

  ctx.fillStyle = '#1A1D20';
  ctx.font = 'bold 42px monospace';
  ctx.letterSpacing = '6px';
  ctx.fillText('JT0-1234567-89', 450, 355);

  ctx.font = '14px sans-serif';
  ctx.fillStyle = '#64748B';
  ctx.fillText('(Laser ID Code - 12 Characters Alphanumeric)', 450, 430);

  return new Promise((resolve) => {
    canvas.toBlob((blob) => {
      resolve(new File([blob], 'sample_laser_id_back.jpg', { type: 'image/jpeg' }));
    }, 'image/jpeg', 0.95);
  });
}
