#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path

def summarize(text: str) -> dict:
    nodes: dict[int,int] = {}
    lines = 0
    for line in text.splitlines():
        found = re.findall(r'\bN(\d+)=(\d+)\b', line)
        if found: lines += 1
        for node,pages in found:
            nodes[int(node)] = nodes.get(int(node),0) + int(pages)
    total=sum(nodes.values())
    return {
        'mapped_lines_with_node_counts':lines,
        'total_pages':total,
        'nodes':{str(node):{'pages':pages,'percent':100.0*pages/total if total else 0.0} for node,pages in sorted(nodes.items())}
    }

def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument('--pid',type=int)
    p.add_argument('--input')
    p.add_argument('--output')
    args=p.parse_args()
    if bool(args.pid)==bool(args.input): p.error('provide exactly one of --pid or --input')
    source=Path(f'/proc/{args.pid}/numa_maps') if args.pid else Path(args.input)
    result=summarize(source.read_text(errors='replace'))
    result['source']=str(source)
    rendered=json.dumps(result,indent=2)+'\n'
    if args.output: Path(args.output).write_text(rendered)
    print(rendered,end='')

if __name__=='__main__': main()
