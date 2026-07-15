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
