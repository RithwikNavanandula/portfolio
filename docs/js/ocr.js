/**
 * OCR Module - Maximum Accuracy Version
 * Features: Dual engine, advanced preprocessing, noise reduction, adaptive contrast
 */
const OCR = {
    API_KEY: 'K85403682988957',
    API_URL: 'https://api.ocr.space/parse/image',

    async process(file, onProgress) {
        onProgress && onProgress('Enhancing image...');

        // Advanced image preprocessing
        const enhanced = await this.enhanceImage(file);

        onProgress && onProgress('Running dual-engine OCR...');

        // Try both engines and pick best result
        const [result1, result2] = await Promise.all([
            this.callOCR(enhanced, 1),
            this.callOCR(enhanced, 2)
        ]);

        console.log('Engine 1 result:', result1?.length || 0, 'chars');
        console.log('Engine 2 result:', result2?.length || 0, 'chars');

        // Pick the result with more useful content
        const score1 = this.scoreResult(result1);
        const score2 = this.scoreResult(result2);

        console.log('Engine 1 score:', score1);
        console.log('Engine 2 score:', score2);

        const bestResult = score1 >= score2 ? result1 : result2;
        const engine = score1 >= score2 ? 1 : 2;

        onProgress && onProgress(`Done! (Engine ${engine} selected)`);

        return bestResult || '';
    },

    /**
     * Score OCR result based on useful content for labels
     */
    scoreResult(text) {
        if (!text) return 0;
        let score = 0;

        // Count dates found (most important)
        const dates = (text.match(/\d{1,2}[\/.-]\d{1,2}[\/.-]\d{2,4}/g) || []).length;
        score += dates * 15;

        // Count batch-like patterns
        const batches = (text.match(/\d{2}-\d{4}-\d{4}/g) || []).length;
        score += batches * 20;

        // Count keywords
        const keywords = ['BATCH', 'MFG', 'EXP', 'DATE', 'MANUFACTURE', 'EXPIRY', 'BEST BEFORE', 'USE BY'];
        keywords.forEach(kw => {
            if (text.toUpperCase().includes(kw)) score += 5;
        });

        // Penalize very short results
        if (text.length < 30) score -= 30;
        if (text.length < 50) score -= 10;

        // Bonus for reasonable length
        score += Math.min(text.length / 8, 25);

        return score;
    },

    async callOCR(imageBlob, engine) {
        const formData = new FormData();
        formData.append('apikey', this.API_KEY);
        formData.append('file', imageBlob, 'image.png');
        formData.append('language', 'eng');
        formData.append('OCREngine', engine.toString());
        formData.append('scale', 'true');
        formData.append('isTable', 'false');
        formData.append('detectOrientation', 'true');

        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 35000);

        try {
            const response = await fetch(this.API_URL, {
                method: 'POST',
                body: formData,
                signal: controller.signal
            });

            clearTimeout(timeout);

            if (!response.ok) return null;

            const data = await response.json();

            if (data.IsErroredOnProcessing) {
                console.log(`Engine ${engine} error:`, data.ErrorMessage);
                return null;
            }

            return data.ParsedResults?.[0]?.ParsedText || '';
        } catch (err) {
            clearTimeout(timeout);
            console.log(`Engine ${engine} failed:`, err.message);
            return null;
        }
    },

    /**
     * Advanced image preprocessing for maximum accuracy
     */
    async enhanceImage(file) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            const url = URL.createObjectURL(file);

            img.onload = () => {
                URL.revokeObjectURL(url);

                // Higher resolution for better accuracy (1800px)
                const maxWidth = 1800;
                let w = img.width;
                let h = img.height;

                if (w > maxWidth) {
                    h = (h * maxWidth) / w;
                    w = maxWidth;
                }

                const canvas = document.createElement('canvas');
                canvas.width = w;
                canvas.height = h;
                const ctx = canvas.getContext('2d');

                // Draw original
                ctx.drawImage(img, 0, 0, w, h);

                // Apply preprocessing pipeline
                this.applyGrayscale(ctx, w, h);
                this.applyNoiseReduction(ctx, w, h);
                this.applyAdaptiveContrast(ctx, w, h);
                this.applySharpen(ctx, w, h);

                // Output as PNG for lossless quality
                canvas.toBlob(
                    blob => blob ? resolve(blob) : reject(new Error('Processing failed')),
                    'image/png',
                    1.0
                );
            };

            img.onerror = () => {
                URL.revokeObjectURL(url);
                reject(new Error('Failed to load image'));
            };

            img.src = url;
        });
    },

    /**
     * Convert to grayscale - removes color noise
     */
    applyGrayscale(ctx, w, h) {
        const imageData = ctx.getImageData(0, 0, w, h);
        const data = imageData.data;

        for (let i = 0; i < data.length; i += 4) {
            // Use luminosity method for better contrast
            const gray = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
            data[i] = gray;
            data[i + 1] = gray;
            data[i + 2] = gray;
        }

        ctx.putImageData(imageData, 0, 0);
    },

    /**
     * Noise reduction using median-like filter
     */
    applyNoiseReduction(ctx, w, h) {
        const imageData = ctx.getImageData(0, 0, w, h);
        const data = imageData.data;
        const copy = new Uint8ClampedArray(data);

        // Simple box blur for noise reduction (3x3)
        for (let y = 1; y < h - 1; y++) {
            for (let x = 1; x < w - 1; x++) {
                for (let c = 0; c < 3; c++) {
                    let sum = 0;
                    for (let ky = -1; ky <= 1; ky++) {
                        for (let kx = -1; kx <= 1; kx++) {
                            const idx = ((y + ky) * w + (x + kx)) * 4 + c;
                            sum += copy[idx];
                        }
                    }
                    const idx = (y * w + x) * 4 + c;
                    data[idx] = sum / 9;
                }
            }
        }

        ctx.putImageData(imageData, 0, 0);
    },

    /**
     * Apply adaptive contrast enhancement (CLAHE-like)
     */
    applyAdaptiveContrast(ctx, w, h) {
        const imageData = ctx.getImageData(0, 0, w, h);
        const data = imageData.data;

        // Calculate histogram
        const histogram = new Array(256).fill(0);
        for (let i = 0; i < data.length; i += 4) {
            histogram[data[i]]++;
        }

        // Find min/max values (ignore outliers)
        let min = 0, max = 255;
        const pixelCount = w * h;
        let count = 0;

        for (let i = 0; i < 256; i++) {
            count += histogram[i];
            if (count >= pixelCount * 0.01) {
                min = i;
                break;
            }
        }

        count = 0;
        for (let i = 255; i >= 0; i--) {
            count += histogram[i];
            if (count >= pixelCount * 0.01) {
                max = i;
                break;
            }
        }

        // Apply contrast stretching
        const range = max - min || 1;
        const factor = 255 / range;

        for (let i = 0; i < data.length; i += 4) {
            const val = Math.min(255, Math.max(0, (data[i] - min) * factor));
            data[i] = val;
            data[i + 1] = val;
            data[i + 2] = val;
        }

        ctx.putImageData(imageData, 0, 0);
    },

    /**
     * Apply sharpening filter
     */
    applySharpen(ctx, w, h) {
        const imageData = ctx.getImageData(0, 0, w, h);
        const data = imageData.data;
        const copy = new Uint8ClampedArray(data);

        // Unsharp mask kernel
        const kernel = [
            0, -1, 0,
            -1, 5, -1,
            0, -1, 0
        ];

        for (let y = 1; y < h - 1; y++) {
            for (let x = 1; x < w - 1; x++) {
                for (let c = 0; c < 3; c++) {
                    let sum = 0;
                    for (let ky = -1; ky <= 1; ky++) {
                        for (let kx = -1; kx <= 1; kx++) {
                            const idx = ((y + ky) * w + (x + kx)) * 4 + c;
                            sum += copy[idx] * kernel[(ky + 1) * 3 + (kx + 1)];
                        }
                    }
                    const idx = (y * w + x) * 4 + c;
                    data[idx] = Math.min(255, Math.max(0, sum));
                }
            }
        }

        ctx.putImageData(imageData, 0, 0);
    }
};
