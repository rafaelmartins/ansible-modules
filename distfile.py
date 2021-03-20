#!/usr/bin/python

# Copyright: (c) 2021, Rafael G. Martins <rafael@rafaelmartins.eng.br>
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: distfile

short_description: Returns available distfile for a given project

description:
    - This module returns available distfile for a given project.

options:
    name:
        description:
            - Project name
        required: true
    version:
        description:
            - Project version
        required: false
        default: "LATEST"
    file_prefix:
        description:
            - Distfile file prefix
        required: false
        default: name + "-"
    file_extension:
        description:
            - Distfile file extension
        required: false
        default: ".tar.gz"

author:
    - Rafael G. Martins (@rafaelmartins)
'''

EXAMPLES = '''
# Find blogc source for latest build
- name: Find blogc source
  distfile:
    name: blogc

# Find blogc source for latest release
- name: Find blogc source
  distfile:
    name: blogc
    version: LATEST_RELEASE

# Find blogc source for 0.20.1
- name: Find blogc source
  distfile:
    name: blogc
    version: "0.20.1"
'''

RETURN = '''
version:
    description: The distfile version
    type: str
    returned: success
file_url:
    description: The distfile file name
    type: str
    returned: success
checksum:
    description: The distfile checksum url, compatible with get_url checksum
    type: str
    returned: success
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url

import re

base_url = 'https://distfiles.rgm.io'


def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
        version=dict(type='str', required=False, default='LATEST'),
        file_prefix=dict(type='str', required=False, default=''),
        file_extension=dict(type='str', required=False, default='.tar.gz'),
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    folder = module.params['version']
    if not folder.startswith('LATEST'):
        folder = '%s-%s' % (module.params['name'], module.params['version'])
    index = '%s/%s/%s/' % (base_url, module.params['name'], folder)

    rsp, info = fetch_url(module, index)
    if info['status'] != 200:
        module.fail_json(msg='Failed to request index listing', **result)
    index_data = rsp.read()
    rsp.close()

    prefix = module.params['file_prefix']
    if prefix == '':
        prefix = '%s-' % (module.params['name'],)

    re_archive = r'["\'](%s([^"\']+)%s)["\']' % (re.escape(prefix),
                                                 re.escape(module.params['file_extension']))
    m = re.search(re_archive, index_data.decode('utf-8'))
    if not m:
        module.fail_json(msg='Failed to detect distfile archive', **result)

    file_url = '%s/%s/%s-%s/%s' % (base_url, module.params['name'],
                                   module.params['name'], m.group(2), m.group(1))

    result['version'] = m.group(2)
    result['file_url'] = file_url
    result['checksum'] = 'sha512:%s.sha512' % (file_url,)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
