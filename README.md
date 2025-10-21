ProjecHhgSys - Setup and Deployment
=================================

This README documents how to prepare a CentOS VM to run the ProjecHhgSys Django project, how to reproduce the local development environment, and the exact dependency installation steps.

1) Project Python dependencies
------------------------------
The project uses Python 3.6 (tested) and the following pinned Python packages (in `requirements.txt`):

- Django==3.2.20
- PyMySQL==0.10.1

Optional:
- mysqlclient==1.4.6  # uncomment in `requirements.txt` if you prefer the C driver (requires system dev headers)

2) System packages required on CentOS
-------------------------------------
Install the development toolchain, Python headers, and MySQL client headers on the VM.

For CentOS 7 (yum):

```bash
sudo yum install -y epel-release
sudo yum groupinstall -y "Development Tools"
sudo yum install -y gcc gcc-c++ make
sudo yum install -y python36 python36-devel python36-virtualenv
sudo yum install -y mariadb-devel
sudo yum install -y openssl-devel libffi-devel git rsync
```

For CentOS 8 / Stream (dnf):

```bash
sudo dnf groupinstall -y "Development Tools"
sudo dnf install -y gcc gcc-c++ make python3 python3-devel python3-virtualenv mariadb-devel openssl-devel libffi-devel git rsync
```

Notes:
- `mariadb-devel` provides MySQL client headers needed by `mysqlclient`.
- If you prefer a pure-Python driver, `PyMySQL` avoids the need for `mariadb-devel`.

3) Create and activate a Python virtual environment
--------------------------------------------------
From the project root on the VM (`/opt/ProjecHhgSys`):

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
```

4) Install Python dependencies
------------------------------
With the venv activated, install packages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

If you want to use `mysqlclient` instead of `PyMySQL`:

```bash
# ensure system dev deps are installed (mariadb-devel, python3-devel, gcc)
pip uninstall -y PyMySQL
pip install mysqlclient==1.4.6
```

5) DB migrations and static
---------------------------
Run migrations and collect static assets (if used):

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

6) Start the development server (testing only)
----------------------------------------------

```bash
python manage.py runserver 0.0.0.0:8000
```

Open `http://<vm_ip>:8000` from your workstation.

7) Verification commands
------------------------
On the VM (local):

```bash
curl -I http://127.0.0.1:8000
```

From your workstation:

```bash
curl -I http://<vm_ip>:8000
```

8) Notes & recommendations
--------------------------
- The project currently targets Python 3.6; upgrading to Python 3.8+ is recommended for long-term support.
- `PyMySQL` is recommended for faster setup. `mysqlclient` gives a native C driver but needs build tools and dev headers.
- For production, use a WSGI server (gunicorn) behind Nginx and manage using systemd. I can provide sample configs.

9) Common troubleshooting
-------------------------
- If `mysqlclient` build fails, ensure `gcc`, `python3-devel`, and `mariadb-devel` are installed.
- If you see `ModuleNotFoundError: No module named 'pymysql'`, install `PyMySQL` in the active venv: `pip install PyMySQL`.
- If the code uses Python 3.8+ features (e.g. `from __future__ import annotations`), remove those lines or upgrade Python on the VM.


If you want, I can also:
- Provide commands to rsync files from local to VM.
- Create a systemd unit and Nginx config for production deployment.
- Generate a `deploy.sh` script to fully automate the VM setup.
