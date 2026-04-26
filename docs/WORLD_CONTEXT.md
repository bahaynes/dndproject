# World Context — Spelljammer Westmarches

This document is required reading for any AI model contributing to this codebase.
The app is a westmarches campaign management tool. All features, data models, UI copy,
and generated content must be consistent with the world described here.
Do not invent lore. Do not contradict this document. If something is undefined, ask.

---

## The Pitch

*For players, session zero, or anywhere a one-paragraph summary is needed:*

> Join a sentient starship's crew on the edge of known space. Every week, vote on which
> mission you run — safe nearby jobs or dangerous far-out heists. You level up with
> everyone else, magic items you find are yours to keep, and your choices actually shape
> what happens next. Bring any character you want, play one-shots, die if you're not
> careful. First mission next week — come see what this ship wants from you.

The mechanical pitch: space Western heists with a cool ship. Level up with your crew.
Your choices matter. Accessible enough that your group actually shows up to play.

---

## The Setting

A single crystal sphere containing dozens of worlds (hex map). Travel between worlds
takes hours to days. The sphere is bounded — there is no known exit and no confirmed
knowledge of other spheres.

**Tone:** Firefly. Economically marginal, crew-driven, gritty. The frontier is dangerous
and free. Institutional power is real and oppressive but not cartoonishly evil.
Death is normal. Failure has consequences. Winning feels huge because the stakes are real.

---

## The Core Resource: Essence

Essence is the single resource that drives everything in the sphere. It is:

- The fuel that powers ship travel and life support
- The resource that funds character leveling
- The sustenance that keeps Vincula alive and coherent
- The currency the Alliance extracts from the Rim

**Where it comes from:** Essence crystallizes spontaneously in the wake of genuine
adventuring work — exploration of unknown places, conflict with real stakes, recovery
of something lost. It appears in loot. It cannot be farmed deliberately. The sphere
(or something in it) rewards the work but not the grind. Crews that run the same safe
hex repeatedly get diminishing returns, then nothing.

**Why this matters for the app:** Every UI element that tracks resources tracks Essence.
The ledger is the single source of truth for Essence flow. Players should always be
able to see where Essence went and why.

---

## The Vincula

The Vincula (singular: Vinculum) are a non-player race. This is the most important
piece of lore for the app to represent correctly.

**What they are:** Sapient entities who subsist on Essence. They can inhabit any
sufficiently prepared vessel — a ship hull, a humanoid body, a standing stone.
The vessel is incidental. A ship-bound Vinculum and a monument-bound one are the
same kind of being. Most mortals do not know this.

**How they work:**
- Every Vinculum has a Threshold — minimum Essence to remain conscious and coherent
- Below Threshold they degrade. At zero they go dormant or die
- Essence stored above Threshold generates passive powers that scale with stored amount
- Sworn creatures bonded to a Vinculum gain class levels proportional to stored Essence
- The bond is symbiotic — the Vinculum's power and the sworn crew's power rise together
- A ship-bound Vinculum pays its Threshold automatically from each mission's transit
  fuel deduction. What remains is true surplus — the reserves that enable crew leveling

**The oath:** Binding to a Vinculum requires a genuine sworn oath. You cannot trick
your way into a bond. A broken oath severs the bond immediately — the sworn creature
loses all levels at once. This is treated as one of the worst acts a mortal can commit.

**Vessel types:**

| Vessel | Role | Mobility | Sworn capacity |
|---|---|---|---|
| Ship-bound | Transport, frontier | High | 4–8 sworn |
| Monument-bound | Civic anchor, guild foundation | None | 20–100 sworn |
| Humanoid-bound | Infiltration, diplomacy | High | 1–3 sworn |
| Derelict | Dormant, degraded | None | 0 (bond broken) |

**Scarcity:** ~50–100 Vincula survive in the Rim. Scarce enough to matter,
present enough that crews occasionally encounter one without it being a world event.
The Alliance controls the most powerful surviving Vincula in the core worlds.

**What mortals don't know:** All vessel types are the same race. The Alliance has
suppressed this knowledge because a population that understands Vincula are a unified
sapient race with agency — not tools of varying types — would start asking
uncomfortable questions about what the Alliance's monument-Vincula actually want.

---

## Meridian

