![AberMUSH](docs/logo.png)

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

## Player Commands

All players can use the following commands:

``` bash
who                              - List players and where they are
quit/exit                        - Leave the game
say [message]                    - Says something out loud
look/examine                     - Examines the surroundings
go [exit]                        - Moves through the exit specified
attack [target]                  - Attack another player or NPC
check inventory                  - Check the contents of your inventory
take/get [item]                  - Pick up an item
drop [item]                      - Drop an item
whisper [target] [message]       - Whisper to a player in the same room
tell [target] [message]          - Send a tell message to another player
```

## Witch Commands

Witches are the admins of the system, and have additional supernatural powers. The first user to create an account gains witch status. Additional witches may be assigned by appending them to the `witches` file, which is located in the same directory as `abermush.py` is run from.

``` bash
mute/silence [target]            - Mutes a player and prevents them from attacking
unmute/unsilence [target]        - Unmutes a player
teleport [room]                  - Teleport to a room
summon [target]                  - Summons a player to your location
```
