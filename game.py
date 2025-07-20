import streamlit as st
import random

# --- Safe Initialization ---
if 'phase' not in st.session_state:
    st.session_state.phase = 'setup'
if 'players' not in st.session_state:
    st.session_state.players = []
if 'alive' not in st.session_state:
    st.session_state.alive = []
if 'roles' not in st.session_state:
    st.session_state.roles = {}
if 'current' not in st.session_state:
    st.session_state.current = 0
if 'night_actions' not in st.session_state:
    st.session_state.night_actions = {}

# --- Setup Phase ---
if st.session_state.phase == 'setup':
    st.title("Mafia Game Setup")

    char_input = st.text_area(
        "Enter roles (e.g., mafia:1, police:1, doctor:1, likend:1, citizen:2)",
        placeholder="mafia:1, police:1, doctor:1, likend:1, citizen:2"
    )
    players_raw = st.text_area(
        "Enter player names (one per line)",
        placeholder="Alice\nBob\nCharlie"
    )

    if st.button("Distribute Roles"):
        # Parse roles
        roles_list = []
        for token in char_input.split(','):
            if ':' in token:
                name, cnt = token.strip().split(':')
                for _ in range(int(cnt)):
                    roles_list.append(name.strip())
        # Parse players
        players = [p.strip() for p in players_raw.split('\n') if p.strip()]
        if len(players) != len(roles_list):
            st.error(f"{len(players)} players but {len(roles_list)} roles—please match counts.")
        else:
            random.shuffle(roles_list)
            st.session_state.players = players
            st.session_state.alive = players.copy()
            st.session_state.roles = dict(zip(players, roles_list))
            st.session_state.phase = 'reveal'
            st.session_state.current = 0
            # move on
            st.rerun()

# --- Reveal Phase (Secret Role Reveal) ---
elif st.session_state.phase == 'reveal':
    players = st.session_state.players
    roles = st.session_state.roles
    idx = st.session_state.current

    if idx >= len(players):
        st.session_state.phase = 'night'
        st.session_state.current = 0
        st.rerun()
    else:
        player = players[idx]
        st.title(f"{player}, hold the phone")
        if st.button("Reveal your role"):
            st.info(f"**You are: {roles[player]}**")
        if st.button("Next Player"):
            st.session_state.current += 1
            st.rerun()

# --- Night Phase ---
elif st.session_state.phase == 'night':
    alive = st.session_state.alive
    roles = st.session_state.roles
    idx = st.session_state.current

    # Initialize per-player night flags
    if 'revealed' not in st.session_state:
        st.session_state.revealed = {}
    if 'action_done' not in st.session_state:
        st.session_state.action_done = {}
    if 'action_result' not in st.session_state:
        st.session_state.action_result = {}

    # 1) Win conditions
    mafia_alive = sum(1 for p in alive if roles[p] == 'mafia')
    num_alive = len(alive)
    if mafia_alive == 0:
        st.balloons()
        st.success("All mafia are dead. Citizens win! 🎉")
        if st.button("Restart"):
            st.session_state.clear()
            st.rerun()
        st.stop()
    if mafia_alive >= num_alive - mafia_alive:
        st.error("Mafia have taken over. Mafia win! 🏴")
        if st.button("Restart"):
            st.session_state.clear()
            st.rerun()
        st.stop()

    # 2) After all have acted: resolve night, remove victim, loop
    if idx >= len(alive):
        target = st.session_state.night_actions.get('mafia')
        save   = st.session_state.night_actions.get('doctor')
        st.title("🌙 Night Results 🌙")
        if target == save:
            st.success(f"{target} was attacked but saved by the doctor!")
        else:
            st.error(f"{target} was killed by the mafia.")
            alive.remove(target)
        if st.button("Next Round"):
            # reset for next cycle
            st.session_state.current = 0
            st.session_state.night_actions.clear()
            st.session_state.revealed.clear()
            st.session_state.action_done.clear()
            st.session_state.action_result.clear()
            st.rerun()
    else:
        # 3) Per-player private turn
        player = alive[idx]
        role   = roles[player]
        st.title(f"{player}, hold the phone")

        # Reveal step
        if not st.session_state.revealed.get(player, False):
            if st.button("Reveal your role"):
                st.session_state.revealed[player] = True
                st.rerun()
        else:
            st.info(f"**You are: {role}**")

            # Action step
            if not st.session_state.action_done.get(player, False):
                # Mafia kill
                if role == 'mafia':
                    choice = st.selectbox("Choose someone to kill:", [p for p in alive if p != player])
                    if st.button("Confirm Kill"):
                        st.session_state.night_actions['mafia'] = choice
                        st.session_state.action_result[player] = f"You chose to kill {choice}."
                        st.session_state.action_done[player] = True
                        st.rerun()

                # Police investigate
                elif role == 'police':
                    suspect = st.selectbox("Choose someone to investigate:", [p for p in alive if p != player])
                    if st.button("Confirm Investigation"):
                        is_m = roles[suspect] == 'mafia'
                        res = f"{suspect} is {'Mafia' if is_m else 'Not Mafia'}!"
                        st.session_state.action_result[player] = res
                        st.session_state.action_done[player] = True
                        st.rerun()

                # Doctor save
                elif role == 'doctor':
                    save = st.selectbox("Choose someone to save:", alive)
                    if st.button("Confirm Save"):
                        st.session_state.night_actions['doctor'] = save
                        st.session_state.action_result[player] = f"You chose to save {save}."
                        st.session_state.action_done[player] = True
                        st.rerun()

                # Likend guess police
                elif role == 'likend':
                    guess = st.selectbox("Guess who is the police:", [p for p in alive if p != player])
                    if st.button("Confirm Guess"):
                        is_p = roles[guess] == 'police'
                        res = f"{guess} is {'Police' if is_p else 'Not Police'}!"
                        st.session_state.action_result[player] = res
                        st.session_state.action_done[player] = True
                        st.rerun()

                # Citizen does nothing
                else:
                    st.info("You are a citizen. You do nothing.")
                    if st.button("End Turn"):
                        st.session_state.action_result[player] = "You did nothing."
                        st.session_state.action_done[player] = True
                        st.rerun()

            # Result & Continue
            else:
                st.write(st.session_state.action_result[player])
                if st.button("Continue"):
                    # advance turn
                    st.session_state.current += 1
                    # reset flags for next player
                    st.session_state.revealed[player] = False
                    st.session_state.action_done[player] = False
                    st.session_state.action_result[player] = ""
                    st.rerun()
