# Ansible Deployment (Ubuntu Target)

This folder provides a simple modular Ansible setup to deploy the Docker Compose stack on a remote Ubuntu machine.

## Structure

- `ansible.cfg`: local Ansible config.
- `inventories/production/hosts.ini`: target hosts.
- `group_vars/all.yml`: global deployment variables.
- `playbooks/deploy.yml`: main playbook.
- `roles/ubuntu_base`: base Ubuntu packages.
- `roles/docker_engine`: Docker Engine + Compose plugin installation.
- `roles/stack_deploy`: fetch source (`git` or `local`) and run `docker compose`.

## Prerequisites (Control Machine)

- Ansible installed (`ansible-core`).
- SSH access to target Ubuntu machine.
- Sudo privileges on target.

## 1) Configure Inventory

Edit `inventories/production/hosts.ini`:

```ini
[microservices]
ubuntu-target ansible_host=192.168.1.50 ansible_user=ubuntu ansible_ssh_private_key_file=../../keys/id_rsa
```

## 2) Configure Variables

Edit `group_vars/all.yml`:

- `stack_source_type`: `git` (recommended) or `local`.
- `stack_git_repo`: source repository.
- `stack_git_version`: branch/tag/commit.
- `stack_git_manage_ssh_key`: if `true`, copy SSH key from control host to target.
- `stack_git_ssh_key_local_path`: private key path on control host.
- `stack_git_ssh_user`: target user used for git clone.
- `stack_git_ssh_key_target_path`: key path created on target.
- `stack_remote_dir`: checkout root on target.
- `stack_project_subdir`: path to compose project in repository.
- `stack_compose_dir`: effective compose directory.
- `stack_local_src`: local source path (used only when `stack_source_type=local`).
- `stack_state`: `present`, `absent`, or `restart`.
- `stack_build`: build images on deploy.
- `stack_pull`: pull images before deploy.

Default repo is already set to:

`git@github.com:Ankoay-Feno/MINIMIZE_SPOF.git`

## 3) Deploy

Run from `ansible_roles/`:

```bash
ansible-playbook playbooks/deploy.yml
```

If your sudo requires password:

```bash
ansible-playbook playbooks/deploy.yml -K
```

## 4) Common Operations

Deploy/update:

```bash
ansible-playbook playbooks/deploy.yml -e stack_state=present
```

Restart stack:

```bash
ansible-playbook playbooks/deploy.yml -e stack_state=restart
```

Stop/remove stack:

```bash
ansible-playbook playbooks/deploy.yml -e stack_state=absent
```

## Notes

- In `git` mode with `stack_git_manage_ssh_key: true`, Ansible copies the key from control host to target automatically.
- Default key location on control host is `keys/id_rsa` (relative to repository root).
- If you disable key management, target host must already have SSH access to GitHub.
- If SSH key setup is not ready, use HTTPS repo URL instead in `group_vars/all.yml`.
- Target OS is validated as Ubuntu in `roles/ubuntu_base`.
- Docker Compose uses the remote file:
  - `{{ stack_compose_dir }}/{{ stack_compose_file }}`
