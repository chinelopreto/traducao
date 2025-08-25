# traducao
ddon

## Translation Scripts

This repository contains scripts for translating game text data from English to Portuguese (Brazil).

### Files

- `translate_gmd_blocks.py` - Main translation script using OpenAI API
- `fix_csv.py` - Utility to fix malformed CSV files
- `split_gmd1.py` - Utility to split large CSV files into smaller blocks
- `gmd1_block_*.csv` - Split CSV files ready for translation (blocks 1-7)

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up OpenAI API key:
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

### Usage

#### Basic Translation
```bash
python translate_gmd_blocks.py --input-dir ./ --model gpt-4o-mini --block-start 1 --block-end 7 --batch-size 20
```

#### Test Mode
```bash
# Test the script without making API calls
python translate_gmd_blocks.py --test-mode --block-start 1 --block-end 1
```

#### Single Block Translation
```bash
# Translate only block 1
python translate_gmd_blocks.py --block-start 1 --block-end 1
```
- `--input-dir`: Directory containing gmd1_block_*.csv files (default: current directory)
- `--model`: OpenAI model to use (default: gpt-4o-mini)
- `--block-start`: First block to process (default: 1)
- `--block-end`: Last block to process (default: 7)
- `--batch-size`: Number of rows per API request (default: 20)
- `--overwrite`: Regenerate existing output files

#### Output
- Creates `gmd1_block_*_pt.csv` files with Portuguese translations
- Preserves original CSV structure (8 columns)
- Protects placeholders (%s, %d, {0}, etc.) and proper names
- Maintains game-specific formatting

### Data Processing

The original `gmd1.csv` file contained malformed lines. The processing workflow:

1. **Fix CSV**: `fix_csv.py` cleans malformed data (277K → 131K valid rows)
2. **Split**: `split_gmd1.py` creates 7 manageable block files (~18,741 rows each)
3. **Translate**: `translate_gmd_blocks.py` processes blocks using OpenAI API

### Translation Features

- **Portuguese (Brazil)** localization
- **Placeholder protection**: Preserves %s, %d, {0}, <tags>, [buttons], etc.
- **Proper name protection**: Prevents translation of character/location names
- **Resumable**: Skips existing files unless --overwrite is used
- **Error handling**: Retries with exponential backoff
- **Progress tracking**: Shows translation progress with tqdm
