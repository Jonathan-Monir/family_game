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
/* Full-page background */
[data-testid="stAppViewContainer"] {
  background: url('https://images.unsplash.com/photo-1524567496280-30c409fc0772?auto=format&fit=crop&w=1500&q=80') no-repeat center center fixed;
  background-size: cover;
}
/* Semi‑transparent panels */
[data-testid="stSidebar"], .css-18e3th9 {
  background-color: rgba(0, 0, 0, 0.6) !important;
  color: #fafafa !important;
}
/* Headings & buttons */
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
    cols = st.columns([2,1])
    with cols[0]:
        char_input = st.text_area(
            "Enter roles (e.g., mafia:1, police:1, doctor:1, likend:1, citizen:2)",
            height=80, placeholder="mafia:1, police:1, doctor:1, likend:1, citizen:2"
        )
        players_raw = st.text_area(
            "Enter player names (one per line)",
            height=120, placeholder="Alice\nBob\nCharlie"
        )
    with cols[1]:
        st.image("https://via.placeholder.com/150", width=150)
        st.markdown("> Ready to play?")

    if st.button("🚀 Distribute Roles"):
        # Parse inputs
        roles_list = []
        for t in char_input.split(','):
            if ':' in t:
                name, cnt = t.strip().split(':')
                roles_list += [name.strip()] * int(cnt)
        players = [p.strip() for p in players_raw.split('\n') if p.strip()]

        if len(players) != len(roles_list):
            st.error(f"{len(players)} players but {len(roles_list)} roles—please match counts.")
        else:
            random.shuffle(roles_list)
            st.session_state.players     = players
            st.session_state.alive       = players.copy()
            st.session_state.roles       = dict(zip(players, roles_list))
            st.session_state.phase       = 'reveal'
            st.session_state.current     = 0
            # clear any old turn flags
            for d in ['revealed','action_done','action_result']:
                st.session_state[d] = {}
            st.rerun()

# --- Reveal Phase ---
elif st.session_state.phase == 'reveal':
    idx     = st.session_state.current
    players = st.session_state.players
    roles   = st.session_state.roles

    if idx >= len(players):
        st.session_state.phase   = 'night'
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
    idx   = st.session_state.current

    # Initialize per-player flags if missing
    for flag in ['revealed','action_done','action_result']:
        if flag not in st.session_state:
            st.session_state[flag] = {}

    # Win checks
    maf_count = sum(1 for p in alive if 'maf' in roles[p].lower())
    if maf_count == 0:
        st.balloons(); st.success("Citizens win! 🎉", icon="🏆")
        if st.button("🔄 Restart"):
            st.session_state.clear(); st.rerun()
        st.stop()
    if maf_count >= len(alive) - maf_count:
        st.error("Mafia wins! 🏴", icon="💀")
        if st.button("🔄 Restart"):
            st.session_state.clear(); st.rerun()
        st.stop()

    # All acted → show results
    if idx >= len(alive):
        tgt  = st.session_state.night_actions.get('mafia')
        save = st.session_state.night_actions.get('doctor')
        st.markdown("<h2>🌙 Night Results</h2>", unsafe_allow_html=True)
        if tgt == save:
            st.success(f"Someone was attacked but saved by the doctor! ❤️", icon="💉")
        else:
            st.error(f"{tgt} was killed by the mafia. 💀", icon="🔪")
            if tgt in st.session_state.alive:
                st.session_state.alive.remove(tgt)
        if st.button("➡️ Next Round"):
            st.session_state.current = 0
            for d in ['night_actions','revealed','action_done','action_result']:
                st.session_state[d].clear()
            st.rerun()

    # Otherwise: each player's private turn
    else:
        player = alive[idx]
        role   = roles[player].lower()
        st.markdown(f"<h2>👤 {player}, hold the phone</h2>", unsafe_allow_html=True)

        if not st.session_state.revealed.get(player, False):
            if st.button("🕵️ Reveal your role"):
                st.session_state.revealed[player] = True
                st.rerun()

        else:
            card("Your Role", f"**{roles[player].upper()}**")

            if not st.session_state.action_done.get(player, False):
                # Mafia
                if 'maf' in role:
                    choice = st.selectbox("Kill who?", [p for p in alive if p != player])
                    if st.button("🔪 Confirm Kill"):
                        st.session_state.night_actions['mafia'] = choice
                        st.session_state.action_result[player]  = f"You targeted **{choice}**."
                        st.session_state.action_done[player]    = True
                        st.rerun()

                # Police
                elif 'polic' in role:
                    suspect = st.selectbox("Investigate who?", [p for p in alive if p != player])
                    if st.button("🔍 Investigate"):
                        is_m = 'maf' in roles[suspect].lower()
                        st.session_state.action_result[player] = (
                            f"🔍 **{suspect}** is *{'Mafia' if is_m else 'Innocent (not mafia)'}*"
                        )
                        st.session_state.action_done[player] = True
                        st.rerun()

                # Doctor
                elif 'doc' in role:
                    save = st.selectbox("Save who?", alive)
                    if st.button("💉 Save"):
                        st.session_state.night_actions['doctor'] = save
                        st.session_state.action_result[player]   = f"You chose to save **{save}**."
                        st.session_state.action_done[player]     = True
                        st.rerun()

                # Likend
                elif 'likend' in role:
                    guess = st.selectbox("Guess Police:", [p for p in alive if p != player])
                    if st.button("❓ Guess"):
                        is_p = 'polic' in roles[guess].lower()
                        st.session_state.action_result[player] = (
                            f"❓ **{guess}** is *{'Police' if is_p else 'Not Police'}*"
                        )
                        st.session_state.action_done[player] = True
                        st.rerun()

                # Citizen
                else:
                    st.info("Citizen: no action at night.")
                    if st.button("➡️ End Turn"):
                        st.session_state.action_result[player] = "You did nothing."
                        st.session_state.action_done[player]    = True
                        st.rerun()

            # After action, show result and continue
            else:
                st.markdown(f"> {st.session_state.action_result[player]}")
                if st.button("➡️ Continue"):
                    st.session_state.current += 1
                    # Reset flags for next player
                    st.session_state.revealed[player]      = False
                    st.session_state.action_done[player]   = False
                    st.session_state.action_result[player] = ""
                    st.rerun()
