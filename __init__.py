from aqt import mw
from aqt.utils import tooltip
from aqt.qt import QAction, qconnect
from aqt import gui_hooks
from aqt.deckbrowser import DeckBrowserContent

# Cache stats globally so the homepage renders instantly without database lag
resolver_stats = {
    "mature_vocab": 0,
    "suspended_sentences": 0,
    "unlocked_recently": 0
}

def get_field_index(model, field_name: str) -> int:
    """Helper to find the ordinal index of a field within a Note Type."""
    for c, f in enumerate(model['flds']):
        if f['name'] == field_name:
            return c
    return -1

def update_and_resolve_dependencies(is_startup=False) -> None:
    global resolver_stats
    if not mw.col:
        return

    # 1. Load User Configuration Safely
    config = mw.addonManager.getConfig(__name__) or {}
    
    # Both vocab and sentences now accept lists to handle multiple Note Types
    vocab_model_names = config.get("vocab_note_types", ["Vocabulary+", "Russian Custom Vocab"])
    sentence_model_names = config.get("sentence_note_types", ["Sentence", "Sentence+", "Russian Custom Sentence"])
    
    vocab_id_fname = config.get("vocab_id_field", "Vocab_ID")
    sentence_deps_fname = config.get("sentence_deps_field", "Dependencies")
    maturity_ivl = config.get("maturity_interval", 14)
    apply_tag = config.get("apply_tag", "auto-unlocked")

    # 2. Fetch Mature Vocabulary across MULTIPLE Note Types
    known_vocab_ids = set()
    
    for model_name in vocab_model_names:
        vocab_model = mw.col.models.by_name(model_name)
        if not vocab_model:
            continue
            
        vocab_id_idx = get_field_index(vocab_model, vocab_id_fname)
        if vocab_id_idx == -1:
            continue

        vocab_query = f'"note:{model_name}" prop:ivl>={maturity_ivl}'
        try:
            vocab_note_ids = mw.col.find_notes(vocab_query)
        except Exception:
            continue

        if not vocab_note_ids:
            continue

        id_list = ",".join(map(str, vocab_note_ids))
        rows = mw.col.db.all(f"SELECT flds FROM notes WHERE id IN ({id_list})")
        
        for (flds,) in rows:
            fields = flds.split('\x1f')
            if len(fields) > vocab_id_idx:
                val = fields[vocab_id_idx].strip()
                if val:
                    known_vocab_ids.add(val)

    # Update Mature Vocab Stat
    resolver_stats["mature_vocab"] = len(known_vocab_ids)

    # 3. Fetch Suspended Sentences across MULTIPLE Note Types
    total_suspended_sentences = 0
    cards_to_unsuspend = []
    notes_to_tag = set()

    for model_name in sentence_model_names:
        sentence_model = mw.col.models.by_name(model_name)
        if not sentence_model:
            continue
            
        sentence_deps_idx = get_field_index(sentence_model, sentence_deps_fname)
        if sentence_deps_idx == -1:
            continue

        sentence_query = f'"note:{model_name}" is:suspended'
        try:
            suspended_card_ids = mw.col.find_cards(sentence_query)
        except Exception:
            continue

        if not suspended_card_ids:
            continue

        total_suspended_sentences += len(suspended_card_ids)

        suspended_cids_str = ",".join(map(str, suspended_card_ids))
        query = f"""
            SELECT c.id, n.id, n.flds 
            FROM cards c
            JOIN notes n ON c.nid = n.id
            WHERE c.id IN ({suspended_cids_str})
        """
        
        rows = mw.col.db.all(query)
        
        # 4. Evaluate Dependencies in Memory
        for cid, nid, flds in rows:
            fields = flds.split('\x1f')
            if len(fields) > sentence_deps_idx:
                deps_raw = fields[sentence_deps_idx]
                dependencies = [d.strip() for d in deps_raw.split(',') if d.strip()]
                
                # If valid dependencies exist and ALL are in the known vocabulary set
                if dependencies and all(dep in known_vocab_ids for dep in dependencies):
                    cards_to_unsuspend.append(cid)
                    notes_to_tag.add(nid)

    # Update Suspended and Unlocked Stats
    resolver_stats["suspended_sentences"] = total_suspended_sentences
    resolver_stats["unlocked_recently"] = len(cards_to_unsuspend)

    # 5. Execute Changes safely
    if cards_to_unsuspend:
        mw.checkpoint("Resolve Dependencies")
        mw.col.sched.unsuspend_cards(cards_to_unsuspend)
        mw.col.tags.bulk_add(list(notes_to_tag), apply_tag)
        
        # Deduct newly unlocked from the suspended total so the UI is immediately accurate
        resolver_stats["suspended_sentences"] -= len(cards_to_unsuspend)
        
        if not is_startup:
            tooltip(f"Dependency Resolver: Unsuspended {len(cards_to_unsuspend)} new sentences!")
    else:
        if not is_startup and total_suspended_sentences > 0:
            tooltip("Dependency Resolver: No new sentences unlocked.")
            
    # If triggered manually via the tools menu, redraw the homepage to update stats
    if not is_startup:
        mw.reset()


def render_stats_on_homepage(deck_browser, content: DeckBrowserContent):
    """Injects a custom stat panel below the Heatmap on the Anki homepage."""
    html = f"""
    <div style="margin: 20px auto; max-width: 650px; text-align: center; font-family: sans-serif; 
                background-color: var(--window-bg); border: 1px solid var(--border); 
                border-radius: 8px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
        <h3 style="margin-top: 0; margin-bottom: 15px; color: var(--text-fg); font-size: 14px; font-weight: 600;">
            Dependency Resolver Status
        </h3>
        <div style="display: flex; justify-content: space-around; font-size: 13px; color: var(--text-fg);">
            <div>
                <strong style="font-size: 18px; color: #4caf50;">{resolver_stats['mature_vocab']}</strong><br>
                Mature Vocab
            </div>
            <div>
                <strong style="font-size: 18px; color: #ff9800;">{resolver_stats['suspended_sentences']}</strong><br>
                Locked Sentences
            </div>
            <div>
                <strong style="font-size: 18px; color: #2196f3;">{resolver_stats['unlocked_recently']}</strong><br>
                Recently Unlocked
            </div>
        </div>
    </div>
    """
    content.stats += html

# ==========================================
# UI INTEGRATION
# ==========================================

# 1. Run the dependency solver and calculate stats quietly on startup
gui_hooks.profile_did_open.append(lambda: update_and_resolve_dependencies(is_startup=True))

# 2. Inject the HTML into the Deck Browser (Homepage)
gui_hooks.deck_browser_will_render_content.append(render_stats_on_homepage)

# 3. Allow manual triggering from the Tools menu
action = QAction("Resolve Dependencies", mw)
qconnect(action.triggered, lambda: update_and_resolve_dependencies(is_startup=False))
mw.form.menuTools.addAction(action)
