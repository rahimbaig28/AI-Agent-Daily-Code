# Auto-generated via Perplexity on 2026-02-18T05:37:55.499778Z
import json
import re
import statistics
import pathlib
from datetime import datetime
import sys

DB_PATH = pathlib.Path('results.json')

def load_history():
    if DB_PATH.exists():
        try:
            with open(DB_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(history):
    try:
        with open(DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Could not save history: {e}")

def count_syllables(word):
    word = word.lower()
    syllable_count = len(re.findall(r'[aeiouy]+', word))
    if word.endswith('e'):
        syllable_count = max(1, syllable_count - 1)
    if len(word) > 2 and word[-3:] in ['ion', 'ious']:
        syllable_count += 1
    return max(1, syllable_count)

def analyze_text(text):
    if not text.strip():
        return None
    
    # Clean text
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Sentences: .!? followed by space/capital
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    num_sentences = len(sentences)
    
    # Words
    words = re.findall(r'\b\w+\b', text)
    num_words = len(words)
    
    if num_sentences == 0 or num_words == 0:
        return None
    
    # Word and sentence lengths
    word_lengths = [len(w) for w in words]
    avg_word_length = statistics.mean(word_lengths)
    
    sentence_lengths = [len(re.findall(r'\b\w+\b', s)) for s in sentences]
    avg_sentence_length = statistics.mean(sentence_lengths)
    
    # Syllables for Flesch-Kincaid
    total_syllables = sum(count_syllables(w) for w in words)
    syllables_per_word = total_syllables / num_words
    
    # Flesch-Kincaid Grade Level
    # 0.39 * (words/sentences) + 11.8 * (syllables/words) - 15.59
    flesch_kincaid = 0.39 * (num_words / num_sentences) + 11.8 * syllables_per_word - 15.59
    
    # Passive voice (heuristic: forms of "be" + past participle)
    passive_patterns = [
        r'\b(is|are|was|were|been|being)\s+\w+(ed|ing)?\b',
        r'\b(gets?|got|gotten)\s+(called|done|named)\b'
    ]
    passive_count = sum(len(re.findall(p, text, re.I)) for p in passive_patterns)
    passive_percentage = (passive_count / num_sentences * 100) if num_sentences else 0
    
    metrics = {
        'avg_word_length': round(avg_word_length, 2),
        'avg_sentence_length': round(avg_sentence_length, 2),
        'flesch_kincaid_grade': round(flesch_kincaid, 2),
        'passive_voice_pct': round(passive_percentage, 2),
        'num_words': num_words,
        'num_sentences': num_sentences,
        'word_lengths': {'mean': round(statistics.mean(word_lengths), 2),
                        'median': round(statistics.median(word_lengths), 2)},
        'sentence_lengths': {'mean': round(statistics.mean(sentence_lengths), 2),
                           'median': round(statistics.median(sentence_lengths), 2)}
    }
    
    # Accessibility flags
    issues = []
    if metrics['flesch_kincaid_grade'] > 18:
        issues.append("High grade level (>18)")
    if metrics['avg_sentence_length'] > 20:
        issues.append("Long sentences (>20 words)")
    if metrics['passive_voice_pct'] > 30:
        issues.append("High passive voice usage")
    
    metrics['accessibility_issues'] = issues
    metrics['readability_rating'] = "Hard to read" if issues else "Accessible"
    
    return metrics

def analyze_file(filepath):
    try:
        path = pathlib.Path(filepath)
        if not path.exists():
            print(f"❌ File not found: {filepath}")
            return None
        
        text = path.read_text(encoding='utf-8', errors='replace')
        
        # Handle JSON files
        if filepath.lower().endswith('.json'):
            try:
                data = json.loads(text)
                text = json.dumps(data, ensure_ascii=False, indent=2)
            except:
                pass  # Treat as plain text
        
        metrics = analyze_text(text)
        if metrics:
            metrics['filename'] = path.name
            metrics['timestamp'] = datetime.now().isoformat()
            print(f"\n📊 Analysis for: {path.name}")
            print("=" * 50)
            print(f"Words: {metrics['num_words']:,} | Sentences: {metrics['num_sentences']:,}")
            print(f"Avg word length: {metrics['avg_word_length']:.1f} chars")
            print(f"Avg sentence length: {metrics['avg_sentence_length']:.1f} words")
            print(f"Flesch-Kincaid Grade: {metrics['flesch_kincaid_grade']:.1f}")
            print(f"Passive voice: {metrics['passive_voice_pct']:.1f}%")
            print(f"\n📈 Statistics:")
            print(f"  Word lengths - Mean: {metrics['word_lengths']['mean']:.1f}, Median: {metrics['word_lengths']['median']:.1f}")
            print(f"  Sentence lengths - Mean: {metrics['sentence_lengths']['mean']:.1f}, Median: {metrics['sentence_lengths']['median']:.1f}")
            
            if metrics['accessibility_issues']:
                print(f"\n⚠️  Accessibility Issues:")
                for issue in metrics['accessibility_issues']:
                    print(f"   • {issue}")
            else:
                print(f"\n✅ {metrics['readability_rating']}")
            
            return metrics
        else:
            print("❌ No valid text found in file")
            return None
            
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return None

def print_history(history):
    if not history:
        print("📋 No analysis history found.")
        return
    
    print(f"\n📋 Analysis History ({len(history)} entries):")
    print("-" * 60)
    for i, result in enumerate(reversed(history[-10:]), 1):  # Show last 10
        print(f"{i}. {result['filename']} ({result['timestamp'][:16]})")
        print(f"   Grade: {result['flesch_kincaid_grade']:.1f} | "
              f"Sentences: {result['avg_sentence_length']:.1f}w | "
              f"Issues: {len(result['accessibility_issues'])}")
        print()

def export_history(history, output_file):
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        print(f"💾 History exported to: {output_file}")
    except Exception as e:
        print(f"❌ Export failed: {e}")

def main():
    history = load_history()
    
    while True:
        print("\n" + "="*50)
        print("🎯 ACCESSIBILITY TEXT ANALYZER")
        print("1. Analyze file")
        print("2. View history")
        print("3. Export history to JSON")
        print("4. Clear history")
        print("5. Exit")
        print("="*50)
        
        choice = input("Select option (1-5): ").strip()
        
        if choice == '1':
            filepath = input("Enter file path: ").strip()
            if filepath:
                result = analyze_file(filepath)
                if result:
                    history.append(result)
                    save_history(history)
                    print("✅ Saved to history")
        
        elif choice == '2':
            print_history(history)
        
        elif choice == '3':
            export_name = input("Export filename [history.json]: ").strip() or "history.json"
            export_history(history, export_name)
        
        elif choice == '4':
            confirm = input("Clear all history? (y/N): ").lower()
            if confirm == 'y':
                history.clear()
                DB_PATH.unlink(missing_ok=True)
                print("🗑️ History cleared")
        
        elif choice == '5':
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid option. Please try again.")

if __name__ == "__main__":
    main()