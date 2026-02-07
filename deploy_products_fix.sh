#!/bin/bash
# ChefPort Products Fix - Automated Deployment Script

set -e  # Exit on error

echo "=== ChefPort Products Data Fix Deployment ==="
echo ""

# Step 1: Navigate to project
cd /root/chefport-bot
echo "✓ Changed to /root/chefport-bot"

# Step 2: Stash local changes
echo ""
echo "Step 1/4: Stashing local changes..."
git stash
echo "✓ Local changes stashed"

# Step 3: Pull latest code
echo ""
echo "Step 2/4: Pulling latest code from GitHub..."
git pull origin main
echo "✓ Code updated"

# Step 4: Regenerate products_data.js with fixed script
echo ""
echo "Step 3/4: Regenerating products_data.js with fixed JavaScript syntax..."
source venv311/bin/activate
python scripts/import_products.py
echo "✓ products_data.js regenerated"

# Step 5: Verify the fix
echo ""
echo "Checking syntax (should see 'false' and 'null', NOT 'False' and 'None'):"
head -20 web/products_data.js | grep -E '"is_weighted"|"image_url"' || echo "Pattern check..."

# Step 6: Restart API
echo ""
echo "Step 4/4: Restarting API service..."
systemctl restart chefport-api
echo "✓ API restarted"

echo ""
echo "=== DEPLOYMENT COMPLETE ==="
echo "Products should now appear in Mini App!"
echo "If you see 'false' and 'null' above (NOT 'False'/'None'), the fix worked."
