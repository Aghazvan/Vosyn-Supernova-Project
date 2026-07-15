# DSPy & GEPA Translation Optimizer Setup

Complete environment setup for the translation optimization pipeline.

## Quick Start

1. Clone this repo and create virtual environment:
   ```bash
   git clone <your-repo-url>
   cd my-dspy-gepa-setup
   python3.10 -m venv gepa_env
   source gepa_env/bin/activate
   pip install -r requirements.txt
   ```

2. Configure your API keys:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

3. Open and run the notebook:
   ```bash
   jupyter notebook DSPy_GEPA_Setup.ipynb
   ```

## Notebook Contents

- **Phase 1**: DSPy installation & validation
- **Phase 2**: Judge model API configuration
- **Phase 3**: RRWA multi-run aggregation
- **Phase 4**: End-to-end GEPA loop
- **Phase 5**: Full validation summary

## Requirements

- Python 3.10+
- OpenAI, Anthropic, or Together API keys
- See requirements.txt for Python packages

## Troubleshooting

**Issue**: Import dspy fails
- **Solution**: Collecting dspy-ai
  Downloading dspy_ai-3.2.1-py3-none-any.whl.metadata (421 bytes)
Collecting dspy>=3.2.1 (from dspy-ai)
  Downloading dspy-3.2.1-py3-none-any.whl.metadata (8.4 kB)
Collecting openai>=0.28.1 (from dspy>=3.2.1->dspy-ai)
  Downloading openai-2.44.0-py3-none-any.whl.metadata (34 kB)
Requirement already satisfied: regex>=2023.10.3 in /Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages (from dspy>=3.2.1->dspy-ai) (2026.4.4)
Collecting orjson>=3.9.0 (from dspy>=3.2.1->dspy-ai)
  Downloading orjson-3.11.9-cp310-cp310-macosx_10_15_x86_64.macosx_11_0_arm64.macosx_10_15_universal2.whl.metadata (41 kB)
Requirement already satisfied: tqdm>=4.66.1 in /Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages (from dspy>=3.2.1->dspy-ai) (4.67.3)
Requirement already satisfied: requests>=2.31.0 in /Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages (from dspy>=3.2.1->dspy-ai) (2.33.1)
Collecting pydantic>=2.0 (from dspy>=3.2.1->dspy-ai)
  Downloading pydantic-2.13.4-py3-none-any.whl.metadata (109 kB)
Collecting litellm>=1.64.0 (from dspy>=3.2.1->dspy-ai)
  Downloading litellm-1.91.0-py3-none-any.whl.metadata (40 kB)
Collecting diskcache>=5.6.0 (from dspy>=3.2.1->dspy-ai)
  Downloading diskcache-5.6.3-py3-none-any.whl.metadata (20 kB)
Collecting json-repair>=0.54.2 (from dspy>=3.2.1->dspy-ai)
  Downloading json_repair-0.61.2-py3-none-any.whl.metadata (20 kB)
Collecting tenacity>=8.2.3 (from dspy>=3.2.1->dspy-ai)
  Downloading tenacity-9.1.4-py3-none-any.whl.metadata (1.2 kB)
Requirement already satisfied: anyio in /Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages (from dspy>=3.2.1->dspy-ai) (4.13.0)
Collecting asyncer==0.0.8 (from dspy>=3.2.1->dspy-ai)
  Downloading asyncer-0.0.8-py3-none-any.whl.metadata (6.7 kB)
Collecting cachetools>=5.5.0 (from dspy>=3.2.1->dspy-ai)
  Downloading cachetools-7.1.4-py3-none-any.whl.metadata (5.5 kB)
Collecting cloudpickle>=3.1.2 (from dspy>=3.2.1->dspy-ai)
  Downloading cloudpickle-3.1.2-py3-none-any.whl.metadata (7.1 kB)
Requirement already satisfied: numpy>=1.26.0 in /Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages (from dspy>=3.2.1->dspy-ai) (1.26.4)
Collecting xxhash>=3.5.0 (from dspy>=3.2.1->dspy-ai)
  Downloading xxhash-3.8.1-cp310-cp310-macosx_10_9_x86_64.whl.metadata (15 kB)
