XEN_CONFIG_TPL = '''
bootloader = '/usr/lib/xen-4.4/bin/pygrub'

name        = '{{ name }}'
vcpus       = {{ cpu }}
memory      = {{ ram }}
root        = '/dev/xvda2 ro'
disk        = [
                  'file:{{ dest }}/{{ name }}/disk.img,xvda2,w',
                  'file:{{ dest }}/{{ name }}/swap.img,xvda1,w',
              ]
vif         = [
{%- for iface in interfaces %}
                  '{% if iface.address is defined %}ip={{ iface.address }}{% endif %}{% if iface.bridge is defined %},bridge={{ iface.bridge }}{% endif %}', 
{%- endfor %}
              ]

on_poweroff = 'destroy'
on_reboot   = 'restart'
on_crash    = 'restart'
'''

#
# Need to pass server.interfaces
#
DEB_IFACE_TPL = '''
# The loopback network interface
auto lo
iface lo inet loopback

{% for iface in interfaces %}
auto {{ iface.name }}
iface {{ iface.name }} inet {{ iface.type }}
{% if iface.type == 'static' %}
    address {{ iface.address }}
    netmask {{ iface.netmask }}
    {% if iface.gateway is defined %}gateway {{ iface.gateway }}{% endif %}
{% endif %}
{% endfor %}
'''

#
# Need to pass 1 interface from server.interfaces
#
RH_IFACE_TPL = '''
DEVICE={{ name }}
BOOTPROTO={{ type }}
ONBOOT=yes
TYPE=Ethernet
NM_CONTROLLED=no

{% if type == 'static' %}
IPADDR={{ address }}
NETMASK={{ netmask }}
{% if gateway is defined -%}
GATEWAY={{ gateway }}
{%- endif %}
{% endif %}
'''