#!/bin/bash
sudo rm kams_erp/ -R
sudo cp /media/sf_odoo/odoo/modules/kams_erp/ . -R
sudo chown odoo:odoo kams_erp/ -R
sudo find * -type d -print0 | sudo xargs -0 chmod 0755
sudo find . -type f -print0 | sudo xargs -0 chmod 0644
sudo /etc/init.d/odoo-server force-reload
sudo /etc/init.d/odoo-server restart
tail /var/log/odoo/odoo-server.log -f

