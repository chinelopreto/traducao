#!/usr/bin/env python3
"""
translate_gmd_blocks.py
-----------------------
Translate the MsgEn column of gmd1_block_*.csv to Portuguese in-place outputs as gmd1_block_*_pt.csv,
preserving CSV structure (8 columns) and avoiding translation of proper names / placeholders.

USAGE:
  export OPENAI_API_KEY="sk-..."
  python translate_gmd_blocks.py --input-dir ./ --model gpt-4o-mini --block-start 1 --block-end 7 --batch-size 20

Notes:
- Requires: pip install openai pandas python-dotenv tqdm
- Model can be any capable text model; defaults to "gpt-4o-mini".
- Resumable: existing *_pt.csv files are skipped unless --overwrite is set.
"""

import os, re, csv, json, time, argparse, sys
from typing import List, Dict, Tuple
import pandas as pd
from tqdm import tqdm

try:
    from openai import OpenAI
except Exception as e:
    print("ERROR: Missing 'openai' package. Install with: pip install openai", file=sys.stderr)
    raise

# ---------------------- Helpers ----------------------

PLACEHOLDER_PATTERNS = [
    r"%\d*\.*\d*[sdif]",           # %s, %d, %0.2f etc.
    r"\{[0-9]+\}",                 # {0}, {1}
    r"\{[A-Za-z_][A-Za-z0-9_]*\}", # {name}
    r"\\n",                        # \n
    r"\\t",                        # \t
    r"<[^>]+>",                    # <color=...>, <br>, <sprite=...>
    r"\[[^\]]+\]",                 # [Button], [Key: E]
]

PLACEHOLDER_REGEX = re.compile("|".join(f"({p})" for p in PLACEHOLDER_PATTERNS))

def find_placeholders(text: str) -> List[str]:
    return [m.group(0) for m in PLACEHOLDER_REGEX.finditer(text or "")]

def mask_tokens(text: str, tokens: List[str], marker_left="«", marker_right="»") -> Tuple[str, Dict[str,str]]:
    """Mask exact tokens to prevent translation; returns masked text and a map for unmasking."""
    safe = text if isinstance(text, str) else ""
    mapping = {}
    # Sort by length desc to avoid partial overlaps
    for tok in sorted(set(tokens), key=len, reverse=True):
        if not tok:
            continue
        safe_tok = f"{marker_left}{len(mapping)}{marker_right}"
        mapping[safe_tok] = tok
        safe = safe.replace(tok, safe_tok)
    return safe, mapping

def unmask(text: str, mapping: Dict[str,str]) -> str:
    out = text
    for k,v in mapping.items():
        out = out.replace(k, v)
    return out

def extract_proper_nouns(msg_en: str) -> List[str]:
    """Heuristic: keep capitalized multiword names and TitleCase tokens as protected."""
    if not isinstance(msg_en, str) or not msg_en:
        return []
    # Keep hyphenated and apostrophized words
    tokens = re.findall(r"[A-Za-z][A-Za-z'\-]+(?:\s+[A-Za-z][A-Za-z'\-]+)+|[A-Z][a-z0-9'\-]+", msg_en)
    # Filter generic English words that start uppercase at sentence start
    # We'll keep as-is; over-protecting is safer than mistranslating names.
    return list(set(tokens))

def build_system_prompt():
    return (
        "Você é um tradutor profissional de jogos. Traduza do inglês para português do Brasil (pt-BR). "
        "Mantenha exatamente quaisquer placeholders e tags (%s, %d, {0}, {name}, \\n, <...>, [...]). "
        "NÃO traduza nomes próprios de NPCs, inimigos, lugares, itens únicos. "
        "Evite aumentar o comprimento desnecessariamente. "
        "Saída apenas com os textos traduzidos na mesma ordem das entradas, um por linha, sem enumeração."
    )

def build_user_prompt(batch_en: List[str]) -> str:
    # Join inputs by newline with marker to avoid accidental merges
    sep = "\n---\n"
    return f"Traduza cada linha individualmente, mantendo placeholders intactos e nomes próprios intactos. Linhas:\n{sep.join(batch_en)}"

def call_openai(client, model: str, batch_en: List[str], temperature: float=0.2, max_retries: int=5, test_mode: bool=False) -> List[str]:
    if test_mode:
        # Return mock Portuguese translations for testing
        mock_translations = []
        for text in batch_en:
            # Simple mock translation: keep placeholders but add "PT:" prefix
            mock_pt = f"PT:{text}" if text and not text.startswith("PT:") else text
            mock_translations.append(mock_pt or "")
        return mock_translations
    
    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(batch_en)
    backoff = 2.0
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=model,
                temperature=temperature,
                messages=[
                    {"role":"system", "content": system_prompt},
                    {"role":"user", "content": user_prompt}
                ]
            )
            text = resp.choices[0].message.content.strip()
            # Split on the separator or newline fallback
            if "\n---\n" in text:
                parts = [p.strip() for p in text.split("\n---\n")]
            else:
                parts = [p.strip() for p in text.splitlines() if p.strip()!=""]
            return parts
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(backoff)
            backoff = min(30.0, backoff * 1.8)
    return []

