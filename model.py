"""One bounded CPU generation at a time, with explicit evidence references."""
import re
import threading
import time

MODEL = 'Qwen/Qwen2.5-Coder-1.5B-Instruct'
REVISION = '2e1fd397ee46e1388853d2af2c993145b0f1098a'
_lock = threading.Lock()
_model = _tokenizer = None

def load():
    global _model, _tokenizer
    if _model is None:
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM
        torch.set_num_threads(2)
        _tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION)
        _model = AutoModelForCausalLM.from_pretrained(MODEL, revision=REVISION, torch_dtype=torch.float32).eval()
    return _model, _tokenizer

def converse(question, ghost, evidence):
    if not _lock.acquire(blocking=False):
        raise RuntimeError('Another séance is running. Try again shortly.')
    try:
        start=time.monotonic()
        model, tok=load()
        facts='\n'.join(f"[{x['id']}] {x['fact']}" for x in evidence)
        loops=[]
        for item in evidence:
            loop=next((line.strip() for line in item['quote'].splitlines() if line.strip().startswith('for attempt in range(')),None)
            if loop:loops.append(f"[{item['id']}] Observed loop: {loop}")
        facts+='\n'+'\n'.join(loops)
        prompt = f'''Function: {ghost['name']}\nRECORDS:\n{facts}\nQUESTION: {question}\nAnswer with ONE short English sentence, starting with [E1], [E2] or [E3]. Explain; do not copy the records. Do not write code, diffs or lists. If the answer is unknown, say that the record does not establish it.'''
        messages=[{'role':'system','content':'You are a code-history ghost. Explain recorded facts in one plain English sentence, in first person, with a source citation. Never invent author intentions.'},
          {'role':'user','content':prompt}]
        inputs=tok.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_tensors='pt')
        import torch
        with torch.inference_mode():
            out=model.generate(inputs, attention_mask=torch.ones_like(inputs), max_new_tokens=100,
                do_sample=False, repetition_penalty=1.08, pad_token_id=tok.eos_token_id,
                max_time=45)
        raw=tok.decode(out[0][inputs.shape[-1]:], skip_special_tokens=True).strip()
        refs=set(re.findall(r'\[(E\d+)\]',raw)); allowed={x['id'] for x in evidence}
        hit_limit=out.shape[-1]-inputs.shape[-1]>=100
        valid=bool(refs) and refs<=allowed and not hit_limit
        return {'text':raw, 'citations':sorted(refs), 'citation_ids_valid':valid,
                'model':MODEL, 'revision':REVISION, 'output_limit_reached':hit_limit, 'input_tokens':inputs.shape[-1],
                'output_tokens':out.shape[-1]-inputs.shape[-1], 'seconds':round(time.monotonic()-start,3),
                'interpretation_notice':'Model interpretation, not a verified account of developer intent. Valid citation IDs do not prove the explanation; inspect the exact evidence.'}
    finally:
        _lock.release()
