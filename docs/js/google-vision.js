/**
 * Google Cloud Vision API Module
 * Highest accuracy OCR available
 * Free tier: 1000 images/month
 */
const GoogleVision = {
    // User needs to set their API key
    API_KEY: localStorage.getItem('google_vision_key') || '',
    API_URL: 'https://vision.googleapis.com/v1/images:annotate',

    isConfigured() {
        return !!this.API_KEY;
    },

    setApiKey(key) {
        this.API_KEY = key;
        localStorage.setItem('google_vision_key', key);
    },

    async process(file, onProgress) {
        if (!this.isConfigured()) {
            throw new Error('Google Vision API key not set');
        }

        onProgress && onProgress('Converting image...');

        // Convert file to base64
        const base64 = await this.fileToBase64(file);

        onProgress && onProgress('Calling Google Vision AI...');

        const requestBody = {
            requests: [{
                image: { content: base64 },
                features: [{
                    type: 'TEXT_DETECTION',
                    maxResults: 1
                }],
                imageContext: {
                    languageHints: ['en']
                }
            }]
        };

        try {
            const response = await fetch(`${this.API_URL}?key=${this.API_KEY}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error?.message || `HTTP ${response.status}`);
            }

            const data = await response.json();
            console.log('Google Vision Response:', data);

            const text = data.responses?.[0]?.textAnnotations?.[0]?.description || '';

            onProgress && onProgress('Done!');

            console.log('Google Vision OCR Result:', text);
            return text;
        } catch (err) {
            console.error('Google Vision Error:', err);
            throw new Error('Google Vision failed: ' + err.message);
        }
    },

    async fileToBase64(file) {
        return new Promise((resolve, reject) => {
            // First enhance the image
            const img = new Image();
            const url = URL.createObjectURL(file);

            img.onload = () => {
                URL.revokeObjectURL(url);

                const canvas = document.createElement('canvas');
                const maxWidth = 1600;
                let w = img.width;
                let h = img.height;

                if (w > maxWidth) {
                    h = (h * maxWidth) / w;
                    w = maxWidth;
                }

                canvas.width = w;
                canvas.height = h;
                const ctx = canvas.getContext('2d');

                // Draw and enhance
                ctx.drawImage(img, 0, 0, w, h);

                // Apply contrast
                const imageData = ctx.getImageData(0, 0, w, h);
                const data = imageData.data;
                const contrast = 1.3;

                for (let i = 0; i < data.length; i += 4) {
                    data[i] = Math.min(255, Math.max(0, ((data[i] - 128) * contrast) + 128));
                    data[i + 1] = Math.min(255, Math.max(0, ((data[i + 1] - 128) * contrast) + 128));
                    data[i + 2] = Math.min(255, Math.max(0, ((data[i + 2] - 128) * contrast) + 128));
                }
                ctx.putImageData(imageData, 0, 0);

                // Convert to base64
                const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
                const base64 = dataUrl.split(',')[1];
                resolve(base64);
            };

            img.onerror = () => {
                URL.revokeObjectURL(url);
                reject(new Error('Failed to load image'));
            };

            img.src = url;
        });
    }
};
