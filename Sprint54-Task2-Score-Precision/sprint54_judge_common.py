"""Shared Sprint 54 Qwen3-8B judge utilities, based on Sprint 53 P1 Compliance."""
from __future__ import annotations
import hashlib, json, os, platform, random, re, subprocess, sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import numpy as np
import pandas as pd
import torch

# MODEL_NAME = "Qwen/Qwen3-8B"
MODEL_NAME = "zai-org/GLM-4-9B-0414"

MAX_SEQ_LENGTH = 4096
MAX_NEW_TOKENS = 512
LOAD_IN_4BIT = True
PROMPT_ID = "P1_compliance"
SCORE_MIN, SCORE_MAX = 1.0, 10.0

COMMON_OUTPUT_SCHEMA = '''{
  "score": 1-10,
  "feedback": "brief explanation",
  "compliance": {"fully_translated": true, "target_language_mandarin": true,
    "simplified_chinese": true, "english_leakage": false,
    "pinyin_or_romanization": false, "cantonese_or_non_mandarin": false},
  "errors": [{"category": "mistranslation|omission|addition|entity|number|negation|terminology|fluency|grammar|language|script|source_leakage|format|other",
    "severity": "minor|major|critical", "description": "short description"}]
}'''

P1_SYSTEM = f'''You are a strict English-to-Mandarin translation evaluator.
FIRST check output compliance before judging fluency.
Required target:
- The source meaning must be translated, not copied.
- The output must be Mandarin Chinese.
- Use Simplified Chinese.
- Do not accept English/source leakage unless genuinely required.
- Do not accept Pinyin/romanization as a substitute for Chinese translation.
- Do not accept Cantonese-specific wording when standard Mandarin is required.
Mandatory score ceilings:
- Mostly untranslated / wrong target language: score <= 2
- Pinyin/romanization instead of Mandarin: score <= 2
- Predominantly Traditional Chinese when Simplified is required: score <= 4
- Major English/source leakage: score <= 4
After compliance, judge accuracy, fidelity, and fluency.
Return ONLY valid JSON using this schema:
{COMMON_OUTPUT_SCHEMA}
Do not add text outside JSON. Do not think aloud.'''

