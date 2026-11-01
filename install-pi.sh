#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
set -euo pipefail

if [[ $(id -u) -ne 0 ]]; then
    echo "Run this installer with sudo." >&2
    exit 1
fi

app_user=${SUDO_USER:-coimager}
if ! id "$app_user" >/dev/null 2>&1; then
    echo "User $app_user does not exist." >&2
    exit 1
fi

source_dir=$(cd -- "$(dirname -- "$0")" && pwd)
app_dir=/opt/coimager
data_dir=/var/lib/coimager
driver_commit=826f4646905ca9a895f5bf1fd640c4bf5dd8a97c
driver_sha256=603b27babbe57bbe33a35d76f40d8949899cbcef268456e1c2c9375765e12b91

apt-get update
apt-get install -y curl python3-venv python3-pil python3-rpi.gpio python3-spidev

printf 'i2c-dev\n' > /etc/modules-load.d/coimager-i2c.conf
modprobe i2c-dev
udevadm trigger --subsystem-match=i2c-dev
udevadm settle

install -d -m 0755 "$app_dir"
install -d -m 0755 -o "$app_user" -g "$app_user" "$data_dir"
for file in main.py printToEpaper.py sensorDataGen.py sensorPlotEpaper.py settings.py manage.py requirements.txt LICENCE.md; do
    install -m 0644 "$source_dir/$file" "$app_dir/$file"
done

curl -fsSL "https://raw.githubusercontent.com/geeekpi/epaper/$driver_commit/Epaper.py" -o "$app_dir/Epaper.py"
actual_sha256=$(sha256sum "$app_dir/Epaper.py" | cut -d ' ' -f 1)
if [[ "$actual_sha256" != "$driver_sha256" ]]; then
    echo "GeeekPi driver checksum did not match. Installation stopped." >&2
    exit 1
fi
curl -fsSL "https://raw.githubusercontent.com/geeekpi/epaper/$driver_commit/LICENSE" -o "$app_dir/EPAPER-LICENSE"

if [[ ! -x "$app_dir/.venv/bin/python" ]]; then
    python3 -m venv --system-site-packages "$app_dir/.venv"
fi
"$app_dir/.venv/bin/python" -m pip install -r "$app_dir/requirements.txt"

raspi-config nonint do_i2c 0
raspi-config nonint do_spi 0
config=/boot/firmware/config.txt
if [[ ! -f "$config" ]]; then
    config=/boot/config.txt
fi
if ! grep -q '^dtparam=i2c_arm_baudrate=' "$config"; then
    printf '\ndtparam=i2c_arm_baudrate=10000\n' >> "$config"
fi

for group in i2c spi gpio; do
    if getent group "$group" >/dev/null; then
        usermod -aG "$group" "$app_user"
    fi
done

cat > /etc/systemd/system/coimager.service <<EOF
[Unit]
Description=CCS811 eCO2 e-paper imager
After=multi-user.target

[Service]
Type=simple
User=$app_user
WorkingDirectory=$app_dir
Environment=COIMAGER_DATA_DIR=$data_dir
ExecStart=$app_dir/.venv/bin/python $app_dir/main.py
Restart=always
RestartSec=15

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/coimager-manage.service <<EOF
[Unit]
Description=Local settings page for the CCS811 e-paper imager

[Service]
Type=simple
User=$app_user
WorkingDirectory=$app_dir
Environment=COIMAGER_DATA_DIR=$data_dir
Environment=PYTHONDONTWRITEBYTECODE=1
ExecStart=$app_dir/.venv/bin/python $app_dir/manage.py
Restart=always
RestartSec=15
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$data_dir
UMask=0077

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable coimager.service coimager-manage.service
systemctl restart coimager.service coimager-manage.service
echo "Installed. Reboot once for I2C/SPI changes, then check: systemctl status coimager.service"
