#!/bin/bash
set -e

##### Constants

HELP_INFO="To replace all code use parameter -a | --all,\nif you want replace only custom modules use -n | --noall"


##### Functions

function start_project
{
    sudo /etc/init.d/odoo-server force-reload
    sudo /etc/init.d/odoo-server restart
    sudo chmod +x fast_replace_script.sh
    tail /var/log/odoo/odoo-server.log -f
}

function change_file_privilege
{
    echo -e $1
    sudo chown odoo:odoo $1 -R
    sudo find * -type d -print0 | sudo xargs -0 chmod 0755
    sudo find . -type f -print0 | sudo xargs -0 chmod 0644
}

function replace_module
{
    echo -e "Removing files"
    sudo rm /opt/odoo/modules/kams_erp/ -R
    if [ ! -d '/media/sf_odoo/odoo/modules/kams_erp' ]; then
        if [ -d '/media/sf_kamserp-v10/modules/kams_erp' ]; then
            echo -e "Copying files"
            sudo cp /media/sf_kamserp-v10/modules/kams_erp/ /opt/odoo/modules/ -R
            change_file_privilege /opt/odoo/modules/kams_erp/
        else
            echo "File not found"
        fi
    else
        sudo cp /media/sf_odoo/odoo/modules/kams_erp/ . -R
        change_file_privilege /opt/odoo/modules/kams_erp/
    fi
    start_project
}   # end of replace module

function replace_all
{
    echo -e "Removing files"
    sudo rm /opt/odoo/ -R
    if [ ! -d '/media/sf_odoo/odoo/modules/kams_erp' ]; then
        if [ -d '/media/sf_kamserp-v10/modules/kams_erp' ]; then
            echo -e "Copying files"
            sudo rsync -ar --progress /media/sf_kamserp-v10/ /opt/odoo/ --exclude=.git --exclude=.idea --exclude=.mailmap
            change_file_privilege /opt/odoo
        else
            echo "File not found"
        fi
    else
        sudo rsync -ar --progress /media/sf_odoo/odoo/ /opt/odoo/ --exclude=.git --exclude=.idea --exclude=.mailmap
        change_file_privilege /opt/odoo
    fi
    start_project
}   # end of replace all of project

if [ "$1" == "" ]; then
    echo -e ${HELP_INFO}
else
    while [ "$1" != "" ]; do
        case $1 in
            -a | --all )            replace_all
                                    ;;
            -n | --noall )          replace_module
                                    ;;
            -h | --help )           echo -e ${HELP_INFO}
                                    exit
                                    ;;
            * )                     echo -e ${HELP_INFO}
                                    exit 1
        esac
    done
fi