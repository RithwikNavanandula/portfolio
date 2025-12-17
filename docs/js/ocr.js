/**
 * OCR Module - Maximum Accuracy Version
 * Features: Dual engine comparison, strong preprocessing, grayscale, sharpening
 */
const OCR = {
    API_KEY: 'K85403682988957',
    API_URL: 'https://api.ocr.space/parse/image',

    async process(file, onProgress) {
        onProgress && onProgress('Preprocessing image...');

        // Strong image preprocessing
        const enhanced = await this.enhanceImage(file);

        onProgress && onProgress('Running OCR (Engine 1)...');

        // Try both engines and pick best result
        const [result1, result2] = await Promise.all([
            this.callOCR(enhanced, 1, onProgress),
            this.callOCR(enhanced, 2, onProgress)
        ]);

        console.log('Engine 1 result:', result1?.length || 0, 'chars');
        console.log('Engine 2 result:', result2?.length || 0, 'chars');

        // Pick the result with more detected dates/batches (better for labels)
        const score1 = this.scoreResult(result1);
        const score2 = this.scoreResult(result2);

        console.log('Engine 1 score:', score1);
        console.log('Engine 2 score:', score2);

        const bestResult = score1 >= score2 ? result1 : result2;
        const engine = score1 >= score2 ? 1 : 2;

        onProgress && onProgress(`Done! (Engine ${engine} was better)`);

        return bestResult || '';
    },

    /**
     * Score OCR result based on useful content for labels
     */
    scoreResult(text) {
        if (!text) return 0;
        let score = 0;

        // Count dates found
        const dates = (text.match(/\d{1,2}[\/.-]\d{1,2}[\/.-]\d{2,4}/g) || []).length;
        score += dates * 10;

        // Count batch-like patterns
        const batches = (text.match(/\d{2}-\d{4}-\d{4}/g) || []).length;
        score += batches * 15;

        // Count keywords
        const keywords = ['BATCH', 'MFG', 'EXP', 'DATE', 'MANUFACTURE', 'EXPIRY'];
        keywords.forEach(kw => {
            if (text.toUpperCase().includes(kw)) score += 5;
        });

        // Penalize very short results
        if (text.length < 50) score -= 20;

        // Bonus for longer, readable text
        score += Math.min(text.length / 10, 20);

        return score;
    },

    async callOCR(imageBlob, engine, onProgress) {
        const formData = new FormData();
        formData.append('apikey', this.API_KEY);
        formData.append('file', imageBlob, 'image.jpg');
        formData.append('language', 'eng');
        formData.append('OCREngine', engine.toString());
        formData.append('scale', 'true');
        formData.append('isTable', 'false');
        formData.append('detectOrientation', 'true');

        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 30000);

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
     * Enhanced image preprocessing for maximum accuracy
     */
    async enhanceImage(file) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            const url = URL.createObjectURL(file);

            img.onload = () => {
                URL.revokeObjectURL(url);

                // Higher resolution for better accuracy
                const maxWidth = 1600;
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

                // Apply all enhancements
                this.applyGrayscale(ctx, w, h);
                this.applyContrast(ctx, w, h, 1.5);
                this.applySharpening(ctx, w, h);

                // Higher quality output
                canvas.toBlob(
                    blob => blob ? resolve(blob) : reject(new Error('Processing failed')),
                    'image/png',  // PNG for lossless
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
            const gray = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
            data[i] = gray;
            data[i + 1] = gray;
            data[i + 2] = gray;
        }

        ctx.putImageData(imageData, 0, h);
        ctx.putImageData(imageData, 0, 0);
    },

    /**
     * Apply contrast enhancement
     */
    applyContrast(ctx, w, h, factor) {
        const imageData = ctx.getImageData(0, 0, w, h);
        const data = imageData.data;

        for (let i = 0; i < data.length; i += 4) {
            data[i] = Math.min(255, Math.max(0, ((data[i] - 128) * factor) + 128));
            data[i + 1] = Math.min(255, Math.max(0, ((data[i + 1] - 128) * factor) + 128));
            data[i + 2] = Math.min(255, Math.max(0, ((data[i + 2] - 128) * factor) + 128));
        }

        ctx.putImageData(imageData, 0, 0);
    },

    /**
     * Apply sharpening using unsharp mask technique
     */
    applySharpening(ctx, w, h) {
        const imageData = ctx.getImageData(0, 0, w, h);
        const data = imageData.data;
        const copy = new Uint8ClampedArray(data);

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