Collecting gepa==0.0.27 (from gepa[dspy]==0.0.27->dspy>=3.2.1->dspy-ai)
  Downloading gepa-0.0.27-py3-none-any.whl.metadata (30 kB)
Collecting typeguard==4.4.3 (from dspy>=3.2.1->dspy-ai)
  Downloading typeguard-4.4.3-py3-none-any.whl.metadata (3.4 kB)
Requirement already satisfied: typing_extensions>=4.14.0 in /Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages (from typeguard==4.4.3->dspy>=3.2.1->dspy-ai) (4.15.0)
Requirement already satisfied: exceptiongroup>=1.0.2 in /Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages (from anyio->dspy>=3.2.1->dspy-ai) (1.3.1)
Requirement already satisfied: idna>=2.8 in /Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages (from anyio->dspy>=3.2.1->dspy-ai) (3.11)
Collecting fastuuid<1.0,>=0.14.0 (from litellm>=1.64.0->dspy>=3.2.1->dspy-ai)
  Downloading fastuuid-0.14.0-cp310-cp310-macosx_10_12_x86_64.whl.metadata (1.1 kB)
Requirement already satisfied: httpx<1.0,>=0.28.0 in /Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages (from litellm>=1.64.0->dspy>=3.2.1->dspy-ai) (0.28.1)
Collecting python-dotenv<2.0,>=1.0.0 (from litellm>=1.64.0->dspy>=3.2.1->dspy-ai)
  Downloading python_dotenv-1.2.2-py3-none-any.whl.metadata (27 kB)
Collecting tiktoken<1.0,>=0.8.0 (from litellm>=1.64.0->dspy>=3.2.1->dspy-ai)
  Downloading tiktoken-0.13.0-cp310-cp310-macosx_10_12_x86_64.whl.metadata (6.7 kB)
Collecting importlib-metadata<9.0,>=8.0.0 (from litellm>=1.64.0->dspy>=3.2.1->dspy-ai)
  Downloading importlib_metadata-8.9.0-py3-none-any.whl.metadata (4.5 kB)
Collecting tokenizers<1.0,>=0.21.0 (from litellm>=1.64.0->dspy>=3.2.1->dspy-ai)
  Downloading tokenizers-0.23.1-cp310-abi3-macosx_10_12_x86_64.whl.metadata (9.8 kB)
Requirement already satisfied: click<9.0,>=8.0.0 in /Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages (from litellm>=1.64.0->dspy>=3.2.1->dspy-ai) (8.3.2)
Requirement already satisfied: jinja2<4.0,>=3.1.6 in /Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages (from litellm>=1.64.0->dspy>=3.2.1->dspy-ai) (3.1.6)
Collecting aiohttp<4.0,>=3.10 (from litellm>=1.64.0->dspy>=3.2.1->dspy-ai)
  Downloading aiohttp-3.14.1-cp310-cp310-macosx_10_9_x86_64.whl.metadata (8.3 kB)
Collecting jsonschema<5.0,>=4.0.0 (from litellm>=1.64.0->dspy>=3.2.1->dspy-ai)
  Downloading jsonschema-4.26.0-py3-none-any.whl.metadata (7.6 kB)
Collecting aiohappyeyeballs>=2.5.0 (from aiohttp<4.0,>=3.10->litellm>=1.64.0->dspy>=3.2.1->dspy-ai)
  Downloading aiohappyeyeballs-2.7.1-py3-none-any.whl.metadata (5.9 kB)
Collecting aiosignal>=1.4.0 (from aiohttp<4.0,>=3.10->litellm>=1.64.0->dspy>=3.2.1->dspy-ai)
  Using cached aiosignal-1.4.0-py3-none-any.whl.metadata (3.7 kB)
Collecting async-timeout<6.0,>=4.0 (from aiohttp<4.0,>=3.10->litellm>=1.64.0->dspy>=3.2.1->dspy-ai)
  Downloading async_timeout-5.0.1-py3-none-any.whl.metadata (5.1 kB)
Collecting attrs>=17.3.0 (from aiohttp<4.0,>=3.10->litellm>=1.64.0->dspy>=3.2.1->dspy-ai)
  Downloading attrs-26.1.0-py3-none-any.whl.metadata (8.8 kB)
