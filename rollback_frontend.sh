#!/bin/bash
# Client Revert
sed -i '464,467d' /root/chefport-bot/web/miniapp_client.html
sed -i '447,448d' /root/chefport-bot/web/miniapp_client.html
sed -i '406,407d' /root/chefport-bot/web/miniapp_client.html
sed -i '366,376d' /root/chefport-bot/web/miniapp_client.html
sed -i '228,230d' /root/chefport-bot/web/miniapp_client.html

# Admin Revert
sed -i '613s/document.*checked/false/' /root/chefport-bot/web/miniapp_admin.html
sed -i '507,512d' /root/chefport-bot/web/miniapp_admin.html
sed -i '476,479d' /root/chefport-bot/web/miniapp_admin.html
