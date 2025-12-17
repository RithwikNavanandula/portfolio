/**
 * Offline OCR Module - Uses Tesseract.js for browser-based OCR
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
            // Wait for existing init to complete
            while (this.isLoading) {
                await new Promise(r => setTimeout(r, 100));
            }
            return this.isReady;
        }

        this.isLoading = true;

        try {
            onProgress && onProgress('Loading OCR engine...');

            // Create worker
            this.worker = await Tesseract.createWorker('eng', 1, {
                logger: m => {
                    if (m.status === 'recognizing text') {
                        const pct = Math.round(m.progress * 100);
                        onProgress && onProgress(`Recognizing... ${pct}%`);
                    }
                }
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

    /**
     * Process image with Tesseract
     */
    async process(imageData, onProgress) {
        // Initialize if needed
        if (!this.isReady) {
            await this.init(onProgress);
        }

        onProgress && onProgress('Processing image...');

        try {
            // Preprocess image for better accuracy
            const processed = await this.preprocessImage(imageData);

            onProgress && onProgress('Running OCR...');

            const result = await this.worker.recognize(processed);

            onProgress && onProgress('Done!');

            console.log('OCR Result:', result.data.text);
            return result.data.text;
        } catch (err) {
            console.error('OCR Error:', err);
            throw new Error('OCR failed: ' + err.message);
        }
    },

    /**
     * Preprocess image for better OCR accuracy
     */
    async preprocessImage(imageData) {
        return new Promise((resolve, reject) => {
            const img = new Image();

            img.onload = () => {
                // Create canvas for processing
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');

                // Use larger size for better accuracy
                const maxWidth = 1400;
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

                // Apply contrast enhancement
                const imageData = ctx.getImageData(0, 0, w, h);
                const data = imageData.data;

                // Increase contrast
                const contrast = 1.3;
                for (let i = 0; i < data.length; i += 4) {
                    data[i] = Math.min(255, Math.max(0, ((data[i] - 128) * contrast) + 128));
                    data[i + 1] = Math.min(255, Math.max(0, ((data[i + 1] - 128) * contrast) + 128));
                    data[i + 2] = Math.min(255, Math.max(0, ((data[i + 2] - 128) * contrast) + 128));
                }

                ctx.putImageData(imageData, 0, 0);

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

            // Handle different input types
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
     * Terminate worker to free memory
     */
    async terminate() {
        if (this.worker) {
            await this.worker.terminate();
            this.worker = null;
            this.isReady = false;
        }
    }
};
