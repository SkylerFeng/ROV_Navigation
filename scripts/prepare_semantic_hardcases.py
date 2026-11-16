"""Merge fixed-layout train views with baseline; entire wrong-hint scene held out."""
from pathlib import Path
import argparse,json,os
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('logs/hardening_20261116'));a=p.parse_args();root=a.root.resolve();out=root/'merged'
out.mkdir(exist_ok=False)
sources=[Path('logs/semantic_dataset_lit').resolve(),root/'data_west',root/'data_east'];counts={}
for split in ('train','val','test'):
 for kind in ('images','labels'):
  target=out/kind/split;target.mkdir(parents=True)
  for source in sources:
   for f in (source/kind/split).glob('*'):(target/f.name).symlink_to(f)
 counts[split]=len(list((out/'images'/split).glob('*.png')))
for dest,base in [(out,out),(root/'data_heldout',root/'data_heldout')]:
 (dest/'dataset.yaml').write_text(f'path: {base}\ntrain: images/train\nval: images/val\ntest: images/test\nnames: {{0: pipe, 1: box}}\n')
(root/'data_summary.json').write_text(json.dumps({'merged_counts':counts,'heldout_frames':len(list((root/'data_heldout/images/test').glob('*.png'))),'sources':list(map(str,sources))},indent=2))
