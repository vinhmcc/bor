cat > install.sh << 'EOF'
#!/bin/bash

echo "========================================"
echo "   CÀI ĐẶT TẤT CẢ PIP CHO BOT STRESSER   "
echo "========================================"

# Cập nhật pip
echo "[1/4] Đang nâng cấp pip..."
pip install --upgrade pip

# Cài các thư viện chính
echo "[2/4] Đang cài python-telegram-bot..."
pip install python-telegram-bot --upgrade

echo "[3/4] Đang cài APScheduler và tzdata..."
pip install apscheduler tzdata --upgrade

echo "[4/4] Cài thêm một số thư viện hữu ích..."
pip install requests cloudscraper aiohttp colorama --upgrade

echo ""
echo "========================================"
echo "✅ CÀI ĐẶT HOÀN TẤT!"
echo "========================================"
echo ""
echo "Bạn có thể chạy bot bằng lệnh:"
echo "python3 bot_tele.py"
echo ""
echo "Hoặc chạy file này lần sau bằng lệnh:"
echo "bash install.sh"
EOF
