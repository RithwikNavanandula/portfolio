/**
 * Offline OCR Module - Enhanced Tesseract.js for maximum accuracy
 * Works completely offline after first load
 */
const OfflineOCR = {
    worker: null,
    isReady: false,
    isLoading: false,

    /**
     * Initialize Tesseract worker (lazy load)
     */
    async init(onProgress) {
        if (this.isReady) return true;
        if (this.isLoading) {
            while (this.isLoading) {
                await new Promise(r => setTimeout(r, 100));
            }
            return this.isReady;
        }

        this.isLoading = true;

        try {
            onProgress && onProgress('Loading OCR engine...');

            this.worker = await Tesseract.createWorker('eng', 1, {
                logger: m => {
                    if (m.status === 'recognizing text') {
                        const pct = Math.round(m.progress * 100);
                        onProgress && onProgress(`Recognizing... ${pct}%`);
                    }
                }
            });

            // Set optimal parameters for label scanning
            await this.worker.setParameters({
                tessedit_pageseg_mode: '6'  // Assume uniform block of text
            });

            this.isReady = true;
            console.log('Tesseract worker ready');
            return true;
        } catch (err) {
            console.error('Tesseract init failed:', err);
            this.isLoading = false;
            throw new Error('Failed to load offline OCR: ' + err.message);
        } finally {
            this.isLoading = false;
        }
    },

    async process(imageData, onProgress) {
        if (!this.isReady) {
            await this.init(onProgress);
        }

        onProgress && onProgress('Enhancing image...');

        try {
            const processed = await this.preprocessImage(imageData);

            onProgress && onProgress('Running OCR...');

            const result = await this.worker.recognize(processed);

            onProgress && onProgress('Done!');

            console.log('Offline OCR Result:', result.data.text);
            return result.data.text;
        } catch (err) {
            console.error('Offline OCR Error:', err);
            throw new Error('OCR failed: ' + err.message);
        }
    },

    /**
     * Enhanced preprocessing for maximum accuracy
     */
    async preprocessImage(imageData) {
        return new Promise((resolve, reject) => {
            const img = new Image();

            img.onload = () => {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');

                // Higher resolution
                const maxWidth = 1600;
                let w = img.width;
                let h = img.height;

                if (w > maxWidth) {
                    h = (h * maxWidth) / w;
                    w = maxWidth;
                }

                canvas.width = w;
                canvas.height = h;

                // Draw image
                ctx.drawImage(img, 0, 0, w, h);

                // Apply all enhancements
                this.applyGrayscale(ctx, w, h);
                this.applyContrast(ctx, w, h, 1.5);
                this.applyBinarization(ctx, w, h);

                // Return as blob URL
                canvas.toBlob(blob => {
                    if (blob) {
                        resolve(URL.createObjectURL(blob));
                    } else {
                        reject(new Error('Failed to process image'));
                    }
                }, 'image/png');
            };

            img.onerror = () => reject(new Error('Failed to load image'));

            if (typeof imageData === 'string') {
                img.src = imageData;
            } else if (imageData instanceof Blob || imageData instanceof File) {
                img.src = URL.createObjectURL(imageData);
            } else {
                reject(new Error('Invalid image data'));
            }
        });
    },

    /**
     * Convert to grayscale
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

        ctx.putImageData(imageData, 0, 0);
    },

    /**
     * Apply contrast
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
     * Apply adaptive binarization (Otsu's method) for clearer text
     */
    applyBinarization(ctx, w, h) {
        const imageData = ctx.getImageData(0, 0, w, h);
        const data = imageData.data;

        // Calculate histogram
        const histogram = new Array(256).fill(0);
        for (let i = 0; i < data.length; i += 4) {
            histogram[data[i]]++;
        }

        // Find Otsu's threshold
        const total = w * h;
        let sum = 0;
        for (let i = 0; i < 256; i++) sum += i * histogram[i];

        let sumB = 0, wB = 0, wF = 0, maxVar = 0, threshold = 128;

        for (let i = 0; i < 256; i++) {
            wB += histogram[i];
            if (wB === 0) continue;
            wF = total - wB;
            if (wF === 0) break;

            sumB += i * histogram[i];
            const mB = sumB / wB;
            const mF = (sum - sumB) / wF;
            const variance = wB * wF * (mB - mF) ** 2;

            if (variance > maxVar) {
                maxVar = variance;
                threshold = i;
            }
        }

        // Apply threshold
        for (let i = 0; i < data.length; i += 4) {
            const val = data[i] > threshold ? 255 : 0;
            data[i] = val;
            data[i + 1] = val;
            data[i + 2] = val;
        }

        ctx.putImageData(imageData, 0, 0);
    },

    async terminate() {
        if (this.worker) {
            await this.worker.terminate();
            this.worker = null;
            this.isReady = false;
        }
    }
};
