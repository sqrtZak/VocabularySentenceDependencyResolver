# Dependency Resolver (Comprehensible Input)

Automate your i+1 sentence mining workflow! This add-on connects your Vocabulary cards to your Sentence cards so you never have to manually unsuspend cards again. 

If you use a Comprehensible Input or sentence mining approach (like Refold, AJATT, or MIA), you likely have sentence cards suspended because they contain unknown words. This add-on bridges that gap: once you learn the required vocabulary and those cards become "mature," the add-on automatically unlocks the associated sentence cards so you can start studying them.

## ✨ Features
* **Automated Unsuspending:** Runs seamlessly in the background every time you open your profile.
* **Homepage Dashboard:** Injects a beautiful, clean statistics panel right below your decks on the home screen, tracking your *Mature Vocab*, *Locked Sentences*, and *Recently Unlocked* counts.
* **i+1 Ready:** Supports multiple dependencies per sentence (comma-separated). A sentence is only unlocked when *all* required vocabulary words are mature.
* **Auto-Tagging:** Automatically tags newly unlocked sentences (default: `auto-unlocked`) so you can easily find them or filter them into custom study decks.
* **Manual Override:** Includes a "Resolve Dependencies" button in the Tools menu if you want to trigger a check manually.

## 🛠️ How It Works
1. You have a **Vocabulary** note type and a **Sentence** note type.
2. Your Sentence notes have a "Dependencies" field containing the target words you need to learn. 
3. The add-on checks your Vocabulary cards. Once a card hits a certain interval (default: 14 days), it is considered "known".
4. If a suspended Sentence card has all of its dependencies met by your "known" vocabulary, the add-on unsuspends it for you.

## ⚙️ Setup & Configuration
The add-on is highly customizable via the standard Anki Config menu (*Tools > Add-ons > Dependency Resolver > Config*). 

**Default Configuration:**
```json
{
    "vocab_note_types": ["Vocabulary+", "Russian Custom Vocab"],
    "sentence_note_types": ["Sentence", "Sentence+", "Russian Custom Sentence"],
    "vocab_id_field": "Vocab_ID",
    "sentence_deps_field": "Dependencies",
    "maturity_interval": 14,
    "apply_tag": "auto-unlocked"
}
```

* **`vocab_note_types` / `sentence_note_types`**: The names of your note types. You can include as many as you want in these lists.
* **`vocab_id_field`**: The field on your Vocabulary cards that contains the target word.
* **`sentence_deps_field`**: The field on your Sentence cards that lists the required words (if requiring multiple words, separate them with commas).
* **`maturity_interval`**: How many days the interval of a Vocab card needs to be before it is considered "known" (default is 14 days).
* **`apply_tag`**: The tag applied to sentences the moment they are unlocked.
