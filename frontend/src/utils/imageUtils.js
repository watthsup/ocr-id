/**
 * Client-side image utility functions for ID card processing.
 */

/**
 * Rotates an image File by a specified angle in degrees (+90 for clockwise, -90 for counter-clockwise).
 * Uses HTML5 Canvas to perform fast, lossless/high-quality client-side transformation.
 *
 * @param {File} file - Original Image File
 * @param {number} angleDegrees - Rotation angle (+90, -90, 180, 270)
 * @returns {Promise<File>} - Rotated Image File ready for submission
 */
export async function rotateImageFile(file, angleDegrees = 90) {
  return new Promise((resolve, reject) => {
    if (!file) {
      reject(new Error('No file provided for rotation'));
      return;
    }

    const img = new Image();
    const objectUrl = URL.createObjectURL(file);

    img.onload = () => {
      URL.revokeObjectURL(objectUrl);

      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        reject(new Error('Failed to get 2D canvas context'));
        return;
      }

      // Calculate radians and swap dimensions if 90 or 270 degrees
      const rad = (angleDegrees * Math.PI) / 180;
      const normalizedAngle = ((angleDegrees % 360) + 360) % 360;
      const isOrthogonal = normalizedAngle === 90 || normalizedAngle === 270;

      canvas.width = isOrthogonal ? img.height : img.width;
      canvas.height = isOrthogonal ? img.width : img.height;

      // Center and rotate
      ctx.translate(canvas.width / 2, canvas.height / 2);
      ctx.rotate(rad);
      ctx.drawImage(img, -img.width / 2, -img.height / 2);

      const mimeType = file.type && file.type.startsWith('image/') ? file.type : 'image/jpeg';
      const quality = mimeType === 'image/png' ? undefined : 0.95;

      canvas.toBlob(
        (blob) => {
          if (!blob) {
            reject(new Error('Failed to create Blob from rotated canvas'));
            return;
          }
          const rotatedFile = new File([blob], file.name || 'rotated_id_card.jpg', {
            type: mimeType,
            lastModified: Date.now(),
          });
          resolve(rotatedFile);
        },
        mimeType,
        quality
      );
    };

    img.onerror = (err) => {
      URL.revokeObjectURL(objectUrl);
      reject(err);
    };

    img.src = objectUrl;
  });
}
