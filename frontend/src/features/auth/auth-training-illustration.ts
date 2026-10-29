import { LitElement, svg } from 'lit';

// Decorative sample artwork, independent of user history and business calculations.
const weights = [
  80, 80, 82.5, 82.5, 85, 85, 87.5, 87.5, 90, 90, 92.5, 92.5, 95, 95, 97.5, 97.5, 100, 102.5,
];
const points = weights.map((weight, i) => [34 + i * 31.2, 278 - (weight - 70) * 4.5]);
const line = points.map(([x, y], i) => `${i ? 'L' : 'M'} ${x} ${y}`).join(' ');

class AuthTrainingIllustration extends LitElement {
  createRenderRoot() {
    return this;
  }
  render() {
    return svg`<svg class="auth-training-art" viewBox="0 0 640 390" aria-hidden="true" focusable="false">
      <defs>
        <linearGradient id="training-area" x1="0" y1="0" x2="0" y2="1"><stop stop-color="var(--color-progress)" stop-opacity=".12"/><stop offset="1" stop-color="var(--color-progress)" stop-opacity="0"/></linearGradient>
        <radialGradient id="training-glow"><stop stop-color="var(--color-progress)" stop-opacity=".045"/><stop offset="1" stop-color="var(--color-progress)" stop-opacity="0"/></radialGradient>
      </defs>
      <ellipse cx="430" cy="160" rx="230" ry="180" fill="url(#training-glow)"/>
      <text class="art-symbol" x="26" y="24">KNIEBEUGE</text><text x="124" y="24">3 × 5 @ 8</text><text class="art-demo" x="630" y="24" text-anchor="end">BEISPIELPLAN</text>
      <path class="art-divider" d="M26 40H630 M26 295H630"/>
      <path class="art-grid" d="M26 76H586 M26 121H586 M26 166H586 M26 211H586 M26 256H586 M26 280H586 M64 54V280 M158 54V280 M252 54V280 M346 54V280 M440 54V280 M534 54V280 M586 54V280"/>
      <path d="${line} L564.4 280 L34 280 Z" fill="url(#training-area)"/>
      <path class="art-target" d="M34 246L128 228L222 211L316 194L410 176L504 158L564 148"/>
      <path class="art-progress-line" d=${line}/>
      ${points.map(([x, y], i) => svg`<circle class="art-point ${i === points.length - 1 ? 'last' : ''}" cx=${x} cy=${y} r=${i === points.length - 1 ? 4 : 2.5}/>`)}
      <path class="art-guide" d="M26 131.75H588"/>
      <rect class="art-marker" x="588" y="122.75" width="48" height="18" rx="3"/><text class="art-marker-label" x="612" y="135" text-anchor="middle">102,5</text>
      ${[80, 90, 100, 110].map((w) => svg`<text class="art-axis" x="630" y=${282 - (w - 70) * 4.5} text-anchor="end">${w} kg</text>`)}
      <text class="art-demo" x="26" y="319">TRAININGSTAGE</text>
      ${Array.from({ length: 6 }, (_, week) => svg`<g transform="translate(${26 + week * 94},335)">${[0, 1, 2].map((day) => svg`<rect class="art-session ${week < 3 || (week === 3 && day === 0) ? 'done' : ''}" x=${day * 24} y="0" width="20" height="7" rx="2"/>`)}<text class="art-axis" x="32" y="35" text-anchor="middle">W${week + 1}</text></g>`)}
      <path class="art-barbell" d="M602 338v28m12-28v28m-18-21v14m24-14v14m-18-7h12"/>
    </svg>`;
  }
}
customElements.define('auth-training-illustration', AuthTrainingIllustration);