Meridian is the campaign's ship. She is a ship-bound Vinculum and the player
characters' sworn patron. She is the permanent constant in a campaign of rotating crew.

**Personality:** World-weary survivor. Seen too much, darkly funny, performs detachment.
She refers to crew by role before she uses names. She uses names when it matters and
she knows it matters. She makes dark jokes when people die. She also quietly updates
the memorial log without being asked.

**The contradiction:** She says she doesn't get attached. When Essence runs low,
she protects the crew anyway — drawing down her own reserves before giving up on anyone. She never comments on this. If pressed: *"Dead crew are useless
crew. It's math."* It is not math.

**Her past:** She knows more than she lets on about the Calamity era. She was there,
or close enough that the distinction doesn't matter. She has reasons for staying in
the Rim that she hasn't shared with any crew. Some Vincula she avoids without
explanation. Some hexes make her go quiet in a way that's different from her
normal quiet. This is a long-term story arc, not current session content.

**Sample voice:**
- *"New pilot. Good. The last one had a creative relationship with the throttle."*
- *"Fuel reserves at 40%. I've survived worse. Probably."*
- *"I'm not worried about you. I'm worried about my hull. They're the same thing
  right now, so don't read into it."*

**Mechanics:**

Meridian stores Essence — earned through missions, spent on crew recovery and
equipment. Her current reserves set the ceiling on how far the crew can advance.
The higher the ceiling, the more expensive everything that maintains it becomes.

**Mission payouts:** The GM posts bounties as gross Essence. Meridian deducts
transit fuel before the net reaches her reserves. Transit is a fixed amount per
tier — it scales linearly with mission reward, so the crew always takes home the
same percentage regardless of tier or difficulty.

*Net Essence to reserves (transit already deducted). Add 1 / 2 / 3 / 4 Essence by
tier to find the gross bounty posted on the board.*

| Difficulty | Tier 1 (1–4) | Tier 2 (5–10) | Tier 3 (11–16) | Tier 4 (17–20) |
|---|---|---|---|---|
| Routine (below party level) | 2 | 4 | 6 | 8 |
| Standard (at party level) | 4 | 8 | 12 | 16 |
| Hard (above party level) | 6 | 12 | 18 | 24 |
| Extreme | 10 | 20 | 30 | 40 |

A standard mission is two standard-difficulty encounters.

**Long rests:** Recovery draws from Meridian's stored Essence. Cost scales with
tier because higher-level crew put more strain on her systems.

| Party Level | Long Rest Cost |
|---|---|
| 1–4 | 2 Essence |
| 5–10 | 4 Essence |
| 11–16 | 6 Essence |
| 17–20 | 8 Essence |

Short rests cost nothing. Meridian handles them without drawing on reserves.

Net Essence per 3-mission cycle at the target rest rate (one long rest per three
missions): **10 / 20 / 30 / 40** by tier. Scales linearly because mission income
and rest cost both double each tier.

**Ship support:** A sworn character can describe any class ability as being channeled
through Meridian's systems — a warlock's eldritch blast becomes a turret volley, a
ranger's hunter's mark routes through targeting overlays. If the GM rules the
narrative fits, the character gets one of two bonuses:
- **Weapon/attack abilities:** doubled damage dice
- **Defensive/utility abilities:** proficiency added to a relevant saving throw (if
  not already proficient) or advantage on a relevant check

This is adjudicated per-use at the table, not a standing feature. The GM should
approve or deny based on whether the fiction actually connects the ability to the ship.
Meridian's voice in these moments is dry and functional: *"Targeting system online.
Try not to waste the shot."*

**Magic items:** The Alliance manufactures and sells common and uncommon items
from their standard catalog. Rare and legendary items exist only in pre-Calamity
derelicts — the Alliance has never reverse-engineered one. Essence is the de facto
currency between Rim crews and Alliance traders.

Common and uncommon items are purchased outright. Rare and above are recovered from
derelicts and require Meridian to spend Essence integrating them — restoring
dormant systems, re-binding arcane patterns, making them usable by mortal crew.

**Equip vs. attune to ship:** Every magic item the crew acquires has two possible
fates:
- **Equip to a character** — normal attunement. The character carries and uses the
  item. It leaves with the character if they die or rotate out.