def ensure_placeholders(original: str, translated: str) -> str:
    """Ensure translated keeps same placeholder instances count; if missing, restore from original."""
    orig_ph = find_placeholders(original or "")
    if not orig_ph:
        return translated or ""
    # quick check: ensure each placeholder appears at least once; if not, append missing at end (safer than losing)
    out = translated or ""
    for ph in orig_ph:
        if out.count(ph) < original.count(ph):
            out += f" {ph}"
    return out

# ---------------------- Main ----------------------

def process_block(input_path: str, output_path: str, client, model: str, batch_size: int=20, overwrite: bool=False, test_mode: bool=False):
    if os.path.exists(output_path) and not overwrite:
        print(f"[skip] {os.path.basename(output_path)} already exists. Use --overwrite to regenerate.")
        return

    # Read CSV with error handling for extra columns
    try:
        df = pd.read_csv(input_path, dtype=str, keep_default_na=False, quoting=csv.QUOTE_MINIMAL)
    except pd.errors.ParserError as e:
        print(f"[warn] Parser error reading {input_path}: {e}")
        print("[info] Trying with error_bad_lines=False...")
        df = pd.read_csv(input_path, dtype=str, keep_default_na=False, quoting=csv.QUOTE_MINIMAL, on_bad_lines='skip')
    
    required_cols = ["#Index","Key","MsgJp","MsgEn","GmdPath","ArcPath","ArcName","ReadIndex"]
    for c in required_cols:
        if c not in df.columns:
            raise RuntimeError(f"Missing column in {input_path}: {c}")
    
    # Keep only the required columns (drop any extra columns)
    df = df[required_cols]

    en_texts = df["MsgEn"].astype(str).tolist()
    results = [""] * len(en_texts)

    # Process in batches
    indices = list(range(len(en_texts)))
    for i in tqdm(range(0, len(indices), batch_size), desc=f"Translating {os.path.basename(input_path)}"):
        batch_idx = indices[i:i+batch_size]
        batch_en_raw = [en_texts[j] for j in batch_idx]

        # Protect placeholders and names
        masked_batch = []
        unmask_maps = []
        for s in batch_en_raw:
            phs = find_placeholders(s)
            names = extract_proper_nouns(s)
            to_protect = phs + names
            masked, mapp = mask_tokens(s, to_protect)
            masked_batch.append(masked)
            unmask_maps.append(mapp)

        # Call model
        outs = call_openai(client, model, masked_batch, test_mode=test_mode)

        # If model returned a single blob with same count separated by lines, map directly;
        # Otherwise, try to pad/truncate to batch size.
        if len(outs) != len(batch_idx):
            # Attempt a more robust split by assuming one per line
            outs = (outs + [""]*len(batch_idx))[:len(batch_idx)]

        # Unmask + placeholder check
        for k, j in enumerate(batch_idx):
            restored = unmask(outs[k], unmask_maps[k])
            restored = ensure_placeholders(batch_en_raw[k], restored)
            results[j] = restored

    # Write output with PT in MsgEn column
    df_out = df.copy()
    df_out["MsgEn"] = results

    # Use QUOTE_ALL to preserve commas safely
    df_out.to_csv(output_path, index=False, encoding="utf-8", quoting=csv.QUOTE_ALL)
    print(f"[ok] Saved {output_path}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", default=".", help="Directory where gmd1_block_*.csv live")
    ap.add_argument("--model", default=os.getenv("MODEL","gpt-4o-mini"), help="OpenAI model to use")
    ap.add_argument("--block-start", type=int, default=1, help="First block index (1..7)")
    ap.add_argument("--block-end", type=int, default=7, help="Last block index (1..7)")
    ap.add_argument("--batch-size", type=int, default=20, help="Rows per API request")
    ap.add_argument("--overwrite", action="store_true", help="Regenerate even if output exists")
    ap.add_argument("--test-mode", action="store_true", help="Use mock translations for testing (no API calls)")
    args = ap.parse_args()

    if not args.test_mode:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("ERROR: Please set OPENAI_API_KEY environment variable.", file=sys.stderr)
            sys.exit(1)
        client = OpenAI(api_key=api_key)
    else:
        print("[INFO] Running in test mode - no API calls will be made")
        client = None

    for idx in range(args.block_start, args.block_end+1):
        inp = os.path.join(args.input_dir, f"gmd1_block_{idx}.csv")
        out = os.path.join(args.input_dir, f"gmd1_block_{idx}_pt.csv")
        if not os.path.exists(inp):
            print(f"[warn] Missing {inp}, skipping.")
            continue
        process_block(inp, out, client, args.model, batch_size=args.batch_size, overwrite=args.overwrite, test_mode=args.test_mode)

if __name__ == "__main__":
    main()