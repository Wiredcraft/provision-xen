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

XEN_CONFIG_LVM_TPL = '''
bootloader = '/usr/lib/xen-4.4/bin/pygrub'

name        = '{{ name }}'
vcpus       = {{ cpu }}
memory      = {{ ram }}
root        = '/dev/xvda2 ro'
disk        = [
                  '{{ dest }}/{{ name }}/disk.img,raw,xvda2,w',
                  '{{ dest }}/{{ name }}/swap.img,raw,xvda1,w',
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

#
# Simple Iptables template - consider eth0 public, eth1 private
# Useful for gateway / router
#
IPTABLES_TPL = '''*nat
:PREROUTING ACCEPT [0:0]
:INPUT ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
:POSTROUTING ACCEPT [0:0]
{%- if portforwards is defined %}
{% for pf in portforwards -%}
-A PREROUTING -i eth0 -p tcp -m tcp --dport {{ pf.from }} -j DNAT --to-destination {{ pf.to }}
{% endfor %}
{% endif %}
{% if gateway is defined -%}{% if gateway -%}
-A POSTROUTING -o eth0 -j MASQUERADE
{%- endif %}{%- endif %}
COMMIT

*filter
:INPUT ACCEPT [0:0]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
{% if gateway is defined -%}{% if gateway -%}
-A FORWARD -i eth1 -j ACCEPT
{%- endif %}{%- endif %}
COMMIT

'''