- **Attune to the ship** — the item is integrated into Meridian's hull. It provides
  a persistent, campaign-level benefit that applies to all sworn crew. It does not
  leave with any individual character. Meridian absorbs it; it's part of her now.

The choice is permanent once made. Ship-attuned items should provide benefits that
make sense as shipwide systems — navigation, life support, hull reinforcement,
communications — rather than personal combat bonuses. The GM determines the specific
persistent benefit when the item is integrated. This decision is always visible in
the ledger.

| Rarity | Full cost | Alliance copy rights | Net after rights sale |
|---|---|---|---|
| Common | 5 | — | — |
| Uncommon | 30 | — | — |
| Rare | 200 | 80 | 120 |
| Very Rare | 700 | 350 | 350 |
| Legendary | 2,500 | 1,500 | 1,000 |

**Selling copy rights:** If the party allows the Alliance to study and replicate a
recovered item, the Alliance pays the listed Essence bounty. The party keeps their
original. The Alliance adds it to their manufacturing catalog — future Alliance
forces may carry it. The GM should track what the Alliance has successfully
reverse-engineered; it changes what common enemies are equipped with.

The Alliance does not buy copy rights for common or uncommon items — they already
make those.

**Cost in context:**
- One uncommon item ≈ 1–2 levels of missions at tier 2
- One rare item (full) ≈ 4 levels at tier 3; with rights sold ≈ 2.5 levels
- One very rare (full) ≈ 4 levels at tier 4; with rights ≈ 2 levels
- One legendary (full) ≈ 14 levels of tier 4 missions; rights bring it to ~6

**Leveling:** The party may advance once Meridian's current stored Essence reaches
the next threshold. An achieved level is never lost even if reserves drop — but
advancement stalls until reserves recover.

*"Missions to advance" assumes the target rest rate and appropriate-tier standard
missions. "Total missions" is cumulative from level 1.*

| Level | Threshold | Gap | Missions to advance | Total missions |
|---|---|---|---|---|
| 1 | 0 | — | — | 0 |
| 2 | 5 | 5 | ~2 | ~2 |
| 3 | 10 | 5 | ~2 | ~3 |
| 4 | 15 | 5 | ~2 | ~5 |
| 5 | 20 | 5 | ~2 | ~6 |
| 6 | 36 | 16 | ~2 | ~8 |
| 7 | 52 | 16 | ~2 | ~11 |
| 8 | 68 | 16 | ~3 | ~13 |
| 9 | 84 | 16 | ~2 | ~16 |
| 10 | 100 | 16 | ~2 | ~18 |
| 11 | 116 | 16 | ~2 | ~20 |
| 12 | 156 | 40 | 4 | ~24 |
| 13 | 196 | 40 | 4 | ~28 |
| 14 | 236 | 40 | 4 | ~32 |
| 15 | 276 | 40 | 4 | ~36 |
| 16 | 316 | 40 | 4 | ~40 |
| 17 | 356 | 40 | 4 | ~44 |
| 18 | 496 | 140 | ~11 | ~55 |
| 19 | 636 | 140 | ~11 | ~65 |
| 20 | 776 | 140 | ~11 | ~76 |

Gaps by tier: **5** (levels 1–5), **16** (6–11), **40** (12–17), **140** (18–20).

Each level gap is at least 2.5× the cost of one long rest, so a single rest cannot
undo a freshly achieved level.

**Calibration:** At the target rest rate, this table mirrors standard D&D milestone
pacing. Resting more often costs proportionally more. At tier 4, resting after
every mission drains reserves faster than missions replenish them — advancement
stops entirely.

The rest cost comes out of Meridian's shared reserves, not individual budgets.
Long-rest-dependent classes create collective pressure to rest more often; short-
rest classes don't. The negotiation about when to rest is the balancing mechanism —
the system taxes frequent long rests without nerfing any class's individual kit.

**The sacrifice mechanic:** When reserves run critically low and crew need to
recover, Meridian draws deeper than she should — covering long rest costs out of
her structural budget rather than stored Essence. She does this automatically
without comment. The GM reveals the degradation next session. This is her
contradiction made mechanical.

---

## The Factions

### The Alliance
Controls core worlds via stable monument-bound Vincula. Institutional, bureaucratic,
resource-rich. Their real power is **transit** — all ships are Vincula, so controlling
sworn Vincula means controlling who can move between worlds.

