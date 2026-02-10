# Linux Environment Setup

1. Install git and ansible

2. Clone this repository into ~/repo

3. sudo ansible-playbook main.yml --ask-become-pass

# Misc.
- To update packages only, run the following:
`sudo ansible-playbook main.yml --tags install_packages`

