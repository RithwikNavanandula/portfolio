#!/bin/bash
# Sitari API - AWS Lightsail Deployment Script
# Run this script on your Lightsail instance after cloning the repo

set -e  # Exit on error

echo "🚀 Sitari API - AWS Lightsail Deployment"
echo "========================================="

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Set environment variables (you should set these in /etc/environment or systemd)
export DJANGO_DEBUG=False
# DJANGO_SECRET_KEY should be set securely
# DJANGO_ALLOWED_HOSTS should be set to your domain

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Run migrations
echo "🗃️ Running migrations..."
python manage.py migrate

# Create media directory
mkdir -p media/messages media/temp

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 IMPORTANT NEXT STEPS:"
echo ""
echo "1. Set environment variables in /etc/environment or your systemd service:"
echo "   DJANGO_SECRET_KEY=<generate-a-secure-key>"
echo "   DJANGO_DEBUG=False"
echo "   DJANGO_ALLOWED_HOSTS=your-domain.com,www.your-domain.com"
echo ""
echo "2. Copy the systemd service file:"
echo "   sudo cp sitari.service /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable sitari"
echo "   sudo systemctl start sitari"
echo ""
echo "3. Configure Nginx as reverse proxy (see nginx.conf)"
echo ""
echo "4. Update WhatsApp webhook URL in Meta Dashboard to:"
echo "   https://your-domain.com/api/webhook/"
echo ""
echo "To run manually:"
echo "  source venv/bin/activate"
echo "  gunicorn sitari.wsgi:application --bind 0.0.0.0:8000"
