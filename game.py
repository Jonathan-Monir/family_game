import streamlit as st
import random

# --- Safe Initialization ---
if 'phase' not in st.session_state:
    st.session_state.phase = 'setup'
if 'players' not in st.session_state:
    st.session_state.players = []
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
        placeholder="Alice\nBob\nCharlie\nDavid"
    )

    if st.button("Distribute Roles"):
        # Parse roles
        roles = []
        for token in char_input.split(','):
            if ':' in token:
                name, count = token.strip().split(':')
                for _ in range(int(count.strip())):
                    roles.append(name.strip())

        # Parse players
        players = [p.strip() for p in players_raw.split('\n') if p.strip()]

        if len(players) != len(roles):
            st.error(f"Number of players ({len(players)}) must match the total roles ({len(roles)}).")
        else:
            random.shuffle(roles)
            st.session_state.roles = dict(zip(players, roles))
            st.session_state.players = players
            st.session_state.current = 0
            st.session_state.night_actions = {}
            st.session_state.phase = 'reveal'
            st.rerun()

# --- Reveal Phase ---
elif st.session_state.phase == 'reveal':
    players = st.session_state.players
    roles = st.session_state.roles
    current = st.session_state.current

    if current >= len(players):
        st.session_state.phase = 'night'
        st.session_state.current = 0
        st.rerun()
    else:
        player = players[current]
        st.title(f"{player}, hold the phone!")
        if st.button("Reveal your role"):
            st.info(f"**You are: {roles[player]}**")
        if st.button("Next Player"):
            st.session_state.current += 1
            st.rerun()

# --- Night Phase ---
elif st.session_state.phase == 'night':
    players = st.session_state.players
    roles = st.session_state.roles
    current = st.session_state.current

    if current >= len(players):
        # Resolve night actions
        mafia_target = st.session_state.night_actions.get('mafia')
        doctor_save = st.session_state.night_actions.get('doctor')

        st.title("🌙 Night Results 🌙")
        if mafia_target == doctor_save:
            st.success(f"{mafia_target} was attacked but saved by the doctor!")
        else:
            st.error(f"{mafia_target} was killed by the mafia.")

        if st.button("Play Again"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    else:
        player = players[current]
        role = roles[player]
        st.title(f"{player}, hold the phone")

        if st.button("Reveal your role"):
            st.info(f"**You are: {role}**")

            if role == 'mafia':
                target = st.selectbox("Choose someone to kill:", [p for p in players if p != player])
                if st.button("Confirm Kill"):
                    st.session_state.night_actions['mafia'] = target
                    st.session_state.current += 1
                    st.rerun()

            elif role == 'police':
                suspect = st.selectbox("Choose someone to investigate:", [p for p in players if p != player])
                if st.button("Confirm Investigation"):
                    if roles[suspect] == 'mafia':
                        st.success(f"{suspect} IS Mafia!")
                    else:
                        st.error(f"{suspect} is NOT Mafia.")
                    st.session_state.current += 1
                    st.rerun()

            elif role == 'doctor':
                save = st.selectbox("Choose someone to save:", players)
                if st.button("Confirm Save"):
                    st.session_state.night_actions['doctor'] = save
                    st.session_state.current += 1
                    st.rerun()

            elif role == 'likend':
                guess = st.selectbox("Guess who is the police:", [p for p in players if p != player])
                if st.button("Confirm Guess"):
                    if roles[guess] == 'police':
                        st.success(f"Correct! {guess} is the police.")
                    else:
                        st.error(f"Wrong! {guess} is not the police.")
                    st.session_state.current += 1
                    st.rerun()

            else:
                st.info("You are a citizen. You do nothing at night.")
                if st.button("End Turn"):
                    st.session_state.current += 1
                    st.rerun()
