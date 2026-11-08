import os, re, sys, collections, unicodedata
# 저장소 점검: 깨진 위키링크, 인덱스 누락, 번호 중복, 형식 위반을 출력한다.
# 실행: python -X utf8 .claude/scripts/audit.py
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.stdout.reconfigure(encoding="utf-8")
EXCL = {'.git','.obsidian','.stfolder','.claude'}
N = lambda s: unicodedata.normalize('NFC', s)
md, allfiles = [], {}
for dp, dns, fns in os.walk(ROOT):
    dns[:] = [d for d in dns if d not in EXCL]
    for f in fns:
        rel = os.path.relpath(os.path.join(dp,f), ROOT).replace('\\','/')
        allfiles.setdefault(N(f), []).append(rel)
        if f.endswith('.md'): md.append(N(rel))
names = collections.defaultdict(list)
for r in md: names[os.path.basename(r)[:-3]].append(r)
out = []
def P(*a): out.append(' '.join(str(x) for x in a))

# 1. wikilinks
link_re = re.compile(r'(!?)\[\[([^\]\n]+?)\]\]')
broken, broken_code, img_broken = [], [], []
total_links = 0
for r in md:
    txt = N(open(os.path.join(ROOT,r), encoding='utf-8').read())
    in_fence = False
    for ln, line in enumerate(txt.split('\n'),1):
        if line.strip().startswith('```'): in_fence = not in_fence; continue
        stripped = re.sub(r'`[^`]*`', '', line)
        for m in link_re.finditer(line):
            total_links += 1
            code = in_fence or m.group(0) not in stripped
            t = m.group(2).split('|')[0].split('#')[0].strip()
            t = t.replace('\\','')
            if not t: continue
            base = t.split('/')[-1]
            ext = os.path.splitext(base)[1].lower()
            if ext and ext != '.md' and ext in ('.png','.jpg','.jpeg','.gif','.svg','.pdf','.webp','.txt','.mp4'):
                if base not in allfiles: img_broken.append((r, ln, m.group(0), code))
                continue
            if base.endswith('.md'): base = base[:-3]
            if base not in names:
                (broken_code if code else broken).append((r, ln, t))
P('TOTAL_LINKS', total_links)
P('== BROKEN', len(broken)); [P(' ', *b) for b in broken]
P('== BROKEN_IN_CODE', len(broken_code)); [P(' ', *b) for b in broken_code]
P('== IMG_BROKEN', len(img_broken)); [P(' ', *b) for b in img_broken]

# 2. index
idx = N(open(os.path.join(ROOT,'000_인덱스.md'),encoding='utf-8').read()).split('\n')
sections = collections.defaultdict(lambda: collections.defaultdict(list))
sec, sub = None, None
for line in idx:
    m = re.match(r'> \[!note\]-\s*(.+)', line)
    if m: sec, sub = m.group(1).strip(), '노트'; continue
    if sec is None: continue
    m = re.match(r'>\s*\*\*(.+?)\*\*', line)
    if m: sub = m.group(1); continue
    for m in link_re.finditer(line):
        sections[sec][sub].append(m.group(2).split('|')[0].strip())
P('== SECTIONS'); [P(' ', s, {k: len(v) for k,v in d.items()}) for s,d in sections.items()]
P('== MALFORMED INDEX LINES')
for i,line in enumerate(idx,1):
    if '[[' in line and not re.match(r'^> - \[\[[^\]]+\]\]\s*$', line): P(' ', i, repr(line))
idx_all = set()
for s,d in sections.items():
    for k,v in d.items(): idx_all.update(v)
P('== INDEX TARGETS MISSING FILE')
for t in sorted(idx_all):
    if t not in names: P(' ', t)
P('== DUPLICATE ENTRIES IN SAME SECTION')
for s,d in sections.items():
    allv = sum(d.values(), [])
    for t,c in collections.Counter(allv).items():
        if c>1: P(' ', s, t, c)
def kind(r):
    parts = r.split('/')
    return parts[-2] if len(parts)>=2 else ''
skip = {'000_인덱스.md','README.md'}
total = sections.get('전체 통합 목록 (작성순)',{}); total_set = set(sum(total.values(), []))
lists = {'노트':'전체 노트 목록','실습':'전체 실습 목록','오답노트':'전체 오답노트 목록'}
P('== NOT IN INDEX AT ALL')
for r in md:
    if r in skip: continue
    b = os.path.basename(r)[:-3]
    if b not in idx_all: P(' ', r)
