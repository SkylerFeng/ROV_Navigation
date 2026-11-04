"""Optional local KEY=value file. No shell evaluation, no credential logging."""
import os
from pathlib import Path
ALLOWED={'DEEPSEEK_API_KEY','DASHSCOPE_API_KEY','ROV_LLM_MODEL','ROV_LLM_BASE_URL'}
def load_credentials(path):
    if path is None:return
    for line in Path(path).read_text().splitlines():
        line=line.strip()
        if not line or line.startswith('#'):continue
        if line.startswith('export '):line=line[7:].strip()
        key,sep,value=line.partition('=')
        if not sep or key.strip() not in ALLOWED:raise ValueError('Unsupported credential-file entry')
        value=value.strip()
        if len(value)>=2 and value[0]==value[-1] and value[0] in ('"',"'"):value=value[1:-1]
        if value:os.environ.setdefault(key.strip(),value)