Collecting frozenlist>=1.1.1 (from aiohttp<4.0,>=3.10->litellm>=1.64.0->dspy>=3.2.1->dspy-ai)
  Downloading frozenlist-1.8.0-cp310-cp310-macosx_10_9_x86_64.whl.metadata (20 kB)
Collecting multidict<7.0,>=4.5 (from aiohttp<4.0,>=3.10->litellm>=1.64.0->dspy>=3.2.1->dspy-ai)
  Downloading multidict-6.7.1-cp310-cp310-macosx_10_9_x86_64.whl.metadata (5.3 kB)
Collecting propcache>=0.2.0 (from aiohttp<4.0,>=3.10->litellm>=1.64.0->dspy>=3.2.1->dspy-ai)
  Downloading propcache-0.5.2-cp310-cp310-macosx_10_9_x86_64.whl.metadata (16 kB)
Collecting yarl<2.0,>=1.17.0 (from aiohttp<4.0,>=3.10->litellm>=1.64.0->dspy>=3.2.1->dspy-ai)
  Downloading yarl-1.24.2-cp310-cp310-macosx_10_9_x86_64.whl.metadata (94 kB)
Requirement already satisfied: certifi in /Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages (from httpx<1.0,>=0.28.0->litellm>=1.64.0->dspy>=3.2.1->dspy-ai) (2026.2.25)
Requirement already satisfied: httpcore==1.* in /Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages (from httpx<1.0,>=0.28.0->litellm>=1.64.0->dspy>=3.2.1->dspy-ai) (1.0.9)
Requirement already satisfied: h11>=0.16 in /Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages (from httpcore==1.*->httpx<1.0,>=0.28.0->litellm>=1.64.0->dspy>=3.2.1->dspy-ai) (0.16.0)
Collecting zipp>=3.20 (from importlib-metadata<9.0,>=8.0.0->litellm>=1.64.0->dspy>=3.2.1->dspy-ai)
  Downloading zipp-4.1.0-py3-none-any.whl.metadata (3.6 kB)
Requirement already satisfied: MarkupSafe>=2.0 in /Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages (from jinja2<4.0,>=3.1.6->litellm>=1.64.0->dspy>=3.2.1->dspy-ai) (3.0.3)
Collecting jsonschema-specifications>=2023.03.6 (from jsonschema<5.0,>=4.0.0->litellm>=1.64.0->dspy>=3.2.1->dspy-ai)
  Downloading jsonschema_specifications-2025.9.1-py3-none-any.whl.metadata (2.9 kB)
Collecting referencing>=0.28.4 (from jsonschema<5.0,>=4.0.0->litellm>=1.64.0->dspy>=3.2.1->dspy-ai)
  Downloading referencing-0.37.0-py3-none-any.whl.metadata (2.8 kB)
Collecting rpds-py>=0.25.0 (from jsonschema<5.0,>=4.0.0->litellm>=1.64.0->dspy>=3.2.1->dspy-ai)
  Downloading rpds_py-0.30.0-cp310-cp310-macosx_10_12_x86_64.whl.metadata (4.1 kB)
Collecting distro<2,>=1.7.0 (from openai>=0.28.1->dspy>=3.2.1->dspy-ai)
  Downloading distro-1.9.0-py3-none-any.whl.metadata (6.8 kB)
Collecting jiter<1,>=0.10.0 (from openai>=0.28.1->dspy>=3.2.1->dspy-ai)
  Downloading jiter-0.16.0-cp310-cp310-macosx_10_12_x86_64.whl.metadata (5.2 kB)
Collecting sniffio (from openai>=0.28.1->dspy>=3.2.1->dspy-ai)
  Downloading sniffio-1.3.1-py3-none-any.whl.metadata (3.9 kB)
Collecting annotated-types>=0.6.0 (from pydantic>=2.0->dspy>=3.2.1->dspy-ai)
  Downloading annotated_types-0.7.0-py3-none-any.whl.metadata (15 kB)
Collecting pydantic-core==2.46.4 (from pydantic>=2.0->dspy>=3.2.1->dspy-ai)
  Downloading pydantic_core-2.46.4-cp310-cp310-macosx_10_12_x86_64.whl.metadata (6.6 kB)
