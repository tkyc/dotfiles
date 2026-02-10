# Linux Environment Setup

1. Install git and ansible

2. Clone this repository into ~/repo

3. Run the ansible playbook <br>

`sudo ansible-playbook main.yml --ask-become-pass`

# Misc.
 Run the following to update packages only:<br>

`sudo ansible-playbook main.yml --tags install_packages`

