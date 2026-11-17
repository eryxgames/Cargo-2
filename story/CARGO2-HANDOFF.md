# Cargo 2: what Cargo 3 inherits

Written by `tools/handoff.py` from the built story; do not edit by hand.

Cargo 2 has 113 story nodes, 14 characters and 26 flags; 23 flags are meant for Cargo 3. A captain record carries every flag that is set (up to 160, the carried ones first), the endings below, the achievements and the standings with the Hansa, the Mandate and the Concord.

## Endings and the segments

Each road's climax decides who holds the ring's segments when Cargo 3 begins (a flag in the record).

| Ending (record) | Road | Possible holders |
| --- | --- | --- |
| A Road Anyone Can Book (`trade`) | hansa | `segments_common`, `segments_hansa` |
| Every Jump Seen (`combat`) | mandate | `segments_common`, `segments_hansa`, `segments_mandate` |
| Through the Door (`discovery`) | door | `segments_common`, `segments_rostrom` |
| The Quiet Node (`dawn`) | dawn | `segments_dawn` |

| Holder flag | Means |
| --- | --- |
| `segments_common` | the segments are common ground in the Hansa's charter: watched by all, owned by none |
| `segments_hansa` | the Hansa holds the segments |
| `segments_mandate` | the Mandate holds the segments |
| `segments_rostrom` | House Rostrom and the Concord hold the segments |
| `segments_dawn` | the Binary Dawn keeps the segments' timing; nobody else can turn them |

## Promises owed to Cargo 3

| Promise | What |
| --- | --- |
| `the_warning` | 'Make sure it starts from home': the Gyrotron must be restarted from Sol, not from a faction's end of the ring. |
| `the_stonewright` | Stonewright comes back from the sublight run with Anselm's grandchild in command. |

## Flags carried to Cargo 3, by arc

### debts

| Flag | Means |
| --- | --- |
| `dawn_answered` | the captain answered the Binary Dawn when it first spoke |
| `lyra_log_given` | the captain gave the Lyra expedition the old signal log |
| `lyra_probe_sent` | the captain's own probe went quiet near the cold moon in Lyra |
| `lyra_warned` | the captain told the Lyra expedition the Maud Kettle's story |
| `ottavine_patron` | the captain took Conte Ottavine's first contract after she woke |
| `rock_listening` | the captain kept the colony's news to themselves and kept listening |
| `santor_hidden` | the captain hid Dharr Santor from the Mandate |
| `santor_with_hansa` | Dharr Santor went to the Hansa after he came back |
| `santor_with_rostrom` | Dharr Santor went to House Rostrom after he came back |

### hansa

| Flag | Means |
| --- | --- |
| `joined_late` | the captain joined the Hansa forty years after it was founded |

### ring

| Flag | Means |
| --- | --- |
| `saw_the_segment_turn` | the captain's needle was the last to see the first segment turn |

### road_dawn

| Flag | Means |
| --- | --- |
| `carried_nodes` | the captain carried machines out of the Mandate's census |
| `segments_dawn` | the Binary Dawn keeps the segments' timing; nobody else can turn them |

### road_door

| Flag | Means |
| --- | --- |
| `paid_with_the_pellet` | the captain paid for a young captain's drink with a Hansa Mark from before there were any |
| `segments_rostrom` | House Rostrom and the Concord hold the segments |
| `volunteered_for_the_door` | the captain volunteered to fly through the segment for House Rostrom |

### road_hansa

| Flag | Means |
| --- | --- |
| `bought_the_drive_vote` | the captain bought the votes that made the segments common ground |
| `ran_the_blockade` | the captain ran a needle through the Mandate's closed buoys |
| `segments_common` | the segments are common ground in the Hansa's charter: watched by all, owned by none |
| `segments_hansa` | the Hansa holds the segments |

### road_mandate

| Flag | Means |
| --- | --- |
| `segments_mandate` | the Mandate holds the segments |
| `sold_the_decoy` | the captain sold a Mandate decoy's schedule to pirates |
| `told_serac` | the captain told Serac what a segment does to clocks |

## Achievements in the record

| Id | Title | What it took |
| --- | --- | --- |
| `no_more_deadheads` | No more deadheads | twenty-five trades |
| `milk_run` | Milk run | a hundred trades |
| `steel_rain` | Steel rain | twenty-five fights won |
| `far_and_wide` | Far and wide | fifteen places visited |
| `bondholder` | Bondholder | five Hansa bonds |
| `full_train` | Full train | every grip of a Farstrider filled |
| `shiny_side_up` | Shiny-side up | a million credits |
| `hansa_own` | One of the Hansa's own | the Hansa's standing at 60 |
| `mandate_own` | One of the Mandate's own | the Mandate's standing at 60 |
| `concord_own` | One of the Concord's own | the Concord's standing at 60 |
| `keeps_things` | A captain who keeps things | the Binary Dawn's trust at 40 |
| `lot_1187` | Lot 1187 | the heading file opened |
| `eleven_years` | Eleven years early | a needle seen thrown into the past |
| `the_pellet` | The pellet | a drink paid for forty years ago |

## Characters who go on

| Character | In Cargo 3 |
| --- | --- |
| The captain | the player at the restart, or the name on a memorial |
| Anselm Rockwarden | a name on Stonewright's keel; Maret Rockwarden commands |
| Tylde Kren | her notes, or her upload |
| CU-113 | unchanged, several times over |
| Eela | still digging for Stonewright, if it was given a share |
| Conte Ottavine Kraal | awake for the restart, barely older |
| Magister Notary Augias Pfennig | a Pfennig still at the sarcophagus, by then nobody is sure which |
| Serac | unchanged; still asks after the captain |