Collecting typing-inspection>=0.4.2 (from pydantic>=2.0->dspy>=3.2.1->dspy-ai)
  Downloading typing_inspection-0.4.2-py3-none-any.whl.metadata (2.6 kB)
Requirement already satisfied: huggingface-hub<2.0,>=0.16.4 in /Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages (from tokenizers<1.0,>=0.21.0->litellm>=1.64.0->dspy>=3.2.1->dspy-ai) (0.36.2)
Requirement already satisfied: filelock in /Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages (from huggingface-hub<2.0,>=0.16.4->tokenizers<1.0,>=0.21.0->litellm>=1.64.0->dspy>=3.2.1->dspy-ai) (3.25.2)
Requirement already satisfied: fsspec>=2023.5.0 in /Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages (from huggingface-hub<2.0,>=0.16.4->tokenizers<1.0,>=0.21.0->litellm>=1.64.0->dspy>=3.2.1->dspy-ai) (2026.3.0)
Requirement already satisfied: hf-xet<2.0.0,>=1.1.3 in /Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages (from huggingface-hub<2.0,>=0.16.4->tokenizers<1.0,>=0.21.0->litellm>=1.64.0->dspy>=3.2.1->dspy-ai) (1.4.3)
Requirement already satisfied: packaging>=20.9 in /Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages (from huggingface-hub<2.0,>=0.16.4->tokenizers<1.0,>=0.21.0->litellm>=1.64.0->dspy>=3.2.1->dspy-ai) (26.0)
Requirement already satisfied: pyyaml>=5.1 in /Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages (from huggingface-hub<2.0,>=0.16.4->tokenizers<1.0,>=0.21.0->litellm>=1.64.0->dspy>=3.2.1->dspy-ai) (6.0.3)
Requirement already satisfied: charset_normalizer<4,>=2 in /Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages (from requests>=2.31.0->dspy>=3.2.1->dspy-ai) (3.4.7)
Requirement already satisfied: urllib3<3,>=1.26 in /Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/site-packages (from requests>=2.31.0->dspy>=3.2.1->dspy-ai) (2.6.3)
Downloading dspy_ai-3.2.1-py3-none-any.whl (1.2 kB)
Downloading dspy-3.2.1-py3-none-any.whl (331 kB)
Downloading asyncer-0.0.8-py3-none-any.whl (9.2 kB)
Downloading gepa-0.0.27-py3-none-any.whl (146 kB)
Downloading typeguard-4.4.3-py3-none-any.whl (34 kB)
Downloading cachetools-7.1.4-py3-none-any.whl (16 kB)
Downloading cloudpickle-3.1.2-py3-none-any.whl (22 kB)
Downloading diskcache-5.6.3-py3-none-any.whl (45 kB)
Downloading json_repair-0.61.2-py3-none-any.whl (48 kB)
Downloading litellm-1.91.0-py3-none-any.whl (16.7 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 16.7/16.7 MB 74.4 MB/s  0:00:00
Downloading aiohttp-3.14.1-cp310-cp310-macosx_10_9_x86_64.whl (519 kB)
Downloading async_timeout-5.0.1-py3-none-any.whl (6.2 kB)
Downloading fastuuid-0.14.0-cp310-cp310-macosx_10_12_x86_64.whl (264 kB)
Downloading importlib_metadata-8.9.0-py3-none-any.whl (27 kB)
Downloading jsonschema-4.26.0-py3-none-any.whl (90 kB)
Downloading multidict-6.7.1-cp310-cp310-macosx_10_9_x86_64.whl (44 kB)
Downloading openai-2.44.0-py3-none-any.whl (1.4 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.4/1.4 MB 23.7 MB/s  0:00:00
Downloading distro-1.9.0-py3-none-any.whl (20 kB)
Downloading jiter-0.16.0-cp310-cp310-macosx_10_12_x86_64.whl (310 kB)
Downloading pydantic-2.13.4-py3-none-any.whl (472 kB)
Downloading pydantic_core-2.46.4-cp310-cp310-macosx_10_12_x86_64.whl (2.1 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.1/2.1 MB 39.4 MB/s  0:00:00
Downloading python_dotenv-1.2.2-py3-none-any.whl (22 kB)
Downloading tiktoken-0.13.0-cp310-cp310-macosx_10_12_x86_64.whl (1.0 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.0/1.0 MB 19.8 MB/s  0:00:00
Downloading tokenizers-0.23.1-cp310-abi3-macosx_10_12_x86_64.whl (3.1 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 3.1/3.1 MB 42.1 MB/s  0:00:00
Downloading yarl-1.24.2-cp310-cp310-macosx_10_9_x86_64.whl (91 kB)
Downloading aiohappyeyeballs-2.7.1-py3-none-any.whl (15 kB)
Using cached aiosignal-1.4.0-py3-none-any.whl (7.5 kB)
Downloading annotated_types-0.7.0-py3-none-any.whl (13 kB)
Downloading attrs-26.1.0-py3-none-any.whl (67 kB)
Downloading frozenlist-1.8.0-cp310-cp310-macosx_10_9_x86_64.whl (49 kB)
Downloading jsonschema_specifications-2025.9.1-py3-none-any.whl (18 kB)
Downloading orjson-3.11.9-cp310-cp310-macosx_10_15_x86_64.macosx_11_0_arm64.macosx_10_15_universal2.whl (228 kB)
Downloading propcache-0.5.2-cp310-cp310-macosx_10_9_x86_64.whl (53 kB)
Downloading referencing-0.37.0-py3-none-any.whl (26 kB)
Downloading rpds_py-0.30.0-cp310-cp310-macosx_10_12_x86_64.whl (370 kB)
Downloading tenacity-9.1.4-py3-none-any.whl (28 kB)
Downloading typing_inspection-0.4.2-py3-none-any.whl (14 kB)
Downloading xxhash-3.8.1-cp310-cp310-macosx_10_9_x86_64.whl (34 kB)
Downloading zipp-4.1.0-py3-none-any.whl (10 kB)
Downloading sniffio-1.3.1-py3-none-any.whl (10 kB)
Installing collected packages: zipp, xxhash, typing-inspection, typeguard, tenacity, sniffio, rpds-py, python-dotenv, pydantic-core, propcache, orjson, multidict, json-repair, jiter, gepa, frozenlist, fastuuid, distro, diskcache, cloudpickle, cachetools, attrs, async-timeout, annotated-types, aiohappyeyeballs, yarl, tiktoken, referencing, pydantic, importlib-metadata, aiosignal, tokenizers, jsonschema-specifications, asyncer, aiohttp, openai, jsonschema, litellm, dspy, dspy-ai
  Attempting uninstall: tokenizers
    Found existing installation: tokenizers 0.15.2
    Uninstalling tokenizers-0.15.2:
      Successfully uninstalled tokenizers-0.15.2

Successfully installed aiohappyeyeballs-2.7.1 aiohttp-3.14.1 aiosignal-1.4.0 annotated-types-0.7.0 async-timeout-5.0.1 asyncer-0.0.8 attrs-26.1.0 cachetools-7.1.4 cloudpickle-3.1.2 diskcache-5.6.3 distro-1.9.0 dspy-3.2.1 dspy-ai-3.2.1 fastuuid-0.14.0 frozenlist-1.8.0 gepa-0.0.27 importlib-metadata-8.9.0 jiter-0.16.0 json-repair-0.61.2 jsonschema-4.26.0 jsonschema-specifications-2025.9.1 litellm-1.91.0 multidict-6.7.1 openai-2.44.0 orjson-3.11.9 propcache-0.5.2 pydantic-2.13.4 pydantic-core-2.46.4 python-dotenv-1.2.2 referencing-0.37.0 rpds-py-0.30.0 sniffio-1.3.1 tenacity-9.1.4 tiktoken-0.13.0 tokenizers-0.23.1 typeguard-4.4.3 typing-inspection-0.4.2 xxhash-3.8.1 yarl-1.24.2 zipp-4.1.0

**Issue**: API key not found
- **Solution**: Check .env file and ensure OPENAI_API_KEY (or relevant key) is set

**Issue**: Judge returns errors
- **Solution**: Verify API key validity and account has sufficient credits

## Next Steps

Once fine-tuned model is ready:
1. Update the GEPA loop with your model endpoint
2. Run full optimization pipeline on complete dataset
3. Log results for comparison with baseline

---
**Setup Completed**: [Date]
**Team**: [Your Team Name]
