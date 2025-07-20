import streamlit as st
import random

# --- Page config & styling ---
st.set_page_config(
    page_title="🕵️ Mafia Night",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
  background: url('https://images.unsplash.com/photo-1524567496280-30c409fc0772?auto=format&fit=crop&w=1500&q=80') no-repeat center center fixed;
  background-size: cover;
}
[data-testid="stSidebar"], .css-18e3th9 {
  background-color: rgba(0, 0, 0, 0.6) !important;
  color: #fafafa !important;
}
h1, h2, h3 { color: #ffcc00; text-shadow: 1px 1px 2px #000; }
button { background-color: #333 !important; color: #ffcc00 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center'>🎭 Welcome to Mafia Night 🎭</h1>", unsafe_allow_html=True)

# --- Initialization ---
for key, default in [
    ('phase', 'setup'),
    ('players', []),
    ('alive', []),
    ('roles', {}),
    ('current', 0),
    ('night_actions', {}),
    ('vote_results', {}),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# Helper: card container
def card(title, content):
    st.markdown(f"""
    <div style="
      background: rgba(255,255,255,0.1);
      border: 1px solid #444;
      border-radius:10px;
      padding:15px;
      margin:10px 0;
    ">
      <h3 style="margin-bottom:5px">{title}</h3>
      <div>{content}</div>
    </div>
    """, unsafe_allow_html=True)

# --- Setup Phase ---
if st.session_state.phase == 'setup':
    st.markdown("## 🔧 Game Setup")
    cols = st.columns([1,1,1,1,1,2])

    with cols[0]:
        n_mafia = st.number_input("Mafia", min_value=0, step=1, value=1)
    with cols[1]:
        n_police = st.number_input("Police", min_value=0, step=1, value=1)
    with cols[2]:
        n_doctor = st.number_input("Doctor", min_value=0, step=1, value=1)
    with cols[3]:
        n_likend = st.number_input("Likend", min_value=0, step=1, value=1)
    with cols[4]:
        n_cit = st.number_input("Citizen", min_value=0, step=1, value=2)
    with cols[5]:
        players_raw = st.text_area(
            "Enter player names (one per line)",
            height=120,
            placeholder="Alice\nBob\nCharlie\n..."
        )

    total_roles = n_mafia + n_police + n_doctor + n_likend + n_cit
    players = [p.strip() for p in players_raw.split('\n') if p.strip()]

    st.markdown(f"**Total roles**: {total_roles} — **Players entered**: {len(players)}")

    if st.button("🚀 Distribute Roles"):
        if len(players) != total_roles:
            st.error("Number of players must equal total roles. Adjust counts or names accordingly.")
        else:
            roles_list = (
                ["mafia"] * n_mafia +
                ["police"] * n_police +
                ["doctor"] * n_doctor +
                ["likend"] * n_likend +
                ["citizen"] * n_cit
            )
            random.shuffle(roles_list)

            st.session_state.players = players
            st.session_state.alive = players.copy()
            st.session_state.roles = dict(zip(players, roles_list))
            st.session_state.phase = 'reveal'
            st.session_state.current = 0
            for d in ['night_actions','revealed','action_done','action_result','vote_results']:
                st.session_state[d] = {}
            st.rerun()

# --- Reveal Phase ---
elif st.session_state.phase == 'reveal':
    idx = st.session_state.current
    players = st.session_state.players
    roles = st.session_state.roles

    if idx >= len(players):
        st.session_state.phase = 'night'
        st.session_state.current = 0
        st.rerun()
    else:
        player = players[idx]
        st.markdown(f"<h2>👤 {player}, your turn</h2>", unsafe_allow_html=True)
        if st.button("🕵️ Reveal Role"):
            st.success(f"**{roles[player].upper()}**", icon="🔍")
        if st.button("➡️ Next Player"):
            st.session_state.current += 1
            st.rerun()

# --- Night Phase ---
elif st.session_state.phase == 'night':
    alive = st.session_state.alive
    roles = st.session_state.roles
    idx = st.session_state.current

    for flag in ['revealed','action_done','action_result']:
        if flag not in st.session_state:
            st.session_state[flag] = {}

    maf_count = sum(1 for p in alive if 'maf' in roles[p].lower())
    if maf_count == 0:
        st.balloons()
        st.success("Citizens win! 🎉", icon="🏆")
        if st.button("🔄 Restart"):
            st.session_state.clear(); st.rerun()
        st.stop()
    if maf_count >= len(alive) - maf_count:
        st.error("Mafia wins! 🏴", icon="💀")
        if st.button("🔄 Restart"):
            st.session_state.clear(); st.rerun()
        st.stop()

    if idx >= len(alive):
        tgt = st.session_state.night_actions.get('mafia')
        save = st.session_state.night_actions.get('doctor')
        st.markdown("<h2>🌙 Night Results</h2>", unsafe_allow_html=True)
        if tgt == save:
            st.success(f"{tgt} was attacked but saved by the doctor! ❤️", icon="💉")
        else:
            st.error(f"{tgt} was killed by the mafia. 💀", icon="🔪")
            if tgt in st.session_state.alive:
                st.session_state.alive.remove(tgt)
        if st.button("🗳️ Proceed to Voting"):
            st.session_state.phase = 'voting'
            st.session_state.current = 0
            st.session_state.vote_results = {}
            for d in ['revealed','action_done','action_result']:
                st.session_state[d] = {}
            st.rerun()

    else:
        player = alive[idx]
        role = roles[player].lower()
        st.markdown(f"<h2>👤 {player}, hold the phone</h2>", unsafe_allow_html=True)

        if not st.session_state.revealed.get(player, False):
            if st.button("🕵️ Reveal your role"):
                st.session_state.revealed[player] = True
                st.rerun()
        else:
            card("Your Role", f"**{roles[player].upper()}**")
            if not st.session_state.action_done.get(player, False):
                if 'maf' in role:
                    choice = st.selectbox("Kill who?", [p for p in alive if p != player])
                    if st.button("🔪 Confirm Kill"):
                        st.session_state.night_actions['mafia'] = choice
                        st.session_state.action_result[player] = f"You targeted **{choice}**."
                        st.session_state.action_done[player] = True
                        st.rerun()
                elif 'polic' in role:
                    suspect = st.selectbox("Investigate who?", [p for p in alive if p != player])
                    if st.button("🔍 Investigate"):
                        is_m = 'maf' in roles[suspect].lower()
                        st.session_state.action_result[player] = (
                            f"🔍 {suspect} is {'Mafia' if is_m else 'Innocent'}."
                        )
                        st.session_state.action_done[player] = True
                        st.rerun()
                elif 'doc' in role:
                    save = st.selectbox("Save who?", alive)
                    if st.button("💉 Save"):
                        st.session_state.night_actions['doctor'] = save
                        st.session_state.action_result[player] = f"You chose to save **{save}**."
                        st.session_state.action_done[player] = True
                        st.rerun()
                elif 'likend' in role:
                    guess = st.selectbox("Guess Police:", [p for p in alive if p != player])
                    if st.button("❓ Guess"):
                        is_p = 'polic' in roles[guess].lower()
                        st.session_state.action_result[player] = (
                            f"❓ {guess} is {'Police' if is_p else 'Not Police'}."
                        )
                        st.session_state.action_done[player] = True
                        st.rerun()
                else:
                    st.info("Citizen: no action at night.")
                    if st.button("➡️ End Turn"):
                        st.session_state.action_result[player] = "You did nothing."
                        st.session_state.action_done[player] = True
                        st.rerun()
            else:
                st.markdown(f"> {st.session_state.action_result[player]}")
                if st.button("➡️ Continue"):
                    st.session_state.current += 1
                    st.session_state.revealed[player] = False
                    st.session_state.action_done[player] = False
                    st.session_state.action_result[player] = ""
                    st.rerun()

# --- Voting Phase ---
elif st.session_state.phase == 'voting':
    alive = st.session_state.alive
    idx = st.session_state.current

    if idx >= len(alive):
        vote_counts = {}
        for voted in st.session_state.vote_results.values():
            if voted and voted != "Skip":
                vote_counts[voted] = vote_counts.get(voted, 0) + 1

        if vote_counts:
            max_votes = max(vote_counts.values())
            candidates = [p for p, v in vote_counts.items() if v == max_votes]
        else:
            max_votes = 0
            candidates = []

        st.markdown("## 🗳️ Voting Results")
        for p, v in vote_counts.items():
            st.write(f"{p}: {v} vote(s)")

        if len(candidates) == 1 and max_votes > 1:
            eliminated = candidates[0]
            st.error(f"{eliminated} has been executed by voting. ⚰️")
            if eliminated in st.session_state.alive:
                st.session_state.alive.remove(eliminated)
        else:
            st.info("No player was eliminated this round due to tie or insufficient votes.")

        if st.button("➡️ Next Night"):
            st.session_state.phase = 'night'
            st.session_state.current = 0
            st.session_state.vote_results = {}
            for d in ['night_actions','revealed','action_done','action_result']:
                st.session_state[d] = {}
            st.rerun()
    else:
        player = alive[idx]
        st.markdown(f"<h2>🗳️ {player}, it's your turn to vote</h2>", unsafe_allow_html=True)
        choice = st.selectbox("Choose who you suspect is Mafia (or skip):", ["Skip"] + [p for p in alive if p != player])
        if st.button("✅ Submit Vote"):
            st.session_state.vote_results[player] = choice
            st.session_state.current += 1
            st.rerun()