def build_prompt(source, candidate):
    return ("<|im_start|>system\n" + P1_SYSTEM.strip() +
            "\n<|im_end|>\n<|im_start|>user\nEnglish source:\n" + str(source) +
            "\n\nCandidate Mandarin:\n" + str(candidate) +
            "\n<|im_end|>\n<|im_start|>assistant\n/no_think\n")

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def config_fingerprint(config):
    return hashlib.sha256(json.dumps(config,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def package_version(name):
    try:
        from importlib.metadata import version
        return version(name)
    except Exception: return "not-installed-or-unknown"

def environment_metadata(config, data_path):
    try:
        gpu=torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
    except Exception: gpu="unknown"
    try:
        cuda_runtime=torch.version.cuda
    except Exception: cuda_runtime=None
    try:
        commit=subprocess.check_output(['git','rev-parse','HEAD'],stderr=subprocess.DEVNULL,text=True).strip()
    except Exception: commit=None
    result={"config":config,"config_fingerprint_sha256":config_fingerprint(config),"prompt_sha256":hashlib.sha256(P1_SYSTEM.encode("utf-8")).hexdigest(),
      "timestamp_utc":pd.Timestamp.now(tz='UTC').isoformat(),"python":sys.version,
      "platform":platform.platform(),"machine":platform.machine(),"gpu":gpu,"cuda_runtime":cuda_runtime,
      "torch":torch.__version__,"transformers":package_version('transformers'),
      "unsloth":package_version('unsloth'),"numpy":np.__version__,"pandas":pd.__version__,
      "dataset_path":str(Path(data_path).resolve()),"dataset_sha256":sha256_file(data_path),"git_commit":commit}
    return result

def load_gold(path, direction='EN_CMN'):
    df=pd.read_csv(path)
    required={'sample_id','source_en','mt_output','overall_gold'}
    missing=required-set(df.columns)
    if missing: raise ValueError(f"Gold CSV missing required columns {sorted(missing)}; found {list(df.columns)}")
    if 'direction' in df: df=df[df['direction'].astype(str).str.upper().eq(direction.upper())].copy()
    df=df.dropna(subset=['source_en','mt_output','overall_gold']).copy()
    df['source_en']=df['source_en'].astype(str).str.strip(); df['mt_output']=df['mt_output'].astype(str).str.strip()
    df=df[(df.source_en!='')&(df.mt_output!='')]
    df['overall_gold']=pd.to_numeric(df['overall_gold'],errors='coerce'); df=df.dropna(subset=['overall_gold'])
    return df.reset_index(drop=True)

class P1Judge:
    def __init__(self, model_name=MODEL_NAME, max_seq_length=MAX_SEQ_LENGTH, max_new_tokens=MAX_NEW_TOKENS, load_in_4bit=LOAD_IN_4BIT):
        try:
            from unsloth import FastLanguageModel
        except ImportError as e:
            raise RuntimeError('Install Unsloth and its supported PyTorch/Transformers dependencies before running.') from e
        self.model_name=model_name; self.max_seq_length=max_seq_length; self.max_new_tokens=max_new_tokens
        self.model,self.tokenizer=FastLanguageModel.from_pretrained(model_name=model_name,max_seq_length=max_seq_length,dtype=None,load_in_4bit=load_in_4bit)
        FastLanguageModel.for_inference(self.model)
        if self.tokenizer.pad_token_id is None: self.tokenizer.pad_token_id=self.tokenizer.eos_token_id
    @staticmethod
    def parse(raw):
        cleaned=re.sub(r'<think>.*?</think>','',raw,flags=re.S).strip()
        if cleaned.startswith('```'):
            cleaned=re.sub(r'^```(?:json)?\s*','',cleaned,flags=re.I); cleaned=re.sub(r'\s*```$','',cleaned)
        obj=None
        try: obj=json.loads(cleaned)
        except Exception:
            a,b=cleaned.find('{'),cleaned.rfind('}')
            if a>=0 and b>a:
                try: obj=json.loads(cleaned[a:b+1])
                except Exception: pass
        score=None
        if isinstance(obj,dict):
            try: score=float(obj.get('score'))
            except Exception: pass
        if score is None:
            m=re.search(r'(?<!\d)(10(?:\.0+)?|[1-9](?:\.\d+)?)(?!\d)',cleaned)
            if m: score=float(m.group(1))
        valid=score is not None and SCORE_MIN<=score<=SCORE_MAX
        return {"score":round(score,2) if valid else None,"parse_ok":bool(valid),"feedback":obj.get('feedback') if isinstance(obj,dict) else None,
                "compliance":obj.get('compliance',{}) if isinstance(obj,dict) else {},"errors":obj.get('errors',[]) if isinstance(obj,dict) else [],"raw_output":raw}
    def evaluate(self, source, candidate, temperature=0.0, seed=5300):
        if seed is not None:
            random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
            if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)
        prompt=build_prompt(source,candidate)
        try:
            inputs=self.tokenizer(prompt,return_tensors='pt',truncation=True,max_length=self.max_seq_length).to(self.model.device)
            kwargs=dict(**inputs,max_new_tokens=self.max_new_tokens,do_sample=temperature>0,renormalize_logits=True,use_cache=True,
                        pad_token_id=self.tokenizer.pad_token_id,eos_token_id=self.tokenizer.eos_token_id)
            if temperature>0: kwargs['temperature']=temperature
            with torch.no_grad(): outputs=self.model.generate(**kwargs)
            raw=self.tokenizer.decode(outputs[:,inputs.input_ids.shape[1]:][0],skip_special_tokens=True)
            result=self.parse(raw); result.update({"success":result['parse_ok'],"error":None if result['parse_ok'] else 'Could not parse valid 1-10 score',"temperature":temperature,"seed":seed})
            return result
        except Exception as e:
            return {"score":None,"parse_ok":False,"success":False,"error":str(e),"raw_output":None,"temperature":temperature,"seed":seed,"feedback":None,"compliance":{},"errors":[]}
