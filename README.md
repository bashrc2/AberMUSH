![AberMUSH](docs/title.png)

<blockquote>"Once a year the dragon emerged from its cave. The people of the valleys could hear its thundering roar as it awakened from its long slumber."</blockquote>

AberMUSH is a text based role playing game with UTF-8 ANSI graphics, set in the [AberMUD](https://en.wikipedia.org/wiki/AberMUD) 5 universe. Explore, battle and adventure in a fantasy version of medieval Wales. Experience DnD style combat, gambling disputes, excessive ale consumption and puzzling mysteries in the once magnificent but now fallen city of Tranoch, with dynamic scenery, tides, wildlife and weather effects.

This game includes 8 bit console graphics, but if you are a MUD purist or don't need graphics then you can turn them off.

Based on dumserver by Bartek Radwanski and Mark Frimston https://github.com/wowpin/dumserver

![AberMUSH](docs/screenshot2.jpg)

You can also use a mud client of your choice if you wish - use connection details below:

```
telnet [hostname] 35123
```
or via ssh:

```
ssh [username]@[hostname] -p 35124
```

If you havn't already created an account then when logging in via ssh your username and password can be anything and you can then use the *new* command to create an account. After that you can log into your account directly from ssh.

Use UTF-8 terminal encoding.

## Running the Server
``` diff
- IMPORTANT - Python >= 3.6.7 is required (Ubuntu >= 18.04 LTS)!
```
1. Update your system `sudo apt update && sudo apt upgrade`
2. Get the repo `git clone https://gitlab.com/bashrc2/AberMUSH`
3. CD into 'AberMUSH' and install the server `sudo ./installer.sh`

If you want to add a firewall which only allows logins via ssh or telnet:

``` bash
sudo cp /opt/abermush/firewall.nft /etc/firewall.conf
sudo apt -y install nftables
sudo nft -f /etc/firewall.conf
sudo echo '#!/bin/sh' > /etc/network/if-up.d/firewall
sudo echo 'nft flush ruleset' >> /etc/network/if-up.d/firewall
sudo echo 'nft -f /etc/firewall.conf' >> /etc/network/if-up.d/firewall
sudo chmod +x /etc/network/if-up.d/firewall
```

You now should be able to connect to your server on `<server IP/hostname>:35123`

![AberMUSH](docs/cat.png)

## Player Commands

All players can use the following commands:

``` text
bio [description]                       - Set a description of yourself
graphics [on|off]                       - Turn graphical content on or off
change password [newpassword]           - Change your password
who                                     - List players and where they are
quit/exit                               - Leave the game
eat/drink [item]                        - Eat or drink a consumable
speak [language]                        - Switch to speaking a different language
say [message]                           - Says something out loud
look/examine                            - Examines the surroundings
go [exit]                               - Moves through the exit specified
climb though/onto [exit]                - Try to climb through or onto an exit
move/roll/heave [target]                - Try to move or roll a heavy object
jump to [exit]                          - Try to jump onto something
attack/punch/kick/headbutt [target]     - Attack another player or NPC
throw [weapon] at [target]              - Throw a weapon at another player or NPC
shove/trip                              - Try to knock down a target during an attack
prone                                   - Lie down
stand                                   - Stand up
check inventory                         - Check the contents of your inventory
take/get [item]                         - Pick up an item
put [item] in/on [item]                 - Put an item into or onto another one
drop [item]                             - Drop an item
whisper [target] [message]              - Whisper to a player in the same room
tell/ask [target] [message]             - Send a tell message to another player or NPC
use/hold/pick/wield [item] [left|right] - Transfer an item to your hands
stow                                    - Free your hands of items
wear [item]                             - Wear an item
remove/unwear [item]                    - Remove a worn item
open [item]                             - Open an item or door
close [item]                            - Close an item or door
push [item]                             - Pushes a lever
pull [item]                             - Pulls a lever
affinity [player name]                  - Shows your affinity level with another player
cut/escape                              - Attempt to escape from a trap
step over tripwire [exit]               - Step over a tripwire in the given direction
dodge                                   - Dodge an attacker on the next combat round
```

## Chess Commands

![AberMUSH](docs/chess.jpg)

If you can find a chess board to play on:

``` text
chess                                   - Shows the board
chess reset                             - Rests the game
chess move [coords]                     - eg. chess move e2e3
chess undo                              - undoes the last move
```

## Cards

If you can find a deck of cards:

``` text
shuffle                                 - Shuffles the deck
deal to [player names]                  - Deals cards
hand                                    - View your hand of cards
stick                                   - Stick with your current hand
swap [card description]                 - Swaps a card
call                                    - Players show their hands
```

## Nine Men's Morris

If you can find a [Morris](https://en.wikipedia.org/wiki/Nine_men%27s_morris) board:

``` text
morris                                  - Show the board
morris put [coordinate]                 - Place a counter
morris move [from coord] [to coord]     - Move a counter
morris take [coordinate]                - Remove a counter after mill
morris reset                            - Resets the board
```

## Spell Commands

Some characters can use magic with the following commands:

``` text
prepare spells                          - List spells which can be prepared
prepare [spell name]                    - Prepares a spell
spells                                  - Lists your prepared spells
clear spells                            - Clears your prepared spells list
cast find familiar                      - Summons a familiar with random form
dismiss familiar                        - Dismisses a familiar
cast [spell name] on [target]           - Cast a spell on a player or NPC
```

Spells are defined within `spells.json` and the system for spellcasting is a simplified version of the one within conventional D&D games. You prepare a spell, it gets added to your list and then you can cast it and it disappears from the prepared list. Some spells require certain items to be in the player's inventory.

![AberMUSH](docs/lake.jpg)

## Witch Commands

Witches are the admins of the system, and have additional supernatural powers. The first user to create an account gains witch status. Additional witches may be assigned by appending them to the `witches` file, which is located in the same directory as `abermush.py` is run from.

``` text
close registrations                - Closes registrations of new players
open registrations                 - Allows registrations of new players
mute/silence [target]              - Mutes a player and prevents them from attacking
unmute/unsilence [target]          - Unmutes a player
freeze [target]                    - Prevents a player from moving or attacking
unfreeze [target]                  - Allows a player to move or attack
teleport [room]                    - Teleport to a room
summon [target]                    - Summons a player to your location
kick out/remove [target]           - Remove a player from the game
blocklist                          - Show the current blocklist
block [word or phrase]             - Adds a word or phrase to the blocklist
unblock [word or phrase]           - Removes a word or phrase to the blocklist
describe "room" "room name"        - Changes the name of the current room
describe "room description"        - Changes the current room description
describe "tide" "room description" - Changes the room description when tide is out
describe "item" "item description" - Changes the description of an item in the room
describe "NPC" "NPC description"   - Changes the description of an NPC in the room
conjure room [direction]           - Creates a new room in the given direction
conjure npc [target]               - Creates a named NPC in the room
conjure [item]                     - Creates a new item in the room
destroy room [direction]           - Removes the room in the given direction
destroy npc [target]               - Removes a named NPC from the room
destroy [item]                     - Removes an item from the room
resetuniverse                      - Resets the universe, losing any changes from defaults
shutdown                           - Shuts down the game server
```

### NPC Types

NPCs defined within `def/npcs.json` have a few different modes. The rooms which they can occupy are defined within the `path` list and the ways in which they move is defined by the `moveType` parameter. Movement types are:

 * *cyclic* - Move from the start to the end of the list of rooms
 * *inverse cyclic* - Move from the end to the start of the list of rooms
 * *random* - Move to random rooms in the list
 * *patrol* - Move from the start to the end of the list, then back again
 * *follow* - Look for players and follow them around
 * *leader:name* - Follow a named leader, which may be a player or NPC

If no `moveType` is specified then random movement is the default.

The speed at which NPCs move between rooms is defined by `moveDelay` and `randomFactor` parameters. RandomFactor just makes the delay between movements not completely predictable.

### NPC Presence

NPCs may be present at certain times of day or days of the year. To define this use the `moveTimes` list within `npcs.json`.

``` text
"moveTimes": [["hour",8,19],["day","saturday","sunday"],["inactive",1386]],
```

In the above example the NPC will be active between 8:00 (8am) and 19:00 (7pm) on the weekend and when inactive will be in room 1386. So for example a cleric might be present at a church only on Sunday between certain hours and then be at a monestary at other times. If the `inactive` list isn't specified then when inactive an NPC will go to a default purgatory room.

You can also use `moveTimes` within `items.json` to specify items which are only present at certain times. However, these must be items having a weight value of zero so that they can't be taken.

![AberMUSH](docs/crossbow.png)

### NPC Conversations

You can create simple kinds of conversations with NPCs by editing `npcs.json` and adding line entries within the `conv` parameter. For example:

``` text
"conv" : [
    [["serve","beer","?"], "Yes, of course"],
    [["serve","wine","?"], "We only serve the more disreputable wine"],
    [["have","order","like","beer","ale","drink","please"],"Here you go","give","114"],
    [["have","order","buy","purchase","trade","like","weapon","dagger","knife","please"],"This weapon may come in handy on your adventures","buy","624","1367"]
],
```

This uses a simple "bag of words" matching, so `serve` and `wine` could be in any order.

You can then tell the NPC something like:

``` text
ask inn-keeper Do you serve wine?
```

The system will then try to match words within your `ask` command and pick the most appropriate reply:

``` text
the old inn-keeper says: We only serve the more disreputable wine.
```

The NPC can also give an item if some words are matched, or exchange/buy/barter an item such as a gold coin for a small dagger. The numbers refer to item numbers within `items.json`.

Possible types of actions within NPC conversations are:

``` text
give [item ID]                       - Gives an item
teach [skill] [adjustment value]     - Adjusts a skill level
transport [room ID]                  - Moves the player to a different room
taxi [room ID] [itemID]              - Moves the player to a different room in exchange for an inventory item
date [dd/mm]                         - Conversation can only occur on a given day of the year
buy [obtain item ID] [give item ID]  - Obtains one item in exchange for another
experience [points]                  - Increase player experience
```

To show an image during a conversation:

``` text
"conv" : [
    [["have","order","like","beer","ale","drink","please"],"Here you go","image:givedrink","give","114"]
],
```

If an image then exists in `images/events` called `givedrink` then it will be shown when the conversation event happens.

If an NPC moves between rooms then you can make conversation lines dependent on being in a particular region.

``` text
"conv" : [
    [["what","you","doing","?","region=cave"],"I'm digging for gold"]
    [["what","you","doing","?","region=garden"],"I'm doing some gardening"]
],
```

Region names can be set within `rooms.json`, and could be for a single room or a group of rooms.

### Spoken Languages

Players and NPCs have their own languages: `common`, `dwarvish`, `elvish`, `draconic` and `druidic`. Goblins and humans may not be able to understand each other.

The language spoken and understood by NPCs can be defined with two parameters within `npcs.json`. `language` is a list of languages which the NPC understands and `speakLanguage` is the language which they are currently using to communicate.

``` text
"speakLanguage": "common",
"language": ["common","dwarvish"],
```

Players also have the same parameters and if they are multi-lingual then they can switch between languages using the `speak` command. For example:

``` text
speak common
speak dwarvish
```

### Stateful NPC Conversations

It may be useful for an NPC to keep track of the state of your conversation and it's possible to do this via state variables. There is only one conversation state variable per NPC/player combination and it can be named anything you like. For example:

``` text
"conv" : [
    [["order","beer","please"],"Free as in beer","state:beer given","give","114"],
    [["state:beer given","order","beer","please"],"Have another one then","give","114"]
],
```

Here whenever you ask for a beer the state variable `beer given` will be set for the NPC. If you subsequently ask for another beer the NPC gives a different response by matching the state variable. In this way you can have branching narratives dependent upon conversational context. Maybe an NPC only gives you some item after an appropriate sequence of dialogue.

### NPC Conversation conditions

It's also possible to add extra conditions to the conversation response selection.

``` text
"conv" : [
    [["order","ale","please"],"Have an ale!","state:beer given","give","114"],
    [["strength>90","order","ale","please"],"I'm sorry, we don't serve bodybuilders here."]
],
```
The variables available are the various player attributes: `level`, `experience`, `strength`, `size`, `weight` (of inventory carried), `perception`, `endurance`, `charisma`, `intelligence`, `agility` and `luck`. You can match multiple conditions if necessary.

![AberMUSH](docs/lava.jpg)

### Conditional Room Descriptions

You may want the description of a room to change if some condition is met. For example, within `rooms.json`:

``` text
"conditional": [
    ["hour","<2","The night's drinking is over and amidst occasional complaining the inn-keeper is kicking the remaining crowd out of this disreputable establishment. Displaced coasters, drug paraphenalia and cutlery remain strewn around. The door leading back out looks inviting."],
    ["hour","<10","Not much is going on within this disreputable establishment. It's dark, customers have been kicked out and the bar is empty. The inn-keeper is still around, cleaning up spilt ale, opium pipes, lost darts and randomly displaced cutlery. The door leading back out looks tempting."],
    ["date","25/12","Punters are engaging in festive celebrations in this disreputable boozing establishment. The inn-keeper looks busy behind the bar, and also slightly under the influence of the clouds of opium smoke wafting over from the merrymakers. The door leading back out looks tempting."],
    ["hold","114","You stare dispondently into your flagon of ale, but matters don't seem to improve. Is it worth drinking a beverage this cheap, you ask yourself. There's a door leading out."],
    ["hold","lightsource","The dark street is illuminated by the light you are holding."],
    ["rain","true","Puddles form in the street."],
    ["sunrise","true","You see the sun rise over the tops of the trees."]
    ["sunset","true","You see the sun set below the horizon."]
],
```

This provides different room descriptions in the morning to at other times.

Possible condition types are `hour`, `month`, `season`, `dayofweek`, `date`, `skill`, `rain`, `rainmorning`, `rainafternoon`, `rainevening`, `rainnight`, `sunrise`, `sunset`, `hold` and `wear`.

You can use this to do things like describing a dark cave by default but changing the description if you are holding a lamp, of having different descriptions for different seasons of the year.

``` text
"conditional": [
    ["season","spring","You are in an orchard with blossoming trees"],
    ["season","summer","Bright sunlight casts shadows through the trees"],
    ["season","autumn","The ground is covered with leaves."],
    ["season","winter","The trees look bleak and bare"]
],
```

Seasons in this system are not accelerated, so if it's summer where you are it will be summer in the MUSH.

If you want to specify a particular image which will show when a particular condition is true then you can add a fourth parameter which is a reference to the room image filename. For example:

``` text
    ["hold","lightsource","The dark street is illuminated by the light you are holding.","roomwithlight"]
```

This would correspond to the image within *images/rooms/roomwithlight*, and be shown instead of the usual room image when a light source is held.

In rooms which need a light source items won't be noticed until at least one player is holding a light source. Hence things can be hidden in the dark.

![AberMUSH](docs/door.png)

### Adding Doors and Opening things

To add a door, or other object to be opened or closed you will need a pair of items, like the following:

``` text
    "429": {
        "name": "old trapdoor",
        ...
        "state": "closed",
        "exitName": "up|down",
        "linkedItem": 430,
        "lockedWithItem": 0,
        "open_description": "As you push open the trapdoor bright light streams in.",
        "open_failed_description": "You try to open the trapdoor, but it's locked.",
        "close_description": "You close the trapdoor and it takes a few moments for your eyes to adjust to the darkness.",
        "exit": "$rid=433$"
    },
    "430": {
        "name": "old trapdoor",
        ...
        "state": "closed",
        "exitName": "down|up",
        "linkedItem": 429,
        "lockedWithItem": 0,
        "open_description": "You carefully lift open the trapdoor. It looks dark down there.",
        "open_failed_description": "You try to lift the trapdoor, but it's locked down.",
        "close_description": "You gently close the trapdoor",
        "exit": "$rid=431$"
    },
```

These are the same trapdoor as seen from two rooms. The `linkedItem` parameter links the two and the `exit` parameter defines which room to go to when going through. Exits called `down` and `up` are added if the trapdoor is open.

You should make some vague suggestion that these items can be opened within their `long_description` parameter.

If you need a key to open the door then specify the item number within the `lockedWithItem` parameter.

### Lever Operated Doors

It's possible to have doors which can't be manually opened but are lever operated.

To define a lever:

``` text
    "518": {
        "name": "ivory lever",
        "short_description": "There is an ivory lever set in the wall, next to the door.",
        "long_description": "It is highly polished, and the end is ornately carved in the shape of a skull. It is in the up position.",
        "state": "lever up",
        "open_description": "With great effort you yank the lever down",
        "open_failed_description": "It doesn't appear to have any handle",
        "close_description": "You push the lever up",
        "lockedWithItem": 0,
        "exitName": "east|west",
        "linkedItem": 526,
        "exit": "$rid=528$",
    },
```

Here `linkedItem` is the item number of the door which will be opened and `exit` is the room which it goes to. `exitName` defines the door as heading east from its location, with the opposite direction back to this location being west. The `state` variable can be `lever up` or `lever down`.

The door is then defined with:

``` text
    "526": {
        "name": "wooden door",
        "short_description": "The door is closed.",
        "long_description": "The old wooden door made from solid oak beams is closed.",
        "state": "closed",
        "lockedWithItem": 518,
        "exitName": "east|west",
        "linkedItem": 527,
        "exit": "$rid=528$",
    },
    "527": {
        "name": "wooden door",
        "short_description": "The door is closed.",
        "long_description": "The old wooden door made from solid oak beams is closed.",
        "state": "closed",
        "lockedWithItem": 520,
        "exitName": "west|east",
        "linkedItem": 526,
        "exit": "$rid=530$",
    }
```

`lockedWithItem` indicates that the door can only be opened with the lever with the given item number.

You can then use the following command to open the door:

``` text
pull ivory lever
```

You can get as devious as you like with this and have levers which open or close doors in some entirely different location, or one way doors which once shut with the lever can't be opened from the other side.

### Jumping

The *jump* command can be used to jump onto an item. For example, an item can be defined as follows:

``` text
    "1817": {
        "name": "precarious ledge",
        "short_description": "The precarious ledge is across the chasm",
        "long_description": "The precarious ledge is across the chasm",
        "jumpTo": "You take a running jump onto the ledge",
        "exit": "$rid=1835$",
        ...
```

The exit is the room to move to when jumping.

You can then use the command:

``` text
jump onto ledge
```

### Heaving/Rolling

Sometimes you want to move an item in a manner which isn't the same thing as opening.

``` text
    "2971": {
        "name": "tomb stone",
        "short_description": "A giant spherical stone covers the entrance to the tomb.",
        "long_description": "A giant spherical stone covers the entrance to the tomb.",
        "heave": "You roll the giant stone to one side and enter the tomb.",
        "exit": "$rid=4356$",
        ...
```

The exit is the room to move to when rolling.

You can then use the command:

``` text
roll the tomb stone
```

### Climbing through windows and boarding boats

You can add items to a room such as windows which the player can then climb through. Size restrictions apply and so this could be another way to escape from ogres or dragons. This can also be used to set up non-obvious exits as a puzzle, or for boarding boats.

``` text
    "1293": {
        "name": "large window",
        "short_description": "A huge window looks out across the snows.",
        "long_description": "It looks out over the snows. You could climb out of the window and down the snowbanks outside, providing of course they will take your weight. It is difficult to tell if they will though.",
        "climbThrough": "With considerable effort you scramble through the window.",
        "exit": "$rid=1294$",
        ...
```

The exit is the room to move to when climbing through.

You can then use the command:

``` text
climb through window
```

You can also make climbing conditional upon wearing a particular item.

``` text
    "1293": {
        "name": "ice wall",
        "short_description": "A huge wall of ice.",
        "climbWhenWearing": [7358, 6562],
        "climbThrough": "Wearing the ice boots you climb up the wall of ice.",
        "exit": "$rid=1294$",
        ...
```

If there are items in the room which the player might try to climb, but which aren't climbable then you can specify a failure message for that.

``` text
    "3713": {
        "name": "snowman",
        "short_description": "A giant snowman.",
        "long_description": "A giant snowman.",
        "climbFail": "You try to climb onto the snowman, but slip back down again.",
        ...
```

### Visibility

Some wearable items may allow the player to see things which are otherwise hidden. So for example wearing a certain necklace might allow you to see an ancester spirit or hidden treasure.

Within `items.json` and `npcs.json` the list called `visibleWhenWearing` can contain the ID numbers of wearable items. If the player is wearing any of the items in the list then they will be able to see the NPC or item.

![AberMUSH](docs/chest.png)

### Failing to take items

If an item has a weight of zero then it is fixed in place. If you want to provide a custom message when a player tries to take an item and fails then this can be specified within `items.json` with the parameter *takeFail*.

``` json
"517": {
    "name": "manacled skeleton",
    "long_description": "There is a skeleton chained to the wall.",
    "takeFail": "You try to remove the skeleton but it's firmly chained to the wall.",
    "weight": 0,
    ...
}
```

### Containers, Chests and Tables

Other than opening and closing doors you may also want to have items which can be opened or closed, and have things removed or put into them. For example a treasure chest containing gold coins. To define an item as openable the relevant attributes are similar to the following:

``` text
    "207": {
        "name": "clothes chest",
        ...
        "state": "container closed",
        "open_description": "Tiny moths flutter out as you open the clothes chest.",
        "close_description": "The clothes chest closes with a satisfying thud.",
        "contains": ["107","1386","1389","1390"],
        "useTimes": 10,
        "lockedWithItem": 0,
    },
```

The state of the item can be `container open` or `container closed`. You can then use commands such as:

``` text
open chest
examine chest
take hat from chest
wear hat
close chest
```

The `useTimes` parameter defines the maximum number of items which can be put into a container.

Similar to doors, items may be locked with another item which could be a key. Tables can be a special type of always open item.

``` text
    "1289": {
        "name": "inn table",
        ...
        "state": "container open always",
    },
```

You can then use a command such as:

``` text
put hat on table
```

It's also possible to have items which can be opened and closed but which can't have things put into them. Use `noput` within the state parameter to indicate this.


``` text
    "1289": {
        "name": "dusty book",
        ...
        "state": "container closed noput",
        "open_description": "A dust cloud emerges as you open the ancient tome.",
        "close_description": "You close the book and blow off some dust from its cover.",
    },
```

With commands such as:

``` text
open book
close book
```

### Consumables

Food or drink can be defined by setting `edible` to a non-zero value within `items.json`. If the value is negative then the item is a type of poison.

### Weather

The system includes a dynamic weather simulation with varying seasonal and daily temperatures, passing clouds and rain. The ambient weather conditions may affect your combat performance, especialy if you are wearing armor or carrying a lot of weight.

### Item activated exits

Some exits may be activated only when the player is wearing or holding a particular item. Within `rooms.json` you can add something like:

``` json
"exitsWhenWearing": [
    ["east","123","$rid=7160$"]
],
```

So that an exit to the east will become available when you are wearing the item with number 123. This is like holding open a portal which other players can then use even if they are not wearing the same item.

![AberMUSH](docs/tide.png)

### Tides

For coastal locations an optional alternative description may be entered into `tideOutDescription`. When the tide is in the default `description` parameter will be used.

It is also possible to specify exits which only become available when the tide is out, to implement [tidal islands](https://en.wikipedia.org/wiki/Tidal_island).

``` json
"tideOutExits": {
    "east": "$rid=7160$"
},
```

![AberMUSH](docs/combat.png)

### Players in Combat

Collecting weapons or armor will alter your chances of success in combat. In order to use a weapon you first need to be holding it. Merely having it in your inventory isn't enough for it to be effective. For example:

``` text
take dagger
hold dagger
```

You can also choose which hand.

``` text
hold dagger right
hold dagger left
```

With the possibility of using two weapons at the same time. However, some weapons require two hands to use and this is specified by the `bothHands` parameter in `items.json`.

Similar applies with armour:


``` text
take chainmail
wear chainmail
```

To see what you or other players are wearing or holding use the `bio` command or:

``` text
examine [player]
```

To start a fight you can then use the `attack` or `throw` commands. If you throw a weapon the damage it does may be higher but it may also then be picked up by any other player or NPC and used against you.

The `mod_str` parameter within an item which is a weapon defines how much damage it can inflict during combat. `mod_endu` defines how much protection a wearable item will provide against attacks.

There is a limit to how much weight you can carry and carrying or wearing a lot of heavy items will reduce your agility.

If you are attacked then your `hit points` will decrease. Rest, or the consumption of food or drink, can restore your hit points.

The type or armor which players (including NPCs) are wearing can also modify their agility, altering their combat performance. Agility values for armor items can be set with the `mod_agi` parameter. Negative values mean that wearing the item slows the player down. Positive values improve fighting performance.

While fighting you can use the `dodge` command to try to evade the attacker's next blow. You will miss a turn when trying to attack, but have less chance of being hit in the current round. Success in dodging depends on your `luck` and `agility`, which can vary depending upon items carried or worn and the weather/terrain.

### NPCs in Combat

NPCs are able to pick up and use any weapons or armor available in the vicinity. For some types of NPC, such as small animals, this isn't appropriate and so it's possible to set `canWear` and `canWield` parameters to zero within `npcs.json` if necessary.

### Parental Controls

If you don't want certain words or phrases to be used by players then you can create a file called `blocked.txt` containing them in the same directory that you run `abermush.py` from. Entries can be on separate lines or comma separated and the matching is case insensitive. This then alters the `say`, `tell` and `whisper` commands such that recipients won't receive messages containing blocked text.

You can also use the commands `block` and `unblock` to update the blocklist without restarting the server.

### Affinity Levels

The system keeps track of affinity levels between players, including between players and NPCs, via sentiment analysis and friendly or unfriendly actions. This enables NPCs to adjust their narrative based upon how friendly or hostile a player is towards them or other individuals which they know. For example:

``` text
"conv" : [
    [["affinity>0","serve","ale","?"], "Yes, of course"],
    [["affinity<0","serve","ale","?"], "Begone, scoundrel!"]
],
```

In some cases this may mean that you need to sufficiently charm an NPC before it will give you an item, skill or clue.

You can also see your affinity level with other players or NPCs with the command:

``` text
affinity [player name]
```

![AberMUSH](docs/familiars.png)

### Interacting with Familiars

Some characters can have familiars, which are arcane spirits in the form of an animal and with a telepathic link to the player who summons them. Familiars follow the player and can also be commanded to scout, hide or distract other players. They don't have much strength or intelligence and so can easily be killed, but can be summoned again if that happens. Every time a familiar is summoned it takes a random animal form.

To summon a familiar:

``` text
prepare find familiar
cast find familiar
```

or witches may use the `conjure` command:

``` text
conjure familiar
```

By default the familiar will follow you, or you can tell it to:

``` text
ask familiar to follow
```

You can have it scout around in the local area:

``` text
ask familiar to scout
```

or in a particular direction:

``` text
ask familiar to scout north
```

When scouting familiars will be visible and attackable by other players or NPCs.

Familiars are small and so can easily conceal themselves in obscure nooks and corners. To make the familiar hide:

``` text
ask familiar to hide
```

Once hidden a familiar will remain in place regardless of where the player moves. Only the player can see the familiar once it is hidden.

It is also possible to ask the familiar what it sees. Because it is a spirit from the arcane realm it is only able to describe the scene in abstract elemental terms. It can see other players and has a sense about whether they are friendly and how large they are.

``` text
ask familiar what do you see?
```

### Room height and capacity

Within `rooms.json` the parameters `maxPlayers` and `maxPlayerSize` can be used to define the maximum number of players which a room can contain (including NPCs) and also the height of the room. The numbers corresponding to player size are:

``` text
0 - Tiny (raven, cat, imp)
1 - Small (dwarf, halfling, goblin, gremlin)
2 - medium (human, elf, witch)
3 - Large (giant)
4 - Huge (ogre, dragon)
```

Thus you can have rooms which are accessible to halflings or familiars but not to humans, which could add an extra element to the story. Maybe certain rooms enable humans to escape from giants.

For small rooms you might want to only allow one or two players to occupy it at any point in time.

If these values are set to -1 then there are no limits on player size or numbers.

### Traps

Various kinds of traps can cause minor damage to players or prevent them from moving temporarily. After being activated they get reset again after a period of time.

To set a dart trap when exiting north within `rooms.json`:

``` text
"trap": {
    "trapType": "dart",
    "trapExit": "north",
    "trapPerception": 2,
    "trapActivation": "tripwire",
    "trapActivationProbability": 100,
    "trapActivationTime": 0,
    "trapActivationDescription": "",
    "trapEscapeMethod": "",
    "trapDamagedMax": 1,
    "trapDamaged": 0,
    "trapEscapeDescription": "",
    "trapDuration": "0 min",
    "trapPenaltyType": "hp",
    "trapPenalty": 10,
    "trapResetTime": "2 hours",
    "trappedPlayers": []
},
```

This causes a sting of up to 10 hit points. `trapPerception` specifies the minimum perception (`per` value in player json file) needed to see the trap, and it gets reset after two hours if activated. `trapActivationProbability` indicates that the trap always works 100% of the time when the tripwire is crossed.

To create a falling net trap activated by a pressure plate:

``` text
"trap": {
    "trapType": "net",
    "trapExit": "north",
    "trapPerception": 2,
    "trapActivation": "pressure",
    "trapActivationProbability": 100,
    "trapActivationTime": 0,
    "trapActivationDescription": "",
    "trapEscapeMethod": "slashing",
    "trapDamagedMax": 20,
    "trapDamaged": 0,
    "trapEscapeDescription": "",
    "trapDuration": "5 min",
    "trapPenaltyType": "hp",
    "trapPenalty": 0,
    "trapResetTime": "2 hours",
    "trappedPlayers": []
},
```

When the net falls on a player it will prevent them from moving for up to 5 mins. During that time they can try to cut themselves out if they are holding a `slashing` type weapon. They will need to do 20 points of damage to the net to escape. Hence with a sword it may be easy to break free, but with a small dagger it may take a while. If you're trapped by a net then other players or NPCs have an advantage when attacking you.

To create a tar pit trap activated when a player tries to move in a given direction:

``` text
"trap": {
    "trapType": "tar pit",
    "trapExit": "west",
    "trapPerception": 2,
    "trapActivation": "move",
    "trapActivationProbability": 40,
    "trapActivationTime": 0,
    "trapActivationDescription": "",
    "trapEscapeMethod": "wait",
    "trapDamagedMax": 99999,
    "trapDamaged": 0,
    "trapEscapeDescription": "",
    "trapDuration": "1 min",
    "trapPenaltyType": "hp",
    "trapPenalty": 0,
    "trapResetTime": "30 mins",
    "trappedPlayers": []
},
```

When you try to move west you will get stick in the tar pit 40% of the time. Once stuck the only thing you can do is to wait for one minute. Other possible traps are "ditch", "marsh" and "pit".

### Room images

These are 8 bit ANSI images, created using climage. They're derived from CC0 licensed images on https://free-images.com or Wikimedia.

To install:

``` bash
sudo apt install catimg
```

To convert an image:

``` bash
catimg -w 120 myimage.jpg > images/rooms/[rid]
```

The numbers should correspond to room ID or item ID.

You can also add a night time version of the image by appending _night to the filename.

``` bash
catimg -w 120 myimage.jpg > images/rooms/[rid]_night
```


![AberMUSH](docs/creators.png)

### Constructing the Universe

AberMUSH is already large by the standards of the late 1980s when AberMUD was originally developed, having about 600 rooms. But you don't have to stop there. Witches have the power to alter the universe arbitrarily by adding or removing rooms, items and NPCs interactively while the game is in progress. They can also change the descriptions.

To change the description of a room:

``` text
describe "This is a new description of the room."
look
```

You can also change the name of the room:

``` text
describe "room" "New room title"
```

To create and describe a new room:

``` text
conjure room south
go south
describe "room" "Cave Entrance"
describe "The cave entrance is narrow with rocks strewn around."
```

To remove the room just created:

``` text
go north
destroy room south
```

You can also create and remove items in a room:

``` text
conjure sword
destroy sword
```

And similar with NPCs:

``` text
conjure npc "Huge Ogre"
describe npc "The ogre is huge and angry looking."
destroy ogre
```

If you make any blunders then you can reset the universe back to its original state with the `resetuniverse` command, then restart the server.

### Markets

Different types of markets are defined within *def/markets.json*. If a room name matches a market type then it is possible to buy or sell within that room, using the *inventory* command to see what is on offer. The *sells* parameter indicates that certain items may only be sold within the market. The *trades* parameter indicates items which can be bought or sold.

### Culture and Regions

Each room can be assigned a region, and within *def/cultures.json* the regions for each culture can be defined.

Items can be assigned a culture so that if they are being sold within a market then the types of items can be culturally specific to the region.
