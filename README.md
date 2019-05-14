# AberMUSH
A modern Python MU* engine with AberMUD universe.

Based on dumserver by Bartek Radwanski and Mark Frimston https://github.com/wowpin/dumserver

You can also use a mud client of your choice if you wish - use connection details below:

```
telnet [hostname] 35123
```

## Running the Server
```diff
- IMPORTANT - Python >= 3.6.7 is required (Ubuntu >= 18.04 LTS)!
```
1. Update your system `sudo apt update && sudo apt upgrade`
2. Get the repo `git clone https://code.freedombone.net/bashrc/AberMUSH`
3. CD into 'AberMUSH' and install the server `sudo ./installer.sh`
4. Run it by typing `python3 abermush.py`

You now should be able to connect to your server on `<server IP/hostname>:35123`

You can define who has admin/ArchWizard status by creating a file called `admins` within the same directory that you ran `abermush.py` from and adding their usernames. Admins can mute or unmute other players, teleport to rooms or summon other players to their location.
