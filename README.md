# F4R3S.DZ Scanner

F4R3S.DZ is a web security scanner with a license system.  
It allows scanning targets for open ports using multiple profiles.

## Features
- Port scanning with three profiles: Quick, Full, Stealth
- License key authentication (username + key)
- Modern dark UI
- Easy to run on any Linux distribution

## Requirements
- Python 3.9 or higher
- Kali Linux (recommended) or any Linux distribution
- A valid license key (contact the seller)

## Installation on Kali Linux

1. Update your system:
   ```bash
   sudo apt update && sudo apt upgrade -y

2- Install Python, pip, and git:
 sudo apt install python3 python3-pip python3-venv git -y

3- Clone this repository:

git clone https://github.com/F4R3SX0/F4R3S.DZ.git
cd F4R3S.DZ

4- Create and activate a virtual environment (recommended):
python3 -m venv venv
source venv/bin/activate

5- Install dependencies:

pip install -r requirements.txt

6- Place your config.key file in the same directory as app.py.
(The seller will provide this file. It contains your credentials.)

7- Run the application:

 python app.py

 8-  Open your browser and go to:

http://localhost:8080