P('== MISSING FROM 통합목록 (non-summary, non-99)')
for r in md:
    if r in skip or r.startswith('00_요약노트') or r.startswith('99_기타'): continue
    b = os.path.basename(r)[:-3]
    if b not in total_set: P(' ', r)
P('== 통합목록 contains summary/99')
for t in total_set:
    for r in names.get(t,[]):
        if r.startswith('00_') or r.startswith('99_'): P(' ', r)
P('== MISSING FROM 종류별 목록')
for r in md:
    k = kind(r)
    if r.startswith('00_') or r.startswith('99_') or k not in lists: continue
    b = os.path.basename(r)[:-3]
    if b not in set(sum(sections[lists[k]].values(),[])): P(' ', lists[k], r)
P('== 종류별 목록 contains wrong kind')
for k,sn in lists.items():
    for t in sum(sections[sn].values(),[]):
        for r in names.get(t,[]):
            if kind(r)!=k: P(' ', sn, r)
P('== CATEGORY CALLOUT CHECK')
catsec = {}
for s in sections:
    m = re.match(r'(\d\d)\.', s)
    if m: catsec[m.group(1)] = s
for r in md:
    if r in skip: continue
    top = r.split('/')[0]; num = top[:2]; k = kind(r)
    b = os.path.basename(r)[:-3]
    s = catsec.get(num)
    if not s: P(' NO CALLOUT', r); continue
    found = [sub for sub,v in sections[s].items() if b in v]
    if not found:
        others = [ss for ss in catsec.values() if any(b in v for v in sections[ss].values())]
        P(' MISSING', r, '| in other callouts:', others)
    else:
        if num != '00' and k in ('노트','실습','참고자료','오답노트') and k not in found: P(' WRONG_SUB', r, found)
P('== CALLOUT ENTRY IN WRONG CATEGORY')
for num,s in catsec.items():
    for sub,v in sections[s].items():
        for t in v:
            for r in names.get(t,[]):
                if not r.startswith(num+'_'): P(' ', s, sub, r)

# 3. numbering
P('== NUMBERING')
for k in ['노트','실습','참고자료']:
    nums = collections.defaultdict(list)
    for r in md:
        if kind(r)==k:
            m = re.match(r'(\d{3})_', os.path.basename(r))
            if m: nums[int(m.group(1))].append(r)
            else: P(' NO NUMBER', k, r)
    P(' ', k, 'count', sum(len(v) for v in nums.values()), 'max', max(nums), 'distinct', len(nums))
    for n,v in sorted(nums.items()):
        if len(v)>1: P('  DUP', k, n, v)
    missing = [n for n in range(1,max(nums)+1) if n not in nums]
    P('  GAPS', missing)
P('== DUP BASENAMES')
for b,v in names.items():
    if len(v)>1: P(' ', v)
# 4. format
P('== FORMAT')
for r in md:
    if r in skip: continue
    raw = open(os.path.join(ROOT,r),'rb').read()
    txt = N(raw.decode('utf-8-sig'))
    probs=[]
    fm = re.match(r'---\r?\n(.*?)\r?\n---', txt, re.S)
    if not fm: probs.append('frontmatter 없음')
    elif not re.search(r'^tags\s*:', fm.group(1), re.M): probs.append('tags 없음')
    else:
        tm = re.search(r'^tags\s*:[ \t]*(.*)$', fm.group(1), re.M)
        if tm.group(1).strip() in ('','[]') and not re.search(r'^tags\s*:\s*\r?\n\s*-', fm.group(1), re.M): probs.append('tags 비어있음')
    if '🔗 관련 노트' not in txt: probs.append('관련 노트 줄 없음')
    if raw.startswith(b'\xef\xbb\xbf'): probs.append('BOM')
    k = kind(r)
    if not r.startswith('00_요약노트') and k not in ('노트','실습','참고자료','오답노트'): probs.append('하위폴더 밖')
    if k=='오답노트' and re.match(r'\d{3}_', os.path.basename(r)): probs.append('오답노트에 번호')
    if k=='오답노트' and not os.path.basename(r).endswith('오답노트.md'): probs.append('오답노트 이름형식')
    if k in ('노트','실습','참고자료') and not r.startswith('99_') and not re.match(r'\d{3}_', os.path.basename(r)): probs.append('번호 없음')
    if re.search(r'[\\:*?"<>|]', os.path.basename(r)): probs.append('금지문자')
    if probs: P(' ', r, '|', ', '.join(probs))
print('\n'.join(out))
