# Combat Mechanics in CNRD

## Overview

The combat system in Cyberpunk NetRunner: Digital Hunters (CNRD) is a turn-based battle system inspired by classic monster collecting RPGs. Battles take place between Daemons - digital entities that can be captured and trained by the player.

## Combat Initialization

Combat can be initiated in several ways:
- **Random encounters**: When moving between locations (chance based on the location's `encounter_rate`)
- **Scan command**: Using the "scan" command (improved encounter rate with minimum 60% chance)
- **Training battles**: Player-initiated practice battles with selectable difficulty levels
- **ACT command**: Directly interact with daemons in specific locations for unique encounters

### Scan Command Implementation
The scan command should:
- Generate a random encounter with 60% base chance + player's skill level modifier
- Allow player to specify a daemon type to search for (increasing chance of that specific type)
- Include validation to check if player has a healthy daemon before initiating combat
- Log scanning attempts for debugging purposes

### Training Battle Implementation
Training battles should:
- Allow player to select difficulty (Easy: -2 levels, Normal: same level, Hard: +2 levels)
- Let player choose opponent daemon type from a list or random selection
- Not allow capture (training daemons are simulations)
- Award reduced XP (75% of normal) but no risk of losing items
- Include proper error handling if selected daemon type is invalid

### ACT Command Implementation
The ACT command should:
- Allow player to interact with suspicious areas or objects that may contain daemons
- Trigger special encounters with rare or unique daemons not found through normal encounters
- Provide contextual interaction options based on environment and player skills
- Potentially bypass standard encounter calculations for scripted daemon appearances
- Include special dialogue or scene descriptions before combat initialization

When combat starts, the following occurs:
1. Enemy daemon is generated with appropriate level for the area
2. Player's first healthy daemon is automatically selected as active
3. Combat state changes from "roaming" to "combat"
4. Initial stats are displayed for both daemons

## Combat Flow

### Turn Sequence
1. **Display Status**: Show both daemons with their current HP, level, and status effects
2. **Player Action Selection**: Player chooses from Fight, Switch, Capture, or Run
3. **Enemy AI Decision**: Enemy daemon selects its action based on simple AI rules
4. **Turn Order Determination**: Based primarily on speed stat and status effects
5. **Action Execution**: Actions resolve in order of speed
6. **Status Effect Processing**: End-of-turn status effects are applied
7. **Faint Checking**: Check if any daemon has fainted and handle accordingly
8. **Repeat**: Continue until combat ends (victory, defeat, run, or capture)

### Turn Order
- Turn order is determined by comparing the `speed` stat of each daemon
- The daemon with higher speed acts first
- Status effects like "LAGGING" can modify turn order (LAGGING daemon always goes last)

### Player Actions

#### 1. FIGHT
- Player selects one of the active daemon's programs (attacks)
- The damage calculation formula is applied
- Type effectiveness and other modifiers are considered
- Hit/miss is determined based on program accuracy
- Status effects may be applied depending on the program

#### 2. SWITCH
- Player can switch to another conscious daemon in their roster
- Switching uses up the player's turn
- The new active daemon is protected until its turn

#### 3. CAPTURE
- Only available in wild daemon encounters
- Success rate is based on:
  - Base capture rate of the daemon species (lower is harder)
  - Current HP percentage (lower HP = higher chance)
  - Status effects (certain effects increase capture chance)
- If successful, the wild daemon is added to the player's roster
- If unsuccessful, the enemy daemon gets its turn

#### 4. RUN
- Attempt to escape from battle
- Success chance is based on speed comparison between player's and enemy daemon
- Base 90% chance modified by speed ratio
- Only works in wild encounters

### Enemy AI
The enemy daemon's behavior follows these rules:
- When at low HP (<30% of max), it selects its highest-power program
- Otherwise, it randomly selects from available programs
- If no programs are available, it uses a basic "struggle" attack
- Cannot run from battle or switch daemons (in wild encounters)

### Status Effect Restrictions
- **LOCKED**: 30% chance of being unable to act each turn
- **LAGGING**: Always acts last regardless of speed stat
- If a daemon cannot act due to status, its turn is skipped

## Damage Calculation

The damage calculation system incorporates multiple factors:

```
Base Damage = (((2 * level / 5) + 2) * program_power * (attacker_attack / target_defense)) / 50) + 2
Final Damage = Base Damage * STAB_Bonus * Type_Effectiveness * Random_Variance
```

Where:
- **STAB_Bonus** (Same Type Attack Bonus): 1.5x if the program type matches the attacker's type, otherwise 1.0x
- **Type_Effectiveness**: Multiplier based on program type vs defender type (from TYPE_CHART)
- **Random_Variance**: Random value between 0.85 and 1.0

### Type Effectiveness
Type effectiveness is determined using the TYPE_CHART defined in `daemon.py`:

```python
TYPE_CHART = {
    "VIRUS": {
        "VIRUS": 1.0,
        "FIREWALL": 0.5,
        "CRYPTO": 1.0,
        "TROJAN": 1.0,
        "NEURAL": 2.0,
        "SHELL": 1.0,
        "GHOST": 0.5
    },
    # Other types and their effectiveness relationships...
}
```

Examples:
- VIRUS is super effective against NEURAL (2.0x damage)
- VIRUS is not very effective against FIREWALL (0.5x damage)
- Some combinations may result in no effect (0x damage)

Messages display during combat to indicate effectiveness:
- "It's super effective!" (multiplier > 1.5)
- "It's not very effective..." (multiplier < 0.6)
- "It has no effect..." (multiplier = 0)

### Status Effects

Status effects can be applied during combat:

- **CORRUPTED**: Loses HP each turn (1/16 of max HP)
- **LOCKED**: 30% chance of being unable to act each turn
- **LAGGING**: Always acts last in turn order

Status effects influence:
- Turn order (LAGGING)
- Ability to act (LOCKED)
- HP over time (CORRUPTED)
- Capture success rates (all status effects improve capture chance)

## Capture Mechanics

The capture system uses a probability-based approach:

```python
hp_factor = (max_hp * 3 - current_hp * 2) / (max_hp * 3)
catch_chance = min(1.0, (base_rate / 255.0) * hp_factor * status_bonus)
```

Factors affecting capture rates:
- **Base Capture Rate**: Each daemon type has a base difficulty (lower value = harder to catch)
- **HP Factor**: Lower HP increases capture chance (maximum at 1/3 HP or less)
- **Status Bonus**: Status effects improve capture chance:
  - LOCKED: 2.0x bonus
  - CORRUPTED: 1.7x bonus
  - Other status effects: 1.5x bonus

The system displays the calculated catch chance to the player before making the attempt.

## Combat Outcomes

Combat can end in several ways:

1. **Player Victory** (`player_win`)
   - Occurs when all enemy daemons faint
   - XP is awarded to participating daemons (formula: enemy_level * 15)
   - Player daemons may level up if sufficient XP gained

2. **Player Defeat** (`enemy_win`)
   - Occurs when all player daemons faint
   - Player is returned to the last safe location (encounter_rate = 0)
   - All player daemons are automatically healed

3. **Run** (`run`)
   - Success chance based on speed comparison
   - Combat ends with no rewards if successful

4. **Capture** (`capture`)
   - Enemy daemon is added to player's roster if successful
   - Combat ends with no additional XP reward

## Leveling System

When daemons gain enough XP, they level up:

- Experience needed for next level: `100 + (level - 1) * 50`
- On level up:
  - Stats increase based on base stats and level multiplier
  - HP is fully restored
  - May learn new programs at certain levels

Stats are calculated with the following formula:
```python
level_multiplier = 1 + (level - 1) * 0.1
stat = int(base_stat * level_multiplier)
```

## Special Combat Features

### Auto-switching
If the player's active daemon faints mid-combat, the system:
1. Automatically checks for other healthy daemons
2. If none exist, the player loses the battle
3. Otherwise, prompts the player to select a new active daemon

### Status Effect Damage
Status effects like CORRUPTED apply damage at the end of each combat turn:
- Damage is calculated as 1/16 of the daemon's max HP
- If a daemon faints from status effect damage, the battle can end

### Struggle Attack
When a daemon has no programs available:
- Uses a basic "flailed wildly" attack
- Deals damage equal to attack / 4 (minimum 1)
- Has no type effectiveness considerations

## Future Combat Features

According to development logs, planned combat improvements include:
- XP sharing across all participating daemons
- Critical hit chance system
- More sophisticated status effects with varied durations
- Enemy daemon AI personality types (aggressive, defensive, strategic)
- Combo attacks for daemons with complementary types
- Environmental effects based on location
- Leveling milestones with special program choices
- NPC trainer battles with themed daemon teams