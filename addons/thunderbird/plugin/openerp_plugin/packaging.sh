# Use this Shell Script for Cleaning & Compressing  the chnages in Plugin 
# Run this script using jar command.

rm chrome/openerp_plugin.jar
rm ../openerp_plugin.xpi 
cd chrome/openerp_plugin/
jar cvf openerp_plugin.jar *
cd ..
mv openerp_plugin/openerp_plugin.jar openerp_plugin.jar
cd ..
zip -r ../openerp_plugin.xpi *