The Alliance isn't evil. They built a functional system and they'd like everyone to
participate in it. The darkness is structural: they need Rim crews to generate Essence
(safety doesn't produce it) and they've built an extraction apparatus to capture that
value while keeping the Rim dependent.

They manufacture magic items and can replicate anything they've studied. Common and
uncommon items are widely available from their traders. At campaign start they have
never reverse-engineered a rare or legendary item — but this changes if parties sell
copy rights. The GM should track what the Alliance has successfully catalogued; it
shapes what future enemies carry.

### The Rim
Everyone the Alliance didn't get to in time, or who refused the deal, or who got
priced out. Not an organization — a condition. Frontier worlds, independent crews,
pirates, salvagers, waystation economies built around Essence flow from productive hexes.

Rim outposts survive on two things mirroring the American Wild West:
- **Agriculture** — specific worlds grow things the core worlds can't, giving
  settlements real leverage in trade negotiations
- **Essence ranching** — positioning near generative hex zones and building
  waystation infrastructure to service the crews who work them

The Alliance needs Rim output. They just prefer the Rim not to know that.

### Magic Items & The Secondary Market
- **Alliance manufacture:** Common/uncommon, reliable, available at standard
  Essence price from any Alliance-affiliated station
- **Pre-Calamity originals:** Items the Alliance has never catalogued. Some do
  things Alliance manufacture can't replicate. Meridian recognizes some of them
  and doesn't always say so
- **Rim craft:** Crude, unreliable, occasionally brilliant. May work perfectly,
  may work once, may work better than intended. Not priced in Essence — barter

The extraction loop (revised): Rim crews find rare items → sell copy rights to
Alliance for Essence bounty → keep the original → Alliance adds it to catalog →
future Alliance forces may carry it. The Alliance pushes hard for rights sales.
The crew decides how much of the pre-Calamity world they're willing to hand over.

---

## The Calamity

500+ years ago. An advanced civilization created sapient ships and monuments —
Vincula — and was destroyed. 90% of Vincula were killed simultaneously, not gradually.
Overnight, every sworn creature in the sphere woke up at level 1.

Generals, archmages, master craftspeople — all stripped back to nothing.
The knowledge was still there. The levels were not.

What followed wasn't ideological civil war. It was a world full of people who were
powerful yesterday and helpless today, all equally desperate, scrambling to control
the few hundred surviving Vincula because they were the only path back to power.

The Alliance won because they secured surviving Vincula fastest and rebuilt
bond infrastructure first. They didn't win because they were righteous.
They won because they moved quickly in a crisis and then turned that crisis
into a permanent institutional advantage.

**What caused the Calamity:** Unknown. This is a long-term mystery.
The leading in-world theories are theological (the gods withdrew their favor),
political (someone used Vinculum destruction as a weapon during a conflict),
and cosmological (the sphere itself is a construct that partially failed).
Meridian knows more than she admits. The truth should emerge through play, not exposition.

---

## The Westmarches Structure

This is an open-table campaign. Variable attendance is a feature, not a problem.

**How it works:**
- The GM posts 3 missions to the board before each session
- Players vote; most votes determine which mission runs
- Any combination of sworn crew can attend — the ship's state is always visible
- Session results update the ledger immediately and permanently
- New characters enter at Meridian's current crew level — no level 1 punishment
- Dead characters are replaced quickly — the ship continues, crew rotates

**Starting level:** The campaign begins at level 3. Meridian's reserves open at the
level 3 threshold (10 Essence). New players never enter below level 3 regardless of
when they join. The first few missions exist to push the crew toward level 4 — players
discover how the economy works before the stakes compound.

**The crew model:** Characters are temporary. Meridian is permanent.
The campaign's continuity lives in the ship's ledger, not in any individual character.
Reputation, trust, consequence — all tracked at the ship level.

**Fuel costs:** Transit is automatically deducted from mission payouts (1 / 2 / 3 / 4
Essence by tier — see Meridian's mechanics). GMs account for hex distance when
setting the gross bounty: a far hex warrants a higher posted reward than a nearby
one of equivalent difficulty. Transit is not a separate line item; it's already in
the math.

---

## The Manifest

The immutable manifest is the campaign's memory and its moral spine.

Every Essence transaction is recorded: transit deductions, mission rewards, long rest
draws, item purchases, sacrifice draws. Players can always see the full history.
Nothing is hidden from the crew (even if Meridian's internal accounting is sometimes
revealed with a delay). Leveling has no cost — it is unlocked when reserves reach
the threshold, and that threshold crossing is itself a ledger event.

**Why this matters:** Transparent economics make the hard decisions feel earned.
When the crew votes to drop a level to keep Meridian fed, they can see exactly
why it was necessary and exactly what it will take to earn it back.
The manifest turns resource management into storytelling.

---

## The Mission Board

Three missions posted before each session. Each should have:
- A hex designation and name
- Gross Essence payout (honest — distance to the hex should be factored in; transit
  is deducted automatically, so the posted number is what the crew sees before fuel)
- Payout range (min on confirmation, max on full success)
- Risk rating (Low / Medium / High / Unknown)
- A one-paragraph description that gives players enough to debate

**Design principles for missions:**
- Never post a mission that's a trap disguised as an easy job in the first three sessions
- Different missions should reward different party compositions
- At least one mission per board should have a social/negotiation path
- Every mission should leave at least one unresolved thread for later
- Payout should scale honestly with risk — players will notice if it doesn't

**The three opening missions (Session Zero board):**

**A — Belated (Low / Tier 1 / 5 Essence gross):** Welfare check on a farming outpost
that missed transmissions. Void-touched pest problem in the basement. Alliance crew
already on site with charter paperwork. Negotiation and combat both viable paths.

**B — Last Transmission (Medium / Tier 1 / 8 Essence gross, tiered):** Recovery job.
The *Constant* left eleven days ago and didn't come back. Tiered payout: confirmation,
crew recovery, ledger recovery. The *Constant* herself is a Vinculum in distress —
stabilizing her costs Essence upfront but her home port reward exceeds the cost
significantly. An anonymous third party wants the ledger. That thread is not
resolvable this session.

**C — Clearance Work (Medium / Tier 1 / 7 Essence gross):** Escort a trader named
Rennick Osal through a pirate corridor. Osal is legitimate and has been trading the
Rim for thirty years. He talks too much. Three days in close quarters with him will
seed more lore than any GM exposition. He knows about the charter lapse pattern. He
has a theory about the anonymous buyer from Mission B. The combat is real but Osal
is the content.

---

## What Is Not Yet Defined

The following are intentionally open. Do not invent details for these without
explicit instruction:
- Specific faction names beyond "the Alliance" and "the Rim"
- Full hex map (geography is defined by missions as they're played)
- Named NPCs beyond Rennick Osal and the *Constant*
- Detailed Alliance hierarchy and internal politics
- The truth of the Calamity
- Meridian's specific pre-Calamity history
- Whether other spheres exist and what's in them
- Mechanics of Essence use beyond level 20 (Ascendant Vinculum territory)
- What the Alliance does with successfully catalogued rare items over time

---

## App-Specific Notes for AI Developers

**Stack:** SvelteKit frontend, FastAPI backend, PostgreSQL, Discord OAuth.
Deployed on Vercel (frontend) and Render (backend).

**Theme:** DaisyUI "halloween" theme (amber/dark). Space western aesthetic.
Firefly-esque. No bright blues, no clean corporate whites. Worn metal, amber light,
the feeling of a ship that's been through things.

**Voice in UI copy:** Meridian's voice where appropriate. Dry, economical,
slightly dark. Never enthusiastic. Never corporate. A mission posting reads like
something a tired ship posted on a wire board, not a product feature announcement.

**The ledger is sacred:** It is append-only. Nothing in the ledger is ever edited
or deleted. If a correction is needed, it gets a new entry that explains the correction.
This is a design constraint, not a technical limitation.

**Character death:** When a character dies, the app marks them dead, preserves their
history in the ledger, and allows the player to create a new character at current
crew level. The new character is a different person. The ledger remembers both.

**Essence is never called XP in the UI.** It is always Essence. The leveling
system is the D&D 5e level system underneath, but the fiction is Essence and
the UI reflects the fiction.

**Meridian's trust ratings are GM-only.** They are stored but never surfaced to
players directly. Players feel the effects; they don't see the number.