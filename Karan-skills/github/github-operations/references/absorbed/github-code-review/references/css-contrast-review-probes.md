# CSS Contrast Review Probes

Use this when a PR claims it fixes color contrast, WCAG AA failures, design-token colors, or accessibility styling. Treat the PR/issue claim as executable, not narrative.

## Pattern

1. Read the PR claim and linked issue. Identify exact selectors/elements claimed to be fixed.
2. Search for impacted selectors in both CSS and markup:

```bash
rg -n 'todo|section-navy|limited|color: var\(--gold\)|#[0-9a-fA-F]{3,6}|rgba?\(' site/index.html site/styles.css
```

3. Inspect the changed CSS with line numbers and surrounding HTML context:

```bash
nl -ba site/styles.css | sed -n '88,116p;386,396p'
nl -ba site/index.html | sed -n '190,230p;252,290p'
```

4. For transparent/tinted backgrounds, calculate the composite background and contrast ratio instead of eyeballing.

```bash
node - <<'NODE'
function srgb(c){c/=255; return c<=0.03928?c/12.92:Math.pow((c+0.055)/1.055,2.4)}
function rgbFromHex(hex){return hex.match(/[0-9a-f]{2}/gi).map(x=>parseInt(x,16))}
function lumRgb(rgb){return .2126*srgb(rgb[0])+.7152*srgb(rgb[1])+.0722*srgb(rgb[2])}
function ratioRgb(a,b){const [l1,l2]=[lumRgb(a),lumRgb(b)].sort((x,y)=>y-x); return (l1+0.05)/(l2+0.05)}
function compositeRgb(f,alpha,b){return f.map((v,i)=>Math.round(v*alpha+b[i]*(1-alpha)))}
const cotton=rgbFromHex('#F7F7F4');
const todoBg=compositeRgb(rgbFromHex('#FFEB3B'),0.18,cotton);
const navyTodoBg=compositeRgb(rgbFromHex('#FFEB3B'),0.18,rgbFromHex('#010092'));
const checks = [
 ['base/.limited .todo', '#54576E on cream TODO tint', ratioRgb(rgbFromHex('#54576E'), todoBg), 4.5],
 ['.section-navy .todo', '#FFFFFF on navy TODO tint', ratioRgb(rgbFromHex('#FFFFFF'), navyTodoBg), 4.5],
 ['.limited-list .num', '#7A5D20 on cream', ratioRgb(rgbFromHex('#7A5D20'), cotton), 4.5]
];
let ok=true;
for (const [name, desc, ratio, min] of checks) {
  const pass = ratio >= min;
  ok &&= pass;
  console.log(`${pass ? 'PASS' : 'FAIL'} ${name}: ${desc} = ${ratio.toFixed(2)}:1`);
}
if (!ok) process.exit(1);
NODE
```

## Review Pitfalls

- A selector name may sound like a dark section while the actual markup is on a light/cream surface. Verify the parent background in CSS and the element location in HTML.
- `rgba()`/alpha tokens require compositing over the real section background; raw foreground-vs-token comparisons can be wrong.
- If a PR claims “zero contrast failures,” check unchanged nearby small text too, not only the exact lines in the diff.
- If a local server or Lighthouse is blocked by sandbox permissions, report that honestly and include deterministic ratio calculations as the fallback evidence.
