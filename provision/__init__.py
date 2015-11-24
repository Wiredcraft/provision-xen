__author__ = 'Vincent Viallet'
__author_email__ = 'vincent@wiredcraft.com'
__version__ = '0.0.1'

from jinja2 import Template

TEMPLATE = '''
bootloader = '/usr/lib/xen-4.4/bin/pygrub'

name        = '{{ name }}'
vcpus       = {{ cpu }}
memory      = {{ ram }}
root        = '/dev/xvda2 ro'
disk        = [
                  'file:/data/xen/domains/{{ name }}/disk.img,xvda2,w',
                  'file:/data/xen/domains/{{ name }}/swap.img,xvda1,w',
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

def prepare_config(server):
    template = Template( TEMPLATE )
    outputText = template.render( server )
    return outputText


def build(server={}):
    '''
    Provided with a server definition; build the server
    '''
    if not server:
        raise RuntimeError('Invalid server definition')

    config = prepare_config(server)
    print config